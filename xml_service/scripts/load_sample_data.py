"""
Load sample collision data into the database for testing
This simulates the data that would come from the Data Processor
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.collision_service import collision_service
from datetime import datetime, timedelta
import random

# Sample data
WEATHER_CONDITIONS = ["Clear", "Rain", "Snow", "Fog", "Cloudy"]
CONTRIBUTING_FACTORS = [
    "Driver Inattention/Distraction",
    "Failure to Yield Right-of-Way",
    "Following Too Closely",
    "Passing or Lane Usage Improper",
    "Unsafe Speed",
    "Traffic Control Disregarded",
    "Backing Unsafely",
    "Alcohol Involvement",
    "Pedestrian/Bicyclist/Other Pedestrian Error/Confusion"
]
VEHICLE_TYPES = ["Sedan", "Station Wagon/Sport Utility Vehicle", "Taxi", "Pick-up Truck", "Box Truck", "Bus", "Bike"]


def generate_sample_collisions(count=100):
    """Generate sample collision data"""
    collisions = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(count):
        # Random date within last year
        crash_date = base_date + timedelta(days=random.randint(0, 365))
        crash_time = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"
        
        # Random casualties
        persons_injured = random.choice([0, 0, 0, 1, 1, 2, 3])
        persons_killed = random.choice([0, 0, 0, 0, 0, 0, 0, 1])
        pedestrians_injured = random.choice([0, 0, 0, 1]) if persons_injured > 0 else 0
        cyclists_injured = random.choice([0, 0, 0, 1]) if persons_injured > 0 else 0
        motorists_injured = persons_injured - pedestrians_injured - cyclists_injured
        
        # Random factors and vehicles
        num_factors = random.randint(1, 3)
        factors = random.sample(CONTRIBUTING_FACTORS, num_factors)
        num_vehicles = random.randint(1, 3)
        vehicles = random.sample(VEHICLE_TYPES, num_vehicles)
        
        collision = {
            "crash_date": crash_date.strftime("%Y-%m-%d"),
            "crash_time": crash_time,
            "persons_injured": persons_injured,
            "persons_killed": persons_killed,
            "pedestrians_injured": pedestrians_injured,
            "pedestrians_killed": 0,
            "cyclists_injured": cyclists_injured,
            "cyclists_killed": 0,
            "motorists_injured": motorists_injured,
            "motorists_killed": persons_killed,
            "factor_1": factors[0] if len(factors) > 0 else None,
            "factor_2": factors[1] if len(factors) > 1 else None,
            "factor_3": factors[2] if len(factors) > 2 else None,
            "factor_4": None,
            "factor_5": None,
            "vehicle_1": vehicles[0] if len(vehicles) > 0 else None,
            "vehicle_2": vehicles[1] if len(vehicles) > 1 else None,
            "vehicle_3": vehicles[2] if len(vehicles) > 2 else None,
            "vehicle_4": None,
            "vehicle_5": None,
            "weather_condition": random.choice(WEATHER_CONDITIONS)
        }
        collisions.append(collision)
    
    return collisions


def load_data():
    """Load sample data into database"""
    print("🔄 Generating sample collision data...")
    collisions = generate_sample_collisions(200)  # Generate 200 sample records
    
    print(f"📤 Creating XML document with {len(collisions)} collisions...")
    request_id, xml_content, is_valid, error = collision_service.create_xml_document(collisions)
    
    if not is_valid:
        print(f"❌ XML validation failed: {error}")
        return False
    
    print(f"✅ XML document created and validated")
    print(f"💾 Saving to database...")
    
    try:
        document_id, status = collision_service.save_xml_document(request_id, xml_content, is_valid, error)
    except Exception as e:
        print(f"❌ Error saving document: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    if document_id:
        print(f"✅ Successfully loaded data!")
        print(f"   Request ID: {request_id}")
        print(f"   Document ID: {document_id}")
        print(f"   Status: {status}")
        print(f"   Total collisions: {len(collisions)}")
    else:
        print(f"❌ Error saving document to database")
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = load_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
