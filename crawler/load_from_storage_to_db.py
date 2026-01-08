# -*- coding: utf-8 -*-
"""
Load enriched collision data to PostgreSQL Database
This script:
1. Uses the locally generated collisions_enriched.csv file
2. Converts CSV data to XML format (with hierarchical structure)
3. Loads XML documents to PostgreSQL via XML Service webhook endpoint
"""
import os
import sys
import pandas as pd
import requests
from dotenv import load_dotenv
from datetime import datetime
import time

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Configuration
# Auto-detect if running inside or outside Docker
# If running outside Docker (localhost), use localhost:5000
# If running inside Docker, use xml-service:5000
default_xml_service_url = "http://localhost:5000/api/webhook"
if os.path.exists("/.dockerenv"):  # Running inside Docker
    default_xml_service_url = "http://xml-service:5000/api/webhook"

XML_SERVICE_URL = os.getenv("XML_SERVICE_URL", default_xml_service_url)
# Override if it's pointing to graphql (legacy config)
if "/graphql" in XML_SERVICE_URL:
    XML_SERVICE_URL = XML_SERVICE_URL.replace("/graphql", "/api/webhook")

LOCAL_CSV_PATH = "collisions_enriched.csv"
BATCH_SIZE = 100  # Load 100 records at a time (reduced for reliability)

print("=" * 70)
print("📥 Enriched Collision Data to PostgreSQL Loader")
print("=" * 70)

print(f"\n🔗 Configuration:")
print(f"   XML Service: {XML_SERVICE_URL}")
print(f"   Local CSV: {LOCAL_CSV_PATH}")
print(f"   Batch Size: {BATCH_SIZE} records")

# Test XML Service connectivity
print(f"\n🔌 Testing XML Service connectivity...")
try:
    test_response = requests.get(XML_SERVICE_URL.replace('/graphql', '/health'), timeout=5)
    print(f"✅ XML Service is reachable (status: {test_response.status_code})")
except Exception as e:
    print(f"⚠️  Warning: Cannot reach XML Service: {e}")
    print(f"   Make sure the XML Service is running at {XML_SERVICE_URL}")
    print(f"   Continuing anyway (automated pipeline)...")

# Step 1: Check for local enriched CSV file
print(f"\n📥 STEP 1: Checking for local enriched CSV file...")

if not os.path.exists(LOCAL_CSV_PATH):
    print(f"❌ Enriched CSV not found: {LOCAL_CSV_PATH}")
    print(f"   Please run the enrich-weather step first to generate the enriched data.")
    exit(1)

file_size = os.path.getsize(LOCAL_CSV_PATH)
file_size_mb = file_size / (1024 * 1024)
print(f"✅ Found enriched CSV: {file_size_mb:.2f} MB ({file_size:,} bytes)")

# Step 2: Parse CSV
print(f"\n📊 STEP 2: Parsing CSV data...")

try:
    df = pd.read_csv(LOCAL_CSV_PATH, low_memory=False)
    total_records = len(df)
    print(f"✅ Loaded {total_records:,} collision records")
    print(f"   Columns: {list(df.columns)}")
    
except Exception as e:
    print(f"❌ Failed to parse CSV: {e}")
    exit(1)

# Step 3: Convert to collision format and load in batches
print(f"\n💾 STEP 3: Converting and loading data to PostgreSQL...")

