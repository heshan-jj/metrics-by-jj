@echo off
title Metrics by JJ - System Telemetry Server
cls
echo =======================================================
echo           METRICS BY JJ - SYSTEM TELEMETRY HUB
echo =======================================================
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in your PATH.
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [*] Checking Python dependencies...
python -m pip install -r backend\requirements.txt --quiet

echo [*] Starting telemetry server on port 9090...
echo.
echo =======================================================
echo  LOCAL ACCESS:    http://localhost:9090
echo  LAN ACCESS:      http://0.0.0.0:9090
echo =======================================================
echo.
echo Tip: To unlock full CPU/GPU temperatures, run
echo      LibreHardwareMonitor in the background.
echo.
echo Starting FastAPI Uvicorn Server...
python -m uvicorn backend.main:app --host 0.0.0.0 --port 9090
pause
