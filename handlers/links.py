import logging
import uuid

from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from database import load_data, save_data, get_user, get_user_lang
from keyboards import back_to_menu_kb, cancel_kb
from locales import get_text
from states import LinkStates

logger = logging.getLogger(__name__)
router = Router()


# ==================== LINKLARIM ====================

@router.callback_query(F.data == "my_links")
async def my_links(callback: CallbackQuery, state: FSMContext):
    """Linklar ro'yxati."""
    await state.clear()
    await callback.answer()
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)
    user_data = get_user(user_id)
    links = user_data.get("links", {})

    if not links:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Link Qo'shish", callback_data="add_link")],
            [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            get_text("no_links", lang),
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return

    buttons = []
    for link_id, link_info in links.items():
        preview = link_info["title"][:20] + "..." if len(link_info["title"]) > 20 else link_info["title"]
        buttons.append([InlineKeyboardButton(
            text=f"🔗 {preview}",
            callback_data=f"view_link_{link_id}",
        )])

    buttons.append([InlineKeyboardButton(text="➕ Yangi Link", callback_data="add_link")])
    buttons.append([InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        f"🔗 *Linklarim* ({len(links)} ta)\n\nLinkni ko'rish uchun tanlang:",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# ==================== LINK QO'SHISH ====================

@router.callback_query(F.data == "add_link")
async def add_link(callback: CallbackQuery, state: FSMContext):
    """Link qo'shish boshlash."""
    await callback.answer()
    await state.set_state(LinkStates.adding_url)

    await callback.message.edit_text(
        "➕ *Yangi Link*\n\n"
        "Link URL manzilini kiriting:\n"
        "(Masalan: https://youtube.com/..., https://instagram.com/...)",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )


@router.message(LinkStates.adding_url)
async def link_url_entered(message: Message, state: FSMContext):
    """Link URL kiritildi."""
    url = message.text.strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer(
            "❌ Noto'g'ri URL format. URL http:// yoki https:// bilan boshlanishi kerak.",
            reply_markup=back_to_menu_kb(),
        )
        return

    await state.update_data(link_url=url)
    await state.set_state(LinkStates.adding_title)

    await message.answer(
        "➕ *Yangi Link*\n\n"
        "Link uchun sarlavha kiriting:\n"
        "(Masalan: 'Mening video', 'Instagram post')",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )


@router.message(LinkStates.adding_title)
async def link_title_entered(message: Message, state: FSMContext):
    """Link sarlavhasi kiritildi."""
    title = message.text.strip()
    if len(title) < 1:
        title = "Nomsiz link"

    await state.update_data(link_title=title)
    await state.set_state(LinkStates.adding_description)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ O'tkazib yuborish", callback_data="skip_link_description")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")],
    ])

    await message.answer(
        "➕ *Yangi Link*\n\n"
        "Link uchun qo'shimcha izoh kiriting (ixtiyoriy):\n"
        "Yoki 'O'tkazib yuborish' tugmasini bosing:",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.message(LinkStates.adding_description)
async def link_description_entered(message: Message, state: FSMContext):
    """Link izohi kiritildi — saqlash."""
    description = message.text.strip()
    await _save_link(message, state, description=description)


@router.callback_query(F.data == "skip_link_description")
async def skip_link_description(callback: CallbackQuery, state: FSMContext):
    """Izohni o'tkazib yuborish - saqlash."""
    await callback.answer()
    await _save_link_from_callback(callback, state)


async def _save_link(message: Message, state: FSMContext, description: str = ""):
    """Linkni saqlash (message orqali)."""
    state_data = await state.get_data()
    url = state_data.get("link_url", "")
    title = state_data.get("link_title", "Nomsiz link")
    user_id = str(message.from_user.id)

    link_id = str(uuid.uuid4())[:8]
    db = load_data()
    user = get_user(user_id)
    db[user_id] = user
    if "links" not in db[user_id]:
        db[user_id]["links"] = {}

    db[user_id]["links"][link_id] = {
        "url": url,
        "title": title,
        "description": description,
        "created_at": datetime.now().isoformat(),
    }
    save_data(db)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Linklarim", callback_data="my_links")],
        [InlineKeyboardButton(text="➕ Yana Link", callback_data="add_link")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])

    await message.answer(
        f"✅ *Link saqlandi!*\n\n🔗 *{title}*\n📎 {url[:50]}...",
        reply_markup=kb,
        parse_mode="Markdown",
    )


async def _save_link_from_callback(callback: CallbackQuery, state: FSMContext):
    """Linkni saqlash (callback orqali)."""
    state_data = await state.get_data()
    url = state_data.get("link_url", "")
    title = state_data.get("link_title", "Nomsiz link")
    user_id = str(callback.from_user.id)

    link_id = str(uuid.uuid4())[:8]
    db = load_data()
    user = get_user(user_id)
    db[user_id] = user
    if "links" not in db[user_id]:
        db[user_id]["links"] = {}

    db[user_id]["links"][link_id] = {
        "url": url,
        "title": title,
        "description": "",
        "created_at": datetime.now().isoformat(),
    }
    save_data(db)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Linklarim", callback_data="my_links")],
        [InlineKeyboardButton(text="➕ Yana Link", callback_data="add_link")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])

    await callback.message.edit_text(
        f"✅ *Link saqlandi!*\n\n🔗 *{title}*\n📎 {url[:50]}...",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# ==================== LINK KO'RISH ====================

@router.callback_query(F.data.startswith("view_link_"))
async def view_link(callback: CallbackQuery):
    """Linkni ko'rish."""
    await callback.answer()
    link_id = callback.data.replace("view_link_", "")
    user_id = str(callback.from_user.id)
    user_data = get_user(user_id)
    link = user_data.get("links", {}).get(link_id)

    if not link:
        await callback.message.edit_text("❌ Link topilmadi.", reply_markup=back_to_menu_kb())
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Ochish", url=link["url"])],
        [InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"delete_link_{link_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="my_links")],
    ])

    text = f"🔗 *{link['title']}*\n\n📎 URL: `{link['url']}`\n"
    if link.get("description"):
        text += f"\n📝 {link['description']}"

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


# ==================== LINK O'CHIRISH ====================

@router.callback_query(F.data.startswith("delete_link_"))
async def delete_link(callback: CallbackQuery):
    """Linkni o'chirish — tasdiq."""
    await callback.answer()
    link_id = callback.data.replace("delete_link_", "")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_link_{link_id}")],
        [InlineKeyboardButton(text="❌ Yo'q, bekor qilish", callback_data=f"view_link_{link_id}")],
    ])

    await callback.message.edit_text(
        "🗑️ *Linkni o'chirish*\n\nIshonchingiz komilmi?",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("confirm_delete_link_"))
async def confirm_delete_link(callback: CallbackQuery):
    """Link o'chirish tasdiqlangan."""
    await callback.answer()
    link_id = callback.data.replace("confirm_delete_link_", "")
    user_id = str(callback.from_user.id)

    db = load_data()
    if user_id in db and "links" in db[user_id] and link_id in db[user_id]["links"]:
        del db[user_id]["links"][link_id]
        save_data(db)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Linklarim", callback_data="my_links")],
        ])
        await callback.message.edit_text("✅ *Link o'chirildi!*", reply_markup=kb, parse_mode="Markdown")
    else:
        await callback.message.edit_text("❌ Link topilmadi.", reply_markup=back_to_menu_kb())
