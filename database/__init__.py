import json
import os
import logging
from datetime import datetime

from config import DATA_FILE

logger = logging.getLogger(__name__)

# ==================== MA'LUMOTLAR OMBORI ====================

def load_data() -> dict:
    """Ma'lumotlarni JSON fayldan yuklash."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Ma'lumotlarni yuklashda xatolik: %s", e)
            return {}
    return {}


def save_data(data: dict) -> None:
    """Ma'lumotlarni JSON faylga saqlash."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error("Ma'lumotlarni saqlashda xatolik: %s", e)


def get_user(user_id: str) -> dict:
    """Foydalanuvchi ma'lumotlarini olish, agar yo'q bo'lsa yangi yaratish."""
    data = load_data()
    if user_id not in data:
        data[user_id] = {
            "folders": {},
            "contacts": {},
            "notes": {},
            "links": {},
            "schedules": {},
            "language": None,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
        }
        save_data(data)
    return data[user_id]


def update_user_field(user_id: str, field: str, value) -> None:
    """Foydalanuvchining bitta maydonini yangilash."""
    data = load_data()
    if user_id not in data:
        get_user(user_id)
        data = load_data()
    data[user_id][field] = value
    data[user_id]["last_activity"] = datetime.now().isoformat()
    save_data(data)


def get_user_lang(user_id: str) -> str:
    """Foydalanuvchi tilini olish."""
    user = get_user(user_id)
    return user.get("language") or "uz"


def update_user_activity(user_id: str) -> None:
    """Foydalanuvchi aktivligini yangilash."""
    data = load_data()
    if user_id in data:
        data[user_id]["last_activity"] = datetime.now().isoformat()
        save_data(data)


def get_user_stats() -> dict:
    """Umumiy foydalanuvchi statistikasini olish (admin uchun)."""
    data = load_data()
    total_users = 0
    active_today = 0
    active_weekly = 0

    for user_id, user_data in data.items():
        if user_id == "stats":
            continue
        total_users += 1
        last_activity = user_data.get("last_activity")
        if last_activity:
            try:
                last_seen = datetime.fromisoformat(last_activity)
                days_diff = (datetime.now() - last_seen).days
                if days_diff <= 1:
                    active_today += 1
                if days_diff <= 7:
                    active_weekly += 1
            except (ValueError, TypeError):
                pass

    return {
        "total_users": total_users,
        "active_today": active_today,
        "active_weekly": active_weekly,
    }
