# 🖥️ Telegram PC Monitor & Remote Control

Bilgisayarınızın başından uzaktayken Telegram üzerinden bilgisayarınızın ne yaptığını anlık olarak takip etmenizi, ekran görüntüsü almanızı ve sistem durumunu kontrol etmenizi sağlayan Python tabanlı uzaktan izleme ve bildirim aracı.

---

## ✨ Özellikler

- 📸 **Anlık Ekran Görüntüsü (`/screenshot`):** Tek bir komutla monitörünüzün ekran görüntüsünü alır ve Telegram'a fotoğraf olarak iletir.
- 💻 **Aktif Pencere Takibi (`/active`):** Şu anda ekranda hangi programın veya web sayfasının odakta olduğunu gösterir.
- 📊 **Sistem Durumu (`/status`):** CPU, RAM, Disk (C:), Pil/Priz durumu ve bilgisayarın ne kadar süredir açık olduğunu raporlar.
- ⚙️ **Süreç & Kaynak Takibi (`/processes`):** En çok bellek ve işlemci tüketen uygulamaları listeler.
- 🌐 **Ağ ve IP Bilgisi (`/ip`):** Yerel IP ve Harici (Public) IP adresinizi gösterir.
- 🔒 **Uzaktan Kilitleme (`/lock`):** Bilgisayarı uzaktan kilitler (`Win + L`).
- ⚡ **Uzaktan Komut Çalıştırma (`/cmd <komut>`):** PowerShell komutlarını uzaktan çalıştırıp çıktısını Telegram'dan görebilirsiniz.
- 🔔 **Harici Bildirim Modülü (`notify.py`):** Uzun süren bir kodlama, veri indirme, model eğitimi veya render bittiğinde tek satırla Telegram'ınıza bildirim gönderir.
- 🛡️ **Kişisel Güvenlik Filtresi:** Yalnızca sizin belirlediğiniz Telegram Chat ID'lerinin botu kullanmasına izin verilir. Yabancılar botunuza erişemez.
- 🚀 **Windows Başlangıç Desteği:** İster tek tıklamayla görünmez arka plan modu (`start_hidden.vbs`), ister Windows açılışına otomatik ekleme (`install_autostart.bat`).

---

## 🚀 Hızlı Başlangıç Rehberi

### 1. Telegram Bot Token Alın
1. Telegram uygulamanızda **[@BotFather](https://t.me/BotFather)** botunu açın.
2. `/newbot` komutunu gönderin ve botunuza bir isim ve kullanıcı adı belirleyin.
3. BotFather'ın size verdiği **API Token**'ı kopyalayın (Örn: `7123456789:AAH...`).

### 2. Kendi Chat ID'nizi Öğrenin
1. Telegram'da **[@userinfobot](https://t.me/userinfobot)** botunu açıp `/start` deyin.
2. Size gönderilen `Id:` karşısındaki sayıyı not edin (Örn: `123456789`).

### 3. Yapılandırma (`.env` Dosyası)
Proje kök dizinindeki `.env.example` dosyasının bir kopyasını alıp adını `.env` yapın ve bilgilerinizi girin:

```env
TELEGRAM_BOT_TOKEN=buraya_botfather_tokeninizi_yazin
ALLOWED_CHAT_IDS=buraya_chat_id_nizi_yazin
HEARTBEAT_INTERVAL_MINUTES=0
```

> **Not:** `ALLOWED_CHAT_IDS` alanına kendi ID'nizi yazarak botun sadece size yanıt vermesini sağlarsınız.

### 4. Gerekli Kütüphaneleri Yükleyin
Terminalde proje dizinindeyken:
```bash
pip install -r requirements.txt
```

### 5. Botu Çalıştırın
```bash
python bot.py
```
veya doğrudan `start_bot.bat` dosyasına çift tıklayın!

Telegram'da botunuza gidip `/start` yazdığınızda hızlı erişim butonları karşınıza çıkacaktır.

---

## 🔔 Başka Scriptlerden Bildirim Gönderme (`notify.py`)

Bilgisayarınızda uzun süren bir işlem çalıştırdığınızda (örn. makine öğrenmesi eğitimi, veri kazıma, video render, yedekleme vb.), bittiğinde Telegram'a bildirim atabilirsiniz:

### Python İçinden:
```python
from notify import send_telegram_alert, send_telegram_photo

# Basit bildirim
send_telegram_alert("Model eğitimi başarıyla tamamlandı! Doğruluk: %98.4")

# Ekran görüntüsü ile birlikte bildirim
send_telegram_photo("sonuc_grafigi.png", caption="Eğitim kaybı grafiği")
```

### Komut Satırından / Terminalden:
```bash
python notify.py "Veri indirme işlemi bitti!"
python notify.py --screenshot "Model eğitimi bitti, güncel ekran görüntüsü"
```

---

## 🪟 Windows Başlangıcında Otomatik Başlatma

Bilgisayarınız her açıldığında botun arka planda sessizce (siyah pencere açılmadan) çalışması için:
1. `install_autostart.bat` dosyasına çift tıklayın.
2. Bot otomatik olarak Windows Başlangıç (`shell:startup`) klasörünüze eklenir.

---

## 📂 Dosya Yapısı

```
telegram-pc-monitor/
├── bot.py                 # Ana Telegram Bot uygulaması ve komut yöneticisi
├── system_info.py         # Ekran görüntüsü alma ve sistem izleme modülü
├── notify.py              # Harici projelerden bildirim atmak için CLI / modül
├── config.py              # Ortam değişkenleri ve güvenlik kontrolleri
├── requirements.txt       # Gerekli Python kütüphaneleri
├── .env.example           # Örnek konfigürasyon şablonu
├── .gitignore             # Hassas verilerin GitHub'a gitmesini engelleyen kural dosyası
├── start_bot.bat          # Hızlı başlatıcı (Konsol pencereli)
├── start_hidden.vbs       # Arka planda sessiz çalıştırıcı
├── install_autostart.bat  # Windows başlangıç klasörüne ekleyici
└── README.md              # Dokümantasyon
```

---

## 🔒 Güvenlik Notu

`.env` dosyası içerisinde hassas `TELEGRAM_BOT_TOKEN` ve `ALLOWED_CHAT_IDS` bilgileri yer aldığından `.gitignore` dosyasına eklenmiştir ve asla GitHub'a yüklenmez. Başka bir bilgisayara kurarken `.env.example` dosyasından yeni `.env` oluşturmanız yeterlidir.
