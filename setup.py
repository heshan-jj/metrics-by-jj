"""
Metrics by JJ - Master Setup & Service Manager
Zero PowerShell dependency. Pure Python + Windows Native APIs (netsh, WScript.Shell, Win32 Service).

Features:
- Automatic UAC elevation prompt (Windows Native, no PowerShell)
- Dependency checker & installer (FastAPI, uvicorn, psutil, pywin32, etc.)
- Inbound Windows Defender Firewall rule configuration (netsh)
- Windows Service registration, auto-start configuration, and daemon control
- Start Menu and Desktop shortcuts with custom icon
- Real-time LAN IP discovery & Web Dashboard launcher
- Clean uninstallation with full cleanup
"""

import sys
import os
import ctypes
import subprocess
import time
import socket
import urllib.request
from pathlib import Path

# Configure standard streams for UTF-8 in Windows console
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Paths
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
REQ_FILE = BACKEND_DIR / "requirements.txt"
INSTALLER_DIR = ROOT_DIR / "installer"
ICON_FILE = INSTALLER_DIR / "metrics-jj.ico"
LOG_FILE = ROOT_DIR / "service.log"
SERVICE_NAME = "MetricsByJJ"
SERVICE_DISPLAY = "Metrics by JJ"
PORT = 8989

# Color formatting for terminal
class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

# Enable VT100 ANSI escape codes on Windows console
def enable_ansi():
    if os.name == "nt":
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(handle, mode)

enable_ansi()


