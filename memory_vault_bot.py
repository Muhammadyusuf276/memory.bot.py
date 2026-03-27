import os
import json
import hashlib
import random
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# Ma'lumotlar fayllari
DATA_FILE = "memory_vault_data.json"
STORAGE_DIR = "memory_vault_storage"

# Admin ID (o'zingizning Telegram ID'ingiz)
ADMIN_ID = "YOUR_ADMIN_ID"  # Bu yerga o'zingizning Telegram ID'ingizni yozing
ADMIN_ID = "8330169236"  # Bu yerga o'zingizning Telegram ID'ingizni yozing

# Replicate API token (rasm tiniqlashtirish uchun)
REPLICATE_API_TOKEN = "YOUR_REPLICATE_API_TOKEN"  # replicate.com dan oling

# Saqlash papkasini yaratish
os.makedirs(STORAGE_DIR, exist_ok=True)

# ==================== STATISTIKA FUNKSIYALARI ====================

def get_user_stats():
    """Foydalanuvchilar statistikasini olish"""
    data = load_data()
    total_users = len(data)
    
    # Faol foydalanuvchilar (oxirgi 7 kun ichida aktiv)
    active_users = 0
    weekly_active = 0
    
    for user_id, user_data in data.items():
        if user_id == "stats":  # Statistika ma'lumotlarini o'tkazib yuborish
            continue
            
        last_activity = user_data.get("last_activity")
        if last_activity:
            try:
                last_seen = datetime.fromisoformat(last_activity)
                days_diff = (datetime.now() - last_seen).days
                
                if days_diff <= 1:  # 1 kun ichida faol
                    active_users += 1
                if days_diff <= 7:  # 7 kun ichida faol
                    weekly_active += 1
            except:
                pass
    
    return {
        "total_users": total_users,
        "active_today": active_users,
        "active_weekly": weekly_active
    }

def update_user_activity(user_id):
    """Foydalanuvchi aktivligini yangilash"""
    data = load_data()
    if user_id in data:
        data[user_id]["last_activity"] = datetime.now().isoformat()
        save_data(data)

# ==================== TIL SOZLAMALARI ====================

TRANSLATIONS = {
    "uz": {
        "welcome": "🔐 *Xotira Vault* - Shaxsiy Xotira Saqlash\n\n📸 Rasmlar, videolar, kontaktlar va eslatmalaringizni xavfsiz saqlang!\n\n✨ *Imkoniyatlar:*\n• 📁 Cheksiz papka yaratish\n• 📇 Cheksiz kontakt saqlash\n• 📝 Cheksiz eslatma yozish\n• 🔒 Parol bilan himoyalash\n• 📸 Rasm va video saqlash\n• 🗑️ Papka o'chirish\n\n*Xotirangizni biz bilan xavfsiz saqlang!*",
        "select_language": "🌐 *Tilni tanlang*\n\nIltimos, tilni tanlang:",
        "my_folders": "📁 Mening Papkalarim",
        "my_contacts": "📇 Kontaktlarim",
        "my_notes": "📝 Eslatmalarim",
        "my_links": "🔗 Linklarim",
        "add_folder": "➕ Yangi Papka",
        "add_contact": "➕ Kontakt",
        "add_note": "➕ Eslatma",
        "add_link": "➕ Link",
        "my_schedule": "📅 Kun Tartibim",
        "add_schedule": "➕ Vazifa",
        "upload_file": "📤 Fayl Yuklash",
        "help": "❓ Yordam",
        "schedule_title": "📅 *Kun Tartibim*",
        "schedule_desc": "Bugungi rejangizni ko'ring yoki yangi vazifa qo'shing\n\nEslatma: Har bir vazifa vaqtida bot sizga eslatib qo'yadi!",
        "no_schedules": "📅 *Kun Tartibim*\n\nBugun uchun vazifalar yo'q.\nYangi vazifa qo'shish uchun tugmani bosing:",
        "add_schedule_title": "➕ *Yangi Vazifa*",
        "add_schedule_desc": "Vazifa matnini yuboring:\n\n*Misol:* Darsga borish, Sport, Uy ishi...",
        "enter_schedule_time": "⏰ *Vaqtini kiriting*\n\nSoat va daqiqani quyidagi formatda yuboring:\n• `09:00`\n• `14:30`\n• `18:45`",
        "schedule_added": "✅ Vazifa qo'shildi!\n\n⏰ {time}\n📝 {task}",
        "schedule_reminder": "⏰ *Eslatma!*\n\n📝 {task}\n\nBu vazifani bajardingizmi?",
        "schedule_completed": "✅ Bajarildi!",
        "schedule_missed": "❌ Bajarilmadi",
        "schedule_stats": "📊 Bugungi statistika:\n✅ Bajarildi: {completed}\n❌ Bajarilmadi: {missed}\n⏳ Kutilmoqda: {pending}",
        "weekly_stats_title": "📊 *Haftalik Statistika*",
        "weekly_stats": "📅 {week_start} - {week_end}\n\n✅ Bajarildi: {completed}\n❌ Bajarilmadi: {missed}\n📊 Jami: {total}\n\n🎯 Bajarilish darajasi: {percentage}%",
        "no_weekly_stats": "📊 *Haftalik Statistika*\n\nBu hafta uchun hali vazifalar yo'q.",
        "view_weekly_stats": "📊 Haftalik Stat",
        "my_statistics": "📈 Statistiklarim",
        "stats_title": "📈 *Mening Statistikalarim*",
        "stats_overall": "📊 *Umumiy Statistika*\n\n✅ Bajarilgan vazifalar: {completed}\n❌ Bajarilmagan vazifalar: {missed}\n📊 Jami vazifalar: {total}",
        "stats_rating": "🎯 *Baholash*\n\nBajarilish darajasi: {percentage}%\n⭐ Baho: {rating}/10\n\n{rating_text}",
        "rating_excellent": "🏆 A'lo! Siz juda mehnatkorsiz!",
        "rating_good": "👍 Yaxshi! Davom eting!",
        "rating_average": "😐 O'rtacha. Yanada harakat qiling!",
        "rating_poor": "😔 Yaxshiroq harakat qilishingiz kerak!",
        "main_menu": "🏠 Bosh menu",
        "back": "⬅️ Orqaga",
        "cancel": "❌ Bekor qilish",
        "delete": "🗑️ O'chirish",
        "confirm_delete": "✅ Ha, o'chirish",
        "cancel_delete": "❌ Yo'q, bekor qilish",
        "add": "➕ Yangi",
        "no_folders": "📁 *Sizda hali papkalar yo'q*\n\nYangi papka yaratish uchun tugmani bosing:",
        "no_contacts": "📇 *Kontaktlarim*\n\nSizda hali kontaktlar yo'q.\nYangi kontakt qo'shish uchun tugmani bosing:",
        "no_notes": "📝 *Eslatmalarim*\n\nSizda hali eslatmalar yo'q.\nYangi eslatma qo'shish uchun tugmani bosing:",
        "enter_folder_name": "📁 *Yangi Papka*\n\nPapka nomini kiriting:",
        "select_color": "🎨 *Rang tanlang*\n\nPapka uchun rang tanlang:",
        "pin_folder": "📌 Prikrepit",
        "unpin_folder": "📌 Otkrepit",
        "color_red": "🔴 Qizil",
        "color_green": "🟢 Yashil",
        "color_blue": "🔵 Ko'k",
        "color_yellow": "🟡 Sariq",
        "color_purple": "🟣 Siyohrang",
        "color_orange": "🟠 To'q sariq",
        "enter_contact_phone": "➕ *Yangi Kontakt*\n\nTelefon raqamini kiriting:\n(Masalan: +998901234567)",
        "enter_contact_name": "Endi kontaktga ism bering:\n(Masalan: 'Ali', 'Dadam')",
        "enter_note_title": "➕ *Yangi Eslatma*\n\nEslatma sarlavhasini kiriting:\n(Masalan: 'Bank karta PIN', 'Wi-Fi parol')",
        "enter_note_content": "Endi eslatma matnini kiriting:",
        "saved": "✅ *Saqlandi!*",
        "deleted": "✅ *O'chirildi!*",
        "confirm_delete_text": "🗑️ *O'chirish*\n\nIshonchingiz komilmi?",
        "not_found": "❌ Topilmadi.",
        "help_text": "📋 *Yordam*\n\nBu bot orqadi:\n• 📁 Shaxsiy papkalar yaratishingiz\n• 🔒 Papkalarni parol bilan himoyalashingiz\n• 📸 Rasmlar va videolar saqlashingiz\n• 📇 Kontaktlar saqlashingiz\n• 📝 Eslatmalar yozishingiz mumkin",
    },
    "ru": {
        "welcome": "🔐 *Xotira Vault* - Личное Хранилище\n\n📸 Храните фото, видео, контакты и заметки безопасно!\n\n✨ *Возможности:*\n• 📁 Создавать неограниченно папок\n• 📇 Сохранять неограниченно контактов\n• 📝 Писать неограниченно заметок\n• 🔒 Защита паролем\n• 📸 Хранить фото и видео\n• 🗑️ Удалять папки\n\n*Храните свои воспоминания с нами!*",
        "select_language": "🌐 *Выберите язык*\n\nПожалуйста, выберите язык:",
        "my_folders": "📁 Мои Папки",
        "my_contacts": "📇 Контакты",
        "my_notes": "📝 Заметки",
        "my_links": "🔗 Мои Ссылки",
        "add_folder": "➕ Новая Папка",
        "add_contact": "➕ Контакт",
        "add_note": "➕ Заметка",
        "add_link": "➕ Ссылка",
        "upload_file": "📤 Загрузить",
        "help": "❓ Помощь",
        "main_menu": "🏠 Главное меню",
        "back": "⬅️ Назад",
        "cancel": "❌ Отмена",
        "delete": "🗑️ Удалить",
        "confirm_delete": "✅ Да, удалить",
        "cancel_delete": "❌ Нет, отмена",
        "add": "➕ Новый",
        "no_folders": "📁 *У вас пока нет папок*\n\nНажмите кнопку, чтобы создать:",
        "no_contacts": "📇 *Контакты*\n\nУ вас пока нет контактов.\nНажмите кнопку, чтобы добавить:",
        "no_notes": "📝 *Заметки*\n\nУ вас пока нет заметок.\nНажмите кнопку, чтобы добавить:",
        "enter_folder_name": "📁 *Новая Папка*\n\nВведите название папки:",
        "select_color": "🎨 *Выберите цвет*\n\nВыберите цвет для папки:",
        "pin_folder": "📌 Закрепить",
        "unpin_folder": "📌 Открепить",
        "color_red": "🔴 Красный",
        "color_green": "🟢 Зеленый",
        "color_blue": "🔵 Синий",
        "color_yellow": "🟡 Желтый",
        "color_purple": "🟣 Фиолетовый",
        "color_orange": "🟠 Оранжевый",
        "enter_contact_phone": "➕ *Новый Контакт*\n\nВведите номер телефона:\n(Например: +79991234567)",
        "enter_contact_name": "Теперь введите имя:\n(Например: 'Али', 'Папа')",
        "enter_note_title": "➕ *Новая Заметка*\n\nВведите заголовок:\n(Например: 'PIN карты', 'Wi-Fi пароль')",
        "enter_note_content": "Теперь введите текст заметки:",
        "saved": "✅ *Сохранено!*",
        "deleted": "✅ *Удалено!*",
        "confirm_delete_text": "🗑️ *Удаление*\n\nВы уверены?",
        "not_found": "❌ Не найдено.",
        "help_text": "📋 *Помощь*\n\nС помощью этого бота вы можете:\n• 📁 Создавать личные папки\n• 🔒 Защищать паролем\n• 📸 Хранить фото и видео\n• 📇 Сохранять контакты\n• 📝 Писать заметки",
    },
    "kz": {
        "welcome": "🔐 *Xotira Vault* - Жеке Қойма\n\n📸 Фото, видео, контакттар мен ескертулерді қауіпсіз сақтаңыз!\n\n✨ *Мүмкіндіктер:*\n• 📁 Шексіз қапша жасау\n• 📇 Шексіз контакт сақтау\n• 📝 Шексіз ескерту жазу\n• 🔒 Құпия сөзбен қорғау\n• 📸 Фото және видео сақтау\n• 🗑️ Қапшаны жою\n\n*Естеліктеріңізді бізбен қауіпсіз сақтаңыз!*",
        "select_language": "🌐 *Тілді таңдаңыз*\n\nТілді таңдаңыз:",
        "my_folders": "📁 Менің Қапшаларым",
        "my_contacts": "📇 Контакттарым",
        "my_notes": "📝 Ескертулерім",
        "add_folder": "➕ Жаңа Қапша",
        "add_contact": "➕ Контакт",
        "add_note": "➕ Ескерту",
        "upload_file": "📤 Жүктеу",
        "help": "❓ Көмек",
        "main_menu": "🏠 Басты мәзір",
        "back": "⬅️ Артқа",
        "cancel": "❌ Болдырмау",
        "delete": "🗑️ Жою",
        "confirm_delete": "✅ Иә, жою",
        "cancel_delete": "❌ Жоқ, болдырмау",
        "add": "➕ Жаңа",
        "no_folders": "📁 *Сізде әлі қапша жоқ*\n\nЖасау үшін батырманы басыңыз:",
        "no_contacts": "📇 *Контакттарым*\n\nСізде әлі контакттар жоқ.\nҚосу үшін батырманы басыңыз:",
        "no_notes": "📝 *Ескертулерім*\n\nСізде әлі ескертулер жоқ.\nҚосу үшін батырманы басыңыз:",
        "no_links": "🔗 *Сілтемелерім*\n\nСізде әлі сілтемелер жоқ.\nҚосу үшін батырманы басыңыз:",
        "enter_folder_name": "📁 *Жаңа Қапша*\n\nҚапша атын енгізіңіз:",
        "select_color": "🎨 *Түс таңдаңыз*\n\nҚапша үшін түс таңдаңыз:",
        "pin_folder": "📌 Бекіту",
        "unpin_folder": "📌 Бекітуді алу",
        "color_red": "🔴 Қызыл",
        "color_green": "🟢 Жасыл",
        "color_blue": "🔵 Көк",
        "color_yellow": "🟡 Сары",
        "color_purple": "🟣 Күлгін",
        "color_orange": "🟠 Қызғылт сары",
        "enter_contact_phone": "➕ *Жаңа Контакт*\n\nТелефон нөмірін енгізіңіз:\n(Мысалы: +77001234567)",
        "enter_contact_name": "Енді контактке ат беріңіз:\n(Мысалы: 'Али', 'Папа')",
        "enter_note_title": "➕ *Жаңа Ескерту*\n\nЕскерту тақырыбын енгізіңіз:\n(Мысалы: 'Банк картасы PIN', 'Wi-Fi құпия сөзі')",
        "enter_note_content": "Енді ескерту мәтінін енгізіңіз:",
        "saved": "✅ *Сақталды!*",
        "deleted": "✅ *Жойылды!*",
        "confirm_delete_text": "🗑️ *Жою*\n\nСенімдісіз бе?",
        "not_found": "❌ Табылмады.",
        "help_text": "📋 *Көмек*\n\nБұл бот арқылы сіз:\n• 📁 Жеке қапшалар жасай аласыз\n• 🔒 Құпия сөзбен қорғай аласыз\n• 📸 Фото және видео сақтай аласыз\n• 📇 Контакттар сақтай аласыз\n• 📝 Ескертулер жаза аласыз",
    }
}

