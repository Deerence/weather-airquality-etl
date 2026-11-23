from datetime import datetime, timezone
import json
from typing import Optional


def safe_avg(values: list) -> Optional[float]:
    """Return the rounded average of non-null values, or None if all are missing."""
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return round(sum(clean) / len(clean), 2)


def safe_max(values: list) -> Optional[float]:
    """Return the rounded maximum of non-null values, or None if all are missing."""
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return round(max(clean), 2)


def classify_us_aqi(aqi: Optional[float]) -> str:
    """Map a numeric US AQI value to its official EPA health category."""
    if aqi is None:
        return "Unknown"
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    if aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi <= 200:
        return "Unhealthy"
    if aqi <= 300:
        return "Very Unhealthy"
    return "Hazardous"


def aggregate_hourly_aq(aq_raw: dict) -> dict[str, dict]:
    """Roll up 24 hourly air-quality readings per day into daily summaries."""
    hourly = aq_raw.get("hourly", {})
    times = hourly.get("time", [])
    pm2_5_list = hourly.get("pm2_5", [])
    pm10_list = hourly.get("pm10", [])
    aqi_list = hourly.get("us_aqi", [])

    grouped: dict[str, dict[str, list]] = {}

    for timestamp, pm2_5, pm10, aqi in zip(times, pm2_5_list, pm10_list, aqi_list):
        # Timestamps look like "2026-11-24T13:00" -> keep just "2026-11-24"
        date_str = timestamp.split("T")[0]
        if date_str not in grouped:
            grouped[date_str] = {"pm2_5": [], "pm10": [], "us_aqi": []}

        grouped[date_str]["pm2_5"].append(pm2_5)
        grouped[date_str]["pm10"].append(pm10)
        grouped[date_str]["us_aqi"].append(aqi)

    daily_aq = {}
    for date_str, metrics in grouped.items():
        daily_aq[date_str] = {
            "pm2_5_avg": safe_avg(metrics["pm2_5"]),
            "pm10_avg": safe_avg(metrics["pm10"]),
            "us_aqi_avg": safe_avg(metrics["us_aqi"]),
            "us_aqi_max": safe_max(metrics["us_aqi"]),
        }

    return daily_aq


def transform_city_record(raw_record: dict, extracted_at: str) -> list[dict]:
    """Combine daily weather and rolled-up air quality into clean daily rows."""
    city_name = raw_record["city"]["name"]
    daily_weather = raw_record["weather"].get("daily", {})
    daily_aq = aggregate_hourly_aq(raw_record["air_quality"])

    dates = daily_weather.get("time", [])
    max_temps = daily_weather.get("temperature_2m_max", [])
    min_temps = daily_weather.get("temperature_2m_min", [])
    precips = daily_weather.get("precipitation_sum", [])

    rows = []
    for date_str, t_max, t_min, precip in zip(dates, max_temps, min_temps, precips):
        aq_for_day = daily_aq.get(date_str, {})
        us_aqi_max = aq_for_day.get("us_aqi_max")

        temp_range = (
            round(t_max - t_min, 2) if t_max is not None and t_min is not None else None
        )

        rows.append(
            {
                "city_name": city_name,
                "date": date_str,
                "temp_max_c": t_max,
                "temp_min_c": t_min,
                "temp_range_c": temp_range,
                "precipitation_mm": precip,
                "pm2_5_avg": aq_for_day.get("pm2_5_avg"),
                "pm10_avg": aq_for_day.get("pm10_avg"),
                "us_aqi_avg": aq_for_day.get("us_aqi_avg"),
                "us_aqi_max": us_aqi_max,
                "aqi_category": classify_us_aqi(us_aqi_max),
                "extracted_at_utc": extracted_at,
            }
        )

    return rows


def transform_all(raw_batch: list[dict]) -> dict[str, list[dict]]:
    """Transform raw city payloads into normalized lists for cities and daily metrics."""
    extracted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cities = []
    daily_metrics = []

    for raw_record in raw_batch:
        cities.append(raw_record["city"])
        daily_metrics.extend(transform_city_record(raw_record, extracted_at))

    return {
        "cities": cities,
        "daily_metrics": daily_metrics,
    }


if __name__ == "__main__":
    from src.extract import extract_all_cities

    raw_batch = extract_all_cities()
    transformed = transform_all(raw_batch)

    print("\n--- Transform Verification ---")
    print(f"Cities prepared       : {len(transformed['cities'])}")
    print(f"Daily rows prepared   : {len(transformed['daily_metrics'])}")
    print("\nSample Row 1 (first):")
    print(json.dumps(transformed["daily_metrics"][0], indent=2))
    print("\nSample Row 2 (latest):")
    print(json.dumps(transformed["daily_metrics"][-1], indent=2))
