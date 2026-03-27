import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database import get_user, update_user_field, get_user_lang, update_user_activity
from keyboards import main_menu_kb, back_to_menu_kb, language_kb
from locales import get_text

logger = logging.getLogger(__name__)
router = Router()


# ==================== /start KOMANDASI ====================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Botni boshlash — til tanlash yoki bosh menyu."""
    await state.clear()
    user_id = str(message.from_user.id)
    user = get_user(user_id)
    update_user_activity(user_id)

    if user.get("language"):
        lang = user["language"]
        await message.answer(
            get_text("welcome", lang),
            reply_markup=main_menu_kb(lang),
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            "🧠 *MemoryBot*\n\n"
            "🌐 *Tilni tanlang / Выберите язык / Тілді таңдаңыз*\n\n"
            "Iltimos, tilni tanlang:\n"
            "Пожалуйста, выберите язык:\n"
            "Тілді таңдаңыз:",
            reply_markup=language_kb(),
            parse_mode="Markdown",
        )


# ==================== TIL TANLASH ====================

@router.callback_query(F.data.startswith("lang_"))
async def select_language(callback: CallbackQuery, state: FSMContext):
    """Til tanlash callback."""
    await callback.answer()
    lang = callback.data.replace("lang_", "")
    user_id = str(callback.from_user.id)

    update_user_field(user_id, "language", lang)

    await callback.message.edit_text(
        get_text("welcome", lang),
        reply_markup=main_menu_kb(lang),
        parse_mode="Markdown",
    )


# ==================== BOSH MENYU ====================

@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    """Bosh menyuга qaytish."""
    await state.clear()
    await callback.answer()
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)
    update_user_activity(user_id)

    await callback.message.edit_text(
        get_text("welcome", lang),
        reply_markup=main_menu_kb(lang),
        parse_mode="Markdown",
    )


# ==================== YORDAM ====================

@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Yordam ko'rsatish."""
    await callback.answer()
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)

    await callback.message.edit_text(
        get_text("help_text", lang),
        reply_markup=back_to_menu_kb(),
        parse_mode="Markdown",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """/help komandasi."""
    user_id = str(message.from_user.id)
    lang = get_user_lang(user_id)

    text = (
        "📋 *Bot buyruqlari:*\n\n"
        "/start - Bosh menyu\n"
        "/help - Yordam\n\n"
        "🔍 *Qanday foydalanish:*\n"
        "1. 📁 'Yangi Papka Yaratish' tugmasini bosing\n"
        "2. 📝 Papka nomini kiriting\n"
        "3. 🔒 (ixtiyoriy) Parol qo'ying\n"
        "4. 📤 Rasmingiz yoki videongizni yuboring\n"
        "5. ✅ Tayyor!\n\n"
        "🔐 *Xavfsizlik:*\n"
        "• Barcha ma'lumotlar shifrlanadi\n"
        "• Parolni bilmasdan papka ochilmaydi\n"
        "• Faqat siz ko'rishingiz mumkin"
    )

    await message.answer(text, reply_markup=back_to_menu_kb(), parse_mode="Markdown")
