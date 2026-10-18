import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını projenin bulunduğu dizinden yükle
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# İzin verilen kullanıcı / chat id'leri
raw_allowed = os.getenv("ALLOWED_CHAT_IDS", "").strip()
ALLOWED_CHAT_IDS = []
if raw_allowed:
    for cid in raw_allowed.split(","):
        cid = cid.strip()
        if cid.lstrip("-").isdigit():
            ALLOWED_CHAT_IDS.append(int(cid))

# Periyodik heartbeat (dakika, 0 ise kapalı)
try:
    HEARTBEAT_INTERVAL_MINUTES = int(os.getenv("HEARTBEAT_INTERVAL_MINUTES", "0"))
except ValueError:
    HEARTBEAT_INTERVAL_MINUTES = 0


def is_authorized(user_id: int) -> bool:
    """Kullanıcının bu botu kullanma yetkisi var mı kontrol eder."""
    if not ALLOWED_CHAT_IDS:
        # Eğer henüz ID girilmediyse ilk kullanıcı için uyarı vermek üzere izin verilebilir
        # ancak güvenlik gereği ID girildiyse kesinlikle eşleşme arar.
        return True
    return user_id in ALLOWED_CHAT_IDS
