"""
Calculation Engine Desktop Application Launcher (.exe)
Double-clickable native Windows application that automatically detects the environment,
cleans port 8005, applies migrations, opens the browser, and runs the server.
"""
import sys
import os
import time
import subprocess
import webbrowser
from pathlib import Path

# Get directory where the executable or script is located
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

os.chdir(BASE_DIR)


def find_python() -> str:
    """Finds the Python executable inside .venv or venv."""
    candidates = [
        BASE_DIR / ".venv" / "Scripts" / "python.exe",
        BASE_DIR / "venv" / "Scripts" / "python.exe",
        BASE_DIR / "env" / "Scripts" / "python.exe",
        BASE_DIR.parent / ".venv" / "Scripts" / "python.exe",
        BASE_DIR.parent / "venv" / "Scripts" / "python.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)

    # Fallback to system python
    return "python"


def free_port(port: int = 8005):
    """Frees port 8005 if an existing zombie process is holding it."""
    if sys.platform == "win32":
        try:
            cmd = (
                f'powershell -NoProfile -Command "$p = Get-NetTCPConnection -LocalPort {port} '
                f'-ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; '
                f'if ($p) {{ Stop-Process -Id $p -Force }}"'
            )
            subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
        except Exception:
            pass


def main():
    print("=" * 65)
    print("      Calculation Engine & AI Agent - Desktop Launcher")
    print("=" * 65)
    print()

    py_exe = find_python()
    print(f"[1/4] Found Python environment: {py_exe}")

    # 1. Clear Port 8005
    print("[2/4] Ensuring port 8005 is available...")
    free_port(8005)

    # 2. Apply Migrations
    print("[3/4] Verifying database tables...")
    try:
        subprocess.run([py_exe, "manage.py", "migrate", "--noinput"], check=False)
    except Exception as e:
        print(f"      [Notice] Migration check skipped: {e}")

    # 3. Open Browser
    print("[4/4] Opening default web browser in 2 seconds...")
    import threading
    def _open_url():
        time.sleep(2)
        try:
            webbrowser.open("http://127.0.0.1:8005/")
        except Exception:
            pass

    threading.Thread(target=_open_url, daemon=True).start()

    # 4. Run Server
    print()
    print("=" * 65)
    print("  Calculation Dashboard is LIVE!")
    print("  - Local URL:   http://127.0.0.1:8005/")
    print("  - Network URL: http://0.0.0.0:8005/")
    print("=" * 65)
    print("  * KEEP THIS WINDOW OPEN while using the application.")
    print("  * Close this window or press Ctrl + C to stop.")
    print("=" * 65)
    print()

    try:
        subprocess.run([py_exe, "manage.py", "runserver", "0.0.0.0:8005"])
    except KeyboardInterrupt:
        print("\n[INFO] Application closed successfully.")
    except Exception as e:
        print(f"\n[ERROR] Server stopped: {e}")
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
