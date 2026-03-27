import logging
import random

from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from database import load_data, save_data, get_user, get_user_lang, update_user_activity
from keyboards import (
    back_to_menu_kb, cancel_kb, confirm_delete_kb,
    color_kb, folder_contents_kb, folder_settings_kb,
)
from locales import get_text
from states import FolderStates
from utils import hash_password, verify_password

logger = logging.getLogger(__name__)
router = Router()


# ==================== PAPKALARIM ====================

@router.callback_query(F.data == "my_folders")
async def my_folders(callback: CallbackQuery, state: FSMContext):
    """Papkalar ro'yxatini ko'rsatish."""
    await state.clear()
    await callback.answer()
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)
    user_data = get_user(user_id)
    folders = user_data.get("folders", {})

    if not folders:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Yangi Papka Yaratish", callback_data="create_folder")],
            [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            get_text("no_folders", lang),
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return

    # Papkalarni pin bo'yicha saralash
    sorted_folders = sorted(
        folders.items(),
        key=lambda x: (not x[1].get("pinned", False), x[1].get("name", "")),
    )

    buttons = []
    for folder_id, folder_info in sorted_folders:
        lock_icon = "🔒" if folder_info.get("password") else "📂"
        file_count = len(folder_info.get("files", []))
        color = folder_info.get("color", "📂")
        pin_icon = "📌 " if folder_info.get("pinned", False) else ""
        buttons.append([InlineKeyboardButton(
            text=f"{pin_icon}{color} {folder_info['name']} ({file_count} ta)",
            callback_data=f"open_folder_{folder_id}",
        )])

    buttons.append([InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "📁 *Mening Papkalarim*\n\n"
        "Papkani ochish uchun uni tanlang:\n"
        "📌 = Prikreplennye",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# ==================== PAPKA YARATISH ====================

@router.callback_query(F.data == "create_folder")
async def create_folder(callback: CallbackQuery, state: FSMContext):
    """Papka yaratish boshlash."""
    await callback.answer()
    await state.set_state(FolderStates.creating_folder)

    await callback.message.edit_text(
        "➕ *Yangi Papka Yaratish*\n\n"
        "Papka nomini kiriting:\n"
        "(Masalan: 'Mening rasmlarim', '2024-yil', 'Oilaviy')",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )


@router.message(FolderStates.creating_folder)
async def folder_name_entered(message: Message, state: FSMContext):
    """Papka nomi kiritildi — rang tanlash."""
    folder_name = message.text.strip()

    if len(folder_name) < 2:
        await message.answer(
            "❌ Papka nomi juda qisqa. Kamida 2 ta belgi kiriting.",
            reply_markup=back_to_menu_kb(),
        )
        return

    user_id = str(message.from_user.id)
    lang = get_user_lang(user_id)
    await state.update_data(folder_name=folder_name)
    await state.set_state(FolderStates.selecting_color)

    await message.answer(
        get_text("select_color", lang),
        reply_markup=color_kb(lang),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("color_"), FolderStates.selecting_color)
async def color_selected(callback: CallbackQuery, state: FSMContext):
    """Rang tanlangandan keyin papka yaratish."""
    await callback.answer()
    color = callback.data.replace("color_", "")
    state_data = await state.get_data()
    folder_name = state_data.get("folder_name", "Yangi Papka")
    user_id = str(callback.from_user.id)

    folder_id = f"folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"

    db = load_data()
    user = get_user(user_id)
    db[user_id] = user
    db[user_id]["folders"][folder_id] = {
        "name": folder_name,
        "color": color,
        "pinned": False,
        "created_at": datetime.now().isoformat(),
        "files": [],
        "password": None,
    }
    save_data(db)

    await state.update_data(folder_id=folder_id)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Fayl yuklash", callback_data=f"upload_to_{folder_id}")],
        [InlineKeyboardButton(text="🔒 Parol qo'yish", callback_data="set_password")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])

    await callback.message.edit_text(
        f"✅ *Papka yaratildi!*\n\n"
        f"{color} *{folder_name}*\n\n"
        f"Endi fayl yuklash yoki parol qo'yishingiz mumkin:",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# FSMsiz rang tanlash (papka yaratilgandan keyin rang tanlash)
@router.callback_query(F.data.startswith("color_"))
async def color_selected_no_state(callback: CallbackQuery, state: FSMContext):
    """Rang tanlash (FSM state'siz - boshqa holatlardan)."""
    await callback.answer()
    color = callback.data.replace("color_", "")
    state_data = await state.get_data()
    folder_name = state_data.get("folder_name", "Yangi Papka")
    user_id = str(callback.from_user.id)

    folder_id = f"folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"

    db = load_data()
    user = get_user(user_id)
    db[user_id] = user
    db[user_id]["folders"][folder_id] = {
        "name": folder_name,
        "color": color,
        "pinned": False,
        "created_at": datetime.now().isoformat(),
        "files": [],
        "password": None,
    }
    save_data(db)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Fayl yuklash", callback_data=f"upload_to_{folder_id}")],
        [InlineKeyboardButton(text="🔒 Parol qo'yish", callback_data="set_password")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])

    await callback.message.edit_text(
        f"✅ *Papka yaratildi!*\n\n"
        f"{color} *{folder_name}*\n\n"
        f"Endi fayl yuklash yoki parol qo'yishingiz mumkin:",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# ==================== PAPKA OCHISH ====================

@router.callback_query(F.data.startswith("open_folder_"))
async def open_folder(callback: CallbackQuery, state: FSMContext):
    """Papkani ochish."""
    await callback.answer()
    folder_id = callback.data.replace("open_folder_", "")
    user_id = str(callback.from_user.id)
    user_data = get_user(user_id)
    folder = user_data.get("folders", {}).get(folder_id)

    if not folder:
        await callback.message.edit_text(
            "❌ Papka topilmadi.",
            reply_markup=back_to_menu_kb(),
        )
        return

    # Parol tekshirish
    if folder.get("password"):
        await state.set_state(FolderStates.entering_password)
        await state.update_data(folder_id=folder_id)

        await callback.message.edit_text(
            f"🔒 *Papka himoyalangan*\n\n"
            f"Papka: *{folder['name']}*\n\n"
            f"Parolni kiriting:",
            reply_markup=cancel_kb(),
            parse_mode="Markdown",
        )
        return

    # Parolsiz ochish
    await show_folder_contents(callback, folder_id, folder)


async def show_folder_contents(callback: CallbackQuery, folder_id: str, folder: dict):
    """Papka ichini ko'rsatish va fayllarni yuborish."""
    files = folder.get("files", [])
    kb = folder_contents_kb(folder_id)

    if not files:
        await callback.message.edit_text(
            f"📁 *{folder['name']}*\n\n"
            f"📝 Yaratilgan: {folder.get('created_at', 'Nomalum')[:10]}\n"
            f"📂 Fayllar: 0 ta\n\n"
            f"Bu papka bo'sh. Fayl yuklash uchun tugmani bosing:",
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return

    await callback.message.edit_text(
        f"📁 *{folder['name']}*\n\n"
        f"📝 Yaratilgan: {folder.get('created_at', 'Nomalum')[:10]}\n"
        f"📂 Jami fayllar: {len(files)} ta\n\n"
        f"Fayllar yuborilmoqda...",
        reply_markup=kb,
        parse_mode="Markdown",
    )

    # Fayllarni yuborish
    sent_count = 0
    failed_count = 0

    for file_info in files:
        file_id = file_info.get("file_id")
        caption = f"📎 *{file_info['name']}*\n📅 {file_info.get('uploaded_at', file_info.get('date', ''))[:10]}"

        try:
            if file_id:
                if file_info.get("type") == "photo":
                    await callback.message.answer_photo(
                        photo=file_id, caption=caption, parse_mode="Markdown",
                    )
                else:
                    await callback.message.answer_video(
                        video=file_id, caption=caption, parse_mode="Markdown",
                    )
                sent_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
            logger.error("Fayl yuborishda xatolik: %s", e)

    if failed_count > 0:
        status_text = (
            f"✅ *Fayllar yuborildi!*\n\n"
            f"📁 {folder['name']}\n"
            f"✅ Yuborildi: {sent_count} ta\n"
            f"❌ Topilmadi: {failed_count} ta"
        )
    else:
        status_text = f"✅ *Barcha fayllar yuborildi!*\n\n📁 {folder['name']} - {sent_count} ta fayl"

    await callback.message.answer(status_text, reply_markup=kb, parse_mode="Markdown")


# ==================== PAROL KIRITISH ====================

@router.message(FolderStates.entering_password)
async def enter_password(message: Message, state: FSMContext):
    """Papka parolini kiritish."""
    password = message.text.strip()
    state_data = await state.get_data()
    folder_id = state_data.get("folder_id")
    user_id = str(message.from_user.id)

    if not folder_id:
        await message.answer("❌ Xatolik yuz berdi.", reply_markup=back_to_menu_kb())
        await state.clear()
        return

    db = load_data()
    folder = db.get(user_id, {}).get("folders", {}).get(folder_id)

    if not folder:
        await message.answer("❌ Papka topilmadi.", reply_markup=back_to_menu_kb())
        await state.clear()
        return

    if verify_password(password, folder.get("password", "")):
        await state.clear()
        await message.answer("✅ *Parol to'g'ri!*\nPapka ochilmoqda...", parse_mode="Markdown")

        # Fayllarni yuborish
        files = folder.get("files", [])
        kb = folder_contents_kb(folder_id)

        if not files:
            await message.answer(
                f"📁 *{folder['name']}*\n\nBu papka bo'sh.",
                reply_markup=kb,
                parse_mode="Markdown",
            )
            return

        sent_count = 0
        for file_info in files:
            file_id = file_info.get("file_id")
            caption = f"📎 *{file_info['name']}*\n📅 {file_info.get('uploaded_at', file_info.get('date', ''))[:10]}"
            try:
                if file_id:
                    if file_info.get("type") == "photo":
                        await message.answer_photo(photo=file_id, caption=caption, parse_mode="Markdown")
                    else:
                        await message.answer_video(video=file_id, caption=caption, parse_mode="Markdown")
                    sent_count += 1
            except Exception as e:
                logger.error("Fayl yuborishda xatolik: %s", e)

        await message.answer(
            f"✅ *{folder['name']}* — {sent_count} ta fayl yuborildi!",
            reply_markup=kb,
            parse_mode="Markdown",
        )
    else:
        await message.answer(
            "❌ *Noto'g'ri parol!*\n\nQayta urinib ko'ring:",
            reply_markup=back_to_menu_kb(),
            parse_mode="Markdown",
        )


# ==================== PAPKA SOZLAMALARI ====================

@router.callback_query(F.data.startswith("folder_settings_"))
async def folder_settings(callback: CallbackQuery, state: FSMContext):
    """Papka sozlamalari."""
    await callback.answer()
    folder_id = callback.data.replace("folder_settings_", "")
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)

    await state.update_data(folder_id=folder_id)

    user_data = get_user(user_id)
    folder = user_data.get("folders", {}).get(folder_id, {})
    is_pinned = folder.get("pinned", False)

    await callback.message.edit_text(
        "⚙️ *Papka Sozlamalari*\n\nNima qilishni xohlaysiz?",
        reply_markup=folder_settings_kb(folder_id, is_pinned, lang),
        parse_mode="Markdown",
    )


# ==================== PIN / UNPIN ====================

@router.callback_query(F.data.startswith("toggle_pin_"))
async def toggle_pin(callback: CallbackQuery, state: FSMContext):
    """Papkani pin/unpin qilish."""
    await callback.answer()
    folder_id = callback.data.replace("toggle_pin_", "")
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)

    db = load_data()
    if user_id in db and folder_id in db[user_id]["folders"]:
        current_pin = db[user_id]["folders"][folder_id].get("pinned", False)
        db[user_id]["folders"][folder_id]["pinned"] = not current_pin
        save_data(db)

        is_pinned = not current_pin
        status = "📌 Prikrepleno!" if is_pinned else "📌 Otkrepleno!"

        await callback.message.edit_text(
            f"✅ {status}\n\n⚙️ *Papka Sozlamalari*\n\nNima qilishni xohlaysiz?",
            reply_markup=folder_settings_kb(folder_id, is_pinned, lang),
            parse_mode="Markdown",
        )


# ==================== PAROL QO'YISH ====================

@router.callback_query(F.data == "set_password")
async def set_password(callback: CallbackQuery, state: FSMContext):
    """Papkaga parol qo'yish."""
    await callback.answer()
    await state.set_state(FolderStates.setting_password)

    await callback.message.edit_text(
        "🔒 *Parol qo'yish*\n\n"
        "Yangi parolni kiriting:\n"
        "(Kamida 4 ta belgi)",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )


@router.message(FolderStates.setting_password)
async def password_entered(message: Message, state: FSMContext):
    """Parolni saqlash."""
    password = message.text.strip()
    state_data = await state.get_data()
    folder_id = state_data.get("folder_id")
    user_id = str(message.from_user.id)

    if len(password) < 4:
        await message.answer(
            "❌ Parol juda qisqa. Kamida 4 ta belgi kiriting.",
            reply_markup=back_to_menu_kb(),
        )
        return

    db = load_data()
    if user_id in db and folder_id and folder_id in db[user_id].get("folders", {}):
        db[user_id]["folders"][folder_id]["password"] = hash_password(password)
        save_data(db)
        await state.clear()

        await message.answer(
            "🔒 *Parol qo'yildi!*\n\nEndi bu papka himoyalangan.",
            reply_markup=back_to_menu_kb(),
            parse_mode="Markdown",
        )
    else:
        await message.answer("❌ Xatolik yuz berdi.", reply_markup=back_to_menu_kb())
        await state.clear()


# ==================== PAPKA O'CHIRISH ====================

@router.callback_query(F.data == "delete_folder")
async def delete_folder(callback: CallbackQuery, state: FSMContext):
    """Papkani o'chirish — tasdiq so'rash."""
    await callback.answer()
    state_data = await state.get_data()
    folder_id = state_data.get("folder_id")

    if not folder_id:
        await callback.message.edit_text("❌ Xatolik yuz berdi.", reply_markup=back_to_menu_kb())
        return

    await callback.message.edit_text(
        "🗑️ *Papkani o'chirish*\n\n"
        "Ishonchingiz komilmi?\n"
        "Barcha fayllar o'chib ketadi!",
        reply_markup=confirm_delete_kb(f"confirm_delete_{folder_id}", "my_folders"),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("confirm_delete_folder_"))
async def confirm_delete_folder(callback: CallbackQuery, state: FSMContext):
    """Papka o'chirish tasdiqlangan."""
    await callback.answer()
    folder_id = callback.data.replace("confirm_delete_folder_", "")
    user_id = str(callback.from_user.id)

    db = load_data()
    if user_id in db and folder_id in db[user_id].get("folders", {}):
        del db[user_id]["folders"][folder_id]
        save_data(db)

        await callback.message.edit_text(
            "✅ *Papka o'chirildi!*",
            reply_markup=back_to_menu_kb(),
            parse_mode="Markdown",
        )
    else:
        await callback.message.edit_text("❌ Papka topilmadi.", reply_markup=back_to_menu_kb())


# confirm_delete_ prefixi bilan eski papka o'chirish
@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_generic(callback: CallbackQuery, state: FSMContext):
    """Umumiy o'chirish tasdiqlash (papka uchun fallback)."""
    await callback.answer()
    item_id = callback.data.replace("confirm_delete_", "")
    user_id = str(callback.from_user.id)

    # Papkalar ichidan qidirish
    db = load_data()
    if user_id in db and item_id in db[user_id].get("folders", {}):
        del db[user_id]["folders"][item_id]
        save_data(db)

        await callback.message.edit_text(
            "✅ *Papka o'chirildi!*",
            reply_markup=back_to_menu_kb(),
            parse_mode="Markdown",
        )
    else:
        await callback.message.edit_text("❌ Topilmadi.", reply_markup=back_to_menu_kb())
