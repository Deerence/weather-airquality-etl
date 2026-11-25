-- 1. 7-Day Weather & Air Quality Summary by City
SELECT
    c.name AS city,
    COUNT(*) AS days_recorded,
    ROUND(AVG(m.temp_max_c), 1) AS avg_max_c,
    ROUND(SUM(m.precipitation_mm), 1) AS total_rain_mm,
    ROUND(AVG(m.pm2_5_avg), 1) AS avg_pm2_5,
    ROUND(MAX(m.us_aqi_max), 0) AS peak_us_aqi
FROM daily_measurements m
JOIN cities c ON m.city_id = c.city_id
GROUP BY c.name
ORDER BY peak_us_aqi DESC;

-- 2. 3-Day Rolling Average Temperature & AQI (Window Function)
SELECT
    c.name AS city,
    m.date,
    m.temp_max_c,
    ROUND(
        AVG(m.temp_max_c) OVER (
            PARTITION BY c.name
            ORDER BY m.date
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        1
    ) AS rolling_3d_temp_c,
    m.us_aqi_avg,
    ROUND(
        AVG(m.us_aqi_avg) OVER (
            PARTITION BY c.name
            ORDER BY m.date
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        1
    ) AS rolling_3d_aqi
FROM daily_measurements m
JOIN cities c ON m.city_id = c.city_id
ORDER BY c.name, m.date;

-- 3. Air Quality Health Category & Rainy-Day Breakdown
SELECT
    c.name AS city,
    m.aqi_category,
    COUNT(*) AS days,
    SUM(CASE WHEN m.precipitation_mm > 0 THEN 1 ELSE 0 END) AS rainy_days
FROM daily_measurements m
JOIN cities c ON m.city_id = c.city_id
GROUP BY c.name, m.aqi_category
ORDER BY c.name, days DESC;