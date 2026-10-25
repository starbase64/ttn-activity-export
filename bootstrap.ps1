param([Parameter(ValueFromRemainingArguments=$true)][string[]]$AppArgs)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot
function Get-TtnSha256([string]$Path) {
    $stream=[IO.File]::OpenRead($Path);$sha=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose();$stream.Dispose() }
}
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
    # The original shortcut stays valid: activate checked versions beside this
    # folder rather than overwriting a running program or touching user data.
    $activeFile=Join-Path $PSScriptRoot '.active-version.json'
    if (Test-Path -LiteralPath $activeFile) {
        $active=Get-Content -LiteralPath $activeFile -Raw | ConvertFrom-Json
        if ($active.schema -ne 1 -or $active.path -notmatch '^\.versions/[A-Za-z0-9_.-]+$') { throw 'Invalid active update pointer.' }
        $activeRoot=Join-Path $PSScriptRoot $active.path
        if ((Get-Item -LiteralPath (Split-Path -Parent $activeRoot)).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Invalid active update directory.' }
        if ((Get-Item -LiteralPath $activeRoot).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Invalid active update directory.' }
        $env:TTN_UPDATE_CONTROLLER=$PSScriptRoot
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $activeRoot 'bootstrap.ps1') @AppArgs
        $activeCode=$LASTEXITCODE
        if ($activeCode -eq 0) { exit 0 }
        # A failed new app cannot strand the old launcher. Restore its previous
        # checked destination (or this original package), then start it again.
        if ($null -eq $active.previous) { Remove-Item -LiteralPath $activeFile }
        else {
            if ($active.previous.path -notmatch '^\.versions/[A-Za-z0-9_.-]+$') { throw 'Invalid fallback update pointer.' }
            $fallback=@{schema=1;path=$active.previous.path;version=$active.previous.version;previous=$null}
            $temporary=$activeFile+'.tmp'
            [IO.File]::WriteAllText($temporary,($fallback | ConvertTo-Json),[Text.UTF8Encoding]::new($false))
            [IO.File]::Replace($temporary,$activeFile,$null)
        }
        Write-Host 'Update fehlgeschlagen; bisherige Version wird gestartet / Restarting the previous version.'
        $setupLock.Dispose();$setupLock=$null
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'bootstrap.ps1') @AppArgs
        exit $LASTEXITCODE
    }
    $lock = Get-Content -LiteralPath './windows-dependencies.lock.json' -Raw | ConvertFrom-Json
    $runtime = Join-Path $PSScriptRoot 'runtime'
    $python = Join-Path $runtime 'python.exe'
    $cache = Join-Path $PSScriptRoot '.setup-cache'
    # Reuse the original verified wheel/runtime cache across version folders.
    if ($env:TTN_UPDATE_CONTROLLER) {
        $controller=[IO.Path]::GetFullPath($env:TTN_UPDATE_CONTROLLER)
        $versions=Join-Path $controller '.versions'
        if ((Split-Path -Parent $PSScriptRoot) -eq $versions -and (Test-Path -LiteralPath (Join-Path $controller 'Start-TTN-Activity-Export.cmd'))) {
            $cache=Join-Path $controller '.setup-cache'
        }
    }
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
        if (-not (Test-Path -LiteralPath $zip) -or (Get-TtnSha256 $zip) -ne $lock.python.sha256) {
            $partial = "$zip.partial"
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $url -OutFile $partial -UseBasicParsing
            if ((Get-TtnSha256 $partial) -ne $lock.python.sha256) { throw 'Python checksum mismatch.' }
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
        & $python $bootstrap verify --cache-dir $cache 2>&1 | Tee-Object -FilePath (Join-Path $PSScriptRoot 'setup.log') -Append
        if ($LASTEXITCODE -ne 0) { throw 'Einrichtung fehlgeschlagen. Internetverbindung und setup.log pruefen / Check Internet connection and setup.log.' }
        & $python $bootstrap check
        if ($LASTEXITCODE -ne 0) { throw 'Abhaengigkeitspruefung fehlgeschlagen / Dependency check failed. See console and setup.log.' }
    }
    Write-Host 'TTN Activity Export startet / Starting TTN Activity Export...'
    & $python (Join-Path $PSScriptRoot 'app/app.py') @AppArgs
    if ($LASTEXITCODE -ne 0) { throw 'App beendet mit Fehler / App exited with an error.' }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
} finally {
    if ($null -ne $setupLock) { $setupLock.Dispose() }
}
