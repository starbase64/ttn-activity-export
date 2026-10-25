"""Publish only a successful same-repository main push's verified Windows artifact."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

ARTIFACT='TTN-Activity-Export-Windows-Starter'
WORKFLOW='Windows starter tests and package'


def validate_source(event,repository):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository):raise ValueError('Invalid repository')
    run=event.get('workflow_run',{})
    if (run.get('event'),run.get('head_branch'),run.get('conclusion'),run.get('status'),run.get('name'))!=('push','main','success','completed',WORKFLOW):raise ValueError('Untrusted workflow source')
    if run.get('head_repository',{}).get('full_name')!=repository or event.get('repository',{}).get('full_name')!=repository:raise ValueError('Cross-repository workflow source')
    if not re.fullmatch('[a-f0-9]{40}',str(run.get('head_sha',''))) or type(run.get('id')) is not int:raise ValueError('Invalid workflow identity')
    return run


def python_version(data):
    for node in ast.parse(data.decode('utf-8')).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in node.targets):return ast.literal_eval(node.value)
    raise ValueError('Missing app version')


def prepare_artifact(folder,version,output):
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Only stable release versions are published')
    source=Path(folder)/(ARTIFACT+'.zip');checksum=source.with_suffix('.zip.sha256')
    if source.is_symlink() or not source.is_file() or source.stat().st_size>50*1024**2:raise ValueError('Invalid Windows package')
    recorded=checksum.read_text(encoding='ascii').strip().split()
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if recorded!=[digest,source.name]:raise ValueError('Windows artifact checksum mismatch')
    with zipfile.ZipFile(source) as archive:
        if archive.testzip():raise ValueError('Damaged Windows package')
        root='TTN-Activity-Export/'
        if python_version(archive.read(root+'app/app.py'))!=version:raise ValueError('Windows package version differs from release')
        for name in ('Start-TTN-Activity-Export.cmd','LICENSE','THIRD_PARTY_NOTICES.md','app/docs/ANLEITUNG.md','app/docs/USER_GUIDE.md'):
            if root+name not in archive.namelist():raise ValueError('Incomplete Windows package')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    target=output/('TTN-Activity-Export-Windows-'+version+'.zip');shutil.copyfile(source,target)
    sha=target.with_suffix('.zip.sha256');sha.write_text(digest+'  '+target.name+'\n',encoding='ascii')
    return target,sha


def command(*args):return subprocess.check_output(list(args),text=True)
def api(repository,path):return json.loads(command('gh','api','repos/'+repository+'/'+path))


def main():
    repository=os.environ['GITHUB_REPOSITORY']
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text());run=validate_source(event,repository)
    sha=run['head_sha'];run_id=run['id']
    if command('git','rev-parse','HEAD').strip()!=sha:raise ValueError('Checkout differs from tested commit')
    actual=api(repository,'actions/runs/'+str(run_id))
    if any(actual.get(k)!=run.get(k) for k in ('head_sha','event','head_branch','conclusion','status','name')) or actual.get('path')!='.github/workflows/starter.yml':raise ValueError('Windows run verification failed')
    if actual.get('head_repository',{}).get('full_name')!=repository:raise ValueError('Invalid Windows run repository')
    if api(repository,'git/ref/heads/main')['object']['sha']!=sha:
        print('A newer main commit exists; wait for its checks.');return
    config=json.loads(Path('release.json').read_text())
    if config.get('publish') is not True:print('Release publication disabled.');return
    version=config['version']
    if not isinstance(version,str) or not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid stable release version')
    if python_version(Path('app.py').read_bytes())!=version:raise ValueError('Release version differs from source')
    notes=Path('docs/releases')/('v'+version+'.md')
    if not notes.is_file():raise ValueError('Missing release notes')
    tag='v'+version
    releases=json.loads(command('gh','release','list','--repo',repository,'--limit','100','--json','tagName,isDraft'))
    existing=next((r for r in releases if r['tagName']==tag),None)
    if existing and not existing['isDraft']:print('Already published: '+tag);return
    if existing:
        draft=json.loads(command('gh','release','view',tag,'--repo',repository,'--json','targetCommitish'))
        if draft['targetCommitish']!=sha:raise ValueError('Existing release draft targets another commit')
    with tempfile.TemporaryDirectory(prefix='validated-windows-') as directory:
        command('gh','run','download',str(run_id),'--repo',repository,'--name',ARTIFACT,'--dir',directory)
        package,checksum=prepare_artifact(directory,version,Path(directory)/'release')
        if existing:
            command('gh','release','upload',tag,str(package),str(checksum),'--repo',repository,'--clobber')
        else:
            command('gh','release','create',tag,str(package),str(checksum),'--repo',repository,'--target',sha,'--title','TTN Activity Export '+version,'--notes-file',str(notes),'--draft')
        # Publication is the final mutation, after successful validation/upload.
        command('gh','release','edit',tag,'--repo',repository,'--draft=false','--prerelease=false','--latest')
        print('Published: https://github.com/'+repository+'/releases/tag/'+tag)


if __name__=='__main__':main()
