# -*- coding: utf-8 -*-
"""
Download weather_nyc_2025.csv from Supabase Storage Bucket
Used during the merge process to enrich collision data
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL and SUPABASE_KEY must be set in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET_NAME = "dataBucket"
WEATHER_FILE = "weather_nyc_2025.csv"


def download_weather_from_bucket():
    """Download weather data from Supabase Storage bucket"""
    
    # Check if file already exists locally (cached)
    if os.path.exists(WEATHER_FILE):
        file_size = os.path.getsize(WEATHER_FILE) / (1024 * 1024)
        print(f"✅ Weather file already exists locally ({file_size:.2f} MB)")
        print(f"   Using cached version: {WEATHER_FILE}")
        return True
    
    print(f"📥 Downloading '{WEATHER_FILE}' from bucket '{BUCKET_NAME}'...")
    
    try:
        # Download file from bucket
        response = supabase.storage.from_(BUCKET_NAME).download(WEATHER_FILE)
        
        # Save to local file
        with open(WEATHER_FILE, "wb") as f:
            f.write(response)
        
        file_size = os.path.getsize(WEATHER_FILE) / (1024 * 1024)
        print(f"✅ Downloaded: {WEATHER_FILE} ({file_size:.2f} MB)")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        print(f"   Make sure weather data is uploaded to bucket first")
        print(f"   Run: python upload_weather_to_bucket.py")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("🌦️  Download Weather Data from Supabase Bucket")
    print("=" * 70)
    success = download_weather_from_bucket()
    if success:
        print("\n✅ Weather data ready for merging!")
    else:
        print("\n❌ Failed to download weather data")
