# 📋 Memory Vault Bot — Optimizatsiya va Loyiha Holati

Ushbu ro'yxat botdagi xatoliklarni to'liq bartaraf etish (optimizatsiya), yangi qulayliklarni qo'shish va hozirgi kodning zaif nuqtalarini kuzatib borish uchun mo'ljallangan.

### 🛠 Arxitaktura va Optimizatsiya
- [ ] **Ma'lumotlar bazasini o'zgartirish:** Bitta monolitik `JSON` fayldan `aiosqlite` (SQLite) asinxron ma'lumotlar bazasiga o'tish.
- [ ] **Middleware Yaratish:** Kodlarning keraksiz joyda takrorlanishini qisqartirish uchun `UserMiddleware` yozish (til va faollik vaqtini har doim qo'lda chaqirmaslik uchun).
- [ ] **Sahifalash (Pagination) qo'shish:** Papka, Eslatma va Kontaktlarning limitdan ortib ketsa bot ishdan chiqishini olish uchun Pagination qolipini yaratish.

### 🚀 Yangi Qo'shiladigan Funksiyalar
- [ ] **Kengaytirilgan Fayllar:** Bot papkasiga faqat rasm/video emas, balki `document`, `audio`, `voice` fayllarini ham yuklash funksiyasini qo'shish.
- [ ] **Qidiruv Tizimi:** Xabarlar va eslatmalar bo'yicha "Qidiruv (Search)" mexanizmini qo'shish (Sarlavha yoki matn qismi bo'yicha).
- [ ] **Export / Backup:** Foydalanuvchi ma'lumotlarini arxiv (.zip) yoki TXT formatida tashqariga ko'chirib olish imkoniyati.
- [ ] **Admin Broadcast:** Boshqaruvchi barcha bot foydalanuvchilariga bir paytning o'zida post yuborish imkoniyatini (Admin Mailer) qo'shish.

---

### ⚠️ Ayni Paytdagi Asosiy Kamchiliklar (Zaif Nuqtalar)
Hozirgi kodni o'qib chiqqanimdan keyin, loyihada darhol to'g'irlanishi kerak bo'lgan quyidagi muammolar vizualizatsiya qilindi:

1. ❌ **Sinxron Bloklanish (Block Loop):** `json.load()` va `json.dump()` funksiyalari Asinxron muhitni (Aiogram) qotirib qo'yadi. Fayl hajmi kattalashgani sari botingiz sekinlashadi va boshqa foydalanuvchilarga javob bermay qoladi.
2. ❌ **Data Loss Xavfi:** Har safar ma'lumot o'zgarganda faqat yagona JSON fayli qaytadan yozilyabdi. Agar yoza yotganda server uzilsa yoki xatolik ketsa fayl butunlay yo'q qilinib **nolga aylanadi**.
3. ❌ **Pagination (Sahifalash) ning yo'qligi:** Hozirgi darchalarda hamma kontaktlarni bitta betga chiqaryapti. Telegram inline tugmachalari maksimal logik chegaradan yiriklashib ketsa xabar jo'natib bo'lmay qoladi va Crash beradi.
4. ❌ **Dasturiy Kodning Takrori (DRY prinsipiga zid):** Har bitta handlerda `user_id = message.from_user.id`, `get_user(user_id)`, `get_user_lang(user_id)` ketma-ket qaytarilgan. Bu kod o'qilishini buzilishi nafaqat hajmni balki qayta ishlashni sekinlashtiradi.
5. ❌ **Xotira boshqaruvi yo'q:** User papkaga noto'g'ri narsa yuborsa xatolik qaytarish holati ishlanmagan. Exception handling yetishmaydi.
