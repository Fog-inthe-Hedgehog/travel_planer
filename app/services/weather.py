import aiohttp
import time
from app.config import settings

class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self._cache = {}
        self._ttl_seconds = 600

    async def get_current_weather(self, city: str) -> dict:
        try:
            cached = self._cache.get(("current", city.lower()))
            now = time.time()
            if cached and now - cached[0] < self._ttl_seconds:
                return cached[1]
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
                        result = {
                            "temperature": data["main"]["temp"],
                            "description": data["weather"][0]["description"],
                            "humidity": data["main"]["humidity"],
                            "wind_speed": data["wind"]["speed"]
                        }
                        self._cache[("current", city.lower())] = (now, result)
                        return result
                    else:
                        return {"error": "Не удалось получить данные о погоде"}
        except Exception as e:
            return {"error": f"Ошибка при запросе погоды: {str(e)}"}

    async def get_weather_forecast(self, city: str, days: int = 5) -> dict:
        try:
            cached = self._cache.get(("forecast", city.lower(), days))
            now = time.time()
            if cached and now - cached[0] < self._ttl_seconds:
                return cached[1]
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

                        daily_forecasts = []
                        processed_dates = set()

                        for forecast in forecast_list:
                            forecast_date = forecast["dt_txt"].split()[0]
                            forecast_time = forecast["dt_txt"].split()[1]

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

                        result = {"forecast": daily_forecasts}
                        self._cache[("forecast", city.lower(), days)] = (now, result)
                        return result
                    else:
                        return {"error": "Не удалось получить прогноз погоды"}
        except Exception as e:
            return {"error": f"Ошибка при запросе прогноза: {str(e)}"}