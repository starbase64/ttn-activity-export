import csv
import io
import json
import struct
import threading
import zipfile
from pathlib import Path
import pytest
from datahub import (parse_activity,load_archive,import_files,write_kml,trim_track,aggregate,
 backup_archive,validate_archive,write_csv,import_cache,similar_routes)
from archive import Archive,OfflineAccountMismatch
from engine import Plan,account_key,request_spec,Exporter
from offline import OfflineExporter,ArchiveSync
from demo_data import DemoGarmin
from repairs import repair_plan,RepairSync

GPX=b'''<?xml version="1.0"?><gpx version="1.1"><trk><name>Test &amp; Ride</name><type>cycling</type><trkseg>
<trkpt lat="51.10" lon="8.10"><time>2020-01-01T10:00:00Z</time></trkpt>
<trkpt lat="51.11" lon="8.11"><time>2020-01-01T10:10:00Z</time></trkpt></trkseg>
<trkseg><trkpt lat="51.12" lon="8.12"><time>2020-01-01T10:20:00Z</time></trkpt>
<trkpt lat="51.13" lon="8.13"><time>2020-01-01T10:30:00Z</time></trkpt></trkseg></trk></gpx>'''

def make_fit():
    # A real binary FIT session and two records with valid CRCs.
    from fitdecode.utils import compute_crc
    start=946771200  # FIT epoch, arbitrary valid date in 2019.
    session_fields=[(2,4,0x86),(5,1,0),(7,4,0x86),(8,4,0x86),(9,4,0x86),(14,2,0x84),(16,1,2)]
    payload=bytes([0x40,0,0])+struct.pack('<H',18)+bytes([len(session_fields)])+b''.join(bytes(x) for x in session_fields)
    payload+=b'\x00'+struct.pack('<IBIIIHB',start,2,600000,600000,250000,4200,140)
    record_fields=[(253,4,0x86),(0,4,0x85),(1,4,0x85)]
    payload+=bytes([0x41,0,0])+struct.pack('<H',20)+bytes([len(record_fields)])+b''.join(bytes(x) for x in record_fields)
    for i in range(2):payload+=b'\x01'+struct.pack('<Iii',start+i*600,int((51.1+i*.01)*2**31/180),int((8.1+i*.01)*2**31/180))
    header=struct.pack('<BBHI4s',14,0x20,2100,len(payload),b'.FIT');header+=struct.pack('<H',compute_crc(header))
    stream=header+payload
    return stream+struct.pack('<H',compute_crc(stream))

def p(tmp):return Plan('2020-01-01','2020-01-01',['activities'],str(tmp/'out'),account_key('test'),delay=0,refresh_days=0,archive_path=str(tmp/'data.sqlite'))

def test_real_fit_binary_decode_units_and_gpx_segment_gaps():
    summary,points=parse_activity(make_fit(),'fit')
    assert summary['distance']==2500 and summary['duration']==600 and summary['averageHR']==140
    assert summary['activityType']['typeKey']=='cycling'
    assert len(points)==2 and points[0][0]==pytest.approx(51.1,abs=.000001)
    summary,points=parse_activity(GPX,'gpx')
    assert summary['duration']==1800 and summary['activityName']=='Test & Ride'
    assert points[2] is None
    assert summary['distance']<4000  # No invented link between GPX segments.

def test_import_dedup_portable_reopen_offline_export_and_original_files(tmp_path):
    plan=p(tmp_path);file=tmp_path/'ride.gpx';file.write_bytes(GPX)
    r=import_files(plan.archive_path,[str(file)],plan.account)
    assert r['imported']==1 and not r['failed']
    assert import_files(plan.archive_path,[str(file)],plan.account)['duplicates']==1
    data=load_archive(plan.archive_path)
    assert len(data['activities'])==1 and len(next(iter(data['tracks'].values())))==5
    from dataclasses import replace
    dest,report=OfflineExporter(replace(plan,source='offline')).run()
    assert report['stats']['activities']==1 and report['stats']['downloaded']==0
    assert report['warnings']==['local_import_partial_day:2020-01-01']
    assert list(Path(dest).glob('activities*.csv'))
    backup=tmp_path/'backup.sqlite';backup_archive(plan.archive_path,backup)
    assert validate_archive(backup)['integrity']=='ok'
    assert load_archive(backup)['activities']==data['activities']
    with Archive(backup,readonly=True) as db:
        assert db.db.execute("SELECT COUNT(*) FROM responses WHERE is_binary=1").fetchone()[0]==1

