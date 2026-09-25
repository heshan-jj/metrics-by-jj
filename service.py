"""
Metrics by JJ - Windows Service Wrapper
Runs the FastAPI/uvicorn backend as a Windows NT Service.

Usage (Administrator PowerShell):
  python service.py install
  python service.py start
  python service.py stop
  python service.py remove
  python service.py debug
"""

import sys
import time
import subprocess
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
except ImportError:
    print("ERROR: pywin32 not installed.")
    print("Run:  pip install pywin32")
    print("Then: python -m pywin32_postinstall -install")
    sys.exit(1)

SERVICE_NAME    = "MetricsByJJ"
SERVICE_DISPLAY = "Metrics by JJ"
SERVICE_DESC    = "Real-time hardware and system telemetry server."
PORT            = 9090
LOG_FILE        = BASE_DIR / "service.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("MetricsByJJ.Service")


def get_python_exe() -> str:
    exe = Path(sys.executable)
    if "pythonservice" in exe.name.lower():
        cand = Path(sys.prefix) / "python.exe"
        if cand.exists():
            return str(cand)
        cand = exe.parent.parent / "python.exe"
        if cand.exists():
            return str(cand)
    return sys.executable


class MetricsByJJService(win32serviceutil.ServiceFramework):
    _svc_name_         = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY
    _svc_description_  = SERVICE_DESC

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process    = None

    def SvcStop(self):
        log.info("Stop requested.")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                self.process.kill()
        log.info("Stopped.")

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        log.info("Service starting...")
        self._run()

    def _run(self):
        python_bin = get_python_exe()
        cmd = [
            python_bin, "-m", "uvicorn",
            "backend.main:app",
            "--host", "0.0.0.0",
            "--port", str(PORT),
            "--no-access-log",
        ]
        log.info("CMD: " + " ".join(str(c) for c in cmd))
        log.info("CWD: " + str(BASE_DIR))

        def spawn():
            return subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                stdout=open(str(LOG_FILE), "a"),
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

        try:
            self.process = spawn()
            log.info("Server PID: " + str(self.process.pid))

            while True:
                rc = win32event.WaitForSingleObject(self.stop_event, 2000)
                if rc == win32event.WAIT_OBJECT_0:
                    break
                if self.process.poll() is not None:
                    log.warning("Server exited unexpectedly, restarting in 5s...")
                    time.sleep(5)
                    self.process = spawn()
                    log.info("Restarted PID: " + str(self.process.pid))
        except Exception as exc:
            log.exception("Service run error: " + str(exc))
            servicemanager.LogErrorMsg("Metrics by JJ error: " + str(exc))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MetricsByJJService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MetricsByJJService)
