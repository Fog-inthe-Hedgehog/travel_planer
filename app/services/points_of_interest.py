import aiohttp
import requests
from app.config import settings

class PointsOfInterestService:
    def __init__(self):
        self.amadeus_api_key = settings.AMADEUS_API_KEY
        self.amadeus_api_secret = settings.AMADEUS_API_SECRET
        self.foursquare_api_key = settings.FOURSQUARE_API_KEY
        self.opentripmap_api_key = settings.OPENTRIPMAP_API_KEY
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
                    "client_id": self.amadeus_api_key,
                    "client_secret": self.amadeus_api_secret
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
            # Используем Foursquare API для получения POI
            poi_data = await self._get_poi_from_foursquare(city, limit)
            if poi_data:
                return poi_data

            # Fallback к OpenTripMap API
            poi_data = await self._get_poi_from_opentripmap(city, limit)
            if poi_data:
                return poi_data

            # Если все API недоступны, возвращаем mock данные
            return self._get_mock_poi(city, limit)

        except Exception as e:
            print(f"Ошибка при получении POI: {e}")
            return self._get_mock_poi(city, limit)

    async def _get_poi_from_foursquare(self, city: str, limit: int) -> list:
        """Получение POI через Foursquare API"""
        try:
            # Используем бесплатный Foursquare API
            url = "https://api.foursquare.com/v3/places/search"
            headers = {
                "Accept": "application/json",
                "Authorization": f"fsq3{self.foursquare_api_key}" if self.foursquare_api_key else None
            }

            if not self.foursquare_api_key:
                return None
            params = {
                "query": "tourist attractions",
                "near": city,
                "limit": limit,
                "categories": "16000"  # Туристические достопримечательности
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        poi_list = []
                        for place in data.get("results", [])[:limit]:
                            poi_list.append({
                                "name": place.get("name", "Неизвестное место"),
                                "type": place.get("categories", [{}])[0].get("name", "Достопримечательность"),
                                "rating": str(place.get("rating", "4.0"))
                            })
                        return poi_list
        except Exception as e:
            print(f"Ошибка Foursquare API: {e}")
            return None

    async def _get_poi_from_opentripmap(self, city: str, limit: int) -> list:
        """Получение POI через OpenTripMap API"""
        try:
            # Сначала получаем координаты города
            geocode_url = "https://api.opentripmap.com/0.1/en/places/geoname"
            if not self.opentripmap_api_key:
                return None

            geocode_params = {
                "name": city,
                "apikey": self.opentripmap_api_key
            }

            async with aiohttp.ClientSession() as session:
                # Получаем координаты города
                async with session.get(geocode_url, params=geocode_params) as response:
                    if response.status == 200:
                        geocode_data = await response.json()
                        if geocode_data:
                            lat = geocode_data.get("lat")
                            lon = geocode_data.get("lon")

                            # Получаем POI для координат
                            poi_url = "https://api.opentripmap.com/0.1/en/places/radius"
                            poi_params = {
                                "radius": 10000,  # 10km радиус
                                "lon": lon,
                                "lat": lat,
                                "kinds": "interesting_places",
                                "limit": limit,
                                "apikey": self.opentripmap_api_key
                            }

                            async with session.get(poi_url, params=poi_params) as poi_response:
                                if poi_response.status == 200:
                                    poi_data = await poi_response.json()
                                    poi_list = []
                                    for place in poi_data.get("features", [])[:limit]:
                                        properties = place.get("properties", {})
                                        poi_list.append({
                                            "name": properties.get("name", "Неизвестное место"),
                                            "type": properties.get("kinds", "Достопримечательность").split(",")[0],
                                            "rating": "4.0"  # OpenTripMap не предоставляет рейтинги
                                        })
                                    return poi_list
        except Exception as e:
            print(f"Ошибка OpenTripMap API: {e}")
            return None

    def _get_mock_poi(self, city: str, limit: int) -> list:
        """Возвращает mock данные о достопримечательностях"""
        mock_poi = [
            {"name": f"Главная площадь {city}", "type": "Площадь", "rating": "4.5"},
            {"name": f"Исторический музей {city}", "type": "Музей", "rating": "4.7"},
            {"name": f"Городской парк {city}", "type": "Парк", "rating": "4.3"},
            {"name": f"Кафедральный собор {city}", "type": "Религиозный памятник", "rating": "4.8"},
            {"name": f"Смотровая площадка {city}", "type": "Достопримечательность", "rating": "4.6"},
            {"name": f"Центральная улица {city}", "type": "Улица", "rating": "4.4"},
            {"name": f"Городская ратуша {city}", "type": "Архитектура", "rating": "4.2"},
            {"name": f"Памятник основателю {city}", "type": "Памятник", "rating": "4.1"}
        ]
        return mock_poi[:limit]