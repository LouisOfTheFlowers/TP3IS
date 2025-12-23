import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET_NAME = "Data"
FILE_NAME = "collisions_weather.csv"

with open(FILE_NAME, "rb") as f:
    supabase.storage.from_(BUCKET_NAME).upload(
        FILE_NAME,
        f,
        {"content-type": "text/csv"}
    )

print("✅ File uploaded to Supabase Storage")
