"""Install pinned Windows wheels into the private runtime; stdlib only, no pip."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def load_lock(root):
    lock=json.loads((root/'windows-dependencies.lock.json').read_text(encoding='utf-8'))
    if lock.get('schema')!=1 or not lock.get('wheels'):raise ValueError('Invalid dependency lock')
    for wheel in lock['wheels']:
        url=urllib.parse.urlsplit(wheel['url'])
        if url.scheme!='https' or url.hostname!='files.pythonhosted.org':raise ValueError('Unexpected download source')
        if Path(wheel['filename']).name!=wheel['filename'] or not wheel['filename'].endswith('.whl'):raise ValueError('Invalid wheel filename')
        if len(wheel['sha256'])!=64:raise ValueError('Invalid wheel checksum')
    return lock


def read_state(root):
    try:return json.loads((root/'runtime'/'ttn-installed.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):return {}


def installed(wheel,site,state,verify=False):
    record=state.get(wheel['name'],{})
    if record.get('sha256')!=wheel['sha256'] or not record.get('files'):return False
    for name,info in record['files'].items():
        path=site/name
        if not path.is_file() or path.stat().st_size!=info['size']:return False
        if verify and digest(path)!=info['sha256']:return False
    return True


def wheel_members(archive):
    result=[]
    for member in archive.infolist():
        if member.is_dir():continue
        raw=member.filename;parts=PurePosixPath(raw).parts
        if not parts or raw.startswith('/') or '\\' in raw or ':' in raw or '..' in parts or ((member.external_attr>>16)&0o170000)==0o120000:
            raise ValueError('Unsafe wheel member')
        if parts[0].endswith('.data'):
            if len(parts)<3 or parts[1] not in ('purelib','platlib'):continue
            parts=parts[2:]
        result.append((member,PurePosixPath(*parts).as_posix()))
    return result


def install_wheel(path,wheel,site,state):
    if digest(path)!=wheel['sha256']:raise ValueError('Wheel checksum mismatch: '+wheel['name'])
    files={}
    with zipfile.ZipFile(path) as archive:
        members=wheel_members(archive)  # Validate every path before writing.
        for member,name in members:
            target=site/name;target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_name(target.name+'.ttn-tmp')
            with archive.open(member) as source,temporary.open('wb') as output:shutil.copyfileobj(source,output)
            os.replace(temporary,target)
            files[name]={'size':target.stat().st_size,'sha256':digest(target)}
    # Namespace packages may share files; their last installer owns the file.
    for previous in state.values():
        for name in files:previous.get('files',{}).pop(name,None)
    state[wheel['name']]={'sha256':wheel['sha256'],'files':files}


def download(wheel,cache):
    target=cache/wheel['filename']
    if target.is_file() and digest(target)==wheel['sha256']:return target
    temporary=target.with_name(target.name+'.partial')
    print('Download:',wheel['name'],wheel['version'],flush=True)
    try:
        with urllib.request.urlopen(wheel['url'],timeout=60) as response,temporary.open('wb') as output:
            shutil.copyfileobj(response,output,1024*1024)
        if digest(temporary)!=wheel['sha256']:raise ValueError('Download checksum mismatch: '+wheel['name'])
        os.replace(temporary,target)
    finally:temporary.unlink(missing_ok=True)
    return target


def setup(root,offline_wheels=None,verify=False):
    lock=load_lock(root);site=root/'runtime'/'Lib'/'site-packages';site.mkdir(parents=True,exist_ok=True)
    cache=root/'.setup-cache';cache.mkdir(exist_ok=True);state=read_state(root)
    for index,wheel in enumerate(lock['wheels'],1):
        print(f'[{index}/{len(lock["wheels"])}] {wheel["name"]}',flush=True)
        if installed(wheel,site,state,verify):continue
        path=Path(offline_wheels)/wheel['filename'] if offline_wheels else download(wheel,cache)
        install_wheel(path,wheel,site,state)
        target=root/'runtime'/'ttn-installed.json';temporary=target.with_suffix('.tmp')
        temporary.write_text(json.dumps(state),encoding='utf-8');os.replace(temporary,target)
    return lock


def check(root):
    lock=load_lock(root);state=read_state(root);site=root/'runtime'/'Lib'/'site-packages'
    if any(not installed(w,site,state) for w in lock['wheels']):return False
    # Runs only in the private interpreter. Native Qt/CFFI imports expose missing
    # dependent DLLs as well as missing distributions; no Garmin network calls.
    for wheel in lock['wheels']:
        if importlib.metadata.version(wheel['name'])!=wheel['version']:return False
    from PySide6 import QtWidgets,QtNetwork,QtWebEngineWidgets  # noqa: F401
    import curl_cffi,garminconnect,openpyxl,fitdecode,tzdata  # noqa: F401
    required=['PySide6/plugins/platforms/qwindows.dll','PySide6/QtWebEngineProcess.exe']
    return all((site/name).is_file() for name in required)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('check','setup','verify'))
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--offline-wheels',type=Path);args=parser.parse_args()
    try:
        if args.action=='check':return 0 if check(args.root) else 1
        setup(args.root,args.offline_wheels,verify=args.action=='verify')
        return 0
    except Exception as exc:
        # Setup receives no Garmin credentials. Keep messages concise and useful.
        print('Einrichtung fehlgeschlagen / Setup failed:',type(exc).__name__,str(exc),file=sys.stderr)
        return 1


if __name__=='__main__':sys.exit(main())
