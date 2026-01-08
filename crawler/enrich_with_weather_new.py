# -*- coding: utf-8 -*-
"""
Weather Enrichment using WeatherAPI.com
Fetches hourly weather data for NYC collision dates
"""
import pandas as pd
import requests
import time
import os
from datetime import datetime

# WeatherAPI.com configuration
API_KEY = os.getenv("WEATHERAPI_KEY", "f1d9335f3cd940b1910154917252612")
LOCATION = "New York"  # NYC
BASE_URL = "http://api.weatherapi.com/v1/history.json"

print(f"🔑 Using WeatherAPI.com with key: {API_KEY[:8]}...{API_KEY[-4:]}")

# Request settings
REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RATE_LIMIT_DELAY = 1  # delay between successful requests

print("=" * 60)
print("🌦️  Weather Enrichment - WeatherAPI.com")
print("=" * 60)

# Load collision data
print("\n📄 Loading collisions_raw.csv...")
try:
    df = pd.read_csv("collisions_raw.csv")
    print(f"✅ Loaded {len(df)} collision records")
except FileNotFoundError:
    print("❌ Error: collisions_raw.csv not found!")
    print("   Run fetch_collisions.py first to generate the CSV file.")
    exit(1)

# Extract date and hour from collision data
df["date"] = df["crash_date"].astype(str).str.slice(0, 10)

def parse_hour(t):
    """Extract hour from time string (HH:MM format)"""
    try:
        hour = int(str(t).split(":")[0])
        return hour if 0 <= hour <= 23 else None
    except:
        return None

df["hour"] = df["crash_time"].apply(parse_hour)

# Get unique dates to fetch weather for
unique_dates = df["date"].dropna().unique()
print(f"📆 Found {len(unique_dates)} unique dates to fetch weather data")

# Fetch weather data for each date
weather_by_date_hour = {}
successful_dates = 0
failed_dates = 0

for idx, date in enumerate(unique_dates, 1):
    print(f"\n[{idx}/{len(unique_dates)}] 🌦️  Fetching weather for {date}...")
    
    # WeatherAPI.com uses date format: YYYY-MM-DD
    params = {
        "key": API_KEY,
        "q": LOCATION,
        "dt": date
    }
    
    # Retry logic
    success = False
    response = None
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                success = True
                break
            elif response.status_code == 429:
                print(f"   ⚠️  Rate limited, waiting {RETRY_DELAY * 2}s...")
                time.sleep(RETRY_DELAY * 2)
            elif response.status_code == 400:
                print(f"   ⚠️  Bad request (date might be in future or invalid)")
                break
            else:
                print(f"   ⚠️  HTTP {response.status_code}, attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout on attempt {attempt + 1}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request error: {str(e)[:50]}...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    if not success or response is None:
        print(f"   ❌ Failed to fetch weather for {date} after {MAX_RETRIES} attempts")
        failed_dates += 1
        continue
    
    # Parse JSON response
    try:
        data = response.json()
    except Exception as e:
        print(f"   ❌ Failed to parse JSON: {e}")
        failed_dates += 1
        continue
    
    # Extract hourly weather data
    if "forecast" not in data or "forecastday" not in data["forecast"]:
        print(f"   ⚠️  No forecast data found for {date}")
        failed_dates += 1
        continue
    
    forecast_day = data["forecast"]["forecastday"][0]
    
    if "hour" not in forecast_day:
        print(f"   ⚠️  No hourly data found for {date}")
        failed_dates += 1
        continue
    
    # Store weather by hour for this date
    hourly_data = {}
    first_hour_logged = False
    for hour_data in forecast_day["hour"]:
        # Extract hour from time string (format: "YYYY-MM-DD HH:MM")
        time_str = hour_data["time"]
        hour = int(time_str.split(" ")[1].split(":")[0])
        
        # Debug: Log first hour's full data structure
        if not first_hour_logged:
            print(f"   DEBUG - Hour data keys: {list(hour_data.keys())}")
            print(f"   DEBUG - Condition field: {hour_data.get('condition', 'NOT FOUND')}")
            first_hour_logged = True
        
        # Get actual weather condition from API
        condition_data = hour_data.get("condition", {})
        if isinstance(condition_data, dict):
            condition = condition_data.get("text", "Unknown")
        else:
            condition = str(condition_data) if condition_data else "Unknown"
        
        # If condition is still Unknown, derive from precipitation
        if condition == "Unknown":
            precip = hour_data.get("precip_mm", 0)
            will_rain = hour_data.get("will_it_rain", 0)
            will_snow = hour_data.get("will_it_snow", 0)
            
            if will_snow == 1 or hour_data.get("snow_cm", 0) > 0:
                condition = "Snow"
            elif will_rain == 1 or precip > 0:
                condition = "Rain"
            elif hour_data.get("cloud", 0) > 50:
                condition = "Cloudy"
            else:
                condition = "Clear"
        
        # Get actual humidity from API
        humidity = hour_data.get("humidity", 50)
        
        # Get precipitation
        precip_mm = hour_data.get("precip_mm", 0)
        
        # Store the 3 requested fields with actual API data
        hourly_data[hour] = {
            "condition": condition,
            "humidity": humidity,
            "precip_mm": precip_mm
        }
    
    weather_by_date_hour[date] = hourly_data
    successful_dates += 1
    print(f"   ✅ Got weather data for {len(hourly_data)} hours")
    
    # Rate limiting - small delay between requests
    if idx < len(unique_dates):
        time.sleep(RATE_LIMIT_DELAY)

print("\n" + "=" * 60)
print(f"✅ Weather fetch complete!")
print(f"   Successful: {successful_dates} dates")
print(f"   Failed: {failed_dates} dates")
print("=" * 60)

# Enrich collision data with weather
print("\n🔄 Enriching collision data with weather information...")

def map_weather(row):
    """Map weather data to collision row based on date and hour"""
    date = row["date"]
    hour = row["hour"]
    
    # Check if we have weather data for this date
    if pd.isna(date) or date not in weather_by_date_hour:
        return pd.Series({
            "weather_condition": None,
            "humidity": None,
            "precipitation_mm": None
        })
    
    # Check if we have data for this specific hour
    date_weather = weather_by_date_hour[date]
    if pd.isna(hour) or hour not in date_weather:
        # Use data from noon (12:00) as fallback
        hour = 12 if 12 in date_weather else list(date_weather.keys())[0]
    
    weather_info = date_weather.get(hour, {})
    
    return pd.Series({
        "weather_condition": weather_info.get("condition"),
        "humidity": weather_info.get("humidity"),
        "precipitation_mm": weather_info.get("precip_mm")
    })

# Apply weather mapping
weather_columns = df.apply(map_weather, axis=1)
df_enriched = pd.concat([df, weather_columns], axis=1)

# Count how many rows got weather data
enriched_count = df_enriched["weather_condition"].notna().sum()
print(f"✅ Enriched {enriched_count}/{len(df_enriched)} collision records with weather data")

# Save enriched data
output_file = "collisions_weather.csv"
df_enriched.to_csv(output_file, index=False)
print(f"\n💾 Saved enriched data to: {output_file}")

print("\n" + "=" * 60)
print("✅ Weather enrichment complete!")
print("=" * 60)
print(f"\nOutput file: {output_file}")
print(f"Total records: {len(df_enriched)}")
print(f"Records with weather: {enriched_count}")
print(f"Records without weather: {len(df_enriched) - enriched_count}")
