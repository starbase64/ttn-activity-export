import csv
import json
import sqlite3
import threading
from dataclasses import replace
from pathlib import Path
import pytest
from archive import Archive,OfflineArchiveError,OfflineAccountMismatch
from offline import ArchiveSync,OfflineExporter,OfflinePreviewer
from engine import Plan,Exporter,account_key,request_spec
from demo_data import DemoGarmin


def plan(tmp_path,**kwargs):
    defaults=dict(start='2020-01-01',end='2020-01-02',datasets=['summary','heart_rate','sleep','activities'],
        output=str(tmp_path/'exports'),account=account_key('archive@example.invalid'),
        archive_path=str(tmp_path/'data.sqlite'),delay=0,refresh_days=0)
    return Plan(**(defaults|kwargs))


def test_sync_resume_self_contained_and_offline_export_without_network(tmp_path,monkeypatch):
    class Tracked(DemoGarmin):
        summaries=0
        def get_user_summary(self,day):
            self.summaries+=1;return super().get_user_summary(day)
    api=Tracked();p=plan(tmp_path)
    first=ArchiveSync(api,p).run_sync()
    assert first['report']['completed'] and api.summaries==2
    assert not (tmp_path/'exports').exists()  # No CSV or legacy cache copies.
    second=ArchiveSync(api,p).run_sync()
    assert second['report']['stats']['cached']==8 and api.summaries==2
    def forbidden(*a,**kw):raise AssertionError('No network allowed')
    monkeypatch.setattr('garminconnect.Garmin.connectapi',forbidden)
    monkeypatch.setattr('garminconnect.Garmin.login',forbidden)
    monkeypatch.setattr('garminconnect.Garmin.download',forbidden)
    offline=replace(p,source='offline',datasets=['activities'],activity_type='cycling',formats=['csv','xlsx','json'])
    destination,report=OfflineExporter(offline).run()
    assert report['completed'] and report['stats']['downloaded']==0 and report['stats']['activities']==60
    with next(Path(destination).glob('activities-*.csv')).open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f,delimiter=';'))
    assert len(rows)==60 and rows[0]['Distanz (km)']=='15,67'
    sample=OfflinePreviewer(offline).run_preview()
    assert sample['requests']==0 and len(sample['groups'][0]['rows'])==10


def test_existing_cache_is_imported_without_network(tmp_path):
    p=plan(tmp_path,datasets=['summary'])
    Exporter(DemoGarmin(),p).run()
    class Cached(DemoGarmin):
        def get_user_summary(self,day):raise AssertionError('Reuse successful local cache')
    result=ArchiveSync(Cached(),p).run_sync()
    assert result['report']['completed'] and result['report']['stats']['cached']==2
    with Archive(p.archive_path,readonly=True) as db:
        assert db.get('summary',p.start,request_spec('summary','get_user_summary',(p.start,)))['data']['totalSteps']==6240


def test_rate_limit_leaves_partial_database_and_missing_offline_data_is_explicit(tmp_path):
    from garminconnect import GarminConnectTooManyRequestsError
    class Limited(DemoGarmin):
        def get_user_summary(self,day):
            if day=='2020-01-02':raise GarminConnectTooManyRequestsError('limit')
            return super().get_user_summary(day)
    p=plan(tmp_path,datasets=['summary'])
    result=ArchiveSync(Limited(),p).run_sync()
    assert not result['report']['completed'] and result['report']['fatal_diagnostic']['reason']=='rate_limit'
    destination,report=OfflineExporter(replace(p,source='offline')).run()
    assert not report['completed'] and report['stats']['cached']==1 and report['stats']['errors']==1
    assert report['errors'][0]['error_type']=='OfflineDataMissing'


def test_archive_keeps_binary_and_activity_details(tmp_path):
    class Files(DemoGarmin):
        def search_activities(self,**kwargs):return super().search_activities(**kwargs)[:1] if kwargs.get('start',0)==0 else []
        def get_activity_laps(self,ident):return [{'distance':1000,'duration':90}]
        def download_activity(self,ident,dl_fmt):return b'archive-binary-test'
    p=plan(tmp_path,end='2020-01-01',datasets=['activities'],activity_details=['get_activity_laps'],activity_files=['ORIGINAL'])
    assert ArchiveSync(Files(),p).run_sync()['report']['completed']
    destination,report=OfflineExporter(replace(p,source='offline')).run()
    assert report['completed']
    assert next((Path(destination)/'activities').glob('*.zip')).read_bytes()==b'archive-binary-test'
    assert len(list(Path(destination).glob('activity-*-laps-*.csv')))==1
    _,report=OfflineExporter(replace(p,source='offline',activity_files=['GPX'])).run()
    assert not report['completed'] and report['errors'][0]['error_type']=='OfflineDataMissing'


def test_account_validation_and_unrelated_sqlite_are_protected(tmp_path):
    p=plan(tmp_path,datasets=['summary'])
    ArchiveSync(DemoGarmin(),p).run_sync()
    with pytest.raises(OfflineAccountMismatch):Archive(p.archive_path,account_key('other'))
    other=tmp_path/'unrelated.sqlite'
    con=sqlite3.connect(other);con.execute('CREATE TABLE valuable(x)');con.commit();con.close()
    before=other.read_bytes()
    with pytest.raises(OfflineArchiveError):Archive(other,p.account)
    assert other.read_bytes()==before


def test_empty_responses_are_preserved_and_coverage_is_not_a_completeness_claim(tmp_path):
    p=plan(tmp_path)
    with Archive(p.archive_path,p.account) as db:
        req=request_spec('summary','get_user_summary',(p.start,))
        db.put('summary',p.start,req,None)
        saved=db.get('summary',p.start,req)
        assert saved is not None and saved['data'] is None
        coverage=db.coverage(p.start,p.end)[0]
        assert coverage['stored_days']==1 and coverage['empty_responses']==1


def test_unsupported_category_does_not_abort_unrelated_sync(tmp_path):
    from garminconnect import GarminConnectConnectionError
    class Unsupported(DemoGarmin):
        calls=0
        def get_user_summary(self,day):
            self.calls+=1;raise GarminConnectConnectionError('API Error 400')
    p=plan(tmp_path,datasets=['summary','heart_rate'])
    api=Unsupported();result=ArchiveSync(api,p).run_sync()
    assert api.calls==1 and result['report']['stats']['errors']==1
    with Archive(p.archive_path,readonly=True) as db:
        assert db.samples('heart_rate',p.start,p.end,10) and not db.samples('summary',p.start,p.end,10)


def test_cancelled_sync_retains_readable_archive(tmp_path):
    stop=threading.Event();stop.set();p=plan(tmp_path)
    result=ArchiveSync(DemoGarmin(),p,stop).run_sync()
    assert result['report']['cancelled']
    with Archive(p.archive_path,readonly=True) as db:assert db.account==p.account
