@echo off
setlocal enabledelayedexpansion
title Metrics by JJ - Setup ^& Manager
cd /d "%~dp0"

:: 1. Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================================
    echo  [ERROR] Python is not installed or not in your PATH.
    echo ========================================================
    echo.
    echo  Metrics by JJ requires Python 3.10 or higher.
    echo  Please download and install Python from:
    echo  https://www.python.org/downloads/
    echo.
    echo  * Important: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Launch setup engine
python setup.py %*
if %ERRORLEVEL% NEQ 0 (
    pause
)
