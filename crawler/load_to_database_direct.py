"""
Load collision data directly to database (bypassing storage bucket)
This version reads the CSV directly and sends to XML Service
"""
import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

XML_SERVICE_URL = os.getenv("XML_SERVICE_URL", "http://xml-service:5000/graphql")
FILE_NAME = "collisions_weather.csv"


def parse_csv_to_collisions():
    """Parse CSV file and convert to collision data format"""
    print(f"📊 Parsing CSV file: {FILE_NAME}")
    
    if not os.path.exists(FILE_NAME):
        print(f"❌ File '{FILE_NAME}' not found")
        return None
    
    try:
        df = pd.read_csv(FILE_NAME)
        print(f"📄 Found {len(df)} collision records")
        
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
        print(f"🔗 Sending GraphQL request to: {XML_SERVICE_URL}")
        response = requests.post(
            XML_SERVICE_URL,
            json={"query": mutation, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        print(f"📡 Response status: {response.status_code}")
        
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


def main():
    """Main workflow: Parse CSV → Load to Database"""
    try:
        print("🚀 Starting direct database load...")
        
        # Step 1: Parse CSV to collision data format
        collisions = parse_csv_to_collisions()
        if not collisions:
            print("❌ No collision data to load")
            return False
        
        # Step 2: Load data to database via XML Service
        success = load_to_database(collisions)
        
        if success:
            print("🎉 All collision data loaded to database successfully!")
        else:
            print("⚠️ Failed to load data to database")
        
        return success
        
    except Exception as e:
        print(f"❌ Load to database failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
