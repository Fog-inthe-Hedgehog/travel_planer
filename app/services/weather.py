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