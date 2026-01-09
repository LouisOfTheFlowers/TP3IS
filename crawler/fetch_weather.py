"""
Fetch weather data for collision time periods
Creates a separate weather dataset with hourly intervals
"""
import requests
import pandas as pd
import os
import sys
from datetime import datetime, timedelta

WEATHER_API_KEY = os.getenv("WEATHERAPI_KEY")
WEATHER_API_URL = "http://api.weatherapi.com/v1/history.json"

# Location for NYC (use coordinates for accuracy)
NYC_LOCATION = "40.7128,-74.0060"  # NYC coordinates

def get_date_range_from_collisions():
    """Get date range from collisions_raw.csv"""
    try:
        df = pd.read_csv("collisions_raw.csv")
        if len(df) == 0:
            print("❌ No collision data found")
            return None, None
        
        # Parse dates
        df['crash_date'] = pd.to_datetime(df['crash_date'])
        
        if len(df) == 0:
            print("❌ No collision data found")
            return None, None
        
        min_date = df['crash_date'].min()
        max_date = df['crash_date'].max()
        
        print(f"📅 Collision date range: {min_date.date()} to {max_date.date()}")
        return min_date, max_date
    except Exception as e:
        print(f"❌ Error reading collision data: {e}")
        return None, None

def fetch_weather_for_date(date):
    """Fetch hourly weather data for a specific date"""
    date_str = date.strftime("%Y-%m-%d")
    
    params = {
        "key": WEATHER_API_KEY,
        "q": NYC_LOCATION,
        "dt": date_str
    }
    
    print(f"   API Request: {WEATHER_API_URL}?key=***&q={NYC_LOCATION}&dt={date_str}")
    
    try:
        response = requests.get(WEATHER_API_URL, params=params, timeout=10)
        print(f"   Response status: {response.status_code}")
        response.raise_for_status()
        data = response.json()
        
        # Debug: Print response structure
        if "error" in data:
            print(f"   ⚠️  API Error: {data['error']}")
            return []
        
        print(f"   Response keys: {data.keys()}")
        
        # Extract hourly data
        hourly_records = []
        if "forecast" in data and "forecastday" in data["forecast"]:
            for day in data["forecast"]["forecastday"]:
                day_date = day.get("date", date_str)
                hours = day.get("hour", [])
                print(f"   Found {len(hours)} hours for {day_date}")
                
                if len(hours) > 0:
                    # Debug first hour
                    first_hour = hours[0]
                    print(f"   Sample hour data keys: {first_hour.keys()}")
                    print(f"   Sample condition: {first_hour.get('condition', {})}")
                
                for hour_data in hours:
                    time_str = hour_data.get("time", "")
                    if " " in time_str:
                        time_part = time_str.split()[1]
                        hour_num = int(time_part.split(":")[0])
                    else:
                        continue
                    
                    # Derive weather condition from available data
                    precip = hour_data.get("precip_mm", 0)
                    snow = hour_data.get("snow_cm", 0)
                    will_rain = hour_data.get("will_it_rain", 0)
                    will_snow = hour_data.get("will_it_snow", 0)
                    
                    if snow > 0:
                        condition = "Snow"
                    elif precip > 0 or will_rain == 1:
                        condition = "Rain"
                    elif precip == 0:
                        condition = "Clear"
                    else:
                        condition = "Cloudy"
                    
                    hourly_records.append({
                        "date": date_str,
                        "time": time_part,
                        "hour": hour_num,
                        "condition": condition,
                        "humidity": hour_data.get("humidity", 50),
                        "temp_c": hour_data.get("temp_c", 0),
                        "wind_kph": hour_data.get("wind_kph", 0),
                        "precip_mm": precip,
                        "visibility_km": hour_data.get("vis_km", 10)
                    })
        else:
            print(f"   ⚠️  No forecast data in response")
        
        return hourly_records
    except Exception as e:
        print(f"⚠️  Error fetching weather for {date_str}: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("🌤️  Fetching weather data...")
    
    if not WEATHER_API_KEY:
        print("❌ WEATHERAPI_KEY environment variable not set")
        sys.exit(1)
    
    # Get date range from collisions
    min_date, max_date = get_date_range_from_collisions()
    
    if not min_date or not max_date:
        print("❌ Could not determine date range")
        sys.exit(1)
    
    # Fetch weather for each date in range
    all_weather_records = []
    current_date = min_date
    
    while current_date <= max_date:
        print(f"📡 Fetching weather for {current_date.date()}...")
        records = fetch_weather_for_date(current_date)
        all_weather_records.extend(records)
        print(f"   ✅ Got {len(records)} hourly records")
        current_date += timedelta(days=1)
    
    if not all_weather_records:
        print("❌ No weather data retrieved")
        sys.exit(1)
    
    # Save to CSV
    weather_df = pd.DataFrame(all_weather_records)
    weather_df.to_csv("weather_data.csv", index=False)
    
    print(f"✅ Weather data saved: {len(weather_df)} hourly records")
    print(f"📊 Date range: {weather_df['date'].min()} to {weather_df['date'].max()}")
    print(f"📊 Hours covered: {weather_df['hour'].min()}:00 to {weather_df['hour'].max()}:00")

if __name__ == "__main__":
    main()
