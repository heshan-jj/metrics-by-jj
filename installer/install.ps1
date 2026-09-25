#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Installs Metrics by JJ as a Windows service.
#>

$ErrorActionPreference = "Stop"

$AppName    = "Metrics by JJ"
$SvcName    = "MetricsByJJ"
$AppDir     = Split-Path -Parent $PSScriptRoot   # project root (one level above installer\)
$PythonExe  = (Get-Command python -ErrorAction SilentlyContinue).Source

Write-Host ""
Write-Host "  ⚡ $AppName Installer" -ForegroundColor Cyan
Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# ── 1. Python check ───────────────────────────────────────────────
if (-not $PythonExe) {
    Write-Host "  [ERROR] Python not found in PATH." -ForegroundColor Red
    Write-Host "  Download Python from https://python.org/downloads/" -ForegroundColor Yellow
    Read-Host "  Press Enter to exit"; exit 1
}
Write-Host "  [✓] Python: $PythonExe" -ForegroundColor Green

# ── 2. Install pip dependencies ───────────────────────────────────
Write-Host "  [→] Installing Python dependencies..." -ForegroundColor Yellow
$reqFile = Join-Path $AppDir "backend\requirements.txt"
& $PythonExe -m pip install --quiet -r $reqFile
if ($LASTEXITCODE -ne 0) { Write-Host "  [ERROR] pip install failed." -ForegroundColor Red; exit 1 }

& $PythonExe -m pip install --quiet pywin32
if ($LASTEXITCODE -ne 0) { Write-Host "  [ERROR] pywin32 install failed." -ForegroundColor Red; exit 1 }

# Run pywin32 post-install to register COM objects
& $PythonExe -m pywin32_postinstall -install 2>$null
Write-Host "  [✓] Dependencies installed." -ForegroundColor Green

# ── 3. Stop + remove old service if present ──────────────────────
$existing = Get-Service -Name $SvcName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  [→] Removing existing service..." -ForegroundColor Yellow
    if ($existing.Status -eq "Running") { Stop-Service -Name $SvcName -Force }
    & $PythonExe (Join-Path $AppDir "service.py") remove 2>$null
    Start-Sleep -Seconds 2
}

# ── 4. Install service ────────────────────────────────────────────
Write-Host "  [→] Registering Windows service..." -ForegroundColor Yellow
Push-Location $AppDir
& $PythonExe service.py install
if ($LASTEXITCODE -ne 0) { Write-Host "  [ERROR] Service install failed." -ForegroundColor Red; Pop-Location; exit 1 }
Pop-Location

# Set service to auto-start and configure description
Set-Service -Name $SvcName -StartupType Automatic
$svc = Get-WmiObject Win32_Service -Filter "Name='$SvcName'"
$svc.Change($null,$null,$null,$null,$null,$null,$null,$null,$null,$null,$null) | Out-Null

# ── 5. Start service ──────────────────────────────────────────────
Write-Host "  [→] Starting service..." -ForegroundColor Yellow
Start-Service -Name $SvcName
Start-Sleep -Seconds 3

$status = (Get-Service -Name $SvcName).Status
if ($status -eq "Running") {
    Write-Host "  [✓] Service is RUNNING on port 8989." -ForegroundColor Green
} else {
    Write-Host "  [!] Service status: $status (check service.log for errors)" -ForegroundColor Yellow
}

# ── 6. Firewall rule ──────────────────────────────────────────────
$fwRule = Get-NetFirewallRule -DisplayName "Metrics by JJ" -ErrorAction SilentlyContinue
if (-not $fwRule) {
    Write-Host "  [→] Adding firewall rule (port 8989)..." -ForegroundColor Yellow
    New-NetFirewallRule `
        -DisplayName "Metrics by JJ" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 8989 `
        -Action Allow `
        -Profile Any `
        -Description "Allows LAN access to Metrics by JJ telemetry dashboard." | Out-Null
    Write-Host "  [✓] Firewall rule added." -ForegroundColor Green
}

# ── 7. Start-menu shortcut ────────────────────────────────────────
$ShortcutDir  = [Environment]::GetFolderPath("StartMenu") + "\Programs"
$ShortcutPath = "$ShortcutDir\Metrics by JJ.lnk"
$IconPath     = Join-Path $PSScriptRoot "metrics-jj.ico"
$WshShell     = New-Object -ComObject WScript.Shell
$Shortcut     = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath       = "http://localhost:8989"
$Shortcut.Description      = "Open Metrics by JJ dashboard"
if (Test-Path $IconPath) { $Shortcut.IconLocation = $IconPath }
$Shortcut.Save()
Write-Host "  [✓] Start Menu shortcut created." -ForegroundColor Green

# ── Done ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "  ✓  Metrics by JJ installed successfully!" -ForegroundColor Cyan
Write-Host "     Dashboard → http://localhost:8989" -ForegroundColor White
Write-Host "     Service   → Services.msc (MetricsByJJ)" -ForegroundColor White
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""

$open = Read-Host "  Open dashboard in browser now? [Y/n]"
if ($open -ne "n" -and $open -ne "N") {
    Start-Process "http://localhost:8989"
}
