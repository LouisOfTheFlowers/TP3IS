# -*- coding: utf-8 -*-
"""
HTTP Wrapper for Data Processor
Provides HTTP endpoints to trigger the crawler scripts
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import subprocess
import sys
import os
import json

app = Flask(__name__)
CORS(app)

# Crawler directory
CRAWLER_DIR = '/app/crawler'


def stream_json(data):
    """Helper to stream JSON data"""
    return json.dumps(data) + "\n"


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'data-processor-http',
        'version': '2.0.0'
    })


# ============================================================================
# STEP 1: SCRAPE COLLISION DATA
# ============================================================================

@app.route('/scrape', methods=['POST'])
def scrape_data():
    """
    Step 1: Fetch collision data from NYC Open Data API
    Streams progress updates to the client
    """
    def generate():
        try:
            data = request.get_json() or {}
            limit = data.get('limit', 1000)
            
            yield stream_json({'status': 'info', 'message': f'Starting scrape for {limit} records...'})
            
            if not os.path.exists(CRAWLER_DIR):
                yield stream_json({'status': 'error', 'message': f'Crawler directory not found: {CRAWLER_DIR}'})
                return
            
            # Run the fetch_collisions.py script
            yield stream_json({'status': 'progress', 'records': 0, 'message': 'Connecting to NYC Open Data API...'})
            
            result = subprocess.run(
                [sys.executable, 'fetch_collisions.py', str(limit)],
                cwd=CRAWLER_DIR,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                yield stream_json({'status': 'error', 'message': f'Scrape failed: {result.stderr or result.stdout}'})
                return
            
            # Check output file
            csv_path = os.path.join(CRAWLER_DIR, 'collisions_raw.csv')
            if os.path.exists(csv_path):
                import pandas as pd
                df = pd.read_csv(csv_path)
                total = len(df)
                yield stream_json({'status': 'progress', 'records': total, 'message': f'Fetched {total} records'})
                yield stream_json({'status': 'complete', 'total': total})
            else:
                yield stream_json({'status': 'error', 'message': 'Output file not created'})
                
        except subprocess.TimeoutExpired:
            yield stream_json({'status': 'error', 'message': 'Scrape timed out after 5 minutes'})
        except Exception as e:
            yield stream_json({'status': 'error', 'message': str(e)})
    
    return Response(generate(), mimetype='application/x-ndjson')


# ============================================================================
# STEP 2: ENRICH WITH WEATHER (Download from bucket, merge locally)
# ============================================================================

@app.route('/enrich-weather', methods=['POST'])
def enrich_weather():
    """
    Step 2: Download weather from bucket, merge with collision data
    - Downloads weather_nyc_2025.csv from Supabase bucket (if not cached)
    - Merges collision data with weather by date+hour
    - Produces collisions_enriched.csv (ready for PostgreSQL)
    """
    def generate():
        try:
            yield stream_json({'status': 'info', 'message': 'Starting weather enrichment...'})
            
            weather_csv = os.path.join(CRAWLER_DIR, 'weather_nyc_2025.csv')
            
            # Check if we need to download weather data from bucket
            if not os.path.exists(weather_csv):
                yield stream_json({'status': 'info', 'message': '📥 Downloading weather data from Supabase bucket...'})
                
                # Download weather data from bucket
                result = subprocess.run(
                    [sys.executable, 'download_weather_from_bucket.py'],
                    cwd=CRAWLER_DIR,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    yield stream_json({'status': 'error', 'message': f'Failed to download weather data: {result.stderr or result.stdout}'})
                    yield stream_json({'status': 'error', 'message': 'Make sure weather data is uploaded to bucket first!'})
                    return
                
                yield stream_json({'status': 'info', 'message': '✅ Weather data downloaded from bucket'})
            else:
                yield stream_json({'status': 'info', 'message': '✅ Using cached weather data (weather_nyc_2025.csv)'})
            
            # Now merge weather with collision data
            yield stream_json({'status': 'progress', 'current': 0, 'total': 1, 'date': 'Merging datasets...'})
            
            result = subprocess.run(
                [sys.executable, 'merge_weather_collisions.py'],
                cwd=CRAWLER_DIR,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                yield stream_json({'status': 'error', 'message': f'Failed to merge weather data: {result.stderr or result.stdout}'})
                return
            
            # Check enriched file
            enriched_csv = os.path.join(CRAWLER_DIR, 'collisions_enriched.csv')
            if os.path.exists(enriched_csv):
                import pandas as pd
                df = pd.read_csv(enriched_csv)
                total = len(df)
                
                # Calculate weather distribution
                weather_counts = df['weather'].value_counts().to_dict()
                
                yield stream_json({'status': 'info', 'message': f'Weather distribution: {weather_counts}'})
                yield stream_json({
                    'status': 'complete',
                    'totalRecords': total,
                    'enrichedRecords': total,
                    'successRate': '100',
                    'weatherDistribution': weather_counts
                })
            else:
                yield stream_json({'status': 'error', 'message': 'Enriched file not created'})
                
        except subprocess.TimeoutExpired:
            yield stream_json({'status': 'error', 'message': 'Weather enrichment timed out'})
        except Exception as e:
            yield stream_json({'status': 'error', 'message': str(e)})
    
    return Response(generate(), mimetype='application/x-ndjson')


# ============================================================================
# STEP 3: UPLOAD RAW COLLISIONS TO SUPABASE BUCKET
# ============================================================================

@app.route('/upload-storage', methods=['POST'])
def upload_storage():
    """
    Step 3: Upload raw collision CSV to Supabase bucket
    Note: Weather data should already be in the bucket (uploaded once via /upload-weather)
    """
    try:
        result = subprocess.run(
            [sys.executable, 'upload_enriched_to_supabase.py'],
            cwd=CRAWLER_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': result.stderr or result.stdout
            }), 500
        
        # Get file sizes
        raw_csv = os.path.join(CRAWLER_DIR, 'collisions_raw.csv')
        raw_size = os.path.getsize(raw_csv) / (1024 * 1024) if os.path.exists(raw_csv) else 0
        
        return jsonify({
            'success': True,
            'message': 'Raw collision data uploaded to bucket',
            'files': {
                'raw': {'name': 'collisions_raw.csv', 'size': f'{raw_size:.2f}'}
            }
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Upload timed out'}), 408
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# STEP 4: LOAD TO DATABASE
# ============================================================================

@app.route('/load-database', methods=['POST'])
def load_database():
    """
    Step 4: Load enriched data to PostgreSQL via XML Service
    """
    def generate():
        try:
            data = request.get_json() or {}
            batch_size = data.get('batchSize', 100)
            
            yield stream_json({'status': 'info', 'message': f'Starting database load with batch size {batch_size}...'})
            
            result = subprocess.run(
                [sys.executable, 'load_from_storage_to_db.py'],
                cwd=CRAWLER_DIR,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                yield stream_json({'status': 'error', 'message': f'Load failed: {result.stderr or result.stdout}'})
                return
            
            # Parse output to get stats
            output_lines = result.stdout.split('\n')
            records_loaded = 0
            for line in output_lines:
                if 'records' in line.lower() or 'loaded' in line.lower():
                    yield stream_json({'status': 'progress', 'batch': 1, 'totalBatches': 1, 'recordsLoaded': records_loaded, 'message': line.strip()})
            
            yield stream_json({
                'status': 'complete',
                'totalBatches': 1,
                'totalRecords': records_loaded,
                'successRate': '100%'
            })
            
        except subprocess.TimeoutExpired:
            yield stream_json({'status': 'error', 'message': 'Database load timed out after 10 minutes'})
        except Exception as e:
            yield stream_json({'status': 'error', 'message': str(e)})
    
    return Response(generate(), mimetype='application/x-ndjson')


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.route('/status', methods=['GET'])
def get_status():
    """Get current pipeline status - check what files exist"""
    files = {
        'collisions_raw.csv': os.path.exists(os.path.join(CRAWLER_DIR, 'collisions_raw.csv')),
        'weather_nyc_2025.csv': os.path.exists(os.path.join(CRAWLER_DIR, 'weather_nyc_2025.csv')),
        'collisions_enriched.csv': os.path.exists(os.path.join(CRAWLER_DIR, 'collisions_enriched.csv'))
    }
    
    record_counts = {}
    for filename, exists in files.items():
        if exists:
            try:
                import pandas as pd
                df = pd.read_csv(os.path.join(CRAWLER_DIR, filename))
                record_counts[filename] = len(df)
            except:
                record_counts[filename] = 0
    
    return jsonify({
        'status': 'healthy',
        'files': files,
        'recordCounts': record_counts
    })


@app.route('/upload-weather', methods=['POST'])
def upload_weather():
    """
    Upload weather_nyc_2025.csv to Supabase bucket (one-time setup)
    This should be run once to initialize the bucket with weather data
    """
    def generate():
        try:
            yield stream_json({'status': 'info', 'message': 'Uploading weather data to Supabase bucket...'})
            
            weather_csv = os.path.join(CRAWLER_DIR, 'weather_nyc_2025.csv')
            
            # Check if weather file exists locally
            if not os.path.exists(weather_csv):
                yield stream_json({'status': 'info', 'message': 'Weather data not found locally. Fetching from Open-Meteo API...'})
                
                result = subprocess.run(
                    [sys.executable, 'fetch_weather_2025.py'],
                    cwd=CRAWLER_DIR,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode != 0:
                    yield stream_json({'status': 'error', 'message': f'Failed to fetch weather: {result.stderr or result.stdout}'})
                    return
                
                yield stream_json({'status': 'info', 'message': '✅ Weather data fetched successfully'})
            
            # Upload to bucket
            yield stream_json({'status': 'info', 'message': 'Uploading to Supabase bucket...'})
            
            result = subprocess.run(
                [sys.executable, 'upload_weather_to_bucket.py'],
                cwd=CRAWLER_DIR,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                yield stream_json({'status': 'error', 'message': f'Upload failed: {result.stderr or result.stdout}'})
                return
            
            # Get stats
            import pandas as pd
            df = pd.read_csv(weather_csv)
            weather_counts = df['simple_condition'].value_counts().to_dict()
            
            yield stream_json({
                'status': 'complete',
                'totalRecords': len(df),
                'dateRange': f"{df['date'].min()} to {df['date'].max()}",
                'weatherDistribution': weather_counts,
                'message': 'Weather data uploaded to bucket successfully!'
            })
                
        except Exception as e:
            yield stream_json({'status': 'error', 'message': str(e)})
    
    return Response(generate(), mimetype='application/x-ndjson')


# ============================================================================
# LEGACY ENDPOINT (for backwards compatibility)
# ============================================================================

@app.route('/load-data', methods=['POST'])
def load_data():
    """
    Legacy endpoint - runs the full pipeline in one call
    """
    try:
        data = request.get_json() or {}
        total_limit = data.get('limit', 1000)
        
        print(f"[INFO] Running full pipeline for {total_limit} records...")
        
        # Step 1: Fetch collision data
        print("[STEP 1] Fetching collision data...")
        result = subprocess.run(
            [sys.executable, 'fetch_collisions.py', str(total_limit)],
            cwd=CRAWLER_DIR,
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'Failed to fetch collision data',
                'error': result.stderr or result.stdout
            }), 500
        
        # Step 2: Download weather data from bucket if needed
        weather_csv = os.path.join(CRAWLER_DIR, 'weather_nyc_2025.csv')
        if not os.path.exists(weather_csv):
            print("[STEP 2a] Downloading weather data from bucket...")
            result = subprocess.run(
                [sys.executable, 'download_weather_from_bucket.py'],
                cwd=CRAWLER_DIR,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                return jsonify({
                    'success': False,
                    'message': 'Failed to download weather data from bucket',
                    'error': result.stderr or result.stdout
                }), 500
        
        # Step 3: Merge weather with collisions
        print("[STEP 2b] Merging weather with collision data...")
        result = subprocess.run(
            [sys.executable, 'merge_weather_collisions.py'],
            cwd=CRAWLER_DIR,
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'Failed to merge weather data',
                'error': result.stderr or result.stdout
            }), 500
        
        # Step 4: Upload raw collisions to Supabase bucket
        print("[STEP 3] Uploading raw collisions to Supabase bucket...")
        result = subprocess.run(
            [sys.executable, 'upload_enriched_to_supabase.py'],
            cwd=CRAWLER_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'Failed to upload raw collisions to bucket',
                'error': result.stderr or result.stdout
            }), 500
        
        # Get final stats BEFORE loading to DB (load_from_storage_to_db.py deletes the CSV)
        import pandas as pd
        enriched_csv = os.path.join(CRAWLER_DIR, 'collisions_enriched.csv')
        df = pd.read_csv(enriched_csv)
        total_records = len(df)
        weather_dist = df['weather'].value_counts().to_dict() if 'weather' in df.columns else df.get('weather_condition', pd.Series()).value_counts().to_dict()
        
        # Step 5: Load merged data to Database (PostgreSQL as XML)
        print("[STEP 4] Loading to database...")
        result = subprocess.run(
            [sys.executable, 'load_from_storage_to_db.py'],
            cwd=CRAWLER_DIR,
            capture_output=True,
            text=True,
            timeout=7200
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'Failed to load to database',
                'error': result.stderr or result.stdout
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'Full pipeline completed! Processed {len(df)} records.',
            'details': {
                'total_records': len(df),
                'weather_distribution': weather_dist
            },
            'steps_completed': [
                f'Fetched {total_records} collision records from NYC Open Data',
                'Enriched records with accurate hourly weather data',
                'Uploaded to Supabase Storage',
                'Loaded to PostgreSQL database'
            ]
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Pipeline timed out'}), 408
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('HTTP_PORT', '8001'))
    print(f"[START] Data Processor HTTP Server starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
