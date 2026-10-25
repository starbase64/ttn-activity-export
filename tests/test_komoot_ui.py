import json
import threading
from types import SimpleNamespace
import pytest
from PySide6.QtCore import QDate,QEvent,QStandardPaths,QTimer
from PySide6.QtWidgets import QApplication,QLabel,QPushButton,QCheckBox,QDialog
from app import DesktopWindow
from secure_sessions import KomootSessions
from tests.test_secure_sessions import fake_codec

QT_APP=QApplication.instance() or QApplication([])


@pytest.fixture
def windows(tmp_path,monkeypatch):
    native=QStandardPaths.writableLocation
    monkeypatch.setattr(QStandardPaths,'writableLocation',lambda key:str(tmp_path/'profile') if key==QStandardPaths.StandardLocation.AppLocalDataLocation else native(key))
    import secure_sessions
    monkeypatch.setattr(secure_sessions,'KomootSessions',lambda folder:KomootSessions(folder,fake_codec))
    made=[]
    def create():
        w=DesktopWindow();made.append(w)
        w.message=lambda *args:pytest.fail('Unexpected dialog: '+str(args))
        w.run_worker=lambda op,done,**kwargs:done(op(SimpleNamespace(cancel=threading.Event())))
        return w
    yield create
    for w in made:
        if w.worker and w.worker.isRunning():w.worker.cancel.set();w.worker.wait(15000)
        QApplication.processEvents();w.close();w.deleteLater()
    QApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()


def test_komoot_remembered_login_dates_custom_choice_and_reset_survive_restart(windows,tmp_path,monkeypatch):
    import komoot_client
    calls=[];real=komoot_client.KomootClient
    def transport(path,*args):
        calls.append(path)
        if '/account/email/' in path:return b'{"username":"42","password":"private-token"}'
        assert 'sort_direction=asc' in path
        return b'{"_embedded":{"tours":[{"id":123,"date":"2017-05-17T12:00:00Z","type":"tour_recorded"}]}}'
    monkeypatch.setattr(komoot_client,'KomootClient',lambda path:real(path,transport))
    w=windows();a=w.workspace.add_account('komoot','mine@example.invalid',tmp_path/'Komoot');w.refresh_accounts(a['id'])
    w.start_komoot_login(a,'never-persist-this-password',remember=True)
    assert w.komoot_sessions.exists(a['id']) and w.komoot_from.date()==QDate(2017,5,17)
    assert w.komoot_reset.isEnabled() and w.date_values(a['id'])['first_activity']=='2017-05-17'
    w.toggle_language();assert 'First recorded activity: 2017-05-17' in w.komoot_first_label.text()
    w.toggle_language();assert 'Erste aufgezeichnete Aktivität: 2017-05-17' in w.komoot_first_label.text()
    assert len(calls)==2
    w.komoot_from.setDate(QDate(2020,1,2));w.close()
    second=windows()
    assert second.active_account['id']==a['id'] and second.komoot_clients[a['id']].token=='private-token'
    assert second.komoot_from.date()==QDate(2020,1,2) and len(calls)==2
    second.komoot_reset.click();assert second.komoot_from.date()==QDate(2017,5,17)
    second.close();third=windows()
    assert third.komoot_from.date()==QDate(2017,5,17)
    assert third.forget_komoot_session(third.active_account)
    assert a['id'] not in third.komoot_clients and not third.komoot_sessions.exists(a['id'])
    for path in (tmp_path/'profile').rglob('*'):
        if path.is_file():assert b'never-persist-this-password' not in path.read_bytes()


def test_komoot_date_lookup_failure_keeps_login_and_custom_range(windows,tmp_path,monkeypatch):
    import komoot_client
    class API:
        user='42';token='live-token'
        def __init__(self,*a):pass
        def login(self,*a):return self
        def oldest_activity(self,*a):raise komoot_client.KomootError(400)
    monkeypatch.setattr(komoot_client,'KomootClient',API)
    w=windows();a=w.workspace.add_account('komoot','mine@example.invalid',tmp_path/'Komoot');w.refresh_accounts(a['id'])
    w.komoot_from.setDate(QDate(2021,2,3));w.start_komoot_login(a,'password')
    assert a['id'] in w.komoot_clients and w.komoot_from.date()==QDate(2021,2,3)
    assert not w.komoot_reset.isEnabled() and not w.komoot_sessions.exists(a['id'])
    w.record_komoot_first(a,'2017-05-17')
    assert w.komoot_from.date()==QDate(2021,2,3)


