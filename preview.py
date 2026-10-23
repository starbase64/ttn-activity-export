"""Bounded, in-memory export samples. Never invokes the full export or writes files."""
from __future__ import annotations
import itertools
import json
from engine import Exporter, Cancelled, days, error_status, safe_cell
from catalog import DATASETS, ACTIVITY_DETAILS, selected_datasets
from failures import diagnostic


class PreviewConnectionFailed(Exception):
    pass


class PreviewBudgetReached(Exception):
    pass


def bounded_json(value, limit, budget=None):
    """Bound the display representation, including deep/nested JSON payloads."""
    budget = [3000] if budget is None else budget
    budget[0] -= 1
    if budget[0] < 0:
        return '[preview truncated]'
    if isinstance(value, dict):
        result={k:bounded_json(v,limit,budget) for k,v in itertools.islice(value.items(),100)}
        if len(value)>100:result['__preview__']='additional fields omitted'
        return result
    if isinstance(value,list):
        result=[bounded_json(v,limit,budget) for v in value[:limit]]
        if len(value)>limit:result.append({'__preview__':'additional items omitted'})
        return result
    return value[:2000]+'…' if isinstance(value,str) and len(value)>2000 else value


class Previewer(Exporter):
    def __init__(self,api,plan,cancel=None,event=lambda *a:None):
        super().__init__(api,plan,cancel,event)
        self.request_count=0
        self.sample_records=[]
        self.payloads={}
        self.preview_errors=[]
        self.preview_notes=[]
        self.budget_reached=False

    def call(self,fn,*args,**kwargs):
        if self.request_count>=self.plan.preview_requests:
            self.budget_reached=True
            raise PreviewBudgetReached()
        self.request_count+=1
        # No retries for a preview: a predictable upper bound is more useful here.
        self.check()
        self.wait(self.plan.delay)
        return fn(*args,**kwargs)

    def iter_payloads(self,records):
        for record in records:
            yield record,self.payloads[record['path']]

    def store_sample(self,key,day,payload):
        token=str(len(self.sample_records))
        record={'dataset':key,'date':day,'path':token}
        self.sample_records.append(record);self.payloads[token]=payload
        return record

    def activity_sample(self):
        selected=[];seen=set();offset=0
        for page in range(3):
            self.check()
            if not callable(getattr(self.api,'search_activities',None)):
                self.preview_notes.append('activity_reader_unavailable')
                return selected
            # Only a few pages from the configured date range, never its full history.
            try:
                batch=self.call(self.api.search_activities,start=offset,limit=20,
                                startDate=self.plan.start,endDate=self.plan.end,sortOrder='asc')
            except PreviewBudgetReached:
                break
            if not isinstance(batch,list):raise ValueError('Invalid activity response')
            if not batch:break
            offset+=len(batch)
            fresh=[]
            for item in batch:
                if not isinstance(item,dict):raise ValueError('Invalid activity record')
                ident=item.get('activityId')
                token=str(ident) if ident is not None else json.dumps(item,sort_keys=True)
                if token not in seen:seen.add(token);fresh.append(item)
            if not fresh:
                self.preview_notes.append('repeated_page')
                break
            selected.extend(self.match_activities(fresh))
            if len(selected)>=self.plan.preview_rows:break
        return selected[:self.plan.preview_rows]

    def add_activity_details(self,activities):
        if not activities:return
        ident=activities[0].get('activityId')
        if ident is None:return
        for method in self.plan.activity_details:
            kwargs={'maxchart':self.plan.preview_rows,'maxpoly':self.plan.preview_rows} if method=='get_activity_details' else {}
            try:
                payload=self.call(getattr(self.api,method),ident,**kwargs)
                self.store_sample('activity-'+str(ident)+'-'+method.removeprefix('get_activity_'),self.plan.start,payload)
            except (PreviewBudgetReached,PreviewConnectionFailed,Cancelled):raise
            except Exception as exc:
                self.record_error(method,exc)

    def record_error(self,key,exc):
        from garminconnect import GarminConnectAuthenticationError,GarminConnectTooManyRequestsError
        if isinstance(exc,(GarminConnectAuthenticationError,GarminConnectTooManyRequestsError)):
            raise exc
        from garminconnect import GarminConnectConnectionError,GarminConnectNotFoundError
        self.preview_errors.append({'dataset':key,**diagnostic(exc)})
        if isinstance(exc,GarminConnectConnectionError) and not isinstance(exc,GarminConnectNotFoundError):
            raise PreviewConnectionFailed() from exc

    def sample_dataset(self,ds):
        result=[]
        if ds.binary:
            self.preview_notes.append('files_not_downloaded');return result
        for day in (['snapshot'] if ds.kind=='account' else itertools.islice(days(self.plan.start,self.plan.end),3)):
            self.check()
            try:
                if ds.key=='goals':
                    # get_goals auto-paginates; use the same read endpoint for just one page.
                    payload=self.call(self.api.connectapi,self.api.garmin_connect_goals_url,
                        params={'status':'active','start':'1','limit':str(self.plan.preview_rows)},
                        headers={'Sec-Fetch-Site':'same-origin'})
                else:
                    args=() if ds.kind=='account' else (day,day) if ds.kind=='range' else (day,)
                    kwargs={'aggregation':'daily'} if ds.key=='endurance' else {}
                    payload=self.fetch_data(ds.key,day,ds.method,args,kwargs)
                result.append(self.store_sample(ds.key,day,payload))
                if len(list(itertools.islice(self.rows(result),self.plan.preview_rows)))>=self.plan.preview_rows:
                    break
            except (PreviewBudgetReached,PreviewConnectionFailed,Cancelled):raise
            except Exception as exc:
                self.record_error(ds.key,exc)
        return result

    def make_groups(self):
        groups={}
        for record in self.sample_records:
            groups.setdefault(record['dataset'],[]).append(record)
        output=[]
        for key,records in groups.items():
            rows=list(itertools.islice(self.rows(records),self.plan.preview_rows))
            summary=key=='activities' and self.plan.activity_summary
            fields=self.summary_fields() if summary else (
                ['source_date','dataset','path','value','type'] if self.plan.layout=='long' else
                list(dict.fromkeys(k for row in rows for k in row)))
            # Match spreadsheet-safe CSV values, including German decimal commas.
            if len(fields)>100:
                fields=fields[:100];self.preview_notes.append('columns_truncated')
            cells=[(self.table_cells(row,summary) if 'csv' in self.plan.formats else {k:safe_cell(v) for k,v in row.items()}) for row in rows]
            output.append({'key':key,'fields':fields,'rows':cells,
                'raw':[{'source_date':r['date'],'dataset':r['dataset'],'data':bounded_json(self.payloads[r['path']],self.plan.preview_rows)} for r in records]})
        return output

    def run_preview(self):
        cancelled=False
        try:
            for ds in selected_datasets(self.plan):
                if ds.key=='activities':
                    try:
                        activities=self.activity_sample()
                        self.store_sample('activities',self.plan.start,activities)
                        self.add_activity_details(activities)
                    except (PreviewBudgetReached,PreviewConnectionFailed,Cancelled):raise
                    except Exception as exc:self.record_error(ds.key,exc)
                else:self.sample_dataset(ds)
        except PreviewConnectionFailed:
            self.preview_notes.append('stopped_after_connection_error')
        except PreviewBudgetReached:
            self.budget_reached=True
        except Cancelled:
            cancelled=True
        if self.plan.expert_method:self.preview_notes.append('expert_not_sampled')
        if self.plan.activity_files:self.preview_notes.append('files_not_downloaded')
        return {'groups':self.make_groups(),'requests':self.request_count,'budget_reached':self.budget_reached,
                'cancelled':cancelled,'errors':self.preview_errors,'notes':self.preview_notes+self.warnings,
                'plan':self.plan}
