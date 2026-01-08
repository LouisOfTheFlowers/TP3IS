# -*- coding: utf-8 -*-
"""
HTTP Wrapper for Data Processor
Provides HTTP endpoints to trigger the crawler scripts
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import sys
import os

app = Flask(__name__)
CORS(app)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'data-processor-http',
        'version': '1.0.0'
    })


@app.route('/load-data', methods=['POST'])
def load_data():
    """
    Full data pipeline following the architecture:
    1. Run fetch_collisions.py - Gets data from NYC Open Data (Crawler)
    2. Upload raw CSV to Supabase Storage Bucket (Protocol A)
    3. Run enrich_with_weather_new.py - Adds weather info from External API
    4. Upload enriched CSV to Supabase Storage Bucket (Protocol A)
    5. Run load_from_storage_to_db.py - Downloads from bucket and sends to XML Service (Protocol B) → PostgreSQL
    """
    try:
        # Get limit parameter from request (default 100)
        data = request.get_json() or {}
        limit = data.get('limit', 100)
        print(f"[INFO] Record limit: {limit}")
        
        # Crawler directory is mounted as a volume
        crawler_dir = '/app/crawler'
        
        if not os.path.exists(crawler_dir):
            return jsonify({
                'success': False,
                'message': f'Crawler directory not found. Make sure it is mounted at {crawler_dir}'
            }), 500
        
        print(f"[INFO] Using crawler directory: {crawler_dir}")
        
        # Step 1: Run fetch_collisions.py (Crawler - produces CSV)
        print(f"[STEP 1] Fetching up to {limit} collision records from NYC Open Data API...")
        result = subprocess.run(
            [sys.executable, 'fetch_collisions.py', str(limit)],
            cwd=crawler_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'Failed to fetch collision data',
                'error': result.stderr or result.stdout
            }), 500
        
        print("[SUCCESS] Collision data fetched successfully")
        
        # Check if we have any new data
        import pandas as pd
        try:
            raw_df = pd.read_csv(os.path.join(crawler_dir, 'collisions_raw.csv'))
            if len(raw_df) == 0:
                return jsonify({
                    'success': True,
                    'message': 'Database is up to date - no new collision data to fetch',
                    'steps_completed': [
                        'Checked NYC Open Data for new records',
                        'No new records found - database is current'
                    ]
                })
        except Exception as e:
            print(f"[WARNING] Could not check CSV: {e}")
        
        # Step 2: Run enrich_with_weather_new.py (External Weather API)
        print("[STEP 2] Enriching collision data with weather information from External API...")
        result = subprocess.run(
            [sys.executable, 'enrich_with_weather_new.py'],
            cwd=crawler_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes for weather API calls
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'Failed to enrich with weather data',
                'error': result.stderr or result.stdout
            }), 500
        
        print("[SUCCESS] Weather data enriched successfully")
        
        # Step 3: Upload enriched CSV to Supabase Storage Bucket (Protocol A)
        print("[STEP 3] Uploading enriched CSV to Supabase Storage Bucket (Protocol A)...")
        result = subprocess.run(
            [sys.executable, 'upload_to_supabase.py'],
            cwd=crawler_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'Failed to upload to Supabase Storage',
                'error': result.stderr or result.stdout
            }), 500
        
        print("[SUCCESS] Data uploaded to Supabase Storage bucket")
        
        # Step 4: Load from Storage to Database (Protocol B to XML Service)
        print("[STEP 4] Loading data from Storage bucket to PostgreSQL via XML Service (Protocol B)...")
        result = subprocess.run(
            [sys.executable, 'load_from_storage_to_db.py'],
            cwd=crawler_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for database loading
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'Failed to load data to database',
                'error': result.stderr or result.stdout
            }), 500
        
        print("[SUCCESS] Data loaded to PostgreSQL database via XML Service")
        
        return jsonify({
            'success': True,
            'message': 'Full pipeline completed successfully!',
            'steps_completed': [
                'Fetched collision data from NYC Open Data (Crawler)',
                'Enriched with weather information (External API)',
                'Uploaded to Supabase Storage bucket (Protocol A)',
                'Loaded to PostgreSQL via XML Service (Protocol B)'
            ]
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': 'Data loading timed out'
        }), 408
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error loading data',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('HTTP_PORT', '8001'))
    print(f"[START] Data Processor HTTP Server starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
