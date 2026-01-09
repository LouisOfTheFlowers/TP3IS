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

# Optional: Get date range from command line (format: YYYY-MM-DD)
# Usage: python fetch_collisions.py 100 2024-01-01 2024-12-31
START_DATE = sys.argv[2] if len(sys.argv) > 2 else None
END_DATE = sys.argv[3] if len(sys.argv) > 3 else None

if START_DATE or END_DATE:
    print(f"📅 Date range filter: {START_DATE or 'any'} to {END_DATE or 'any'}")


def get_existing_collision_keys():
    """
    Get all existing collision keys (date|time) from the database.
    This is used to skip duplicates BEFORE scraping/processing.
    """
    try:
        response = requests.get(f"{XML_SERVICE_URL}/existing-collision-keys", timeout=60)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                keys = set(data["data"].get("keys", []))
                print(f"📋 Found {len(keys)} existing collision keys in database")
                return keys
    except Exception as e:
        print(f"⚠️  Could not fetch existing collision keys: {e}")
    return set()


def normalize_time(time_str):
    """Normalize time format to HH:MM for consistent comparison"""
    if not time_str or pd.isna(time_str):
        return "00:00"
    time_str = str(time_str).strip()
    if ":" in time_str:
        parts = time_str.split(":")
        hour = int(parts[0]) if parts[0].isdigit() else 0
        minute = int(parts[1]) if parts[1].isdigit() else 0
        return f"{hour:02d}:{minute:02d}"
    return "00:00"


def normalize_date(date_str):
    """Normalize date format to YYYY-MM-DD"""
    if not date_str or pd.isna(date_str):
        return ""
    date_str = str(date_str).strip()
    # Handle ISO format with time component (e.g., "2025-01-01T00:00:00.000")
    if "T" in date_str:
        date_str = date_str.split("T")[0]
    return date_str


def create_collision_key(date_str, time_str):
    """Create a collision key in format 'date|time' for duplicate checking"""
    date = normalize_date(date_str)
    time = normalize_time(time_str)
    return f"{date}|{time}"


# Get existing collision keys from database FIRST
print("🔍 Fetching existing collision keys from database...")
existing_keys = get_existing_collision_keys()

# We'll keep fetching until we have enough NEW records
MAX_API_LIMIT = 50000  # NYC API limit per request
BATCH_SIZE = 10000  # Fetch this many records per request
MAX_ITERATIONS = 50  # Safety limit to prevent infinite loops (50 iterations = up to 500k records)

all_new_records = []
offset = 0
iteration = 0

print(f"🎯 Target: {RECORD_LIMIT} NEW unique records")
print(f"📊 Strategy: Fetch in batches of {BATCH_SIZE}, filter duplicates, repeat until target reached\n")

