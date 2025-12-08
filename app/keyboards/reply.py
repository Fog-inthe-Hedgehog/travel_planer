from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def build_trips_reply(trip_buttons: list[str]) -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for text in trip_buttons:
        builder.add(types.KeyboardButton(text=text))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def build_city_choices_reply(cities: list[str], include_other: bool = True) -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for city in cities:
        builder.add(types.KeyboardButton(text=city))
    if include_other:
        builder.add(types.KeyboardButton(text="Другой город..."))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
