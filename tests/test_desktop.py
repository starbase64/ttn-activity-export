"""Regression coverage for the compact shell, inventory and persisted job snapshots."""
import json
import threading
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import pytest
from PySide6.QtCore import QEvent,QDate,Qt,QStandardPaths
from PySide6.QtWidgets import QApplication,QDialog,QLineEdit,QTableWidget
from PySide6.QtTest import QTest
from app import DesktopWindow
from archive import Archive
from engine import Plan,account_key
from workspace_state import Workspace
from inventory import read_inventory
from demo_data import DemoGarmin
from offline import ArchiveExporter,OfflineExporter,ArchiveSync

QT_APP=QApplication.instance() or QApplication([])

@pytest.fixture
def window(tmp_path,monkeypatch):
    native=QStandardPaths.writableLocation
    monkeypatch.setattr(QStandardPaths,'writableLocation',lambda key:str(tmp_path/'profile') if key==QStandardPaths.StandardLocation.AppLocalDataLocation else native(key))
    w=DesktopWindow(demo=True)
    w.delay.setValue(0);w.refresh.setValue(0);w.workers.setValue(1)
    w.message=lambda *a:pytest.fail('Unexpected dialog: '+str(a))
    yield w
    if w.worker and w.worker.isRunning():w.worker.cancel.set();w.worker.wait(5000)
    for dialog in w.findChildren(QDialog):dialog.close()
    w.close();w.deleteLater();QApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()


def test_workspace_preserves_snapshots_and_never_restarts_running_jobs(tmp_path):
    path=tmp_path/'workspace.json';store=Workspace(path)
    a=store.add_account('garmin','a@example.invalid',tmp_path/'Garmin')
    p=Plan('2020-01-01','2020-01-01',['activities'],str(tmp_path),a['id'],activity_ids=['123'])
    j=store.enqueue(a,p,'download');p.activity_ids.append('456');p.datasets.clear()
    assert j['plan']['activity_ids']==['123'] and j['plan']['datasets']==['activities']
    j['status']='running';store.save();loaded=Workspace(path)
    assert loaded.jobs[0]['status']=='interrupted'
    assert not {'password','secret','token'}&set(loaded.accounts[0])
    other=store.add_account('strava','a@example.invalid',tmp_path/'Strava')
    assert other['id']!=a['id']
    with pytest.raises(ValueError):store.enqueue(other,replace(p,account=other['id'],datasets=['activities']),'download')


def test_inventory_is_metadata_only_bounded_and_resumable():
    class API:
        def __init__(self):self.calls=[]
        def search_activities(self,**kw):
            self.calls.append(kw)
            if kw['start']>=3:return []
            return [{'activityId':kw['start']+1,'activityName':'Trip','startTimeLocal':'2020-01-01 10:00:00',
                     'activityType':{'typeKey':'cycling'},'secretExtra':'not in inventory','summaryPolyline':{'points':'not copied'}}]
        def get_activity_details(self,*a):pytest.fail('No details in inventory')
        def download_activity(self,*a):pytest.fail('No files in inventory')
    api=API();r=read_inventory(api,'2020-01-01','2020-01-02',pages=2,interval=0)
    assert len(r['items'])==2 and not r['complete'] and r['offset']==2
    assert 'secretExtra' not in r['items'][0] and 'summaryPolyline' not in r['items'][0]
    r=read_inventory(api,'2020-01-01','2020-01-02',previous=r,pages=2,interval=0)
    assert r['complete'] and len(r['items'])==3
    assert [q['start'] for q in api.calls]==[0,1,2,3]


def test_inventory_retains_success_on_error_without_claiming_complete():
    from garminconnect import GarminConnectTooManyRequestsError
    class API:
        def search_activities(self,**kw):
            if kw['start']:raise GarminConnectTooManyRequestsError('429')
            return [{'activityId':1}]
    events=[];r=read_inventory(API(),'2020-01-01','2020-01-01',interval=0,event=lambda *a:events.append(a))
    assert len(r['items'])==1 and not r['complete'] and r['offset']==1
    assert r['error']['reason']=='rate_limit' and any(e[0]=='rate_limit' for e in events)


