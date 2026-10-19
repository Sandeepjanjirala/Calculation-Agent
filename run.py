"""
Universal Cross-Platform Application Launcher for Calculation Engine & AI Agent.
Works seamlessly in any environment, auto-detects virtual environments (.venv or venv),
auto-locates project folder, cleans up stale ports, applies migrations, launches browser, and starts the server.
"""
import sys
import os
import time
import subprocess
import webbrowser
from pathlib import Path


def find_project_dir() -> Path:
    current = Path(__file__).resolve().parent
    if (current / "manage.py").is_file():
        return current
    if (current / "Calculation-Agent" / "manage.py").is_file():
        return current / "Calculation-Agent"

    home = Path.home()
    candidates = [
        Path("C:/calculation/Calculation-Agent"),
        Path("C:/Calculation-Agent"),
        home / "Calculation-Agent",
        home / "Desktop" / "Calculation-Agent",
        home / "OneDrive" / "Desktop" / "Calculation-Agent",
        home / "Downloads" / "Calculation-Agent",
        home / "Documents" / "Calculation-Agent",
        home / "OneDrive" / "Documents" / "Calculation-Agent",
    ]
    for c in candidates:
        if (c / "manage.py").is_file():
            return c
    return current


def find_python(project_dir: Path) -> str:
    """Finds the best Python executable prioritizing virtual environments (.venv, venv)."""
    candidates = [
        project_dir / ".venv" / "Scripts" / "python.exe",
        project_dir / "venv" / "Scripts" / "python.exe",
        project_dir / "env" / "Scripts" / "python.exe",
        project_dir.parent / ".venv" / "Scripts" / "python.exe",
        project_dir.parent / "venv" / "Scripts" / "python.exe",
        project_dir / ".venv" / "bin" / "python",
        project_dir / "venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)

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

    project_dir = find_project_dir()
    os.chdir(project_dir)
    manage_py = project_dir / "manage.py"

    if not manage_py.is_file():
        print(f"[ERROR] manage.py not found in {project_dir}")
        sys.exit(1)

    py_exe = find_python(project_dir)
    print(f"[INFO] Project Directory: {project_dir}")
    print(f"[INFO] Using Python environment: {py_exe}")

    # 1. Clean port 8005
    print("[INFO] Checking port 8005 availability...")
    free_port(8005)

    # 2. Run migrations
    print("[INFO] Verifying database migrations...")
    try:
        subprocess.run([py_exe, str(manage_py), "migrate", "--noinput"], check=False)
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
        subprocess.run([py_exe, str(manage_py), "runserver", "0.0.0.0:8005"])
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped gracefully.")


if __name__ == "__main__":
    main()
