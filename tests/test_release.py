"""Publication gates and artifact integrity; no GitHub calls or releases in tests."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
import pytest
from scripts import publish_release as release

REPO='starbase64/ttn-activity-export'
SHA='a'*40


def event():return {'repository':{'full_name':REPO},'workflow_run':{'id':123,'head_sha':SHA,'event':'push','head_branch':'main','conclusion':'success','status':'completed','name':release.WORKFLOW,'head_repository':{'full_name':REPO}}}


def artifact(folder,version='0.6.8'):
    folder.mkdir(parents=True,exist_ok=True);path=folder/(release.ARTIFACT+'.zip')
    with zipfile.ZipFile(path,'w') as archive:
        archive.writestr('TTN-Activity-Export/app/app.py',"VERSION = '"+version+"'\n")
        for name in ('Start-TTN-Activity-Export.cmd','LICENSE','THIRD_PARTY_NOTICES.md','app/docs/ANLEITUNG.md','app/docs/USER_GUIDE.md'):archive.writestr('TTN-Activity-Export/'+name,'synthetic fixture')
    path.with_suffix('.zip.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.name+'\n')
    return path


def test_release_artifact_is_verified_and_renamed_without_changing_bytes(tmp_path):
    source=artifact(tmp_path/'source');package,checksum=release.prepare_artifact(source.parent,'0.6.8',tmp_path/'out')
    assert source.read_bytes()==package.read_bytes()
    assert package.name=='TTN-Activity-Export-Windows-0.6.8.zip'
    assert checksum.read_text().split()==[hashlib.sha256(package.read_bytes()).hexdigest(),package.name]
    source.with_suffix('.zip.sha256').write_text('0'*64+'  '+source.name)
    with pytest.raises(ValueError,match='checksum'):release.prepare_artifact(source.parent,'0.6.8',tmp_path/'invalid')
    source=artifact(tmp_path/'preview','0.6.8-preview')
    with pytest.raises(ValueError,match='version'):release.prepare_artifact(source.parent,'0.6.8',tmp_path/'invalid')


@pytest.mark.parametrize('field,value',[('event','pull_request'),('head_branch','other'),('conclusion','failure'),('status','in_progress'),('head_sha','unsafe'),('name','Untrusted CI'),('head_repository',{'full_name':'attacker/fork'})])
def test_publication_rejects_untrusted_or_failed_workflow_sources(field,value):
    data=event();data['workflow_run'][field]=value
    with pytest.raises(ValueError):release.validate_source(data,REPO)


@pytest.fixture
def publisher(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);source=artifact(tmp_path/'artifact')
    (tmp_path/'app.py').write_text("VERSION = '0.6.8'\n");(tmp_path/'release.json').write_text('{"version":"0.6.8","publish":true}')
    notes=tmp_path/'docs/releases/v0.6.8.md';notes.parent.mkdir(parents=True);notes.write_text('Release notes')
    data=event();event_path=tmp_path/'event.json';event_path.write_text(json.dumps(data))
    monkeypatch.setenv('GITHUB_REPOSITORY',REPO);monkeypatch.setenv('GITHUB_EVENT_PATH',str(event_path))
    calls=[];state={'existing':[],'draft_sha':SHA}
    def api(repository,path):
        assert repository==REPO
        if path=='git/ref/heads/main':return {'object':{'sha':SHA}}
        assert path=='actions/runs/123';return {**data['workflow_run'],'path':'.github/workflows/starter.yml'}
    def command(*args):
        calls.append(args)
        if args[:2]==('git','rev-parse'):return SHA+'\n'
        if args[:3]==('gh','release','list'):return json.dumps(state['existing'])
        if args[:3]==('gh','release','view'):return json.dumps({'targetCommitish':state['draft_sha']})
        if args[:3]==('gh','run','download'):
            target=Path(args[args.index('--dir')+1]);shutil.copy2(source,target/source.name);shutil.copy2(source.with_suffix('.zip.sha256'),target/(source.name+'.sha256'))
        return ''
    monkeypatch.setattr(release,'api',api);monkeypatch.setattr(release,'command',command)
    return calls,state,source


def test_release_is_uploaded_as_draft_before_final_publication(publisher):
    calls,state,source=publisher;release.main()
    create=next(c for c in calls if c[:3]==('gh','release','create'))
    assert '--draft' in create and create[create.index('--target')+1]==SHA
    assert calls[-1][:3]==('gh','release','edit') and '--draft=false' in calls[-1] and '--latest' in calls[-1]


def test_existing_published_release_is_not_overwritten_and_wrong_draft_is_rejected(publisher):
    calls,state,source=publisher;state['existing']=[{'tagName':'v0.6.8','isDraft':False}];release.main()
    assert not any(c[:3] in [('gh','release','create'),('gh','release','edit'),('gh','run','download')] for c in calls)
    state['existing'][0]['isDraft']=True;state['draft_sha']='b'*40
    with pytest.raises(ValueError,match='another commit'):release.main()


def test_corrupt_windows_artifact_prevents_release_creation(publisher):
    calls,state,source=publisher;source.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='checksum'):release.main()
    assert not any(c[:3] in [('gh','release','create'),('gh','release','edit')] for c in calls)
