"""Verified Windows starter updates, installed beside the active program version.

The launcher pointer changes only after the new private runtime/app passes smoke.
Existing program folders and all user data remain in place for fallback.
"""
import ast
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import sys
import tempfile
import threading
import time
from urllib.parse import quote,urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler
import uuid
import zipfile

REPOSITORY='starbase64/ttn-activity-export'
MANIFEST='app-manifest.json'
MAX_ARCHIVE=50*1024**2
MAX_EXPANDED=100*1024**2
ROOT_FILES={'Start-TTN-Activity-Export.cmd','bootstrap.ps1','windows_bootstrap.py',
 'windows-dependencies.lock.json','windows_update.ps1','LICENSE','THIRD_PARTY_NOTICES.md',
 'README.md','CHANGELOG.md','RELEASE_NOTES.md','ROADMAP.md','BITTE-ZUERST-LESEN.txt'}


class UpdateError(Exception):pass
class UpdateCancelled(UpdateError):pass


@dataclass(order=True,frozen=True)
class Version:
    major:int
    minor:int
    patch:int
    phase:int
    number:int


def version(value):
    if not isinstance(value,str) or len(value)>100:return None
    m=re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)(?:[-.](alpha|beta|preview|rc)(?:[.-]?(\d+))?)?(?:\+[\w.-]+)?',value.strip(),re.I)
    if not m:return None
    a,b,c,phase,n=m.groups()
    return Version(int(a),int(b),int(c),{'alpha':0,'beta':1,'preview':2,'rc':3,None:4}[phase.lower() if phase else None],int(n or 0))


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def relative_name(name):
    if not isinstance(name,str) or not name or len(name)>240 or '\\' in name or ':' in name or name.startswith('/'):raise UpdateError('path')
    parts=name.split('/')
    for part in parts:
        if not part or part in ('.','..') or part.endswith((' ','.')) or re.search(r'[\x00-\x1f<>"|?*]',part) or re.match(r'(?i)^(con|prn|aux|nul|com\d|lpt\d)(\.|$)',part):raise UpdateError('path')
    allowed=name in ROOT_FILES or (len(parts)==2 and parts[0]=='app' and parts[1].endswith('.py')) or (len(parts)==3 and parts[:2]==['app','docs'] and parts[2].endswith(('.md','.html')))
    if not allowed:raise UpdateError('path')
    return name


def manifest_bytes(files,version):
    entries={}
    for name,data in files.items():
        relative_name(name);entries[name]={'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    return json.dumps({'schema':1,'protocol':1,'distribution':'windows-starter','version':version,'files':entries},sort_keys=True,indent=2).encode('utf-8')


def read_manifest(raw):
    if len(raw)>512*1024:raise UpdateError('manifest')
    try:data=json.loads(raw)
    except (ValueError,UnicodeError):raise UpdateError('manifest') from None
    if not isinstance(data,dict) or (data.get('schema'),data.get('protocol'),data.get('distribution'))!=(1,1,'windows-starter'):raise UpdateError('manifest')
    if not isinstance(data.get('version'),str) or not re.fullmatch(r'\d+\.\d+\.\d+(?:-(?:preview|rc|beta|alpha)(?:\.\d+)?)?',data['version']):raise UpdateError('manifest')
    entries=data.get('files')
    if not isinstance(entries,dict) or not entries or len(entries)>1500:raise UpdateError('manifest')
    seen=set();total=0
    for name,info in entries.items():
        relative_name(name)
        if name.casefold() in seen:raise UpdateError('manifest')
        seen.add(name.casefold())
        if not isinstance(info,dict) or type(info.get('size')) is not int or not 0<=info['size']<=MAX_EXPANDED or not re.fullmatch('[a-f0-9]{64}',str(info.get('sha256',''))):raise UpdateError('manifest')
        total+=info['size']
    required={'bootstrap.ps1','windows_update.ps1','Start-TTN-Activity-Export.cmd','windows-dependencies.lock.json','app/app.py'}
    if total>MAX_EXPANDED or not required<=set(entries):raise UpdateError('manifest')
    return data


def installation_context(app_file,current,platform=None):
    if (platform or sys.platform)!='win32' or getattr(sys,'frozen',False):return None
    root=Path(app_file).resolve().parent.parent
    if Path(app_file).resolve().parent.name!='app':return None
    try:
        meta=read_manifest((root/MANIFEST).read_bytes())
        if meta['version']!=current or not (root/'runtime/python.exe').is_file():return None
        helper=root/'windows_update.ps1'
        if digest(helper)!=meta['files']['windows_update.ps1']['sha256']:return None
        controller=root
        if root.parent.name=='.versions':controller=root.parent.parent
        pointer=controller/'.active-version.json'
        if pointer.exists():
            info=json.loads(pointer.read_text(encoding='utf-8'))
            if info.get('schema')!=1 or not re.fullmatch(r'\.versions/[A-Za-z0-9_.-]+',str(info.get('path',''))):return None
            if (controller/info['path']).resolve()!=root:return None
        elif controller!=root:return None
        return {'root':root,'controller':controller,'version':current}
    except (OSError,ValueError,KeyError,UpdateError):return None


def installer_asset(release,tag):
    if not isinstance(release,dict) or not isinstance(tag,str):return None
    label=tag[1:] if tag.startswith(('v','V')) else tag
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-(?:preview|rc|beta|alpha)(?:\.\d+)?)?',label):return None
    filename='TTN-Activity-Export-Windows-'+label+'.zip'
    expected='https://github.com/'+REPOSITORY+'/releases/download/'+quote(tag,safe='')+'/'+filename
    matches=[a for a in release.get('assets',[]) if isinstance(a,dict) and a.get('name')==filename and a.get('state')=='uploaded']
    if len(matches)!=1:return None
    item=matches[0];sha=item.get('digest','')
    if item.get('browser_download_url')!=expected or type(item.get('size')) is not int or not 0<item['size']<=MAX_ARCHIVE or not isinstance(sha,str) or not re.fullmatch('sha256:[a-f0-9]{64}',sha):return None
    return {'url':expected,'size':item['size'],'sha256':sha[7:],'version':label}


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        url=urlsplit(newurl)
        if url.scheme!='https' or url.hostname not in ('github.com','release-assets.githubusercontent.com','objects.githubusercontent.com') or url.port not in (None,443) or url.username or url.password:raise UpdateError('download_source')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def download_asset(asset,target,cancel,progress):
    expected='https://github.com/'+REPOSITORY+'/releases/download/'
    if not asset['url'].startswith(expected):raise UpdateError('download_source')
    deadline=time.monotonic()+300;received=0;hashing=hashlib.sha256()
    with build_opener(SafeRedirect()).open(Request(asset['url'],headers={'User-Agent':'TTN-Activity-Export-Updater'}),timeout=20) as response,Path(target).open('xb') as out:
        while True:
            if cancel.is_set():raise UpdateCancelled('cancelled')
            if time.monotonic()>deadline:raise UpdateError('timeout')
            part=response.read(128*1024)
            if not part:break
            received+=len(part)
            if received>asset['size'] or received>MAX_ARCHIVE:raise UpdateError('size')
            out.write(part);hashing.update(part);progress(received,asset['size'])
    if received!=asset['size'] or hashing.hexdigest()!=asset['sha256']:raise UpdateError('checksum')


