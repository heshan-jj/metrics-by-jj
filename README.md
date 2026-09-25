<div align="center">

# ⚡ Metrics by JJ

**Lightweight, Real-Time & 100% Private Windows Telemetry Dashboard**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![WebSockets](https://img.shields.io/badge/WebSockets-Realtime-00f2fe?style=for-the-badge)](https://websockets.readthedocs.io/)
[![Privacy: 100% Local](https://img.shields.io/badge/Privacy-100%25%20Local-success?style=for-the-badge)](README.md)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](README.md)

<p align="center">
  A free, open-source system monitor that streams your PC's hardware metrics to any browser, phone, tablet, or secondary screen over your local network in real-time.
  <br />
  <strong>Zero Cloud • Zero Tracking • Zero Bloat • Sub-1% CPU Overhead</strong>
</p>

---

</div>

## ✨ Highlights

- 🔒 **100% Local & Private**: No cloud connections, no telemetry collection, no accounts. All data stays entirely inside your private local network (LAN).
- ⚡ **Real-Time WebSocket Stream**: Live telemetry pushed at 1-second intervals with zero polling overhead.
- 📱 **Responsive Cockpit UI**: Zero-dependency frontend engineered for desktop monitors, mobile phones, tablets, and dedicated status displays.
- 🪟 **Native Windows Service**: Runs silently in the background and auto-starts on system boot without open terminal windows.
- 🚀 **1-Click Setup (Zero PowerShell)**: Seamless installer that handles elevation, dependencies, firewall rules, and desktop shortcuts automatically.
- 🪶 **Ultra Lightweight**: Minimal footprint consuming less than ~50 MB RAM and negligible CPU cycles.

---

## 📊 Monitored Metrics

| Category | Telemetry & Details |
| :--- | :--- |
| **🖥️ CPU** | Overall load percentage, per-core utilization bars, clock frequency (GHz), physical & logical core count |
| **🎮 GPU** | Model identification, thermal sensors, clock speed, power consumption & load |
| **🧠 Memory** | Physical RAM (Used / Available / Total GB), swap & Windows pagefile utilization |
| **💾 Storage** | Per-drive partition capacity, disk free space, live real-time Read/Write I/O throughput |
| **📡 Network** | Rolling 60-second upload/download throughput sparkline, live bandwidth rates (KB/s, MB/s) |
| **🛠️ Services** | Filterable Windows services manager with status indicators, PIDs, and startup types |
| **📈 Processes** | Live Top 10 CPU & Memory consuming processes with PID, thread counts, and memory footprint |
| **🌐 Network Endpoints** | Auto-detected host IPv4 addresses with one-click copyable LAN access URLs |

---

## 🚀 Quick Start

### Option A: One-Click Setup (Recommended for Windows)

1. Clone or download this repository:
   ```cmd
   git clone https://github.com/heshan-jj/metrics-by-jj.git
   cd metrics-by-jj
   ```
2. Double-click **[`Setup.bat`](Setup.bat)**.

> **What the installer does automatically:**
> - Verifies Python 3.10+ in your system PATH
> - Automatically requests Administrator privileges via native Windows UAC (no PowerShell execution policy blocks)
> - Installs required dependencies (`requirements.txt` + `pywin32`)
> - Configures an inbound Windows Defender Firewall rule for TCP port `9090` via native `netsh`
> - Registers and starts the **MetricsByJJ** Windows background service (auto-starts on boot)
> - Creates Start Menu and Desktop shortcuts with custom application icons
> - Opens the live dashboard in your default web browser

---

### Option B: Portable / Developer Mode (Foreground)

If you prefer to run the server in the foreground without registering a Windows service:

```cmd
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Start the telemetry server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 9090
```

Or simply double-click **[`start.bat`](start.bat)**.

---

## 🌐 Accessing Your Dashboard

Once started, open your dashboard from any device connected to the same Wi-Fi or LAN:

- **Local Machine:** [`http://localhost:9090`](http://localhost:9090)
- **Phone / Tablet / Laptop:** `http://<YOUR_PC_IP>:9090` (e.g. `http://192.168.8.164:9090`)

> 💡 *Tip: Run `python setup.py --status` to list all detected IPv4 addresses for your machine.*

---

## 🛠️ CLI & Management Commands

The built-in manager ([`setup.py`](setup.py)) provides full lifecycle management:

```cmd
:: Open interactive setup & control menu
Setup.bat

:: Silent automated full installation
python setup.py --install

:: Check service health, port listener, and active LAN URLs
python setup.py --status

:: Start or Stop the background Windows service
python setup.py --start
python setup.py --stop

:: Run telemetry server in foreground console mode
python setup.py --run

:: Clean uninstallation (removes service, firewall rule, and shortcuts)
python setup.py --uninstall
```

---

## 🌡️ Unlocking Deep Kernel Thermal Sensors (Optional)

On Windows, kernel-level sensors (such as per-core CPU temperatures and GPU junction thermals) require a signed ring-0 driver.

`Metrics by JJ` natively integrates with **[LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)** via WMI:

1. Download the free, portable release of [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases).
2. Extract and run `LibreHardwareMonitor.exe`.
3. Ensure **Options → WMI** is enabled (enabled by default).
4. `Metrics by JJ` will instantly hook into the WMI telemetry feed and render full hardware temperature gauges!

---

## 📐 Project Architecture

```
metrics-by-jj/
├── backend/
│   ├── main.py          # FastAPI application & WebSocket broadcaster
│   ├── metrics.py       # psutil, WMI, and network rate aggregator
│   ├── hardware.py      # Hardware sensor bridge (LibreHardwareMonitor / ACPI)
│   └── requirements.txt # Core backend Python dependencies
├── frontend/
│   └── index.html       # Zero-dependency, responsive dark cockpit dashboard
├── installer/
│   ├── metrics-jj.ico   # Windows shortcut icon
│   └── metrics-jj.png   # Dashboard logo asset
├── Setup.bat            # 1-Click Master Setup & Manager Launcher
├── setup.py             # Pure Python setup engine (zero PowerShell)
├── service.py           # Windows NT Service wrapper
├── start.bat            # Quick foreground runner
├── LICENSE              # MIT Open Source License
└── README.md
```

---

## 🤝 Contributing

Contributions from the open-source community are warmly welcomed!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m "feat: Add AmazingFeature"`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<div align="center">
  <sub>Built with ❤️ for privacy, efficiency, and hardware enthusiasts.</sub>
</div>
