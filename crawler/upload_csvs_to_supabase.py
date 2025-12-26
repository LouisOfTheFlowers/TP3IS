# -*- coding: utf-8 -*-
"""
Upload CSV files to Supabase Storage Bucket
Uploads collision data CSVs to the dataBucket in Supabase
Uses Supabase Python SDK
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "dataBucket"

# CSV files to upload
CSV_FILES = [
    "collisions_raw.csv",
    "collisions_weather.csv"
]

print("=" * 60)
print("📤 Supabase Storage Upload")
print("=" * 60)

# Validate environment variables
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY in environment variables")
    exit(1)

print(f"\n🔗 Connecting to Supabase...")
print(f"   URL: {SUPABASE_URL}")

try:
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase")
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    exit(1)

# Upload each CSV file
print(f"\n📦 Target bucket: {BUCKET_NAME}")
successful_uploads = 0
failed_uploads = 0

for csv_file in CSV_FILES:
    print(f"\n📄 Processing: {csv_file}")
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"   ⚠️  File not found: {csv_file}")
        failed_uploads += 1
        continue
    
    # Get file size
    file_size = os.path.getsize(csv_file)
    file_size_mb = file_size / (1024 * 1024)
    print(f"   📊 File size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
    
    try:
        # Read file content
        print(f"   📖 Reading file...")
        with open(csv_file, 'rb') as f:
            file_content = f.read()
        
        # Upload to Supabase Storage (with upsert to overwrite if exists)
        print(f"   ⬆️  Uploading to bucket '{BUCKET_NAME}'...")
        
        response = supabase.storage.from_(BUCKET_NAME).upload(
            path=csv_file,
            file=file_content,
            file_options={"content-type": "text/csv", "upsert": "true"}
        )
        
        print(f"   ✅ Successfully uploaded: {csv_file}")
        successful_uploads += 1
        
        # Get public URL
        try:
            public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(csv_file)
            print(f"   🔗 Storage path: {csv_file}")
        except Exception as url_error:
            print(f"   ℹ️  Could not get URL: {url_error}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Upload failed: {error_msg}")
        failed_uploads += 1

# Summary
print("\n" + "=" * 60)
print("📊 Upload Summary")
print("=" * 60)
print(f"✅ Successful uploads: {successful_uploads}")
print(f"❌ Failed uploads: {failed_uploads}")
print(f"📁 Total files processed: {len(CSV_FILES)}")

if successful_uploads == len(CSV_FILES):
    print("\n🎉 All files uploaded successfully!")
elif successful_uploads > 0:
    print(f"\n⚠️  Partial success: {successful_uploads}/{len(CSV_FILES)} files uploaded")
else:
    print("\n❌ No files were uploaded successfully")

print("=" * 60)
