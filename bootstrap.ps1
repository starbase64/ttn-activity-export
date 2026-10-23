param([Parameter(ValueFromRemainingArguments=$true)][string[]]$AppArgs)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot
$setupLock = $null
try {
    if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem) {
        throw 'Windows 10/11 x64 wird benoetigt / Windows 10/11 x64 is required.'
    }
    if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') {
        throw 'Dieses Paket ist fuer x64 / This package targets x64, not ARM64.'
    }
    try { $setupLock = [IO.File]::Open((Join-Path $PSScriptRoot '.setup.lock'),'OpenOrCreate','ReadWrite','None') }
    catch { throw 'App oder Einrichtung laeuft bereits, oder der Ordner ist nicht beschreibbar / App or setup is running, or folder is not writable.' }
    $lock = Get-Content -LiteralPath './windows-dependencies.lock.json' -Raw | ConvertFrom-Json
    $runtime = Join-Path $PSScriptRoot 'runtime'
    $python = Join-Path $runtime 'python.exe'
    $cache = Join-Path $PSScriptRoot '.setup-cache'
    New-Item -ItemType Directory -Path $cache -Force | Out-Null
    $runtimeReady = $false
    if (Test-Path -LiteralPath $python) {
        try {
            & $python -I -c "import sys,ssl,sqlite3,zipfile; sys.exit(0 if sys.version.split()[0]=='$($lock.python.version)' else 1)" 2>$null
            $runtimeReady = $LASTEXITCODE -eq 0
        } catch { $runtimeReady = $false }
    }
    if (-not $runtimeReady) {
        Write-Host 'Python wird lokal eingerichtet / Preparing private Python runtime...'
        $url = [Uri]$lock.python.url
        if ($url.Scheme -ne 'https' -or $url.Host -ne 'www.python.org') { throw 'Unexpected Python source.' }
        $zip = Join-Path $cache 'python-runtime.zip'
        if (-not (Test-Path -LiteralPath $zip) -or (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ne $lock.python.sha256) {
            $partial = "$zip.partial"
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $url -OutFile $partial -UseBasicParsing
            if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash -ne $lock.python.sha256) { throw 'Python checksum mismatch.' }
            Move-Item -LiteralPath $partial -Destination $zip -Force
        }
        $stage = Join-Path $cache ('python-' + [Guid]::NewGuid().ToString('N'))
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [IO.Compression.ZipFile]::ExtractToDirectory($zip,$stage)
        New-Item -ItemType Directory -Path $runtime -Force | Out-Null
        Copy-Item -Path (Join-Path $stage '*') -Destination $runtime -Recurse -Force
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
    # Isolated embedded runtime; never changes PATH, registry or system Python.
    $pth = "python313.zip`n.`nLib/site-packages`n../app`nimport site`n"
    [IO.File]::WriteAllText((Join-Path $runtime 'python313._pth'),$pth,[Text.UTF8Encoding]::new($false))
    $bootstrap = Join-Path $PSScriptRoot 'windows_bootstrap.py'
    & $python $bootstrap check
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Fehlende Pakete werden installiert oder repariert / Installing or repairing missing packages...'
        & $python $bootstrap verify 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'setup.log') -Append
        if ($LASTEXITCODE -ne 0) { throw 'Einrichtung fehlgeschlagen. Internetverbindung und setup.log pruefen / Check Internet connection and setup.log.' }
        & $python $bootstrap check
        if ($LASTEXITCODE -ne 0) { throw 'Abhaengigkeitspruefung fehlgeschlagen / Dependency check failed. See console and setup.log.' }
    }
    Write-Host 'TTN Garmin Export startet / Starting TTN Garmin Export...'
    & $python (Join-Path $PSScriptRoot 'app/app.py') @AppArgs
    if ($LASTEXITCODE -ne 0) { throw 'App beendet mit Fehler / App exited with an error.' }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
} finally {
    if ($null -ne $setupLock) { $setupLock.Dispose() }
}