def test_repeated_page_is_partial_and_cancellation_does_not_advance():
    api=SimpleNamespace(search_activities=lambda **kw:[{'activityId':1}])
    r=read_inventory(api,'2020-01-01','2020-01-01',interval=0)
    assert not r['complete'] and r['offset']==1 and r['error']
    cancel=threading.Event();cancel.set()
    r=read_inventory(api,'2020-01-01','2020-01-01',cancel=cancel)
    assert r['requests']==0 and r['cancelled']


def test_activity_id_selection_filters_downloads_and_offline_reuse(tmp_path):
    class API(DemoGarmin):
        def __init__(self):self.details=[]
        def get_activity_laps(self,ident):self.details.append(str(ident));return {'activityId':ident,'lapDTOs':[]}
    api=API();p=Plan('2020-01-01','2020-01-01',['activities'],str(tmp_path/'out'),account_key('selection'),
        archive_path=str(tmp_path/'archive.sqlite'),formats=['json'],delay=0,refresh_days=0,
        activity_ids=['2020010101'],activity_details=['get_activity_laps'])
    dest,r=ArchiveExporter(api,p).run()
    assert r['completed'] and api.details==['2020010101']
    data=json.loads((Path(dest)/'activities-2020.json').read_text())
    assert len(data[0]['data'])==1 and str(data[0]['data'][0]['activityId'])=='2020010101'
    # All summary responses stay cached, allowing another selection without corrupting source coverage.
    other=replace(p,source='offline',activity_ids=['2020010102'],activity_details=[])
    dest,r=OfflineExporter(other).run()
    assert r['completed'] and r['output_stats']['reused']==0
    data=json.loads((Path(dest)/'activities-2020.json').read_text())
    assert str(data[0]['data'][0]['activityId'])=='2020010102'


def test_compact_tabs_dialogs_and_translations_preserve_unsaved_choice(window,tmp_path):
    w=window
    assert [w.tabs.tabText(i) for i in range(4)]==['Konten','Download','Daten','Anleitung']
    assert w.option_tabs.count()==5 and w.account_list.count()==1
    w.output.setText(str(tmp_path/'custom'));w.dataset_checks['heart_rate'].setChecked(True)
    before=w.make_plan();w.toggle_language();after=w.make_plan()
    assert w.output.text()==str(tmp_path/'custom') and w.dataset_checks['heart_rate'].isChecked()
    assert w.tabs.tabText(0)=='Accounts' and w.tabs.tabText(3)=='User guide'
    after.language=before.language;assert after==before
    assert w.subtitle.text()=='Your activities. Your data. All local.'


def test_account_defaults_and_clients_are_isolated(window,tmp_path):
    w=window;first=w.active_account
    w.output.setText(str(tmp_path/'first'));w.workers.setValue(7);w.save_account_defaults()
    second=w.workspace.add_account('garmin','second@example.invalid',tmp_path/'second')
    w.refresh_accounts(second['id']);assert not w.api and w.workers.value()==3
    w.refresh_accounts(first['id']);assert w.api and w.workers.value()==7
    assert w.output.text()==str(tmp_path/'first')
    assert w.account_picker.currentData()==first['id']


def test_enqueue_takes_snapshot_and_review_does_not_start_work(window,monkeypatch):
    w=window;w.start_date.setDate(QDate(2020,1,1));w.end_date.setDate(QDate(2020,1,1))
    w.selected_activity_ids=['2020010101'];w.enqueue_current()
    assert len(w.workspace.jobs)==1 and w.workspace.jobs[0]['plan']['activity_ids']==['2020010101']
    w.selected_activity_ids=['2020010102'];w.delay.setValue(2)
    assert w.workspace.jobs[0]['plan']['delay']==0
    monkeypatch.setattr(QDialog,'exec',lambda self:QDialog.DialogCode.Rejected)
    monkeypatch.setattr(w,'run_worker',lambda *a,**k:pytest.fail('Review must not start work'))
    w.review_jobs();assert w.workspace.jobs[0]['status']=='queued'


