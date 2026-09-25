@echo off
title Metrics by JJ - System Telemetry Server
cls
echo =======================================================
echo           METRICS BY JJ - SYSTEM TELEMETRY HUB
echo =======================================================
echo.
echo [*] Checking Python dependencies...
python -m pip install -r backend\requirements.txt --quiet

echo [*] Starting telemetry server on port 8989...
echo.
echo =======================================================
echo  LOCAL ACCESS:    http://localhost:8989
echo  LAN ACCESS:      http://0.0.0.0:8989
echo =======================================================
echo.
echo Tip: To unlock full CPU/GPU temperatures, run
echo      LibreHardwareMonitor in the background.
echo.
echo Starting FastAPI Uvicorn Server...
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8989
pause
