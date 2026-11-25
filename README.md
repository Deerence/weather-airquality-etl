
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
Paste your 7-Day Weather & Air Quality Summary table from `python -m src.report` here
```

## Tech Stack

- **Language:** Python 3.10+ (`requests`, `python-dotenv`, `sqlite3`, `logging`)
- **Database & Analytics:** SQLite, SQL (CTEs/Window Functions, Aggregations, Upserts)
- **Data Source:** Open-Meteo Weather Forecast API & Air Quality API (CAMS)