def test_queue_executes_stored_plan_without_later_ui_changes(window):
    w=window;w.start_date.setDate(QDate(2020,1,1));w.end_date.setDate(QDate(2020,1,1))
    w.selected_activity_ids=['2020010101'];w.enqueue_current();j=w.workspace.jobs[0]
    w.start_date.setDate(QDate(2021,1,1));w.selected_activity_ids=[]
    w._queue_active=True;w._run_ids=[j['id']];w.queue_next()
    deadline=time.monotonic()+5
    while w._queue_active and time.monotonic()<deadline:QTest.qWait(20)
    assert not w._queue_active and j['status']=='complete'
    from archive import Archive
    with Archive(j['plan']['archive_path'],readonly=True) as db:
        rows=db.db.execute("SELECT day FROM responses WHERE dataset='activities'").fetchall()
        assert rows and all(row['day']=='2020-01-01' for row in rows)


def test_missing_login_job_waits_but_does_not_block_ready_job(window,tmp_path):
    w=window;w.start_date.setDate(QDate(2020,1,1));w.end_date.setDate(QDate(2020,1,1));w.enqueue_current()
    good=w.workspace.jobs[0]
    other=w.workspace.add_account('garmin','not-connected@example.invalid',tmp_path/'other')
    plan=Plan('2020-01-01','2020-01-01',['activities'],str(tmp_path/'other'),other['id'])
    waiting=w.workspace.enqueue(other,plan,'download');w.workspace.jobs.reverse()
    w._queue_active=True;w._run_ids=[waiting['id'],good['id']];w.queue_next()
    deadline=time.monotonic()+5
    while w._queue_active and time.monotonic()<deadline:QTest.qWait(20)
    assert waiting['status']=='waiting' and good['status']=='complete'


def test_options_cancel_restores_changes_and_apply_keeps_them(window):
    w=window;original=w.make_plan();w.show_options();w.workers.setValue(19);w.dataset_checks['sleep'].setChecked(True);w.archive_original.setChecked(False)
    w.options_dialog.reject()
    assert w.make_plan()==original and w.archive_original.isChecked()
    w.show_options();w.workers.setValue(17);w.options_dialog.accept()
    assert w.make_plan().workers==17
    w.options_dialog.close();assert w.make_plan().workers==17


def test_inventory_selection_applies_only_chosen_ids(window):
    w=window;r=read_inventory(DemoGarmin(),'2020-01-01','2020-01-01',interval=0,pages=1);r['account']=w.active_account['id']
    w.show();w.open_inventory_dialog(r);dialog=w.inventory_dialog;QApplication.processEvents();table=dialog.findChild(QTableWidget)
    assert table.rowCount()==30
    index=table.model().index(3,1)
    QTest.mouseClick(table.viewport(),Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,table.visualRect(index).center())
    assert len(table.selectionModel().selectedRows())==1
    from PySide6.QtWidgets import QPushButton
    button=next(b for b in dialog.findChildren(QPushButton) if b.text()=='Auswahl übernehmen');button.click()
    assert w.selected_activity_ids==['2020010104']
    assert w.make_plan().activity_ids==['2020010104']


def test_inventory_fits_all_content_and_keeps_manual_layout(window):
    from PySide6.QtWidgets import QHeaderView
    w=window;r=read_inventory(DemoGarmin(),'2020-01-01','2020-01-01',interval=0,pages=1);r['account']=w.active_account['id']
    r['items'][-1]['activityName']='A very long activity name '+('X'*220)
    w.open_inventory_dialog(r);dialog=w.inventory_dialog;QApplication.processEvents();table=dialog.findChild(QTableWidget)
    header=table.horizontalHeader()
    assert dialog.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint
    assert header.sectionsMovable() and header.sectionResizeMode(1)==QHeaderView.ResizeMode.Interactive
    assert table.columnWidth(1)>1000 and table.horizontalScrollBar().maximum()>0
    header.resizeSection(1,350);header.moveSection(1,0)
    search=dialog.findChild(QLineEdit);search.setText('2020')
    assert table.columnWidth(1)==350 and header.visualIndex(1)==0