def test_import_nested_garmin_zip_ignores_other_json_and_never_extracts_paths(tmp_path):
    nested=io.BytesIO()
    with zipfile.ZipFile(nested,'w') as z:z.writestr('../../ride.gpx',GPX)
    archive=tmp_path/'garmin-export.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('DI_CONNECT/DI-Connect-Fitness-Uploaded-Files/activity.zip',nested.getvalue())
        z.writestr('private.json','{}')
    plan=p(tmp_path);r=import_files(plan.archive_path,[archive],plan.account)
    assert r['imported']==1 and not r['failed']
    assert not (tmp_path/'ride.gpx').exists()

def test_import_rejects_entities_and_preserves_existing_on_cancel_or_wrong_account(tmp_path):
    plan=p(tmp_path);file=tmp_path/'bad.gpx';file.write_bytes(b'<!DOCTYPE x [<!ENTITY y SYSTEM "file:///etc/passwd">]><gpx/>')
    r=import_files(plan.archive_path,[file],plan.account)
    assert r['failed']==1 and not r['imported']
    with pytest.raises(OfflineAccountMismatch):import_files(plan.archive_path,[file],account_key('another'))
    cancel=threading.Event();cancel.set();r=import_files(plan.archive_path,[file],plan.account,cancel)
    assert r['cancelled'] and not r['failed']

def test_day_summary_units_aggregation_missing_values_and_csv_formula(tmp_path):
    plan=p(tmp_path)
    from dataclasses import replace
    plan=replace(plan,datasets=['summary','heart_rate','sleep'])
    ArchiveSync(DemoGarmin(),plan).run_sync()
    data=load_archive(plan.archive_path)
    assert data['health']==[{'date':'2020-01-01','steps':6240,'resting_hr':57,'calories':2340,'sleep_hours':7}]
    result=aggregate([{'_day':'2020-01-01','activityType':{'typeKey':'cycling'},'distance':10000,'duration':3600},
                      {'_day':'2020-01-02','activityType':{'typeKey':'cycling'},'distance':20000,'duration':7200}])
    assert result[0]['km']==30 and result[0]['hours']==3 and result[0]['ascent'] is None
    out=tmp_path/'safe.csv';write_csv(out,[{'name':'=1+1','km':1}])
    assert "'=1+1" in out.read_text(encoding='utf-8-sig')

def test_privacy_mask_splits_track_and_kml_escapes_name(tmp_path):
    pts=[(51.,8.),(51.01,8.),(51.02,8.),(51.01,8.),(51.,8.)]
    masked=trim_track(pts,100)
    assert masked[0]!=(51.,8.) and masked[-1] is None
    out=tmp_path/'share.kml';write_kml(out,[{'_key':'x','activityName':'A < B'}],{'x':pts},100)
    text=out.read_text();assert 'A &lt; B' in text and '8.0,51.0,0' not in text

def test_missing_gps_repair_checks_account_and_requests_only_selected_track(tmp_path):
    plan=p(tmp_path);ArchiveSync(DemoGarmin(),plan).run_sync();a=load_archive(plan.archive_path)['activities'][:1]
    tasks=repair_plan(plan.archive_path,plan.account,0,a,plan)
    assert len(tasks)==1 and tasks[0][2]=='download_activity'
    with pytest.raises(OfflineAccountMismatch):repair_plan(plan.archive_path,account_key('other'),0,a,plan)
    class API:
        def download_activity(self,ident,**kwargs):assert ident==a[0]['activityId'];return GPX
    result=RepairSync(API(),plan).run_tasks(tasks)
    assert result['report']['completed'] and result['report']['stats']['downloaded']==1
    assert not repair_plan(plan.archive_path,plan.account,0,a,plan)

