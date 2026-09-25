#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Uninstalls Metrics by JJ service and removes related shortcuts/firewall rules.
#>

$ErrorActionPreference = "SilentlyContinue"
$SvcName   = "MetricsByJJ"
$AppDir    = Split-Path -Parent $PSScriptRoot
$PythonExe = (Get-Command python).Source

Write-Host ""
Write-Host "  ⚡ Metrics by JJ Uninstaller" -ForegroundColor Cyan
Write-Host ""

# Stop service
$svc = Get-Service -Name $SvcName -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -eq "Running") {
    Write-Host "  [→] Stopping service..." -ForegroundColor Yellow
    Stop-Service -Name $SvcName -Force
    Start-Sleep -Seconds 2
}

# Remove service
if ($svc) {
    Write-Host "  [→] Removing service registration..." -ForegroundColor Yellow
    Push-Location $AppDir
    & $PythonExe service.py remove 2>$null
    Pop-Location
    Start-Sleep -Seconds 1
    Write-Host "  [✓] Service removed." -ForegroundColor Green
}

# Remove firewall rule
Remove-NetFirewallRule -DisplayName "Metrics by JJ" -ErrorAction SilentlyContinue
Write-Host "  [✓] Firewall rule removed." -ForegroundColor Green

# Remove Start Menu shortcut
$ShortcutPath = [Environment]::GetFolderPath("StartMenu") + "\Programs\Metrics by JJ.lnk"
if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
    Write-Host "  [✓] Start Menu shortcut removed." -ForegroundColor Green
}

Write-Host ""
Write-Host "  Metrics by JJ has been uninstalled." -ForegroundColor Cyan
Write-Host "  The application files in $AppDir were NOT deleted." -ForegroundColor DarkGray
Write-Host ""
Read-Host "  Press Enter to close"
