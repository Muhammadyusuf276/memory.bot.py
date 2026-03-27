from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from locales import get_text


# ==================== UMUMIY KEYBOARD'LAR ====================

def main_menu_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    """Asosiy menyu keyboard'i."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("my_folders", lang), callback_data="my_folders"),
            InlineKeyboardButton(text=get_text("add_folder", lang), callback_data="create_folder"),
        ],
        [
            InlineKeyboardButton(text=get_text("my_contacts", lang), callback_data="my_contacts"),
            InlineKeyboardButton(text=get_text("add_contact", lang), callback_data="add_contact"),
        ],
        [
            InlineKeyboardButton(text=get_text("my_notes", lang), callback_data="my_notes"),
            InlineKeyboardButton(text=get_text("add_note", lang), callback_data="add_note"),
        ],
        [
            InlineKeyboardButton(text=get_text("my_links", lang), callback_data="my_links"),
            InlineKeyboardButton(text=get_text("add_link", lang), callback_data="add_link"),
        ],
        [
            InlineKeyboardButton(text=get_text("my_schedule", lang), callback_data="my_schedule"),
            InlineKeyboardButton(text=get_text("add_schedule", lang), callback_data="add_schedule"),
        ],
        [InlineKeyboardButton(text=get_text("my_statistics", lang), callback_data="my_statistics")],
        [InlineKeyboardButton(text=get_text("upload_file", lang), callback_data="upload_file")],
        [InlineKeyboardButton(text=get_text("help", lang), callback_data="help")],
    ])


def back_to_menu_kb() -> InlineKeyboardMarkup:
    """Bosh menyu tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    """Bekor qilish tugmasi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")],
    ])


def confirm_delete_kb(confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
    """O'chirishni tasdiqlash keyboard'i."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=confirm_data)],
        [InlineKeyboardButton(text="❌ Yo'q, bekor qilish", callback_data=cancel_data)],
    ])


def language_kb() -> InlineKeyboardMarkup:
    """Til tanlash keyboard'i."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kz")],
    ])


def color_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    """Rang tanlash keyboard'i."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("color_red", lang), callback_data="color_🔴"),
            InlineKeyboardButton(text=get_text("color_green", lang), callback_data="color_🟢"),
        ],
        [
            InlineKeyboardButton(text=get_text("color_blue", lang), callback_data="color_🔵"),
            InlineKeyboardButton(text=get_text("color_yellow", lang), callback_data="color_🟡"),
        ],
        [
            InlineKeyboardButton(text=get_text("color_purple", lang), callback_data="color_🟣"),
            InlineKeyboardButton(text=get_text("color_orange", lang), callback_data="color_🟠"),
        ],
        [InlineKeyboardButton(text=get_text("cancel", lang), callback_data="main_menu")],
    ])


def folder_contents_kb(folder_id: str) -> InlineKeyboardMarkup:
    """Papka ichidagi tugmalar."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Fayl yuklash", callback_data=f"upload_to_{folder_id}")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data=f"folder_settings_{folder_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="my_folders")],
    ])


def folder_settings_kb(folder_id: str, is_pinned: bool, lang: str = "uz") -> InlineKeyboardMarkup:
    """Papka sozlamalari keyboard'i."""
    pin_text = get_text("unpin_folder", lang) if is_pinned else get_text("pin_folder", lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Fayl qo'shish", callback_data=f"upload_to_{folder_id}")],
        [InlineKeyboardButton(text=pin_text, callback_data=f"toggle_pin_{folder_id}")],
        [InlineKeyboardButton(text="🔒 Parol qo'yish", callback_data="set_password")],
        [InlineKeyboardButton(text="🗑️ Papkani o'chirish", callback_data="delete_folder")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="my_folders")],
    ])
