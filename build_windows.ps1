param([switch]$NoVenv)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if ($env:OS -ne 'Windows_NT') { throw 'This script builds on Windows only.' }
$PythonExe = 'python'
if (-not $NoVenv) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12+ is required.' }
    $PythonExe = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    & $PythonExe -m pip install -r requirements.txt -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
& $PythonExe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
& $PythonExe -m PyInstaller --noconfirm --clean --onedir --windowed --name TTNGarminExport --collect-all curl_cffi --collect-all ua_generator --collect-data tzdata app.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
& $PythonExe -m piplicenses --with-license-file --no-license-path --format=plain-vertical --output-file dist/TTNGarminExport/THIRD_PARTY_LICENSES.txt
if ($LASTEXITCODE -ne 0) { throw 'License collection failed.' }
Copy-Item LICENSE, README.md, THIRD_PARTY_NOTICES.md -Destination dist/TTNGarminExport/
Copy-Item docs -Destination dist/TTNGarminExport/docs -Recurse -Force
& $PythonExe -c "import sys, pathlib, shutil; p=pathlib.Path(sys.base_prefix)/'LICENSE.txt'; shutil.copyfile(p, 'dist/TTNGarminExport/PYTHON_LICENSE.txt') if p.exists() else sys.exit('Python license missing')"
if ($LASTEXITCODE -ne 0) { throw 'Python license collection failed.' }
Write-Output 'Ready: dist/TTNGarminExport/TTNGarminExport.exe (keep the entire folder together).'
