import os
import base64
import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression

load_dotenv()

st.set_page_config(
    page_title="Air Pollution Monitoring Dashboard",
    layout="wide"
)

def get_base64(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

bg_image = get_base64("background.png")

st.markdown(
    f"""
    <style>

    .stApp {{
    background-image: url("data:image/png;base64,{bg_image}");
    background-size: 100% 100%;
    background-repeat: no-repeat;
    background-position: center;
    background-attachment: fixed;
    min-height: 100vh;
}}

    .block-container {{
        background-color: rgba(0, 0, 0, 0.70);
        padding: 2rem;
        border-radius: 15px;
    }}

    h1, h2, h3, h4, h5, h6, p, div, label {{
        color: white !important;
        font-weight: bold;
    }}

    section[data-testid="stSidebar"] {{
        background-color: rgba(0, 0, 0, 0.88);
    }}

    section[data-testid="stSidebar"] * {{
        color: white !important;
    }}

    .stSelectbox div[data-baseweb="select"] > div {{
        background-color: rgba(30,30,30,0.95) !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }}

    .stSelectbox svg {{
        fill: white !important;
    }}

    </style>
    """,
    unsafe_allow_html=True
)

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT"),
    sslmode="require"
)

query = """
SELECT *
FROM pollution_data
ORDER BY recorded_at;
"""

df = pd.read_sql(query, conn)

conn.close()

if df.empty:
    st.warning("No data found in database.")
    st.stop()

df["recorded_at"] = pd.to_datetime(df["recorded_at"])
city_options = ["All Cities"] + sorted(df["city"].unique())

selected_city = st.sidebar.selectbox(
    "Select City",
    city_options
)

if selected_city == "All Cities":
    city_df = df.copy()
else:
    city_df = df[df["city"] == selected_city].copy()

city_locations = {
    "Delhi": (28.6139, 77.2090),
    "Ghaziabad": (28.6692, 77.4538),
    "Noida": (28.5355, 77.3910),
    "Kanpur": (26.4499, 80.3319),
    "Lucknow": (26.8467, 80.9462),
    "Mumbai": (19.0760, 72.8777),
    "Nagpur": (21.1458, 79.0882),
    "Bhopal": (23.2599, 77.4126)
}

location_df = pd.DataFrame([
    {
        "city": city,
        "lat": coords[0],
        "lon": coords[1]
    }
    for city, coords in city_locations.items()
])

latest_df = (
    df.sort_values("recorded_at")
    .groupby("city")
    .tail(1)
)

st.title("Real-Time Air Pollution Monitoring Dashboard")
st.markdown("### Live Pollution Analytics + Future Health Risk Trend")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Average PM2.5",
    round(latest_df["pm25"].mean(), 2)
)

col2.metric(
    "Average PM10",
    round(latest_df["pm10"].mean(), 2)
)

col3.metric(
    "Highest Risk City",
    latest_df.sort_values("pm25", ascending=False).iloc[0]["city"]
)

col4.metric(
    "Cities Monitored",
    latest_df["city"].nunique()
)

st.subheader("Pollution Monitoring Locations")

map_df = latest_df.merge(
    location_df,
    on="city",
    how="left"
)

map_fig = px.scatter_mapbox(
    map_df,
    lat="lat",
    lon="lon",
    hover_name="city",
    hover_data=["pm25", "respiratory_risk"],
    color="pm25",
    zoom=3,
    height=400
)

map_fig.update_layout(
    mapbox_style="carto-darkmatter",
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(
        color="white",
        size=16
    ),
    legend=dict(
        font=dict(color="white", size=14)
    )
)

st.plotly_chart(map_fig, use_container_width=True)

st.subheader("PM2.5 Trend Analysis")

city_df["month"] = (
    city_df["recorded_at"]
    .dt.to_period("M")
    .astype(str)
)

monthly_pm25_df = (
    city_df.groupby("month")["pm25"]
    .mean()
    .reset_index()
)

