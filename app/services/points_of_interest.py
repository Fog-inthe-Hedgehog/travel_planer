import aiohttp
import requests
from app.config import settings

class PointsOfInterestService:
    def __init__(self):
        self.api_key = settings.AMADEUS_API_KEY
        self.api_secret = settings.AMADEUS_API_SECRET
        self.base_url = "https://test.api.amadeus.com/v1"
        self.access_token = None

    async def _get_access_token(self) -> str:
        """Получение access token для Amadeus API"""
        if self.access_token:
            return self.access_token

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data["access_token"]
                    return self.access_token
                else:
                    raise Exception("Не удалось получить access token")

    async def get_points_of_interest(self, city: str, limit: int = 5) -> list:
        """Получение достопримечательностей для города"""
        try:
            token = await self._get_access_token()

            # Для демонстрации используем mock данные, так как Amadeus API требует геокоординаты
            # В реальном приложении здесь был бы запрос к Amadeus Points of Interest API

            mock_poi = [
                {"name": "Главная площадь", "type": "Площадь", "rating": "4.5"},
                {"name": "Исторический музей", "type": "Музей", "rating": "4.7"},
                {"name": "Городской парк", "type": "Парк", "rating": "4.3"},
                {"name": "Кафедральный собор", "type": "Религиозный памятник", "rating": "4.8"},
                {"name": "Смотровая площадка", "type": "Достопримечательность", "rating": "4.6"}
            ]

            return mock_poi[:limit]

        except Exception as e:
            # Возвращаем mock данные в случае ошибки
            return [
                {"name": "Центральный парк", "type": "Парк", "rating": "4.5"},
                {"name": "Городской музей", "type": "Музей", "rating": "4.3"},
                {"name": "Исторический центр", "type": "Архитектура", "rating": "4.7"}
            ]