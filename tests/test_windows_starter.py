import hashlib
import json
from pathlib import Path
import zipfile
import pytest
from build_starter import build
from windows_bootstrap import install_wheel,installed,setup


def fixture_wheel(tmp_path,member='example/module.py',data=b'VALUE=1\n'):
    path=tmp_path/'example-1.0-py3-none-any.whl'
    with zipfile.ZipFile(path,'w') as archive:
        info=zipfile.ZipInfo('placeholder');info.filename=member
        archive.writestr(info,data)  # Preserve deliberately unsafe separators on Windows too.
        archive.writestr('example-1.0.dist-info/METADATA','Name: example\nVersion: 1.0\n')
    return path,dict(name='example',version='1.0',filename=path.name,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),url='https://files.pythonhosted.org/example.whl')


def test_install_missing_and_corrupted_files_then_reuse_offline_without_download(tmp_path,monkeypatch):
    wheel,entry=fixture_wheel(tmp_path);root=tmp_path/'program';root.mkdir()
    (root/'windows-dependencies.lock.json').write_text(json.dumps({'schema':1,'wheels':[entry]}))
    setup(root,offline_wheels=tmp_path)
    site=root/'runtime/Lib/site-packages';state=json.loads((root/'runtime/ttn-installed.json').read_text())
    assert installed(entry,site,state,True)
    import windows_bootstrap
    monkeypatch.setattr(windows_bootstrap,'download',lambda *a:pytest.fail('Unnecessary download'))
    setup(root)
    target=site/'example/module.py';target.write_bytes(b'VALUE=2\n')
    assert not installed(entry,site,state,True)
    setup(root,offline_wheels=tmp_path,verify=True)
    assert target.read_bytes()==b'VALUE=1\n'
    target.unlink();setup(root,offline_wheels=tmp_path)
    assert target.read_bytes()==b'VALUE=1\n'


@pytest.mark.parametrize('member',['../escape.py','/absolute.py','C:/escape.py','example\\escape.py'])
def test_wheel_path_traversal_never_writes_outside_target(tmp_path,member):
    path,entry=fixture_wheel(tmp_path,member);site=tmp_path/'site'
    with pytest.raises(ValueError):install_wheel(path,entry,site,{})
    assert not site.exists() and not (tmp_path/'escape.py').exists()


def test_mismatched_hash_never_installs_wheel(tmp_path):
    path,entry=fixture_wheel(tmp_path);entry['sha256']='0'*64
    with pytest.raises(ValueError):install_wheel(path,entry,tmp_path/'site',{})
    assert not (tmp_path/'site').exists()


def test_starter_archive_contains_self_setup_and_no_runtime_or_personal_data(tmp_path):
    output=build(tmp_path/'starter.zip')
    with zipfile.ZipFile(output) as archive:
        names=archive.namelist()
        for name in ('bootstrap.ps1','Start-TTN-Activity-Export.cmd','windows_bootstrap.py','windows-dependencies.lock.json','app/app.py','app/branding.py','app/docs/ANLEITUNG.md','app/docs/USER_GUIDE.md'):
            assert 'TTN-Activity-Export/'+name in names
        assert not any('Garmin-Export.cmd' in n for n in names)
        assert not any('/runtime/' in n or n.endswith(('.log','.sqlite','.db')) for n in names)
        lock=json.loads(archive.read('TTN-Activity-Export/windows-dependencies.lock.json'))
        assert len(lock['wheels'])>=5 and all(w['url'].startswith('https://files.pythonhosted.org/') for w in lock['wheels'])
    assert output.with_suffix('.zip.sha256').read_text().startswith(hashlib.sha256(output.read_bytes()).hexdigest())
