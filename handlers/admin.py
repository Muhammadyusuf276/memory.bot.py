import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, ADMIN_USERNAME
from database import get_user_stats, load_data
from states import AdminStates

logger = logging.getLogger(__name__)
router = Router()

def is_admin(user) -> bool:
    if user.id == ADMIN_ID:
        return True
    username = user.username.replace("@", "") if user.username else ""
    if ADMIN_USERNAME and username.lower() == ADMIN_USERNAME.lower():
        return True
    return False

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Barchaga Xabar", callback_data="admin_broadcast")],
    ])

# ==================== ADMIN BUYRUQLARI ====================

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """/admin — Admin panel."""
    if not is_admin(message.from_user):
        await message.answer("❌ Sizda bu buyruqni ishlatish huquqi yo'q.", parse_mode="Markdown")
        return
    await state.clear()
    await message.answer("👮‍♂️ *Admin Panel*\n\nKerakli bo'limni tanlang:", reply_markup=admin_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    await callback.answer()
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
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_back")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data == "admin_back")
async def cb_admin_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user):
        return
    await state.clear()
    await callback.message.edit_text("👮‍♂️ *Admin Panel*\n\nKerakli bo'limni tanlang:", reply_markup=admin_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user):
        return
    await callback.answer()
    await state.set_state(AdminStates.waiting_for_broadcast)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_back")]])
    await callback.message.edit_text("📢 *Xabar yuborish*\n\nBarcha foydalanuvchilarga yuboriladigan xabarni kiriting (rasm/video ham mumkin):", reply_markup=kb, parse_mode="Markdown")

@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user):
        return
    db = load_data()
    users = [uid for uid in db.keys() if uid != "stats"]
    sent, failed = 0, 0
    await message.answer("⏳ Xabarlar yuborilmoqda, kuting...")
    for uid in users:
        if uid == str(message.from_user.id): continue # Don't send to admin himself
        try:
            await message.send_copy(chat_id=uid)
            sent += 1
        except Exception:
            failed += 1
    
    await state.clear()
    text = f"✅ *Xabar yuborildi!*\n\n🟢 Yetib bordi: {sent} ta\n🔴 Yetib bormadi (bloklaganlar): {failed} ta"
    await message.answer(text, reply_markup=admin_kb(), parse_mode="Markdown")
