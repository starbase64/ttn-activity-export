import hashlib
import json
from pathlib import Path
import shutil
import threading
from types import SimpleNamespace
import zipfile
import pytest
from updater import (manifest_bytes,read_manifest,stage_package,installation_context,
 installer_asset,prepare_update,discard_prepared,UpdateError,UpdateCancelled,MANIFEST)


def files(version):
    return {'app/app.py':("VERSION = '"+version+"'\n").encode(),'bootstrap.ps1':b'# bootstrap',
            'windows_update.ps1':b'# helper','windows-dependencies.lock.json':b'{}','Start-TTN-Activity-Export.cmd':b'@echo off'}


def package(path,version='0.6.10',changes=None,extra=None):
    data=files(version);meta=manifest_bytes(data,version)
    data.update(changes or {});data.update(extra or {})
    with zipfile.ZipFile(path,'w') as archive:
        for name,raw in data.items():archive.writestr('TTN-Activity-Export/'+name,raw)
        archive.writestr('TTN-Activity-Export/'+MANIFEST,meta)
    return path


@pytest.fixture
def installed(tmp_path,monkeypatch):
    root=tmp_path/'App with spaces and ü';root.mkdir()
    data=files('0.6.9')
    for name,raw in data.items():p=root/name;p.parent.mkdir(exist_ok=True);p.write_bytes(raw)
    (root/MANIFEST).write_bytes(manifest_bytes(data,'0.6.9'));(root/'runtime').mkdir();(root/'runtime/python.exe').write_bytes(b'placeholder')
    (root/'app/my-data.sqlite').write_bytes(b'private database');(root/'settings.json').write_text('keep me')
    monkeypatch.setattr(shutil,'disk_usage',lambda *a:SimpleNamespace(free=10*1024**3))
    return installation_context(root/'app/app.py','0.6.9',platform='win32')


def test_context_requires_matching_starter_and_preserves_the_original_launcher(installed,tmp_path):
    ctx=installed;assert ctx and ctx['root']==ctx['controller']
    root=ctx['root'];assert installation_context(root/'app/app.py','0.6.8',platform='win32') is None
    child=root/'.versions/0.6.10-123';child.mkdir(parents=True)
    for name,raw in files('0.6.10').items():p=child/name;p.parent.mkdir(exist_ok=True);p.write_bytes(raw)
    (child/MANIFEST).write_bytes(manifest_bytes(files('0.6.10'),'0.6.10'));(child/'runtime').mkdir();(child/'runtime/python.exe').write_bytes(b'placeholder')
    (root/'.active-version.json').write_text(json.dumps({'schema':1,'path':'.versions/0.6.10-123','version':'0.6.10','previous':None}))
    assert installation_context(child/'app/app.py','0.6.10',platform='win32')['controller']==root
    assert installation_context(root/'app/app.py','0.6.9',platform='win32') is None


def test_only_uploaded_matching_github_assets_with_server_digests_are_installable():
    tag='v0.6.10';name='TTN-Activity-Export-Windows-0.6.10.zip'
    asset={'name':name,'state':'uploaded','size':123,'digest':'sha256:'+'a'*64,
           'browser_download_url':'https://github.com/starbase64/ttn-activity-export/releases/download/'+tag+'/'+name}
    assert installer_asset({'assets':[asset]},tag)['sha256']=='a'*64
    for change in ({'digest':None},{'state':'new'},{'size':-1},{'browser_download_url':'https://host.invalid/file.zip'}):
        assert installer_asset({'assets':[asset|change]},tag) is None


def test_staging_checks_every_file_and_does_not_touch_existing_data(installed,tmp_path):
    ctx=installed;source=package(tmp_path/'new.zip')
    asset={'version':'0.6.10','sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    def download(asset,target,*args):shutil.copyfile(source,target)
    plan=Path(prepare_update(ctx,asset,downloader=download));data=json.loads(plan.read_text())
    assert (ctx['root']/'app/my-data.sqlite').read_bytes()==b'private database'
    assert (ctx['root']/'settings.json').read_text()=='keep me'
    assert not (ctx['controller']/'.active-version.json').exists()
    target=ctx['controller']/data['target'];assert read_manifest((target/MANIFEST).read_bytes())['version']=='0.6.10'
    discard_prepared(plan);assert not target.exists() and not plan.exists()


@pytest.mark.parametrize('extra',[{'../escape.py':b'x'},{'app/CON.py':b'x'},{'app/a.py:stream':b'x'},{'app/App.py':b'x'},{'app/data.sqlite':b'x'}])
def test_zip_paths_and_unmanaged_payloads_are_rejected(tmp_path,extra):
    source=package(tmp_path/'unsafe.zip',extra=extra)
    with pytest.raises(UpdateError):stage_package(source,tmp_path/'stage','0.6.10')
    assert not (tmp_path/'escape.py').exists()


def test_corrupt_files_cancel_and_downgrades_do_not_activate_an_update(installed,tmp_path):
    ctx=installed;source=package(tmp_path/'bad.zip',changes={'app/app.py':b"VERSION='0.6.10'\n# altered"})
    asset={'version':'0.6.10','sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    def download(asset,target,*args):shutil.copyfile(source,target)
    with pytest.raises(UpdateError,match='checksum'):prepare_update(ctx,asset,downloader=download)
    cancel=threading.Event();cancel.set()
    with pytest.raises(UpdateCancelled):prepare_update(ctx,asset,cancel=cancel,downloader=lambda *a:pytest.fail('No request after cancellation'))
    with pytest.raises(UpdateError,match='version'):prepare_update(ctx,asset|{'version':'0.6.8'},downloader=download)
    assert not (ctx['root']/'.active-version.json').exists()
    assert (ctx['root']/'app/my-data.sqlite').read_bytes()==b'private database'


def test_declared_package_version_must_match_actual_app_code(tmp_path):
    source=package(tmp_path/'wrong.zip',changes={'app/app.py':b"VERSION='0.6.8'"})
    # Recompute the manifest too: metadata alone cannot claim a newer app.
    data=files('0.6.10');data['app/app.py']=b"VERSION='0.6.8'"
    with zipfile.ZipFile(source,'w') as archive:
        for name,raw in data.items():archive.writestr('TTN-Activity-Export/'+name,raw)
        archive.writestr('TTN-Activity-Export/'+MANIFEST,manifest_bytes(data,'0.6.10'))
    with pytest.raises(UpdateError,match='version'):stage_package(source,tmp_path/'stage','0.6.10')
