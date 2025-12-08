from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.database.session import get_db
from app.repositories import TripRepository
from app.utils.states import CitySelection
from app.utils.formatters import format_weather_response, format_forecast_response
from app.keyboards import build_city_choices_reply
from app.services.weather import WeatherService

router = Router()
weather_service = WeatherService()


async def _start_city_selection(message: types.Message, state: FSMContext, mode: str, prompt: str):
    db_gen = get_db()
    db = next(db_gen)
    try:
        trips = TripRepository(db).list_for_user(message.from_user.id)
        unique_cities = sorted({t.destination for t in trips})
        await state.update_data(city_mode=mode)
        await message.answer(prompt, reply_markup=build_city_choices_reply(unique_cities))
        await state.set_state(CitySelection.waiting_city_input)
    finally:
        db.close()


async def cmd_weather_list(message: types.Message, state: FSMContext):
    if not message.from_user:
        await message.answer("Ошибка: пользователь не найден")
        return

    await _start_city_selection(
        message,
        state,
        mode="weather",
        prompt="Выберите город из ваших поездок или введите название:",
    )


@router.message(CitySelection.waiting_city_input)
async def process_weather_city_selection(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mode = data.get("city_mode")
    print(f"weather mode: {mode}")
    if mode not in ("weather", "forecast"):
        return

    try:
        if not message.text:
            await message.answer("Ошибка: пустое сообщение")
            return

        if message.text.strip() == "Другой город...":
            await message.answer("Введите название города:")
            return

        city_name = message.text.strip()
        if not city_name:
            await message.answer("Ошибка: не указано название города")
            return

        await message.answer(
            f"🌤️ Запрашиваю {'погоду' if mode == 'weather' else 'прогноз'} для {city_name}...",
            reply_markup=types.ReplyKeyboardRemove()
        )

        if mode == "weather":
            result = await weather_service.get_current_weather(city_name)
            response = format_weather_response(city_name, result)
        else:
            result = await weather_service.get_weather_forecast(city_name, days=5)
            response = format_forecast_response(city_name, result)

        await message.answer(response)
        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке запроса: {str(e)}")
        await state.clear()


@router.message(Command("weather"))
async def cmd_weather_with_city(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return

    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await cmd_weather_list(message, state)
        return

    city_name = command_parts[1].strip()
    if not city_name:
        await message.answer("Пожалуйста, укажите название города: /weather Москва")
        return

    await message.answer(f"🌤️ Запрашиваю погоду для {city_name}...")

    try:
        weather_data = await weather_service.get_current_weather(city_name)
        response = format_weather_response(city_name, weather_data)
        await message.answer(response)
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении погоды: {str(e)}")


@router.message(Command("forecast"))
async def cmd_forecast_with_city(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return

    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await _start_city_selection(
            message,
            state,
            mode="forecast",
            prompt="Выберите город из ваших поездок или введите название:",
        )
        return

    city_name = command_parts[1].strip()
    if not city_name:
        await message.answer("Пожалуйста, укажите название города: /forecast Москва")
        return

    await message.answer(f"🌤️ Запрашиваю прогноз погоды для {city_name}...")

    try:
        forecast_data = await weather_service.get_weather_forecast(city_name, days=5)
        response = format_forecast_response(city_name, forecast_data)
        await message.answer(response)
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении прогноза: {str(e)}")
