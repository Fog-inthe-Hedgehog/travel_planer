import os
from typing import Optional
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

class Settings:
    BOT_TOKEN: Optional[str] = os.getenv("BOT_TOKEN")
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    AMADEUS_API_KEY: Optional[str] = os.getenv("AMADEUS_API_KEY")
    AMADEUS_API_SECRET: Optional[str] = os.getenv("AMADEUS_API_SECRET")
    FOURSQUARE_API_KEY: Optional[str] = os.getenv("FOURSQUARE_API_KEY")
    OPENTRIPMAP_API_KEY: Optional[str] = os.getenv("OPENTRIPMAP_API_KEY")
    # Опционально: добавьте проверки на наличие обязательных переменных
    def validate(self):
        required_vars = ["BOT_TOKEN", "DATABASE_URL", "OPENWEATHER_API_KEY", "AMADEUS_API_KEY", "AMADEUS_API_SECRET"]
        for var in required_vars:
            if not getattr(self, var):
                raise ValueError(f"Missing required environment variable: {var}")


settings = Settings()
settings.validate()  # Проверяем обязательные переменные