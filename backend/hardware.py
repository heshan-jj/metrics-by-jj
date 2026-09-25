"""
Hardware monitor bridge for Windows.
Reads sensor data (temps, clock speeds, fan speeds, power, voltages) from:
1. LibreHardwareMonitor WMI (root/LibreHardwareMonitor)
2. OpenHardwareMonitor WMI (root/OpenHardwareMonitor)
3. Windows ACPI Thermal Zones (root/wmi)
4. nvidia-smi / generic fallback
"""

import subprocess
import shutil
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("hardware")

class HardwareBridge:
    def __init__(self):
        self._lhm_available = None
        self._ohm_available = None
        self._has_nvidia_smi = shutil.which("nvidia-smi") is not None

    def _init_com(self):
        """Ensure COM is initialized for the current thread."""
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass

    def get_hardware_sensors(self) -> Dict[str, Any]:
        """
        Query LibreHardwareMonitor or OpenHardwareMonitor WMI namespace for temperatures,
        power, fans, etc.
        """
        self._init_com()
        
        result = {
            "lhm_active": False,
            "cpu_temp": None,
            "cpu_package_temp": None,
            "cpu_core_temps": [],
            "cpu_max_temp": None,
            "gpu_temp": None,
            "gpu_name": None,
            "gpu_core_clock": None,
            "gpu_memory_clock": None,
            "gpu_power": None,
            "disk_temps": [],
            "fans": [],
            "sensors_raw": []
        }

        # Try LibreHardwareMonitor first
        try:
            import wmi
            lhm_wmi = wmi.WMI(namespace="root/LibreHardwareMonitor")
            sensors = lhm_wmi.Sensor()
            if sensors:
                result["lhm_active"] = True
                self._parse_sensors(sensors, result)
                return result
        except Exception:
            pass

        # Try OpenHardwareMonitor second
        try:
            import wmi
            ohm_wmi = wmi.WMI(namespace="root/OpenHardwareMonitor")
            sensors = ohm_wmi.Sensor()
            if sensors:
                result["lhm_active"] = True
                self._parse_sensors(sensors, result)
                return result
        except Exception:
            pass

        # Fallback 1: Windows ACPI Thermal Zone
        try:
            import wmi
            acpi_wmi = wmi.WMI(namespace="root/wmi")
            thermal_zones = acpi_wmi.MSAcpi_ThermalZoneTemperature()
            temps = []
            for tz in thermal_zones:
                # Value is in tenths of Kelvin
                celsius = (float(tz.CurrentTemperature) - 2732.0) / 10.0
                if 0 <= celsius <= 120:
                    temps.append(round(celsius, 1))
            if temps:
                result["cpu_temp"] = max(temps)
                result["cpu_package_temp"] = max(temps)
                result["cpu_core_temps"] = temps
        except Exception:
            pass

        # Fallback 2: nvidia-smi for GPU temp if NVIDIA GPU is present
        if result["gpu_temp"] is None and self._has_nvidia_smi:
            try:
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw",
                     "--format=csv,noheader,nounits"],
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                    text=True,
                    timeout=2
                ).strip()
                if out:
                    parts = [p.strip() for p in out.split(',')]
                    if len(parts) >= 2:
                        result["gpu_name"] = parts[0]
                        result["gpu_temp"] = float(parts[1])
                    if len(parts) >= 6:
                        result["gpu_power"] = float(parts[5])
            except Exception:
                pass

        return result

    def _parse_sensors(self, sensors, result: Dict[str, Any]):
        """Parse raw LHM/OHM sensors into structured output."""
        core_temps = []
        package_temps = []
        all_cpu_temps = []

        for s in sensors:
            try:
                name = getattr(s, "Name", "")
                stype = getattr(s, "SensorType", "")
                val = getattr(s, "Value", None)
                ident = getattr(s, "Identifier", "")
                
                if val is None:
                    continue
                val = float(val)

                # Collect temperatures
                if stype == "Temperature":
                    ident_lower = ident.lower()
                    name_lower = name.lower()

                    # CPU sensors
                    if "/cpu/" in ident_lower or "cpu" in name_lower:
                        if "package" in name_lower:
                            package_temps.append(round(val, 1))
                        elif "core" in name_lower or "ccd" in name_lower or "tdie" in name_lower:
                            core_temps.append({"name": name, "temp": round(val, 1)})
                            all_cpu_temps.append(val)
                        else:
                            all_cpu_temps.append(val)

                    # GPU sensors
                    elif "/gpu/" in ident_lower or "gpu" in name_lower:
                        if "core" in name_lower or "gpu" in name_lower:
                            if result["gpu_temp"] is None or "core" in name_lower:
                                result["gpu_temp"] = round(val, 1)

                    # Disk / Storage sensors (HDD, SSD, NVMe)
                    elif (
                        "/hdd/" in ident_lower
                        or "/ssd/" in ident_lower
                        or "/nvme/" in ident_lower
                        or "nvme" in name_lower
                        or ("temperature" in name_lower and any(kw in name_lower for kw in ["hdd", "ssd", "disk", "storage", "drive", "ata", "nvme"]))
                    ):
                        result["disk_temps"].append({
                            "name": name,
                            "temp": round(val, 1),
                            "id": ident
                        })

                    # Motherboard / System — always append to sensors_raw
                    result["sensors_raw"].append({
                        "name": name,
                        "type": stype,
                        "value": round(val, 1),
                        "unit": "°C",
                        "id": ident
                    })

                elif stype == "Fan":
                    result["fans"].append({
                        "name": name,
                        "rpm": int(val),
                        "id": ident
                    })

                elif stype == "Clock":
                    if "/gpu/" in ident.lower() and "core" in name.lower():
                        result["gpu_core_clock"] = round(val, 0)
                    elif "/gpu/" in ident.lower() and "memory" in name.lower():
                        result["gpu_memory_clock"] = round(val, 0)

                elif stype == "Power":
                    if "/gpu/" in ident.lower() and ("package" in name.lower() or "core" in name.lower() or "power" in name.lower()):
                        result["gpu_power"] = round(val, 1)

            except Exception:
                continue

        if package_temps:
            result["cpu_package_temp"] = package_temps[0]
            result["cpu_temp"] = package_temps[0]
        elif all_cpu_temps:
            result["cpu_temp"] = round(sum(all_cpu_temps) / len(all_cpu_temps), 1)

        if core_temps:
            result["cpu_core_temps"] = [c["temp"] for c in core_temps]
            result["cpu_max_temp"] = max(c["temp"] for c in core_temps)
        elif all_cpu_temps:
            result["cpu_max_temp"] = round(max(all_cpu_temps), 1)


# Global singleton instance
bridge = HardwareBridge()
