
# Local Weather & Air Quality ETL Pipeline

An end-to-end Python and SQLite ETL pipeline that extracts daily weather and hourly air-quality metrics from the [Open-Meteo API](https://open-meteo.com/), aligns and enriches the data, loads records idempotently into a normalized relational database, and runs analytical SQL queries.

## Key Engineering Highlights

- **Grain Alignment & Aggregation:** Rolls up 24 hourly air-quality readings (`pm2_5`, `pm10`, `us_aqi`) per day to match daily weather summaries.
- **Defensive Data Validation:** Uses `zip(..., strict=True)` to fail fast on mismatched API arrays and filters `None` readings safely without discarding valid `0.0` measurements.
- **Normalized Relational Schema:** Separates static city metadata (`cities`) from time-series readings (`daily_measurements`) with foreign-key enforcement (`PRAGMA foreign_keys = ON`).
- **Idempotent Loading (UPSERT):** Enforces a composite `UNIQUE (city_id, date)` constraint with `ON CONFLICT DO UPDATE` so re-running the pipeline refreshes records in place instead of creating duplicates.
- **Structured Logging & SQL Analytics:** Tracks stage timing and exceptions via Python's `logging` module and answers trend questions with `JOIN`, `CASE`, and SQL window functions (`OVER`).

## Pipeline Architecture

1. **Extract (`src/extract.py`):** Calls Open-Meteo's Weather Forecast and Air Quality REST endpoints for configured cities with timeouts and HTTP status checks (`raise_for_status`).
2. **Transform (`src/transform.py`):** Aggregates hourly air-quality arrays into daily averages and peaks, computes `temp_range_c`, maps peak US AQI to EPA health categories, and stamps each batch with a UTC extraction timestamp.
3. **Load (`src/load.py` & `sql/schema.sql`):** Initializes SQLite tables and upserts both `cities` and `daily_measurements` inside a single transaction.
4. **Analyze (`sql/analytics.sql` & `src/report.py`):** Executes 7-day city summaries, 3-day rolling averages (window functions), and AQI/rainy-day breakdowns against the local database.

## Project Structure

```text
weather-airquality-etl/
├── data/
│   └── .gitkeep            # Keeps folder tracked while ignoring local .db files
├── sql/
│   ├── schema.sql          # Normalized SQLite table definitions and constraints
│   └── analytics.sql       # Analytical SQL queries (JOINs, CASE, window functions)
├── src/
│   ├── __init__.py
│   ├── config.py           # Environment config and target city coordinates
│   ├── extract.py          # Open-Meteo API ingestion
│   ├── transform.py        # Grain alignment, cleaning, and enrichment
│   ├── load.py             # SQLite schema initialization and idempotent upserts
│   ├── pipeline.py         # Main ETL runner with structured logging
│   └── report.py           # Lightweight CLI runner for analytical SQL queries
├── .env.example            # Safe configuration template
├── .gitignore
├── requirements.txt
└── README.md
```

## Database Schema

- **`cities`**: `city_id` (PK), `name` (UNIQUE), `country`, `latitude`, `longitude`
- **`daily_measurements`**: `measurement_id` (PK), `city_id` (FK), `date`, `temp_max_c`, `temp_min_c`, `temp_range_c`, `precipitation_mm`, `pm2_5_avg`, `pm10_avg`, `us_aqi_avg`, `us_aqi_max`, `aqi_category`, `extracted_at_utc` — constrained by `UNIQUE (city_id, date)`

## Quick Start (Windows PowerShell)

```powershell
# 1. Clone the repository
git clone [https://github.com/Deerence/weather-airquality-etl.git](https://github.com/Deerence/weather-airquality-etl.git)
cd weather-airquality-etl

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the environment template (no API key required)
Copy-Item .env.example .env

# 5. Run the ETL pipeline and analytical SQL report
python -m src.pipeline
python -m src.report
```

## Sample Output

```text
=== 1. 7-Day Weather & Air Quality Summary by City ===
city      | days_recorded | avg_max_c | total_rain_mm | avg_pm2_5 | peak_us_aqi
----------+---------------+-----------+---------------+-----------+------------
Tokyo     | 7             | 15.0      | 5.2           | 22.9      | 106.0      
Singapore | 7             | 31.6      | 66.0          | 14.2      | 78.0       
London    | 7             | 8.5       | 5.9           | 11.5      | 66.0       

=== 2. 3-Day Rolling Average Temperature & AQI (Window Function) ===
city      | date       | temp_max_c | rolling_3d_temp_c | us_aqi_avg | rolling_3d_aqi
----------+------------+------------+-------------------+------------+---------------
London    | 2026-11-19 | 10.3       | 10.3              | 35.29      | 35.3          
London    | 2026-11-20 | 10.3       | 10.3              | 52.88      | 44.1          
London    | 2026-11-21 | 9.3        | 10.0              | 59.17      | 49.1          
London    | 2026-11-22 | 8.9        | 9.5               | 57.54      | 56.5          
London    | 2026-11-23 | 7.7        | 8.6               | 45.33      | 54.0          
London    | 2026-11-24 | 6.9        | 7.8               | 55.17      | 52.7          
London    | 2026-11-25 | 6.4        | 7.0               | 56.92      | 52.5          
Singapore | 2026-11-19 | 28.4       | 28.4              | 68.0       | 68.0          
Singapore | 2026-11-20 | 32.7       | 30.6              | 74.08      | 71.0          
Singapore | 2026-11-21 | 29.8       | 30.3              | 55.33      | 65.8          
Singapore | 2026-11-22 | 32.7       | 31.7              | 51.17      | 60.2          
Singapore | 2026-11-23 | 33.2       | 31.9              | 53.67      | 53.4          
Singapore | 2026-11-24 | 31.9       | 32.6              | 62.54      | 55.8          
Singapore | 2026-11-25 | 32.6       | 32.6              | 60.67      | 59.0          
Tokyo     | 2026-11-19 | 19.3       | 19.3              | 96.29      | 96.3          
Tokyo     | 2026-11-20 | 14.6       | 16.9              | 58.46      | 77.4          
Tokyo     | 2026-11-21 | 14.1       | 16.0              | 64.46      | 73.1          
Tokyo     | 2026-11-22 | 13.1       | 13.9              | 99.46      | 74.1          
Tokyo     | 2026-11-23 | 13.1       | 13.4              | 84.29      | 82.7          
Tokyo     | 2026-11-24 | 17.4       | 14.5              | 75.25      | 86.3          
Tokyo     | 2026-11-25 | 13.3       | 14.6              | 64.29      | 74.6          

=== 3. Air Quality Health Category & Rainy-Day Breakdown ===
city      | aqi_category                   | days | rainy_days
----------+--------------------------------+------+-----------
London    | Moderate                       | 5    | 1         
London    | Good                           | 2    | 1         
Singapore | Moderate                       | 7    | 7         
Tokyo     | Moderate                       | 5    | 1         
Tokyo     | Unhealthy for Sensitive Groups | 2    | 0    
```

## Tech Stack

- **Language:** Python 3.10+ (`requests`, `python-dotenv`, `sqlite3`, `logging`)
- **Database & Analytics:** SQLite, SQL (CTEs/Window Functions, Aggregations, Upserts)
- **Data Source:** Open-Meteo Weather Forecast API & Air Quality API (CAMS)
