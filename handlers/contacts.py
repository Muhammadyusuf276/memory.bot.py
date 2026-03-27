import logging
import random
import uuid

from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from database import load_data, save_data, get_user, get_user_lang
from keyboards import back_to_menu_kb, cancel_kb
from locales import get_text
from states import ContactStates

logger = logging.getLogger(__name__)
router = Router()


# ==================== KONTAKTLARIM ====================

@router.callback_query(F.data == "my_contacts")
async def my_contacts(callback: CallbackQuery, state: FSMContext):
    """Kontaktlar ro'yxati."""
    await state.clear()
    await callback.answer()
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)
    user_data = get_user(user_id)
    contacts = user_data.get("contacts", {})

    if not contacts:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kontakt Qo'shish", callback_data="add_contact")],
            [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            get_text("no_contacts", lang),
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return

    buttons = []
    for contact_id, contact_info in contacts.items():
        buttons.append([InlineKeyboardButton(
            text=f"👤 {contact_info['name']} • 📱 {contact_info['phone']}",
            callback_data=f"view_contact_{contact_id}",
        )])

    buttons.append([InlineKeyboardButton(text="➕ Yangi Kontakt", callback_data="add_contact")])
    buttons.append([InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        f"📇 *Kontaktlarim* ({len(contacts)} ta)\n\n"
        f"Kontaktni ko'rish uchun tanlang:",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# ==================== KONTAKT QO'SHISH ====================

@router.callback_query(F.data == "add_contact")
async def add_contact(callback: CallbackQuery, state: FSMContext):
    """Kontakt qo'shish boshlash."""
    await callback.answer()
    await state.set_state(ContactStates.adding_phone)

    await callback.message.edit_text(
        "➕ *Yangi Kontakt*\n\n"
        "Telefon raqamini kiriting:\n"
        "(Masalan: +998901234567)",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )


@router.message(ContactStates.adding_phone)
async def contact_phone_entered(message: Message, state: FSMContext):
    """Telefon raqami kiritildi."""
    phone = message.text.strip()

    if len(phone) < 7:
        await message.answer(
            "❌ Telefon raqami noto'g'ri. Kamida 7 ta raqam kiriting.",
            reply_markup=back_to_menu_kb(),
        )
        return

    await state.update_data(contact_phone=phone)
    await state.set_state(ContactStates.adding_name)

    await message.answer(
        f"✅ *Telefon:* {phone}\n\n"
        f"Endi kontaktga ism bering:\n"
        f"(Masalan: 'Ali', 'Dadam', 'Do'stim')",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )


@router.message(ContactStates.adding_name)
async def contact_name_entered(message: Message, state: FSMContext):
    """Kontakt ismi kiritildi."""
    contact_name = message.text.strip()

    if len(contact_name) < 2:
        await message.answer(
            "❌ Ism juda qisqa. Kamida 2 ta belgi kiriting.",
            reply_markup=back_to_menu_kb(),
        )
        return

    await state.update_data(contact_name=contact_name)
    await state.set_state(ContactStates.adding_note)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ O'tkazib yuborish", callback_data="skip_contact_note")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")],
    ])

    await message.answer(
        f"✅ *Ism:* {contact_name}\n\n"
        f"Izoh qo'shishni xohlaysizmi? (ixtiyoriy)\n"
        f"(Masalan: 'Ishonchi', 'Qarindosh', 'Do'st')",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.message(ContactStates.adding_note)
async def contact_note_entered(message: Message, state: FSMContext):
    """Kontakt izohi kiritildi — saqlash."""
    note = message.text.strip()
    await _save_contact(message, state, note=note)


@router.callback_query(F.data == "skip_contact_note")
async def skip_contact_note(callback: CallbackQuery, state: FSMContext):
    """Izohni o'tkazib yuborish."""
    await callback.answer()
    await _save_contact_from_callback(callback, state)


async def _save_contact(message: Message, state: FSMContext, note: str = ""):
    """Kontaktni saqlash (message orqali)."""
    state_data = await state.get_data()
    contact_name = state_data.get("contact_name")
    contact_phone = state_data.get("contact_phone")
    user_id = str(message.from_user.id)

    if not all([contact_name, contact_phone]):
        await message.answer("❌ Xatolik yuz berdi.", reply_markup=back_to_menu_kb())
        await state.clear()
        return

    contact_id = f"contact_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

    db = load_data()
    user = get_user(user_id)
    db[user_id] = user
    if "contacts" not in db[user_id]:
        db[user_id]["contacts"] = {}

    db[user_id]["contacts"][contact_id] = {
        "name": contact_name,
        "phone": contact_phone,
        "note": note,
        "created_at": datetime.now().isoformat(),
    }
    save_data(db)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yana kontakt qo'shish", callback_data="add_contact")],
        [InlineKeyboardButton(text="📇 Kontaktlarim", callback_data="my_contacts")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])

    text = f"✅ *Kontakt saqlandi!*\n\n👤 Ism: {contact_name}\n📱 Telefon: {contact_phone}\n"
    if note:
        text += f"📝 Izoh: {note}\n"

    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


async def _save_contact_from_callback(callback: CallbackQuery, state: FSMContext):
    """Kontaktni saqlash (callback orqali — izohsiz)."""
    state_data = await state.get_data()
    contact_name = state_data.get("contact_name")
    contact_phone = state_data.get("contact_phone")
    user_id = str(callback.from_user.id)

    if not all([contact_name, contact_phone]):
        await callback.message.edit_text("❌ Xatolik yuz berdi.", reply_markup=back_to_menu_kb())
        await state.clear()
        return

    contact_id = f"contact_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

    db = load_data()
    user = get_user(user_id)
    db[user_id] = user
    if "contacts" not in db[user_id]:
        db[user_id]["contacts"] = {}

    db[user_id]["contacts"][contact_id] = {
        "name": contact_name,
        "phone": contact_phone,
        "note": "",
        "created_at": datetime.now().isoformat(),
    }
    save_data(db)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yana kontakt qo'shish", callback_data="add_contact")],
        [InlineKeyboardButton(text="📇 Kontaktlarim", callback_data="my_contacts")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])

    await callback.message.edit_text(
        f"✅ *Kontakt saqlandi!*\n\n"
        f"👤 Ism: {contact_name}\n"
        f"📱 Telefon: {contact_phone}\n\n"
        f"Xotirangiz xavfsiz saqlandi! 🔐",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# ==================== KONTAKT KO'RISH ====================

@router.callback_query(F.data.startswith("view_contact_"))
async def view_contact(callback: CallbackQuery):
    """Kontaktni ko'rish."""
    await callback.answer()
    contact_id = callback.data.replace("view_contact_", "")
    user_id = str(callback.from_user.id)
    user_data = get_user(user_id)
    contact = user_data.get("contacts", {}).get(contact_id)

    if not contact:
        await callback.message.edit_text("❌ Kontakt topilmadi.", reply_markup=back_to_menu_kb())
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"delete_contact_{contact_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="my_contacts")],
    ])

    text = f"👤 *{contact['name']}*\n\n📱 Telefon: {contact['phone']}\n"
    if contact.get("note"):
        text += f"📝 Izoh: {contact['note']}"

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


