"""
REST API Routes for XML Service
Provides REST endpoints for analytics and XPath queries
"""
from flask import Blueprint, request, jsonify
from services.analytics_cache import analytics_cache
from services.xpath_query_service import xpath_query_service

rest_api = Blueprint('rest_api', __name__, url_prefix='/api')


# ============================================================
# Analytics Endpoints (Fast - uses SQL cache)
# ============================================================

@rest_api.route('/statistics', methods=['GET'])
def get_statistics():
    """
    GET /api/statistics
    Get summary statistics (total collisions, injured, killed, documents)
    """
    try:
        data = analytics_cache.get_summary_statistics()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rest_api.route('/latest-collision-date', methods=['GET'])
def get_latest_collision_date():
    """
    GET /api/latest-collision-date
    Get the most recent collision date in the database
    Used to avoid re-scraping old data
    """
    try:
        latest_date = analytics_cache.get_latest_collision_date()
        return jsonify({
            'success': True,
            'data': {
                'latestDate': latest_date
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rest_api.route('/weather-correlation', methods=['GET'])
def get_weather_correlation():
    """
    GET /api/weather-correlation
    Get weather-accident correlation analysis
    """
    try:
        data = analytics_cache.get_weather_correlation_fast()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rest_api.route('/casualties-by-weather', methods=['GET'])
def get_casualties_by_weather():
    """
    GET /api/casualties-by-weather?weather=Rain
    Get casualties grouped by weather condition
    Query params:
        - weather (optional): Filter by specific weather condition
    """
    try:
        weather_filter = request.args.get('weather', None)
        data = analytics_cache.get_casualties_by_weather_fast(weather_filter)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rest_api.route('/contributing-factors', methods=['GET'])
def get_contributing_factors():
    """
    GET /api/contributing-factors?limit=20
    Get top contributing factors to accidents
    Query params:
        - limit (optional): Number of results to return (default: 20)
    """
    try:
        limit = int(request.args.get('limit', 20))
        data = analytics_cache.get_contributing_factors_fast(limit)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rest_api.route('/time-period', methods=['GET'])
def get_time_period():
    """
    GET /api/time-period?startDate=2023-01-01&endDate=2023-12-31&groupBy=hour
    Get accidents by time period
    Query params:
        - startDate (optional): Start date filter
        - endDate (optional): End date filter
        - groupBy (optional): Grouping level (hour, day, month)
    """
    try:
        start_date = request.args.get('startDate', None)
        end_date = request.args.get('endDate', None)
        group_by = request.args.get('groupBy', 'hour')
        
        data = analytics_cache.get_time_period_stats_fast(start_date, end_date, group_by)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rest_api.route('/vehicle-types', methods=['GET'])
def get_vehicle_types():
    """
    GET /api/vehicle-types?limit=15
    Get accidents by vehicle type
    Query params:
        - limit (optional): Number of results to return (default: 15)
    """
    try:
        limit = int(request.args.get('limit', 15))
        data = analytics_cache.get_vehicle_types_fast(limit)
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# XPath Query Endpoints (Custom queries)
# ============================================================

@rest_api.route('/xpath', methods=['POST'])
def execute_xpath_short():
    """
    POST /api/xpath
    Execute a custom XPath query on XML documents (short route)
    
    Request body:
    {
        "query": "//collision[@weatherCondition='Rain']",
        "xpath": "//collision[@weatherCondition='Rain']",  (alternative)
        "limit": 100
    }
    """
    try:
        data = request.get_json()
        # Support both 'query' and 'xpath' parameter names
        xpath_query = data.get('query') or data.get('xpath')
        limit = data.get('limit', 100)
        
        if not xpath_query:
            return jsonify({
                'success': False,
                'error': 'XPath query is required (use "query" or "xpath" parameter)'
            }), 400
        
        print(f"[XML Service /xpath] Executing XPath: {xpath_query} (limit: {limit})")
        
        # Execute the XPath query - returns list of dicts with document_id and result
        results = xpath_query_service.execute_xpath(xpath_query)
        
        # Limit results if specified
        if limit and len(results) > limit:
            results = results[:limit]
        
        print(f"[XML Service /xpath] XPath returned {len(results)} results")
            
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        print(f"[XML Service /xpath] XPath Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rest_api.route('/xpath/query', methods=['POST'])
def execute_xpath():
    """
    POST /api/xpath/query
    Execute a custom XPath query on XML documents
    
    Request body:
    {
        "query": "//collision[@weatherCondition='Rain']",
        "xpath": "//collision[@weatherCondition='Rain']",  (alternative)
        "limit": 100
    }
    """
    try:
        data = request.get_json()
        # Support both 'query' and 'xpath' parameter names
        xpath_query = data.get('query') or data.get('xpath')
        limit = data.get('limit', 100)
        
        if not xpath_query:
            return jsonify({
                'success': False,
                'error': 'XPath query is required (use "query" or "xpath" parameter)'
            }), 400
        
        print(f"[XML Service] Executing XPath: {xpath_query} (limit: {limit})")
        
        # Execute the XPath query - returns list of dicts with document_id and result
        results = xpath_query_service.execute_xpath(xpath_query)
        
        # Limit results if specified
        if limit and len(results) > limit:
            results = results[:limit]
        
        print(f"[XML Service] XPath returned {len(results)} results")
            
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        print(f"[XML Service] XPath Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@rest_api.route('/xpath/count', methods=['POST'])
def count_xpath():
    """
    POST /api/xpath/count
    Count results of an XPath query
    
    Request body:
    {
        "query": "//collision[@weatherCondition='Rain']"
    }
    """
    try:
        data = request.get_json()
        xpath_query = data.get('query')
        
        if not xpath_query:
            return jsonify({
                'success': False,
                'error': 'XPath query is required'
            }), 400
        
        # Execute query and count results
        results = xpath_query_service.execute_xpath(xpath_query)
        total_count = sum(len(r.get('result', [])) for r in results)
        
        return jsonify({
            'success': True,
            'count': total_count,
            'documents': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# Webhook Endpoint (for Data Processor)
# ============================================================

@rest_api.route('/webhook', methods=['POST'])
def webhook_receiver():
    """
    POST /api/webhook
    Receive notifications from Data Processor
    This receives CSV data and triggers XML creation
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # If receiving collision data, process it
        if "collisions" in data:
            from services.collision_service import collision_service
            result = collision_service.process_and_store_collisions(data["collisions"])
            return jsonify({
                'success': True,
                'data': result
            })
        
        # If receiving status update
        if "status" in data:
            return jsonify({
                'success': True,
                'received': True,
                'data': data
            })
        
        return jsonify({
            'success': True,
            'received': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
