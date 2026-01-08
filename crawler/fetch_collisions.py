import requests
import pandas as pd
import os
import sys
from datetime import datetime, timedelta

URL = "https://data.cityofnewyork.us/resource/h9gi-nx95.json"
XML_SERVICE_URL = os.getenv("XML_SERVICE_URL", "http://xml-service:5000/api")

# Get limit from command line argument (default 100)
RECORD_LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 100
print(f"📊 Record limit set to: {RECORD_LIMIT}")

def get_latest_date_from_db():
    """Get the latest collision date from the database to avoid re-scraping old data"""
    try:
        response = requests.get(f"{XML_SERVICE_URL}/latest-collision-date", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data", {}).get("latestDate"):
                latest_date = data["data"]["latestDate"]
                print(f"📅 Latest collision date in database: {latest_date}")
                return latest_date
    except Exception as e:
        print(f"⚠️  Could not fetch latest date from database: {e}")
    return None

# Check if we have data in the database
latest_db_date = get_latest_date_from_db()

# Build query parameters with the specified limit
PARAMS = {
    "$limit": RECORD_LIMIT,   
    "$order": "crash_date DESC"
}

# If we have data, only fetch records newer than the latest date
if latest_db_date:
    # Add a day buffer to ensure we don't miss any records
    print(f"📥 Fetching up to {RECORD_LIMIT} records newer than {latest_db_date}...")
    PARAMS["$where"] = f"crash_date > '{latest_db_date}'"
else:
    print(f"📥 No existing data found, fetching up to {RECORD_LIMIT} records...")

print(f"🔗 Requesting data from NYC Open Data API...")
response = requests.get(URL, params=PARAMS)
data = response.json()

if not data:
    print("✅ No new collision data to fetch (database is up to date)")
    # Create an empty CSV to signal no new data
    df = pd.DataFrame(columns=[
        "crash_date", "crash_time", "persons_injured", "persons_killed",
        "pedestrians_injured", "pedestrians_killed", "cyclists_injured", "cyclists_killed",
        "motorists_injured", "motorists_killed", "factor_1", "factor_2", "factor_3",
        "factor_4", "factor_5", "vehicle_1", "vehicle_2", "vehicle_3", "vehicle_4", "vehicle_5"
    ])
    df.to_csv("collisions_raw.csv", index=False)
    print("✅ Empty CSV created (no new records)")
    exit(0)

df = pd.DataFrame(data)
print(f"📊 Retrieved {len(df)} records from API")

# selecionar e renomear colunas
columns = {
    "crash_date": "crash_date",
    "crash_time": "crash_time",
    "number_of_persons_injured": "persons_injured",
    "number_of_persons_killed": "persons_killed",
    "number_of_pedestrians_injured": "pedestrians_injured",
    "number_of_pedestrians_killed": "pedestrians_killed",
    "number_of_cyclist_injured": "cyclists_injured",
    "number_of_cyclist_killed": "cyclists_killed",
    "number_of_motorist_injured": "motorists_injured",
    "number_of_motorist_killed": "motorists_killed",
    "contributing_factor_vehicle_1": "factor_1",
    "contributing_factor_vehicle_2": "factor_2",
    "contributing_factor_vehicle_3": "factor_3",
    "contributing_factor_vehicle_4": "factor_4",
    "contributing_factor_vehicle_5": "factor_5",
    "vehicle_type_code1": "vehicle_1",
    "vehicle_type_code2": "vehicle_2",
    "vehicle_type_code3": "vehicle_3",
    "vehicle_type_code4": "vehicle_4",
    "vehicle_type_code5": "vehicle_5",
}# garantir que todas as colunas existem
for col in columns.keys():
    if col not in df.columns:
        df[col] = None

# agora sim, selecionar e renomear
df = df[list(columns.keys())].rename(columns=columns)

df.to_csv("collisions_raw.csv", index=False)

print(f"✅ CSV de colisões criado com {len(df)} novos registos")


