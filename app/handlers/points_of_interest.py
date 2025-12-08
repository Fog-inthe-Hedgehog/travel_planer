from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.database.session import get_db
from app.repositories import TripRepository
from app.utils.states import CitySelection
from app.utils.formatters import format_poi_response
from app.keyboards import build_city_choices_reply
from app.services.points_of_interest import PointsOfInterestService

router = Router()
poi_service = PointsOfInterestService()


async def _start_city_selection(message: types.Message, state: FSMContext, prompt: str):
    db_gen = get_db()
    db = next(db_gen)
    try:
        trips = TripRepository(db).list_for_user(message.from_user.id)
        unique_cities = sorted({t.destination for t in trips})
        await state.update_data(city_mode="poi")
        await message.answer(prompt, reply_markup=build_city_choices_reply(unique_cities))
        await state.set_state(CitySelection.waiting_city_input)
    finally:
        db.close()


async def cmd_top_location_list(message: types.Message, state: FSMContext):
    if not message.from_user:
        await message.answer("Ошибка: пользователь не найден")
        return

    await _start_city_selection(
        message,
        state,
        prompt="Выберите город из ваших поездок или введите название:",
    )


@router.message(Command("top_location"))
async def cmd_top_location_with_city(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return

    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await cmd_top_location_list(message, state)
        return

    city_name = command_parts[1].strip()
    if not city_name:
        await message.answer("Пожалуйста, укажите название города: /top_location Москва")
        return

    await message.answer(f"🏛️ Ищу достопримечательности в {city_name}...")

    try:
        poi_data = await poi_service.get_points_of_interest(city_name)
        response = format_poi_response(city_name, poi_data)
        await message.answer(response)
    except Exception as e:
        await message.answer(f"❌ Ошибка при поиске достопримечательностей: {str(e)}")
