from pathlib import Path
import sqlite3
from src.config import DB_PATH

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"

UPSERT_CITY_SQL = """
INSERT INTO cities (name, country, latitude, longitude)
VALUES (:name, :country, :latitude, :longitude)
ON CONFLICT(name) DO UPDATE SET
    country = excluded.country,
    latitude = excluded.latitude,
    longitude = excluded.longitude;
"""

UPSERT_MEASUREMENT_SQL = """
INSERT INTO daily_measurements (
    city_id,
    date,
    temp_max_c,
    temp_min_c,
    temp_range_c,
    precipitation_mm,
    pm2_5_avg,
    pm10_avg,
    us_aqi_avg,
    us_aqi_max,
    aqi_category,
    extracted_at_utc
)
VALUES (
    :city_id,
    :date,
    :temp_max_c,
    :temp_min_c,
    :temp_range_c,
    :precipitation_mm,
    :pm2_5_avg,
    :pm10_avg,
    :us_aqi_avg,
    :us_aqi_max,
    :aqi_category,
    :extracted_at_utc
)
ON CONFLICT(city_id, date) DO UPDATE SET
    temp_max_c = excluded.temp_max_c,
    temp_min_c = excluded.temp_min_c,
    temp_range_c = excluded.temp_range_c,
    precipitation_mm = excluded.precipitation_mm,
    pm2_5_avg = excluded.pm2_5_avg,
    pm10_avg = excluded.pm10_avg,
    us_aqi_avg = excluded.us_aqi_avg,
    us_aqi_max = excluded.us_aqi_max,
    aqi_category = excluded.aqi_category,
    extracted_at_utc = excluded.extracted_at_utc;
"""


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with foreign-key enforcement enabled."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create database tables from sql/schema.sql if they do not exist."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)


def load_data(
    transformed: dict[str, list[dict]], db_path: str = DB_PATH
) -> dict[str, int]:
    """Upsert cities and daily measurements into SQLite without duplicates."""
    conn = get_connection(db_path)
    try:
        init_db(conn)

        with conn:
            cursor = conn.cursor()

            # 1. Upsert cities first so every city has a valid city_id
            cursor.executemany(UPSERT_CITY_SQL, transformed["cities"])

            # 2. Build a lookup map: {"Singapore": 1, "Tokyo": 2, "London": 3}
            cursor.execute("SELECT city_id, name FROM cities;")
            city_id_map = {row["name"]: row["city_id"] for row in cursor.fetchall()}

            # 3. Attach city_id to each measurement row and upsert
            measurement_rows = [
                {**row, "city_id": city_id_map[row["city_name"]]}
                for row in transformed["daily_metrics"]
            ]
            cursor.executemany(UPSERT_MEASUREMENT_SQL, measurement_rows)

            # 4. Read back totals for verification
            cities_total = cursor.execute("SELECT COUNT(*) FROM cities;").fetchone()[0]
            measurements_total = cursor.execute(
                "SELECT COUNT(*) FROM daily_measurements;"
            ).fetchone()[0]

        return {
            "cities_total": cities_total,
            "measurements_total": measurements_total,
            "rows_processed": len(measurement_rows),
        }
    finally:
        conn.close()


if __name__ == "__main__":
    from src.extract import extract_all_cities
    from src.transform import transform_all

    raw_batch = extract_all_cities()
    transformed = transform_all(raw_batch)
    summary = load_data(transformed)

    print("\n--- Load Verification ---")
    print(f"Rows processed this run : {summary['rows_processed']}")
    print(f"Total cities in DB      : {summary['cities_total']}")
    print(f"Total measurements in DB: {summary['measurements_total']}")

    conn = get_connection()
    try:
        latest = conn.execute("""
            SELECT c.name, m.date, m.temp_max_c, m.us_aqi_max, m.aqi_category, m.extracted_at_utc
            FROM daily_measurements m
            JOIN cities c ON m.city_id = c.city_id
            ORDER BY m.date DESC, c.name ASC
            LIMIT 3;
            """).fetchall()
        print("\nLatest stored records:")
        for row in latest:
            print(dict(row))
    finally:
        conn.close()
