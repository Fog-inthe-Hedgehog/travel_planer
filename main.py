import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.handlers.start import router as start_router
from app.handlers.trips import router as trips_router
from app.handlers.tasks import router as tasks_router
from app.handlers.weather_poi import router as weather_poi_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    if not settings.BOT_TOKEN:
        logging.error("BOT_TOKEN not found in environment variables")
        return

    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(start_router)
    dp.include_router(trips_router)
    dp.include_router(tasks_router)
    dp.include_router(weather_poi_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())