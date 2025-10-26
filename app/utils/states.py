from aiogram.fsm.state import State, StatesGroup

class TripCreation(StatesGroup):
    destination = State()
    start_date = State()
    end_date = State()
    notes = State()

class TaskCreation(StatesGroup):
    trip_selection = State()
    description = State()