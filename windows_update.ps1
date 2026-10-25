param([Parameter(Mandatory=$true)][string]$PlanPath,[int]$ParentProcessId=0,[switch]$NoRestart,[switch]$NoUI)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$setupLock=$null; $form=$null; $success=$false; $activated=$false; $previousText=$null
$planFile=[IO.Path]::GetFullPath($PlanPath); $work=Split-Path -Parent $planFile
$controller=Split-Path -Parent (Split-Path -Parent $work)
$pointer=Join-Path $controller '.active-version.json'
function Get-TtnSha256([string]$Path) {
    $stream=[IO.File]::OpenRead($Path);$sha=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose();$stream.Dispose() }
}
function Write-AtomicJson([string]$Path,$Value) {
    $temporary=$Path+'.tmp'
    [IO.File]::WriteAllText($temporary,($Value | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    if (Test-Path -LiteralPath $Path) { [IO.File]::Replace($temporary,$Path,$null) }
    else { [IO.File]::Move($temporary,$Path) }
}
function Launch-App {
    if ($NoRestart) { return }
    $script=Join-Path $controller 'bootstrap.ps1'
    Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$script+'"')) -WindowStyle Hidden | Out-Null
}
try {
    if ((Split-Path -Leaf (Split-Path -Parent $work)) -ne '.updates' -or (Split-Path -Leaf $work) -notmatch '^[a-f0-9]{32}$') { throw 'Invalid update location.' }
    $plan=Get-Content -LiteralPath $planFile -Raw | ConvertFrom-Json
    if ($plan.schema -ne 1 -or $plan.token -ne (Split-Path -Leaf $work) -or [IO.Path]::GetFullPath($plan.controller) -ne $controller -or $plan.target -notmatch '^\.versions/[A-Za-z0-9_.-]+$') { throw 'Invalid update plan.' }
    $target=Join-Path $controller $plan.target
    if ((Get-Item -LiteralPath (Split-Path -Parent $target)).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Invalid update path.' }
    if ((Get-Item -LiteralPath $target).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Invalid update path.' }
    if ($ParentProcessId -gt 0) {
        $parent=Get-Process -Id $ParentProcessId -ErrorAction SilentlyContinue
        if ($null -ne $parent -and -not $parent.WaitForExit(60000)) { throw 'The previous app has not exited.' }
    }
    $deadline=[DateTime]::UtcNow.AddSeconds(60)
    do {
        try { $setupLock=[IO.File]::Open((Join-Path $controller '.setup.lock'),'OpenOrCreate','ReadWrite','None') }
        catch { if ([DateTime]::UtcNow -ge $deadline) { throw 'The app or another setup is still running.' }; Start-Sleep -Milliseconds 200 }
    } while ($null -eq $setupLock)
    if (Test-Path -LiteralPath $pointer) { $previousText=[IO.File]::ReadAllText($pointer) }
    $previous=$null
    if ($null -ne $previousText) {
        $old=$previousText | ConvertFrom-Json
        if ($old.schema -ne 1 -or $old.path -ne $plan.from) { throw 'The active version changed. Please check updates again.' }
        $previous=@{path=$old.path;version=$old.version}
    } elseif ($plan.from -ne '.') { throw 'The active version changed.' }
    $manifest=Get-Content -LiteralPath (Join-Path $target 'app-manifest.json') -Raw | ConvertFrom-Json
    if ($manifest.schema -ne 1 -or $manifest.protocol -ne 1 -or $manifest.distribution -ne 'windows-starter' -or $manifest.version -ne $plan.version) { throw 'Update manifest mismatch.' }
    foreach ($entry in $manifest.files.PSObject.Properties) {
        $name=$entry.Name
        if ($name -match '(^/|\\|:|(^|/)\.\.(/|$))') { throw 'Invalid package path.' }
        $file=Join-Path $target $name
        if (-not (Test-Path -LiteralPath $file -PathType Leaf) -or (Get-Item -LiteralPath $file).Length -ne $entry.Value.size -or (Get-TtnSha256 $file) -ne $entry.Value.sha256) { throw 'Update file checksum mismatch.' }
    }
    if (-not $NoUI) {
        Add-Type -AssemblyName System.Windows.Forms
        $form=New-Object Windows.Forms.Form; $form.Text='TTN Activity Export'; $form.Width=470; $form.Height=150; $form.ControlBox=$false; $form.StartPosition='CenterScreen'
        $label=New-Object Windows.Forms.Label; $label.Left=20; $label.Top=18; $label.Width=420; $label.Height=40
        $label.Text=if ($plan.language -eq 'de') { 'Update wird eingerichtet und geprueft. Die App startet anschliessend automatisch.' } else { 'Preparing and checking the update. The app will restart automatically.' }
        $form.Controls.Add($label);$bar=New-Object Windows.Forms.ProgressBar;$bar.Left=20;$bar.Top=65;$bar.Width=420;$bar.Style='Marquee';$form.Controls.Add($bar);$form.Show();[Windows.Forms.Application]::DoEvents()
    }
    $env:TTN_UPDATE_CONTROLLER=$controller
    $bootstrap=Join-Path $target 'bootstrap.ps1'
    $probe=Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$bootstrap+'"'),'--smoke-test') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $work 'setup-output.log') -RedirectStandardError (Join-Path $work 'setup-error.log')
    # Keep the process handle before it exits: Windows PowerShell can otherwise
    # return a null ExitCode for a completed Start-Process -PassThru process.
    $null=$probe.Handle
    $deadline=[DateTime]::UtcNow.AddMinutes(15)
    while (-not $probe.WaitForExit(200)) {
        if ($null -ne $form) { [Windows.Forms.Application]::DoEvents() }
        if ([DateTime]::UtcNow -ge $deadline) { & taskkill.exe /PID $probe.Id /T /F | Out-Null; throw 'Update setup timed out.' }
    }
    $probe.WaitForExit()
    if ($null -eq $probe.ExitCode) { throw 'The installation check returned no exit status.' }
    if ($probe.ExitCode -ne 0) { throw ('The new version failed its installation/startup check (exit '+$probe.ExitCode+').') }
    Write-AtomicJson $pointer @{schema=1;path=$plan.target;version=$plan.version;previous=$previous}
    $activated=$true;$success=$true
    Write-AtomicJson (Join-Path $work 'result.json') @{success=$true;version=$plan.version}
} catch {
    $success=$false
    $detail=$_.Exception.Message
    [IO.File]::WriteAllText((Join-Path $work 'update-error.log'),$detail,[Text.UTF8Encoding]::new($false))
    if ($activated) {
        if ($null -eq $previousText) { Remove-Item -LiteralPath $pointer -ErrorAction SilentlyContinue }
        else { Write-AtomicJson $pointer ($previousText | ConvertFrom-Json) }
    }
    if (-not $NoUI) {
        Add-Type -AssemblyName System.Windows.Forms
        [Windows.Forms.MessageBox]::Show('Update fehlgeschlagen. Die bisherige Version bleibt erhalten und wird wieder gestartet. / Update failed; restarting the previous version.'+"`n"+$detail,'TTN Activity Export') | Out-Null
    }
} finally {
    if ($null -ne $form) { $form.Close();$form.Dispose() }
    if ($null -ne $setupLock) { $setupLock.Dispose() }
}
Launch-App
if (-not $success) { exit 1 }
