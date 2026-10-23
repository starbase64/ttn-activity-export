import csv
import json
import threading
from pathlib import Path
from demo_data import DemoGarmin
from engine import Plan, Exporter, account_key
from preview import Previewer


def plan(tmp_path,**kwargs):
    values=dict(start='2000-01-01',end='2020-12-31',datasets=['activities'],output=str(tmp_path),
                account=account_key('preview@example.invalid'),preview_rows=5,preview_requests=4,delay=0)
    return Plan(**(values|kwargs))


def test_activity_preview_is_bounded_and_writes_nothing(tmp_path,monkeypatch):
    class Fake(DemoGarmin):
        calls=[]
        def search_activities(self,**kwargs):
            self.calls.append(kwargs)
            return super().search_activities(**kwargs)
        def download_activity(self,*a,**kw):raise AssertionError('No binary downloads')
    monkeypatch.setattr(Exporter,'run',lambda *a: (_ for _ in ()).throw(AssertionError('No full export')))
    monkeypatch.setattr(Exporter,'retrieve',lambda *a: (_ for _ in ()).throw(AssertionError('No file cache')))
    p=plan(tmp_path,activity_type='e_bike_mountain',activity_files=['GPX'])
    result=Previewer(Fake(),p).run_preview()
    assert result['requests']==2 and len(Fake.calls)==1
    assert Fake.calls[0]['limit']==20
    assert Fake.calls[0]['startDate']=='2000-01-01'
    assert len(result['groups'][0]['rows'])==5
    assert result['groups'][0]['rows'][0]['Distanz (km)']=='15,67'
    assert 'files_not_downloaded' in result['notes']
    assert list(tmp_path.iterdir())==[]


def test_sparse_many_years_does_not_scan_entire_range(tmp_path):
    class Empty(DemoGarmin):
        def search_activities(self,**kwargs):return []
    result=Previewer(Empty(),plan(tmp_path)).run_preview()
    assert result['requests']==1 and not result['groups'][0]['rows']
    result=Previewer(DemoGarmin(),plan(tmp_path,datasets=['summary'],preview_rows=50)).run_preview()
    assert result['requests']==3
    assert list(tmp_path.iterdir())==[]


def test_budget_stops_pages_and_keeps_partial_samples(tmp_path):
    class Capped(DemoGarmin):
        offsets=[]
        def search_activities(self,start=0,**kwargs):
            self.offsets.append(start)
            return super().search_activities(start=start,limit=2,startDate='2000-01-01')
    result=Previewer(Capped(),plan(tmp_path,preview_requests=2)).run_preview()
    assert result['requests']==2 and result['budget_reached']
    assert Capped.offsets==[0,2]
    assert len(result['groups'][0]['rows'])==4


def test_preview_matches_export_and_field_selection(tmp_path):
    p=plan(tmp_path,start='2020-01-01',end='2020-01-01',selectors=['/activityName','/distance'])
    result=Previewer(DemoGarmin(),p).run_preview()
    destination,report=Exporter(DemoGarmin(),p).run()
    assert report['completed']
    with next(Path(destination).glob('activities-*.csv')).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,delimiter=';');export=list(reader)
    sample=result['groups'][0]
    assert sample['fields']==reader.fieldnames
    assert sample['rows']==export[:5]


def test_health_error_cancel_and_expert_are_safe(tmp_path):
    from garminconnect import GarminConnectConnectionError
    class Fail(DemoGarmin):
        def get_user_summary(self,*args):raise GarminConnectConnectionError('API Error 400 - private message')
    result=Previewer(Fail(),plan(tmp_path,datasets=['summary'],preview_requests=1)).run_preview()
    assert result['errors'][0]['http_status']==400
    assert 'private message' not in json.dumps(result['errors'])
    stop=threading.Event();stop.set()
    result=Previewer(DemoGarmin(),plan(tmp_path),stop).run_preview()
    assert result['cancelled'] and result['requests']==0
    result=Previewer(DemoGarmin(),plan(tmp_path,datasets=[],expert_method='get_activities_by_date')).run_preview()
    assert result['requests']==0 and 'expert_not_sampled' in result['notes']


def test_json_preview_is_truncated_not_an_entire_history(tmp_path):
    p=plan(tmp_path,formats=['json'])
    result=Previewer(DemoGarmin(),p).run_preview()
    assert len(result['groups'][0]['raw'][0]['data'])==5
    assert list(tmp_path.iterdir())==[]


def test_goal_preview_requests_only_one_page(tmp_path):
    class Goals:
        garmin_connect_goals_url='/goal-service/goals'
        calls=[]
        def get_goals(self,*a,**kw):raise AssertionError('Do not auto-paginate all goals')
        def connectapi(self,url,**kwargs):
            self.calls.append(kwargs)
            return [{'id':i,'title':'Example'} for i in range(5)]
    api=Goals()
    result=Previewer(api,plan(tmp_path,datasets=['goals'])).run_preview()
    assert result['requests']==1 and len(api.calls)==1
    assert api.calls[0]['params']['limit']=='5'
    assert len(result['groups'][0]['rows'])==5
    assert list(tmp_path.iterdir())==[]
