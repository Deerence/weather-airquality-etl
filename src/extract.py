import requests
from src.config import AIR_QUALITY_API_URL, CITIES, WEATHER_API_URL


def fetch_json(url: str, params: dict) -> dict:
    """Send a GET request and return the parsed JSON dictionary."""
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def extract_city_data(city: dict, past_days: int = 6) -> dict:
    """Fetch raw daily weather and hourly air-quality JSON for one city."""
    weather_params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "past_days": past_days,
        "forecast_days": 1,
    }

    aq_params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "hourly": "pm2_5,pm10,us_aqi",
        "timezone": "auto",
        "past_days": past_days,
        "forecast_days": 1,
    }

    weather_raw = fetch_json(WEATHER_API_URL, weather_params)
    aq_raw = fetch_json(AIR_QUALITY_API_URL, aq_params)

    return {
        "city": city,
        "weather": weather_raw,
        "air_quality": aq_raw,
    }


def extract_all_cities(past_days: int = 6) -> list[dict]:
    """Fetch raw weather and air-quality payloads for every configured city."""
    results = []
    for city in CITIES:
        print(f"Fetching data for {city['name']}...")
        results.append(extract_city_data(city, past_days=past_days))
    return results


if __name__ == "__main__":
    raw_batch = extract_all_cities()

    print("\n--- Quick Inspection ---")
    for record in raw_batch:
        city_name = record["city"]["name"]
        daily_dates = record["weather"]["daily"]["time"]
        max_temps = record["weather"]["daily"]["temperature_2m_max"]
        hourly_times = record["air_quality"]["hourly"]["time"]
        us_aqi_values = record["air_quality"]["hourly"]["us_aqi"]

        print(f"\n{city_name}:")
        print(
            f"  Weather days returned  : {len(daily_dates)} ({daily_dates[0]} to {daily_dates[-1]})"
        )
        print(f"  Latest max temp (C)    : {max_temps[-1]}")
        print(f"  AQ hours returned      : {len(hourly_times)}")
        print(f"  Sample US AQI (first 3): {us_aqi_values[:3]}")
