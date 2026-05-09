import requests
import psycopg2
from datetime import datetime
import time
import logging

logging.basicConfig(
    filename="pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

conn = psycopg2.connect(
    host="aws-1-ap-south-1.pooler.supabase.com",
    database="postgres",
    user="postgres.zlppwyofklrwyrqpbcgj",
    password="98Re@ltimeproj",
    port="6543",
    sslmode="require"
)

cursor = conn.cursor()

create_table_query = """
CREATE TABLE IF NOT EXISTS pollution_data (
    id SERIAL PRIMARY KEY,
    city VARCHAR(50),
    pm25 FLOAT,
    pm10 FLOAT,
    co FLOAT,
    no2 FLOAT,
    ozone FLOAT,
    recorded_at TIMESTAMP,
    respiratory_risk VARCHAR(20),
    UNIQUE(city, recorded_at)
);
"""

cursor.execute(create_table_query)
conn.commit()

cities = {
    "Delhi": (28.6139, 77.2090),
    "Ghaziabad": (28.6692, 77.4538),
    "Noida": (28.5355, 77.3910),
    "Kanpur": (26.4499, 80.3319),
    "Lucknow": (26.8467, 80.9462),
    "Mumbai": (19.0760, 72.8777),
    "Nagpur": (21.1458, 79.0882),
    "Bhopal": (23.2599, 77.4126)
}

for city, (lat, lon) in cities.items():

    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})

    except Exception as e:
        logging.error(f"{city} fetch failed: {e}")
        continue

    pm25 = current.get("pm2_5")
    pm10 = current.get("pm10")
    co = current.get("carbon_monoxide")
    no2 = current.get("nitrogen_dioxide")
    ozone = current.get("ozone")
    recorded_time = current.get("time")

    if recorded_time:
        recorded_time = datetime.fromisoformat(recorded_time)

    if pm25 is None:
        risk = "Unknown"
    elif pm25 > 150:
        risk = "Severe"
    elif pm25 > 100:
        risk = "High"
    elif pm25 > 50:
        risk = "Moderate"
    else:
        risk = "Low"

    insert_query = """
    INSERT INTO pollution_data
    (city, pm25, pm10, co, no2, ozone, recorded_at, respiratory_risk)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (city, recorded_at) DO NOTHING;
    """

    cursor.execute(insert_query, (
        city,
        pm25,
        pm10,
        co,
        no2,
        ozone,
        recorded_time,
        risk
    ))

    logging.info(f"{city} inserted | PM2.5: {pm25} | Risk: {risk}")

    print(f"{city} | PM2.5: {pm25} | Risk: {risk}")

    time.sleep(2)

conn.commit()

cursor.close()
conn.close()

logging.info("Pipeline run completed.")

print("Data inserted successfully into Supabase.")