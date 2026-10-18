"""
Telegram Bildirim Modülü (notify.py)
-----------------------------------
Bu dosyayı doğrudan komut satırından çalıştırabilir veya diğer Python scriptlerinizde import ederek kullanabilirsiniz:

Örnek Python kullanımı:
    from notify import send_telegram_alert, send_telegram_photo
    send_telegram_alert("Model eğitimi bitti! Sonuçlar hazır.")

Örnek Terminal kullanımı:
    python notify.py "Veri indirme tamamlandı!"
    python notify.py --screenshot "Mevcut ekran durumu"
"""

import sys
import argparse
import requests
from pathlib import Path

# Yerel modüller
try:
    from config import BOT_TOKEN, ALLOWED_CHAT_IDS
    from system_info import take_screenshot
except ImportError:
    # Farklı bir dizinden çağrılıyorsa sys.path'e ekle
    current_dir = Path(__file__).resolve().parent
    sys.path.append(str(current_dir))
    from config import BOT_TOKEN, ALLOWED_CHAT_IDS
    from system_info import take_screenshot


def send_telegram_alert(message: str, chat_id: int = None) -> bool:
    """Telegram üzerinden bildirim mesajı gönderir."""
    if not BOT_TOKEN:
        print("[HATA] TELEGRAM_BOT_TOKEN tanımlanmamış. .env dosyasını kontrol edin.")
        return False

    targets = [chat_id] if chat_id else ALLOWED_CHAT_IDS
    if not targets:
        print("[HATA] Hedef chat_id bulunamadı. .env içerisindeki ALLOWED_CHAT_IDS'i doldurun.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    success = True
    for tid in targets:
        payload = {
            "chat_id": tid,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code != 200:
                print(f"[UYARI] Mesaj gönderilemedi (Chat ID: {tid}): {r.text}")
                success = False
        except Exception as e:
            print(f"[HATA] İstek gönderilirken hata oluştu: {e}")
            success = False
    return success


def send_telegram_photo(photo_path: str, caption: str = "", chat_id: int = None) -> bool:
    """Telegram üzerinden fotoğraf/ekran görüntüsü gönderir."""
    if not BOT_TOKEN:
        print("[HATA] TELEGRAM_BOT_TOKEN tanımlanmamış.")
        return False

    targets = [chat_id] if chat_id else ALLOWED_CHAT_IDS
    if not targets:
        print("[HATA] Hedef chat_id bulunamadı.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    success = True
    for tid in targets:
        try:
            with open(photo_path, "rb") as f:
                files = {"photo": f}
                data = {"chat_id": tid, "caption": caption}
                r = requests.post(url, data=data, files=files, timeout=20)
                if r.status_code != 200:
                    print(f"[UYARI] Fotoğraf gönderilemedi (Chat ID: {tid}): {r.text}")
                    success = False
        except Exception as e:
            print(f"[HATA] Fotoğraf gönderim hatası: {e}")
            success = False
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telegram Bildirim Gönderici")
    parser.add_argument("message", nargs="*", help="Gönderilecek mesaj metni")
    parser.add_argument("--screenshot", action="store_true", help="Mesajla birlikte anlık ekran görüntüsü de yolla")
    args = parser.parse_args()

    text = " ".join(args.message).strip() if args.message else "🔔 PC Bildirimi!"

    if args.screenshot:
        sc_path = take_screenshot()
        send_telegram_photo(sc_path, caption=f"📸 {text}")
        print("Ekran görüntüsü ve bildirim başarıyla iletildi.")
    else:
        send_telegram_alert(f"🔔 <b>Bildirim:</b>\n{text}")
        print("Bildirim başarıyla iletildi.")
