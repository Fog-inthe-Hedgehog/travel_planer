from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.session import get_db
from app.utils.states import TripCreation
from app.services.validators import validate_date, validate_destination
from app.repositories import TripRepository
from app.keyboards import build_trips_inline

router = Router()

@router.message(Command("new_trip"))
async def cmd_new_trip(message: types.Message, state: FSMContext):
    await message.answer(
        "🏝️ Давайте создадим новую поездку!\n\n"
        "Введите направление (город или страна):\n"
        "Команда /cancel — чтобы прервать создание."
    )
    await state.set_state(TripCreation.destination)

@router.message(TripCreation.destination)
async def process_destination(message: types.Message, state: FSMContext):
    try:
        destination = validate_destination(message.text)
        await state.update_data(destination=destination)
        await message.answer("📅 Введите дату начала поездки (в формате ДД.ММ.ГГГГ):")
        await state.set_state(TripCreation.start_date)
    except ValueError as e:
        await message.answer(str(e))

@router.message(TripCreation.start_date)
async def process_start_date(message: types.Message, state: FSMContext):
    try:
        start_date = validate_date(message.text)
        await state.update_data(start_date=start_date)
        await message.answer("📅 Введите дату окончания поездки (в формате ДД.ММ.ГГГГ):")
        await state.set_state(TripCreation.end_date)
    except ValueError as e:
        await message.answer(str(e))

@router.message(TripCreation.end_date)
async def process_end_date(message: types.Message, state: FSMContext):
    try:
        end_date = validate_date(message.text)
        data = await state.get_data()
        start_date = data['start_date']

        if end_date < start_date:
            await message.answer("❌ Дата окончания должна быть позже или равна дате начала!")
            return

        await state.update_data(end_date=end_date)
        await message.answer("📝 Хотите добавить заметки к поездке? (Если нет, отправьте '-'):")
        await state.set_state(TripCreation.notes)
    except ValueError as e:
        await message.answer(str(e))

@router.message(TripCreation.notes)
async def process_notes(message: types.Message, state: FSMContext):
    data = await state.get_data()
    notes = message.text if message.text != '-' else None

    db = next(get_db())
    trip_repo = TripRepository(db)
    trip = trip_repo.create(
        user_id=message.from_user.id,
        destination=data['destination'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        notes=notes,
    )

    await message.answer(
        f"✅ Поездка создана!\n\n"
        f"📍 Направление: {data['destination']}\n"
        f"📅 С: {data['start_date'].strftime('%d.%m.%Y')}\n"
        f"📅 По: {data['end_date'].strftime('%d.%m.%Y')}\n"
        f"📝 Заметки: {notes if notes else 'нет'}"
    )

    await state.clear()

@router.message(Command("my_trips"))
async def cmd_my_trips(message: types.Message):
    db = next(get_db())
    trip_repo = TripRepository(db)
    trips = trip_repo.list_for_user(message.from_user.id)

    if not trips:
        await message.answer("У вас пока нет поездок. Создайте первую с помощью /new_trip")
        return

    kb = build_trips_inline([(t.trip_id, t.destination) for t in trips])
    await message.answer("🗺️ Ваши поездки:", reply_markup=kb)


@router.callback_query(F.data.startswith("trip:"))
async def process_trip_action(callback: types.CallbackQuery):
    action, entity, trip_id_str = callback.data.split(":")
    trip_id = int(trip_id_str)
    db = next(get_db())
    trip_repo = TripRepository(db)

    if entity == "delete":
        ok = trip_repo.delete(trip_id)
        if ok:
            await callback.message.edit_text("🗑 Поездка удалена.")
        else:
            await callback.answer("Не удалось удалить", show_alert=True)
    elif entity == "tasks":
        await callback.message.answer("Откройте задачи командой /tasks")
        await callback.answer()
    else:
        await callback.answer()