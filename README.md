# 🧠 Memory Vault Bot

Memory Vault Bot — bu foydalanuvchilarning shaxsiy rasm, video, kontakt, eslatma va linklarini xavfsiz saqlab beruvchi hamda kun tartibini nazorat qilib, eslatmalar yuboradigan ko'p tarmoqli Telegram bot. 

Bot **aiogram 3** freymvorkiga to'liq o'tkazilgan va zamonaviy arxitektura (FSM, Routers, APScheduler) yordamida qurilgan.

## ✨ Imkoniyatlar

*   **📁 Papkalar**: Papka yaratish, rang va parol bilan himoyalash, rasm va videolarni yuklash.
*   **📇 Kontaktlar**: Kontaktlarni qulay saqlash va boshqarish.
*   **📝 Eslatmalar**: Muhim ma'lumotlarni saqlash.
*   **🔗 Linklar**: Kerakli havolalarni saqlash va guruhlash.
*   **📅 Kun tartibi**: Vazifalar belgilash, belgilangan vaqtda bot tomonidan eslatmalar olish (APScheduler orqali).
*   **📊 Statistika**: Bajarilgan va qoldirilgan vazifalar statistikasi, admin uchun umumiy bot statistikasi.
*   **🌐 Ko'p tilli**: O'zbek, Rus va Qozoq tillarini qo'llab-quvvatlaydi.

## 🛠 Texnologiyalar

*   Python 3.10+
*   [aiogram 3.x](https://docs.aiogram.dev/en/latest/) 
*   [APScheduler](https://apscheduler.readthedocs.io/en/3.x/)
*   Foydalanuvchi ma'lumotlar bazasi sifatida JSON (kelajakda SQLite/PostgreSQL ga o'tkazish mumkin).

## 🚀 O'rnatish tartibi

### 1-qadam. Loyihani yuklab oling
```bash
git clone https://github.com/SizningUsername/memory_vault_bot.git
cd memory_vault_bot
```

### 2-qadam. Virtual muhit (Virtual environment) yaratish
```bash
python -m venv venv
# Windows uchun:
venv\Scripts\activate
# Linux/Mac uchun:
source venv/bin/activate
```

### 3-qadam. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4-qadam. Sozlamalar (`.env`)
Loyiha papkasida `.env` nomli fayl yarating va uning ichiga quyidagi ma'lumotlarni yozing:
```env
BOT_TOKEN=Sizning_Bot_Tokeningiz_Shu_Yerda
ADMIN_ID=Sizning_Telegram_IDingiz
```

*(Bot tokenini [@BotFather](https://t.me/botfather) dan olishingiz mumkin)*

### 5-qadam. Botni ishga tushirish
```bash
python bot.py
```

## 📂 Loyiha Strukturasi

```
memory_vault_bot/
├── bot.py              # Asosiy ishga tushirish fayli
├── config.py           # .env dan o'zgaruvchilarni yuklash
├── states.py           # aiogram FSM holatlari (States)
├── database/           # Ma'lumotlar ombori (JSON bilan ishlash)
├── handlers/           # Barcha komanda va tugmalar (Routers)
├── keyboards/          # Inline tugmalar to'plami
├── locales/            # JSON formatidagi tarjima fayllari
├── utils/              # Yordamchi funksiyalar (Parol xeshlash)
└── memory_vault_data.json # Foydalanuvchi ma'lumotlari (avto-yaratiladi)
```

## 🔒 Xavfsizlik bo'yicha ogohlantirish
- Foydalanuvchi parollari **SHA-256** hash orqali saqlanadi.
- Hech qachon `.env` faylini ommaviy omborga (GitHub public repo) yuklamang. Loyihada allaqachon `.gitignore` bunga yo'l qo'ymaslik uchun sozlangan.

## 👨‍💻 Muallif
Ushbu loyiha yuzasidan savollar yoki takliflar bo'lsa, PR (Pull Request) yoki fayllarda yozib qoldirishingiz mumkin.
