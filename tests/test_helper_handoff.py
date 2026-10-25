"""Exercise the real app-to-PowerShell process launch after its parent exits."""
import json
import threading
from pathlib import Path
import subprocess
import sys
import time

import pytest


@pytest.mark.skipif(sys.platform!='win32',reason='Native Windows process creation')
def test_helper_runs_after_the_launching_app_exits(tmp_path):
    work=tmp_path/"Update ü's folder with spaces";work.mkdir()
    plan=work/'plan.json';plan.write_text(json.dumps({'token':'a'*32}),encoding='utf-8')
    (work/'windows_update.ps1').write_text('''param([string]$PlanPath,[int]$ParentProcessId)
$ErrorActionPreference='Stop'
$folder=Split-Path -Parent $PlanPath
$plan=Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json
[IO.File]::WriteAllText((Join-Path $folder 'helper-ready.json'),(@{schema=1;token=$plan.token;pid=$PID}|ConvertTo-Json))
[IO.File]::WriteAllText((Join-Path $folder 'started.txt'),'started')
$parent=Get-Process -Id $ParentProcessId -ErrorAction SilentlyContinue
if ($null -ne $parent -and -not $parent.WaitForExit(15000)) { exit 2 }
[IO.File]::WriteAllText((Join-Path $folder 'finished.txt'),'parent exited')
''',encoding='ascii')
    source=str(Path(__file__).resolve().parents[1])
    child='import sys,threading;sys.path.insert(0,sys.argv[1]);from install_updates import start_helper,wait_helper_ready;p=start_helper(sys.argv[2]);wait_helper_ready(sys.argv[2],p,threading.Event())'
    subprocess.run([sys.executable,'-c',child,source,str(plan)],check=True,timeout=30,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    deadline=time.monotonic()+20
    while not (work/'finished.txt').exists() and time.monotonic()<deadline:time.sleep(.1)
    log=(work/'helper-output.log').read_text(encoding='utf-8',errors='replace')
    assert (work/'started.txt').exists(), 'The app-created helper never entered its script. '+log
    assert (work/'finished.txt').read_text()=='parent exited',log


def test_handoff_requires_matching_live_process_acknowledgement(tmp_path):
    from types import SimpleNamespace
    from install_updates import wait_helper_ready
    from updater import UpdateError,UpdateCancelled
    plan=tmp_path/'plan.json';plan.write_text(json.dumps({'token':'a'*32}))
    ready=tmp_path/'helper-ready.json'
    process=SimpleNamespace(pid=123,poll=lambda:None)
    for payload in ({'schema':1,'token':'b'*32,'pid':123},{'schema':1,'token':'a'*32,'pid':456}):
        ready.write_text(json.dumps(payload))
        with pytest.raises(UpdateError,match='helper_timeout'):wait_helper_ready(plan,process,threading.Event(),timeout=0)
    ready.write_text(json.dumps({'schema':1,'token':'a'*32,'pid':123}))
    wait_helper_ready(plan,process,threading.Event(),timeout=0)
    process.poll=lambda:1
    with pytest.raises(UpdateError,match='helper_exited'):wait_helper_ready(plan,process,threading.Event(),timeout=0)
    cancel=threading.Event();cancel.set()
    with pytest.raises(UpdateCancelled):wait_helper_ready(plan,process,cancel,timeout=0)
