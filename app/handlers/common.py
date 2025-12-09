from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

router = Router()


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=types.ReplyKeyboardRemove())


@router.errors()
async def errors_handler(event, data):
    message = getattr(event.update, "message", None)
    if message:
        await message.answer("⚠️ Произошла ошибка. Попробуйте еще раз позже.")
    return True
