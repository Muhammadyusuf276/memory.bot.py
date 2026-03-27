import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

DATA_FILE = "memory_vault_data.json"
STORAGE_DIR = "memory_vault_storage"

os.makedirs(STORAGE_DIR, exist_ok=True)
