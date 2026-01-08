# -*- coding: utf-8 -*-
"""
Merge Collision Data with Pre-downloaded Weather Data
Uses the weather_nyc_2025.csv file to enrich collision records
"""
import pandas as pd
import os
from datetime import datetime

COLLISION_FILE = "collisions_raw.csv"
WEATHER_FILE = "weather_nyc_2025.csv"
OUTPUT_FILE = "collisions_enriched.csv"

print("=" * 70)
print("🔗 Collision-Weather Data Merger")
print("=" * 70)

# Check if files exist
if not os.path.exists(COLLISION_FILE):
    print(f"❌ Error: {COLLISION_FILE} not found!")
    print("   Run the scraper first to generate collision data.")
    exit(1)

if not os.path.exists(WEATHER_FILE):
    print(f"❌ Error: {WEATHER_FILE} not found!")
    print("   Run: python fetch_weather_2025.py")
    exit(1)

# Load collision data
print(f"\n📄 Loading collision data from {COLLISION_FILE}...")
df_collisions = pd.read_csv(COLLISION_FILE)
print(f"   ✅ Loaded {len(df_collisions)} collision records")

# Preview collision columns
print(f"   Columns: {list(df_collisions.columns)}")

# Load weather data
print(f"\n🌦️  Loading weather data from {WEATHER_FILE}...")
df_weather = pd.read_csv(WEATHER_FILE)
print(f"   ✅ Loaded {len(df_weather)} hourly weather records")

# Preview weather data
print(f"   Date range: {df_weather['date'].min()} to {df_weather['date'].max()}")
print(f"   Weather conditions: {df_weather['simple_condition'].unique()}")

# ============================================================================
# Prepare collision data for merging
# ============================================================================
print("\n🔧 Preparing collision data for merge...")

# Extract date from crash_date
df_collisions["merge_date"] = pd.to_datetime(df_collisions["crash_date"]).dt.strftime("%Y-%m-%d")

# Extract hour from crash_time
def extract_hour(time_val):
    """Extract hour from time string (HH:MM or H:MM format)"""
    try:
        if pd.isna(time_val):
            return None
        time_str = str(time_val).strip()
        
        # Handle different time formats
        if ":" in time_str:
            hour = int(time_str.split(":")[0])
            return hour if 0 <= hour <= 23 else None
        return None
    except:
        return None

df_collisions["merge_hour"] = df_collisions["crash_time"].apply(extract_hour)

# Check how many have valid hours
valid_hours = df_collisions["merge_hour"].notna().sum()
print(f"   ✅ {valid_hours}/{len(df_collisions)} records have valid hours")

# Filter collisions to 2025 only (weather data is for 2025)
df_collisions_2025 = df_collisions[
    (df_collisions["merge_date"] >= "2025-01-01") & 
    (df_collisions["merge_date"] <= "2025-12-31")
].copy()
print(f"   ✅ {len(df_collisions_2025)} collisions are from 2025")

# ============================================================================
# Prepare weather data for merging
# ============================================================================
print("\n🌦️  Preparing weather data for merge...")

# Rename columns for clarity after merge
df_weather_merge = df_weather.rename(columns={
    "date": "merge_date",
    "hour": "merge_hour"
})

# Select only columns we need for merge
weather_columns = [
    "merge_date",
    "merge_hour",
    "temperature_c",
    "temperature_f",
    "humidity_pct",
    "precipitation_mm",
    "rain_mm",
    "snowfall_cm",
    "weather_code",
    "weather_condition",
    "simple_condition",
    "cloud_cover_pct",
    "visibility_m",
    "wind_speed_kmh",
    "wind_gusts_kmh"
]

df_weather_merge = df_weather_merge[weather_columns]
print(f"   ✅ Weather data ready with {len(weather_columns)} columns")

# ============================================================================
# Merge datasets
# ============================================================================
print("\n🔗 Merging datasets...")

