import json
import threading
from pathlib import Path
from dataclasses import replace
import pytest
from engine import Plan,Exporter,account_key,days,Cancelled
from offline import ArchiveSync,OfflineExporter
from archive import Archive
from demo_data import DemoGarmin
from transfer import RemainingTime

def plan(tmp,**kwargs):
    return Plan(**(dict(start='2020-01-01',end='2020-01-14',datasets=['body_battery'],output=str(tmp/'out'),account=account_key('speed-test'),formats=['json'],refresh_days=0,delay=0,retries=0,archive_path=str(tmp/'data.sqlite'))|kwargs))

class BatteryAPI:
    def __init__(self):self.calls=[]
    def get_body_battery(self,start,end):
        self.calls.append((start,end))
        return [{'date':day,'bodyBatteryValuesArray':[[1,80],[2,79]],'charged':4} for day in days(start,end)]

def test_body_battery_14_days_use_2_requests_preserve_daily_shape_and_resume(tmp_path):
    p=plan(tmp_path);api=BatteryAPI();events=[]
    dest,r=Exporter(api,p,event=lambda *e:events.append(e)).run()
    assert api.calls==[('2020-01-01','2020-01-07'),('2020-01-08','2020-01-14')]
    assert r['completed'] and r['transfer']['requests']==2 and r['stats']['downloaded']==14
    data=json.loads(next(Path(dest).glob('body_battery*.json')).read_text())
    assert len(data)==14
    assert all(item['data']==[{'date':item['source_date'],'bodyBatteryValuesArray':[[1,80],[2,79]],'charged':4}] for item in data)
    api.calls.clear();r=Exporter(api,p).run()[1]
    assert not api.calls and r['stats']['cached']==14
    assert any(e[0]=='eta' for e in events) and events[-1]==('eta_end','complete')

def test_existing_cache_from_old_daily_mode_is_reused_and_only_contiguous_gaps_batched(tmp_path):
    api=BatteryAPI();p=plan(tmp_path,end='2020-01-03',optimize=False)
    Exporter(api,p).run();api.calls.clear()
    r=Exporter(api,replace(p,end='2020-01-14',optimize=True)).run()[1]
    assert api.calls==[('2020-01-04','2020-01-10'),('2020-01-11','2020-01-14')]
    assert r['stats']['cached']==3 and r['stats']['downloaded']==11

def test_truncated_body_range_does_not_mark_missing_days_as_empty(tmp_path):
    class Partial(BatteryAPI):
        def get_body_battery(self,start,end):
            data=super().get_body_battery(start,end)
            return data[:1] if start!=end else data
    api=Partial();p=plan(tmp_path,end='2020-01-07')
    dest,r=Exporter(api,p).run();assert r['completed']
    assert len(api.calls)==7 and r['transfer']['fallback_days']==6
    data=json.loads(next(Path(dest).glob('body_battery*.json')).read_text())
    assert len(data)==7 and all(item['data'] for item in data)

def test_rejected_range_falls_back_once_but_not_on_rate_limit(tmp_path):
    from garminconnect import GarminConnectConnectionError,GarminConnectTooManyRequestsError
    class Reject(BatteryAPI):
        def get_body_battery(self,start,end):
            if start!=end:
                self.calls.append((start,end));raise GarminConnectConnectionError('API Error 400')
            return super().get_body_battery(start,end)
    api=Reject();r=Exporter(api,plan(tmp_path)).run()[1]
    assert r['completed'] and sum(a!=b for a,b in api.calls)==1 and len(api.calls)==15
    class Limited(BatteryAPI):
        def get_body_battery(self,start,end):
            self.calls.append((start,end));raise GarminConnectTooManyRequestsError('private body')
    api=Limited();r=Exporter(api,plan(tmp_path/'limited')).run()[1]
    assert len(api.calls)==1 and r['fatal_diagnostic']['reason']=='rate_limit'
    assert 'private body' not in json.dumps(r)

def test_activity_range_pagination_and_grouping_keep_every_activity(tmp_path):
    class API(DemoGarmin):
        def __init__(self):self.pages=[]
        def search_activities(self,**kwargs):self.pages.append(kwargs);return super().search_activities(**kwargs)
    api=API();p=plan(tmp_path,datasets=['activities'],end='2020-01-14')
    dest,r=Exporter(api,p).run()
    assert r['completed'] and r['stats']['activities']==420
    assert len(api.pages)==6  # Five data pages and an explicit empty terminal page.
    assert {v['startDate'] for v in api.pages}=={'2020-01-01'}
    data=json.loads(next(Path(dest).glob('activities*.json')).read_text())
    assert len(data)==14 and all(len(day['data'])==30 for day in data)

def test_activity_range_ignored_filter_or_repeated_page_never_silently_commits(tmp_path):
    class Ignored(DemoGarmin):
        def search_activities(self,**kw):
            rows=super().search_activities(**kw)
            if kw['startDate']!=kw['endDate']:
                for a in rows:a['startTimeLocal']='2019-01-01 00:00:00'
            return rows
    r=Exporter(Ignored(),plan(tmp_path,datasets=['activities'],end='2020-01-02')).run()[1]
    assert r['completed'] and r['stats']['activities']==60 and r['transfer']['fallback_days']==2

def test_archive_batches_are_compatible_with_offline_export_and_legacy_cache(tmp_path):
    api=BatteryAPI();p=plan(tmp_path)
    Exporter(api,replace(p,end='2020-01-03',optimize=False)).run();api.calls.clear()
    r=ArchiveSync(api,p).run_sync()['report']
    assert r['completed'] and r['stats']['cached']==3 and len(api.calls)==2
    with Archive(p.archive_path,readonly=True) as db:assert db.db.execute("SELECT COUNT(*) FROM responses WHERE dataset='body_battery'").fetchone()[0]==14
    api.calls.clear();r=ArchiveSync(api,p).run_sync()['report'];assert not api.calls and r['stats']['cached']==14
    dest,r=OfflineExporter(replace(p,source='offline')).run();assert r['completed'] and r['transfer']['requests']==0
    assert len(json.loads(next(Path(dest).glob('body_battery*.json')).read_text()))==14

def test_cancellation_keeps_completed_daily_cache_for_next_run(tmp_path):
    cancel=threading.Event();api=BatteryAPI();p=plan(tmp_path)
    def event(*args):
        if args[0]=='progress':cancel.set()
    r=Exporter(api,p,cancel,event).run()[1]
    assert r['cancelled'] and r['stats']['downloaded']==1
    api.calls.clear();r=Exporter(api,p).run()[1]
    assert r['completed'] and r['stats']['cached']==1 and r['stats']['downloaded']==13

def test_eta_uses_measured_requests_cache_and_new_file_work_and_retry_floor():
    now=[0.];events=[];eta=RemainingTime(['summary']*10+['cache']*1000,1,lambda *e:events.append(e),clock=lambda:now[0])
    eta.emit();assert events[-1][1]['seconds'] is None
    for _ in range(3):
        eta.begin('summary');now[0]+=2;eta.observe_request(2);eta.finish()
    assert events[-1][1]['seconds']==pytest.approx(16)  # Seven requests plus estimated local cache work.
    eta.add('files',2);before=events[-1][1]['seconds'];eta.begin('files');now[0]+=20;eta.observe_request(20);eta.finish()
    assert events[-1][1]['seconds']>before  # The remaining file is now measured as slower.
    eta.open_activity_days=1;eta.emit();assert events[-1][1]['provisional']
