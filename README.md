# ⚡ Metrics by JJ

> Real-time system metrics monitor & telemetry hub designed for Windows, accessible across your private local network (LAN) from any phone, tablet, or browser.

![Telemetry Dashboard Preview](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python)
![WebSockets](https://img.shields.io/badge/WebSockets-Realtime-00f2fe?style=for-the-badge)

---

## 🚀 Features

- **⚡ Real-time Telemetry via WebSockets (1-sec intervals)**: No polling overhead; updates push instantly.
- **🖥️ CPU Performance**: Overall load %, per-core load grid (e.g. 12 cores individual bars), frequency (GHz), logical & physical core counts.
- **🎮 GPU Detection**: Model name (e.g. NVIDIA RTX 2050), temperature, clock speed, power usage.
- **🧠 Memory (RAM & Swap)**: Used vs total GB, live usage percentage, pagefile metrics.
- **💾 Storage Drives**: Partition capacity, used/free bytes, live Disk Read/Write transfer rates.
- **📡 Network Bandwidth & Sparklines**: Real-time 60-second rolling upload/download throughput graph.
- **🛠️ Windows Services Monitor**: Search and filter running/stopped Windows services with PIDs and startup types.
- **📊 Top Processes**: Live top 10 CPU/Memory hogs with PID, RSS memory, and thread counts.
- **🌐 Private LAN Access**: Auto-detects and displays your LAN IPs (e.g., `http://192.168.8.164:8989`) with one-click copy chips.

---

## 📦 1-Click Setup & Manager

Metrics by JJ includes a zero-PowerShell setup and management engine.

### ⚡ Easy Setup (One-Click)
Double-click **[`Setup.bat`](file:///d:/Projects/metrics%20by%20jj/Setup.bat)** in the project root.

The setup utility automatically:
1. Verifies Python 3.10+ in your environment
2. Prompts for Administrator privileges (via Windows native UAC elevation, no PowerShell)
3. Installs & updates all dependencies (`requirements.txt` + `pywin32`)
4. Configures Windows Defender Firewall (Inbound TCP `8989`) via native `netsh`
5. Registers **MetricsByJJ** as an automatic Windows Service
6. Creates Start Menu and Desktop shortcuts with custom app icons
7. Launches the dashboard in your default browser

---

## 🛠️ CLI & Manual Control

You can also run commands directly or use the interactive manager menu:

```cmd
:: Open interactive setup & control menu
Setup.bat

:: Full automated install
python setup.py --install

:: Check live service status & LAN access URLs
python setup.py --status

:: Start or Stop the background service
python setup.py --start
python setup.py --stop

:: Run in foreground console mode
python setup.py --run

:: Clean uninstall (removes service, firewall rule, and shortcuts)
python setup.py --uninstall
```

### 🌐 Accessing the Dashboard
- **On this PC:** [`http://localhost:8989`](http://localhost:8989)
- **On any device on your Wi-Fi/LAN (Phone, Tablet, Laptop):**  
  Open browser and go to `http://<YOUR_PC_IP>:8989` (e.g. `http://192.168.8.164:8989`). Run `python setup.py --status` to see all active LAN IP addresses.

---

## 🌡️ Unlocking Full CPU & GPU Temperature Sensors

On Windows, deep hardware temperature sensors require kernel-level hardware sensor access.

To unlock per-core temperatures, GPU thermal sensors, and fan speeds:
1. Download [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases) *(Free & Open Source, portable .zip)*.
2. Run `LibreHardwareMonitor.exe`.
3. In Options, make sure **WMI** is enabled (enabled by default).
4. `Metrics by JJ` will automatically hook into the WMI telemetry stream and display full thermal gauges!

---

## 📐 Architecture

```
metrics-by-jj/
├── backend/
│   ├── main.py          # FastAPI app + WebSocket connection hub & broadcaster
│   ├── metrics.py       # psutil + WMI metrics collector & rate calculator
│   ├── hardware.py      # LibreHardwareMonitor / OpenHardwareMonitor / ACPI bridge
│   └── requirements.txt # Python dependencies
├── frontend/
│   └── index.html       # Single-file zero-dependency dark cockpit dashboard
├── installer/
│   ├── metrics-jj.ico   # Application icon for Windows shortcuts
│   └── metrics-jj.png   # High-res application logo
├── Setup.bat            # 1-Click Master Setup & Manager Launcher
├── setup.py             # Pure Python setup engine (zero PowerShell)
├── service.py           # Windows Service wrapper
├── start.bat            # Quick foreground launcher
└── README.md
```

### 📜 Service Logs
Background service output is written to `service.log` in the project root.
