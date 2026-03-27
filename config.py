import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Yusu1F_m1").replace("@", "")

_db_ch = os.getenv("DB_CHANNEL_ID", "")
DB_CHANNEL_ID = int(_db_ch) if _db_ch else None

DATA_FILE = "memory_vault_data.json"
STORAGE_DIR = "memory_vault_storage"

os.makedirs(STORAGE_DIR, exist_ok=True)