def get_text(key, lang="uz"):
    """Tanlangan til bo'yicha matn olish"""
    return TRANSLATIONS.get(lang, TRANSLATIONS["uz"]).get(key, key)

# ==================== YORDAMCHI FUNKSIYALAR ====================

def load_data():
    """Ma'lumotlarni yuklash"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    """Ma'lumotlarni saqlash"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_password(password):
    """Parolni shifrlash"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Parolni tekshirish"""
    return hash_password(password) == hashed

# ==================== BOT KOMMANDALARI ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komandasi - Til tanlash"""
    user_id = str(update.effective_user.id)
    data = load_data()
    
    # Foydalanuvchi aktivligini yangilash
    update_user_activity(user_id)
    
    # Foydalanuvchi mavjudmi va tili tanlanganmi?
    if user_id in data and data[user_id].get("language"):
        # Til tanlangan, asosiy menyuni ko'rsatish
        lang = data[user_id]["language"]
        await show_main_menu(update, context, lang)
        return
    
    # Yangi foydalanuvchi - til tanlash menyusi
    if user_id not in data:
        data[user_id] = {
            "folders": {},
            "contacts": {},
            "notes": {},
            "language": None,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        save_data(data)
    
    # Til tanlash menyusi
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🧠 *MemoryBot*\n\n"
        "🌐 *Tilni tanlang / Выберите язык / Тілді таңдаңыз*\n\n"
        "Iltimos, tilni tanlang:\n"
        "Пожалуйста, выберите язык:\n"
        "Тілді таңдаңыз:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang="uz"):
    """Asosiy menyuni ko'rsatish (yangi xabar)"""
    keyboard = [
        [InlineKeyboardButton(get_text("my_folders", lang), callback_data="my_folders"), 
         InlineKeyboardButton(get_text("add_folder", lang), callback_data="create_folder")],
        [InlineKeyboardButton(get_text("my_contacts", lang), callback_data="my_contacts"), 
         InlineKeyboardButton(get_text("add_contact", lang), callback_data="add_contact")],
        [InlineKeyboardButton(get_text("my_notes", lang), callback_data="my_notes"), 
         InlineKeyboardButton(get_text("add_note", lang), callback_data="add_note")],
        [InlineKeyboardButton(get_text("my_links", lang), callback_data="my_links"), 
         InlineKeyboardButton(get_text("add_link", lang), callback_data="add_link")],
        [InlineKeyboardButton(get_text("my_schedule", lang), callback_data="my_schedule"), 
         InlineKeyboardButton(get_text("add_schedule", lang), callback_data="add_schedule")],
        [InlineKeyboardButton(get_text("my_statistics", lang), callback_data="my_statistics")],
        [InlineKeyboardButton(get_text("upload_file", lang), callback_data="upload_file")],
        [InlineKeyboardButton(get_text("help", lang), callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        get_text("welcome", lang),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_main_menu_query(query, context, lang="uz"):
    """Asosiy menyuni ko'rsatish (edit_message_text bilan)"""
    keyboard = [
        [InlineKeyboardButton(get_text("my_folders", lang), callback_data="my_folders"), 
         InlineKeyboardButton(get_text("add_folder", lang), callback_data="create_folder")],
        [InlineKeyboardButton(get_text("my_contacts", lang), callback_data="my_contacts"), 
         InlineKeyboardButton(get_text("add_contact", lang), callback_data="add_contact")],
        [InlineKeyboardButton(get_text("my_notes", lang), callback_data="my_notes"), 
         InlineKeyboardButton(get_text("add_note", lang), callback_data="add_note")],
        [InlineKeyboardButton(get_text("my_links", lang), callback_data="my_links"), 
         InlineKeyboardButton(get_text("add_link", lang), callback_data="add_link")],
        [InlineKeyboardButton(get_text("my_schedule", lang), callback_data="my_schedule"), 
         InlineKeyboardButton(get_text("add_schedule", lang), callback_data="add_schedule")],
        [InlineKeyboardButton(get_text("my_statistics", lang), callback_data="my_statistics")],
        [InlineKeyboardButton(get_text("upload_file", lang), callback_data="upload_file")],
        [InlineKeyboardButton(get_text("help", lang), callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        get_text("welcome", lang),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help komandasi"""
    text = (
        "📋 *Bot buyruqlari:*\n\n"
        "/start - Bosh menyu\n"
        "/folders - Mening papkalarim\n"
        "/create - Yangi papka yaratish\n"
        "/upload - Fayl yuklash\n"
        "/help - Yordam\n\n"
        "🔍 *Qanday foydalanish:*\n"
        "1. 📁 'Yangi Papka Yaratish' tugmasini bosing\n"
        "2. 📝 Papka nomini kiriting\n"
        "3. 🔒 (ixtiyoriy) Parol qo'ying\n"
        "4. 📤 Rasmingiz yoki videongizni yuboring\n"
        "5. 📝 Faylga nom va sana qo'shing\n"
        "6. ✅ Tayyor!\n\n"
        "🔐 *Xavfsizlik:*\n"
        "• Barcha ma'lumotlar shifrlanadi\n"
        "• Parolni bilmasdan papka ochilmaydi\n"
        "• Faqat siz ko'rishingiz mumkin"
    )
    
    keyboard = [[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def welcome_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi foydalanuvchini kutib olish - /start bosmasdan oldin"""
    # Faqat shaxsiy chatda ishlaydi
    if update.effective_chat.type != "private":
        return
    
    user = update.effective_user
    
    # MemoryBot logotipi - URL orqali
    # SIZ O'ZINGIZNING LOGOTIP URL'INGIZNI QO'YING!
    # Imgur.com ga yuklang va to'g'ri linkni qo'ying
    # Masalan: https://i.imgur.com/ABC123.png
    LOGO_URL = "https://i.imgur.com/placeholder.png"  # <-- BU YERGA O'ZINGIZNING LOGOTIP URL'INGIZNI YOZING
    
    welcome_caption = (
        f"🧠 *MemoryBot*\n\n"
        f"👋 Salom, *{user.first_name}!*\n\n"
        f"📸 *Bu bot orqali siz:*\n"
        f"• 📁 Cheksiz rasm va video saqlash\n"
        f"• 📇 Kontaktlaringizni xavfsiz saqlash\n"
        f"• 📝 Muhim eslatmalarni yozib qo'yish\n"
        f"• 🔒 Parol bilan maxfiy ma'lumotlarni himoyalash\n\n"
        f"💎 *Bu eslatmalar hech qachon ochib ketmaydi!*\n"
        f"• 🛡️ Doimiy va xavfsiz saqlash\n"
        f"• 📱 Har qanday vaqtda, har qanday joyda\n"
        f"• 🆓 Bepul foydalanish\n\n"
        f"🚀 *Boshlash uchun /start bosing!*"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Boshlash", callback_data="start_bot")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Logotip bilan xabar yuborish
        await update.message.reply_photo(
            photo=LOGO_URL,
            caption=welcome_caption,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except:
        # Agar logotip yuklanmasa, faqat matn yuborish
        await update.message.reply_text(welcome_caption, reply_markup=reply_markup, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stats komandasi - Admin uchun statistika"""
    user_id = str(update.effective_user.id)
    
    # Admin tekshiruvi
    if user_id != ADMIN_ID:
        await update.message.reply_text(
            "❌ Sizda bu buyruqni ishlatish huquqi yo'q.",
            parse_mode="Markdown"
        )
        return
    
    stats = get_user_stats()
    
    text = (
        "📊 *Bot Statistikasi*\n\n"
        f"👥 *Jami foydalanuvchilar:* {stats['total_users']}\n"
        f"📱 *Bugun faol:* {stats['active_today']}\n"
        f"📅 *Haftada faol:* {stats['active_weekly']}\n\n"
        f"📈 *Faollik darajasi:* {round(stats['active_today']/stats['total_users']*100, 1) if stats['total_users'] > 0 else 0}%"
    )
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ==================== CALLBACK HANDLERLAR ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugma bosilganda ishga tushadi"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(update.effective_user.id)
    
    # Foydalanuvchi aktivligini yangilash
    update_user_activity(user_id)
    
    # Boshlash tugmasi (start bosmasdan oldin)
    if data == "start_bot":
        await start(update, context)
        return
    
    # Til tanlash
    if data.startswith("lang_"):
        lang = data.replace("lang_", "")
        data_db = load_data()
        if user_id not in data_db:
            data_db[user_id] = {"folders": {}, "contacts": {}, "notes": {}, "language": lang, "created_at": datetime.now().isoformat(), "last_activity": datetime.now().isoformat()}
        else:
            data_db[user_id]["language"] = lang
            data_db[user_id]["last_activity"] = datetime.now().isoformat()
        save_data(data_db)
        
        # Asosiy menyuni ko'rsatish
        await show_main_menu_query(query, context, lang)
        return
    
    # Foydalanuvchi tilini olish
    user_data = load_data().get(user_id, {})
    lang = user_data.get("language", "uz")
    
    # Bosh menu
    if data == "main_menu":
        await show_main_menu_query(query, context, lang)
    
    # Yordam
    elif data == "help":
        keyboard = [[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❓ *Yordam*\n\n"
            "Bu bot orqali:\n"
            "• 📁 Shaxsiy papkalar yaratishingiz\n"
            "• 🔒 Papkalarni parol bilan himoyalashingiz\n"
            "• 📸 Rasmlar va videolar saqlashingiz\n"
            "• ✨ Rasmlarni tiniqlashtirish\n"
            "• 📝 Fayllarga nom va sana qo'shishingiz mumkin\n\n"
            "Boshlash uchun 'Yangi Papka Yaratish' tugmasini bosing.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Kun tartibim
    elif data == "my_schedule":
        await show_schedule_list(query, context, user_id)
    
    # Yangi vazifa qo'shish
    elif data == "add_schedule":
        context.user_data["action"] = "adding_schedule_task"
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            get_text("add_schedule_title", context.user_data.get("language", "uz")) + "\n\n" +
            get_text("add_schedule_desc", context.user_data.get("language", "uz")),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Vazifa bajarildi
    elif data.startswith("schedule_done_"):
        schedule_id = data.replace("schedule_done_", "")
        await mark_schedule_done(query, context, user_id, schedule_id, True)
    
    # Vazifa bajarilmadi
    elif data.startswith("schedule_missed_"):
        schedule_id = data.replace("schedule_missed_", "")
        await mark_schedule_done(query, context, user_id, schedule_id, False)
    
    # Haftalik statistika
    elif data == "weekly_stats":
        await show_weekly_stats(query, context, user_id)
    
    # Mening statistikalarim
    elif data == "my_statistics":
        await show_my_statistics(query, context, user_id)
    
    # Mening papkalarim
    elif data == "my_folders":
        user_data = load_data().get(user_id, {})
        folders = user_data.get("folders", {})
        
        if not folders:
            keyboard = [
                [InlineKeyboardButton("➕ Yangi Papka Yaratish", callback_data="create_folder")],
                [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📁 *Sizda hali papkalar yo'q*\n\n"
                "Yangi papka yaratish uchun tugmani bosing:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        # Papkalarni pin bo'yicha saralash
        sorted_folders = sorted(folders.items(), key=lambda x: (not x[1].get("pinned", False), x[1].get("name", "")))
        
        keyboard = []
        for folder_id, folder_info in sorted_folders:
            lock_icon = "🔒" if folder_info.get("password") else "📂"
            file_count = len(folder_info.get("files", []))
            color = folder_info.get("color", "📂")
            pin_icon = "📌 " if folder_info.get("pinned", False) else ""
            keyboard.append([InlineKeyboardButton(
                f"{pin_icon}{color} {folder_info['name']} ({file_count} ta)",
                callback_data=f"open_folder_{folder_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📁 *Mening Papkalarim*\n\n"
            "Papkani ochish uchun uni tanlang:\n"
            "📌 = Prikreplennye",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Yangi papka yaratish
    elif data == "create_folder":
        context.user_data["action"] = "creating_folder"
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➕ *Yangi Papka Yaratish*\n\n"
            "Papka nomini kiriting:\n"
            "(Masalan: 'Mening rasmlarim', '2024-yil', 'Oilaviy')",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Papka rangi tanlash
    elif data.startswith("select_color_"):
        folder_name = data.replace("select_color_", "")
        context.user_data["folder_name"] = folder_name
        
        lang = context.user_data.get("language", "uz")
        
        keyboard = [
            [InlineKeyboardButton(get_text("color_red", lang), callback_data="color_🔴"),
             InlineKeyboardButton(get_text("color_green", lang), callback_data="color_🟢")],
            [InlineKeyboardButton(get_text("color_blue", lang), callback_data="color_🔵"),
             InlineKeyboardButton(get_text("color_yellow", lang), callback_data="color_🟡")],
            [InlineKeyboardButton(get_text("color_purple", lang), callback_data="color_🟣"),
             InlineKeyboardButton(get_text("color_orange", lang), callback_data="color_🟠")],
            [InlineKeyboardButton(get_text("cancel", lang), callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            get_text("select_color", lang),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Rang tanlanganidan so'ng papka yaratish
    elif data.startswith("color_"):
        color = data.replace("color_", "")
        folder_name = context.user_data.get("folder_name", "Yangi Papka")
        user_id = str(query.from_user.id)
        
        # Papka yaratish
        folder_id = f"folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        data = load_data()
        if user_id not in data:
            data[user_id] = {"folders": {}, "contacts": {}, "notes": {}, "language": context.user_data.get("language", "uz"), "created_at": datetime.now().isoformat()}
        
        data[user_id]["folders"][folder_id] = {
            "name": folder_name,
            "color": color,
            "pinned": False,
            "created_at": datetime.now().isoformat(),
            "files": [],
            "password": None
        }
        save_data(data)
        
        context.user_data["action"] = None
        context.user_data["folder_name"] = None
        context.user_data["folder_id"] = folder_id
        
        keyboard = [
            [InlineKeyboardButton("📤 Fayl yuklash", callback_data=f"upload_to_{folder_id}")],
            [InlineKeyboardButton("🔒 Parol qo'yish", callback_data="set_password")],
            [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ *Papka yaratildi!*\n\n"
            f"{color} *{folder_name}*\n\n"
            f"Endi fayl yuklash yoki parol qo'yishingiz mumkin:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Papka ochish
    elif data.startswith("open_folder_"):
        folder_id = data.replace("open_folder_", "")
        user_data = load_data().get(user_id, {})
        folder = user_data.get("folders", {}).get(folder_id)
        
        if not folder:
            await query.edit_message_text(
                "❌ Papka topilmadi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        # Agar parol bo'lsa, tekshirish
        if folder.get("password"):
            context.user_data["action"] = "entering_password"
            context.user_data["folder_id"] = folder_id
            
            keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🔒 *Papka himoyalangan*\n\n"
                f"Papka: *{folder['name']}*\n\n"
                f"Parolni kiriting:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        # Parol bo'lmasa, to'g'ridan-to'g'ri ochish
        await show_folder_contents(query, context, folder_id, folder)
    
    # Fayl yuklash
    elif data == "upload_file":
        user_data = load_data().get(user_id, {})
        folders = user_data.get("folders", {})
        
        if not folders:
            keyboard = [
                [InlineKeyboardButton("➕ Avval papka yaratish", callback_data="create_folder")],
                [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ *Avval papka yaratishingiz kerak!*\n\n"
                "Fayl yuklashdan oldin papka yarating:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        keyboard = []
        for folder_id, folder_info in folders.items():
            keyboard.append([InlineKeyboardButton(
                f"📂 {folder_info['name']}",
                callback_data=f"upload_to_{folder_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📤 *Fayl Yuklash*\n\n"
            "Qaysi papkaga yuklashni tanlang:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Papkaga yuklash
    elif data.startswith("upload_to_"):
        folder_id = data.replace("upload_to_", "")
        context.user_data["action"] = "uploading_file"
        context.user_data["upload_folder_id"] = folder_id
        # Yuklash hisoblagichini tozalash
        context.user_data.pop("upload_count", None)
        context.user_data.pop("upload_start_time", None)
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📤 *Fayl yuklash*\n\n"
            "Endi rasm yoki video yuboring:\n"
            "(Bir nechta fayl yuklashingiz mumkin)",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Yuklashni tugatish
    elif data == "finish_upload":
        folder_id = context.user_data.get("upload_folder_id")
        upload_count = context.user_data.get("upload_count", 0)
        
        # Tozalash
        context.user_data["action"] = None
        context.user_data.pop("upload_folder_id", None)
        context.user_data.pop("upload_count", None)
        context.user_data.pop("upload_start_time", None)
        
        if folder_id:
            data = load_data()
            folder = data.get(user_id, {}).get("folders", {}).get(folder_id)
            if folder:
                total_files = len(folder.get("files", []))
                
                keyboard = [
                    [InlineKeyboardButton("📤 Yana yuklash", callback_data=f"upload_to_{folder_id}")],
                    [InlineKeyboardButton("📁 Papkalarim", callback_data="my_folders")],
                    [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ *Yuklash tugatildi!*\n\n"
                    f"📁 Papka: {folder['name']}\n"
                    f"📊 Jami fayllar: {total_files} ta\n"
                    f"🆕 Yangi yuklandi: {upload_count} ta\n\n"
                    f"Xotirangiz xavfsiz saqlandi! 🔐",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    "✅ *Yuklash tugatildi!*",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
                )
        else:
            await query.edit_message_text(
                "✅ *Yuklash tugatildi!*",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
    
    # Papka sozlamalari
    elif data.startswith("folder_settings_"):
        folder_id = data.replace("folder_settings_", "")
        context.user_data["folder_id"] = folder_id
        
        user_data = load_data().get(user_id, {})
        folder = user_data.get("folders", {}).get(folder_id, {})
        is_pinned = folder.get("pinned", False)
        lang = context.user_data.get("language", "uz")
        
        pin_text = get_text("unpin_folder", lang) if is_pinned else get_text("pin_folder", lang)
        
        keyboard = [
            [InlineKeyboardButton("📤 Fayl qo'shish", callback_data=f"upload_to_{folder_id}")],
            [InlineKeyboardButton(pin_text, callback_data=f"toggle_pin_{folder_id}")],
            [InlineKeyboardButton("🔒 Parol qo'yish", callback_data="set_password")],
            [InlineKeyboardButton("🗑️ Papkani o'chirish", callback_data="delete_folder")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="my_folders")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ *Papka Sozlamalari*\n\n"
            "Nima qilishni xohlaysiz?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Pin/unpin papka
    elif data.startswith("toggle_pin_"):
        folder_id = data.replace("toggle_pin_", "")
        context.user_data["folder_id"] = folder_id
        
        data = load_data()
        if user_id in data and folder_id in data[user_id]["folders"]:
            current_pin = data[user_id]["folders"][folder_id].get("pinned", False)
            data[user_id]["folders"][folder_id]["pinned"] = not current_pin
            save_data(data)
            
            # Sozlamalarni qayta ko'rsatish
            folder = data[user_id]["folders"][folder_id]
            is_pinned = folder.get("pinned", False)
            lang = context.user_data.get("language", "uz")
            
            pin_text = get_text("unpin_folder", lang) if is_pinned else get_text("pin_folder", lang)
            
            keyboard = [
                [InlineKeyboardButton("📤 Fayl qo'shish", callback_data=f"upload_to_{folder_id}")],
                [InlineKeyboardButton(pin_text, callback_data=f"toggle_pin_{folder_id}")],
                [InlineKeyboardButton("🔒 Parol qo'yish", callback_data="set_password")],
                [InlineKeyboardButton("🗑️ Papkani o'chirish", callback_data="delete_folder")],
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="my_folders")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            status = "📌 Prikrepleno!" if is_pinned else "📌 Otkrepleno!"
            await query.edit_message_text(
                f"✅ {status}\n\n"
                "⚙️ *Papka Sozlamalari*\n\n"
                "Nima qilishni xohlaysiz?",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    
    # Parol qo'yish
    elif data == "set_password":
        context.user_data["action"] = "setting_password"
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔒 *Parol qo'yish*\n\n"
            "Yangi parolni kiriting:\n"
            "(Kamida 4 ta belgi)",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Papka o'chirish
    elif data == "delete_folder":
        folder_id = context.user_data.get("folder_id")
        if not folder_id:
            await query.edit_message_text(
                "❌ Xatolik yuz berdi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"confirm_delete_{folder_id}")],
            [InlineKeyboardButton("❌ Yo'q, bekor qilish", callback_data="my_folders")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑️ *Papkani o'chirish*\n\n"
            "Ishonchingiz komilmi?\n"
            "Barcha fayllar o'chib ketadi!",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # O'chirishni tasdiqlash
    elif data.startswith("confirm_delete_"):
        folder_id = data.replace("confirm_delete_", "")
        
        data = load_data()
        if user_id in data and folder_id in data[user_id]["folders"]:
            # Fayllarni o'chirish
            folder = data[user_id]["folders"][folder_id]
            for file_info in folder.get("files", []):
                file_path = os.path.join(STORAGE_DIR, file_info["filename"])
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Papkani o'chirish
            del data[user_id]["folders"][folder_id]
            save_data(data)
            
            await query.edit_message_text(
                "✅ *Papka o'chirildi!*",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
        else:
            await query.edit_message_text(
                "❌ Papka topilmadi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
    
    # Kontaktlarim
    elif data == "my_contacts":
        user_data = load_data().get(user_id, {})
        contacts = user_data.get("contacts", {})
        
        if not contacts:
            keyboard = [
                [InlineKeyboardButton("➕ Kontakt Qo'shish", callback_data="add_contact")],
                [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📇 *Kontaktlarim*\n\n"
                "Sizda hali kontaktlar yo'q.\n"
                "Yangi kontakt qo'shish uchun tugmani bosing:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        keyboard = []
        for contact_id, contact_info in contacts.items():
            keyboard.append([InlineKeyboardButton(
                f"👤 {contact_info['name']} • 📱 {contact_info['phone']}",
                callback_data=f"view_contact_{contact_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Yangi Kontakt", callback_data="add_contact")])
        keyboard.append([InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📇 *Kontaktlarim* ({len(contacts)} ta)\n\n"
            f"Kontaktni ko'rish uchun tanlang:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Kontakt qo'shish
    elif data == "add_contact":
        context.user_data["action"] = "adding_contact_phone"
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➕ *Yangi Kontakt*\n\n"
            "Telefon raqamini kiriting:\n"
            "(Masalan: +998901234567)",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Kontaktni ko'rish
    elif data.startswith("view_contact_"):
        contact_id = data.replace("view_contact_", "")
        user_data = load_data().get(user_id, {})
        contact = user_data.get("contacts", {}).get(contact_id)
        
        if not contact:
            await query.edit_message_text(
                "❌ Kontakt topilmadi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("🗑️ O'chirish", callback_data=f"delete_contact_{contact_id}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="my_contacts")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        contact_text = (
            f"👤 *{contact['name']}*\n\n"
            f"📱 Telefon: {contact['phone']}\n"
        )
        if contact.get('note'):
            contact_text += f"📝 Izoh: {contact['note']}"
        
        await query.edit_message_text(
            contact_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Kontakt o'chirish
    elif data.startswith("delete_contact_"):
        contact_id = data.replace("delete_contact_", "")
        
        keyboard = [
            [InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"confirm_delete_contact_{contact_id}")],
            [InlineKeyboardButton("❌ Yo'q, bekor qilish", callback_data=f"view_contact_{contact_id}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑️ *Kontaktni o'chirish*\n\n"
            "Ishonchingiz komilmi?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Kontakt o'chirishni tasdiqlash
    elif data.startswith("confirm_delete_contact_"):
        contact_id = data.replace("confirm_delete_contact_", "")
        
        data = load_data()
        if user_id in data and "contacts" in data[user_id] and contact_id in data[user_id]["contacts"]:
            del data[user_id]["contacts"][contact_id]
            save_data(data)
            
            await query.edit_message_text(
                "✅ *Kontakt o'chirildi!*",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📇 Kontaktlarim", callback_data="my_contacts")]])
            )
        else:
            await query.edit_message_text(
                "❌ Kontakt topilmadi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
    
    # Izohni o'tkazib yuborish
    elif data == "skip_contact_note":
        await save_contact_from_callback(query, context)
    
    # Link izohini o'tkazib yuborish
    elif data == "skip_link_description":
        link_url = context.user_data.get("link_url", "")
        link_title = context.user_data.get("link_title", "Nomsiz link")
        user_id = str(query.from_user.id)
        
        data = load_data()
        
        if user_id not in data:
            data[user_id] = {"folders": {}, "contacts": {}, "notes": {}, "links": {}, "created_at": datetime.now().isoformat()}
        
        if "links" not in data[user_id]:
            data[user_id]["links"] = {}
        
        import uuid
        link_id = str(uuid.uuid4())[:8]
        
        data[user_id]["links"][link_id] = {
            "url": link_url,
            "title": link_title,
            "description": "",
            "created_at": datetime.now().isoformat()
        }
        
        save_data(data)
        
        # Tozalash
        context.user_data.pop("action", None)
        context.user_data.pop("link_url", None)
        context.user_data.pop("link_title", None)
        
        keyboard = [
            [InlineKeyboardButton("🔗 Linklarim", callback_data="my_links")],
            [InlineKeyboardButton("➕ Yana Link", callback_data="add_link")],
            [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ *Link saqlandi!*\n\n"
            f"🔗 *{link_title}*\n"
            f"📎 {link_url[:50]}...",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Eslatmalarim
    elif data == "my_notes":
        user_data = load_data().get(user_id, {})
        notes = user_data.get("notes", {})
        
        if not notes:
            keyboard = [
                [InlineKeyboardButton("➕ Eslatma Qo'shish", callback_data="add_note")],
                [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📝 *Eslatmalarim*\n\n"
                "Sizda hali eslatmalar yo'q.\n"
                "Yangi eslatma qo'shish uchun tugmani bosing:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        keyboard = []
        for note_id, note_info in notes.items():
            preview = note_info['title'][:15] + "..." if len(note_info['title']) > 15 else note_info['title']
            created = note_info.get("created_at", "")[:10]
            keyboard.append([InlineKeyboardButton(
                f"📝 {preview} • {created}",
                callback_data=f"view_note_{note_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Yangi Eslatma", callback_data="add_note")])
        keyboard.append([InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📝 *Eslatmalarim* ({len(notes)} ta)\n\n"
            f"Eslatmani ko'rish uchun tanlang:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Eslatma qo'shish
    elif data == "add_note":
        context.user_data["action"] = "adding_note_title"
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➕ *Yangi Eslatma*\n\n"
            "Eslatma sarlavhasini kiriting:\n"
            "(Masalan: 'Bank karta PIN', 'Wi-Fi parol', 'Muhim sanalar')",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Eslatmani ko'rish
    elif data.startswith("view_note_"):
        note_id = data.replace("view_note_", "")
        user_data = load_data().get(user_id, {})
        note = user_data.get("notes", {}).get(note_id)
        
        if not note:
            await query.edit_message_text(
                "❌ Eslatma topilmadi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("🗑️ O'chirish", callback_data=f"delete_note_{note_id}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="my_notes")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        note_text = (
            f"📝 *{note['title']}*\n\n"
            f"{note['content']}\n\n"
            f"📅 Yaratilgan: {note.get('created_at', 'Noma\'lum')[:10]}"
        )
        
        await query.edit_message_text(
            note_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Eslatma o'chirish
    elif data.startswith("delete_note_"):
        note_id = data.replace("delete_note_", "")
        
        keyboard = [
            [InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"confirm_delete_note_{note_id}")],
            [InlineKeyboardButton("❌ Yo'q, bekor qilish", callback_data=f"view_note_{note_id}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑️ *Eslatmani o'chirish*\n\n"
            "Ishonchingiz komilmi?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Eslatma o'chirishni tasdiqlash
    elif data.startswith("confirm_delete_note_"):
        note_id = data.replace("confirm_delete_note_", "")
        
        data = load_data()
        if user_id in data and "notes" in data[user_id] and note_id in data[user_id]["notes"]:
            del data[user_id]["notes"][note_id]
            save_data(data)
            
            await query.edit_message_text(
                "✅ *Eslatma o'chirildi!*",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Eslatmalarim", callback_data="my_notes")]])
            )
        else:
            await query.edit_message_text(
                "❌ Eslatma topilmadi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
    
    # Linklarim
    elif data == "my_links":
        user_data = load_data().get(user_id, {})
        links = user_data.get("links", {})
        
        if not links:
            keyboard = [
                [InlineKeyboardButton("➕ Link Qo'shish", callback_data="add_link")],
                [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🔗 *Linklarim*\n\n"
                "Sizda hali linklar yo'q.\n"
                "Yangi link qo'shish uchun tugmani bosing:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        keyboard = []
        for link_id, link_info in links.items():
            preview = link_info['title'][:20] + "..." if len(link_info['title']) > 20 else link_info['title']
            keyboard.append([InlineKeyboardButton(
                f"🔗 {preview}",
                callback_data=f"view_link_{link_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Yangi Link", callback_data="add_link")])
        keyboard.append([InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🔗 *Linklarim* ({len(links)} ta)\n\n"
            f"Linkni ko'rish uchun tanlang:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Link qo'shish
    elif data == "add_link":
        context.user_data["action"] = "adding_link_url"
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➕ *Yangi Link*\n\n"
            "Link URL manzilini kiriting:\n"
            "(Masalan: https://youtube.com/..., https://instagram.com/...)",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Linkni ko'rish
    elif data.startswith("view_link_"):
        link_id = data.replace("view_link_", "")
        user_data = load_data().get(user_id, {})
        link = user_data.get("links", {}).get(link_id)
        
        if not link:
            await query.edit_message_text(
                "❌ Link topilmadi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("🌐 Ochish", url=link['url'])],
            [InlineKeyboardButton("🗑️ O'chirish", callback_data=f"delete_link_{link_id}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="my_links")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        link_text = (
            f"🔗 *{link['title']}*\n\n"
            f"📎 URL: `{link['url']}`\n"
        )
        if link.get('description'):
            link_text += f"\n📝 {link['description']}"
        
        await query.edit_message_text(
            link_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Link o'chirish
    elif data.startswith("delete_link_"):
        link_id = data.replace("delete_link_", "")
        
        keyboard = [
            [InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"confirm_delete_link_{link_id}")],
            [InlineKeyboardButton("❌ Yo'q, bekor qilish", callback_data=f"view_link_{link_id}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑️ *Linkni o'chirish*\n\n"
            "Ishonchingiz komilmi?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Link o'chirishni tasdiqlash
    elif data.startswith("confirm_delete_link_"):
        link_id = data.replace("confirm_delete_link_", "")
        
        data = load_data()
        if user_id in data and "links" in data[user_id] and link_id in data[user_id]["links"]:
            del data[user_id]["links"][link_id]
            save_data(data)
            
            await query.edit_message_text(
                "✅ *Link o'chirildi!*",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Linklarim", callback_data="my_links")]])
            )
        else:
            await query.edit_message_text(
                "❌ Link topilmadi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )


async def show_folder_contents(query, context, folder_id, folder):
    """Papka ichini ko'rsatish - barcha rasmlar/videolar ko'rinadi"""
    files = folder.get("files", [])
    
    if not files:
        keyboard = [
            [InlineKeyboardButton("📤 Fayl yuklash", callback_data=f"upload_to_{folder_id}")],
            [InlineKeyboardButton("⚙️ Sozlamalar", callback_data=f"folder_settings_{folder_id}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="my_folders")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📁 *{folder['name']}*\n\n"
            f"📝 Yaratilgan: {folder.get('created_at', 'Noma\'lum')[:10]}\n"
            f"📂 Fayllar: 0 ta\n\n"
            f"Bu papka bo'sh. Fayl yuklash uchun tugmani bosing:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Avval matnli xabar yuborish
    keyboard = [
        [InlineKeyboardButton("📤 Fayl yuklash", callback_data=f"upload_to_{folder_id}")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data=f"folder_settings_{folder_id}")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="my_folders")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📁 *{folder['name']}*\n\n"
        f"📝 Yaratilgan: {folder.get('created_at', 'Noma\'lum')[:10]}\n"
        f"📂 Jami fayllar: {len(files)} ta\n\n"
        f"Fayllar yuborilmoqda...",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Barcha fayllarni yuborish (file_id orqali)
    sent_count = 0
    failed_count = 0
    
    for i, file_info in enumerate(files):
        file_id = file_info.get("file_id")
        caption = f"📎 *{file_info['name']}*\n📅 {file_info.get('uploaded_at', file_info.get('date', ''))[:10]}"
        
        try:
            if file_id:
                # file_id orqali yuborish (Telegram serverlarida saqlangan)
                if file_info.get("type") == "photo":
                    await query.message.reply_photo(
                        photo=file_id,
                        caption=caption,
                        parse_mode="Markdown"
                    )
                else:  # video
                    await query.message.reply_video(
                        video=file_id,
                        caption=caption,
                        parse_mode="Markdown"
                    )
                sent_count += 1
            else:
                # Eski fayllar uchun (filename bilan)
                failed_count += 1
                print(f"file_id topilmadi: {file_info}")
        except Exception as e:
            failed_count += 1
            print(f"Fayl yuborishda xatolik: {e}")
    
    # Oxirida tugmalar bilan xabar
    if failed_count > 0:
        status_text = f"✅ *Fayllar yuborildi!*\n\n📁 {folder['name']}\n✅ Yuborildi: {sent_count} ta\n❌ Topilmadi: {failed_count} ta"
    else:
        status_text = f"✅ *Barcha fayllar yuborildi!*\n\n📁 {folder['name']} - {sent_count} ta fayl"
    
    await query.message.reply_text(
        status_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


# ==================== XABAR QABUL QILISH ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Oddiy xabarlarni qayta ishlash"""
    user_id = str(update.effective_user.id)
    action = context.user_data.get("action")
    
    # Papka yaratish
    if action == "creating_folder":
        folder_name = update.message.text.strip()
        
        if len(folder_name) < 2:
            await update.message.reply_text(
                "❌ Papka nomi juda qisqa. Kamida 2 ta belgi kiriting.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        # Rang tanlash uchun yuborish
        lang = context.user_data.get("language", "uz")
        context.user_data["folder_name"] = folder_name
        context.user_data["action"] = "selecting_color"
        
        keyboard = [
            [InlineKeyboardButton(get_text("color_red", lang), callback_data="color_🔴"),
             InlineKeyboardButton(get_text("color_green", lang), callback_data="color_🟢")],
            [InlineKeyboardButton(get_text("color_blue", lang), callback_data="color_🔵"),
             InlineKeyboardButton(get_text("color_yellow", lang), callback_data="color_🟡")],
            [InlineKeyboardButton(get_text("color_purple", lang), callback_data="color_🟣"),
             InlineKeyboardButton(get_text("color_orange", lang), callback_data="color_🟠")],
            [InlineKeyboardButton(get_text("cancel", lang), callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            get_text("select_color", lang),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Parol kiritish
    if action == "entering_password":
        password = update.message.text.strip()
        folder_id = context.user_data.get("folder_id")
        
        if not folder_id:
            await update.message.reply_text(
                "❌ Xatolik yuz berdi. Qayta boshlang.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        data = load_data()
        folder = data.get(user_id, {}).get("folders", {}).get(folder_id)
        
        if not folder:
            await update.message.reply_text(
                "❌ Papka topilmadi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        if verify_password(password, folder.get("password", "")):
            context.user_data["action"] = None
            await update.message.reply_text(
                "✅ *Parol to'g'ri!*\n\n"
                "Papka ochilmoqda...",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            # Bu yerda papka ichini ko'rsatish kerak, lekin query yo'q
            # Shuning uchun oddiy xabar ko'rsatamiz
            await show_folder_contents_simple(update, context, folder_id, folder)
        else:
            await update.message.reply_text(
                "❌ *Noto'g'ri parol!*\n\n"
                "Qayta urinib ko'ring:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
        return
    
    # Parol qo'yish
    if action == "setting_password":
        password = update.message.text.strip()
        folder_id = context.user_data.get("folder_id")
        
        if len(password) < 4:
            await update.message.reply_text(
                "❌ Parol juda qisqa. Kamida 4 ta belgi kiriting.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        data = load_data()
        if user_id in data and folder_id in data[user_id]["folders"]:
            data[user_id]["folders"][folder_id]["password"] = hash_password(password)
            save_data(data)
            
            context.user_data["action"] = None
            
            await update.message.reply_text(
                "🔒 *Parol qo'yildi!*\n\n"
                "Endi bu papka himoyalangan.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
        else:
            await update.message.reply_text(
                "❌ Xatolik yuz berdi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
        return
    
    # Kontakt telefon raqamini qabul qilish (avval)
    if action == "adding_contact_phone":
        phone = update.message.text.strip()
        
        if len(phone) < 7:
            await update.message.reply_text(
                "❌ Telefon raqami noto'g'ri. Kamida 7 ta raqam kiriting.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        context.user_data["contact_phone"] = phone
        context.user_data["action"] = "adding_contact_name"
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Telefon:* {phone}\n\n"
            f"Endi kontaktga ism bering:\n"
            f"(Masalan: 'Ali', 'Dadam', 'Do'stim')",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Kontakt ismini qabul qilish (keyin)
    if action == "adding_contact_name":
        contact_name = update.message.text.strip()
        
        if len(contact_name) < 2:
            await update.message.reply_text(
                "❌ Ism juda qisqa. Kamida 2 ta belgi kiriting.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        context.user_data["contact_name"] = contact_name
        context.user_data["action"] = "adding_contact_note"
        
        keyboard = [
            [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="skip_contact_note")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Ism:* {contact_name}\n\n"
            f"Izoh qo'shishni xohlaysizmi? (ixtiyoriy)\n"
            f"(Masalan: 'Ishonchi', 'Qarindosh', 'Do'st')",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Kontakt izohini qabul qilish
    if action == "adding_contact_note":
        note = update.message.text.strip()
        await save_contact(update, context, note)
        return
    
    # Eslatma sarlavhasini qabul qilish
    if action == "adding_note_title":
        note_title = update.message.text.strip()
        
        if len(note_title) < 2:
            await update.message.reply_text(
                "❌ Sarlavha juda qisqa. Kamida 2 ta belgi kiriting.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        context.user_data["note_title"] = note_title
        context.user_data["action"] = "adding_note_content"
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Sarlavha:* {note_title}\n\n"
            f"Endi eslatma matnini kiriting:\n"
            f"(Masalan: PIN kod, parol, muhim ma'lumotlar)",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Eslatma matnini qabul qilish va saqlash
    if action == "adding_note_content":
        note_content = update.message.text.strip()
        note_title = context.user_data.get("note_title", "Nomsiz")
        
        if len(note_content) < 1:
            await update.message.reply_text(
                "❌ Eslatma matni bo'sh bo'lishi mumkin emas.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        # Eslatmani saqlash
        user_id = str(update.effective_user.id)
        data = load_data()
        
        if user_id not in data:
            data[user_id] = {"folders": {}, "contacts": {}, "notes": {}, "created_at": datetime.now().isoformat()}
        
        if "notes" not in data[user_id]:
            data[user_id]["notes"] = {}
        
        import uuid
        note_id = str(uuid.uuid4())[:8]
        
        data[user_id]["notes"][note_id] = {
            "title": note_title,
            "content": note_content,
            "created_at": datetime.now().isoformat()
        }
        
        save_data(data)
        
        # Tozalash
        context.user_data.pop("action", None)
        context.user_data.pop("note_title", None)
        
        keyboard = [
            [InlineKeyboardButton("📝 Eslatmalarim", callback_data="my_notes")],
            [InlineKeyboardButton("➕ Yana Eslatma", callback_data="add_note")],
            [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Eslatma saqlandi!*\n\n"
            f"📝 *{note_title}*\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d')}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Link URL qabul qilish
    if action == "adding_link_url":
        link_url = update.message.text.strip()
        
        # URL tekshirish
        if not (link_url.startswith("http://") or link_url.startswith("https://")):
            await update.message.reply_text(
                "❌ Noto'g'ri URL format. URL http:// yoki https:// bilan boshlanishi kerak.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        context.user_data["link_url"] = link_url
        context.user_data["action"] = "adding_link_title"
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "➕ *Yangi Link*\n\n"
            "Link uchun sarlavha kiriting:\n"
            "(Masalan: 'Mening video', 'Instagram post')",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Link sarlavhasi qabul qilish
    if action == "adding_link_title":
        link_title = update.message.text.strip()
        link_url = context.user_data.get("link_url", "")
        
        if len(link_title) < 1:
            link_title = "Nomsiz link"
        
        context.user_data["link_title"] = link_title
        context.user_data["action"] = "adding_link_description"
        
        keyboard = [
            [InlineKeyboardButton("⏭️ O'tkazib yuborish", callback_data="skip_link_description")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "➕ *Yangi Link*\n\n"
            "Link uchun qo'shimcha izoh kiriting (ixtiyoriy):\n"
            "Yoki 'O'tkazib yuborish' tugmasini bosing:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Link izohi qabul qilish va saqlash
    if action == "adding_link_description":
        link_description = update.message.text.strip()
        link_url = context.user_data.get("link_url", "")
        link_title = context.user_data.get("link_title", "Nomsiz link")
        
        # Linkni saqlash
        user_id = str(update.effective_user.id)
        data = load_data()
        
        if user_id not in data:
            data[user_id] = {"folders": {}, "contacts": {}, "notes": {}, "links": {}, "created_at": datetime.now().isoformat()}
        
        if "links" not in data[user_id]:
            data[user_id]["links"] = {}
        
        import uuid
        link_id = str(uuid.uuid4())[:8]
        
        data[user_id]["links"][link_id] = {
            "url": link_url,
            "title": link_title,
            "description": link_description,
            "created_at": datetime.now().isoformat()
        }
        
        save_data(data)
        
        # Tozalash
        context.user_data.pop("action", None)
        context.user_data.pop("link_url", None)
        context.user_data.pop("link_title", None)
        
        keyboard = [
            [InlineKeyboardButton("🔗 Linklarim", callback_data="my_links")],
            [InlineKeyboardButton("➕ Yana Link", callback_data="add_link")],
            [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *Link saqlandi!*\n\n"
            f"🔗 *{link_title}*\n"
            f"📎 {link_url[:50]}...",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Vazifa matnini qabul qilish
    if action == "adding_schedule_task":
        task_text = update.message.text.strip()
        
        if len(task_text) < 1:
            await update.message.reply_text(
                "❌ Vazifa matni bo'sh bo'lishi mumkin emas.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
            )
            return
        
        context.user_data["schedule_task"] = task_text
        context.user_data["action"] = "adding_schedule_time"
        
        keyboard = [[InlineKeyboardButton("❌ Bekor qilish", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            get_text("enter_schedule_time", context.user_data.get("language", "uz")),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Vazifa vaqtini qabul qilish
    if action == "adding_schedule_time":
        time_text = update.message.text.strip()
        
        # Vaqt formatini tekshirish (HH:MM)
        import re
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', time_text):
            await update.message.reply_text(
                "❌ Noto'g'ri vaqt formati. Iltimos, quyidagi formatda yuboring:\n• `09:00`\n• `14:30`\n• `18:45`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]]),
                parse_mode="Markdown"
            )
            return
        
        task_text = context.user_data.get("schedule_task", "Nomsiz vazifa")
        user_id = str(update.effective_user.id)
        data = load_data()
        
        if user_id not in data:
            data[user_id] = {"folders": {}, "contacts": {}, "notes": {}, "schedules": {}, "created_at": datetime.now().isoformat()}
        
        if "schedules" not in data[user_id]:
            data[user_id]["schedules"] = {}
        
        import uuid
        schedule_id = str(uuid.uuid4())[:8]
        
        data[user_id]["schedules"][schedule_id] = {
            "task": task_text,
            "time": time_text,
            "completed": False,
            "created_at": datetime.now().isoformat()
        }
        
        save_data(data)
        
        # Tozalash
        context.user_data.pop("action", None)
        context.user_data.pop("schedule_task", None)
        
        keyboard = [
            [InlineKeyboardButton("📅 Kun Tartibim", callback_data="my_schedule")],
            [InlineKeyboardButton("➕ Yana Vazifa", callback_data="add_schedule")],
            [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            get_text("schedule_added", context.user_data.get("language", "uz")).format(time=time_text, task=task_text),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Default
    await update.message.reply_text(
        "Iltimos, menyudan biror amal tanlang.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
    )


async def show_schedule_list(query, context, user_id):
    """Kun tartibini ko'rsatish"""
    data = load_data()
    user_data = data.get(user_id, {})
    schedules = user_data.get("schedules", {})
    lang = context.user_data.get("language", "uz")
    
    if not schedules:
        keyboard = [
            [InlineKeyboardButton("➕ Vazifa Qo'shish", callback_data="add_schedule")],
            [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            get_text("no_schedules", lang),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Vazifalarni vaqt bo'yicha saralash
    sorted_schedules = sorted(schedules.items(), key=lambda x: x[1].get("time", "00:00"))
    
    # Statistika
    completed = sum(1 for s in schedules.values() if s.get("completed", False))
    missed = sum(1 for s in schedules.values() if s.get("missed", False))
    pending = len(schedules) - completed - missed
    
    text = get_text("schedule_title", lang) + "\n\n"
    
    for schedule_id, schedule in sorted_schedules:
        time = schedule.get("time", "--:--")
        task = schedule.get("task", "Nomsiz")
        
        if schedule.get("completed", False):
            status = "✅"
        elif schedule.get("missed", False):
            status = "❌"
        else:
            status = "⏳"
        
        text += f"{status} `{time}` - {task}\n"
    
    text += f"\n{get_text('schedule_stats', lang).format(completed=completed, missed=missed, pending=pending)}"
    
    keyboard = [
        [InlineKeyboardButton("➕ Vazifa Qo'shish", callback_data="add_schedule")],
        [InlineKeyboardButton("📊 Haftalik Stat", callback_data="weekly_stats")],
        [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def show_weekly_stats(query, context, user_id):
    """Haftalik statistikani ko'rsatish"""
    data = load_data()
    user_data = data.get(user_id, {})
    schedules = user_data.get("schedules", {})
    lang = context.user_data.get("language", "uz")
    
    # Haftaning boshlanish va tugash sanalarini aniqlash
    from datetime import datetime, timedelta
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())  # Dushanba
    week_end = week_start + timedelta(days=6)  # Yakshanba
    
    # Bu haftadagi vazifalarni filtrlash
    week_schedules = {}
    for schedule_id, schedule in schedules.items():
        created_at = schedule.get("created_at", "")
        if created_at:
            try:
                schedule_date = datetime.fromisoformat(created_at)
                if week_start <= schedule_date <= week_end + timedelta(days=1):
                    week_schedules[schedule_id] = schedule
            except:
                pass
    
    if not week_schedules:
        keyboard = [
            [InlineKeyboardButton("📅 Kun Tartibim", callback_data="my_schedule")],
            [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            get_text("no_weekly_stats", lang),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Statistika hisoblash
    completed = sum(1 for s in week_schedules.values() if s.get("completed", False))
    missed = sum(1 for s in week_schedules.values() if s.get("missed", False))
    total = len(week_schedules)
    percentage = round((completed / total) * 100) if total > 0 else 0
    
    week_start_str = week_start.strftime("%d.%m")
    week_end_str = week_end.strftime("%d.%m")
    
    text = get_text("weekly_stats", lang).format(
        week_start=week_start_str,
        week_end=week_end_str,
        completed=completed,
        missed=missed,
        total=total,
        percentage=percentage
    )
    
    keyboard = [
        [InlineKeyboardButton("📅 Kun Tartibim", callback_data="my_schedule")],
        [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def show_my_statistics(query, context, user_id):
    """Foydalanuvchining umumiy statistikasini ko'rsatish"""
    data = load_data()
    user_data = data.get(user_id, {})
    schedules = user_data.get("schedules", {})
    lang = context.user_data.get("language", "uz")
    
    if not schedules:
        keyboard = [
            [InlineKeyboardButton("📅 Kun Tartibim", callback_data="my_schedule")],
            [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📈 *Mening Statistikalarim*\n\nHali vazifalar yo'q. Kun tartibiga o'ting:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Umumiy statistika
    completed = sum(1 for s in schedules.values() if s.get("completed", False))
    missed = sum(1 for s in schedules.values() if s.get("missed", False))
    total = len(schedules)
    percentage = round((completed / total) * 100) if total > 0 else 0
    
    # 1-10 gacha baholash
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
    elif percentage >= 20:
        rating = 3
        rating_text = get_text("rating_poor", lang)
    elif percentage >= 10:
        rating = 2
        rating_text = get_text("rating_poor", lang)
    else:
        rating = 1
        rating_text = get_text("rating_poor", lang)
    
    # Yulduzchalar bilan baho
    stars = "⭐" * rating + "⚫" * (10 - rating)
    
    text = get_text("stats_title", lang) + "\n\n"
    text += get_text("stats_overall", lang).format(
        completed=completed,
        missed=missed,
        total=total
    ) + "\n\n"
    text += get_text("stats_rating", lang).format(
        percentage=percentage,
        rating=stars,
        rating_text=rating_text
    )
    
    keyboard = [
        [InlineKeyboardButton("📅 Kun Tartibim", callback_data="my_schedule")],
        [InlineKeyboardButton("📊 Haftalik Stat", callback_data="weekly_stats")],
        [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def mark_schedule_done(query, context, user_id, schedule_id, completed):
    """Vazifani bajarilgan deb belgilash"""
    data = load_data()
    user_data = data.get(user_id, {})
    schedules = user_data.get("schedules", {})
    lang = context.user_data.get("language", "uz")
    
    if schedule_id in schedules:
        if completed:
            schedules[schedule_id]["completed"] = True
            schedules[schedule_id]["missed"] = False
        else:
            schedules[schedule_id]["completed"] = False
            schedules[schedule_id]["missed"] = True
        
        save_data(data)
    
    # Ro'yxatni qayta ko'rsatish
    await show_schedule_list(query, context, user_id)


async def check_schedules_and_remind(context: ContextTypes.DEFAULT_TYPE):
    """Har daqiqa tekshirib, vazifa vaqtida eslatma yuborish"""
    current_time = datetime.now().strftime("%H:%M")
    data = load_data()
    
    for user_id, user_data in data.items():
        schedules = user_data.get("schedules", {})
        
        for schedule_id, schedule in schedules.items():
            # Faqat bajarilmagan va eslatilmagan vazifalar
            if (schedule.get("time") == current_time and 
                not schedule.get("completed", False) and 
                not schedule.get("missed", False) and
                not schedule.get("reminded", False)):
                
                # Eslatma yuborish
                try:
                    task = schedule.get("task", "Nomsiz vazifa")
                    
                    keyboard = [
                        [InlineKeyboardButton("✅ Ha, bajardim", callback_data=f"schedule_done_{schedule_id}")],
                        [InlineKeyboardButton("❌ Yo'q, bajarmadim", callback_data=f"schedule_missed_{schedule_id}")],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await context.bot.send_message(
                        chat_id=int(user_id),
                        text=get_text("schedule_reminder", "uz").format(task=task),
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                    
                    # Eslatilgan deb belgilash
                    schedule["reminded"] = True
                    save_data(data)
                    
                except Exception as e:
                    print(f"Eslatma yuborishda xatolik (user {user_id}): {e}")


async def show_folder_contents_simple(update, context, folder_id, folder):
    """Papka ichini ko'rsatish (oddiy xabar bilan) - barcha rasmlar/videolar ko'rinadi"""
    files = folder.get("files", [])
    
    keyboard = [
        [InlineKeyboardButton("📤 Fayl yuklash", callback_data=f"upload_to_{folder_id}")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data=f"folder_settings_{folder_id}")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="my_folders")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if not files:
        await update.message.reply_text(
            f"📁 *{folder['name']}*\n\n"
            f"📝 Yaratilgan: {folder.get('created_at', 'Noma\'lum')[:10]}\n"
            f"📂 Fayllar: 0 ta\n\n"
            f"Bu papka bo'sh. Fayl yuklash uchun tugmani bosing:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    # Avval umumiy ma'lumot
    await update.message.reply_text(
        f"📁 *{folder['name']}*\n\n"
        f"📝 Yaratilgan: {folder.get('created_at', 'Noma\'lum')[:10]}\n"
        f"📂 Jami fayllar: {len(files)} ta\n\n"
        f"Fayllar yuborilmoqda...",
        parse_mode="Markdown"
    )
    
    # Barcha fayllarni yuborish (file_id orqali)
    sent_count = 0
    failed_count = 0
    
    for i, file_info in enumerate(files):
        file_id = file_info.get("file_id")
        caption = f"📎 *{file_info['name']}*\n📅 {file_info.get('uploaded_at', file_info.get('date', ''))[:10]}"
        
        try:
            if file_id:
                # file_id orqali yuborish (Telegram serverlarida saqlangan)
                if file_info.get("type") == "photo":
                    await update.message.reply_photo(
                        photo=file_id,
                        caption=caption,
                        parse_mode="Markdown"
                    )
                else:  # video
                    await update.message.reply_video(
                        video=file_id,
                        caption=caption,
                        parse_mode="Markdown"
                    )
                sent_count += 1
            else:
                # Eski fayllar uchun
                failed_count += 1
                print(f"file_id topilmadi: {file_info}")
        except Exception as e:
            failed_count += 1
            print(f"Fayl yuborishda xatolik: {e}")
    
    # Oxirida tugmalar bilan xabar
    if failed_count > 0:
        status_text = f"✅ *Fayllar yuborildi!*\n\n📁 {folder['name']}\n✅ Yuborildi: {sent_count} ta\n❌ Topilmadi: {failed_count} ta"
    else:
        status_text = f"✅ *Barcha fayllar yuborildi!*\n\n📁 {folder['name']} - {sent_count} ta fayl"
    
    await update.message.reply_text(
        status_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rasm qabul qilish"""
    await handle_file(update, context, "photo")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Video qabul qilish"""
    await handle_file(update, context, "video")


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE, file_type):
    """Faylni qayta ishlash - cheksiz yuklash, faqat bitta tugma"""
    action = context.user_data.get("action")
    folder_id = context.user_data.get("upload_folder_id")
    user_id = str(update.effective_user.id)
    
    if action != "uploading_file" or not folder_id:
        await update.message.reply_text(
            "❌ Avval papka tanlang!\n\n"
            "'📤 Fayl Yuklash' tugmasini bosing.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
        )
        return
    
    # Agar bu birinchi fayl bo'lsa, xabar yuborish
    if "upload_count" not in context.user_data:
        context.user_data["upload_count"] = 0
        context.user_data["upload_start_time"] = datetime.now()
        
        keyboard = [[InlineKeyboardButton("✅ Tugatish", callback_data="finish_upload")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📤 *Yuklash boshlandi...*\n\n"
            "Rasmlar/videolaringiz yuklanmoqda.\n"
            "Barchasini yuklab bo'lgach 'Tugatish' tugmasini bosing.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # Faylni olish
    if file_type == "photo":
        file = update.message.photo[-1]  # Eng katta o'lcham
        file_name = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}.jpg"
        default_name = f"Rasm {datetime.now().strftime('%d.%m.%Y')}"
    else:
        file = update.message.video
        file_name = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}.mp4"
        default_name = f"Video {datetime.now().strftime('%d.%m.%Y')}"
    
    # Faylni yuklab olish - faqat file_id saqlanadi (Telegram serverlarida)
    file_id = file.file_id
    
    # Ma'lumotlarni saqlash
    data = load_data()
    if user_id in data and folder_id in data[user_id]["folders"]:
        file_date = datetime.now().strftime("%d.%m.%Y")
        data[user_id]["folders"][folder_id]["files"].append({
            "name": default_name,
            "date": file_date,
            "file_id": file_id,
            "type": file_type,
            "uploaded_at": datetime.now().isoformat()
        })
        save_data(data)
        
        context.user_data["upload_count"] += 1
    else:
        await update.message.reply_text(
            "❌ Papka topilmadi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
        )


async def save_contact_from_callback(query, context):
    """Kontaktni callback dan saqlash (izohsiz)"""
    user_id = str(query.from_user.id)
    contact_name = context.user_data.get("contact_name")
    contact_phone = context.user_data.get("contact_phone")
    
    if not all([contact_name, contact_phone]):
        await query.edit_message_text(
            "❌ Xatolik yuz berdi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
        )
        return
    
    # Kontakt ID yaratish
    contact_id = f"contact_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}"
    
    # Ma'lumotlarni saqlash
    data = load_data()
    if user_id not in data:
        data[user_id] = {"folders": {}, "contacts": {}, "created_at": datetime.now().isoformat()}
    
    if "contacts" not in data[user_id]:
        data[user_id]["contacts"] = {}
    
    data[user_id]["contacts"][contact_id] = {
        "name": contact_name,
        "phone": contact_phone,
        "note": "",
        "created_at": datetime.now().isoformat()
    }
    save_data(data)
    
    # Tozalash
    context.user_data.pop("action", None)
    context.user_data.pop("contact_name", None)
    context.user_data.pop("contact_phone", None)
    
    keyboard = [
        [InlineKeyboardButton("➕ Yana kontakt qo'shish", callback_data="add_contact")],
        [InlineKeyboardButton("📇 Kontaktlarim", callback_data="my_contacts")],
        [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ *Kontakt saqlandi!*\n\n"
        f"👤 Ism: {contact_name}\n"
        f"📱 Telefon: {contact_phone}\n\n"
        f"Xotirangiz xavfsiz saqlandi! 🔐",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def save_contact(update: Update, context: ContextTypes.DEFAULT_TYPE, note=""):
    """Kontaktni saqlash"""
    user_id = str(update.effective_user.id)
    contact_name = context.user_data.get("contact_name")
    contact_phone = context.user_data.get("contact_phone")
    
    if not all([contact_name, contact_phone]):
        await update.message.reply_text(
            "❌ Xatolik yuz berdi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
        )
        return
    
    # Kontakt ID yaratish
    contact_id = f"contact_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}"
    
    # Ma'lumotlarni saqlash
    data = load_data()
    if user_id not in data:
        data[user_id] = {"folders": {}, "contacts": {}, "created_at": datetime.now().isoformat()}
    
    if "contacts" not in data[user_id]:
        data[user_id]["contacts"] = {}
    
    data[user_id]["contacts"][contact_id] = {
        "name": contact_name,
        "phone": contact_phone,
        "note": note,
        "created_at": datetime.now().isoformat()
    }
    save_data(data)
    
    # Tozalash
    context.user_data.pop("action", None)
    context.user_data.pop("contact_name", None)
    context.user_data.pop("contact_phone", None)
    
    keyboard = [
        [InlineKeyboardButton("➕ Yana kontakt qo'shish", callback_data="add_contact")],
        [InlineKeyboardButton("📇 Kontaktlarim", callback_data="my_contacts")],
        [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    contact_text = (
        f"✅ *Kontakt saqlandi!*\n\n"
        f"👤 Ism: {contact_name}\n"
        f"📱 Telefon: {contact_phone}\n"
    )
    if note:
        contact_text += f"📝 Izoh: {note}\n"
    
    await update.message.reply_text(
        contact_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def save_uploaded_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yuklangan faylni saqlash"""
    user_id = str(update.effective_user.id)
    folder_id = context.user_data.get("upload_folder_id")
    file_name = context.user_data.get("file_name", "Nomsiz")
    file_date = context.user_data.get("file_date", datetime.now().strftime("%d.%m.%Y"))
    uploaded_file = context.user_data.get("uploaded_file")
    file_type = context.user_data.get("file_type")
    
    if not all([folder_id, uploaded_file]):
        await update.message.reply_text(
            "❌ Xatolik yuz berdi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
        )
        return
    
    # Ma'lumotlarni saqlash
    data = load_data()
    if user_id in data and folder_id in data[user_id]["folders"]:
        data[user_id]["folders"][folder_id]["files"].append({
            "name": file_name,
            "date": file_date,
            "filename": uploaded_file,
            "type": file_type,
            "uploaded_at": datetime.now().isoformat()
        })
        save_data(data)
        
        # Tozalash
        context.user_data["action"] = None
        context.user_data["upload_folder_id"] = None
        context.user_data["file_name"] = None
        context.user_data["file_date"] = None
        context.user_data["uploaded_file"] = None
        context.user_data["file_type"] = None
        
        keyboard = [
            [InlineKeyboardButton("📤 Yana yuklash", callback_data=f"upload_to_{folder_id}")],
            [InlineKeyboardButton("📁 Papkalarim", callback_data="my_folders")],
            [InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        icon = "🖼️" if file_type == "photo" else "🎥"
        
        await update.message.reply_text(
            f"✅ *Fayl saqlandi!*\n\n"
            f"{icon} Nomi: {file_name}\n"
            f"📅 Sana: {file_date}\n"
            f"📁 Papka: {data[user_id]['folders'][folder_id]['name']}\n\n"
            f"Xotirangiz xavfsiz saqlandi! 🔐",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Papka topilmadi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menu", callback_data="main_menu")]])
        )


# ==================== ASOSIY FUNKSIYA ====================

def main():
    """Botni ishga tushirish"""
    BOT_TOKEN = "8783323415:AAFbaJVTgSi6dUk_TgOgJgGrTVoVXtTlaus"
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )
    
    # Komandalarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))  # Admin statistika
    
    # Rasm va video qabul qilish
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    # Matn xabarlarni qabul qilish
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Chat member yangiliklarini kuzatish (yangi foydalanuvchilar)
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_user))
    
    # Tugma bosishlarni qo'shish
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Har daqiqa vazifalarni tekshirish (JobQueue)
    job_queue = application.job_queue
    job_queue.run_repeating(check_schedules_and_remind, interval=60, first=10)
    
    print("Xotira Vault Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main() 
