import logging
import re
import uuid

from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from database import load_data, save_data, get_user, get_user_lang
from keyboards import back_to_menu_kb, cancel_kb
from locales import get_text
from states import ScheduleStates

logger = logging.getLogger(__name__)
router = Router()


# ==================== KUN TARTIBIM ====================

@router.callback_query(F.data == "my_schedule")
async def my_schedule(callback: CallbackQuery, state: FSMContext):
    """Kun tartibini ko'rsatish."""
    await state.clear()
    await callback.answer()
    user_id = str(callback.from_user.id)
    await _show_schedule_list(callback, user_id)


async def _show_schedule_list(callback: CallbackQuery, user_id: str):
    """Vazifalar ro'yxati."""
    lang = get_user_lang(user_id)
    user_data = get_user(user_id)
    schedules = user_data.get("schedules", {})

    if not schedules:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Vazifa Qo'shish", callback_data="add_schedule")],
            [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            get_text("no_schedules", lang),
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return

    sorted_schedules = sorted(schedules.items(), key=lambda x: x[1].get("time", "00:00"))

    completed = sum(1 for s in schedules.values() if s.get("completed", False))
    missed = sum(1 for s in schedules.values() if s.get("missed", False))
    pending = len(schedules) - completed - missed

    text = get_text("schedule_title", lang) + "\n\n"

    for schedule_id, schedule in sorted_schedules:
        time_str = schedule.get("time", "--:--")
        task = schedule.get("task", "Nomsiz")

        if schedule.get("completed", False):
            status = "✅"
        elif schedule.get("missed", False):
            status = "❌"
        else:
            status = "⏳"

        text += f"{status} `{time_str}` - {task}\n"

    text += f"\n{get_text('schedule_stats', lang).format(completed=completed, missed=missed, pending=pending)}"

    # Bajarilmagan vazifalar uchun tugmalar
    buttons = []
    for schedule_id, schedule in sorted_schedules:
        if not schedule.get("completed", False) and not schedule.get("missed", False):
            task_preview = schedule.get("task", "")[:15]
            buttons.append([
                InlineKeyboardButton(text=f"✅ {task_preview}", callback_data=f"schedule_done_{schedule_id}"),
                InlineKeyboardButton(text=f"❌ {task_preview}", callback_data=f"schedule_missed_{schedule_id}"),
            ])

    buttons.append([InlineKeyboardButton(text="➕ Vazifa Qo'shish", callback_data="add_schedule")])
    buttons.append([InlineKeyboardButton(text="📊 Haftalik Stat", callback_data="weekly_stats")])
    buttons.append([InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


# ==================== VAZIFA QO'SHISH ====================

@router.callback_query(F.data == "add_schedule")
async def add_schedule(callback: CallbackQuery, state: FSMContext):
    """Vazifa qo'shish boshlash."""
    await callback.answer()
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)
    await state.set_state(ScheduleStates.adding_task)

    await callback.message.edit_text(
        get_text("add_schedule_title", lang) + "\n\n" + get_text("add_schedule_desc", lang),
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )


@router.message(ScheduleStates.adding_task)
async def schedule_task_entered(message: Message, state: FSMContext):
    """Vazifa matni kiritildi."""
    task_text = message.text.strip()

    if len(task_text) < 1:
        await message.answer(
            "❌ Vazifa matni bo'sh bo'lishi mumkin emas.",
            reply_markup=back_to_menu_kb(),
        )
        return

    user_id = str(message.from_user.id)
    lang = get_user_lang(user_id)
    await state.update_data(schedule_task=task_text)
    await state.set_state(ScheduleStates.adding_time)

    await message.answer(
        get_text("enter_schedule_time", lang),
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )


@router.message(ScheduleStates.adding_time)
async def schedule_time_entered(message: Message, state: FSMContext):
    """Vazifa vaqti kiritildi — saqlash."""
    time_text = message.text.strip()

    if not re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", time_text):
        await message.answer(
            "❌ Noto'g'ri vaqt formati. Iltimos, quyidagi formatda yuboring:\n"
            "• `09:00`\n• `14:30`\n• `18:45`",
            reply_markup=back_to_menu_kb(),
            parse_mode="Markdown",
        )
        return

    state_data = await state.get_data()
    task_text = state_data.get("schedule_task", "Nomsiz vazifa")
    user_id = str(message.from_user.id)
    lang = get_user_lang(user_id)

    schedule_id = str(uuid.uuid4())[:8]
    db = load_data()
    user = get_user(user_id)
    db[user_id] = user
    if "schedules" not in db[user_id]:
        db[user_id]["schedules"] = {}

    db[user_id]["schedules"][schedule_id] = {
        "task": task_text,
        "time": time_text,
        "completed": False,
        "missed": False,
        "reminded": False,
        "created_at": datetime.now().isoformat(),
    }
    save_data(db)
    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Kun Tartibim", callback_data="my_schedule")],
        [InlineKeyboardButton(text="➕ Yana Vazifa", callback_data="add_schedule")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])

    await message.answer(
        get_text("schedule_added", lang).format(time=time_text, task=task_text),
        reply_markup=kb,
        parse_mode="Markdown",
    )


# ==================== VAZIFA BAJARILDI / BAJARILMADI ====================

@router.callback_query(F.data.startswith("schedule_done_"))
async def schedule_done(callback: CallbackQuery):
    """Vazifani bajarilgan deb belgilash."""
    await callback.answer()
    schedule_id = callback.data.replace("schedule_done_", "")
    user_id = str(callback.from_user.id)
    await _mark_schedule(callback, user_id, schedule_id, completed=True)


@router.callback_query(F.data.startswith("schedule_missed_"))
async def schedule_missed(callback: CallbackQuery):
    """Vazifani bajarilmagan deb belgilash."""
    await callback.answer()
    schedule_id = callback.data.replace("schedule_missed_", "")
    user_id = str(callback.from_user.id)
    await _mark_schedule(callback, user_id, schedule_id, completed=False)


async def _mark_schedule(callback: CallbackQuery, user_id: str, schedule_id: str, completed: bool):
    """Vazifani belgilash va ro'yxatni yangilash."""
    db = load_data()
    schedules = db.get(user_id, {}).get("schedules", {})

    if schedule_id in schedules:
        if completed:
            schedules[schedule_id]["completed"] = True
            schedules[schedule_id]["missed"] = False
        else:
            schedules[schedule_id]["completed"] = False
            schedules[schedule_id]["missed"] = True
        save_data(db)

    await _show_schedule_list(callback, user_id)


# ==================== HAFTALIK STATISTIKA ====================

@router.callback_query(F.data == "weekly_stats")
async def weekly_stats(callback: CallbackQuery):
    """Haftalik statistika."""
    await callback.answer()
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)
    user_data = get_user(user_id)
    schedules = user_data.get("schedules", {})

    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    week_schedules = {}
    for sid, schedule in schedules.items():
        created_at = schedule.get("created_at", "")
        if created_at:
            try:
                schedule_date = datetime.fromisoformat(created_at)
                if week_start <= schedule_date <= week_end + timedelta(days=1):
                    week_schedules[sid] = schedule
            except (ValueError, TypeError):
                pass

    if not week_schedules:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📅 Kun Tartibim", callback_data="my_schedule")],
            [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            get_text("no_weekly_stats", lang),
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return

    completed = sum(1 for s in week_schedules.values() if s.get("completed", False))
    missed = sum(1 for s in week_schedules.values() if s.get("missed", False))
    total = len(week_schedules)
    percentage = round((completed / total) * 100) if total > 0 else 0

    text = get_text("weekly_stats", lang).format(
        week_start=week_start.strftime("%d.%m"),
        week_end=week_end.strftime("%d.%m"),
        completed=completed,
        missed=missed,
        total=total,
        percentage=percentage,
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Kun Tartibim", callback_data="my_schedule")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


# ==================== MENING STATISTIKALARIM ====================

@router.callback_query(F.data == "my_statistics")
async def my_statistics(callback: CallbackQuery):
    """Umumiy statistika."""
    await callback.answer()
    user_id = str(callback.from_user.id)
    lang = get_user_lang(user_id)
    user_data = get_user(user_id)
    schedules = user_data.get("schedules", {})

    if not schedules:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📅 Kun Tartibim", callback_data="my_schedule")],
            [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
        ])
        await callback.message.edit_text(
            "📈 *Mening Statistikalarim*\n\nHali vazifalar yo'q.",
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return

    completed = sum(1 for s in schedules.values() if s.get("completed", False))
    missed = sum(1 for s in schedules.values() if s.get("missed", False))
    total = len(schedules)
    percentage = round((completed / total) * 100) if total > 0 else 0

    if percentage >= 90:
        rating = 10
        rating_text = get_text("rating_excellent", lang)
    elif percentage >= 80:
        rating = 9
        rating_text = get_text("rating_excellent", lang)
    elif percentage >= 70:
        rating = 8
        rating_text = get_text("rating_good", lang)
    elif percentage >= 60:
        rating = 7
        rating_text = get_text("rating_good", lang)
    elif percentage >= 50:
        rating = 6
        rating_text = get_text("rating_average", lang)
    elif percentage >= 40:
        rating = 5
        rating_text = get_text("rating_average", lang)
    elif percentage >= 30:
        rating = 4
        rating_text = get_text("rating_poor", lang)
    else:
        rating = max(1, percentage // 10)
        rating_text = get_text("rating_poor", lang)

    stars = "⭐" * rating + "⚫" * (10 - rating)

    text = get_text("stats_title", lang) + "\n\n"
    text += get_text("stats_overall", lang).format(completed=completed, missed=missed, total=total) + "\n\n"
    text += get_text("stats_rating", lang).format(percentage=percentage, rating=stars, rating_text=rating_text)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Kun Tartibim", callback_data="my_schedule")],
        [InlineKeyboardButton(text="📊 Haftalik Stat", callback_data="weekly_stats")],
        [InlineKeyboardButton(text="🏠 Bosh menu", callback_data="main_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")


# ==================== ESLATMA YUBORISH (Scheduler uchun) ====================

async def check_schedules_and_remind(bot: Bot):
    """Har daqiqa vazifalarni tekshirib eslatma yuborish."""
    current_time = datetime.now().strftime("%H:%M")
    db = load_data()

    for user_id, user_data in db.items():
        if user_id == "stats":
            continue

        schedules = user_data.get("schedules", {})
        changed = False

        for schedule_id, schedule in schedules.items():
            if (
                schedule.get("time") == current_time
                and not schedule.get("completed", False)
                and not schedule.get("missed", False)
                and not schedule.get("reminded", False)
            ):
                try:
                    task = schedule.get("task", "Nomsiz vazifa")
                    lang = user_data.get("language", "uz")

                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Ha, bajardim", callback_data=f"schedule_done_{schedule_id}")],
                        [InlineKeyboardButton(text="❌ Yo'q, bajarmadim", callback_data=f"schedule_missed_{schedule_id}")],
                    ])

                    await bot.send_message(
                        chat_id=int(user_id),
                        text=get_text("schedule_reminder", lang).format(task=task),
                        reply_markup=kb,
                        parse_mode="Markdown",
                    )

                    schedule["reminded"] = True
                    changed = True

                except Exception as e:
                    logger.error("Eslatma yuborishda xatolik (user %s): %s", user_id, e)

        if changed:
            save_data(db)
