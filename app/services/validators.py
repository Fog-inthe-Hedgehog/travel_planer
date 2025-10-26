from datetime import datetime
from pydantic import ValidationError

def validate_date(date_string: str) -> datetime:
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD")

def validate_destination(destination: str) -> str:
    if len(destination.strip()) < 2:
        raise ValueError("Название направления должно содержать минимум 2 символа")
    return destination.strip()