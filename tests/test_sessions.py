"""Remembered sessions restore without keeping a password or making real requests."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QStandardPaths,QTimer
import app as app_module

QT_APP=QApplication.instance() or QApplication([])

@pytest.fixture
def session_ui(monkeypatch,tmp_path):
    scheduled=[];calls=[]
    monkeypatch.setattr(QStandardPaths,'writableLocation',lambda location:str(tmp_path))
    monkeypatch.setattr(QTimer,'singleShot',lambda delay,callback:scheduled.append(callback))
    class API:
        def __init__(self,**kwargs):
            calls.append(kwargs)
            self.kwargs=kwargs
            self.client=SimpleNamespace(dump=self.dump,_tokenstore_path=None)
        def login(self,path):
            self.path=Path(path)
            if not self.kwargs['password']:
                assert (self.path/'garmin_tokens.json').read_text()=='synthetic-session'
            self.client._tokenstore_path=path
        def dump(self,path):
            p=Path(path);p.mkdir(parents=True,exist_ok=True)
            (p/'garmin_tokens.json').write_text('synthetic-session')
        def get_activity_types(self):return []
    monkeypatch.setattr(app_module,'Garmin',API)
    windows=[]
    def window():
        w=app_module.MainWindow();windows.append(w)
        w.run_worker=lambda op,done:done(op(SimpleNamespace(ask_mfa=lambda:pytest.fail('MFA was requested'))))
        w.message=lambda *args:None
        return w
    yield window,calls,scheduled,API
    for w in windows:w.close();w.deleteLater()


def save_account(factory):
    w=factory();w.email.setText('remember@example.invalid');w.china.setChecked(True)
    w.password.setText('password-must-not-be-saved');w.remember.setChecked(True);w.login()
    return w


def test_remembered_account_restores_on_next_start_without_password(session_ui):
    factory,calls,scheduled,_=session_ui
    first=save_account(factory)
    prefs=json.loads(first.saved_account_path.read_text())
    assert prefs=={'schema':1,'email':'remember@example.invalid','china':True}
    assert first.password.text()==''
    first.close()
    second=factory()
    assert second.remember.isChecked() and second.china.isChecked()
    assert second.email.text()=='remember@example.invalid' and second.password.text()==''
    assert len(scheduled)==1
    scheduled.pop()()
    assert second.api and second.signed_email=='remember@example.invalid'
    assert calls[-1]['password'] is None and calls[-1]['is_cn'] is True
    assert calls[-1]['retry_attempts']==0


def test_remember_save_failure_is_visible_without_losing_live_login(session_ui,monkeypatch):
    factory,_,_,API=session_ui
    monkeypatch.setattr(API,'dump',lambda *args:(_ for _ in ()).throw(PermissionError('private detail')))
    w=factory();messages=[];w.message=lambda *args:messages.append(args)
    w.email.setText('remember@example.invalid');w.password.setText('not-saved');w.remember.setChecked(True);w.login()
    assert w.api and not w.saved_account_path.exists()
    assert messages and 'gespeichert' in messages[0][0] and 'private detail' not in str(messages)


def test_turning_remember_off_disables_restore(session_ui):
    factory,_,scheduled,_=session_ui
    first=save_account(factory);first.remember.setChecked(False)
    assert not first.saved_account_path.exists()
    second=factory()
    assert not second.remember.isChecked() and not scheduled and not second.api


def test_expired_session_can_be_removed_without_login(session_ui):
    factory,_,_,_=session_ui
    first=save_account(factory);session=Path(first.api.path);first.close()
    second=factory();assert second.api is None
    second.forget()
    assert not session.exists() and not second.saved_account_path.exists()
    assert not second.remember.isChecked()


def test_startup_restore_respects_request_pause(session_ui,monkeypatch):
    factory,calls,scheduled,_=session_ui
    first=save_account(factory);first.close()
    second=factory();monkeypatch.setattr(second.rate_pause,'remaining',lambda:600)
    scheduled.pop()()
    assert len(calls)==1 and second.api is None
