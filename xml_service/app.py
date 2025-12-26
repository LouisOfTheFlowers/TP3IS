"""
XML Service - Main Flask Application
REST API for XML document management and XPath queries
Protocol C: RPC/REST/gRPC
"""
from flask import Flask, jsonify
from flask_cors import CORS
from rest_routes import rest_api
from database.init_db import init_database
from config.settings import Config

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Enable CORS for BI Service and Frontend
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/health": {"origins": "*"}
    })
    
    # Register REST API Blueprint
    app.register_blueprint(rest_api)
    
    @app.route("/")
    def index():
        """Root endpoint with service info"""
        return jsonify({
            "service": "XML Service",
            "version": "2.0.0",
            "protocol": "REST (Protocol C)",
            "endpoints": {
                "health": "/health",
                "statistics": "/api/statistics",
                "weather_correlation": "/api/weather-correlation",
                "casualties_by_weather": "/api/casualties-by-weather",
                "contributing_factors": "/api/contributing-factors",
                "time_period": "/api/time-period",
                "vehicle_types": "/api/vehicle-types",
                "xpath_query": "/api/xpath/query (POST)",
                "webhook": "/api/webhook (POST)"
            }
        })
    
    @app.route("/health")
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "xml-service",
            "protocol": "REST"
        })
    
    return app


def main():
    """Main entry point"""
    # Initialize database
    print("🔧 Initializing database...")
    init_database()
    
    # Create and run app
    app = create_app()
    port = Config.XML_SERVICE_PORT
    
    print(f"🚀 XML Service starting on port {port}")
    print(f"� Protocol: REST (Protocol C)")
    print(f"📊 API endpoints: http://localhost:{port}/api/")
    print(f"❤️  Health check: http://localhost:{port}/health")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )


if __name__ == "__main__":
    main()