while len(all_new_records) < RECORD_LIMIT and iteration < MAX_ITERATIONS:
    iteration += 1
    
    # Calculate how many more we need
    remaining = RECORD_LIMIT - len(all_new_records)
    fetch_size = min(BATCH_SIZE, MAX_API_LIMIT)
    
    print(f"🔄 Iteration {iteration}: Fetching {fetch_size} records (offset: {offset})...")
    print(f"   Current progress: {len(all_new_records)}/{RECORD_LIMIT} new records")
    
    PARAMS = {
        "$limit": fetch_size,
        "$offset": offset,
        "$order": "crash_date DESC"  # Fetch from newest to oldest (2026 -> 2024)
    }
    
    # Add date range filters if specified
    if START_DATE:
        PARAMS["$where"] = f"crash_date >= '{START_DATE}'"
    if END_DATE:
        if "$where" in PARAMS:
            PARAMS["$where"] += f" AND crash_date <= '{END_DATE}'"
        else:
            PARAMS["$where"] = f"crash_date <= '{END_DATE}'"
    
    try:
        response = requests.get(URL, params=PARAMS, timeout=120)
        data = response.json()
        
        if not data or len(data) == 0:
            print(f"⚠️  No more data available from API")
            break
        
        df = pd.DataFrame(data)
        batch_count = len(df)
        print(f"   📥 Retrieved {batch_count} records from API")
        
        # Show date range of retrieved data
        if 'crash_date' in df.columns:
            dates = df['crash_date'].dropna()
            if len(dates) > 0:
                min_date = dates.min()
                max_date = dates.max()
                print(f"   📅 Date range: {min_date} to {max_date}")
        
        # Create collision keys
        df['_collision_key'] = df.apply(
            lambda row: create_collision_key(row.get('crash_date', ''), row.get('crash_time', '')), 
            axis=1
        )
        
        # Build set of already collected keys
        collected_keys = set()
        if all_new_records:
            for record in all_new_records:
                key = create_collision_key(record.get('crash_date', ''), record.get('crash_time', ''))
                collected_keys.add(key)
        
        # Filter out duplicates (both from DB and from what we've already collected)
        existing_keys_combined = existing_keys.union(collected_keys)
        new_in_batch = df[~df['_collision_key'].isin(existing_keys_combined)]
        
        new_count = len(new_in_batch)
        duplicate_count = batch_count - new_count
        
        print(f"   ✨ Found {new_count} NEW records, {duplicate_count} duplicates")
        
        if new_count == 0:
            print(f"⚠️  No new records in this batch, moving to next offset...")
            offset += fetch_size
            continue
        
        # Add new records to our collection
        new_in_batch = new_in_batch.drop(columns=['_collision_key'])
        all_new_records.extend(new_in_batch.to_dict('records'))
        
        print(f"   📊 Total collected: {len(all_new_records)}/{RECORD_LIMIT}")
        
        # Move offset for next iteration
        offset += fetch_size
        
        # If we got fewer records than requested, we might be at the end
        if batch_count < fetch_size:
            print(f"⚠️  API returned fewer records than requested, likely reached end of dataset")
            break
            
    except Exception as e:
        print(f"❌ Error fetching batch: {e}")
        break

# Limit to exactly what was requested
if len(all_new_records) > RECORD_LIMIT:
    all_new_records = all_new_records[:RECORD_LIMIT]

print(f"\n{'='*80}")
print(f"🎉 Collection complete!")
print(f"   🎯 Requested: {RECORD_LIMIT} new records")
print(f"   ✅ Collected: {len(all_new_records)} new records")
print(f"   🔄 Iterations: {iteration}")
print(f"   📋 Existing records skipped: from {len(existing_keys)} in database")
print(f"{'='*80}\n")

if len(all_new_records) == 0:
    print("✅ No NEW collision data to fetch (all available records already exist in database)")
    df = pd.DataFrame(columns=[
        "crash_date", "crash_time", "persons_injured", "persons_killed",
        "pedestrians_injured", "pedestrians_killed", "cyclists_injured", "cyclists_killed",
        "motorists_injured", "motorists_killed", "factor_1", "factor_2", "factor_3",
        "factor_4", "factor_5", "vehicle_1", "vehicle_2", "vehicle_3", "vehicle_4", "vehicle_5"
    ])
    df.to_csv("collisions_raw.csv", index=False)
    print("✅ Empty CSV created (no new records)")
    exit(0)

# Convert back to DataFrame for processing
df = pd.DataFrame(all_new_records)
print(f"📊 Processing {len(df)} unique new records...")

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
}

# garantir que todas as colunas existem
for col in columns.keys():
    if col not in df.columns:
        df[col] = None

# agora sim, selecionar e renomear
df = df[list(columns.keys())].rename(columns=columns)

df.to_csv("collisions_raw.csv", index=False)

print(f"\n✅ CSV created successfully!")
print(f"   📁 File: collisions_raw.csv")
print(f"   📊 Records: {len(df)} NEW unique collisions")
print(f"   🎯 Target achieved: {len(df)}/{RECORD_LIMIT} ({(len(df)/RECORD_LIMIT*100):.1f}%)")

if len(df) < RECORD_LIMIT:
    print(f"\n⚠️  Note: Could only find {len(df)} new records (requested {RECORD_LIMIT})")
    print(f"   This means you've already loaded most available data from the API.")