# Merge on date and hour
df_merged = pd.merge(
    df_collisions_2025,
    df_weather_merge,
    on=["merge_date", "merge_hour"],
    how="left"
)

print(f"   ✅ Merged dataset: {len(df_merged)} records")

# Check merge success rate
matched = df_merged["simple_condition"].notna().sum()
unmatched = df_merged["simple_condition"].isna().sum()
print(f"   ✅ Matched with weather: {matched} ({(matched/len(df_merged))*100:.1f}%)")
print(f"   ⚠️  No weather match: {unmatched} ({(unmatched/len(df_merged))*100:.1f}%)")

# Fill missing weather with nearest hour or default
if unmatched > 0:
    print("\n🔄 Filling missing weather data...")
    
    # For records without exact hour match, fill with default (most common condition for that date)
    for idx, row in df_merged[df_merged["simple_condition"].isna()].iterrows():
        date = row["merge_date"]
        
        # Get most common weather for that date
        date_weather = df_weather_merge[df_weather_merge["merge_date"] == date]
        
        if len(date_weather) > 0:
            # Use the most common condition for that day
            most_common = date_weather["simple_condition"].mode()
            if len(most_common) > 0:
                df_merged.at[idx, "simple_condition"] = most_common.iloc[0]
                df_merged.at[idx, "weather_condition"] = date_weather["weather_condition"].mode().iloc[0]
                # Use daily average temperature
                df_merged.at[idx, "temperature_f"] = date_weather["temperature_f"].mean()
                df_merged.at[idx, "temperature_c"] = date_weather["temperature_c"].mean()
    
    filled = df_merged["simple_condition"].notna().sum()
    print(f"   ✅ After filling: {filled}/{len(df_merged)} have weather data")

# ============================================================================
# Create final output columns
# ============================================================================
print("\n📋 Creating final output...")

# Rename weather columns for final output
df_merged = df_merged.rename(columns={
    "simple_condition": "weather",
    "weather_condition": "weather_detail",
    "temperature_f": "temp_fahrenheit",
    "temperature_c": "temp_celsius",
    "precipitation_mm": "precipitation",
    "wind_speed_kmh": "wind_speed"
})

# Drop merge helper columns
df_merged = df_merged.drop(columns=["merge_date", "merge_hour"], errors="ignore")

# Save to CSV
df_merged.to_csv(OUTPUT_FILE, index=False)
print(f"\n💾 Saved enriched data to {OUTPUT_FILE}")

# ============================================================================
# Statistics
# ============================================================================
print("\n" + "=" * 70)
print("📊 Enriched Dataset Statistics")
print("=" * 70)

# Weather distribution
weather_dist = df_merged["weather"].value_counts()
print("\n🌤️  Weather Condition Distribution:")
for condition, count in weather_dist.items():
    pct = (count / len(df_merged)) * 100
    bar = "█" * int(pct / 2)
    print(f"   {condition:12s}: {count:5d} ({pct:5.1f}%) {bar}")

# Temperature stats
if df_merged["temp_fahrenheit"].notna().any():
    print(f"\n🌡️  Temperature Range: {df_merged['temp_fahrenheit'].min():.1f}°F to {df_merged['temp_fahrenheit'].max():.1f}°F")
    print(f"   Average: {df_merged['temp_fahrenheit'].mean():.1f}°F")

# Collisions by weather
print("\n🚗 Collisions by Weather Condition:")
for condition in ["Clear", "Rain", "Snow", "Cloudy", "Fog", "Other"]:
    count = len(df_merged[df_merged["weather"] == condition])
    if count > 0:
        pct = (count / len(df_merged)) * 100
        avg_injuries = df_merged[df_merged["weather"] == condition].get("number_of_persons_injured", pd.Series([0])).mean()
        print(f"   {condition:12s}: {count:5d} collisions ({pct:5.1f}%), avg injuries: {avg_injuries:.2f}")

print("\n✅ Done! Enriched data saved to:", OUTPUT_FILE)
print("   You can now upload this to Supabase or use it for analysis.")