fig_pm25 = px.line(
    monthly_pm25_df,
    x="month",
    y="pm25",
    title=f"{selected_city} Monthly Average PM2.5 Trend"
)

fig_pm25.update_traces(
    line=dict(width=4)
)

fig_pm25.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        color="white",
        size=16
    ),
    title_font=dict(
        size=24,
        color="white"
    ),
    xaxis=dict(
        title_font=dict(color="white", size=18),
        tickfont=dict(color="white", size=14),
        gridcolor="rgba(255,255,255,0.15)"
    ),
    yaxis=dict(
        title_font=dict(color="white", size=18),
        tickfont=dict(color="white", size=14),
        gridcolor="rgba(255,255,255,0.15)"
    )
)

st.plotly_chart(fig_pm25, use_container_width=True)

st.subheader("PM10 Trend Analysis")

city_df["month"] = (
    city_df["recorded_at"]
    .dt.to_period("M")
    .astype(str)
)

monthly_df = (
    city_df.groupby("month")["pm10"]
    .mean()
    .reset_index()
)

fig_pm10 = px.line(
    monthly_df,
    x="month",
    y="pm10",
    title=f"{selected_city} Monthly Average PM10 Trend"
)

fig_pm10.update_traces(
    line=dict(width=4)
)

fig_pm10.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        color="white",
        size=16
    ),
    title_font=dict(
        size=24,
        color="white"
    ),
    xaxis=dict(
        title_font=dict(color="white", size=18),
        tickfont=dict(color="white", size=14),
        gridcolor="rgba(255,255,255,0.15)"
    ),
    yaxis=dict(
        title_font=dict(color="white", size=18),
        tickfont=dict(color="white", size=14),
        gridcolor="rgba(255,255,255,0.15)"
    )
)

st.plotly_chart(fig_pm10, use_container_width=True)

st.subheader("Respiratory Risk Distribution")

risk_fig = px.histogram(
    latest_df,
    x="respiratory_risk",
    color="respiratory_risk",
    title="Current Risk Categories"
)

risk_fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        color="white",
        size=16
    ),
    title_font=dict(
        size=24,
        color="white"
    ),
    xaxis=dict(
        title_font=dict(color="white", size=18),
        tickfont=dict(color="white", size=14),
        gridcolor="rgba(255,255,255,0.15)"
    ),
    yaxis=dict(
        title_font=dict(color="white", size=18),
        tickfont=dict(color="white", size=14),
        gridcolor="rgba(255,255,255,0.15)"
    ),
    legend=dict(
        font=dict(color="white", size=14)
    )
)

st.plotly_chart(risk_fig, use_container_width=True)

st.subheader("6-Year PM2.5 Future Prediction")

future_results = []

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

    future_results.append({
        "City": city,
        "Predicted_PM25_6Y": round(predicted_pm25, 2),
        "Future_Risk": risk
    })

future_df = pd.DataFrame(future_results)

st.dataframe(future_df, use_container_width=True)

future_fig = px.bar(
    future_df,
    x="City",
    y="Predicted_PM25_6Y",
    color="Future_Risk",
    title="Predicted PM2.5 After 6 Years"
)

future_fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        color="white",
        size=16
    ),
    title_font=dict(
        size=24,
        color="white"
    ),
    xaxis=dict(
        title_font=dict(color="white", size=18),
        tickfont=dict(color="white", size=14),
        gridcolor="rgba(255,255,255,0.15)"
    ),
    yaxis=dict(
        title_font=dict(color="white", size=18),
        tickfont=dict(color="white", size=14),
        gridcolor="rgba(255,255,255,0.15)"
    ),
    legend=dict(
        font=dict(color="white", size=14)
    )
)

st.plotly_chart(future_fig, use_container_width=True)

st.subheader("Live Pollution Dataset")

st.dataframe(df, use_container_width=True)
