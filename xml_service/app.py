"""
XML Service - Main Flask Application
GraphQL API for XML document management and XPath queries
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from ariadne import make_executable_schema, graphql_sync
from ariadne.explorer import ExplorerGraphiQL

from graphql_schema.schema import type_defs
from graphql_schema.resolvers import resolvers
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
        r"/graphql": {"origins": "*"},
        r"/api/*": {"origins": "*"}
    })
    
    # Create executable GraphQL schema
    schema = make_executable_schema(type_defs, *resolvers)
    
    # GraphiQL Explorer for testing
    explorer_html = ExplorerGraphiQL().html(None)
    
    @app.route("/")
    def index():
        """Root endpoint with service info"""
        return jsonify({
            "service": "XML Service",
            "version": "1.0.0",
            "endpoints": {
                "graphql": "/graphql",
                "graphiql": "/graphql (GET for explorer)",
                "health": "/health",
                "webhook": "/api/webhook"
            }
        })
    
    @app.route("/health")
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "xml-service"
        })
    
    @app.route("/graphql", methods=["GET"])
    def graphql_explorer():
        """GraphiQL Explorer interface"""
        return explorer_html, 200
    
    @app.route("/graphql", methods=["POST"])
    def graphql_server():
        """GraphQL endpoint"""
        data = request.get_json()
        
        success, result = graphql_sync(
            schema,
            data,
            context_value={"request": request},
            debug=app.debug
        )
        
        status_code = 200 if success else 400
        return jsonify(result), status_code
    
    @app.route("/api/webhook", methods=["POST"])
    def webhook_receiver():
        """
        Webhook endpoint to receive notifications from Data Processor
        This receives CSV data and triggers XML creation
        """
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # If receiving collision data, process it
        if "collisions" in data:
            from services.collision_service import collision_service
            result = collision_service.process_and_store_collisions(data["collisions"])
            return jsonify(result)
        
        # If receiving status update
        if "status" in data:
            return jsonify({"received": True, "data": data})
        
        return jsonify({"error": "Invalid data format"}), 400
    
    @app.route("/api/import-csv", methods=["POST"])
    def import_csv():
        """
        REST endpoint to import CSV data directly
        Alternative to GraphQL mutation for Data Processor
        """
        from services.collision_service import collision_service
        
        data = request.get_json()
        
        if not data or "collisions" not in data:
            return jsonify({"error": "No collision data provided"}), 400
        
        result = collision_service.process_and_store_collisions(data["collisions"])
        return jsonify(result)
    
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
    print(f"📊 GraphQL endpoint: http://localhost:{port}/graphql")
    print(f"🔍 GraphiQL explorer: http://localhost:{port}/graphql")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )


if __name__ == "__main__":
    main()
