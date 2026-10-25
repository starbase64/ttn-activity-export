"""Assemble a Windows x64 portable folder from official Python + Windows wheels.

This assembly is host-independent; execution still needs Windows validation.
Obtain wheels with: python -m pip download --only-binary=:all: --platform
win_amd64 --python-version 3.13 --implementation cp --abi cp313 -r requirements.txt -d WHEELS
"""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path,PurePosixPath

PYTHON_SHA256='97dae5274cc54867065e8d5a3226e48c35017ed332a0fdb0e27d5b5821961297'

def build(runtime_zip,wheels,output):
    source=Path(__file__).resolve().parent;output=Path(output).resolve()
    if output.exists():raise ValueError('Choose an empty output path')
    if hashlib.sha256(Path(runtime_zip).read_bytes()).hexdigest()!=PYTHON_SHA256:raise ValueError('Official Python 3.13.16 x64 checksum mismatch')
    runtime=output/'runtime';site=runtime/'Lib'/'site-packages';app=output/'app';site.mkdir(parents=True);app.mkdir()
    with zipfile.ZipFile(runtime_zip) as z:z.extractall(runtime)
    (runtime/'python313._pth').write_text('python313.zip\n.\nLib/site-packages\n../app\nimport site\n',encoding='utf-8')
    manifests=[]
    for wheel in sorted(Path(wheels).glob('*.whl')):
        if 'win_' in wheel.name and 'win_amd64' not in wheel.name:raise ValueError('Wrong Windows architecture')
        manifests.append({'file':wheel.name,'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest()})
        with zipfile.ZipFile(wheel) as z:
            for member in z.infolist():
                if member.is_dir():continue
                parts=PurePosixPath(member.filename).parts
                if '..' in parts or not parts or member.filename.startswith('/'):raise ValueError('Invalid wheel member')
                if parts[0].endswith('.data'):
                    if len(parts)<3 or parts[1] not in ('purelib','platlib'):continue
                    parts=parts[2:]
                target=site.joinpath(*parts);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(member))
    if not manifests:raise ValueError('No wheels')
    for file in source.glob('*.py'):
        if file.name!='build_portable_bundle.py':shutil.copy2(file,app/file.name)
    shutil.copytree(source/'docs',app/'docs')
    for name in ('LICENSE','README.md','THIRD_PARTY_NOTICES.md','CHANGELOG.md','ROADMAP.md','requirements.txt'):
        shutil.copy2(source/name,output/name)
    (output/'Start-TTN-Activity-Export.cmd').write_bytes(b'''@echo off\r
setlocal\r
cd /d "%~dp0"\r
if not exist "%LOCALAPPDATA%\\TTNTools\\GarminExportStudio" mkdir "%LOCALAPPDATA%\\TTNTools\\GarminExportStudio"\r
"%~dp0runtime\\python.exe" "%~dp0app\\app.py" %* > "%LOCALAPPDATA%\\TTNTools\\GarminExportStudio\\startup.log" 2>&1\r
if errorlevel 1 (\r
 echo Start fehlgeschlagen / Startup failed.\r
 echo Protokoll / Log: %LOCALAPPDATA%\\TTNTools\\GarminExportStudio\\startup.log\r
 pause\r
)\r
''')
    (output/'Demo.cmd').write_bytes(b'@echo off\r\ncall "%~dp0Start-TTN-Activity-Export.cmd" --demo\r\n')
    (output/'BITTE-ZUERST-LESEN.txt').write_text('''TTN Activity Export 0.6.1-preview — Windows x64 portable

1. Gesamte ZIP in einen eigenen Ordner entpacken.
2. Start-TTN-Activity-Export.cmd doppelklicken.
3. Python und die Abhängigkeiten sind enthalten; keine Python-Installation nötig.
   Das Konsolenfenster gehört zur App und bleibt während ihrer Nutzung geöffnet.
4. Demo.cmd zeigt künstliche Beispieldaten; Start ohne --demo für das echte Konto.
5. Vorhandene .sqlite-Dateien auf der Seite Daten öffnen.

WICHTIG: Das Paket wurde auf Linux zusammengesetzt und statisch geprüft,
aber hier noch nicht unter Windows ausgeführt. Kein signierter Installer.
Die separate GitHub-Buildanleitung erzeugt eine reguläre Windows-EXE.
Google Maps benötigt optional einen eigenen API-Schlüssel. Die normale
lokale Datennutzung braucht keinen Schlüssel.

English: Extract everything and double-click Start-TTN-Activity-Export.cmd.
Bundled Python; no installation needed. Console stays open while the app runs.
Assembled and statically checked on Linux, not executed on Windows here.
For errors, see %LOCALAPPDATA%/TTNTools/GarminExportStudio/startup.log.
App logs and Garmin sessions are kept in the local user profile, not in this folder.
''',encoding='utf-8')
    (output/'DEPENDENCY-MANIFEST.json').write_text(json.dumps({'python':'3.13.16','python_url':'https://www.python.org/ftp/python/3.13.16/python-3.13.16-embed-amd64.zip','python_sha256':PYTHON_SHA256,'wheels':manifests,'windows_execution_tested':False},indent=2),encoding='utf-8')
    # Keep full installed distribution metadata/licenses and replaceable shared Qt libraries.
    required=['PySide6/QtWidgets.pyd','PySide6/QtNetwork.pyd','PySide6/plugins/platforms/qwindows.dll','PySide6/QtWebEngineWidgets.pyd','PySide6/QtWebEngineProcess.exe','_cffi_backend.cp313-win_amd64.pyd','tzdata/__init__.py']
    for name in required:
        if not (site/name).is_file():raise ValueError('Missing Windows dependency: '+name)
    for executable in (runtime/'python.exe',runtime/'pythonw.exe',site/'PySide6/QtWebEngineProcess.exe'):
        if executable.read_bytes()[:2]!=b'MZ':raise ValueError('Invalid Windows executable')
    return output

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('runtime_zip');parser.add_argument('wheels');parser.add_argument('output');args=parser.parse_args()
    print(build(args.runtime_zip,args.wheels,args.output))
