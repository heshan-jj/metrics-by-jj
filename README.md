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

## 📦 Quick Start

### 1. Launch with One Click
Double-click [`start.bat`](file:///d:/Projects/metrics%20by%20jj/start.bat)

*Or run from terminal:*
```powershell
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8989
```

### 2. Access the Dashboard
- **On this PC:** [`http://localhost:8989`](http://localhost:8989)
- **On any other device on your Wi-Fi/LAN (Phone, Tablet, Laptop):**  
  Open browser and go to `http://<YOUR_PC_IP>:8989` (e.g. `http://192.168.8.164:8989`).

---

## 🌡️ Unlocking Full CPU & GPU Temperature Sensors

On Windows, deep hardware temperature sensors require kernel-level hardware sensor access.

To unlock per-core temperatures, GPU thermal sensors, and fan speeds:
1. Download [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases) *(Free & Open Source, portable .zip)*.
2. Run `LibreHardwareMonitor.exe`.
3. In Options, make sure **WMI** is enabled (enabled by default).
4. `Metrics by JJ` will automatically hook into the WMI telemetry stream and display full thermal gauges!

---

## 🛡️ Windows Firewall Note

If other devices on your LAN cannot connect to `http://<YOUR_IP>:8989`:
1. Open Windows Defender Firewall -> **Allow an app or feature through Windows Defender Firewall**.
2. Ensure Python or Port `8989` (Inbound Rule) is allowed on **Private Networks**.

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
├── start.bat            # One-click Windows startup script
└── README.md
```


---

## 🚀 Install as Windows Service

The `installer/` folder contains everything needed to run Metrics by JJ as a **persistent Windows background service** that starts automatically at boot.

### Requirements
- Python 3.10+ in your `PATH`
- Administrator privileges

### Install
Double-click **`installer/Install Metrics by JJ.bat`**

This will:
1. Install all Python dependencies (`requirements.txt` + `pywin32`)
2. Register the **MetricsByJJ** Windows service
3. Start the service (auto-starts on boot)
4. Open firewall port 8989 for LAN access
5. Add a Start Menu shortcut → `http://localhost:8989`

### Uninstall
Double-click **`installer/Uninstall Metrics by JJ.bat`**

### Manual service control (Admin PowerShell)
```powershell
Start-Service MetricsByJJ
Stop-Service MetricsByJJ
Restart-Service MetricsByJJ
Get-Service MetricsByJJ   # check status
```

### Logs
Service output is written to `service.log` in the project root.