def test_cache_button_finds_database_without_opening_file_picker(window,tmp_path,monkeypatch):
    from engine import account_root
    from PySide6.QtWidgets import QFileDialog
    w=window;a=w.active_account;path=account_root(a['output'],a['id'])/'garmin-offline.sqlite'
    with Archive(path,a['id']) as db:
        db.put('activities','2020-01-01',{'import':'activity-files-v1'},[{'activityId':123,'activityName':'Cached ride','startTimeLocal':'2020-01-01T10:00:00','activityType':{'typeKey':'cycling'}}])
    monkeypatch.setattr(QFileDialog,'getExistingDirectory',lambda *a,**k:pytest.fail('Unexpected manual cache picker'))
    monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *a,**k:pytest.fail('Unexpected archive picker'))
    w.data_page.import_cache_dialog();deadline=time.monotonic()+5
    while not w.data_page.data['activities'] and time.monotonic()<deadline:QTest.qWait(20)
    assert w.archive_path.text()==str(path) and len(w.data_page.data['activities'])==1 and not w.request_count


def test_cache_button_opens_manual_picker_only_after_no_match(window,tmp_path,monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    w=window;native=QStandardPaths.writableLocation
    monkeypatch.setattr(QStandardPaths,'writableLocation',lambda key:str(tmp_path/'Downloads') if key==QStandardPaths.StandardLocation.DownloadLocation else native(key))
    called=[];monkeypatch.setattr(QFileDialog,'getExistingDirectory',lambda *a,**k:(called.append(True) or ''))
    w.data_page.import_cache_dialog();deadline=time.monotonic()+5
    while not called and time.monotonic()<deadline:QTest.qWait(20)
    assert called==[True] and not w.request_count


def test_cache_button_imports_legacy_responses_without_picker(window,tmp_path,monkeypatch):
    from engine import account_root
    from PySide6.QtWidgets import QFileDialog
    w=window;a=w.active_account;root=account_root(a['output'],a['id'])
    file=root/'cache-v1/activities/2020/2020-01-01-test.json';file.parent.mkdir(parents=True)
    file.write_text(json.dumps({'request':{},'data':[{'activityId':456,'activityName':'Old cache ride','startTimeLocal':'2020-01-01T10:00:00','activityType':{'typeKey':'cycling'}}]}))
    messages=[];w.message=lambda *args:messages.append(args)
    monkeypatch.setattr(QFileDialog,'getExistingDirectory',lambda *a,**k:pytest.fail('Unexpected manual picker'))
    w.data_page.import_cache_dialog();deadline=time.monotonic()+5
    while not w.data_page.data['activities'] and time.monotonic()<deadline:QTest.qWait(20)
    assert messages and len(w.data_page.data['activities'])==1 and not w.request_count
    assert (root/'garmin-offline.sqlite').is_file() and file.is_file()


def test_komoot_download_is_account_isolated_and_not_blocked_by_garmin_pause(window,tmp_path):
    from komoot_client import KomootClient,tour_summary
    from tests.test_komoot import tour
    from tests.test_datahub import GPX
    w=window;a=w.workspace.add_account('komoot','test@example.invalid',tmp_path/'Komoot');w.refresh_accounts(a['id'])
    assert not w.komoot_panel.isHidden() and w.garmin_controls.isHidden()
    client=KomootClient(tmp_path/'komoot-pause.json',lambda *args:GPX);client.user='42';client.token='not-persisted'
    w.komoot_clients[a['id']]=client;w.refresh_accounts(a['id'])
    assert 'angemeldet' in w.connection.text()
    w.rate_pause.record({'reason':'rate_limit','retry_after_seconds':60})
    w.start_komoot_download(a,[tour_summary(tour())],True)
    deadline=time.monotonic()+5
    while not w.data_page.data['activities'] and time.monotonic()<deadline:QTest.qWait(20)
    assert len(w.data_page.data['activities'])==1 and w.data_page.data['account']==a['id']
    assert w.tabs.currentIndex()==2 and w.request_count==0
    assert 'not-persisted' not in w.workspace.path.read_text()


def test_preflight_reads_cache_without_requests_and_missing_selection_is_reported(tmp_path):
    from preflight import inspect_plan
    p=Plan('2020-01-01','2020-01-01',['activities'],str(tmp_path/'out'),account_key('preflight'),archive_path=str(tmp_path/'archive.sqlite'),delay=0,refresh_days=0)
    class API(DemoGarmin):
        calls=0
        def search_activities(self,**kw):self.calls+=1;return super().search_activities(**kw)
    api=API();before=inspect_plan(p,api);assert before['cached']==0 and before['pending']==1 and api.calls==0
    ArchiveSync(api,p).run_sync();calls=api.calls
    after=inspect_plan(p,api);assert after['cached']==1 and after['pending']==0 and api.calls==calls
    _,r=OfflineExporter(replace(p,source='offline',activity_ids=['9999999999'])).run()
    assert not r['completed'] and any(e['error_type']=='SelectedActivityMissing' for e in r['errors'])


def test_closed_inventory_does_not_leave_deleted_translation_widgets(window):
    w=window;r=read_inventory(DemoGarmin(),'2020-01-01','2020-01-01',interval=0,pages=1);r['account']=w.active_account['id']
    w.open_inventory_dialog(r);w.inventory_dialog.close()
    QApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()
    w.toggle_language();assert w.lang=='en'


def test_fresh_desktop_starts_with_empty_accounts_and_no_remote_requests(monkeypatch,tmp_path):
    from PySide6.QtCore import QStandardPaths
    native=QStandardPaths.writableLocation
    monkeypatch.setattr(QStandardPaths,'writableLocation',lambda kind:str(tmp_path) if kind==QStandardPaths.StandardLocation.AppLocalDataLocation else native(kind))
    w=DesktopWindow()
    assert w.account_list.count()==0 and w.tabs.currentIndex()==0 and w.api is None
    w.tooltip_checkbox.setChecked(False);w.close()
    assert not Workspace(tmp_path/'workspace.json').data['tooltips']


def test_archive_actions_also_require_review(window,monkeypatch):
    w=window;w.start_date.setDate(QDate(2020,1,1));w.end_date.setDate(QDate(2020,1,1))
    monkeypatch.setattr(QDialog,'exec',lambda self:QDialog.DialogCode.Rejected)
    w.start_archive_sync()
    j=w.workspace.jobs[0]
    assert j['status']=='queued' and j['action']=='download' and len(j['plan']['datasets'])==27
    assert j['plan']['activity_ids']==[] and j['plan']['delay']>=.25 and not w._queue_active


def test_failed_workspace_save_never_leaves_an_unconfirmed_job(tmp_path,monkeypatch):
    state=Workspace(tmp_path/'workspace.json');a=state.add_account('garmin','a@example.invalid',tmp_path)
    p=Plan('2020-01-01','2020-01-01',['activities'],str(tmp_path),a['id'])
    def full_disk():raise OSError('disk full')
    monkeypatch.setattr(state,'save',full_disk)
    with pytest.raises(OSError):state.enqueue(a,p,'download')
    assert not state.jobs
    with pytest.raises(OSError):state.add_account('garmin','other@example.invalid',tmp_path)
    assert len(state.accounts)==1 and not Workspace(state.path).jobs


def test_strava_is_import_only_and_local_import_works_during_garmin_pause(window,tmp_path):
    from tests.test_strava_import import package,row
    w=window;account=w.workspace.add_account('strava','local-strava',tmp_path/'Strava');w.refresh_accounts(account['id'])
    assert not w.strava_panel.isHidden() and w.garmin_controls.isHidden()
    assert w.account_settings_button.text()=='Import / Einstellungen'
    assert 'keine Anmeldung' in w.connection.text() and w.api is None
    assert 'strava' not in w.workspace.data['order']
    source=package(tmp_path/'strava.zip',[row(filename='')]);messages=[];w.message=lambda *a:messages.append(a)
    w.rate_pause.record({'reason':'rate_limit','retry_after_seconds':60})
    w.start_strava_import(account,str(source),w.strava_database(account))
    deadline=time.monotonic()+5
    while not w.data_page.data['activities'] and time.monotonic()<deadline:QTest.qWait(20)
    assert len(w.data_page.data['activities'])==1 and w.data_page.data['account']==account['id']
    assert w.tabs.currentIndex()==2 and w.request_count==0 and messages
    w.toggle_language();assert 'local import source' in w.connection.text()
