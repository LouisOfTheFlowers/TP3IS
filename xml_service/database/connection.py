"""
Database connection and management
"""
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config.settings import Config


class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""
    
    def __init__(self):
        self.config = Config.get_db_config()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            # Force IPv4 by resolving hostname to IPv4 address
            import socket
            config = self.config.copy()
            try:
                # Try to resolve to IPv4
                ipv4_addr = socket.getaddrinfo(config['host'], config['port'], socket.AF_INET)[0][4][0]
                config['host'] = ipv4_addr
            except:
                pass  # Use original host if IPv4 resolution fails
            
            conn = psycopg2.connect(**config)
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Context manager for database cursors"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except psycopg2.Error as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
    
    def execute_query(self, query, params=None, fetch=True):
        """Execute a query and optionally fetch results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None
    
    def execute_xpath_query(self, xpath_expression, document_id=None):
        """Execute an XPath query on stored XML documents"""
        if document_id:
            query = """
                SELECT id, 
                       xpath(%s, xml_documento) as result
                FROM collision_documents
                WHERE id = %s
            """
            return self.execute_query(query, (xpath_expression, document_id))
        else:
            query = """
                SELECT id,
                       xpath(%s, xml_documento) as result
                FROM collision_documents
                WHERE status = 'VALID'
            """
            return self.execute_query(query, (xpath_expression,))


# Singleton instance
db_manager = DatabaseManager()
