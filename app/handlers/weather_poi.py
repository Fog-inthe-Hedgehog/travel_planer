from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
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

async def cmd_top_location_list(message: types.Message):
    if not message.from_user:
        await message.answer("Ошибка: пользователь не найден")
        return

    db = next(get_db())
    trips = db.query(Trip).filter(Trip.user_id == message.from_user.id).all()

    if not trips:
        await message.answer(
            "У вас пока нет поездок.\n\n"
            "Вы можете:\n"
            "• Создать поездку с помощью /new_trip\n"
            "• Или ввести название города: /top_location Москва"
        )
        return

    # Создаем клавиатуру с названиями городов
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()

    # Добавляем уникальные города из поездок
    unique_cities = set()
    for trip in trips:
        if trip.destination not in unique_cities:
            unique_cities.add(trip.destination)
            builder.add(types.KeyboardButton(text=f"POI:{trip.destination}"))

    builder.adjust(2)

    await message.answer(
        "Выберите город для просмотра достопримечательностей:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@router.message(F.text.startswith("POI:"))
async def process_poi_request(message: types.Message):
    try:
        if not message.text:
            await message.answer("Ошибка: пустое сообщение")
            return

        city_name = message.text.split(":", 1)[1].strip()

        if not city_name:
            await message.answer("Ошибка: не указано название города")
            return

        await message.answer(f"🏛️ Ищу достопримечательности в {city_name}...")

        poi_data = await poi_service.get_points_of_interest(city_name)

        if not poi_data:
            await message.answer(f"❌ Не удалось найти достопримечательности для {city_name}")
            return

        response = f"🏛️ Достопримечательности в {city_name}:\n\n"
        for i, poi in enumerate(poi_data, 1):
            response += f"{i}. {poi['name']}\n"
            response += f"   Тип: {poi['type']}\n"
            response += f"   Рейтинг: {poi['rating']}/5\n\n"

        await message.answer(response, reply_markup=types.ReplyKeyboardRemove())

    except (ValueError, IndexError):
        await message.answer("Ошибка при обработке запроса")

@router.message(Command("top_location"))
async def cmd_top_location_with_city(message: types.Message):
    """Обработчик команды /top_location с названием города"""
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return

    # Извлекаем название города из команды
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        # Если город не указан, показываем список городов из поездок
        await cmd_top_location_list(message)
        return

    city_name = command_parts[1].strip()

    if not city_name:
        await message.answer("Пожалуйста, укажите название города: /top_location Москва")
        return

    await message.answer(f"🏛️ Ищу достопримечательности в {city_name}...")

    try:
        poi_data = await poi_service.get_points_of_interest(city_name)

        if not poi_data:
            await message.answer(f"❌ Не удалось найти достопримечательности для {city_name}")
            return

        response = f"🏛️ Достопримечательности в {city_name}:\n\n"
        for i, poi in enumerate(poi_data, 1):
            response += f"{i}. {poi['name']}\n"
            response += f"   Тип: {poi['type']}\n"
            response += f"   Рейтинг: {poi['rating']}/5\n\n"

        await message.answer(response)

    except Exception as e:
        await message.answer(f"❌ Ошибка при поиске достопримечательностей: {str(e)}")