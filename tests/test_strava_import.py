"""Synthetic user-downloaded archives: no Strava account or network is used."""
import csv
import gzip
import io
import json
import socket
import threading
import zipfile
from dataclasses import replace
from pathlib import Path
import pytest
from strava_import import import_strava_archive,row_summary,prepare_source
from datahub import load_archive
from archive import Archive,OfflineAccountMismatch
from engine import Plan,account_key
from offline import OfflineExporter
from tests.test_datahub import make_fit,GPX

HEADERS=['Activity ID','Activity Date','Activity Name','Activity Type','Elapsed Time','Distance','Filename','Elapsed Time','Moving Time','Distance','Elevation Gain']

def row(ident='123',name='Morning Ride',filename='activities/123.fit.gz'):
    return [ident,'Jan 1, 2020, 10:00:00 AM',name,'Ride','600','2.50',filename,'600.0','600.0','2500.0','42.0']

def package(path,rows,files=None,prefix=''):
    text=io.StringIO(newline='');writer=csv.writer(text);writer.writerow(HEADERS);writer.writerows(rows)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr(prefix+'activities.csv',text.getvalue())
        for name,data in (files or {}).items():z.writestr(prefix+name,data)
    return path


def test_folder_and_zip_produce_same_data_and_keep_sources(tmp_path):
    source=package(tmp_path/'strava.zip',[row()],{'activities/123.fit.gz':gzip.compress(make_fit())})
    folder=tmp_path/'unpacked'
    with zipfile.ZipFile(source) as z:z.extractall(folder)  # Trusted synthetic fixture only.
    account=account_key('strava:mine')
    for name,src in [('zip',source),('folder',folder)]:
        selected=prepare_source(src,tmp_path/'sources',False)
        assert selected==src and not (tmp_path/'sources').exists()
        report=import_strava_archive(tmp_path/(name+'.sqlite'),selected,account)
        assert report['imported']==1 and report['files']==1 and not report['failed']
    a=load_archive(tmp_path/'zip.sqlite');b=load_archive(tmp_path/'folder.sqlite')
    assert a['activities']==b['activities'] and a['tracks']==b['tracks']
    assert (folder/'activities.csv').is_file() and source.is_file()


def test_source_copy_is_complete_isolated_and_cancellable(tmp_path,monkeypatch):
    import strava_import
    source=package(tmp_path/'source.zip',[row(filename='')],{'photos/example.jpg':b'photo'})
    folder=tmp_path/'folder'
    with zipfile.ZipFile(source) as z:z.extractall(folder)
    for src in (source,folder):
        retained=prepare_source(src,tmp_path/'app-sources',True)
        assert retained!=src and retained.exists()
        if src.is_file():assert retained.read_bytes()==src.read_bytes()
        else:assert (retained/'photos/example.jpg').read_bytes()==b'photo'
    before=set((tmp_path/'app-sources').iterdir());cancel=threading.Event();cancel.set()
    with pytest.raises(InterruptedError):prepare_source(folder,tmp_path/'app-sources',True,cancel)
    assert set((tmp_path/'app-sources').iterdir())==before
    with pytest.raises(ValueError):prepare_source(folder,folder/'nested',True)
    monkeypatch.setattr(strava_import,'MAX_TOTAL',1)
    with pytest.raises(ValueError):prepare_source(source,tmp_path/'app-sources',True)
    assert set((tmp_path/'app-sources').iterdir())==before


def test_folder_does_not_follow_linked_recordings(tmp_path):
    source=package(tmp_path/'source.zip',[row(filename='activities/link.gpx')])
    folder=tmp_path/'folder'
    with zipfile.ZipFile(source) as z:z.extractall(folder)
    (folder/'activities').mkdir();outside=tmp_path/'outside.gpx';outside.write_bytes(GPX)
    try:(folder/'activities/link.gpx').symlink_to(outside)
    except OSError:pytest.skip('Symbolic links unavailable')
    result=import_strava_archive(tmp_path/'db.sqlite',folder,account_key('strava:mine'))
    assert result['imported']==1 and result['failed']==1 and result['files']==0
    copied=prepare_source(folder,tmp_path/'retained',True)
    assert not (copied/'activities/link.gpx').exists()


def test_full_zip_gzip_and_manual_metadata_are_imported_offline(tmp_path,monkeypatch):
    source=package(tmp_path/'strava.zip',[row(),row('456','Manual','')],{'activities/123.fit.gz':gzip.compress(make_fit())})
    target=tmp_path/'strava.sqlite';account=account_key('strava:mine')
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:pytest.fail('No network allowed'))
    report=import_strava_archive(target,source,account)
    assert report['imported']==2 and report['files']==1 and report['failed']==0
    data=load_archive(target);assert len(data['activities'])==2
    ride=next(a for a in data['activities'] if a['sourceActivityId']=='123')
    assert ride['activityId']<0 and ride['distance']==2500 and ride['duration']==600
    assert ride['sourceProvider']=='strava' and ride['sourceTimeZone']=='unspecified'
    assert len(data['tracks'][ride['_key']])==2
    assert len([a for a in ride['stravaCsv'] if a[0]=='Distance'])==2
    assert source.is_file()


