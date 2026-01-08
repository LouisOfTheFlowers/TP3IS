# -*- coding: utf-8 -*-
"""
Weather Data Fetcher for NYC - Full Year 2025
Downloads hourly weather data for every day in 2025 and saves to CSV.
Uses Open-Meteo API (free, no key required, historical data available)
"""
import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# NYC coordinates
NYC_LAT = 40.7128
NYC_LON = -74.0060

# Open-Meteo Historical Weather API (free, no API key needed!)
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Request settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2
BATCH_SIZE = 30  # Days per request (Open-Meteo allows large date ranges)

OUTPUT_FILE = "weather_nyc_2025.csv"

print("=" * 70)
print("🌦️  NYC Weather Data Fetcher - Full Year 2025 (Hourly)")
print("=" * 70)
print(f"📍 Location: New York City ({NYC_LAT}, {NYC_LON})")
print(f"📅 Period: January 1, 2025 to December 31, 2025")
print(f"⏰ Interval: Hourly (8,760 records)")
print(f"💾 Output: {OUTPUT_FILE}")
print("=" * 70)


def fetch_weather_batch(start_date: str, end_date: str) -> list:
    """
    Fetch weather data for a date range from Open-Meteo API.
    Returns list of hourly weather records.
    """
    params = {
        "latitude": NYC_LAT,
        "longitude": NYC_LON,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "snowfall",
            "snow_depth",
            "weather_code",
            "cloud_cover",
            "visibility",
            "wind_speed_10m",
            "wind_gusts_10m"
        ],
        "timezone": "America/New_York"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                return parse_weather_response(data)
            elif response.status_code == 429:
                print(f"   ⚠️  Rate limited, waiting {RETRY_DELAY * 3}s...")
                time.sleep(RETRY_DELAY * 3)
            else:
                print(f"   ⚠️  HTTP {response.status_code} for {start_date} to {end_date}, attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout for {start_date} to {end_date}, attempt {attempt + 1}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request error: {str(e)[:60]}...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    return []


def parse_weather_response(data: dict) -> list:
    """Parse Open-Meteo response into list of weather records"""
    records = []
    
    if "hourly" not in data:
        return records
    
    hourly = data["hourly"]
    times = hourly.get("time", [])
    
    for i, time_str in enumerate(times):
        # Parse datetime
        dt = datetime.fromisoformat(time_str)
        
        # Get weather code and convert to condition
        weather_code = hourly.get("weather_code", [None])[i]
        condition = weather_code_to_condition(weather_code)
        
        # Get precipitation values
        precipitation = hourly.get("precipitation", [0])[i] or 0
        rain = hourly.get("rain", [0])[i] or 0
        snowfall = hourly.get("snowfall", [0])[i] or 0
        
        record = {
            "datetime": time_str,
            "date": dt.strftime("%Y-%m-%d"),
            "hour": dt.hour,
            "temperature_c": hourly.get("temperature_2m", [None])[i],
            "humidity_pct": hourly.get("relative_humidity_2m", [None])[i],
            "precipitation_mm": precipitation,
            "rain_mm": rain,
            "snowfall_cm": snowfall,
            "snow_depth_m": hourly.get("snow_depth", [None])[i],
            "weather_code": weather_code,
            "weather_condition": condition,
            "cloud_cover_pct": hourly.get("cloud_cover", [None])[i],
            "visibility_m": hourly.get("visibility", [None])[i],
            "wind_speed_kmh": hourly.get("wind_speed_10m", [None])[i],
            "wind_gusts_kmh": hourly.get("wind_gusts_10m", [None])[i]
        }
        records.append(record)
    
    return records


def weather_code_to_condition(code) -> str:
    """
    Convert WMO weather code to human-readable condition.
    https://open-meteo.com/en/docs
    """
    if code is None:
        return "Unknown"
    
    # WMO Weather interpretation codes
    conditions = {
        0: "Clear",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing Rime Fog",
        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",
        56: "Light Freezing Drizzle",
        57: "Dense Freezing Drizzle",
        61: "Slight Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",
        66: "Light Freezing Rain",
        67: "Heavy Freezing Rain",
        71: "Slight Snow",
        73: "Moderate Snow",
        75: "Heavy Snow",
        77: "Snow Grains",
        80: "Slight Rain Showers",
        81: "Moderate Rain Showers",
        82: "Violent Rain Showers",
        85: "Slight Snow Showers",
        86: "Heavy Snow Showers",
        95: "Thunderstorm",
        96: "Thunderstorm with Slight Hail",
        99: "Thunderstorm with Heavy Hail"
    }
    
    return conditions.get(code, f"Code_{code}")


def get_simplified_condition(condition: str, precipitation: float, snowfall: float) -> str:
    """
    Simplify weather condition to match collision data categories.
    Returns: Clear, Rain, Snow, Fog, Cloudy, Other
    """
    condition_lower = condition.lower()
    
    # Snow conditions
    if snowfall > 0 or "snow" in condition_lower:
        return "Snow"
    
    # Rain conditions
    if precipitation > 0 or "rain" in condition_lower or "drizzle" in condition_lower:
        return "Rain"
    
    # Fog conditions
    if "fog" in condition_lower:
        return "Fog"
    
    # Thunderstorm (treat as rain)
    if "thunder" in condition_lower:
        return "Rain"
    
    # Cloudy conditions
    if "cloud" in condition_lower or "overcast" in condition_lower:
        return "Cloudy"
    
    # Clear conditions
    if "clear" in condition_lower:
        return "Clear"
    
    return "Other"


def main():
    """Main function to fetch all 2025 weather data"""
    
    # Define date range for 2025
    start = datetime(2025, 1, 1)
    end = datetime(2025, 12, 31)
    
    # Generate batches (Open-Meteo can handle large ranges, but we'll batch for progress tracking)
    batches = []
    current = start
    while current <= end:
        batch_end = min(current + timedelta(days=BATCH_SIZE - 1), end)
        batches.append((current.strftime("%Y-%m-%d"), batch_end.strftime("%Y-%m-%d")))
        current = batch_end + timedelta(days=1)
    
    print(f"\n📦 Fetching data in {len(batches)} batches of ~{BATCH_SIZE} days each...")
    print("-" * 70)
    
    all_records = []
    
    for idx, (batch_start, batch_end) in enumerate(batches, 1):
        print(f"\n[{idx}/{len(batches)}] 🌦️  Fetching {batch_start} to {batch_end}...")
        
        records = fetch_weather_batch(batch_start, batch_end)
        
        if records:
            all_records.extend(records)
            print(f"   ✅ Got {len(records)} hourly records")
        else:
            print(f"   ❌ Failed to fetch batch {batch_start} to {batch_end}")
        
        # Small delay between requests to be nice to the API
        if idx < len(batches):
            time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print(f"📊 Total records fetched: {len(all_records)}")
    
    if len(all_records) == 0:
        print("❌ No weather data fetched! Check your internet connection.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(all_records)
    
    # Add simplified condition for merging with collision data
    df["simple_condition"] = df.apply(
        lambda row: get_simplified_condition(
            row["weather_condition"],
            row["precipitation_mm"] or 0,
            row["snowfall_cm"] or 0
        ),
        axis=1
    )
    
    # Convert temperature to Fahrenheit for US users
    df["temperature_f"] = df["temperature_c"].apply(lambda x: (x * 9/5) + 32 if x is not None else None)
    
    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved to {OUTPUT_FILE}")
    
    # Print statistics
    print("\n" + "=" * 70)
    print("📈 Weather Statistics for NYC 2025:")
    print("-" * 70)
    
    condition_counts = df["simple_condition"].value_counts()
    print("\n🌤️  Weather Condition Distribution:")
    for condition, count in condition_counts.items():
        pct = (count / len(df)) * 100
        print(f"   {condition}: {count} hours ({pct:.1f}%)")
    
    print(f"\n🌡️  Temperature Range: {df['temperature_f'].min():.1f}°F to {df['temperature_f'].max():.1f}°F")
    print(f"🌧️  Total Precipitation Days: {df[df['precipitation_mm'] > 0]['date'].nunique()}")
    print(f"❄️  Total Snow Days: {df[df['snowfall_cm'] > 0]['date'].nunique()}")
    
    # Monthly breakdown
    df["month"] = pd.to_datetime(df["date"]).dt.month
    monthly_precip = df.groupby("month")["precipitation_mm"].sum()
    
    print("\n📅 Monthly Precipitation (mm):")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for month_num, total in monthly_precip.items():
        print(f"   {months[month_num-1]}: {total:.1f}mm")
    
    print("\n✅ Weather data ready for merging with collision data!")
    print(f"   Run: python merge_weather_collisions.py")


if __name__ == "__main__":
    main()
