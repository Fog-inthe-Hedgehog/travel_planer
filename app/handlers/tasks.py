from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from app.database.models import Trip, Task
from app.database.session import get_db
from app.utils.states import TaskCreation

router = Router()

@router.message(Command("add_task"))
async def cmd_add_task(message: types.Message, state: FSMContext):
    db = next(get_db())
    trips = db.query(Trip).filter(Trip.user_id == message.from_user.id).all()

    if not trips:
        await message.answer("У вас пока нет поездок. Создайте первую с помощью /new_trip")
        return

    # Создаем клавиатуру с поездками
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()

    for trip in trips:
        builder.add(types.KeyboardButton(text=f"{trip.trip_id}: {trip.destination}"))

    builder.adjust(1)

    await message.answer(
        "Выберите поездку для добавления задачи:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
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
    new_task = Task(
        trip_id=data['trip_id'],
        description=message.text
    )

    db.add(new_task)
    db.commit()

    await message.answer(f"✅ Задача добавлена: {message.text}")
    await state.clear()

@router.message(Command("tasks"))
async def cmd_show_tasks(message: types.Message):
    db = next(get_db())

    # Получаем поездки пользователя с задачами
    trips = db.query(Trip).filter(Trip.user_id == message.from_user.id).all()

    if not trips:
        await message.answer("У вас пока нет поездок.")
        return

    response = "📋 Ваши задачи:\n\n"

    for trip in trips:
        tasks = db.query(Task).filter(Task.trip_id == trip.trip_id).all()
        if tasks:
            response += f"📍 {trip.destination}:\n"
            for task in tasks:
                status = "✅" if task.is_completed else "⏳"
                response += f"{status} {task.description}\n"
            response += "\n"

    if response == "📋 Ваши задачи:\n\n":
        response = "У вас пока нет задач. Добавьте их с помощью /add_task"

    await message.answer(response)