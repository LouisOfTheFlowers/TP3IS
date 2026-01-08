# -*- coding: utf-8 -*-
"""
Upload raw collision data to Supabase Storage Bucket
This is temporary data that gets merged with weather and then loaded to PostgreSQL
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
RAW_FILE = "collisions_raw.csv"


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


def upload_raw_collisions():
    """Upload raw collision CSV to Supabase Storage"""
    ensure_bucket_exists()
    
    if not os.path.exists(RAW_FILE):
        print(f"❌ File '{RAW_FILE}' not found")
        return False
    
    file_size = os.path.getsize(RAW_FILE) / (1024 * 1024)
    print(f"📤 Uploading '{RAW_FILE}' ({file_size:.2f} MB) to bucket '{BUCKET_NAME}'...")
    
    try:
        # Try to remove existing file first (upsert)
        try:
            supabase.storage.from_(BUCKET_NAME).remove([RAW_FILE])
        except:
            pass
        
        # Upload file
        with open(RAW_FILE, "rb") as f:
            supabase.storage.from_(BUCKET_NAME).upload(
                RAW_FILE,
                f,
                {"content-type": "text/csv"}
            )
        
        print(f"✅ Uploaded raw collisions: {BUCKET_NAME}/{RAW_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False


if __name__ == "__main__":
    upload_raw_collisions()
