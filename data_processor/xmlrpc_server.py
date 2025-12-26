"""
XML-RPC Server for Data Processor Service
Protocol: XML-RPC (requirement #8c)
This exposes the data processing functionality via XML-RPC protocol
"""
import os
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
from functools import wraps
import threading
from datetime import datetime
from dotenv import load_dotenv

# Import local modules
from process_data import (
    download_csv_from_bucket, 
    parse_csv_data, 
    send_to_xml_service,
    safe_int
)

load_dotenv()

# Configuration
XMLRPC_PORT = int(os.getenv("XMLRPC_PORT", "8000"))
XMLRPC_HOST = os.getenv("XMLRPC_HOST", "0.0.0.0")


class RequestHandler(SimpleXMLRPCRequestHandler):
    """Custom request handler with CORS support"""
    rpc_paths = ('/RPC2', '/xmlrpc')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


class DataProcessorXMLRPC:
    """
    XML-RPC Service for Data Processing Operations
    Exposes data processing functionality via XML-RPC protocol
    """
    
    def __init__(self):
        self.version = "1.0.0"
        self.processing_lock = threading.Lock()
        self.last_processed = None
        self.processing_history = []
    
    # ============================================================
    # Health and Status Methods
    # ============================================================
    
    def health_check(self):
        """Check if the service is running"""
        return {
            "status": "healthy",
            "service": "data-processor-xmlrpc",
            "version": self.version,
            "timestamp": datetime.utcnow().isoformat(),
            "last_processed": self.last_processed
        }
    
    def get_version(self):
        """Get service version"""
        return self.version
    
    def get_status(self):
        """Get current service status"""
        return {
            "version": self.version,
            "last_processed": self.last_processed,
            "processing_count": len(self.processing_history),
            "is_processing": self.processing_lock.locked()
        }
    
    # ============================================================
    # Data Processing Methods
    # ============================================================
    
    def process_bucket_data(self):
        """
        Main method: Process CSV data from Supabase bucket
        Downloads CSV, parses it, and sends to XML Service
        
        Returns:
            dict with processing result
        """
        if self.processing_lock.locked():
            return {
                "success": False,
                "error": "Processing already in progress",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        with self.processing_lock:
            try:
                print(f"[XML-RPC] Starting bucket data processing...")
                
                # Step 1: Download CSV
                csv_bytes = download_csv_from_bucket()
                if not csv_bytes:
                    return {
                        "success": False,
                        "error": "Failed to download CSV from bucket",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                # Step 2: Parse CSV
                collisions = parse_csv_data(csv_bytes)
                if not collisions:
                    return {
                        "success": False,
                        "error": "No collision records found in CSV",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                # Step 3: Send to XML Service
                result = send_to_xml_service(collisions)
                
                # Record processing
                processing_record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "records_processed": len(collisions),
                    "result": result
                }
                self.processing_history.append(processing_record)
                self.last_processed = datetime.utcnow().isoformat()
                
                if result and result.get('status') == 'OK':
                    return {
                        "success": True,
                        "document_id": result.get('documentId'),
                        "request_id": result.get('requestId'),
                        "records_processed": len(collisions),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get('error') if result else "Unknown error",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    def process_custom_data(self, collision_data):
        """
        Process custom collision data provided directly
        
        Args:
            collision_data: List of collision dictionaries
            
        Returns:
            dict with processing result
        """
        if not collision_data:
            return {
                "success": False,
                "error": "No collision data provided"
            }
        
        try:
            result = send_to_xml_service(collision_data)
            
            if result and result.get('status') == 'OK':
                return {
                    "success": True,
                    "document_id": result.get('documentId'),
                    "request_id": result.get('requestId'),
                    "records_processed": len(collision_data)
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error') if result else "Unknown error"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============================================================
    # History and Statistics Methods
    # ============================================================
    
    def get_processing_history(self, limit=10):
        """
        Get processing history
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of processing records
        """
        return self.processing_history[-limit:]
    
    def get_total_processed(self):
        """Get total number of records processed"""
        return sum(
            record.get('records_processed', 0) 
            for record in self.processing_history
        )
    
    def clear_history(self):
        """Clear processing history"""
        self.processing_history = []
        return {"success": True, "message": "History cleared"}
    
    # ============================================================
    # Utility Methods
    # ============================================================
    
    def echo(self, message):
        """Echo a message (for testing)"""
        return f"Echo: {message}"
    
    def list_methods(self):
        """List all available XML-RPC methods"""
        return [
            "health_check",
            "get_version",
            "get_status",
            "process_bucket_data",
            "process_custom_data",
            "get_processing_history",
            "get_total_processed",
            "clear_history",
            "echo",
            "list_methods"
        ]


def run_xmlrpc_server():
    """Start the XML-RPC server"""
    print("=" * 60)
    print("🚀 DATA PROCESSOR XML-RPC SERVER")
    print("=" * 60)
    print(f"   Protocol: XML-RPC")
    print(f"   Host: {XMLRPC_HOST}")
    print(f"   Port: {XMLRPC_PORT}")
    print(f"   Endpoints: /RPC2, /xmlrpc")
    print("=" * 60)
    
    # Create server
    server = SimpleXMLRPCServer(
        (XMLRPC_HOST, XMLRPC_PORT),
        requestHandler=RequestHandler,
        allow_none=True
    )
    
    # Register service
    service = DataProcessorXMLRPC()
    server.register_instance(service)
    server.register_introspection_functions()
    
    print(f"✅ XML-RPC Server running at http://{XMLRPC_HOST}:{XMLRPC_PORT}/RPC2")
    print("Available methods:")
    for method in service.list_methods():
        print(f"   - {method}")
    print()
    print("Press Ctrl+C to stop...")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")


if __name__ == "__main__":
    run_xmlrpc_server()
