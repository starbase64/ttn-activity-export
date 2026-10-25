"""Native CI: cached offline update, failed-install rollback and launcher fallback."""
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from updater import MANIFEST,manifest_bytes,installation_context,prepare_update,version as parse_version
from install_updates import start_helper,wait_helper_ready


def make_package(original,target,version,broken=False):
    with zipfile.ZipFile(original) as archive:
        files={name[len('TTN-Activity-Export/'):]:archive.read(name) for name in archive.namelist() if not name.endswith('/') and not name.endswith('/'+MANIFEST)}
    code=files['app/app.py'].decode('utf-8')
    code=re.sub(r"(?m)^VERSION = '[^']+'","VERSION = '"+version+"'",code)
    if broken:code=code.replace('from __future__ import annotations','from __future__ import annotations\nraise RuntimeError("synthetic update failure")',1)
    files['app/app.py']=code.encode('utf-8')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():archive.writestr('TTN-Activity-Export/'+name,data)
        archive.writestr('TTN-Activity-Export/'+MANIFEST,manifest_bytes(files,version))


def install(context,package,version,expected):
    asset={'version':version,'sha256':hashlib.sha256(package.read_bytes()).hexdigest()}
    plan=Path(prepare_update(context,asset,downloader=lambda a,p,*args:shutil.copyfile(package,p)))
    sleeper=subprocess.Popen([str(context['root']/'runtime/python.exe'),'-c','import time;time.sleep(3)'])
    helper=start_helper(plan,parent_process_id=sleeper.pid,no_restart=True,no_ui=True)
    wait_helper_ready(plan,helper,threading.Event())
    returncode=helper.wait(timeout=1000)
    sleeper.wait(timeout=20)
    if returncode!=expected:
        for name in ('helper-output.log','update-error.log','setup-output.log','setup-error.log'):
            path=plan.parent/name
            if path.exists():print(name,path.read_text(encoding='utf-8',errors='replace')[-12000:])
        raise AssertionError('Unexpected update helper exit: '+str(returncode))


def main():
    original_root=Path(sys.argv[1]).resolve();package=Path(sys.argv[2]).resolve()
    root=original_root.with_name("TTN Update ü's space test");original_root.rename(root)
    current=json.loads((root/MANIFEST).read_text())['version']
    parsed=parse_version(current)
    good_version=f'{parsed.major}.{parsed.minor}.{parsed.patch+1}'
    bad_version=f'{parsed.major}.{parsed.minor}.{parsed.patch+2}'
    context=installation_context(root/'app/app.py',current)
    assert context is not None
    baseline=(root/'app/app.py').read_bytes();launcher=(root/'Start-TTN-Activity-Export.cmd').read_bytes()
    (root/'account-data.sqlite').write_bytes(b'keep user database');(root/'app/unmanaged-data.sqlite').write_bytes(b'keep extra data')
    with tempfile.TemporaryDirectory() as folder:
        good=Path(folder)/'good.zip';bad=Path(folder)/'bad.zip'
        make_package(package,good,good_version);install(context,good,good_version,0)
        pointer=json.loads((root/'.active-version.json').read_text());assert pointer['version']==good_version
        active=root/pointer['path'];context=installation_context(active/'app/app.py',good_version);assert context['controller']==root
        subprocess.run([str(active/'runtime/python.exe'),'-c','import app; assert app.VERSION=='+repr(good_version)],check=True)
        make_package(package,bad,bad_version,broken=True);install(context,bad,bad_version,1)
        assert json.loads((root/'.active-version.json').read_text())['version']==good_version
        assert (root/'app/app.py').read_bytes()==baseline and (root/'Start-TTN-Activity-Export.cmd').read_bytes()==launcher
        assert (root/'account-data.sqlite').read_bytes()==b'keep user database' and (root/'app/unmanaged-data.sqlite').read_bytes()==b'keep extra data'
        # Even a later damaged active app falls back through the original shortcut.
        code=(active/'app/app.py').read_text(encoding='utf-8').replace('from __future__ import annotations','from __future__ import annotations\nraise RuntimeError("synthetic damaged active app")',1)
        (active/'app/app.py').write_text(code,encoding='utf-8')
        subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'bootstrap.ps1'),'--smoke-test'],check=True,timeout=120)
        assert not (root/'.active-version.json').exists()
    print('Windows updater: offline activation, failed-install preservation, launcher fallback and user-data preservation passed.')


if __name__=='__main__':main()
