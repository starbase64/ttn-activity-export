import json
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication,QDialog,QCheckBox,QLineEdit
from PySide6.QtCore import QStandardPaths,QEvent
from PySide6.QtGui import QPalette
import pytest
from app import MainWindow
from themes import LIGHT,DARK,load_theme

APP=QApplication.instance() or QApplication([])

@pytest.fixture
def profile(tmp_path,monkeypatch):
    native=QStandardPaths.writableLocation
    monkeypatch.setattr(QStandardPaths,'writableLocation',lambda key:str(tmp_path) if key==QStandardPaths.StandardLocation.AppLocalDataLocation else native(key))
    yield tmp_path
    for widget in QApplication.topLevelWidgets():widget.close();widget.deleteLater()
    QApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()


def test_theme_switch_persists_and_keeps_export_state_and_language(profile):
    window=MainWindow(demo=True);window.dataset_checks['hrv'].setChecked(True);before=window.make_plan();identity=window.identity
    assert window.theme=='light' and window.theme_button.text()=='Dunkelmodus'
    window.log.appendPlainText('retain this session entry')
    window.toggle_theme()
    assert window.theme=='dark' and window.theme_button.text()=='Hellmodus'
    assert window.make_plan()==before and window.identity==identity
    assert 'retain this session entry' in window.log.toPlainText()
    assert json.loads((profile/'ui-preferences.json').read_text(encoding='utf-8'))['theme']=='dark'
    window.toggle_language();assert window.theme_button.text()=='Light mode' and window.theme=='dark'
    other=MainWindow(demo=True);assert other.theme=='dark'
    other.toggle_theme();assert other.theme=='light'
    assert APP.palette().color(QPalette.ColorRole.Window).name()==LIGHT['bg']


def test_dark_widgets_and_new_dialog_follow_palette(profile):
    window=MainWindow(demo=True);window.toggle_theme()
    dialog=QDialog(window);edit=QLineEdit(dialog);box=QCheckBox(dialog);box.setChecked(True)
    dialog.ensurePolished();edit.ensurePolished();box.ensurePolished()
    assert edit.palette().color(QPalette.ColorRole.Text).name()==DARK['text']
    assert edit.palette().color(QPalette.ColorRole.Base).name()==DARK['panel']
    box.setEnabled(False);assert box.isChecked()
    window.toggle_theme();assert edit.palette().color(QPalette.ColorRole.Text).name()==LIGHT['text']
    dialog.close()


def test_theme_switch_recolors_loaded_map_without_garmin_requests(profile,monkeypatch):
    window=MainWindow(demo=True);page=window.data_page
    a={'activityId':1,'_key':'1','_day':'2020-01-01','activityName':'Ride','activityType':{'typeKey':'cycling'},'startTimeLocal':'2020-01-01 10:00:00','distance':1000,'duration':600}
    page.loaded({'activities':[a],'tracks':{'1':[(51.1,8.1),(51.11,8.11)]},'health':[],'account':'demo'})
    page.table.selectAll();assert len(page.map.routes)==1
    monkeypatch.setattr(page.map.network,'get',lambda *a:pytest.fail('theme must not fetch tiles'))
    before=list(page.selected());window.toggle_theme()
    assert page.selected()==before and len(page.map.routes)==1
    assert page.map.palette().color(QPalette.ColorRole.Base).name()==DARK['bg']
    assert page.table.item(0,3).foreground().color().name()=='#7dd3fc'


def test_bad_or_absent_preferences_fall_back_to_light(tmp_path):
    path=tmp_path/'prefs.json';assert load_theme(path)=='light'
    for text in ('broken','[]','{"theme":"unknown"}','{"theme":null}'):
        path.write_text(text,encoding='utf-8');assert load_theme(path)=='light'


def test_dark_foreground_contrast():
    def luminance(value):
        channels=[int(value[i:i+2],16)/255 for i in (1,3,5)]
        channels=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels]
        return sum(v*w for v,w in zip(channels,(.2126,.7152,.0722)))
    for fg,bg in [('text','bg'),('text','panel'),('muted','panel'),('link','panel'),('accent_text','accent'),('selection_text','selection'),('warning','warning_bg'),('disabled','disabled_bg')]:
        a,b=sorted((luminance(DARK[fg]),luminance(DARK[bg])))
        assert (b+.05)/(a+.05)>=4.5,(fg,bg)