def test_repeat_import_updates_titles_without_duplicate_activities(tmp_path):
    target=tmp_path/'db.sqlite';account=account_key('strava:mine')
    source=package(tmp_path/'export.zip',[row()],{'activities/123.fit.gz':gzip.compress(make_fit())})
    import_strava_archive(target,source,account)
    source=package(source,[row(name='Edited title')],{'activities/123.fit.gz':gzip.compress(make_fit())})
    report=import_strava_archive(target,source,account)
    assert report['imported']==0 and report['duplicates']==1
    data=load_archive(target);assert len(data['activities'])==1 and data['activities'][0]['activityName']=='Edited title'
    with Archive(target,readonly=True) as db:assert db.db.execute('SELECT COUNT(*) FROM responses WHERE is_binary=1').fetchone()[0]==1


def test_imported_strava_activities_export_with_correct_link_units_and_csv_safety(tmp_path):
    target=tmp_path/'strava.sqlite';account=account_key('strava:mine')
    source=package(tmp_path/'export.zip',[row(name='=SUM(1,2)')],{'activities/123.fit.gz':gzip.compress(make_fit())})
    import_strava_archive(target,source,account)
    p=Plan('2020-01-01','2020-01-01',['activities'],str(tmp_path/'out'),account,archive_path=str(target),source='offline',delay=0,formats=['csv'])
    folder,report=OfflineExporter(p).run();assert report['completed']
    with next(Path(folder).glob('activities*.csv')).open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f,delimiter=';'))
    assert len(rows)==1 and rows[0]['Aktivität'].startswith("'=")
    assert rows[0]['Aktivitäts-Link']=='https://www.strava.com/activities/123'
    assert rows[0]['Distanz (km)']=='2,5'


def test_nested_root_and_gpx_are_supported(tmp_path):
    source=package(tmp_path/'archive.zip',[row(filename='activities/123.gpx')],{'activities/123.gpx':GPX},prefix='export/')
    target=tmp_path/'db.sqlite';r=import_strava_archive(target,source,account_key('strava:mine'))
    assert r['files']==1 and r['failed']==0 and len(next(iter(load_archive(target)['tracks'].values())))==5


def test_missing_or_corrupt_file_preserves_activity_metadata(tmp_path):
    source=package(tmp_path/'archive.zip',[row(),row('456',filename='activities/456.gpx')],{'activities/456.gpx':b'not xml'})
    target=tmp_path/'db.sqlite';r=import_strava_archive(target,source,account_key('strava:mine'))
    assert r['imported']==2 and r['failed']==2 and r['files']==0
    assert len(load_archive(target)['activities'])==2


def test_gzip_limit_is_bounded_and_path_traversal_never_extracts(tmp_path,monkeypatch):
    import strava_import as module
    monkeypatch.setattr(module,'MAX_FILE',1024)
    source=package(tmp_path/'archive.zip',[row(filename='activities/bomb.fit.gz'),row('456',filename='../outside.gpx')],
                   {'activities/bomb.fit.gz':gzip.compress(b'x'*2048),'../outside.gpx':GPX})
    r=import_strava_archive(tmp_path/'db.sqlite',source,account_key('strava:mine'))
    assert r['failed']==2 and r['imported']==2 and r['files']==0
    assert not (tmp_path.parent/'outside.gpx').exists()


def test_cancellation_keeps_prior_rows_and_resume_is_idempotent(tmp_path):
    source=package(tmp_path/'archive.zip',[row(filename=''),row('456',filename='')]);target=tmp_path/'db.sqlite';account=account_key('strava:mine')
    cancel=threading.Event()
    r=import_strava_archive(target,source,account,cancel,event=lambda *a:cancel.set())
    assert r['cancelled'] and r['imported']==1 and len(load_archive(target)['activities'])==1
    r=import_strava_archive(target,source,account)
    assert r['imported']==1 and r['duplicates']==1 and len(load_archive(target)['activities'])==2


def test_bad_manifest_is_rejected_before_creating_database_and_account_mismatch_is_safe(tmp_path):
    bad=tmp_path/'bad.zip'
    with zipfile.ZipFile(bad,'w') as z:z.writestr('activities.csv','Wrong,Headers\n1,2')
    target=tmp_path/'db.sqlite'
    with pytest.raises(ValueError):import_strava_archive(target,bad,account_key('strava:mine'))
    assert not target.exists()
    with Archive(target,account_key('garmin:other')):pass
    source=package(tmp_path/'valid.zip',[row(filename='')])
    with pytest.raises(OfflineAccountMismatch):import_strava_archive(target,source,account_key('strava:mine'))
    assert not load_archive(target)['activities']


def test_single_ambiguous_distance_column_is_preserved_without_unit_guess():
    summary=row_summary(['Activity ID','Activity Date','Activity Name','Activity Type','Distance'],['1','2020-01-01T10:00:00Z','Walk','Walk','12'])
    assert 'distance' not in summary and summary['sourceTimeZone']=='explicit'
    assert summary['stravaCsv'][-1]==('Distance','12')
