import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from app.config import settings
from app.handlers.start import router as start_router
from app.handlers.common import router as common_router
from app.handlers.trips import router as trips_router
from app.handlers.tasks import router as tasks_router
from app.handlers.weather import router as weather_router
from app.handlers.points_of_interest import router as poi_router
from app.handlers.city_selection import router as city_selection_router

logging.basicConfig(level=logging.INFO)

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="new_trip", description="🏝️ Создать новую поездку"),
        BotCommand(command="my_trips", description="🗺️ Мои поездки"),
        BotCommand(command="add_task", description="📋 Добавить задачу"),
        BotCommand(command="tasks", description="✅ Мои задачи"),
        BotCommand(command="weather", description="🌤️ Текущая погода"),
        BotCommand(command="forecast", description="📅 Прогноз погоды"),
        BotCommand(command="top_location", description="🏛️ Достопримечательности"),
    ]

    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

async def main():
    if not settings.BOT_TOKEN:
        logging.error("BOT_TOKEN not found in environment variables")
        return

    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await set_bot_commands(bot)

    dp.include_router(start_router)
    dp.include_router(common_router)
    dp.include_router(trips_router)
    dp.include_router(tasks_router)
    dp.include_router(city_selection_router)
    dp.include_router(weather_router)
    dp.include_router(poi_router)

    logging.info("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())