def is_admin() -> bool:
    """Check if current process has Administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin(args: list[str] = None):
    """Re-launch the current script with Administrator privileges using native UAC prompt."""
    if args is None:
        args = sys.argv[1:]
    params = f'"{ROOT_DIR / "setup.py"}" ' + " ".join(f'"{arg}"' for arg in args)
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params.strip(), str(ROOT_DIR), 1
    )
    # ShellExecute returns > 32 on success
    if ret <= 32:
        print(f"{Colors.RED}[!] Administrator privileges are required.{Colors.RESET}")
    sys.exit(0)


def print_banner():
    print(f"\n{Colors.CYAN}{Colors.BOLD}  ⚡ METRICS BY JJ — SETUP & MANAGER{Colors.RESET}")
    print(f"{Colors.DIM}  ────────────────────────────────────────────────────────{Colors.RESET}")


def get_local_ips() -> list[str]:
    """Discover host LAN IPv4 addresses."""
    ips = []
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                ips.append(ip)
    except Exception:
        pass
    return ips


def install_dependencies() -> bool:
    """Install requirements.txt and pywin32, plus run post-install."""
    print(f"\n{Colors.YELLOW}[1/5] Checking and installing Python dependencies...{Colors.RESET}")
    if not REQ_FILE.exists():
        print(f"{Colors.RED}  [!] Error: requirements.txt not found at {REQ_FILE}{Colors.RESET}")
        return False

    cmd = [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", "-r", str(REQ_FILE)]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"{Colors.RED}  [!] pip install failed with code {res.returncode}{Colors.RESET}")
        return False

    # Install pywin32
    cmd_pywin = [sys.executable, "-m", "pip", "install", "--quiet", "pywin32"]
    subprocess.run(cmd_pywin)

    # Register pywin32 COM services
    cmd_post = [sys.executable, "-m", "pywin32_postinstall", "-install"]
    subprocess.run(cmd_post, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"{Colors.GREEN}  [✓] All dependencies installed successfully.{Colors.RESET}")
    return True


def configure_firewall() -> bool:
    """Add Windows Defender Firewall rule using native netsh command."""
    print(f"\n{Colors.YELLOW}[2/5] Configuring Windows Defender Firewall...{Colors.RESET}")
    # Remove existing rule first to prevent duplicates
    subprocess.run(
        ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={SERVICE_DISPLAY}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cmd = [
        "netsh", "advfirewall", "firewall", "add", "rule",
        f"name={SERVICE_DISPLAY}",
        "dir=in",
        "action=allow",
        "protocol=TCP",
        f"localport={PORT}",
        "profile=any",
        "description=Allows LAN access to Metrics by JJ telemetry dashboard.",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"{Colors.GREEN}  [✓] Inbound Firewall rule added for TCP port {PORT}.{Colors.RESET}")
        return True
    else:
        print(f"{Colors.YELLOW}  [!] Firewall warning: {res.stderr.strip() or res.stdout.strip()}{Colors.RESET}")
        return False


def get_special_folder(folder_name: str) -> Path:
    """Resolve standard Windows special folders."""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        return Path(shell.SpecialFolders(folder_name))
    except Exception:
        pass

    user_profile = Path(os.environ.get("USERPROFILE", "C:\\Users\\Public"))
    app_data = Path(os.environ.get("APPDATA", user_profile / "AppData" / "Roaming"))

    if folder_name.lower() == "desktop":
        cand = user_profile / "Desktop"
        return cand if cand.exists() else user_profile
    elif folder_name.lower() in ("programs", "startmenu"):
        cand = app_data / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        return cand if cand.exists() else app_data

    return user_profile


def create_shortcut_file(target: str, lnk_path: Path, icon_path: str = "", description: str = ""):
    """Create a Windows .lnk shortcut using COM or VBScript."""
    lnk_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(str(lnk_path))
        shortcut.TargetPath = target
        shortcut.Description = description
        if icon_path and Path(icon_path).exists():
            shortcut.IconLocation = icon_path
        shortcut.Save()
        return True
    except Exception:
        # Fallback to pure VBScript
        vbs_lines = [
            'Set WshShell = CreateObject("WScript.Shell")',
            f'Set Shortcut = WshShell.CreateShortcut("{lnk_path}")',
            f'Shortcut.TargetPath = "{target}"',
            f'Shortcut.Description = "{description}"',
        ]
        if icon_path and Path(icon_path).exists():
            vbs_lines.append(f'Shortcut.IconLocation = "{icon_path}"')
        vbs_lines.append('Shortcut.Save')

        temp_vbs = ROOT_DIR / "_temp_shortcut.vbs"
        try:
            temp_vbs.write_text("\r\n".join(vbs_lines), encoding="utf-8")
            subprocess.run(
                ["cscript.exe", "//nologo", str(temp_vbs)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            return True
        except Exception:
            return False
        finally:
            if temp_vbs.exists():
                try:
                    temp_vbs.unlink()
                except Exception:
                    pass


def create_shortcuts() -> bool:
    """Create Start Menu and Desktop shortcuts."""
    print(f"\n{Colors.YELLOW}[3/5] Creating Start Menu & Desktop shortcuts...{Colors.RESET}")
    url = f"http://localhost:{PORT}"
    icon_path = str(ICON_FILE) if ICON_FILE.exists() else ""
    desc = "Open Metrics by JJ telemetry dashboard"

    start_menu_dir = get_special_folder("Programs")
    desktop_dir = get_special_folder("Desktop")

    s1 = create_shortcut_file(url, start_menu_dir / f"{SERVICE_DISPLAY}.lnk", icon_path, desc)
    s2 = create_shortcut_file(url, desktop_dir / f"{SERVICE_DISPLAY}.lnk", icon_path, desc)

    if s1 or s2:
        print(f"{Colors.GREEN}  [✓] Shortcuts created in Start Menu and Desktop.{Colors.RESET}")
        return True
    else:
        print(f"{Colors.YELLOW}  [!] Could not create desktop shortcuts automatically.{Colors.RESET}")
        return False


def stop_and_remove_service():
    """Stop and remove existing service if present."""
    service_py = ROOT_DIR / "service.py"
    if service_py.exists():
        subprocess.run(["sc.exe", "stop", SERVICE_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        subprocess.run([sys.executable, str(service_py), "remove"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)


def install_and_start_service() -> bool:
    """Register and start the Windows Service."""
    print(f"\n{Colors.YELLOW}[4/5] Registering and configuring Windows Service ({SERVICE_NAME})...{Colors.RESET}")
    stop_and_remove_service()

    service_py = ROOT_DIR / "service.py"
    if not service_py.exists():
        print(f"{Colors.RED}  [!] Error: service.py not found at {service_py}{Colors.RESET}")
        return False

    res = subprocess.run([sys.executable, str(service_py), "install"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"{Colors.RED}  [!] Service install failed: {res.stderr or res.stdout}{Colors.RESET}")
        return False

    # Set service to Automatic start
    subprocess.run(["sc.exe", "config", SERVICE_NAME, "start=", "auto"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"\n{Colors.YELLOW}[5/5] Starting service...{Colors.RESET}")
    start_res = subprocess.run(["sc.exe", "start", SERVICE_NAME], capture_output=True, text=True)
    time.sleep(2)

    # Check status
    status_res = subprocess.run(["sc.exe", "query", SERVICE_NAME], capture_output=True, text=True)
    if "RUNNING" in status_res.stdout:
        print(f"{Colors.GREEN}  [✓] Service is RUNNING on port {PORT}!{Colors.RESET}")
        return True
    else:
        print(f"{Colors.YELLOW}  [!] Service registered. Status output:{Colors.RESET}\n{status_res.stdout}")
        return True


def uninstall() -> bool:
    """Clean uninstallation of service, firewall rules, and shortcuts."""
    if not is_admin():
        run_as_admin(["--uninstall"])
        return True

    print_banner()
    print(f"\n{Colors.YELLOW}Uninstalling Metrics by JJ...{Colors.RESET}\n")

    # 1. Stop and remove service
    print(f"  [→] Stopping and removing Windows Service ({SERVICE_NAME})...")
    stop_and_remove_service()
    print(f"{Colors.GREEN}  [✓] Service removed.{Colors.RESET}")

    # 2. Remove firewall rule
    print(f"  [→] Removing firewall rule...")
    subprocess.run(
        ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={SERVICE_DISPLAY}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"{Colors.GREEN}  [✓] Firewall rule removed.{Colors.RESET}")

    # 3. Remove shortcuts
    print(f"  [→] Removing shortcuts...")
    try:
        start_lnk = get_special_folder("Programs") / f"{SERVICE_DISPLAY}.lnk"
        desk_lnk = get_special_folder("Desktop") / f"{SERVICE_DISPLAY}.lnk"
        if start_lnk.exists():
            start_lnk.unlink()
        if desk_lnk.exists():
            desk_lnk.unlink()
        print(f"{Colors.GREEN}  [✓] Shortcuts removed.{Colors.RESET}")
    except Exception as exc:
        print(f"{Colors.YELLOW}  [!] Shortcut cleanup notice: {exc}{Colors.RESET}")

    print(f"\n{Colors.CYAN}{Colors.BOLD}  ✓ Metrics by JJ has been cleanly uninstalled.{Colors.RESET}")
    print(f"{Colors.DIM}  (Project files at {ROOT_DIR} were kept intact){Colors.RESET}\n")
    return True


def check_service_status():
    """Display real-time service status, port availability, and LAN endpoints."""
    print_banner()
    print(f"\n{Colors.CYAN}{Colors.BOLD}  Service Status & Network Endpoints{Colors.RESET}\n")
    
    # Query SC
    res = subprocess.run(["sc.exe", "query", SERVICE_NAME], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  Status:         {Colors.RED}NOT INSTALLED{Colors.RESET}")
    elif "RUNNING" in res.stdout:
        print(f"  Status:         {Colors.GREEN}● RUNNING (Windows Service){Colors.RESET}")
    elif "STOPPED" in res.stdout:
        print(f"  Status:         {Colors.YELLOW}○ STOPPED{Colors.RESET}")
    else:
        print(f"  Status:         {Colors.YELLOW}UNKNOWN / PENDING{Colors.RESET}")

    # Check local port response
    is_live = False
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=1.5) as resp:
            if resp.status == 200:
                is_live = True
    except Exception:
        is_live = False

    print(f"  Port {PORT}:       " + (f"{Colors.GREEN}LISTENING (HTTP OK){Colors.RESET}" if is_live else f"{Colors.YELLOW}NOT RESPONDING{Colors.RESET}"))
    print(f"\n  Access URLs:")
    print(f"  • Local:        {Colors.CYAN}http://localhost:{PORT}{Colors.RESET}")
    for ip in get_local_ips():
        print(f"  • LAN Device:   {Colors.CYAN}http://{ip}:{PORT}{Colors.RESET}")

    if LOG_FILE.exists():
        print(f"\n  Log File:       {Colors.DIM}{LOG_FILE}{Colors.RESET}")


def run_full_install():
    """Execute complete 1-click installation flow."""
    if not is_admin():
        run_as_admin(["--install"])
        return

    print_banner()
    print(f"{Colors.CYAN}  Starting Complete 1-Click Installation...{Colors.RESET}")

    if not install_dependencies():
        print(f"\n{Colors.RED}[!] Dependency installation failed.{Colors.RESET}")
        return

    configure_firewall()
    create_shortcuts()
    install_and_start_service()

    local_ips = get_local_ips()
    print(f"\n{Colors.CYAN}{Colors.BOLD}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}  ✨ METRICS BY JJ IS READY & RUNNING!{Colors.RESET}")
    print(f"     • Local:      {Colors.CYAN}http://localhost:{PORT}{Colors.RESET}")
    for ip in local_ips:
        print(f"     • LAN Access: {Colors.CYAN}http://{ip}:{PORT}{Colors.RESET}")
    print(f"     • Service:    {Colors.DIM}services.msc -> {SERVICE_NAME}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")

    try:
        choice = input("  Open dashboard in browser now? [Y/n]: ").strip().lower()
        if choice != "n":
            os.startfile(f"http://localhost:{PORT}")
    except Exception:
        pass


def start_standalone_server():
    """Run uvicorn in the current console window directly."""
    print_banner()
    print(f"\n{Colors.YELLOW}Starting Metrics by JJ Telemetry Server in foreground...{Colors.RESET}")
    print(f"Local URL: http://localhost:{PORT}")
    for ip in get_local_ips():
        print(f"LAN URL:   http://{ip}:{PORT}")
    print(f"\nPress Ctrl+C to stop.\n")

    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", "0.0.0.0",
        "--port", str(PORT),
    ]
    try:
        subprocess.run(cmd, cwd=str(ROOT_DIR))
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Server stopped.{Colors.RESET}")


def interactive_menu():
    """Interactive CLI menu when setup is run without arguments."""
    while True:
        print_banner()
        print(f"  {Colors.BOLD}Select an option:{Colors.RESET}\n")
        print(f"  {Colors.CYAN}[1]{Colors.RESET}  ⚡ 1-Click Full Install (Service + Firewall + Shortcuts + Auto-Start)")
        print(f"  {Colors.CYAN}[2]{Colors.RESET}  🚀 Quick Run Server in Console (Foreground mode)")
        print(f"  {Colors.CYAN}[3]{Colors.RESET}  🔍 Check Status & Network URLs")
        print(f"  {Colors.CYAN}[4]{Colors.RESET}  ▶️  Start Background Service")
        print(f"  {Colors.CYAN}[5]{Colors.RESET}  ⏹️  Stop Background Service")
        print(f"  {Colors.CYAN}[6]{Colors.RESET}  🌐 Open Web Dashboard in Browser")
        print(f"  {Colors.CYAN}[7]{Colors.RESET}  🗑️  Uninstall & Clean Up")
        print(f"  {Colors.CYAN}[0]{Colors.RESET}  ❌ Exit\n")

        try:
            choice = input(f"  {Colors.BOLD}Enter choice [1-7, 0]:{Colors.RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if choice == "1":
            run_full_install()
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
        elif choice == "2":
            start_standalone_server()
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
        elif choice == "3":
            check_service_status()
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
        elif choice == "4":
            if not is_admin():
                run_as_admin(["--start"])
            else:
                subprocess.run(["sc.exe", "start", SERVICE_NAME])
                input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
        elif choice == "5":
            if not is_admin():
                run_as_admin(["--stop"])
            else:
                subprocess.run(["sc.exe", "stop", SERVICE_NAME])
                input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
        elif choice == "6":
            os.startfile(f"http://localhost:{PORT}")
            print(f"  {Colors.GREEN}Dashboard opened in browser.{Colors.RESET}")
            time.sleep(1)
        elif choice == "7":
            uninstall()
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
        elif choice in ("0", "exit", "q"):
            print(f"\n  {Colors.DIM}Goodbye!{Colors.RESET}\n")
            break
        else:
            print(f"\n  {Colors.RED}Invalid option, please try again.{Colors.RESET}")
            time.sleep(1)


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--install", "-i", "install"):
            run_full_install()
        elif arg in ("--uninstall", "-u", "uninstall"):
            uninstall()
        elif arg in ("--status", "-s", "status"):
            check_service_status()
        elif arg in ("--start", "start"):
            if not is_admin():
                run_as_admin(["--start"])
            else:
                subprocess.run(["sc.exe", "start", SERVICE_NAME])
        elif arg in ("--stop", "stop"):
            if not is_admin():
                run_as_admin(["--stop"])
            else:
                subprocess.run(["sc.exe", "stop", SERVICE_NAME])
        elif arg in ("--run", "run", "--server"):
            start_standalone_server()
        elif arg in ("--open", "open"):
            os.startfile(f"http://localhost:{PORT}")
        elif arg in ("--help", "-h"):
            print("Metrics by JJ Setup & Control Utility")
            print("Usage: python setup.py [command]")
            print("Commands:")
            print("  --install    Full automated setup & service registration")
            print("  --uninstall  Remove service, shortcuts, and firewall rules")
            print("  --status     Check service and server status")
            print("  --start      Start the Windows service")
            print("  --stop       Stop the Windows service")
            print("  --run        Run standalone server in foreground")
            print("  --open       Open browser dashboard")
        else:
            print(f"Unknown argument: {arg}")
            print("Run with --help for available commands or run without arguments for interactive menu.")
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
