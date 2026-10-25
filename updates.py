"""Bounded public GitHub release checks; installation metadata is opt-in UI input."""
import json
from pathlib import Path
import re
from urllib.parse import quote
from PySide6.QtCore import QObject,QTimer,QUrl,Signal
from PySide6.QtNetwork import QNetworkAccessManager,QNetworkRequest,QNetworkReply
from engine import atomic_json
from updater import Version,version

REPOSITORY='starbase64/ttn-activity-export'
RELEASES_URL='https://github.com/'+REPOSITORY+'/releases'
MAX_BYTES=2*1024*1024
MAX_PAGES=5


def release_result(current,releases,partial=False):
    local=version(current)
    if local is None:raise ValueError('Unknown local version')
    candidates=[]
    for item in releases:
        if not isinstance(item,dict) or item.get('draft') is not False or type(item.get('prerelease')) is not bool:continue
        tag=item.get('tag_name');parsed=version(tag)
        if parsed is None:continue
        if local.phase==4 and (item['prerelease'] or parsed.phase<4):continue
        candidates.append((parsed,tag,item))
    best=max(candidates,key=lambda c:(c[0],c[1]),default=None)
    result={'current':current,'latest':best[1] if best else None,'url':None,'partial':partial,'preview':local.phase<4}
    if best and best[0]>local:
        result.update(status='available',url=RELEASES_URL+'/tag/'+quote(best[1],safe=''))
        from updater import installer_asset
        installer=installer_asset(best[2],best[1])
        if installer:result['installer']=installer
    elif partial:result['status']='incomplete'
    elif not best:result['status']='no_releases'
    else:result['status']='ahead' if local>best[0] else 'current'
    return result


def load_auto_check(path):
    try:return json.loads(Path(path).read_text(encoding='utf-8')).get('automatic') is True
    except (OSError,ValueError,TypeError,AttributeError):return False


def save_auto_check(path,value):atomic_json(Path(path),{'automatic':bool(value)})


class ReleaseCheck(QObject):
    result=Signal(object)
    def __init__(self,current,parent=None,manager=None):
        super().__init__(parent);self.current=current;self.manager=manager or QNetworkAccessManager(self)
        self.reply=None;self.page=0;self.releases=[];self.done=False;self.raw=bytearray()
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.timeout.connect(self.timeout)
    def start(self):self.next_page()
    def next_page(self):
        if self.done:return
        self.page+=1;self.raw.clear()
        url='https://api.github.com/repos/'+REPOSITORY+'/releases?per_page=100&page='+str(self.page)
        request=QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        request.setRawHeader(b'Accept',b'application/vnd.github+json')
        request.setRawHeader(b'X-GitHub-Api-Version',b'2026-03-10')
        request.setRawHeader(b'User-Agent',('TTN-Activity-Export/'+self.current).encode('ascii'))
        self.reply=self.manager.get(request);self.reply.readyRead.connect(self.read_ready);self.reply.finished.connect(self.finished)
        self.timer.start(10000)
    def finish(self,result):
        if self.done:return
        self.done=True;self.timer.stop()
        reply=self.reply;self.reply=None
        if reply:
            reply.abort();reply.deleteLater()
        self.result.emit(result)
    def cancel(self):
        if self.done:return
        self.done=True;self.timer.stop()
        reply=self.reply;self.reply=None
        if reply:reply.abort();reply.deleteLater()
    def timeout(self):self.finish({'status':'error','reason':'timeout'})
    def read_ready(self):
        if self.done or self.reply is None:return
        self.raw.extend(bytes(self.reply.readAll()))
        if len(self.raw)>MAX_BYTES:self.finish({'status':'error','reason':'size'})
    def finished(self):
        if self.done or self.reply is None:return
        self.timer.stop();self.read_ready()
        if self.done:return
        reply=self.reply;self.reply=None
        status=reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error=reply.error();link=bytes(reply.rawHeader('Link'))
        remaining=bytes(reply.rawHeader('X-RateLimit-Remaining'));reply.deleteLater()
        if status!=200 or error!=QNetworkReply.NetworkError.NoError:
            reason='rate_limit' if status==429 or (status==403 and remaining==b'0') else 'http' if status else 'connection'
            self.finish({'status':'error','reason':reason,'http_status':status});return
        try:
            payload=json.loads(bytes(self.raw).decode('utf-8'))
            if not isinstance(payload,list) or len(payload)>100:raise ValueError('Invalid release list')
            self.releases.extend(payload)
            more=re.search(br'rel\s*=\s*"next"',link) is not None
            if more and self.page<MAX_PAGES:self.next_page();return
            self.finish(release_result(self.current,self.releases,partial=more))
        except (ValueError,TypeError,UnicodeError):self.finish({'status':'error','reason':'response'})
