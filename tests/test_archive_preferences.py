"""Account archive locations survive close/restart without an account switch."""
from pathlib import Path
import pytest
from PySide6.QtCore import QEvent,QStandardPaths,QTimer
from PySide6.QtWidgets import QApplication,QFileDialog
from app import DesktopWindow
from archive import Archive
from datahub import load_archive
from engine import account_key,account_root
from workspace_state import Workspace

APP=QApplication.instance() or QApplication([])


@pytest.fixture
def windows(tmp_path,monkeypatch):
    native=QStandardPaths.writableLocation
    monkeypatch.setattr(QStandardPaths,'writableLocation',lambda key:str(tmp_path/'profile') if key==QStandardPaths.StandardLocation.AppLocalDataLocation else str(tmp_path/'Downloads') if key==QStandardPaths.StandardLocation.DownloadLocation else native(key))
    monkeypatch.setattr(QTimer,'singleShot',lambda *args:None)
    made=[]
    def create():
        w=DesktopWindow();w.message=lambda *a:pytest.fail('Unexpected dialog');made.append(w);return w
    yield create,tmp_path
    for w in made:
        if w.worker and w.worker.isRunning():w.worker.cancel.set();w.worker.wait(15000)
        QApplication.processEvents();w.close();w.deleteLater()
    QApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()


def prepare(w,root):
    a=w.workspace.add_account('garmin','mine@example.invalid',root/'Downloads'/'Garmin_Export')
    old=account_root(a['output'],a['id'])/'garmin-offline.sqlite'
    new=account_root(root/'Downloads'/'TTN_Activity_Export'/'Garmin',a['id'])/'garmin-offline.sqlite'
    for path in (old,new):
        with Archive(path,a['id']):pass
    a['archive_path']=str(old);w.workspace.save();w.refresh_accounts(a['id'])
    return a,old,new


def test_loaded_location_is_saved_immediately_and_retained_after_restart_and_login(windows):
    create,root=windows;w=create();a,old,new=prepare(w,root)
    w.archive_path.setText(str(new));w.data_page.loaded(load_archive(new,with_tracks=False))
    assert Workspace(w.workspace.path).accounts[0]['archive_path']==str(new)
    w.close();second=create();assert second.data_page.source.text()==str(new)
    second.login_done((object(),a['id'],a['email'],[],None,{}))
    assert second.archive_path.text()==str(new) and second.data_page.source.text()==str(new)
    assert old.exists() and new.exists()


def test_edited_valid_location_is_saved_on_close_without_loading_or_switching(windows):
    create,root=windows;w=create();a,old,new=prepare(w,root)
    w.data_page.source.setText(str(new));w.close()
    assert create().data_page.source.text()==str(new)


def test_foreign_invalid_and_unselected_missing_paths_do_not_replace_saved_location(windows):
    create,root=windows;w=create();a,old,new=prepare(w,root)
    foreign=root/'other.sqlite'
    with Archive(foreign,account_key('someone else')):pass
    invalid=root/'invalid.sqlite';invalid.write_bytes(b'not a database')
    for path in (foreign,invalid,root/'missing.sqlite'):
        w.data_page.source.setText(str(path));assert not w.remember_active_archive()
        assert a['archive_path']==str(old)
    w.close();assert create().data_page.source.text()==str(old)


def test_explicit_new_archive_target_is_saved_without_creating_or_moving_files(windows,monkeypatch):
    create,root=windows;w=create();a,old,new=prepare(w,root);new.unlink()
    monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *a,**kw:(str(new),'SQLite'))
    w.choose_archive();assert not new.exists() and old.exists()
    assert Workspace(w.workspace.path).accounts[0]['archive_path']==str(new)
    w.close();assert create().data_page.source.text()==str(new)


def test_explicitly_typed_new_sqlite_target_survives_restart_without_creating_it(windows):
    create,root=windows;w=create();a,old,new=prepare(w,root);new.unlink()
    w.data_page.source.setText(str(new));w.data_page.source.textEdited.emit(str(new))
    w.close();assert create().data_page.source.text()==str(new)
    assert old.exists() and not new.exists()


def test_failed_preference_save_keeps_previous_location(windows,monkeypatch):
    create,root=windows;w=create();a,old,new=prepare(w,root)
    monkeypatch.setattr(w,'save_workspace',lambda:False)
    assert not w.remember_active_archive(str(new)) and a['archive_path']==str(old)


def test_default_root_uses_exact_underscore_name_for_every_provider(windows):
    create,root=windows;w=create()
    for provider in ('garmin','komoot','strava'):
        assert w.default_provider_folder(provider)==root/'Downloads'/'TTN_Activity_Export'/provider.capitalize()
    assert Path(w.output.text())==root/'Downloads'/'TTN_Activity_Export'/'Garmin'
