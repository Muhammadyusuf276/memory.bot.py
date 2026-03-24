#!/bin/bash
# AlwaysData da botni ishga tushirish uchun skript
# Username: yusu1f_begimov

echo "=== MemoryVault Bot o'rnatilmoqda ==="

# 1. Papka yaratish
mkdir -p ~/memory_bot
cd ~/memory_bot

# 2. Python kutubxonalarni o'rnatish
echo "Kutubxonalarni o'rnatish..."
pip3 install python-telegram-bot[job-queue] --user

# 3. Bot faylini yaratish (siz faylni FileZilla bilan yuklaysiz)
echo "Bot faylini yuklang: ~/memory_bot/memory_vault_bot.py"

# 4. Botni ishga tushirish
echo "Bot ishga tushirilmoqda..."
python3 ~/memory_bot/memory_vault_bot.py
