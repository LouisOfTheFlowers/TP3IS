"""
Collision Service - Business logic for handling collision data
"""
import uuid
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from database.connection import db_manager
from xml_processing.mapper import xml_mapper
from xml_processing.validator import xml_validator
from services.duplicate_checker import duplicate_checker
from config.settings import Config


class CollisionService:
    """Service for managing collision data and XML operations"""
    
    def __init__(self):
        self.mapper = xml_mapper
        self.validator = xml_validator
        self.duplicate_checker = duplicate_checker
    
    def create_xml_document(
        self, 
        collisions: List[Dict[str, Any]], 
        request_id: Optional[str] = None
    ) -> Tuple[str, str, bool, Optional[str]]:
        """
        Create XML document from collision data
        
        Args:
            collisions: List of collision data dictionaries
            request_id: Optional request identifier
            
        Returns:
            Tuple of (request_id, xml_content, is_valid, error_message)
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        # Create XML using mapper
        xml_element = self.mapper.create_collision_dataset(collisions, request_id)
        xml_content = self.mapper.to_xml_string(xml_element)
        
        # Validate XML
        is_valid, error = self.validator.validate(xml_content)
        
        return request_id, xml_content, is_valid, error
    
    def save_xml_document(
        self, 
        request_id: str, 
        xml_content: str, 
        is_valid: bool,
        validation_error: Optional[str] = None
    ) -> Tuple[Optional[int], str]:
        """
        Save XML document to database
        
        Args:
            request_id: Request identifier
            xml_content: XML content string
            is_valid: Whether XML passed validation
            validation_error: Optional validation error message
            
        Returns:
            Tuple of (document_id, status)
        """
        status = "VALID" if is_valid else "INVALID"
        mapper_version = "1.0.0"  # Current mapper version
        
        try:
            query = """
                INSERT INTO collision_documents (request_id, xml_documento, status, validation_errors, mapper_version)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            result = db_manager.execute_query(
                query, 
                (request_id, xml_content, status, validation_error, mapper_version)
            )
            document_id = result[0]['id'] if result else None
            return document_id, "OK"
        except Exception as e:
            return None, f"ERRO_PERSISTENCIA: {str(e)}"
    
    def process_and_store_collisions(
        self, 
        collisions: List[Dict[str, Any]],
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        Full pipeline: check duplicates, create XML, validate, store, notify webhook
        
        Args:
            collisions: List of collision data
            skip_duplicates: If True, filter out duplicate collisions before processing
            
        Returns:
            Result dictionary with status and details
        """
        # Check for duplicates if requested
        duplicate_stats = None
        if skip_duplicates:
            new_collisions, duplicate_collisions, stats = self.duplicate_checker.check_for_duplicates(collisions)
            duplicate_stats = stats
            
            print(f"[Duplicate Check] Total: {stats['total']}, New: {stats['new']}, Duplicates: {stats['duplicates']}")
            
            if stats['new'] == 0:
                # All collisions are duplicates
                return {
                    "request_id": None,
                    "status": "ALL_DUPLICATES",
                    "document_id": None,
                    "error": "All collision records already exist in the database",
                    "duplicate_stats": duplicate_stats
                }
            
            # Use only new collisions
            collisions = new_collisions
        
        # Create and validate XML
        request_id, xml_content, is_valid, validation_error = self.create_xml_document(collisions)
        
        if not is_valid:
            # Notify webhook about validation error
            self._notify_webhook(request_id, "ERRO_VALIDACAO", None)
            return {
                "request_id": request_id,
                "status": "ERRO_VALIDACAO",
                "document_id": None,
                "error": validation_error,
                "duplicate_stats": duplicate_stats
            }
        
        # Save to database
        document_id, persist_status = self.save_xml_document(
            request_id, 
            xml_content, 
            is_valid, 
            validation_error
        )
        
        if document_id is None:
            # Notify webhook about persistence error
            self._notify_webhook(request_id, "ERRO_PERSISTENCIA", None)
            return {
                "request_id": request_id,
                "status": "ERRO_PERSISTENCIA",
                "document_id": None,
                "error": persist_status,
                "duplicate_stats": duplicate_stats
            }
        
        # Notify webhook about success
        self._notify_webhook(request_id, "OK", document_id)
        
        return {
            "request_id": request_id,
            "status": "OK",
            "document_id": document_id,
            "error": None,
            "duplicate_stats": duplicate_stats
        }
    
    def _notify_webhook(self, request_id: str, status: str, document_id: Optional[int]):
        """Send notification to webhook URL"""
        try:
            webhook_url = Config.WEBHOOK_URL
            if webhook_url:
                payload = {
                    "request_id": request_id,
                    "status": status,
                    "document_id": document_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Warning: Failed to notify webhook: {e}")
    
    def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        query = """
            SELECT id, request_id, xml_documento::text as xml_documento, 
                   status, validation_errors, data_criacao, mapper_version
            FROM collision_documents
            WHERE id = %s
        """
        result = db_manager.execute_query(query, (document_id,))
        return result[0] if result else None
    
    def get_document_by_request_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get document by request ID"""
        query = """
            SELECT id, request_id, xml_documento::text as xml_documento, 
                   status, validation_errors, data_criacao, mapper_version
            FROM collision_documents
            WHERE request_id = %s
        """
        result = db_manager.execute_query(query, (request_id,))
        return result[0] if result else None
    
    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all documents with pagination"""
        query = """
            SELECT id, request_id, status, data_criacao, mapper_version,
                   (xpath('count(//col:collision)', xml_documento, 
                    ARRAY[ARRAY['col', 'http://collision.data/schema']]))[1]::text::integer as collision_count
            FROM collision_documents
            ORDER BY data_criacao DESC
            LIMIT %s OFFSET %s
        """
        return db_manager.execute_query(query, (limit, offset))


# Singleton instance
collision_service = CollisionService()
