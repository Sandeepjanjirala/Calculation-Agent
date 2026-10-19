"""
Calculation Engine Desktop Application Launcher (.exe)
Double-clickable native Windows application that automatically detects:
1. The project folder (even if the user moved this .exe to the Desktop!)
2. Virtual environments (.venv or venv)
3. Cleans port 8005, verifies migrations, opens browser, and runs the server.
"""
import sys
import os
import time
import subprocess
import webbrowser
from pathlib import Path


def find_project_dir() -> Path:
    """Finds the Calculation-Agent project directory containing manage.py."""
    current = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent

    # 1. Is manage.py right here in the same directory?
    if (current / "manage.py").is_file():
        return current

    # 2. Is there a Calculation-Agent subfolder?
    if (current / "Calculation-Agent" / "manage.py").is_file():
        return current / "Calculation-Agent"

    # 3. Known / common locations on Windows
    home = Path.home()
    candidates = [
        Path("C:/calculation/Calculation-Agent"),
        Path("C:/Calculation-Agent"),
        Path("D:/calculation/Calculation-Agent"),
        Path("D:/Calculation-Agent"),
        home / "Calculation-Agent",
        home / "Desktop" / "Calculation-Agent",
        home / "OneDrive" / "Desktop" / "Calculation-Agent",
        home / "Downloads" / "Calculation-Agent",
        home / "Documents" / "Calculation-Agent",
        home / "OneDrive" / "Documents" / "Calculation-Agent",
        current.parent / "Calculation-Agent",
        current.parent,
    ]
    for c in candidates:
        if (c / "manage.py").is_file():
            return c

    # 4. Search user's home and C:\ drive for Calculation-Agent
    search_roots = [
        home / "Desktop",
        home / "OneDrive" / "Desktop",
        home / "Downloads",
        home,
        Path("C:/calculation"),
        Path("C:/"),
    ]
    for root in search_roots:
        if not root.exists():
            continue
        try:
            for p in root.glob("**/Calculation-Agent"):
                if (p / "manage.py").is_file():
                    return p
        except Exception:
            pass

    return current


def find_python(project_dir: Path) -> str:
    """Finds Python executable prioritizing .venv and venv inside project_dir."""
    candidates = [
        project_dir / ".venv" / "Scripts" / "python.exe",
        project_dir / "venv" / "Scripts" / "python.exe",
        project_dir / "env" / "Scripts" / "python.exe",
        project_dir.parent / ".venv" / "Scripts" / "python.exe",
        project_dir.parent / "venv" / "Scripts" / "python.exe",
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

    # Locate project directory
    project_dir = find_project_dir()
    os.chdir(project_dir)
    manage_py = project_dir / "manage.py"

    if not manage_py.is_file():
        print("=" * 65)
        print("  [ERROR] Cannot find 'manage.py'!")
        print("=" * 65)
        print(f"  Attempted location: {project_dir}")
        print()
        print("  CalculationEngine.exe needs the project files.")
        print("  Please make sure CalculationEngine.exe is placed inside the")
        print("  'Calculation-Agent' folder (or that 'Calculation-Agent' exists).")
        print()
        print("  To place a shortcut on Desktop:")
        print("  Right-click CalculationEngine.exe inside Calculation-Agent")
        print("  -> 'Show more options' -> 'Send to' -> 'Desktop (create shortcut)'")
        print("=" * 65)
        input("\nPress Enter to exit...")
        sys.exit(1)

    print(f"[1/5] Project directory: {project_dir}")

    py_exe = find_python(project_dir)
    print(f"[2/5] Python environment: {py_exe}")

    # 1. Clear Port 8005
    print("[3/5] Ensuring port 8005 is available...")
    free_port(8005)

    # 2. Apply Migrations
    print("[4/5] Verifying database tables...")
    try:
        subprocess.run([py_exe, str(manage_py), "migrate", "--noinput"], check=False)
    except Exception as e:
        print(f"      [Notice] Migration check skipped: {e}")

    # 3. Open Browser
    print("[5/5] Opening default web browser in 2 seconds...")
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
        subprocess.run([py_exe, str(manage_py), "runserver", "0.0.0.0:8005"])
    except KeyboardInterrupt:
        print("\n[INFO] Application closed successfully.")
    except Exception as e:
        print(f"\n[ERROR] Server error: {e}")
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
