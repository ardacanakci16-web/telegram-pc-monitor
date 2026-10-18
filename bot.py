import sys
import time
import subprocess
import threading
from pathlib import Path
import telebot
from telebot import types

# Windows konsolunda UTF-8 çıktı desteği
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from config import BOT_TOKEN, ALLOWED_CHAT_IDS, HEARTBEAT_INTERVAL_MINUTES, is_authorized
import system_info

if not BOT_TOKEN:
    print("[HATA] TELEGRAM_BOT_TOKEN bulunamadı!")
    print("Lütfen projedeki .env dosyasına bot tokenınızı girin.")
    print("Örnek: TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


def get_main_keyboard():
    """Hızlı erişim buton menüsü"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_screen = types.KeyboardButton("📸 Ekran Görüntüsü")
    btn_status = types.KeyboardButton("📊 Sistem Durumu")
    btn_active = types.KeyboardButton("💻 Aktif Pencere")
    btn_proc = types.KeyboardButton("⚙️ Süreçler")
    btn_net = types.KeyboardButton("🌐 Ağ & IP")
    btn_lock = types.KeyboardButton("🔒 PC'yi Kilitle")
    markup.add(btn_screen, btn_status)
    markup.add(btn_active, btn_proc)
    markup.add(btn_net, btn_lock)
    return markup


def check_auth(func):
    """Yetkisiz erişimleri engelleyen güvenlik dekoratörü"""
    def wrapper(message, *args, **kwargs):
        user_id = message.from_user.id
        if not is_authorized(user_id):
            bot.reply_to(
                message,
                f"⛔ <b>Yetkisiz Erişim!</b>\n\n"
                f"Bu bot sadece bilgisayar sahibine aittir.\n"
                f"Sizin Telegram ID: <code>{user_id}</code>\n\n"
                f"Eğer bu bilgisayar size aitse, bu ID'yi projedeki <b>.env</b> dosyasına "
                f"<code>ALLOWED_CHAT_IDS={user_id}</code> olarak ekleyin."
            )
            print(f"[GÜVENLİK UYARISI] Yetkisiz kullanıcı istek attı: ID {user_id}")
            return
        return func(message, *args, **kwargs)
    return wrapper


@bot.message_handler(commands=['start', 'help'])
@check_auth
def send_welcome(message):
    user_name = message.from_user.first_name or "Kullanıcı"
    text = (
        f"👋 Merhaba <b>{user_name}</b>!\n"
        f"🖥️ <b>PC Uzaktan Takip ve Yönetim Botu</b> aktif.\n\n"
        f"<b>Kullanabileceğiniz Komutlar:</b>\n"
        f"• 📸 <b>/screenshot</b> - Anlık ekran görüntüsü alır ve gönderir.\n"
        f"• 📊 <b>/status</b> - CPU, RAM, Disk, Pil ve aktif pencere özeti.\n"
        f"• 💻 <b>/active</b> - Şu an açık olan aktif pencere başlığı.\n"
        f"• ⚙️ <b>/processes</b> - En çok kaynak tüketen 5 işlem.\n"
        f"• 🌐 <b>/ip</b> - Bilgisayar adı, yerel ve dış IP bilgisi.\n"
        f"• 🔒 <b>/lock</b> - Bilgisayarı kilitler (Win+L).\n"
        f"• ⚡ <b>/cmd &lt;komut&gt;</b> - PowerShell komutu çalıştırır.\n\n"
        f"Aşağıdaki menü tuşlarını da kullanabilirsiniz 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())


@bot.message_handler(commands=['screenshot'])
@bot.message_handler(func=lambda msg: msg.text == "📸 Ekran Görüntüsü")
@check_auth
def handle_screenshot(message):
    wait_msg = bot.send_message(message.chat.id, "📸 Ekran görüntüsü alınıyor, lütfen bekleyin...")
    try:
        sc_path = system_info.take_screenshot()
        active_win = system_info.get_active_window_title()
        caption = f"🖥️ <b>Aktif Pencere:</b> {active_win}"
        with open(sc_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=caption)
        bot.delete_message(message.chat.id, wait_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Ekran görüntüsü alınamadı: {e}", message.chat.id, wait_msg.message_id)


@bot.message_handler(commands=['status'])
@bot.message_handler(func=lambda msg: msg.text == "📊 Sistem Durumu")
@check_auth
def handle_status(message):
    stats = system_info.get_system_stats()
    text = (
        f"📊 <b>Sistem Durumu</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💻 <b>Aktif Pencere:</b> <code>{stats['active_window']}</code>\n"
        f"⚡ <b>CPU Kullanımı:</b> %{stats['cpu_percent']} ({stats['cpu_count']} Çekirdek)\n"
        f"🧠 <b>RAM:</b> {stats['ram_used_gb']:.1f} GB / {stats['ram_total_gb']:.1f} GB (%{stats['ram_percent']})\n"
        f"💾 <b>Disk (C:):</b> {stats['disk_free_gb']:.1f} GB Boş / {stats['disk_total_gb']:.1f} GB (%{stats['disk_percent']} dolu)\n"
        f"🔋 <b>Güç / Pil:</b> {stats['battery_info']}\n"
        f"⏱️ <b>Çalışma Süresi:</b> {stats['uptime']}\n"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['active'])
@bot.message_handler(func=lambda msg: msg.text == "💻 Aktif Pencere")
@check_auth
def handle_active(message):
    title = system_info.get_active_window_title()
    bot.send_message(message.chat.id, f"💻 <b>Şu An Odaktaki Pencere:</b>\n<code>{title}</code>")


@bot.message_handler(commands=['processes'])
@bot.message_handler(func=lambda msg: msg.text == "⚙️ Süreçler")
@check_auth
def handle_processes(message):
    procs = system_info.get_top_processes(limit=6)
    lines = ["⚙️ <b>En Çok RAM Kullanan Uygulamalar:</b>", "━━━━━━━━━━━━━━━━━━"]
    for p in procs:
        name = p.get('name') or "Bilinmiyor"
        pid = p.get('pid')
        mem = p.get('memory_percent') or 0
        cpu = p.get('cpu_percent') or 0
        lines.append(f"• <b>{name}</b> (PID: {pid}) - RAM: %{mem:.1f} | CPU: %{cpu:.1f}")
    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(commands=['ip'])
@bot.message_handler(func=lambda msg: msg.text == "🌐 Ağ & IP")
@check_auth
def handle_network(message):
    net = system_info.get_network_info()
    text = (
        f"🌐 <b>Ağ & Makine Bilgisi</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💻 <b>Bilgisayar Adı:</b> {net['hostname']}\n"
        f"🏠 <b>Yerel IP:</b> <code>{net['local_ip']}</code>\n"
        f"🌍 <b>Dış IP (Public):</b> <code>{net['public_ip']}</code>\n"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['lock'])
@bot.message_handler(func=lambda msg: msg.text == "🔒 PC'yi Kilitle")
@check_auth
def handle_lock(message):
    success = system_info.lock_workstation()
    if success:
        bot.send_message(message.chat.id, "🔒 Bilgisayar ekranı kilitlendi!")
    else:
        bot.send_message(message.chat.id, "❌ Kilitleme işlemi başarısız oldu.")


@bot.message_handler(commands=['cmd'])
@check_auth
def handle_command(message):
    # Komut argümanını ayıkla
    cmd = message.text.replace("/cmd", "", 1).strip()
    if not cmd:
        bot.send_message(message.chat.id, "Kullanım: <code>/cmd &lt;çalıştırılacak komut&gt;</code>\nÖrnek: <code>/cmd dir</code>")
        return

    wait_msg = bot.send_message(message.chat.id, f"⚡ Komut çalıştırılıyor:\n<code>{cmd}</code>")
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=25
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        result = out if out else (err if err else "[Çıktı yok]")
        if len(result) > 3500:
            result = result[:3500] + "\n\n... (Çıktı çok uzun olduğu için kırpıldı)"
        
        bot.edit_message_text(
            f"✅ <b>Komut Sonucu:</b>\n<pre>{result}</pre>",
            message.chat.id,
            wait_msg.message_id
        )
    except subprocess.TimeoutExpired:
        bot.edit_message_text("⏱️ Komut 25 saniye zaman aşımına uğradı.", message.chat.id, wait_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Komut çalıştırma hatası: {e}", message.chat.id, wait_msg.message_id)


@bot.message_handler(func=lambda msg: True)
@check_auth
def handle_general_message(message):
    raw_text = (message.text or "").strip()
    text_lower = raw_text.lower()
    
    # Gelen mesajı konsola ve dosyaya kaydet
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{ts}] {message.from_user.first_name} (ID: {message.from_user.id}): {raw_text}\n"
    print(f"[MESAJ ALINDI] {raw_text}")
    try:
        from config import BASE_DIR
        with open(BASE_DIR / "chat_history.log", "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass

    # Akıllı yanıtlar ve doğal dil komutları
    if any(k in text_lower for k in ["ekran", "foto", "ss", "screenshot", "resim", "görüntü", "goruntu"]):
        handle_screenshot(message)
    elif any(k in text_lower for k in ["durum", "status", "neler yapıyorsun", "ne yapıyorsun", "ne yapiyorsun", "pc nasıl", "bilgisayar nasıl"]):
        handle_status(message)
    elif any(k in text_lower for k in ["aktif", "pencere", "odak"]):
        handle_active(message)
    elif any(k in text_lower for k in ["süreç", "surec", "process"]):
        handle_processes(message)
    elif any(k in text_lower for k in ["selam", "merhaba", "hey", "hi", "hello", "slm"]):
        stats = system_info.get_system_stats()
        bot.reply_to(
            message,
            f"👋 <b>Merhaba!</b>\n\n"
            f"Bilgisayarınız aktif ve çalışıyor.\n"
            f"• <b>Şu An Açık:</b> <code>{stats['active_window']}</code>\n"
            f"• <b>CPU:</b> %{stats['cpu_percent']} | <b>RAM:</b> %{stats['ram_percent']}\n\n"
            f"Ekranı görmek için <b>'📸 Ekran Görüntüsü'</b>ne basabilirsiniz.",
            reply_markup=get_main_keyboard()
        )
    else:
        bot.reply_to(
            message,
            f"📩 Mesajınızı aldım:\n<i>\"{raw_text}\"</i>\n\n"
            f"Bilgisayarda işlem yapmak için aşağıdaki butonları kullanabilir "
            f"veya <code>/screenshot</code>, <code>/status</code> yazabilirsiniz 👇",
            reply_markup=get_main_keyboard()
        )


def start_heartbeat():
    """Belirlenen aralıklarla arka planda durum bildirimi gönderir."""
    if HEARTBEAT_INTERVAL_MINUTES <= 0 or not ALLOWED_CHAT_IDS:
        return

    print(f"[BİLGİ] Periyodik raporlayıcı (Heartbeat) {HEARTBEAT_INTERVAL_MINUTES} dakikada bir çalışacak.")
    while True:
        try:
            time.sleep(HEARTBEAT_INTERVAL_MINUTES * 60)
            stats = system_info.get_system_stats()
            text = (
                f"⏰ <b>Periyodik Durum Bildirimi ({HEARTBEAT_INTERVAL_MINUTES} dk):</b>\n"
                f"• Aktif: <code>{stats['active_window']}</code>\n"
                f"• CPU: %{stats['cpu_percent']} | RAM: %{stats['ram_percent']}\n"
                f"• Pil: {stats['battery_info']}"
            )
            for cid in ALLOWED_CHAT_IDS:
                bot.send_message(cid, text)
        except Exception as e:
            print(f"[UYARI] Heartbeat döngüsünde hata: {e}")
            time.sleep(60)


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Telegram PC Monitor Başlatılıyor...")
    print(f"İzinli Chat ID'leri: {ALLOWED_CHAT_IDS if ALLOWED_CHAT_IDS else 'Henüz belirtilmedi (Herkese açık - ID öğrenme modu)'}")
    print("Bot mesajları dinliyor (Çıkış için Ctrl+C)...")
    print("=" * 50)

    # Heartbeat thread'ini başlat
    if HEARTBEAT_INTERVAL_MINUTES > 0:
        t = threading.Thread(target=start_heartbeat, daemon=True)
        t.start()

    # Telegram bot polling (sonsuz döngü)
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"[HATA] Bağlantı kesildi, 5 saniye sonra tekrar denenecek: {e}")
            time.sleep(5)
