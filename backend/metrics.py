"""
Comprehensive System Metrics Collector for Windows.
Aggregates CPU, GPU, RAM, Disks, Network rates, Windows Services, Processes, and Hardware Sensors.
"""

import time
import socket
import platform
import psutil
from typing import Dict, Any, List
from .hardware import bridge

class MetricsCollector:
    def __init__(self):
        self.last_time = time.time()
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        
        # Cache static system info
        self.static_info = self._get_static_info()

    def _get_static_info(self) -> Dict[str, Any]:
        """Fetch static host & hardware details."""
        hostname = socket.gethostname()
        local_ips = []
        try:
            # Get all non-loopback IP addresses
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                        local_ips.append({"interface": iface, "ip": addr.address})
        except Exception:
            pass

        primary_ip = "127.0.0.1"
        try:
            # Find primary outbound IP by connecting a dummy UDP socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            s.close()
        except Exception:
            if local_ips:
                primary_ip = local_ips[0]["ip"]

        cpu_freq = psutil.cpu_freq()
        return {
            "hostname": hostname,
            "primary_ip": primary_ip,
            "all_ips": local_ips,
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "arch": platform.machine(),
            "cpu_brand": platform.processor(),
            "cpu_cores_physical": psutil.cpu_count(logical=False) or psutil.cpu_count(),
            "cpu_cores_logical": psutil.cpu_count(logical=True) or 1,
            "max_freq_mhz": round(cpu_freq.max, 0) if cpu_freq and cpu_freq.max else None,
            "boot_time": psutil.boot_time()
        }

    def _get_rates(self) -> Dict[str, Any]:
        """Calculate network and disk read/write transfer rates per second."""
        now = time.time()
        dt = max(now - self.last_time, 0.001)

        # Network rates
        curr_net = psutil.net_io_counters()
        net_sent_rate = max(0, (curr_net.bytes_sent - self.last_net_io.bytes_sent) / dt)
        net_recv_rate = max(0, (curr_net.bytes_recv - self.last_net_io.bytes_recv) / dt)
        self.last_net_io = curr_net

        # Disk rates
        curr_disk = psutil.disk_io_counters()
        disk_read_rate = 0
        disk_write_rate = 0
        if curr_disk and self.last_disk_io:
            disk_read_rate = max(0, (curr_disk.read_bytes - self.last_disk_io.read_bytes) / dt)
            disk_write_rate = max(0, (curr_disk.write_bytes - self.last_disk_io.write_bytes) / dt)
            self.last_disk_io = curr_disk

        self.last_time = now

        return {
            "net_upload_bps": round(net_sent_rate, 1),
            "net_download_bps": round(net_recv_rate, 1),
            "net_total_sent_bytes": curr_net.bytes_sent,
            "net_total_recv_bytes": curr_net.bytes_recv,
            "disk_read_bps": round(disk_read_rate, 1),
            "disk_write_bps": round(disk_write_rate, 1),
        }

    def _get_cpu_metrics(self, hw_sensors: Dict[str, Any]) -> Dict[str, Any]:
        """Collect CPU usage, core loads, frequencies, and temperatures."""
        # Non-blocking per-cpu load
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        total_percent = round(sum(per_core) / max(len(per_core), 1), 1)
        
        freq = psutil.cpu_freq()
        current_freq = round(freq.current, 0) if freq else None

        return {
            "usage_percent": total_percent,
            "cores_percent": per_core,
            "current_freq_mhz": current_freq,
            "temp_c": hw_sensors.get("cpu_temp"),
            "package_temp_c": hw_sensors.get("cpu_package_temp"),
            "core_temps": hw_sensors.get("cpu_core_temps", []),
            "max_temp_c": hw_sensors.get("cpu_max_temp")
        }

    def _get_gpu_metrics(self, hw_sensors: Dict[str, Any]) -> Dict[str, Any]:
        """Collect GPU load, VRAM, and temp."""
        # Check if sensor returned GPU data
        gpu_temp = hw_sensors.get("gpu_temp")
        gpu_name = hw_sensors.get("gpu_name")
        gpu_clock = hw_sensors.get("gpu_core_clock")
        gpu_power = hw_sensors.get("gpu_power")
        
        # If GPU name is not yet known, probe WMI
        if not gpu_name:
            try:
                import wmi
                w = wmi.WMI()
                for gpu in w.Win32_VideoController():
                    if gpu.Name:
                        gpu_name = gpu.Name
                        break
            except Exception:
                pass

        return {
            "available": bool(gpu_name or gpu_temp is not None),
            "name": gpu_name or "Standard Graphics",
            "temp_c": gpu_temp,
            "core_clock_mhz": gpu_clock,
            "power_w": gpu_power,
            "usage_percent": None, # Provided when LHM/NVIDIA is active
        }

    def _get_ram_metrics(self) -> Dict[str, Any]:
        """Collect physical and swap memory metrics."""
        v = psutil.virtual_memory()
        s = psutil.swap_memory()
        return {
            "total_bytes": v.total,
            "used_bytes": v.used,
            "available_bytes": v.available,
            "percent": v.percent,
            "swap_total_bytes": s.total,
            "swap_used_bytes": s.used,
            "swap_percent": s.percent
        }

    def _get_disk_metrics(self, rates: Dict[str, Any]) -> Dict[str, Any]:
        """Collect all logical disk drives and capacities."""
        drives = []
        for part in psutil.disk_partitions(all=False):
            try:
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
                usage = psutil.disk_usage(part.mountpoint)
                drives.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "percent": usage.percent
                })
            except (PermissionError, OSError):
                continue

        return {
            "drives": drives,
            "read_bps": rates["disk_read_bps"],
            "write_bps": rates["disk_write_bps"]
        }

    def _get_network_metrics(self, rates: Dict[str, Any]) -> Dict[str, Any]:
        """Collect network interface and bandwidth usage."""
        interfaces = []
        try:
            stats = psutil.net_if_stats()
            for name, is_up in stats.items():
                if is_up.isup:
                    interfaces.append({
                        "name": name,
                        "speed_mbps": is_up.speed,
                        "mtu": is_up.mtu
                    })
        except Exception:
            pass

        return {
            "upload_bps": rates["net_upload_bps"],
            "download_bps": rates["net_download_bps"],
            "total_sent_bytes": rates["net_total_sent_bytes"],
            "total_recv_bytes": rates["net_total_recv_bytes"],
            "interfaces": interfaces
        }

    def _get_processes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch top running processes sorted by CPU and memory."""
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'num_threads']):
            try:
                info = p.info
                # psutil memory_info might be None
                rss = info['memory_info'].rss if info.get('memory_info') else 0
                procs.append({
                    "pid": info['pid'],
                    "name": info['name'] or f"PID {info['pid']}",
                    "cpu_percent": round(info['cpu_percent'] or 0.0, 1),
                    "memory_percent": round(info['memory_percent'] or 0.0, 1),
                    "memory_rss_bytes": rss,
                    "threads": info.get('num_threads') or 1,
                    "status": info.get('status') or 'running'
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort primarily by CPU, fallback by Memory
        procs.sort(key=lambda x: (x['cpu_percent'], x['memory_percent']), reverse=True)
        return procs[:limit]

    def _get_services(self, limit: int = 30) -> Dict[str, Any]:
        """Fetch Windows services and running counts."""
        services = []
        running_count = 0
        stopped_count = 0

        if hasattr(psutil, 'win_service_iter'):
            try:
                for s in psutil.win_service_iter():
                    try:
                        sinfo = s.as_dict()
                        status = sinfo.get('status', 'unknown')
                        if status == 'running':
                            running_count += 1
                        elif status == 'stopped':
                            stopped_count += 1

                        services.append({
                            "name": sinfo.get('name', ''),
                            "display_name": sinfo.get('display_name', ''),
                            "status": status,
                            "start_type": sinfo.get('start_type', ''),
                            "pid": sinfo.get('pid', None)
                        })
                    except Exception:
                        continue
            except Exception:
                pass

        # Sort running first, then alphabetized
        services.sort(key=lambda x: (0 if x['status'] == 'running' else 1, x['name'].lower()))

        return {
            "running_count": running_count,
            "stopped_count": stopped_count,
            "total_count": running_count + stopped_count,
            "services": services[:limit]
        }

    def collect(self) -> Dict[str, Any]:
        """Collect full unified metrics payload."""
        hw = bridge.get_hardware_sensors()
        rates = self._get_rates()
        uptime_seconds = int(time.time() - self.static_info["boot_time"])

        return {
            "timestamp": time.time(),
            "uptime_seconds": uptime_seconds,
            "system": self.static_info,
            "hardware_bridge": {
                "lhm_active": hw.get("lhm_active", False),
                "fans": hw.get("fans", []),
                "disk_temps": hw.get("disk_temps", []),
                "sensors_raw": hw.get("sensors_raw", [])
            },
            "cpu": self._get_cpu_metrics(hw),
            "gpu": self._get_gpu_metrics(hw),
            "ram": self._get_ram_metrics(),
            "disk": self._get_disk_metrics(rates),
            "network": self._get_network_metrics(rates),
            "processes": self._get_processes(limit=10),
            "services": self._get_services(limit=30)
        }


# Global metrics collector instance
collector = MetricsCollector()
