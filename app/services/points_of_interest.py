import aiohttp
import time
import os
import json
import asyncio
import logging
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class PointsOfInterestService:
    def __init__(self):
        self.amadeus_api_key = settings.AMADEUS_API_KEY
        self.amadeus_api_secret = settings.AMADEUS_API_SECRET
        self.foursquare_api_key = settings.FOURSQUARE_API_KEY
        self.opentripmap_api_key = settings.OPENTRIPMAP_API_KEY
        self.deepseek_api_key = getattr(settings, "DEEPSEEK_API_KEY", None)
        self.base_url = "https://test.api.amadeus.com/v1"
        self.access_token = None
        self._cache = {}
        self._ttl_seconds = 1800

        self._deepseek_client = None
        if self.deepseek_api_key:
            try:
                self._deepseek_client = OpenAI(
                    api_key=self.deepseek_api_key,
                    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                )
            except Exception as e:
                logger.warning(f"Не удалось инициализировать DeepSeek клиента: {e}")

    async def _get_access_token(self) -> str:
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
        try:
            key = (city.lower(), limit)
            cached = self._cache.get(key)
            now = time.time()
            if cached and now - cached[0] < self._ttl_seconds:
                return cached[1]

            poi_data = await self._get_poi_from_foursquare(city, limit)
            if poi_data:
                logger.info(f"Получены данные из Foursquare API для {city}")
                self._cache[key] = (now, poi_data)
                return poi_data

            poi_data = await self._get_poi_from_opentripmap(city, limit)
            if poi_data:
                logger.info(f"Получены данные из OpenTripMap API для {city}")
                self._cache[key] = (now, poi_data)
                return poi_data

            poi_data = await self._get_poi_from_deepseek(city, limit)
            if poi_data:
                logger.info(f"Получены данные из DeepSeek для {city}")
                self._cache[key] = (now, poi_data)
                return poi_data

            logger.warning(f"Используем mock данные для {city}")
            data = self._get_mock_poi(city, limit)
            self._cache[key] = (now, data)
            return data

        except Exception as e:
            logger.error(f"Ошибка при получении POI для {city}: {e}")
            data = self._get_mock_poi(city, limit)
            self._cache[key] = (now, data)
            return data

    async def _get_poi_from_foursquare(self, city: str, limit: int) -> list:
        try:
            if not self.foursquare_api_key or self.foursquare_api_key == "None":
                logger.debug("Foursquare API ключ не установлен")
                return None

            url = "https://api.foursquare.com/v3/places/search"

            # Foursquare expects the API key in Authorization; keep existing fsq3 prefix if present.
            api_key = self.foursquare_api_key
            if api_key and not api_key.lower().startswith("fsq3"):
                api_key = f"fsq3{api_key}"

            headers = {
                "Accept": "application/json",
                "Authorization": api_key
            }
            params = {
                "query": "tourist attractions",
                "near": city,
                "limit": min(limit, 50),
            }
            print(url)
            print(headers)
            print(params)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    response_text = await response.text()
                    print(response_text)
                    if response.status == 200:
                        try:
                            data = await response.json()
                            poi_list = []
                            print(data)
                            for place in data.get("results", [])[:limit]:
                                categories = place.get("categories", [])
                                category_name = categories[0].get("name", "Достопримечательность") if categories else "Достопримечательность"

                                poi_list.append({
                                    "name": place.get("name", "Неизвестное место"),
                                    "type": category_name,
                                    "rating": str(place.get("rating", "4.0")) if place.get("rating") else "4.0"
                                })

                            return poi_list if poi_list else None
                        except Exception as json_error:
                            logger.error(f"Ошибка парсинга JSON ответа Foursquare: {json_error}")
                            logger.debug(f"Ответ сервера: {response_text[:500]}")
                            return None
                    else:
                        logger.warning(f"Ошибка Foursquare API: HTTP {response.status}")
                        try:
                            error_data = await response.json()
                            logger.debug(f"Детали ошибки: {error_data}")
                        except:
                            logger.debug(f"Тело ответа: {response_text[:500]}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при запросе к Foursquare API: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка Foursquare API: {e}")
            return None

    async def _get_poi_from_opentripmap(self, city: str, limit: int) -> list:
        try:
            if not self.opentripmap_api_key or self.opentripmap_api_key == "None":
                logger.debug("OpenTripMap API ключ не установлен")
                return None

            geocode_url = "https://api.opentripmap.com/0.1/en/places/geoname"
            geocode_params = {
                "name": city,
                "apikey": self.opentripmap_api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(geocode_url, params=geocode_params) as response:
                    if response.status == 200:
                        geocode_data = await response.json()
                        if geocode_data and geocode_data.get("lat") is not None and geocode_data.get("lon") is not None:
                            lat = geocode_data.get("lat")
                            lon = geocode_data.get("lon")

                            try:
                                lat_str = str(float(lat))
                                lon_str = str(float(lon))
                            except (TypeError, ValueError):
                                return None

                            poi_url = "https://api.opentripmap.com/0.1/en/places/radius"
                            poi_params = {
                                "radius": 10000,
                                "lon": lon_str,
                                "lat": lat_str,
                                "kinds": "interesting_places",
                                "limit": int(limit),
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
                                            "rating": "4.0"
                                        })
                                    return poi_list
                        return None
        except Exception as e:
            logger.error(f"Ошибка OpenTripMap API: {e}")
            return None

    async def _get_poi_from_deepseek(self, city: str, limit: int) -> list:
        if not self.deepseek_api_key or not self._deepseek_client:
            logger.debug("DeepSeek API ключ не установлен или клиент не инициализирован")
            return None

        user_prompt = (
            f"Назови топ {limit} достопримечательностей города {city}. "
            "Предоставь только названия, адрес и краткое описание. "
            "Ответь строго в формате JSON-массива, где каждый объект имеет поля "
            "name, address и description. Никакого дополнительного текста вне JSON."
        )

        messages = [
            {
                "role": "system",
                "content": "Ты — туристический ассистент. Отвечай кратко и структурированно.",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    stream=False,
                    temperature=0.2,
                ),
            )

            content = response.choices[0].message.content if response.choices else ""
            if not content:
                return None

            def _parse_json(text: str):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    start = text.find("[")
                    end = text.rfind("]")
                    if start != -1 and end != -1 and end > start:
                        return json.loads(text[start : end + 1])
                    raise

            try:
                raw_items = _parse_json(content)
            except Exception as e:
                logger.error(f"Не удалось распарсить JSON из ответа DeepSeek: {e}")
                logger.debug(f"Сырой ответ DeepSeek (обрезан до 500 символов): {content[:500]}")
                return None

            if not isinstance(raw_items, list):
                return None

            poi_list = []
            for item in raw_items[:limit]:
                if not isinstance(item, dict):
                    continue
                name = item.get("name") or "Неизвестное место"
                address = item.get("address") or ""
                description = item.get("description") or ""

                type_field_parts = []
                if address:
                    type_field_parts.append(f"Адрес: {address}")
                if description:
                    type_field_parts.append(description)
                type_field = " | ".join(type_field_parts) if type_field_parts else "Достопримечательность"

                poi_list.append(
                    {
                        "name": name,
                        "type": type_field,
                        "rating": "4.5",
                    }
                )

            return poi_list or None
        except Exception as e:
            logger.error(f"Ошибка DeepSeek API: {e}")
            return None

    def _get_mock_poi(self, city: str, limit: int) -> list:
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