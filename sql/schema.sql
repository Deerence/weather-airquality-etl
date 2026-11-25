CREATE TABLE IF NOT EXISTS cities (
    city_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    country TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_measurements (
    measurement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    temp_max_c REAL,
    temp_min_c REAL,
    temp_range_c REAL,
    precipitation_mm REAL,
    pm2_5_avg REAL,
    pm10_avg REAL,
    us_aqi_avg REAL,
    us_aqi_max REAL,
    aqi_category TEXT NOT NULL,
    extracted_at_utc TEXT NOT NULL,
    FOREIGN KEY (city_id) REFERENCES cities(city_id),
    UNIQUE (city_id, date)
);