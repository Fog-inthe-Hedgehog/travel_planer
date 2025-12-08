from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from app.database.models import Trip
from app.database.session import get_db
from app.utils.states import TaskCreation
from app.repositories import TaskRepository, TripRepository
from app.keyboards import build_trips_reply, build_tasks_inline

router = Router()

@router.message(Command("add_task"))
async def cmd_add_task(message: types.Message, state: FSMContext):
    db = next(get_db())
    trip_repo = TripRepository(db)
    trips = trip_repo.list_for_user(message.from_user.id)

    if not trips:
        await message.answer("У вас пока нет поездок. Создайте первую с помощью /new_trip")
        return

    buttons = [f"{trip.trip_id}: {trip.destination}" for trip in trips]
    await message.answer("Выберите поездку для добавления задачи:", reply_markup=build_trips_reply(buttons))
    await state.set_state(TaskCreation.trip_selection)

@router.message(TaskCreation.trip_selection)
async def process_trip_selection(message: types.Message, state: FSMContext):
    try:
        trip_id = int(message.text.split(":")[0])
        await state.update_data(trip_id=trip_id)
        await message.answer(
            "Введите описание задачи:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(TaskCreation.description)
    except (ValueError, IndexError):
        await message.answer("Пожалуйста, выберите поездку из предложенного списка")

@router.message(TaskCreation.description)
async def process_task_description(message: types.Message, state: FSMContext):
    data = await state.get_data()

    db = next(get_db())
    task_repo = TaskRepository(db)
    task_repo.create(trip_id=data['trip_id'], description=message.text)

    await message.answer(f"✅ Задача добавлена: {message.text}")
    await state.clear()

@router.message(Command("tasks"))
async def cmd_show_tasks(message: types.Message):
    db = next(get_db())
    trip_repo = TripRepository(db)
    task_repo = TaskRepository(db)

    trips = trip_repo.list_for_user(message.from_user.id)
    if not trips:
        await message.answer("У вас пока нет поездок.")
        return

    for trip in trips:
        tasks = task_repo.list_for_trip(trip.trip_id)
        if not tasks:
            continue
        kb = build_tasks_inline([(t.task_id, t.description, t.is_completed) for t in tasks])
        await message.answer(f"📍 {trip.destination}", reply_markup=kb)


@router.callback_query(F.data.startswith("task:"))
async def process_task_action(callback: types.CallbackQuery):
    action, entity, task_id_str = callback.data.split(":")
    task_id = int(task_id_str)
    db = next(get_db())
    task_repo = TaskRepository(db)
    if entity == "toggle":
        ok = task_repo.toggle_complete(task_id)
        await callback.answer("Готово" if ok else "Не найдено", show_alert=not ok)
    elif entity == "delete":
        ok = task_repo.delete(task_id)
        if ok and callback.message:
            await callback.message.delete()
        else:
            await callback.answer("Не удалось удалить", show_alert=True)