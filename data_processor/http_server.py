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
    Load collision data from crawler
    1. Run fetch_collisions.py - Gets data from NYC Open Data
    2. Run enrich_with_weather.py - Adds weather information
    3. Run load_to_database_direct.py - Loads directly to database
    """
    try:
        # Crawler directory is mounted as a volume
        crawler_dir = '/app/crawler'
        
        if not os.path.exists(crawler_dir):
            return jsonify({
                'success': False,
                'message': f'Crawler directory not found. Make sure it is mounted at {crawler_dir}'
            }), 500
        
        print(f"[INFO] Using crawler directory: {crawler_dir}")
        
        # Step 1: Run fetch_collisions.py
        print("[STEP 1] Fetching collision data from NYC Open Data API...")
        result = subprocess.run(
            [sys.executable, 'fetch_collisions.py'],
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
        
        # Step 2: Run enrich_with_weather.py
        print("[STEP 2] Enriching collision data with weather information...")
        result = subprocess.run(
            [sys.executable, 'enrich_with_weather.py'],
            cwd=crawler_dir,
            capture_output=True,
            text=True,
            timeout=120
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
        
        # Step 3: Load directly to database (skip storage bucket)
        print("[STEP 3] Loading data directly to PostgreSQL database...")
        result = subprocess.run(
            [sys.executable, 'load_to_database_direct.py'],
            cwd=crawler_dir,
            capture_output=True,
            text=True,
            timeout=180  # 3 minutes timeout for database loading
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
        
        print("[SUCCESS] Data loaded to database successfully")
        
        return jsonify({
            'success': True,
            'message': 'Successfully scraped collision data, enriched with weather, and loaded to database!',
            'steps_completed': [
                'Fetched collision data from NYC Open Data',
                'Enriched with weather information', 
                'Loaded to PostgreSQL database'
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
