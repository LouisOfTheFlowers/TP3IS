#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run the complete scraper workflow:
1. Fetch collisions from NYC Open Data
2. Enrich with weather data
3. Load to database via GraphQL
"""

import subprocess
import sys
import os

def run_script(script_name):
    """Run a Python script and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print(f"\n❌ Error running {script_name}")
        return False
    
    print(f"\n✅ {script_name} completed successfully")
    return True

def main():
    """Run the complete scraper workflow"""
    print("\n🚀 Starting NYC Collision Data Scraper Workflow")
    print(f"Working directory: {os.getcwd()}\n")
    
    # Step 1: Fetch collisions
    if not run_script("fetch_collisions.py"):
        sys.exit(1)
    
    # Step 2: Enrich with weather (NEW WeatherAPI.com)
    if not run_script("enrich_with_weather_new.py"):
        sys.exit(1)
    
    # Step 3: Load to database
    if not run_script("load_to_database_direct.py"):
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🎉 Complete workflow finished successfully!")
    print("="*60 + "\n")
    print("Output files created:")
    print("  - collisions.csv (raw data)")
    print("  - collisions_weather.csv (with weather enrichment)")
    print("  - Data loaded to PostgreSQL database via GraphQL\n")

if __name__ == "__main__":
    main()