def convert_row_to_collision(row):
    """Convert a CSV row to collision input format for GraphQL"""
    return {
        "crash_date": str(row.get("crash_date", "")),
        "crash_time": str(row.get("crash_time", "")) if pd.notna(row.get("crash_time")) else "",
        "persons_injured": int(row.get("persons_injured", 0) or 0),
        "persons_killed": int(row.get("persons_killed", 0) or 0),
        "pedestrians_injured": int(row.get("pedestrians_injured", 0) or 0),
        "pedestrians_killed": int(row.get("pedestrians_killed", 0) or 0),
        "cyclists_injured": int(row.get("cyclists_injured", 0) or 0),
        "cyclists_killed": int(row.get("cyclists_killed", 0) or 0),
        "motorists_injured": int(row.get("motorists_injured", 0) or 0),
        "motorists_killed": int(row.get("motorists_killed", 0) or 0),
        "factor_1": str(row.get("factor_1", "")) if pd.notna(row.get("factor_1")) else "",
        "factor_2": str(row.get("factor_2", "")) if pd.notna(row.get("factor_2")) else "",
        "factor_3": str(row.get("factor_3", "")) if pd.notna(row.get("factor_3")) else "",
        "factor_4": str(row.get("factor_4", "")) if pd.notna(row.get("factor_4")) else "",
        "factor_5": str(row.get("factor_5", "")) if pd.notna(row.get("factor_5")) else "",
        "vehicle_1": str(row.get("vehicle_1", "")) if pd.notna(row.get("vehicle_1")) else "",
        "vehicle_2": str(row.get("vehicle_2", "")) if pd.notna(row.get("vehicle_2")) else "",
        "vehicle_3": str(row.get("vehicle_3", "")) if pd.notna(row.get("vehicle_3")) else "",
        "vehicle_4": str(row.get("vehicle_4", "")) if pd.notna(row.get("vehicle_4")) else "",
        "vehicle_5": str(row.get("vehicle_5", "")) if pd.notna(row.get("vehicle_5")) else "",
        # Weather data from enriched CSV (merged from weather_nyc_2025.csv)
        "weather_condition": str(row.get("weather", "")) if pd.notna(row.get("weather")) else "",
        "weather_detail": str(row.get("weather_detail", "")) if pd.notna(row.get("weather_detail")) else "",
        "temperature_f": float(row.get("temp_fahrenheit", 0)) if pd.notna(row.get("temp_fahrenheit")) else None,
        "temperature_c": float(row.get("temp_celsius", 0)) if pd.notna(row.get("temp_celsius")) else None,
        "humidity": float(row.get("humidity_pct", 0)) if pd.notna(row.get("humidity_pct")) else None,
        "precipitation": float(row.get("precipitation", 0)) if pd.notna(row.get("precipitation")) else None,
        "wind_speed": float(row.get("wind_speed", 0)) if pd.notna(row.get("wind_speed")) else None,
        "visibility": float(row.get("visibility_m", 0)) if pd.notna(row.get("visibility_m")) else None,
    }

# Calculate number of batches
num_batches = (total_records + BATCH_SIZE - 1) // BATCH_SIZE
print(f"   Processing {num_batches} batches of {BATCH_SIZE} records each...")

successful_batches = 0
failed_batches = 0
total_loaded = 0

for batch_num in range(num_batches):
    start_idx = batch_num * BATCH_SIZE
    end_idx = min(start_idx + BATCH_SIZE, total_records)
    batch_df = df.iloc[start_idx:end_idx]
    
    print(f"\n[Batch {batch_num + 1}/{num_batches}] Records {start_idx + 1}-{end_idx}...")
    
    try:
        # Convert batch to collision format
        collisions = []
        for _, row in batch_df.iterrows():
            collisions.append(convert_row_to_collision(row))
        
        # Send REST request to webhook endpoint
        payload = {
            "collisions": collisions
        }
        
        response = requests.post(
            XML_SERVICE_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                print(f"   ✅ Loaded successfully")
                print(f"      Request ID: {data.get('request_id')}")
                print(f"      Document ID: {data.get('document_id')}")
                print(f"      Status: {data.get('status')}")
                successful_batches += 1
                total_loaded += len(collisions)
            else:
                error = result.get("error", "Unknown error")
                print(f"   ❌ Failed: {error}")
                failed_batches += 1
        else:
            print(f"   ❌ HTTP {response.status_code}")
            print(f"      Response: {response.text[:500]}")
            failed_batches += 1
        
        # Small delay between batches to avoid overwhelming the service
        if batch_num < num_batches - 1:
            time.sleep(0.5)
        
    except Exception as e:
        print(f"   ❌ Batch failed: {e}")
        failed_batches += 1

# Summary
print("\n" + "=" * 70)
print("📊 Loading Summary")
print("=" * 70)
print(f"Total records in CSV: {total_records:,}")
print(f"Successful batches: {successful_batches}/{num_batches}")
print(f"Failed batches: {failed_batches}/{num_batches}")
print(f"Records loaded: {total_loaded:,}")
print(f"Success rate: {(successful_batches/num_batches*100):.1f}%")

if successful_batches == num_batches:
    print("\n🎉 All data loaded successfully into PostgreSQL!")
    print("   ✅ Data stored as XML in collision_documents table")
    print("   ✅ Ready for XPath queries via GraphQL")
elif successful_batches > 0:
    print(f"\n⚠️  Partial success: {successful_batches}/{num_batches} batches loaded")
else:
    print("\n❌ No data was loaded successfully")

print("=" * 70)

# Cleanup
if os.path.exists(LOCAL_CSV_PATH):
    os.remove(LOCAL_CSV_PATH)
    print(f"\n🧹 Cleaned up temporary file: {LOCAL_CSV_PATH}")
