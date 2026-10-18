import os
import time
import socket
import datetime
import ctypes
from pathlib import Path
from typing import Dict, Any, List
import psutil
from PIL import ImageGrab
import requests

BASE_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = BASE_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


def ensure_desktop():
    """Windows'ta arka plan veya servis çağrılarında masaüstü erişimini bağlar."""
    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


def get_active_window_title() -> str:
    """Şu an ekranda aktif/odakta olan pencerenin başlığını döndürür."""
    try:
        ensure_desktop()
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


def take_screenshot(filename: str = None) -> str:
    """Ekran görüntüsü alır ve dosya yolunu döndürür."""
    ensure_desktop()
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(SCREENSHOT_DIR / f"screenshot_{timestamp}.png")
    
    img = ImageGrab.grab(all_screens=True)
    img.save(filename, "PNG")
    return filename


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

    # Disk (C:\ veya ana sürücü)
    try:
        disk = psutil.disk_usage("C:\\")
        disk_total_gb = disk.total / (1024 ** 3)
        disk_free_gb = disk.free / (1024 ** 3)
        disk_percent = disk.percent
    except Exception:
        disk_total_gb = disk_free_gb = disk_percent = 0

    # Pil (Laptop ise)
    battery = psutil.sensors_battery()
    battery_info = "Masaüstü (Pil yok)"
    if battery:
        plugged_str = "Prizde (Sarj oluyor)" if battery.power_plugged else "Pilde"
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
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"

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
    """Bilgisayarı kilitler (Win + L benzeri)."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return True
    except Exception:
        return False
