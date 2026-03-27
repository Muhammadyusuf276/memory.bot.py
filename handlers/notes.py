import logging
import uuid

from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from database import load_data, save_data, get_user, get_user_lang
from keyboards import back_to_menu_kb, cancel_kb
from locales import get_text
from states import NoteStates

logger = logging.getLogger(__name__)
router = Router()


# ==================== ESLATMALARIM ====================

@router.callback_query(F.data == "my_notes")
async def my_notes(callback: CallbackQuery, state: FSMContext):
    """Eslatmalar ro'yxati."""
    await state.clear()
    await callback.answer()
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)
    user_data = get_user(user_id)
    notes = user_data.get("notes", {})

    if not notes:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Eslatma Qo'shish", callback_data="add_note")],
            [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            get_text("no_notes", lang),
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return

    buttons = []
    for note_id, note_info in notes.items():
        preview = note_info["title"][:15] + "..." if len(note_info["title"]) > 15 else note_info["title"]
        created = note_info.get("created_at", "")[:10]
        buttons.append([InlineKeyboardButton(
            text=f"📝 {preview} • {created}",
            callback_data=f"view_note_{note_id}",
        )])

    buttons.append([InlineKeyboardButton(text="➕ Yangi Eslatma", callback_data="add_note")])
    buttons.append([InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        f"📝 *Eslatmalarim* ({len(notes)} ta)\n\nEslatmani ko'rish uchun tanlang:",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# ==================== ESLATMA QO'SHISH ====================

@router.callback_query(F.data == "add_note")
async def add_note(callback: CallbackQuery, state: FSMContext):
    """Eslatma qo'shish boshlash."""
    await callback.answer()
    await state.set_state(NoteStates.adding_title)

    await callback.message.edit_text(
        "➕ *Yangi Eslatma*\n\n"
        "Eslatma sarlavhasini kiriting:\n"
        "(Masalan: 'Bank karta PIN', 'Wi-Fi parol', 'Muhim sanalar')",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )


@router.message(NoteStates.adding_title)
async def note_title_entered(message: Message, state: FSMContext):
    """Eslatma sarlavhasi kiritildi."""
    title = message.text.strip()

    if len(title) < 2:
        await message.answer(
            "❌ Sarlavha juda qisqa. Kamida 2 ta belgi kiriting.",
            reply_markup=back_to_menu_kb(),
        )
        return

    await state.update_data(note_title=title)
    await state.set_state(NoteStates.adding_content)

    await message.answer(
        f"✅ *Sarlavha:* {title}\n\n"
        f"Endi eslatma matnini kiriting:\n"
        f"(Masalan: PIN kod, parol, muhim ma'lumotlar)",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )


@router.message(NoteStates.adding_content)
async def note_content_entered(message: Message, state: FSMContext):
    """Eslatma matni kiritildi — saqlash."""
    content = message.text.strip()

    if len(content) < 1:
        await message.answer(
            "❌ Eslatma matni bo'sh bo'lishi mumkin emas.",
            reply_markup=back_to_menu_kb(),
        )
        return

    state_data = await state.get_data()
    title = state_data.get("note_title", "Nomsiz")
    user_id = str(message.from_user.id)

    note_id = str(uuid.uuid4())[:8]
    db = load_data()
    user = get_user(user_id)
    db[user_id] = user
    if "notes" not in db[user_id]:
        db[user_id]["notes"] = {}

    db[user_id]["notes"][note_id] = {
        "title": title,
        "content": content,
        "created_at": datetime.now().isoformat(),
    }
    save_data(db)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Eslatmalarim", callback_data="my_notes")],
        [InlineKeyboardButton(text="➕ Yana Eslatma", callback_data="add_note")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])

    await message.answer(
        f"✅ *Eslatma saqlandi!*\n\n"
        f"📝 *{title}*\n"
        f"📅 {datetime.now().strftime('%Y-%m-%d')}",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# ==================== ESLATMA KO'RISH ====================

@router.callback_query(F.data.startswith("view_note_"))
async def view_note(callback: CallbackQuery):
    """Eslatmani ko'rish."""
    await callback.answer()
    note_id = callback.data.replace("view_note_", "")
    user_id = str(callback.from_user.id)
    user_data = get_user(user_id)
    note = user_data.get("notes", {}).get(note_id)

    if not note:
        await callback.message.edit_text("❌ Eslatma topilmadi.", reply_markup=back_to_menu_kb())
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"delete_note_{note_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="my_notes")],
    ])

    await callback.message.edit_text(
        f"📝 *{note['title']}*\n\n"
        f"{note['content']}\n\n"
        f"📅 Yaratilgan: {note.get('created_at', 'Nomalum')[:10]}",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# ==================== ESLATMA O'CHIRISH ====================

@router.callback_query(F.data.startswith("delete_note_"))
async def delete_note(callback: CallbackQuery):
    """Eslatmani o'chirish — tasdiq."""
    await callback.answer()
    note_id = callback.data.replace("delete_note_", "")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_note_{note_id}")],
        [InlineKeyboardButton(text="❌ Yo'q, bekor qilish", callback_data=f"view_note_{note_id}")],
    ])

    await callback.message.edit_text(
        "🗑️ *Eslatmani o'chirish*\n\nIshonchingiz komilmi?",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("confirm_delete_note_"))
async def confirm_delete_note(callback: CallbackQuery):
    """Eslatma o'chirish tasdiqlangan."""
    await callback.answer()
    note_id = callback.data.replace("confirm_delete_note_", "")
    user_id = str(callback.from_user.id)

    db = load_data()
    if user_id in db and "notes" in db[user_id] and note_id in db[user_id]["notes"]:
        del db[user_id]["notes"][note_id]
        save_data(db)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Eslatmalarim", callback_data="my_notes")],
        ])
        await callback.message.edit_text("✅ *Eslatma o'chirildi!*", reply_markup=kb, parse_mode="Markdown")
    else:
        await callback.message.edit_text("❌ Eslatma topilmadi.", reply_markup=back_to_menu_kb())
