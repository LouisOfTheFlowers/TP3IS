"""
Duplicate Detection Service
Checks for duplicate collision records before inserting
"""
from typing import List, Dict, Any, Set, Tuple
from database.connection import db_manager


class DuplicateChecker:
    """Service for detecting duplicate collision records"""
    
    def __init__(self):
        self.namespace = [['col', 'http://collision.data/schema']]
    
    def check_for_duplicates(
        self, 
        collisions: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
        """
        Check which collisions already exist in the database
        
        Args:
            collisions: List of collision data to check
            
        Returns:
            Tuple of (new_collisions, duplicate_collisions, stats)
        """
        if not collisions:
            return [], [], {"total": 0, "new": 0, "duplicates": 0}
        
        # Extract unique identifiers from input collisions
        collision_keys = set()
        collision_map = {}
        
        for collision in collisions:
            key = self._create_collision_key(collision)
            collision_keys.add(key)
            collision_map[key] = collision
        
        # Query database for existing collisions
        existing_keys = self._get_existing_collision_keys(collision_keys)
        
        # Separate new from duplicates
        new_collisions = []
        duplicate_collisions = []
        
        for key, collision in collision_map.items():
            if key in existing_keys:
                duplicate_collisions.append(collision)
            else:
                new_collisions.append(collision)
        
        stats = {
            "total": len(collisions),
            "new": len(new_collisions),
            "duplicates": len(duplicate_collisions)
        }
        
        return new_collisions, duplicate_collisions, stats
    
    def _create_collision_key(self, collision: Dict[str, Any]) -> str:
        """
        Create a unique key for a collision based on crash_date and crash_time
        
        Args:
            collision: Collision data dictionary
            
        Returns:
            Unique key string
        """
        date = str(collision.get("crash_date", "")).strip()
        time = str(collision.get("crash_time", "")).strip()
        
        # Normalize time format (handle both HH:MM and H:MM)
        if time and ":" in time:
            parts = time.split(":")
            hour = int(parts[0]) if parts[0].isdigit() else 0
            minute = int(parts[1]) if parts[1].isdigit() else 0
            time = f"{hour:02d}:{minute:02d}"
        
        return f"{date}|{time}"
    
    def _get_existing_collision_keys(self, keys: Set[str]) -> Set[str]:
        """
        Query database to find which collision keys already exist
        
        Args:
            keys: Set of collision keys to check
            
        Returns:
            Set of keys that exist in the database
        """
        if not keys:
            return set()
        
        # Build the query to extract all collision dates and times from XML
        query = """
            WITH collision_data AS (
                SELECT 
                    unnest(xpath('//col:collision/col:crashInfo/col:date/text()', 
                        xml_documento::xml, 
                        ARRAY[ARRAY['col', 'http://collision.data/schema']]))::text as crash_date,
                    unnest(xpath('//col:collision/col:crashInfo/col:time/text()', 
                        xml_documento::xml, 
                        ARRAY[ARRAY['col', 'http://collision.data/schema']]))::text as crash_time
                FROM collision_documents
            )
            SELECT DISTINCT crash_date, crash_time
            FROM collision_data
        """
        
        try:
            results = db_manager.execute_query(query)
            
            existing_keys = set()
            for row in results:
                date = row.get('crash_date', '').strip()
                time = row.get('crash_time', '').strip()
                
                # Normalize time format
                if time and ":" in time:
                    parts = time.split(":")
                    hour = int(parts[0]) if parts[0].isdigit() else 0
                    minute = int(parts[1]) if parts[1].isdigit() else 0
                    time = f"{hour:02d}:{minute:02d}"
                
                key = f"{date}|{time}"
                existing_keys.add(key)
            
            return existing_keys
            
        except Exception as e:
            print(f"⚠️  Error checking duplicates: {e}")
            return set()
    
    def get_duplicate_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about duplicate data in the database
        
        Returns:
            Dictionary with duplicate statistics
        """
        query = """
            WITH collision_data AS (
                SELECT 
                    unnest(xpath('//col:collision/col:crashInfo/col:date/text()', 
                        xml_documento::xml, 
                        ARRAY[ARRAY['col', 'http://collision.data/schema']]))::text as crash_date,
                    unnest(xpath('//col:collision/col:crashInfo/col:time/text()', 
                        xml_documento::xml, 
                        ARRAY[ARRAY['col', 'http://collision.data/schema']]))::text as crash_time
                FROM collision_documents
            ),
            duplicate_counts AS (
                SELECT crash_date, crash_time, COUNT(*) as count
                FROM collision_data
                GROUP BY crash_date, crash_time
                HAVING COUNT(*) > 1
            )
            SELECT 
                COUNT(*) as duplicate_groups,
                SUM(count) as total_duplicates,
                MAX(count) as max_duplicates
            FROM duplicate_counts
        """
        
        try:
            result = db_manager.execute_query(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "duplicate_groups": row.get('duplicate_groups', 0) or 0,
                    "total_duplicates": row.get('total_duplicates', 0) or 0,
                    "max_duplicates": row.get('max_duplicates', 0) or 0
                }
            return {
                "duplicate_groups": 0,
                "total_duplicates": 0,
                "max_duplicates": 0
            }
        except Exception as e:
            print(f"⚠️  Error getting duplicate statistics: {e}")
            return {
                "duplicate_groups": 0,
                "total_duplicates": 0,
                "max_duplicates": 0,
                "error": str(e)
            }


# Singleton instance
duplicate_checker = DuplicateChecker()
