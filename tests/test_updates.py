import json
from types import SimpleNamespace
import pytest
from PySide6.QtCore import QObject,Signal,QByteArray,QEvent,QStandardPaths,QTimer
from PySide6.QtNetwork import QNetworkReply,QNetworkRequest
from PySide6.QtWidgets import QApplication
from app import DesktopWindow
from updates import ReleaseCheck,release_result,version,load_auto_check,save_auto_check,MAX_BYTES,RELEASES_URL

APP=QApplication.instance() or QApplication([])


def release(tag,**kw):return {'tag_name':tag,'draft':False,'prerelease':'-' in tag,**kw}


def test_version_comparison_and_release_channels_never_offer_downgrades():
    assert version('v0.6.10')>version('0.6.9')
    assert version('0.6.8')>version('0.6.8-rc.2')>version('0.6.8-preview.10')>version('0.6.8-preview.2')
    assert release_result('0.6.8-preview',[release('v0.5.0-preview')])['status']=='ahead'
    items=[release('v0.6.9-preview'),release('v0.6.8'),release('v9.0.0',draft=True)]
    assert release_result('0.6.8',items)['status']=='current'
    result=release_result('0.6.8-preview',items)
    assert result['status']=='available' and result['latest']=='v0.6.9-preview'
    assert release_result('0.6.8-preview',[release('v0.6.8')])['status']=='available'
    assert release_result('0.6.8',[release('v0.7.0',prerelease=True)])['status']=='no_releases'


def test_update_urls_are_constructed_from_valid_versions_and_partial_checks_are_honest():
    result=release_result('0.6.8',[release('v0.7.0',html_url='https://host.invalid/private')])
    assert result['url']==RELEASES_URL+'/tag/v0.7.0'
    for tag in ('../escape','nightly','v0.7.0<script>'):
        assert release_result('0.6.8',[release(tag)])['status']=='no_releases'
    assert release_result('0.6.8',[],partial=True)['status']=='incomplete'
    with pytest.raises(ValueError):release_result('unknown',[])


class Reply(QObject):
    readyRead=Signal();finished=Signal()
    def __init__(self,payload,status=200,headers=None,error=QNetworkReply.NetworkError.NoError):
        super().__init__();self.payload=payload;self.status=status;self.headers=headers or {};self.network_error=error;self.aborted=False;self.pending=b''
    def complete(self):
        if self.aborted:return
        self.pending=self.payload;self.readyRead.emit()
        if not self.aborted:self.finished.emit()
    def readAll(self):raw=self.pending;self.pending=b'';return QByteArray(raw)
    def attribute(self,key):return self.status
    def error(self):return self.network_error
    def rawHeader(self,name):return QByteArray(self.headers.get(name.encode() if isinstance(name,str) else name,b''))
    def abort(self):
        if not self.aborted:self.aborted=True;self.finished.emit()


class Manager:
    def __init__(self,*replies):self.pending=list(replies);self.requests=[]
    def get(self,request):self.requests.append(request);return self.pending.pop(0)


def test_release_check_paginates_only_fixed_github_host_without_account_credentials():
    first=Reply(json.dumps([release('v0.5.0')]).encode(),headers={b'Link':b'<https://host.invalid/steal>; rel="next"'})
    second=Reply(json.dumps([release('v0.7.0')]).encode());manager=Manager(first,second);job=ReleaseCheck('0.6.8',manager=manager);results=[];job.result.connect(results.append)
    job.start();first.complete();second.complete()
    assert results[0]['status']=='available' and len(manager.requests)==2
    for i,request in enumerate(manager.requests,1):
        assert request.url().toString().startswith('https://api.github.com/repos/starbase64/ttn-activity-export/releases?')
        assert request.url().query().endswith('page='+str(i))
        assert bytes(request.rawHeader('Authorization'))==b''
        assert request.attribute(QNetworkRequest.Attribute.RedirectPolicyAttribute)==QNetworkRequest.RedirectPolicy.ManualRedirectPolicy


