"""Exercise the real app-to-PowerShell process launch after its parent exits."""
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest


@pytest.mark.skipif(sys.platform!='win32',reason='Native Windows process creation')
def test_helper_runs_after_the_launching_app_exits(tmp_path):
    work=tmp_path/"Update ü's folder with spaces";work.mkdir()
    plan=work/'plan.json';plan.write_text('{}',encoding='utf-8')
    (work/'windows_update.ps1').write_text('''param([string]$PlanPath,[int]$ParentProcessId)
$ErrorActionPreference='Stop'
$folder=Split-Path -Parent $PlanPath
[IO.File]::WriteAllText((Join-Path $folder 'started.txt'),'started')
$parent=Get-Process -Id $ParentProcessId -ErrorAction SilentlyContinue
if ($null -ne $parent -and -not $parent.WaitForExit(15000)) { exit 2 }
[IO.File]::WriteAllText((Join-Path $folder 'finished.txt'),'parent exited')
''',encoding='ascii')
    source=str(Path(__file__).resolve().parents[1])
    child='import sys;sys.path.insert(0,sys.argv[1]);from install_updates import start_helper;start_helper(sys.argv[2])'
    subprocess.run([sys.executable,'-c',child,source,str(plan)],check=True,timeout=30,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    deadline=time.monotonic()+20
    while not (work/'finished.txt').exists() and time.monotonic()<deadline:time.sleep(.1)
    log=(work/'helper-output.log').read_text(encoding='utf-8',errors='replace')
    assert (work/'started.txt').exists(), 'The app-created helper never entered its script. '+log
    assert (work/'finished.txt').read_text()=='parent exited',log
