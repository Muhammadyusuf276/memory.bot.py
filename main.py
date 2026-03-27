import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from handlers import setup_routers
from handlers.schedule import check_schedules_and_remind

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi! .env faylni tekshiring.")
        return

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Routerlarni ulash
    router = setup_routers()
    dp.include_router(router)

    # Scheduler — har daqiqa vazifalarni tekshirish
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_schedules_and_remind,
        "interval",
        seconds=60,
        args=[bot],
    )
    scheduler.start()

    logger.info("🧠 MemoryBot (aiogram 3) ishga tushdi...")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
