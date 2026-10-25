"""Read-only local request planning. Never creates an archive or calls a remote API."""
from datetime import date,timedelta
from pathlib import Path
from types import SimpleNamespace
from archive import Archive,entry_key
from catalog import selected_datasets
from engine import request_spec
from transfer import plan_jobs

def inspect_plan(plan,api=None):
    if plan.source=='offline':return {'network':False,'cached':None,'pending':0,'estimate':0,'note':'offline'}
    archive=None
    result={'network':True,'cached':0,'pending':0,'estimate':None,'note':'sqlite_only'}
    try:
        if plan.archive_path and Path(plan.archive_path).is_file():archive=Archive(plan.archive_path,plan.account,readonly=True)
        recent=(date.today()-timedelta(days=max(0,plan.refresh_days-1))).isoformat()
        def available(key,day,method,args=(),kwargs=None,binary_format=''):
            if not archive or day=='snapshot' or (plan.refresh_days and day>=recent):return False
            token=entry_key(key,day,request_spec(key,method,args,kwargs,binary_format))
            return bool(archive.db.execute('SELECT 1 FROM responses WHERE entry_key=?',(token,)).fetchone())
        planner=SimpleNamespace(plan=plan,api=api,check=lambda:None,available=available)
        jobs=plan_jobs(planner,selected_datasets(plan))
        result['cached']=sum(1 for j in jobs if j.cached);result['pending']=sum(1 for j in jobs if not j.cached)
        activity_count=len(set(plan.activity_ids)) if plan.activity_ids else None
        extras=len(plan.activity_details)+len(plan.activity_files)
        # Pagination/fallback/retries may add calls. Extras here assume no stored detail replies.
        result['estimate']=result['pending']+(activity_count*extras if activity_count is not None else 0)
        result['activity_unknown']='activities' in plan.datasets and activity_count is None
        result['minimum_spacing_seconds']=max(0,result['estimate']-1)*plan.delay
        result['extras_upper_bound']=activity_count*extras if activity_count is not None else None
        return result
    except Exception:
        return dict(result,note='unavailable',estimate=None)
    finally:
        if archive:archive.close()
