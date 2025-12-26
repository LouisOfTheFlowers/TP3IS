"""
Upload collision data CSV to Supabase Storage Bucket
This is the first step in the data pipeline:
  Crawler → Supabase Bucket → Data Processor → XML Service → PostgreSQL
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
FILE_NAME = "collisions_weather.csv"


def ensure_bucket_exists():
    """Create bucket if it doesn't exist"""
    try:
        # Try to get bucket info
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        if BUCKET_NAME not in bucket_names:
            print(f"📦 Creating bucket '{BUCKET_NAME}'...")
            supabase.storage.create_bucket(BUCKET_NAME, options={"public": False})
            print(f"✅ Bucket '{BUCKET_NAME}' created")
        else:
            print(f"✅ Bucket '{BUCKET_NAME}' already exists")
    except Exception as e:
        print(f"⚠️ Bucket check/creation: {e}")


def upload_file():
    """Upload CSV file to Supabase Storage"""
    ensure_bucket_exists()
    
    if not os.path.exists(FILE_NAME):
        print(f"❌ File '{FILE_NAME}' not found. Run the crawler first.")
        return False
    
    print(f"📤 Uploading '{FILE_NAME}' to Supabase Storage bucket '{BUCKET_NAME}'...")
    
    try:
        # Try to remove existing file first (upsert)
        try:
            supabase.storage.from_(BUCKET_NAME).remove([FILE_NAME])
        except:
            pass  # File might not exist
        
        # Upload file
        with open(FILE_NAME, "rb") as f:
            supabase.storage.from_(BUCKET_NAME).upload(
                FILE_NAME,
                f,
                {"content-type": "text/csv"}
            )
        
        print(f"✅ File uploaded to Supabase Storage: {BUCKET_NAME}/{FILE_NAME}")
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False


if __name__ == "__main__":
    upload_file()
