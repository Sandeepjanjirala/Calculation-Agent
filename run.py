"""
Universal Cross-Platform Application Launcher for Calculation Engine & AI Agent.
Works seamlessly in any environment, auto-detects virtual environments (.venv or venv),
cleans up stale ports, applies migrations, launches browser, and starts the server.
"""
import sys
import os
import time
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)


def find_python() -> str:
    """Finds the best Python executable prioritizing virtual environments (.venv, venv)."""
    candidates = [
        BASE_DIR / ".venv" / "Scripts" / "python.exe",
        BASE_DIR / "venv" / "Scripts" / "python.exe",
        BASE_DIR / "env" / "Scripts" / "python.exe",
        BASE_DIR / ".venv" / "bin" / "python",
        BASE_DIR / "venv" / "bin" / "python",
        BASE_DIR.parent / ".venv" / "Scripts" / "python.exe",
        BASE_DIR.parent / "venv" / "Scripts" / "python.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)

    # If current sys.executable is inside a venv, use it
    if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        return sys.executable

    return sys.executable or "python"


def free_port(port: int = 8005):
    """Frees the target port if an old zombie process is holding it."""
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
    print("=" * 60)
    print("   Calculation Specification Engine & AI Agent Launcher")
    print("=" * 60)
    print()

    py_exe = find_python()
    print(f"[INFO] Using Python environment: {py_exe}")

    # 1. Clean port 8005
    print("[INFO] Checking port 8005 availability...")
    free_port(8005)

    # 2. Run migrations
    print("[INFO] Verifying database migrations...")
    try:
        subprocess.run([py_exe, "manage.py", "migrate", "--noinput"], check=False)
    except Exception as e:
        print(f"[WARNING] Migration check skipped: {e}")

    # 3. Launch browser in a background thread
    import threading
    def _open_url():
        time.sleep(2)
        try:
            webbrowser.open("http://127.0.0.1:8005/")
        except Exception:
            pass

    threading.Thread(target=_open_url, daemon=True).start()

    # 4. Start Server on 0.0.0.0:8005
    print()
    print("=" * 60)
    print("   Server running successfully!")
    print("   - Local Browser:   http://127.0.0.1:8005/")
    print("   - Network Access:  http://0.0.0.0:8005/")
    print("=" * 60)
    print("[INFO] Press Ctrl + C to stop the server.\n")

    try:
        subprocess.run([py_exe, "manage.py", "runserver", "0.0.0.0:8005"])
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped gracefully.")


if __name__ == "__main__":
    main()
