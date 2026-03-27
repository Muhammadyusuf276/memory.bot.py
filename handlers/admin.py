import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_ID
from database import get_user_stats
from keyboards import back_to_menu_kb

logger = logging.getLogger(__name__)
router = Router()


# ==================== ADMIN BUYRUQLARI ====================

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """/stats — Admin uchun statistika."""
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        await message.answer(
            "❌ Sizda bu buyruqni ishlatish huquqi yo'q.",
            parse_mode="Markdown",
        )
        return

    stats = get_user_stats()
    total = stats["total_users"]
    today = stats["active_today"]
    weekly = stats["active_weekly"]
    pct = round(today / total * 100, 1) if total > 0 else 0

    text = (
        "📊 *Bot Statistikasi*\n\n"
        f"👥 *Jami foydalanuvchilar:* {total}\n"
        f"📱 *Bugun faol:* {today}\n"
        f"📅 *Haftada faol:* {weekly}\n\n"
        f"📈 *Faollik darajasi:* {pct}%"
    )

    await message.answer(text, reply_markup=back_to_menu_kb(), parse_mode="Markdown")
