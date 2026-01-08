# -*- coding: utf-8 -*-
"""
Upload weather_nyc_2025.csv to Supabase Storage Bucket (one-time)
This weather file stays in the bucket permanently for all merges
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


def ensure_bucket_exists():
    """Create bucket if it doesn't exist"""
    try:
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        if BUCKET_NAME not in bucket_names:
            print(f"📦 Creating bucket '{BUCKET_NAME}'...")
            supabase.storage.create_bucket(BUCKET_NAME, options={"public": False})
            print(f"✅ Bucket '{BUCKET_NAME}' created")
        else:
            print(f"✅ Bucket '{BUCKET_NAME}' already exists")
    except Exception as e:
        print(f"⚠️  Bucket check/creation: {e}")


def upload_weather_to_bucket():
    """Upload weather data CSV to Supabase Storage (one-time)"""
    ensure_bucket_exists()
    
    if not os.path.exists(WEATHER_FILE):
        print(f"❌ File '{WEATHER_FILE}' not found")
        print(f"   Run: python fetch_weather_2025.py first")
        return False
    
    file_size = os.path.getsize(WEATHER_FILE) / (1024 * 1024)
    print(f"📤 Uploading '{WEATHER_FILE}' ({file_size:.2f} MB) to bucket '{BUCKET_NAME}'...")
    
    try:
        # Try to remove existing file first (in case we're updating)
        try:
            supabase.storage.from_(BUCKET_NAME).remove([WEATHER_FILE])
            print(f"   Removed old version")
        except:
            pass
        
        # Upload file
        with open(WEATHER_FILE, "rb") as f:
            result = supabase.storage.from_(BUCKET_NAME).upload(
                WEATHER_FILE,
                f,
                {"content-type": "text/csv"}
            )
        
        print(f"✅ Weather data uploaded: {BUCKET_NAME}/{WEATHER_FILE}")
        print(f"   This file will be used for all future collision merges")
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("🌦️  Upload Weather Data to Supabase Bucket")
    print("=" * 70)
    success = upload_weather_to_bucket()
    if success:
        print("\n✅ Weather data is now in the bucket and ready for use!")
    else:
        print("\n❌ Failed to upload weather data")
