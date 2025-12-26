"""
Load collision data from Supabase Storage to PostgreSQL database via XML Service
This is the final step: Download CSV from bucket → Parse → Insert into DB
"""
import os
import requests
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
XML_SERVICE_URL = os.getenv("XML_SERVICE_URL", "http://xml-service:5000/graphql")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL and SUPABASE_KEY must be set in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET_NAME = "dataBucket"
FILE_NAME = "collisions_weather.csv"
LOCAL_FILE = "/tmp/collisions_weather_download.csv"


def download_from_bucket():
    """Download CSV from Supabase Storage bucket"""
    print(f"📥 Downloading '{FILE_NAME}' from Supabase Storage bucket '{BUCKET_NAME}'...")
    
    try:
        # Download file from Supabase Storage
        response = supabase.storage.from_(BUCKET_NAME).download(FILE_NAME)
        
        # Save to local file
        with open(LOCAL_FILE, 'wb') as f:
            f.write(response)
        
        print(f"✅ File downloaded successfully to {LOCAL_FILE}")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False


def parse_csv_to_collisions():
    """Parse CSV file and convert to collision data format"""
    print(f"📊 Parsing CSV file...")
    
    try:
        df = pd.read_csv(LOCAL_FILE)
        
        # Convert DataFrame to list of dictionaries
        collisions = []
        for _, row in df.iterrows():
            collision = {
                "crashDate": str(row.get("crash_date", "")),
                "crashTime": str(row.get("crash_time", "")),
                "personsInjured": int(row.get("persons_injured", 0) or 0),
                "personsKilled": int(row.get("persons_killed", 0) or 0),
                "pedestriansInjured": int(row.get("pedestrians_injured", 0) or 0),
                "pedestriansKilled": int(row.get("pedestrians_killed", 0) or 0),
                "cyclistsInjured": int(row.get("cyclists_injured", 0) or 0),
                "cyclistsKilled": int(row.get("cyclists_killed", 0) or 0),
                "motoristsInjured": int(row.get("motorists_injured", 0) or 0),
                "motoristsKilled": int(row.get("motorists_killed", 0) or 0),
                "contributingFactors": [
                    str(row.get("factor_1", "")).strip() if pd.notna(row.get("factor_1")) else None,
                    str(row.get("factor_2", "")).strip() if pd.notna(row.get("factor_2")) else None,
                    str(row.get("factor_3", "")).strip() if pd.notna(row.get("factor_3")) else None,
                    str(row.get("factor_4", "")).strip() if pd.notna(row.get("factor_4")) else None,
                    str(row.get("factor_5", "")).strip() if pd.notna(row.get("factor_5")) else None,
                ],
                "vehicleTypes": [
                    str(row.get("vehicle_1", "")).strip() if pd.notna(row.get("vehicle_1")) else None,
                    str(row.get("vehicle_2", "")).strip() if pd.notna(row.get("vehicle_2")) else None,
                    str(row.get("vehicle_3", "")).strip() if pd.notna(row.get("vehicle_3")) else None,
                    str(row.get("vehicle_4", "")).strip() if pd.notna(row.get("vehicle_4")) else None,
                    str(row.get("vehicle_5", "")).strip() if pd.notna(row.get("vehicle_5")) else None,
                ],
                "weatherCondition": str(row.get("weather_condition", "Unknown")).strip() if pd.notna(row.get("weather_condition")) else "Unknown"
            }
            
            # Remove None values from lists
            collision["contributingFactors"] = [f for f in collision["contributingFactors"] if f and f != "nan" and f != ""]
            collision["vehicleTypes"] = [v for v in collision["vehicleTypes"] if v and v != "nan" and v != ""]
            
            collisions.append(collision)
        
        print(f"✅ Parsed {len(collisions)} collision records")
        return collisions
    except Exception as e:
        print(f"❌ CSV parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_to_database(collisions):
    """Send collision data to XML Service via GraphQL mutation"""
    print(f"💾 Loading {len(collisions)} collision records to database via XML Service...")
    
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
    
    variables = {
        "data": collisions
    }
    
    try:
        response = requests.post(
            XML_SERVICE_URL,
            json={"query": mutation, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if "errors" in result:
                print(f"❌ GraphQL errors: {result['errors']}")
                return False
            
            data = result.get("data", {}).get("importCollisionsFromData", {})
            print(f"✅ Data loaded successfully!")
            print(f"   Request ID: {data.get('requestId')}")
            print(f"   Document ID: {data.get('documentId')}")
            print(f"   Status: {data.get('status')}")
            
            if data.get("error"):
                print(f"   Warning: {data.get('error')}")
            
            return True
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Database load failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Remove temporary downloaded file"""
    if os.path.exists(LOCAL_FILE):
        os.remove(LOCAL_FILE)
        print(f"🧹 Cleaned up temporary file: {LOCAL_FILE}")


def main():
    """Main workflow: Download → Parse → Load → Cleanup"""
    try:
        # Step 1: Download CSV from Supabase Storage
        if not download_from_bucket():
            return False
        
        # Step 2: Parse CSV to collision data format
        collisions = parse_csv_to_collisions()
        if not collisions:
            return False
        
        # Step 3: Load data to database via XML Service
        success = load_to_database(collisions)
        
        # Step 4: Cleanup
        cleanup()
        
        return success
        
    except Exception as e:
        print(f"❌ Load to database failed: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("🎉 All collision data loaded to database successfully!")
    else:
        print("⚠️ Some issues occurred during data loading")
