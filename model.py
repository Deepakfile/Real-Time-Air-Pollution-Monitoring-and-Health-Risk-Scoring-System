import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT"),
    sslmode="require"
)

query = """
SELECT city, pm25, recorded_at
FROM pollution_data
WHERE pm25 IS NOT NULL
ORDER BY recorded_at;
"""

df = pd.read_sql(query, conn)

df["recorded_at"] = pd.to_datetime(df["recorded_at"])

results = []

for city in df["city"].unique():

    city_df = df[df["city"] == city].copy()

    city_df = city_df.sort_values("recorded_at")

    city_df["days"] = (
        city_df["recorded_at"] - city_df["recorded_at"].min()
    ).dt.days

    X = city_df[["days"]]
    y = city_df["pm25"]

    model = LinearRegression()
    model.fit(X, y)

    future_day = city_df["days"].max() + (365 * 6)

    predicted_pm25 = model.predict([[future_day]])[0]

    if predicted_pm25 > 150:
        risk = "Severe"
    elif predicted_pm25 > 100:
        risk = "High"
    elif predicted_pm25 > 50:
        risk = "Moderate"
    else:
        risk = "Low"

    results.append({
        "City": city,
        "Predicted_PM25_6Y": round(predicted_pm25, 2),
        "Future_Risk": risk
    })

result_df = pd.DataFrame(results)

print(result_df)

conn.close()
