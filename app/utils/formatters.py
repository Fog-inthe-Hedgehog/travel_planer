from datetime import datetime


def format_date_iso_to_dd_mm_yyyy(date_str: str) -> str:
    date_parts = date_str.split("-")
    if len(date_parts) == 3:
        return f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
    return date_str


def format_weather_response(city: str, weather_data: dict) -> str:
    if "error" in weather_data:
        return f"❌ Не удалось получить погоду для {city}"

    return (
        f"🌤️ Погода в {city}:\n\n"
        f"🌡️ Температура: {weather_data['temperature']}°C\n"
        f"📝 Описание: {weather_data['description']}\n"
        f"💧 Влажность: {weather_data['humidity']}%\n"
        f"💨 Скорость ветра: {weather_data['wind_speed']} м/с"
    )


def format_forecast_response(city: str, forecast_data: dict) -> str:
    if "error" in forecast_data:
        return f"❌ Не удалось получить прогноз для {city}"

    response = f"🌤️ Прогноз погоды в {city} на 5 дней:\n\n"
    for day in forecast_data.get("forecast", []):
        formatted_date = format_date_iso_to_dd_mm_yyyy(day["date"])
        response += (
            f"📅 {formatted_date}:\n"
            f"🌡️ Температура: {day['temperature']}°C\n"
            f"📝 Описание: {day['description']}\n"
            f"💧 Влажность: {day['humidity']}%\n"
            f"💨 Ветер: {day['wind_speed']} м/с\n\n"
        )
    return response


def format_poi_response(city: str, poi_data: list) -> str:
    if not poi_data:
        return f"❌ Не удалось найти достопримечательности для {city}"

    response = f"🏛️ Достопримечательности в {city}:\n\n"
    for i, poi in enumerate(poi_data, 1):
        response += f"{i}. {poi['name']}\n"
        response += f"   Тип: {poi['type']}\n"
        response += f"   Рейтинг: {poi['rating']}/5\n\n"
    return response