@pytest.mark.parametrize('reply,reason',[
    (lambda:Reply(b'private response',403,{b'X-RateLimit-Remaining':b'0'}),'rate_limit'),
    (lambda:Reply(b'private response',302),'http'),
    (lambda:Reply(b'private response',None,error=QNetworkReply.NetworkError.ConnectionRefusedError),'connection'),
    (lambda:Reply(b'{"private":"response"}'),'response'),
    (lambda:Reply(b'x'*(MAX_BYTES+1)),'size'),
])
def test_update_errors_are_explicit_and_never_include_response_bodies(reply,reason):
    response=reply();job=ReleaseCheck('0.6.8',manager=Manager(response));results=[];job.result.connect(results.append);job.start();response.complete()
    assert results[0]['status']=='error' and results[0]['reason']==reason
    assert 'private' not in json.dumps(results)


def test_timeout_cancellation_and_page_limit_are_bounded(monkeypatch):
    response=Reply(b'[]');job=ReleaseCheck('0.6.8',manager=Manager(response));results=[];job.result.connect(results.append);job.start();job.timeout()
    assert response.aborted and results==[{'status':'error','reason':'timeout'}]
    response=Reply(b'[]');job=ReleaseCheck('0.6.8',manager=Manager(response));results=[];job.result.connect(results.append);job.start();job.cancel();response.complete()
    assert response.aborted and not results
    monkeypatch.setattr('updates.MAX_PAGES',1)
    response=Reply(b'[]',headers={b'Link':b'<unused>; rel="next"'});job=ReleaseCheck('0.6.8',manager=Manager(response));results=[];job.result.connect(results.append);job.start();response.complete()
    assert results[0]['status']=='incomplete' and results[0]['partial']


@pytest.fixture
def windows(tmp_path,monkeypatch):
    native=QStandardPaths.writableLocation
    monkeypatch.setattr(QStandardPaths,'writableLocation',lambda key:str(tmp_path/'profile') if key==QStandardPaths.StandardLocation.AppLocalDataLocation else native(key))
    made=[]
    def create(demo=True):
        window=DesktopWindow(demo=demo);made.append(window);return window
    yield create,tmp_path/'profile'
    for w in made:
        if w.worker and w.worker.isRunning():w.worker.cancel.set();w.worker.wait(15000)
        QApplication.processEvents();w.close();w.deleteLater()
    QApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);QApplication.processEvents()


def test_update_preference_survives_restart_theme_and_language_changes(windows):
    create,profile=windows;w=create();assert not w.auto_updates.isChecked()
    w.auto_updates.setChecked(True);w.toggle_theme();w.toggle_language()
    assert load_auto_check(profile/'update-preferences.json')
    assert w.update_button.text()=='Check updates'
    assert create().auto_updates.isChecked()
    for bad in ('[]','broken','{"automatic":"true"}'):
        (profile/'update-preferences.json').write_text(bad)
        assert not load_auto_check(profile/'update-preferences.json')


def test_manual_check_is_independent_and_preserves_export_settings(windows,monkeypatch):
    create,_=windows;w=create();before=w.make_plan();jobs=[]
    class FakeCheck(QObject):
        result=Signal(object)
        def __init__(self,current,parent):super().__init__(parent);self.started=False;self.cancelled=False;jobs.append(self)
        def start(self):self.started=True
        def cancel(self):self.cancelled=True
    monkeypatch.setattr('updates.ReleaseCheck',FakeCheck)
    w.update_button.click();w.check_updates()
    assert len(jobs)==1 and jobs[0].started and not w.update_button.isEnabled()
    jobs[0].result.emit(release_result('0.6.8-preview',[release('v0.7.0-preview')]))
    assert w.update_job is None and w.update_button.isEnabled() and not w.update_download.isHidden()
    assert w.make_plan()==before
    w.toggle_language();assert 'Update available' in w.update_status.text()
    opened=[];monkeypatch.setattr('app.QDesktopServices.openUrl',lambda url:opened.append(url.toString()) or True)
    w.update_download.click();assert opened==[RELEASES_URL+'/tag/v0.7.0-preview']
    w.check_updates();w.close();assert jobs[-1].cancelled


def test_startup_check_is_opt_in_once_and_is_suppressed_in_demo(windows,monkeypatch):
    create,profile=windows;scheduled=[];checked=[]
    monkeypatch.setattr(QTimer,'singleShot',lambda delay,callback:scheduled.append(callback))
    monkeypatch.setattr(DesktopWindow,'check_updates',lambda self,automatic=False:checked.append(automatic))
    create(False);assert not scheduled
    save_auto_check(profile/'update-preferences.json',True)
    create(False);assert len(scheduled)==1
    scheduled.pop()();assert checked==[True]
    create(True);assert not scheduled
