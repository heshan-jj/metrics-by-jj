@echo off
title Metrics by JJ - Installer
echo.
echo   Metrics by JJ Installer
echo   Requesting Administrator privileges...
echo.

powershell -NoProfile -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%~dp0install.ps1""' -Verb RunAs -Wait"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   [!] Installer exited with an error. Check service.log for details.
    pause
)
