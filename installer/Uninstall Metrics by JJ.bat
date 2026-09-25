@echo off
title Metrics by JJ - Uninstaller
echo.
echo   Metrics by JJ Uninstaller
echo   Requesting Administrator privileges...
echo.

powershell -NoProfile -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%~dp0uninstall.ps1""' -Verb RunAs -Wait"