# ==================== KONTAKT O'CHIRISH ====================

@router.callback_query(F.data.startswith("delete_contact_"))
async def delete_contact(callback: CallbackQuery):
    """Kontaktni o'chirish — tasdiq so'rash."""
    await callback.answer()
    contact_id = callback.data.replace("delete_contact_", "")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_contact_{contact_id}")],
        [InlineKeyboardButton(text="❌ Yo'q, bekor qilish", callback_data=f"view_contact_{contact_id}")],
    ])

    await callback.message.edit_text(
        "🗑️ *Kontaktni o'chirish*\n\nIshonchingiz komilmi?",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("confirm_delete_contact_"))
async def confirm_delete_contact(callback: CallbackQuery):
    """Kontaktni o'chirish tasdiqlangan."""
    await callback.answer()
    contact_id = callback.data.replace("confirm_delete_contact_", "")
    user_id = str(callback.from_user.id)

    db = load_data()
    if user_id in db and "contacts" in db[user_id] and contact_id in db[user_id]["contacts"]:
        del db[user_id]["contacts"][contact_id]
        save_data(db)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📇 Kontaktlarim", callback_data="my_contacts")],
        ])
        await callback.message.edit_text("✅ *Kontakt o'chirildi!*", reply_markup=kb, parse_mode="Markdown")
    else:
        await callback.message.edit_text("❌ Kontakt topilmadi.", reply_markup=back_to_menu_kb())
