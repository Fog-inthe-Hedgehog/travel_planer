from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.orm import Session
from app.database.models import User
from app.database.session import get_db

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    # Регистрация пользователя в базе данных
    db = next(get_db())

    user = db.query(User).filter(User.user_id == message.from_user.id).first()
    if not user:
        new_user = User(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        db.add(new_user)
        db.commit()

    welcome_text = """
    🎉 Добро пожаловать в Travel Planner! 🗺️

Я помогу вам планировать ваши поездки:

Основные команды:
/new_trip - Создать новую поездку
/my_trips - Показать мои поездки
/add_task - Добавить задачу для поездки
/weather - Узнать погоду в пункте назначения
/top_location - Показать достопримечательности

Начните с создания вашей первой поездки! ✈️
    """

    await message.answer(welcome_text)