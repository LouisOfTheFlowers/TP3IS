"""
REST API Routes for XML Service
Replaces GraphQL with REST endpoints
"""
from flask import Blueprint, request, jsonify
from services.analytics_cache import analytics_cache
from services.xpath_query_service import xpath_query_service
from services.collision_service import collision_service
from services.duplicate_checker import duplicate_checker

# Create Blueprint
api = Blueprint('api', __name__, url_prefix='/api')


# ============================================================
# STATISTICS ENDPOINTS
# ============================================================

@api.route('/statistics', methods=['GET'])
def get_statistics():
    """
    GET /api/statistics
    Returns summary statistics
    """
    try:
        stats = analytics_cache.get_summary_statistics()
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route('/latest-collision-date', methods=['GET'])
def get_latest_collision_date():
    """
    GET /api/latest-collision-date
    Returns the most recent collision date in the database
    Used to avoid re-scraping old data
    """
    try:
        latest_date = analytics_cache.get_latest_collision_date()
        return jsonify({
            "success": True,
            "data": {
                "latestDate": latest_date
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# WEATHER CORRELATION ENDPOINTS
# ============================================================

@api.route('/weather-correlation', methods=['GET'])
def get_weather_correlation():
    """
    GET /api/weather-correlation
    Returns weather-accident correlation data
    """
    try:
        data = analytics_cache.get_weather_correlation_fast()
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route('/casualties-by-weather', methods=['GET'])
def get_casualties_by_weather():
    """
    GET /api/casualties-by-weather?weather=Rain
    Returns casualties grouped by weather condition
    Optional query param: weather (filter by specific condition)
    """
    try:
        weather_filter = request.args.get('weather')
        data = analytics_cache.get_casualties_by_weather_fast(weather_filter)
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# CONTRIBUTING FACTORS ENDPOINTS
# ============================================================

@api.route('/contributing-factors', methods=['GET'])
def get_contributing_factors():
    """
    GET /api/contributing-factors?limit=20
    Returns top contributing factors
    Optional query param: limit (default: 20)
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        data = analytics_cache.get_contributing_factors_fast(limit)
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# TIME PERIOD ENDPOINTS
# ============================================================

@api.route('/time-period', methods=['GET'])
def get_time_period():
    """
    GET /api/time-period?startDate=2024-01-01&endDate=2024-12-31&groupBy=hour
    Returns accidents grouped by time period
    Optional query params:
    - startDate: Start date filter (ISO format)
    - endDate: End date filter (ISO format)
    - groupBy: Grouping level (hour, day, month, year)
    """
    try:
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        group_by = request.args.get('groupBy', 'hour')
        
        data = analytics_cache.get_time_period_stats_fast(start_date, end_date, group_by)
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# VEHICLE TYPE ENDPOINTS
# ============================================================

@api.route('/vehicle-types', methods=['GET'])
def get_vehicle_types():
    """
    GET /api/vehicle-types?limit=15
    Returns vehicle types involved in accidents
    Optional query param: limit (default: 15)
    """
    try:
        limit = request.args.get('limit', 15, type=int)
        data = analytics_cache.get_vehicle_types_fast(limit)
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# XPATH QUERY ENDPOINTS
# ============================================================

@api.route('/xpath', methods=['POST'])
def execute_xpath():
    """
    POST /api/xpath
    Execute custom XPath query on XML documents
    
    Body:
    {
        "query": "//collision[@severity='Fatal']",
        "xpath": "//collision[@severity='Fatal']", (alternative)
        "limit": 100
    }
    """
    try:
        data = request.get_json()
        
        # Support both 'query' and 'xpath' parameter names
        xpath_expr = data.get('query') or data.get('xpath')
        limit = data.get('limit', 100)
        
        if not xpath_expr:
            return jsonify({
                "success": False,
                "error": "XPath expression required (use 'query' or 'xpath' parameter)"
            }), 400
        
        print(f"[REST API] Executing XPath: {xpath_expr} (limit: {limit})")
        
        results = xpath_query_service.execute_xpath(xpath_expr, limit)
        
        print(f"[REST API] XPath returned {len(results)} results")
        
        return jsonify({
            "success": True,
            "data": results
        })
    except Exception as e:
        print(f"[REST API] XPath Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# DASHBOARD ENDPOINT (Aggregated)
# ============================================================

@api.route('/dashboard', methods=['GET'])
def get_dashboard():
    """
    GET /api/dashboard?quick=true
    Returns all dashboard data in one call
    Optional query param: quick (return cached data)
    """
    try:
       
        
        # Load real data
        statistics = analytics_cache.get_summary_statistics()
        weather_correlation = analytics_cache.get_weather_correlation_fast()
        contributing_factors = analytics_cache.get_contributing_factors_fast(20)
        vehicle_types = analytics_cache.get_vehicle_types_fast(15)
        
        return jsonify({
            "success": True,
            "cached": False,
            "data": {
                "statistics": statistics,
                "weatherCorrelation": weather_correlation,
                "contributingFactors": contributing_factors,
                "vehicleTypes": vehicle_types
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# WEBHOOK ENDPOINT (for Data Processor)
# ============================================================

@api.route('/webhook', methods=['POST'])
def webhook_receiver():
    """
    POST /api/webhook
    Receives notifications from Data Processor
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # If receiving collision data, process it
        if "collisions" in data:
            result = collision_service.process_and_store_collisions(data["collisions"])
            return jsonify({
                "success": True,
                "data": result
            })
        
        # If receiving status update
        if "status" in data:
            return jsonify({
                "success": True,
                "received": True,
                "data": data
            })
        
        return jsonify({
            "success": False,
            "error": "Invalid data format"
        }), 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# IMPORT CSV ENDPOINT
# ============================================================

@api.route('/import-csv', methods=['POST'])
def import_csv():
    """
    POST /api/import-csv
    Import CSV data directly from Data Processor
    
    Body:
    {
        "collisions": [...]
    }
    """
    try:
        data = request.get_json()
        
        if not data or "collisions" not in data:
            return jsonify({
                "success": False,
                "error": "No collision data provided"
            }), 400
        
        result = collision_service.process_and_store_collisions(data["collisions"])
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# DUPLICATE DETECTION ENDPOINTS
# ============================================================

@api.route('/duplicates/check', methods=['POST'])
def check_duplicates():
    """
    POST /api/duplicates/check
    Check which collisions are duplicates without storing them
    
    Body:
    {
        "collisions": [...]
    }
    """
    try:
        data = request.get_json()
        
        if not data or "collisions" not in data:
            return jsonify({
                "success": False,
                "error": "No collision data provided"
            }), 400
        
        new_collisions, duplicate_collisions, stats = duplicate_checker.check_for_duplicates(data["collisions"])
        
        return jsonify({
            "success": True,
            "data": {
                "statistics": stats,
                "new_count": len(new_collisions),
                "duplicate_count": len(duplicate_collisions),
                "duplicates": duplicate_collisions[:10]  # Return first 10 duplicates as sample
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route('/duplicates/stats', methods=['GET'])
def get_duplicate_stats():
    """
    GET /api/duplicates/stats
    Get statistics about duplicates in the database
    """
    try:
        stats = duplicate_checker.get_duplicate_statistics()
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
