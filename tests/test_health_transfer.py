import json
from dataclasses import replace
from pathlib import Path
import pytest
from archive import Archive
from catalog import DAILY_METHODS, selected_datasets
from engine import Plan, Exporter, account_key, days
from offline import ArchiveSync, OfflineExporter, OfflinePreviewer
from preview import Previewer
from repairs import repair_plan


def plan(tmp, **kwargs):
    return Plan(**(dict(start='2020-01-01', end='2020-02-25', datasets=['summary'],
        output=str(tmp/'out'), account=account_key('health-range'), formats=['csv','json'],
        delay=0, retries=0, refresh_days=0, archive_path=str(tmp/'offline.sqlite')) | kwargs))


class API:
    def __init__(self): self.calls=[]
    def get_user_summary(self, day):
        self.calls.append(('summary',day,day))
        return {'calendarDate':day, 'totalSteps':1234, 'extra':{'untouched':True}, 'nullable':None}
    def get_daily_summaries(self, start, end):
        self.calls.append(('summary-range',start,end))
        return {'data':[{'calendarDate':d, 'totalSteps':1234, 'extra':{'untouched':True}, 'nullable':None} for d in days(start,end)]}
    def get_heart_rates(self, day):
        self.calls.append(('full-heart',day,day))
        return {'calendarDate':day,'heartRateValues':[[1,60],[2,62]]}
    def __getattr__(self, method):
        if method not in DAILY_METHODS.values():raise AttributeError(method)
        def fetch(start, end):
            self.calls.append((method,start,end))
            return [{'calendarDate':d,'value':57,'totalSteps':1234} for d in days(start,end)]
        return fetch


def test_full_summaries_56_days_two_calls_and_identical_old_daily_cache(tmp_path):
    api=API(); p=plan(tmp_path)
    dest, r=Exporter(api,p).run()
    assert r['completed'] and r['transfer']['requests']==2
    assert api.calls==[('summary-range','2020-01-01','2020-01-28'),('summary-range','2020-01-29','2020-02-25')]
    rows=json.loads(next(Path(dest).glob('summary*.json')).read_text())
    assert len(rows)==56 and all(x['data']['extra']=={'untouched':True} and x['data']['nullable'] is None for x in rows)
    api.calls.clear()
    r=Exporter(api,replace(p,optimize=False)).run()[1]
    assert r['completed'] and not api.calls and r['stats']['cached']==56


def test_full_summary_legacy_cache_only_missing_ranges_fetched(tmp_path):
    api=API(); p=plan(tmp_path)
    Exporter(api,replace(p,end='2020-01-07',optimize=False)).run(); api.calls.clear()
    r=ArchiveSync(api,p).run_sync()['report']
    assert r['completed'] and r['stats']['cached']==7 and len(api.calls)==2
    dest,r=OfflineExporter(replace(p,source='offline')).run()
    assert r['completed'] and r['transfer']['requests']==0
    assert len(json.loads(next(Path(dest).glob('summary*.json')).read_text()))==56


@pytest.mark.parametrize('key',list(DAILY_METHODS))
def test_each_daily_statistics_category_batches_and_retains_56_dated_rows(tmp_path,key):
    p=plan(tmp_path,datasets=[key],health_detail='daily');api=API()
    dest,r=Exporter(api,p).run()
    assert r['completed'] and len(api.calls)==2 and r['transfer']['requests']==2
    assert all(method==DAILY_METHODS[key] for method,_,_ in api.calls)
    data=json.loads(next(Path(dest).glob(key+'-daily*.json')).read_text())
    assert len(data)==56 and all(x['data'][0]['calendarDate']==x['source_date'] for x in data)
    assert 'daily_statistics_without_timelines' in r['warnings']


def test_statistics_archive_cannot_satisfy_full_timeline_and_resumes_independently(tmp_path):
    p=plan(tmp_path,datasets=['heart_rate'],end='2020-01-03');api=API()
    assert ArchiveSync(api,p).run_sync()['report']['completed']
    daily=replace(p,health_detail='daily')
    assert ArchiveSync(api,daily).run_sync()['report']['completed']
    with Archive(p.archive_path,readonly=True) as db:
        assert dict(db.db.execute('SELECT dataset,COUNT(*) FROM responses GROUP BY dataset'))=={'heart_rate':3,'heart_rate-daily':3}
    for selected in (p,daily):
        api.calls.clear();r=ArchiveSync(api,selected).run_sync()['report']
        assert r['completed'] and not api.calls and r['stats']['cached']==3
        assert OfflineExporter(replace(selected,source='offline')).run()[1]['completed']
    preview=OfflinePreviewer(replace(daily,source='offline')).run_preview()
    assert preview['requests']==0 and preview['groups'][0]['key']=='heart_rate-daily'
    assert not repair_plan(p.archive_path,p.account,2,[],daily)