def test_retry_failed_response_actually_refetches_and_clears_failure(tmp_path):
    plan=p(tmp_path)
    with Archive(plan.archive_path,plan.account) as db:
        req=request_spec('activities','get_activities_by_date',(plan.start,plan.start))
        db.put('activities',plan.start,req,[]);db.failed('activities',plan.start,req,RuntimeError(),None)
    tasks=repair_plan(plan.archive_path,plan.account,1,[],plan)
    api=DemoGarmin();result=RepairSync(api,plan).run_tasks(tasks)
    assert result['report']['stats']['downloaded']==1
    with Archive(plan.archive_path,readonly=True) as db:assert db.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0]==0

def test_cache_import_reuses_old_export_without_any_network(tmp_path):
    plan=p(tmp_path);Exporter(DemoGarmin(),plan).run()
    cache=Path(plan.output)/('account-'+plan.account)/'cache-v1'
    result=import_cache(plan.archive_path,cache,plan.account)
    assert result=={'responses':1,'errors':0}
    assert len(load_archive(plan.archive_path)['activities'])==30

def test_heatmap_counts_trips_not_gps_sample_count_and_similar_routes():
    from mapview import density_segments
    sparse=[(51,8),(51.01,8.01)]
    dense=[(51+i*.001,8+i*.001) for i in range(11)]
    counts,grid=density_segments([sparse,dense])
    assert max(counts.values())==2
    assert sum(v==2 for v in counts.values())>=min(len(counts)//2,2)
    a={'_key':'a','_day':'2020-01-01','activityName':'first'};b={'_key':'b','_day':'2021-01-01','activityName':'second'}
    matches=similar_routes([a,b],{'a':sparse,'b':dense})
    assert matches and matches[0]['trips']==2

def test_table_formats_preserve_numbers_and_escape_spreadsheet_formulas(tmp_path):
    from datahub import write_table
    from openpyxl import load_workbook
    rows=[{'name':'=1+1','km':12.5,'missing':None}]
    for fmt in ('csv','xlsx','json'):write_table(tmp_path/('data.'+fmt),rows,'de')
    assert '12,5' in (tmp_path/'data.csv').read_text(encoding='utf-8-sig')
    assert json.loads((tmp_path/'data.json').read_text())==rows
    book=load_workbook(tmp_path/'data.xlsx');sheet=book.active
    assert sheet['A2'].value=="'=1+1" and sheet['B2'].value==12.5 and sheet['C2'].value is None

def test_repair_rate_limit_stops_queue_and_retains_previous_data(tmp_path):
    from garminconnect import GarminConnectTooManyRequestsError
    plan=p(tmp_path);calls=[]
    class API:
        def get_user_summary(self,day):calls.append(day);raise GarminConnectTooManyRequestsError('private response excluded')
    tasks=[('summary','2020-01-01','get_user_summary',('2020-01-01',),{},''),('summary','2020-01-02','get_user_summary',('2020-01-02',),{},'')]
    result=RepairSync(API(),plan).run_tasks(tasks)
    assert calls==['2020-01-01'] and result['report']['fatal_diagnostic']['reason']=='rate_limit'
    assert 'private response' not in json.dumps(result)


def test_xml_dtd_is_refused_in_any_encoding():
    import pytest
    from datahub import parse_activity
    doc='<?xml version="1.0" encoding="{enc}"?><!DOCTYPE gpx [<!ENTITY a "AAAA"><!ENTITY b "&a;&a;&a;">]><gpx><trk><name>&b;</name><trkseg><trkpt lat="1" lon="1"><time>2020-01-01T10:00:00Z</time></trkpt></trkseg></trk></gpx>'
    for enc,codec in (('UTF-8','utf-8'),('UTF-16','utf-16'),('UTF-16','utf-16-le')):
        data=doc.format(enc=enc).encode(codec)
        with pytest.raises(Exception) as info:parse_activity(data,'gpx')
        assert 'declarations' in str(info.value) or 'ParseError' in type(info.value).__name__


def test_gpx_with_mixed_utc_and_naive_times_imports():
    from datahub import parse_activity
    gpx=b'<gpx><trk><trkseg><trkpt lat="1" lon="1"><time>2020-01-01T10:00:00Z</time></trkpt><trkpt lat="1.1" lon="1"><time>2020-01-01T10:10:00</time></trkpt></trkseg></trk></gpx>'
    summary,points=parse_activity(gpx,'gpx')
    assert summary['duration']==600 and summary['startTimeLocal'].startswith('2020-01-01T10:00:00') and len(points)==2
