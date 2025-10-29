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

async def cmd_weather_list(message: types.Message):
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
            "• Или ввести название города: /weather Москва"
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
            builder.add(types.KeyboardButton(text=f"Weather:{trip.destination}"))

    builder.adjust(2)

    await message.answer(
        "Выберите город для просмотра погоды:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@router.message(F.text.startswith("Weather:"))
async def process_weather_request(message: types.Message):
    try:
        if not message.text:
            await message.answer("Ошибка: пустое сообщение")
            return

        city_name = message.text.split(":", 1)[1].strip()

        if not city_name:
            await message.answer("Ошибка: не указано название города")
            return

        await message.answer(f"🌤️ Запрашиваю погоду для {city_name}...")

        weather_data = await weather_service.get_current_weather(city_name)

        if "error" in weather_data:
            response = f"❌ Не удалось получить погоду для {city_name}"
        else:
            response = (
                f"🌤️ Погода в {city_name}:\n\n"
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

@router.message(Command("weather"))
async def cmd_weather_with_city(message: types.Message):
    """Обработчик команды /weather с названием города"""
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return

    # Извлекаем название города из команды
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        # Если город не указан, показываем список городов из поездок
        await cmd_weather_list(message)
        return

    city_name = command_parts[1].strip()

    if not city_name:
        await message.answer("Пожалуйста, укажите название города: /weather Москва")
        return

    await message.answer(f"🌤️ Запрашиваю погоду для {city_name}...")

    try:
        weather_data = await weather_service.get_current_weather(city_name)

        if "error" in weather_data:
            response = f"❌ Не удалось получить погоду для {city_name}"
        else:
            response = (
                f"🌤️ Погода в {city_name}:\n\n"
                f"🌡️ Температура: {weather_data['temperature']}°C\n"
                f"📝 Описание: {weather_data['description']}\n"
                f"💧 Влажность: {weather_data['humidity']}%\n"
                f"💨 Скорость ветра: {weather_data['wind_speed']} м/с"
            )

        await message.answer(response)

    except Exception as e:
        await message.answer(f"❌ Ошибка при получении погоды: {str(e)}")

@router.message(Command("forecast"))
async def cmd_forecast_with_city(message: types.Message):
    """Обработчик команды /forecast с названием города"""
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return

    # Извлекаем название города из команды
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.answer("Пожалуйста, укажите название города: /forecast Москва")
        return

    city_name = command_parts[1].strip()

    if not city_name:
        await message.answer("Пожалуйста, укажите название города: /forecast Москва")
        return

    await message.answer(f"🌤️ Запрашиваю прогноз погоды для {city_name}...")

    try:
        forecast_data = await weather_service.get_weather_forecast(city_name, days=5)

        if "error" in forecast_data:
            response = f"❌ Не удалось получить прогноз для {city_name}"
        else:
            response = f"🌤️ Прогноз погоды в {city_name} на 5 дней:\n\n"

            for i, day in enumerate(forecast_data["forecast"], 1):
                # Форматируем дату
                date_parts = day["date"].split("-")
                formatted_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"

                response += f"📅 {formatted_date}:\n"
                response += f"🌡️ Температура: {day['temperature']}°C\n"
                response += f"📝 Описание: {day['description']}\n"
                response += f"💧 Влажность: {day['humidity']}%\n"
                response += f"💨 Ветер: {day['wind_speed']} м/с\n\n"

        await message.answer(response)

    except Exception as e:
        await message.answer(f"❌ Ошибка при получении прогноза: {str(e)}")