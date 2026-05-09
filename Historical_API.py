import os
import requests
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT"),
    sslmode="require"
)

cursor = conn.cursor()

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

start_date = "2022-01-01"
end_date = "2025-12-31"

for city, (lat, lon) in cities.items():

    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&daily=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone"
        f"&start_date={start_date}"
        f"&end_date={end_date}"
    )

    response = requests.get(url, timeout=60)
    data = response.json()

    daily = data.get("daily", {})

    times = daily.get("time", [])
    pm25_values = daily.get("pm2_5", [])
    pm10_values = daily.get("pm10", [])
    co_values = daily.get("carbon_monoxide", [])
    no2_values = daily.get("nitrogen_dioxide", [])
    ozone_values = daily.get("ozone", [])

    for i in range(len(times)):

        recorded_time = datetime.fromisoformat(times[i])

        pm25 = pm25_values[i]
        pm10 = pm10_values[i]
        co = co_values[i]
        no2 = no2_values[i]
        ozone = ozone_values[i]

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

    conn.commit()

    print(f"{city} historical data inserted")

cursor.close()
conn.close()

print("Historical daily data insertion completed.")