def test_repeated_page_warning_disables_load_more_and_preserves_incomplete_state(windows):
    w=windows();result={'provider':'komoot','start':'2020-01-01','end':'2020-12-31','items':[],
        'complete':False,'error':None,'stop_reason':'repeated_page'}
    w.open_inventory_dialog(result)
    text=' '.join(x.text() for x in w.inventory_dialog.findChildren(QLabel))
    assert 'wiederholt' in text and 'unvollständig' in text and 'ValueError' not in text
    more=next(x for x in w.inventory_dialog.findChildren(QPushButton) if x.text()=='Weitere Seiten laden')
    assert not more.isEnabled()
    w.inventory_dialog.close()


def test_unchecking_remember_removes_disk_token_but_keeps_current_session(windows,tmp_path):
    w=windows();a=w.workspace.add_account('komoot','mine@example.invalid',tmp_path/'Komoot');w.refresh_accounts(a['id'])
    w.komoot_sessions.save(a['id'],'42','live-token')
    w.komoot_clients[a['id']]=SimpleNamespace(user='42',token='live-token')
    checked=[]
    def interact():
        dialog=next(d for d in w.findChildren(QDialog) if d.windowTitle().startswith('Komoot'))
        remember=next(c for c in dialog.findChildren(QCheckBox) if 'Anmeldung lokal merken' in c.text())
        checked.append(remember.isChecked());remember.setChecked(False);dialog.reject()
    QTimer.singleShot(0,interact);w.open_komoot_account()
    assert checked==[True] and not w.komoot_sessions.exists(a['id']) and a['id'] in w.komoot_clients


def test_komoot_dates_and_tokens_stay_separate_between_accounts(windows,tmp_path):
    w=windows();a=w.workspace.add_account('komoot','a@example.invalid',tmp_path/'Komoot');b=w.workspace.add_account('komoot','b@example.invalid',tmp_path/'Komoot')
    w.record_komoot_first(a,'2017-05-17');w.record_komoot_first(b,'2021-02-03')
    w.refresh_accounts(a['id']);w.komoot_from.setDate(QDate(2019,1,2))
    w.refresh_accounts(b['id']);assert w.komoot_from.date()==QDate(2021,2,3)
    w.refresh_accounts(a['id']);assert w.komoot_from.date()==QDate(2019,1,2)
    w.komoot_reset.click();assert w.komoot_from.date()==QDate(2017,5,17)


def test_komoot_auth_failure_forgets_only_affected_account_and_403_keeps_token(windows,tmp_path):
    w=windows();a=w.workspace.add_account('komoot','a@example.invalid',tmp_path/'Komoot');b=w.workspace.add_account('komoot','b@example.invalid',tmp_path/'Komoot')
    for account in (a,b):
        w.komoot_sessions.save(account['id'],'42','token');w.komoot_clients[account['id']]=SimpleNamespace(user='42',token='token')
    w.refresh_accounts(b['id']);w.message=lambda *a:None
    w.komoot_error({'http_status':403},a)
    assert w.komoot_sessions.exists(a['id']) and a['id'] in w.komoot_clients
    w.komoot_error({'http_status':401},a)
    assert not w.komoot_sessions.exists(a['id']) and a['id'] not in w.komoot_clients
    assert w.komoot_sessions.exists(b['id']) and b['id'] in w.komoot_clients


def test_full_inventory_can_supply_first_date_when_sorted_lookup_is_unavailable(windows,tmp_path):
    w=windows();a=w.workspace.add_account('komoot','a@example.invalid',tmp_path/'Komoot');w.refresh_accounts(a['id'])
    result={'provider':'komoot','start':'1990-01-01','end':'2026-10-25','kind':'tour_recorded','items':[],
        'complete':True,'oldest_recorded':'2017-05-17','error':None}
    w.komoot_clients[a['id']]=SimpleNamespace(inventory=lambda *args:dict(result))
    w.open_inventory_dialog=lambda r:None
    w.fetch_komoot_inventory()
    assert w.date_values(a['id'])['first_activity']=='2017-05-17' and w.komoot_from.date()==QDate(2017,5,17)
