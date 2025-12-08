from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types


def build_trips_inline(trips: list[tuple[int, str]]) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for trip_id, destination in trips:
        builder.row(
            types.InlineKeyboardButton(text=f"📍 {destination}", callback_data=f"trip:view:{trip_id}"),
        )
        builder.row(
            types.InlineKeyboardButton(text="📋 Задачи", callback_data=f"trip:tasks:{trip_id}"),
            types.InlineKeyboardButton(text="🗑 Удалить", callback_data=f"trip:delete:{trip_id}"),
        )
    return builder.as_markup()


def build_tasks_inline(tasks: list[tuple[int, str, bool]]) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task_id, description, is_completed in tasks:
        status = "✅" if is_completed else "⬜"
        builder.row(
            types.InlineKeyboardButton(text=f"{status} {description}", callback_data=f"task:toggle:{task_id}"),
            types.InlineKeyboardButton(text="🗑", callback_data=f"task:delete:{task_id}"),
        )
    return builder.as_markup()
