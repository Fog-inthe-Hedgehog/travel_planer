from aiogram import F, Router, types
from aiogram.filters import Command
from sqlalchemy.orm import Session

from app.database.models import Trip
from app.database.session import get_db
from app.services.weather import WeatherService
from app.services.points_of_interest import PointsOfInterestService

router = Router()
weather_service = WeatherService()
poi_service = PointsOfInterestService()

@router.message(Command("weather"))
async def cmd_weather(message: types.Message):
    db = next(get_db())
    trips = db.query(Trip).filter(Trip.user_id == message.from_user.id).all()

    if not trips:
        await message.answer("У вас пока нет поездок.")
        return

    # Создаем клавиатуру с поездками
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()

    for trip in trips:
        builder.add(types.KeyboardButton(text=f"Weather:{trip.trip_id}"))

    builder.adjust(2)

    await message.answer(
        "Выберите поездку для просмотра погоды:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@router.message(F.text.startswith("Weather:"))
async def process_weather_request(message: types.Message):
    try:
        trip_id = int(message.text.split(":")[1])
        db = next(get_db())
        trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()

        if not trip:
            await message.answer("Поездка не найдена.")
            return

        await message.answer(f"🌤️ Запрашиваю погоду для {trip.destination}...")

        weather_data = await weather_service.get_current_weather(trip.destination)

        if "error" in weather_data:
            response = f"❌ Не удалось получить погоду для {trip.destination}"
        else:
            response = (
                f"🌤️ Погода в {trip.destination}:\n\n"
                f"🌡️ Температура: {weather_data['temperature']}°C\n"
                f"📝 Описание: {weather_data['description']}\n"
                f"💧 Влажность: {weather_data['humidity']}%\n"
                f"💨 Скорость ветра: {weather_data['wind_speed']} м/с"
            )

        await message.answer(response, reply_markup=types.ReplyKeyboardRemove())

    except (ValueError, IndexError):
        await message.answer("Ошибка при обработке запроса")

@router.message(Command("top_location"))
async def cmd_top_location(message: types.Message):
    db = next(get_db())
    trips = db.query(Trip).filter(Trip.user_id == message.from_user.id).all()

    if not trips:
        await message.answer("У вас пока нет поездок.")
        return

    # Создаем клавиатуру с поездками
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()

    for trip in trips:
        builder.add(types.KeyboardButton(text=f"POI:{trip.trip_id}"))

    builder.adjust(2)

    await message.answer(
        "Выберите поездку для просмотра достопримечательностей:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@router.message(F.text.startswith("POI:"))
async def process_poi_request(message: types.Message):
    try:
        trip_id = int(message.text.split(":")[1])
        db = next(get_db())
        trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()

        if not trip:
            await message.answer("Поездка не найдена.")
            return

        await message.answer(f"🏛️ Ищу достопримечательности в {trip.destination}...")

        poi_data = await poi_service.get_points_of_interest(trip.destination)

        response = f"🏛️ Достопримечательности в {trip.destination}:\n\n"
        for i, poi in enumerate(poi_data, 1):
            response += f"{i}. {poi['name']}\n"
            response += f"   Тип: {poi['type']}\n"
            response += f"   Рейтинг: {poi['rating']}/5\n\n"

        await message.answer(response, reply_markup=types.ReplyKeyboardRemove())

    except (ValueError, IndexError):
        await message.answer("Ошибка при обработке запроса")