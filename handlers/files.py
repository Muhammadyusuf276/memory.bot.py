import logging
import random

from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from database import load_data, save_data, get_user, get_user_lang
from keyboards import back_to_menu_kb, cancel_kb, folder_contents_kb
from states import FolderStates

logger = logging.getLogger(__name__)
router = Router()


# ==================== FAYL YUKLASH ====================

@router.callback_query(F.data == "upload_file")
async def upload_file_select(callback: CallbackQuery, state: FSMContext):
    """Fayl yuklash — papka tanlash."""
    await callback.answer()
    user_id = str(callback.from_user.id)
    user_data = get_user(user_id)
    folders = user_data.get("folders", {})

    if not folders:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Avval papka yaratish", callback_data="create_folder")],
            [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            "❌ *Avval papka yaratishingiz kerak!*\n\nFayl yuklashdan oldin papka yarating:",
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return

    buttons = []
    for folder_id, folder_info in folders.items():
        buttons.append([InlineKeyboardButton(
            text=f"📂 {folder_info['name']}",
            callback_data=f"upload_to_{folder_id}",
        )])

    buttons.append([InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "📤 *Fayl Yuklash*\n\nQaysi papkaga yuklashni tanlang:",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("upload_to_"))
async def upload_to_folder(callback: CallbackQuery, state: FSMContext):
    """Tanlangan papkaga yuklash boshlash."""
    await callback.answer()
    folder_id = callback.data.replace("upload_to_", "")

    await state.set_state(FolderStates.uploading_file)
    await state.update_data(upload_folder_id=folder_id, upload_count=0)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yuklashni tugatish", callback_data="finish_upload")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="main_menu")],
    ])
    await callback.message.edit_text(
        "📤 *Fayl yuklash*\n\n"
        "Endi rasm yoki video yuboring:\n"
        "(Bir nechta fayl birdaniga yuborishingiz mumkin. Yuklab bo'lgach, pastdagi '✅ Yuklashni tugatish' tugmasini bosing)",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "finish_upload")
async def finish_upload(callback: CallbackQuery, state: FSMContext):
    """Yuklashni tugatish."""
    await callback.answer()
    state_data = await state.get_data()
    folder_id = state_data.get("upload_folder_id")
    upload_count = state_data.get("upload_count", 0)
    user_id = str(callback.from_user.id)

    await state.clear()

    if folder_id:
        db = load_data()
        folder = db.get(user_id, {}).get("folders", {}).get(folder_id)
        if folder:
            total_files = len(folder.get("files", []))

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📤 Yana yuklash", callback_data=f"upload_to_{folder_id}")],
                [InlineKeyboardButton(text="📁 Papkalarim", callback_data="my_folders")],
                [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
            ])

            await callback.message.edit_text(
                f"✅ *Yuklash tugatildi!*\n\n"
                f"📁 Papka: {folder['name']}\n"
                f"📊 Jami fayllar: {total_files} ta\n"
                f"🆕 Yangi yuklandi: {upload_count} ta\n\n"
                f"Xotirangiz xavfsiz saqlandi! 🔐",
                reply_markup=kb,
                parse_mode="Markdown",
            )
            return

    await callback.message.edit_text(
        "✅ *Yuklash tugatildi!*",
        reply_markup=back_to_menu_kb(),
        parse_mode="Markdown",
    )


# ==================== RASM QABUL QILISH ====================

@router.message(FolderStates.uploading_file, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    """Rasm qabul qilish."""
    await _handle_file_upload(message, state, "photo")


@router.message(FolderStates.uploading_file, F.video)
async def handle_video(message: Message, state: FSMContext):
    """Video qabul qilish."""
    await _handle_file_upload(message, state, "video")


async def _handle_file_upload(message: Message, state: FSMContext, file_type: str):
    """Fayl yuklash logikasi."""
    state_data = await state.get_data()
    folder_id = state_data.get("upload_folder_id")
    upload_count = state_data.get("upload_count", 0)
    user_id = str(message.from_user.id)

    if not folder_id:
        await message.answer(
            "❌ Avval papka tanlang!\n\n'📤 Fayl Yuklash' tugmasini bosing.",
            reply_markup=back_to_menu_kb(),
        )
        return

    # Faylni olish
    if file_type == "photo":
        file = message.photo[-1]
        default_name = f"Rasm {datetime.now().strftime('%d.%m.%Y')}"
    else:
        file = message.video
        default_name = f"Video {datetime.now().strftime('%d.%m.%Y')}"

    file_id = file.file_id

    from config import DB_CHANNEL_ID
    channel_msg_id = None
    if DB_CHANNEL_ID:
        try:
            # Faylni kanalga nusxalash
            channel_msg = await message.copy_to(
                chat_id=DB_CHANNEL_ID,
                caption=f"📁 *Fayl yuklandi*\n\nPapka: {folder_id}\nFayl: {file_type}\n👤 #User_{user_id}",
                parse_mode="Markdown"
            )
            channel_msg_id = channel_msg.message_id
        except Exception as e:
            logger.error(f"Faylni DB_CHANNEL ga yuborishda xatolik: {e}")

    # Saqlash
    db = load_data()
    if user_id in db and folder_id in db[user_id].get("folders", {}):
        db[user_id]["folders"][folder_id]["files"].append({
            "name": default_name,
            "date": datetime.now().strftime("%d.%m.%Y"),
            "file_id": file_id,
            "type": file_type,
            "channel_msg_id": channel_msg_id,
            "uploaded_at": datetime.now().isoformat(),
        })
        save_data(db)

        st = await state.get_data()
        cur_count = st.get("upload_count", 0)
        await state.update_data(upload_count=cur_count + 1)
    else:
        await message.answer("❌ Papka topilmadi.", reply_markup=back_to_menu_kb())
