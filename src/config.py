import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/weather_aq.db")
WEATHER_API_URL = os.getenv("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")
AIR_QUALITY_API_URL = os.getenv(
    "AIR_QUALITY_API_URL", "https://air-quality-api.open-meteo.com/v1/air-quality"
)

CITIES = [
    {"name": "Singapore", "country": "SG", "latitude": 1.3521, "longitude": 103.8198},
    {"name": "Tokyo", "country": "JP", "latitude": 35.6762, "longitude": 139.6503},
    {"name": "London", "country": "GB", "latitude": 51.5074, "longitude": -0.1278},
]
