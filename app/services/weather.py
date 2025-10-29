import aiohttp
import requests
from app.config import settings

class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5"

    async def get_current_weather(self, city: str) -> dict:
        """Получение текущей погоды для города"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/weather",
                    params={
                        "q": city,
                        "appid": self.api_key,
                        "units": "metric",
                        "lang": "ru"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "temperature": data["main"]["temp"],
                            "description": data["weather"][0]["description"],
                            "humidity": data["main"]["humidity"],
                            "wind_speed": data["wind"]["speed"]
                        }
                    else:
                        return {"error": "Не удалось получить данные о погоде"}
        except Exception as e:
            return {"error": f"Ошибка при запросе погоды: {str(e)}"}

    async def get_weather_forecast(self, city: str, days: int = 5) -> dict:
        """Получение прогноза погоды для города на несколько дней"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/forecast",
                    params={
                        "q": city,
                        "appid": self.api_key,
                        "units": "metric",
                        "lang": "ru"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        forecast_list = data["list"]

                        # Группируем прогноз по дням (берем прогноз на полдень каждого дня)
                        daily_forecasts = []
                        processed_dates = set()

                        for forecast in forecast_list:
                            forecast_date = forecast["dt_txt"].split()[0]  # Получаем дату
                            forecast_time = forecast["dt_txt"].split()[1]  # Получаем время

                            # Берем прогноз на 12:00 (полдень) каждого дня
                            if forecast_time == "12:00:00" and forecast_date not in processed_dates:
                                processed_dates.add(forecast_date)
                                daily_forecasts.append({
                                    "date": forecast_date,
                                    "temperature": forecast["main"]["temp"],
                                    "description": forecast["weather"][0]["description"],
                                    "humidity": forecast["main"]["humidity"],
                                    "wind_speed": forecast["wind"]["speed"]
                                })

                                if len(daily_forecasts) >= days:
                                    break

                        return {"forecast": daily_forecasts}
                    else:
                        return {"error": "Не удалось получить прогноз погоды"}
        except Exception as e:
            return {"error": f"Ошибка при запросе прогноза: {str(e)}"}