def test_missing_statistics_day_retried_without_marking_it_empty(tmp_path):
    class Partial(API):
        def get_daily_heart_rate_stats(self,start,end):
            rows=super().__getattr__('get_daily_heart_rate_stats')(start,end)
            return rows[:1] if start!=end else rows
    api=Partial();p=plan(tmp_path,datasets=['heart_rate'],health_detail='daily',end='2020-01-07')
    dest,r=Exporter(api,p).run()
    assert r['completed'] and len(api.calls)==7 and r['transfer']['fallback_days']==6
    assert len(json.loads(next(Path(dest).glob('heart_rate-daily*.json')).read_text()))==7


@pytest.mark.parametrize('status',[401,403,429])
def test_new_summary_range_never_falls_back_after_auth_or_rate_block(tmp_path,status):
    from garminconnect import GarminConnectConnectionError
    class Blocked(API):
        def get_daily_summaries(self,start,end):
            self.calls.append(('blocked',start,end));raise GarminConnectConnectionError(f'API Error {status}')
    api=Blocked();r=Exporter(api,plan(tmp_path)).run()[1]
    assert not r['completed'] and len(api.calls)==1 and r['stats']['downloaded']==0


def test_invalid_full_summary_batch_falls_back_without_persisting_foreign_date(tmp_path):
    class Wrong(API):
        def get_daily_summaries(self,start,end):
            self.calls.append(('bad',start,end));return {'data':[{'calendarDate':'1999-01-01'}]}
    api=Wrong();dest,r=Exporter(api,plan(tmp_path,end='2020-01-03')).run()
    assert r['completed'] and len(api.calls)==4
    assert all(x['data']['totalSteps']==1234 for x in json.loads(next(Path(dest).glob('summary*.json')).read_text()))


def test_rejected_statistics_range_uses_same_statistics_endpoint_daily(tmp_path):
    from garminconnect import GarminConnectConnectionError
    class Rejected(API):
        def get_daily_heart_rate_stats(self,start,end):
            self.calls.append(('stats',start,end))
            if start!=end:raise GarminConnectConnectionError('API Error 400')
            return [{'calendarDate':start,'value':57}]
    api=Rejected();r=Exporter(api,plan(tmp_path,datasets=['heart_rate'],health_detail='daily',end='2020-01-03')).run()[1]
    assert r['completed'] and len(api.calls)==4 and all(m=='stats' for m,_,_ in api.calls)


def test_empty_daily_series_cached_only_after_single_day_checks(tmp_path):
    class Empty(API):
        def get_daily_heart_rate_stats(self,start,end):self.calls.append((start,end));return []
    api=Empty();p=plan(tmp_path,datasets=['heart_rate'],health_detail='daily',end='2020-01-03')
    r=Exporter(api,p).run()[1];assert r['completed'] and r['stats']['empty']==3 and len(api.calls)==4
    api.calls.clear();r=Exporter(api,p).run()[1];assert r['completed'] and not api.calls


def test_daily_preview_bounded_and_does_not_download_full_history_or_create_cache(tmp_path):
    api=API();p=plan(tmp_path,datasets=['heart_rate'],health_detail='daily',preview_requests=1)
    result=Previewer(api,p).run_preview()
    assert result['requests']==1 and len(api.calls)==1 and api.calls[0][1:]==('2020-01-01','2020-01-01')
    assert result['groups'][0]['key']=='heart_rate-daily' and list(tmp_path.iterdir())==[]


def test_old_presets_preserve_full_detail_and_new_values_validated(tmp_path):
    p=plan(tmp_path);assert p.health_detail=='full' and p.health_batch_days==28
    assert selected_datasets(replace(p,datasets=['activities','hrv'],health_detail='daily'))==selected_datasets(replace(p,datasets=['activities','hrv']))
    for options in ({'health_detail':'invalid'},{'health_batch_days':29},{'health_batch_days':True}):
        with pytest.raises(ValueError):Exporter(API(),replace(p,**options))


def test_only_statistics_archive_reports_full_details_missing_and_repairs_target_requested_mode(tmp_path):
    p=plan(tmp_path,datasets=['heart_rate'],health_detail='daily',end='2020-01-02');api=API()
    assert ArchiveSync(api,p).run_sync()['report']['completed']
    missing=OfflineExporter(replace(p,source='offline',health_detail='full')).run()[1]
    assert not missing['completed'] and missing['stats']['errors']==2 and missing['transfer']['requests']==0
    tasks=repair_plan(p.archive_path,p.account,2,[],replace(p,end='2020-01-03'))
    assert len(tasks)==1 and tasks[0][:3]==('heart_rate-daily','2020-01-03','get_daily_heart_rate_stats')


def test_daily_health_browser_reads_statistics_without_detail_responses(tmp_path):
    from datahub import daily_health
    p=plan(tmp_path,datasets=['resting_hr'],health_detail='daily',end='2020-01-02')
    assert ArchiveSync(API(),p).run_sync()['report']['completed']
    with Archive(p.archive_path,readonly=True) as db:
        assert daily_health(db)==[{'date':'2020-01-01','resting_hr':57},{'date':'2020-01-02','resting_hr':57}]
