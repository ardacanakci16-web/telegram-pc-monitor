import os
import sys
import time
import socket
import shutil
import datetime
import subprocess
import ctypes
from pathlib import Path
from typing import Dict, Any, List
import psutil
from PIL import ImageGrab
import requests

IS_WINDOWS = os.name == "nt"

BASE_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = BASE_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


def ensure_desktop():
    """Windows'ta arka plan veya servis çağrılarında masaüstü erişimini bağlar."""
    if not IS_WINDOWS:
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0"
        return
    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


def get_active_window_title() -> str:
    """Şu an ekranda aktif/odakta olan pencerenin başlığını döndürür."""
    ensure_desktop()
    if IS_WINDOWS:
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "Bilinmiyor / Kilitli Ekran"
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            title = buf.value.strip()
            return title if title else "Masaüstü / Boş"
        except Exception as e:
            return f"Hata: {e}"
    else:
        # Linux (X11 / Wayland)
        try:
            if shutil.which("xdotool"):
                res = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True, text=True, timeout=2
                )
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            if shutil.which("xprop"):
                root_res = subprocess.run(
                    ["xprop", "-root", "_NET_ACTIVE_WINDOW"],
                    capture_output=True, text=True, timeout=2
                )
                if root_res.returncode == 0 and "#" in root_res.stdout:
                    win_id = root_res.stdout.split("#")[-1].strip().split()[0]
                    if win_id and win_id != "0x0":
                        win_res = subprocess.run(
                            ["xprop", "-id", win_id, "_NET_WM_NAME", "WM_NAME"],
                            capture_output=True, text=True, timeout=2
                        )
                        for line in win_res.stdout.splitlines():
                            if "=" in line and '"' in line:
                                return line.split('"', 1)[1].rsplit('"', 1)[0]
            return "Linux Masaüstü / Aktif Oturum"
        except Exception as e:
            return f"Linux Oturumu ({e})"


def take_screenshot(filename: str = None) -> str:
    """Ekran görüntüsü alır ve dosya yolunu döndürür (Windows & Linux uyumlu)."""
    ensure_desktop()
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(SCREENSHOT_DIR / f"screenshot_{timestamp}.png")

    # 1. Önce mss kütüphanesini dene (hem Windows hem Linux X11'de hızlıdır)
    try:
        import mss
        with mss.mss() as sct:
            sct.shot(output=filename)
        if Path(filename).exists():
            return filename
    except Exception:
        pass

    # 2. PIL ImageGrab dene
    try:
        img = ImageGrab.grab(all_screens=True) if IS_WINDOWS else ImageGrab.grab()
        img.save(filename, "PNG")
        return filename
    except Exception:
        pass

    # 3. Linux sistem araçları yedekleri (gnome-screenshot, scrot, import)
    if not IS_WINDOWS:
        for cmd in [
            ["gnome-screenshot", "-f", filename],
            ["scrot", filename],
            ["import", "-window", "root", filename],
        ]:
            if shutil.which(cmd[0]):
                subprocess.run(cmd, timeout=5, check=False)
                if Path(filename).exists():
                    return filename

    raise RuntimeError("Ekran görüntüsü alınamadı (uygun grafik sunucusu veya araç bulunamadı).")


def get_system_stats() -> Dict[str, Any]:
    """Sistem CPU, RAM, Disk, Pil ve Aktif Pencere bilgilerini toplar."""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count(logical=True)

    # RAM
    ram = psutil.virtual_memory()
    ram_total_gb = ram.total / (1024 ** 3)
    ram_used_gb = ram.used / (1024 ** 3)
    ram_percent = ram.percent

    # Disk (Windows: C:\, Linux: /)
    disk_mount = "C:\\" if IS_WINDOWS else "/"
    try:
        disk = psutil.disk_usage(disk_mount)
        disk_total_gb = disk.total / (1024 ** 3)
        disk_free_gb = disk.free / (1024 ** 3)
        disk_percent = disk.percent
    except Exception:
        disk_total_gb = disk_free_gb = disk_percent = 0

    # Pil (Laptop ise)
    battery = psutil.sensors_battery()
    battery_info = "Masaüstü (Pil yok)"
    if battery:
        plugged_str = "Prizde (Şarj oluyor)" if battery.power_plugged else "Pilde"
        battery_info = f"%{battery.percent:.0f} ({plugged_str})"

    # Uptime
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime_delta = datetime.datetime.now() - boot_time
    hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{hours} saat {minutes} dk"

    active_win = get_active_window_title()

    return {
        "cpu_percent": cpu_percent,
        "cpu_count": cpu_count,
        "ram_used_gb": ram_used_gb,
        "ram_total_gb": ram_total_gb,
        "ram_percent": ram_percent,
        "disk_mount": "C:" if IS_WINDOWS else "/",
        "disk_free_gb": disk_free_gb,
        "disk_total_gb": disk_total_gb,
        "disk_percent": disk_percent,
        "battery_info": battery_info,
        "uptime": uptime_str,
        "active_window": active_win,
    }


def get_top_processes(limit: int = 5) -> List[Dict[str, Any]]:
    """En çok RAM ve CPU kullanan süreçleri listeler."""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # RAM'e göre sırala
    procs.sort(key=lambda x: x.get('memory_percent') or 0, reverse=True)
    return procs[:limit]


def get_network_info() -> Dict[str, str]:
    """Yerel IP, makine adı ve harici (Public) IP adresini döndürür."""
    hostname = socket.gethostname()
    local_ip = "127.0.0.1"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
    except Exception:
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            pass

    public_ip = "Bilinmiyor"
    try:
        resp = requests.get("https://api.ipify.org?format=json", timeout=3)
        if resp.status_code == 200:
            public_ip = resp.json().get("ip", "Bilinmiyor")
    except Exception:
        pass

    return {
        "hostname": hostname,
        "local_ip": local_ip,
        "public_ip": public_ip
    }


def lock_workstation() -> bool:
    """Bilgisayarı kilitler (Windows & Linux uyumlu)."""
    if IS_WINDOWS:
        try:
            ctypes.windll.user32.LockWorkStation()
            return True
        except Exception:
            return False
    else:
        for cmd in [
            ["loginctl", "lock-session"],
            ["xdg-screensaver", "lock"],
            ["gnome-screensaver-command", "-l"],
        ]:
            if shutil.which(cmd[0]):
                res = subprocess.run(cmd, check=False)
                if res.returncode == 0:
                    return True
        return False
