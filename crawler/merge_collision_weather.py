"""
Merge collision data with weather data by matching date and hour
Downloads both files from Supabase bucket, merges them, and uploads enriched result
"""
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import sys

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "dataBucket"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL and SUPABASE_KEY must be set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def download_from_bucket(filename):
    """Download file from Supabase bucket"""
    try:
        print(f"📥 Downloading {filename} from bucket...")
        data = supabase.storage.from_(BUCKET_NAME).download(filename)
        
        with open(filename, 'wb') as f:
            f.write(data)
        
        print(f"✅ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False

def round_time_to_hour(time_str):
    """Round time to nearest hour"""
    try:
        if pd.isna(time_str) or not time_str:
            return 12  # Default noon
        
        # Parse time (format: HH:MM or HH:MM:SS)
        parts = str(time_str).split(':')
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        
        # Round to nearest hour
        if minute >= 30:
            hour = (hour + 1) % 24
        
        return hour
    except Exception as e:
        print(f"⚠️  Error parsing time '{time_str}': {e}")
        return 12  # Default noon

def merge_collision_weather():
    """Merge collision and weather data by date and hour"""
    try:
        # Read both files
        print("📊 Reading collision data...")
        collisions = pd.read_csv("collisions_raw.csv")
        print(f"   Loaded {len(collisions)} collision records")
        
        print("📊 Reading weather data...")
        weather = pd.read_csv("weather_data.csv")
        print(f"   Loaded {len(weather)} weather records")
        
        # Prepare collision data
        collisions['crash_date'] = pd.to_datetime(collisions['crash_date']).dt.date.astype(str)
        collisions['crash_hour'] = collisions['crash_time'].apply(round_time_to_hour)
        
        # Prepare weather data
        weather['date'] = pd.to_datetime(weather['date']).dt.date.astype(str)
        
        # Debug: Show sample data
        print(f"   Sample collision dates: {collisions['crash_date'].head(3).tolist()}")
        print(f"   Sample collision hours: {collisions['crash_hour'].head(3).tolist()}")
        print(f"   Sample weather dates: {weather['date'].head(3).tolist()}")
        print(f"   Sample weather hours: {weather['hour'].head(3).tolist()}")
        
        # Create merge keys
        collisions['merge_key'] = collisions['crash_date'] + '_' + collisions['crash_hour'].astype(str)
        weather['merge_key'] = weather['date'] + '_' + weather['hour'].astype(str)
        
        print(f"   Sample collision keys: {collisions['merge_key'].head(3).tolist()}")
        print(f"   Sample weather keys: {weather['merge_key'].head(3).tolist()}")
        
        print("🔗 Merging collision and weather data...")
        
        # Merge on date and hour
        merged = collisions.merge(
            weather[['merge_key', 'condition', 'humidity', 'temp_c', 'wind_kph', 'precip_mm', 'visibility_km']],
            on='merge_key',
            how='left'
        )
        
        # Rename condition column to weather_condition
        merged = merged.rename(columns={'condition': 'weather_condition'})
        
        # Drop temporary columns
        merged = merged.drop(columns=['merge_key', 'crash_hour'])
        
        # Fill missing weather data with defaults
        merged['weather_condition'] = merged['weather_condition'].fillna('Unknown')
        merged['humidity'] = merged['humidity'].fillna(50)
        merged['temp_c'] = merged['temp_c'].fillna(15)
        merged['wind_kph'] = merged['wind_kph'].fillna(0)
        merged['precip_mm'] = merged['precip_mm'].fillna(0)
        merged['visibility_km'] = merged['visibility_km'].fillna(10)
        
        # Count successful matches
        matched = merged['weather_condition'].ne('Unknown').sum()
        print(f"✅ Successfully matched {matched}/{len(merged)} collisions with weather data")
        
        # Save enriched data
        merged.to_csv("collisions_weather.csv", index=False)
        print(f"✅ Saved enriched data to collisions_weather.csv")
        
        # Upload enriched file back to bucket
        print("📤 Uploading enriched data back to bucket...")
        try:
            # Remove old file if exists
            try:
                supabase.storage.from_(BUCKET_NAME).remove(["collisions_weather.csv"])
            except:
                pass
            
            # Upload enriched file
            with open("collisions_weather.csv", "rb") as f:
                supabase.storage.from_(BUCKET_NAME).upload(
                    "collisions_weather.csv",
                    f,
                    {"content-type": "text/csv"}
                )
            print(f"✅ Uploaded enriched data to bucket")
        except Exception as e:
            print(f"⚠️  Warning: Could not upload enriched file: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error merging data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔄 Starting collision-weather merge process...")
    
    # Download both files from bucket
    if not download_from_bucket("collisions_raw.csv"):
        print("❌ Failed to download collision data")
        sys.exit(1)
    
    if not download_from_bucket("weather_data.csv"):
        print("❌ Failed to download weather data")
        sys.exit(1)
    
    # Merge the data
    if not merge_collision_weather():
        print("❌ Failed to merge data")
        sys.exit(1)
    
    print("✅ Merge complete!")

if __name__ == "__main__":
    main()
