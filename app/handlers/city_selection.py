from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from app.utils.states import CitySelection
from app.utils.formatters import (
    format_weather_response,
    format_forecast_response,
    format_poi_response,
)
from app.services.weather import WeatherService
from app.services.points_of_interest import PointsOfInterestService

router = Router()
weather_service = WeatherService()
poi_service = PointsOfInterestService()


@router.message(CitySelection.waiting_city_input)
async def process_city_selection(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mode = data.get("city_mode")

    if mode not in ("weather", "forecast", "poi"):
        return

    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return

    text = message.text.strip()
    if text == "Другой город...":
        await message.answer("Введите название города:")
        return

    city_name = text
    if not city_name:
        await message.answer("Ошибка: не указано название города")
        return

    try:
        if mode == "poi":
            await message.answer(
                f"🏛️ Ищу достопримечательности в {city_name}...",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            result = await poi_service.get_points_of_interest(city_name)
            response = format_poi_response(city_name, result)
        elif mode == "weather":
            await message.answer(
                f"🌤️ Запрашиваю погоду для {city_name}...",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            result = await weather_service.get_current_weather(city_name)
            response = format_weather_response(city_name, result)
        else:
            await message.answer(
                f"🌤️ Запрашиваю прогноз погоды для {city_name}...",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            result = await weather_service.get_weather_forecast(city_name, days=5)
            response = format_forecast_response(city_name, result)

        await message.answer(response)
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке запроса: {str(e)}")
    finally:
        await state.clear()
