import pytest
from PySide6.QtCore import QEvent,QStandardPaths
from PySide6.QtWidgets import QApplication,QMessageBox
from app import DesktopWindow

APP=QApplication.instance() or QApplication([])


@pytest.fixture
def window(tmp_path,monkeypatch):
    native=QStandardPaths.writableLocation
    monkeypatch.setattr(QStandardPaths,'writableLocation',lambda key:str(tmp_path) if key==QStandardPaths.StandardLocation.AppLocalDataLocation else native(key))
    w=DesktopWindow(demo=True);w.demo=False;w._install_context={'root':tmp_path,'controller':tmp_path,'version':'0.6.9'}
    w.update_info={'status':'available','latest':'v0.6.10','current':'0.6.9','url':'https://github.com/starbase64/ttn-activity-export/releases/tag/v0.6.10',
                   'installer':{'version':'0.6.10','url':'unused','sha256':'a'*64,'size':123}}
    yield w
    w.close();w.deleteLater();QApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()


def test_cancel_does_not_download_close_or_modify_data(window,monkeypatch):
    w=window;before=w.make_plan();calls=[]
    monkeypatch.setattr(QMessageBox,'question',lambda *a:QMessageBox.StandardButton.Cancel)
    monkeypatch.setattr(w,'_begin_install',lambda *a:calls.append(a))
    w.confirm_update();assert not calls and not w._closing and w.make_plan()==before


def test_ok_starts_only_the_confirmed_update_and_busy_jobs_are_not_interrupted(window,monkeypatch):
    w=window;calls=[]
    monkeypatch.setattr(QMessageBox,'question',lambda *a:QMessageBox.StandardButton.Ok)
    monkeypatch.setattr(w,'_begin_install',lambda asset:calls.append(asset))
    monkeypatch.setattr(w,'update_install_busy',lambda:True)
    w.confirm_update();assert not calls
    monkeypatch.setattr(w,'update_install_busy',lambda:False)
    w.confirm_update();assert len(calls)==1 and calls[0]['version']=='0.6.10'


def test_available_update_prompts_once_and_translates_install_button(window,monkeypatch):
    w=window;calls=[]
    monkeypatch.setattr(QMessageBox,'question',lambda *a:calls.append(a[2]) or QMessageBox.StandardButton.Cancel)
    w.offer_update();w.offer_update();assert len(calls)==1
    w.render_update_result();assert w.update_download.text()=='Update installieren'
    w.toggle_language();assert w.update_download.text()=='Install update'
