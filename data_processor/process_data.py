"""
Data Processor - Fetches CSV from Supabase Storage and sends to XML Service
This bridges the Crawler (Supabase Bucket) to the XML Service (Relational DB)
"""
import os
import csv
import io
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://bkqyppmkssdqwmfjhzop.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
XML_SERVICE_URL = os.getenv("XML_SERVICE_URL", "http://localhost:5000")
BUCKET_NAME = "Data"
FILE_NAME = "collisions_weather.csv"


def download_csv_from_bucket():
    """Download CSV file from Supabase Storage bucket"""
    print(f"📥 Downloading {FILE_NAME} from Supabase bucket '{BUCKET_NAME}'...")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Download file from bucket
        response = supabase.storage.from_(BUCKET_NAME).download(FILE_NAME)
        print(f"✅ Downloaded {len(response)} bytes")
        return response
    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        return None


def parse_csv_data(csv_bytes):
    """Parse CSV bytes into list of dictionaries"""
    print("📊 Parsing CSV data...")
    
    # Decode bytes to string
    csv_string = csv_bytes.decode('utf-8')
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(csv_string))
    records = list(reader)
    
    print(f"✅ Parsed {len(records)} collision records")
    return records


def send_to_xml_service(collisions):
    """Send collision data to XML Service via GraphQL"""
    print(f"📤 Sending {len(collisions)} records to XML Service...")
    
    # GraphQL mutation
    mutation = """
    mutation ImportCollisions($data: [CollisionInput!]!) {
        importCollisionsFromData(data: $data) {
            requestId
            status
            documentId
            error
        }
    }
    """
    
    # Prepare collision data for GraphQL
    collision_inputs = []
    for record in collisions:
        collision_inputs.append({
            "crash_date": record.get("crash_date", ""),
            "crash_time": record.get("crash_time", ""),
            "persons_injured": safe_int(record.get("persons_injured")),
            "persons_killed": safe_int(record.get("persons_killed")),
            "pedestrians_injured": safe_int(record.get("pedestrians_injured")),
            "pedestrians_killed": safe_int(record.get("pedestrians_killed")),
            "cyclists_injured": safe_int(record.get("cyclists_injured")),
            "cyclists_killed": safe_int(record.get("cyclists_killed")),
            "motorists_injured": safe_int(record.get("motorists_injured")),
            "motorists_killed": safe_int(record.get("motorists_killed")),
            "factor_1": record.get("factor_1", ""),
            "factor_2": record.get("factor_2", ""),
            "factor_3": record.get("factor_3", ""),
            "factor_4": record.get("factor_4", ""),
            "factor_5": record.get("factor_5", ""),
            "vehicle_1": record.get("vehicle_1", ""),
            "vehicle_2": record.get("vehicle_2", ""),
            "vehicle_3": record.get("vehicle_3", ""),
            "vehicle_4": record.get("vehicle_4", ""),
            "vehicle_5": record.get("vehicle_5", ""),
            "weather_condition": record.get("weather_condition", "")
        })
    
    # Send to XML Service
    try:
        response = requests.post(
            f"{XML_SERVICE_URL}/graphql",
            json={
                "query": mutation,
                "variables": {"data": collision_inputs}
            },
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout for large datasets
        )
        
        result = response.json()
        
        if "errors" in result:
            print(f"❌ GraphQL errors: {result['errors']}")
            return None
        
        data = result.get("data", {}).get("importCollisionsFromData", {})
        print(f"✅ XML Service response:")
        print(f"   Request ID: {data.get('requestId')}")
        print(f"   Status: {data.get('status')}")
        print(f"   Document ID: {data.get('documentId')}")
        
        if data.get('error'):
            print(f"   Error: {data.get('error')}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error sending to XML Service: {e}")
        return None


def send_to_xml_service_rest(collisions):
    """Alternative: Send via REST API instead of GraphQL"""
    print(f"📤 Sending {len(collisions)} records to XML Service (REST)...")
    
    try:
        response = requests.post(
            f"{XML_SERVICE_URL}/api/import-csv",
            json={"collisions": collisions},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        result = response.json()
        print(f"✅ XML Service response: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error sending to XML Service: {e}")
        return None


def safe_int(value):
    """Safely convert value to integer"""
    try:
        if value is None or value == '' or str(value).lower() == 'nan':
            return 0
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def check_existing_data():
    """Check if there's already data in the XML Service database"""
    print("🔍 Checking for existing data...")
    
    query = """
    query {
        summaryStatistics {
            totalCollisions
            totalDocuments
        }
    }
    """
    
    try:
        response = requests.post(
            f"{XML_SERVICE_URL}/graphql",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "summaryStatistics" in data["data"]:
                stats = data["data"]["summaryStatistics"]
                total_docs = stats.get("totalDocuments", 0)
                total_collisions = stats.get("totalCollisions", 0)
                print(f"📊 Found {total_docs} existing documents with {total_collisions} collisions")
                return total_docs
        
        return 0
    except Exception as e:
        print(f"⚠️ Could not check existing data: {e}")
        return 0


def process_data():
    """Main processing pipeline"""
    print("=" * 60)
    print("🚀 DATA PROCESSOR - Starting")
    print("=" * 60)
    print(f"📦 Source: Supabase Bucket '{BUCKET_NAME}/{FILE_NAME}'")
    print(f"🎯 Target: XML Service at {XML_SERVICE_URL}")
    print("=" * 60)
    
    # Step 1: Download CSV from Supabase bucket
    csv_bytes = download_csv_from_bucket()
    if not csv_bytes:
        print("❌ Failed to download CSV. Aborting.")
        return False
    
    # Step 2: Parse CSV data
    collisions = parse_csv_data(csv_bytes)
    if not collisions:
        print("❌ No collision records found. Aborting.")
        return False
    
    # Step 3: Send to XML Service (creates XML, validates, stores in PostgreSQL)
    result = send_to_xml_service(collisions)
    
    if result and result.get('status') == 'OK':
        print("=" * 60)
        print("✅ DATA PROCESSING COMPLETE!")
        print(f"   Document stored in Supabase PostgreSQL with ID: {result.get('documentId')}")
        print("=" * 60)
        return True
    else:
        print("=" * 60)
        print("❌ DATA PROCESSING FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    process_data()
