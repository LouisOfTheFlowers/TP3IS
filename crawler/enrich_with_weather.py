import pandas as pd
import requests
import os
from dotenv import load_dotenv

# load env variables
load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")
CITY = "New York,NY,USA"

if not API_KEY:
    raise Exception("WEATHER_API_KEY not found in .env")

print("📄 Loading collisions_raw.csv...")
df = pd.read_csv("collisions_raw.csv")

# ----------------------------
# 1️⃣ CLEAN DATE
# ----------------------------
# NYC dates look like: 2018-01-01T00:00:00.000
df["date"] = df["crash_date"].astype(str).str.slice(0, 10)

# ----------------------------
# 2️⃣ SAFE HOUR PARSING
# ----------------------------
def parse_hour(t):
    try:
        hour = int(str(t).split(":")[0])
        return hour if 0 <= hour <= 23 else None
    except:
        return None

df["hour"] = df["crash_time"].apply(parse_hour)

# ----------------------------
# 3️⃣ UNIQUE DATES (KEY OPTIMIZATION)
# ----------------------------
unique_dates = df["date"].dropna().unique()

print(f"📆 Unique dates to fetch: {len(unique_dates)}")

# ----------------------------
# 4️⃣ FETCH WEATHER (1 CALL PER DAY)
# ----------------------------
weather_by_day = {}

for date in unique_dates:
    print(f"🌦 Fetching weather for {date}")

    url = (
        f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/"
        f"timeline/{CITY}/{date}"
        f"?unitGroup=metric&include=hours&key={API_KEY}"
    )

    response = requests.get(url)

    if response.status_code != 200:
        print(f"⚠️ Failed to fetch weather for {date}")
        continue

    data = response.json()

    # map hour -> condition
    hourly_weather = {}
    for h in data["days"][0]["hours"]:
        hour = int(h["datetime"][:2])
        hourly_weather[hour] = h.get("conditions")

    weather_by_day[date] = hourly_weather

print("✅ Weather data fetched")

# ----------------------------
# 5️⃣ MAP WEATHER TO ACCIDENTS
# ----------------------------
def map_weather(row):
    try:
        return weather_by_day[row["date"]][row["hour"]]
    except:
        return None

df["weather_condition"] = df.apply(map_weather, axis=1)

# ----------------------------
# 6️⃣ CLEAN & SAVE
# ----------------------------
df.drop(columns=["date", "hour"], inplace=True)

df.to_csv("collisions_weather.csv", index=False)

print("🚀 collisions_weather.csv created successfully")