def stage_package(package,target,expected,cancel=None):
    cancel=cancel or threading.Event();target=Path(target)
    with zipfile.ZipFile(package) as archive:
        members={};seen=set();total=0
        for item in archive.infolist():
            raw=item.orig_filename
            if item.is_dir():continue
            if not raw.startswith('TTN-Activity-Export/') or item.flag_bits&1 or ((item.external_attr>>16)&0o170000)==0o120000:raise UpdateError('package')
            name=raw[len('TTN-Activity-Export/'):]
            if name!=MANIFEST:relative_name(name)
            if name.casefold() in seen:raise UpdateError('package')
            seen.add(name.casefold());members[name]=item;total+=item.file_size
            if len(members)>1501 or total>MAX_EXPANDED+512*1024:raise UpdateError('size')
        if MANIFEST not in members:raise UpdateError('manifest')
        meta=read_manifest(archive.read(members[MANIFEST]))
        if meta['version']!=expected or set(members)!=(set(meta['files'])|{MANIFEST}):raise UpdateError('manifest')
        target.mkdir(parents=True,exist_ok=False)
        for name,item in members.items():
            if cancel.is_set():raise UpdateCancelled('cancelled')
            data=archive.read(item)
            if name!=MANIFEST:
                info=meta['files'][name]
                if len(data)!=info['size'] or hashlib.sha256(data).hexdigest()!=info['sha256']:raise UpdateError('checksum')
            path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        tree=ast.parse((target/'app/app.py').read_text(encoding='utf-8'))
        actual=next((ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in n.targets)),None)
        if actual!=expected:raise UpdateError('version')
        return meta


def prepare_update(context,asset,language='de',cancel=None,progress=lambda *a:None,downloader=download_asset):
    cancel=cancel or threading.Event();controller=Path(context['controller']).resolve();current=Path(context['root']).resolve()
    if cancel.is_set():raise UpdateCancelled('cancelled')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-(?:preview|rc|beta|alpha)(?:\.\d+)?)?',asset.get('version','')):raise UpdateError('version')
    if version(context.get('version')) is None or version(asset['version'])<=version(context['version']):raise UpdateError('version')
    # Reserve room for a separate private runtime; the prior runtime is retained.
    if shutil.disk_usage(controller).free<1024**3:raise UpdateError('space')
    token=uuid.uuid4().hex;work=controller/'.updates'/token;target=controller/'.versions'/(asset['version']+'-'+token)
    for folder in (controller/'.updates',controller/'.versions'):
        if folder.is_symlink():raise UpdateError('path')
        folder.mkdir(exist_ok=True)
    work.mkdir(mode=0o700);target_owned=False
    try:
        package=work/'package.zip';downloader(asset,package,cancel,progress)
        if digest(package)!=asset['sha256']:raise UpdateError('checksum')
        staged=work/'program';stage_package(package,staged,asset['version'],cancel)
        if target.exists():raise UpdateError('path')
        staged.rename(target);target_owned=True
        shutil.copyfile(current/'windows_update.ps1',work/'windows_update.ps1')
        plan={'schema':1,'token':token,'controller':str(controller),'target':target.relative_to(controller).as_posix(),
              'version':asset['version'],'language':language,'from':current.relative_to(controller).as_posix()}
        (work/'plan.json').write_text(json.dumps(plan),encoding='utf-8')
        return str(work/'plan.json')
    except Exception:
        if target_owned:shutil.rmtree(target,ignore_errors=True)
        shutil.rmtree(work,ignore_errors=True);raise


def discard_prepared(plan_path):
    path=Path(plan_path).resolve();work=path.parent
    if work.parent.name!='.updates' or not re.fullmatch('[a-f0-9]{32}',work.name):return
    try:
        plan=json.loads(path.read_text());controller=work.parent.parent
        if plan.get('token')!=work.name or not re.fullmatch(r'\.versions/[A-Za-z0-9_.-]+',plan.get('target','')) or not plan['target'].endswith('-'+work.name):return
        shutil.rmtree(controller/plan['target'],ignore_errors=True);shutil.rmtree(work,ignore_errors=True)
    except (OSError,ValueError,TypeError):pass
