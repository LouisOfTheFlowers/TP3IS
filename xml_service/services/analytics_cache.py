"""
Analytics Cache Service - Provides fast aggregated statistics
This service uses direct SQL queries on XML data for fast dashboard performance
"""
from typing import Dict, Any, List, Optional
from database.connection import db_manager


class AnalyticsCacheService:
    """Service for fast aggregated analytics without full XPath scans"""
    
    NAMESPACE = "http://collision.data/schema"
    NS_ARRAY = f"ARRAY[ARRAY['col', '{NAMESPACE}']]"
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get overall summary statistics (fast query)
        Uses document-level aggregation
        """
        query = f"""
            SELECT 
                COUNT(DISTINCT id) as total_documents,
                SUM((xpath('count(//col:collision)', xml_documento, {self.NS_ARRAY}))[1]::text::integer) as total_collisions
            FROM collision_documents
            WHERE status = 'VALID'
        """
        result = db_manager.execute_query(query)
        
        if not result:
            return {
                "totalCollisions": 0,
                "totalInjured": 0,
                "totalKilled": 0,
                "totalDocuments": 0
            }
        
        # Get casualty totals from a sample of recent documents
        casualty_query = f"""
            WITH recent_docs AS (
                SELECT id, xml_documento
                FROM collision_documents
                WHERE status = 'VALID'
                ORDER BY data_criacao DESC
                LIMIT 100
            ),
            casualties AS (
                SELECT 
                    COALESCE(SUM((xpath('sum(//col:collision/col:casualties/col:personsInjured/text())', xml_documento, {self.NS_ARRAY}))[1]::text::numeric), 0) as injured,
                    COALESCE(SUM((xpath('sum(//col:collision/col:casualties/col:personsKilled/text())', xml_documento, {self.NS_ARRAY}))[1]::text::numeric), 0) as killed
                FROM recent_docs
            )
            SELECT 
                ROUND(injured * %s / 100) as total_injured,
                ROUND(killed * %s / 100) as total_killed
            FROM casualties
        """
        
        total_docs = result[0]['total_documents']
        casualty_result = db_manager.execute_query(casualty_query, (total_docs, total_docs))
        
        return {
            "totalCollisions": result[0]['total_collisions'] or 0,
            "totalInjured": int(casualty_result[0]['total_injured']) if casualty_result else 0,
            "totalKilled": int(casualty_result[0]['total_killed']) if casualty_result else 0,
            "totalDocuments": total_docs
        }
    
    def get_weather_correlation_fast(self) -> List[Dict[str, Any]]:
        """
        Get weather correlation data using optimized sampling
        Samples recent documents for faster response
        """
        query = f"""
            WITH recent_docs AS (
                SELECT id, xml_documento
                FROM collision_documents
                WHERE status = 'VALID'
                ORDER BY data_criacao DESC
                LIMIT 200
            ),
            weather_data AS (
                SELECT 
                    unnest(xpath('//col:collision/col:weather/col:condition/text()', xml_documento, {self.NS_ARRAY}))::text as weather,
                    unnest(xpath('//col:collision/col:casualties/col:personsInjured/text()', xml_documento, {self.NS_ARRAY}))::text::integer as injured,
                    unnest(xpath('//col:collision/col:casualties/col:personsKilled/text()', xml_documento, {self.NS_ARRAY}))::text::integer as killed,
                    unnest(xpath('//col:collision/col:casualties/col:pedestriansInjured/text()', xml_documento, {self.NS_ARRAY}))::text::integer as ped_injured,
                    unnest(xpath('//col:collision/col:casualties/col:cyclistsInjured/text()', xml_documento, {self.NS_ARRAY}))::text::integer as cyc_injured
                FROM recent_docs
            )
            SELECT 
                COALESCE(weather, 'Unknown') as weather_condition,
                COUNT(*) as total_accidents,
                SUM(injured) as total_injured,
                SUM(killed) as total_killed,
                SUM(ped_injured) as pedestrians_injured,
                SUM(cyc_injured) as cyclists_injured,
                ROUND(AVG(injured)::numeric, 2) as avg_injured_per_accident,
                ROUND(AVG(killed)::numeric, 2) as avg_killed_per_accident,
                ROUND((SUM(killed)::numeric / NULLIF(COUNT(*), 0)) * 1000, 2) as fatality_rate_per_1000
            FROM weather_data
            WHERE weather IS NOT NULL AND weather != ''
            GROUP BY weather
            ORDER BY total_accidents DESC
            LIMIT 20
        """
        
        return db_manager.execute_query(query)
    
    def get_casualties_by_weather_fast(self, weather_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get casualties by weather condition (optimized)
        """
        filter_clause = "AND weather ILIKE %s" if weather_filter else ""
        params = (f"%{weather_filter}%",) if weather_filter else ()
        
        query = f"""
            WITH recent_docs AS (
                SELECT id, xml_documento
                FROM collision_documents
                WHERE status = 'VALID'
                ORDER BY data_criacao DESC
                LIMIT 150
            ),
            weather_data AS (
                SELECT 
                    unnest(xpath('//col:collision/col:weather/col:condition/text()', xml_documento, {self.NS_ARRAY}))::text as weather,
                    unnest(xpath('//col:collision/col:casualties/col:personsInjured/text()', xml_documento, {self.NS_ARRAY}))::text::integer as injured,
                    unnest(xpath('//col:collision/col:casualties/col:personsKilled/text()', xml_documento, {self.NS_ARRAY}))::text::integer as killed
                FROM recent_docs
            )
            SELECT 
                weather as weather_condition,
                COUNT(*) as total_accidents,
                SUM(injured) as total_injured,
                SUM(killed) as total_killed,
                ROUND(AVG(injured + killed)::numeric, 2) as avg_casualties_per_accident
            FROM weather_data
            WHERE weather IS NOT NULL AND weather != '' {filter_clause}
            GROUP BY weather
            ORDER BY total_accidents DESC
        """
        
        return db_manager.execute_query(query, params)
    
    def get_contributing_factors_fast(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top contributing factors (optimized with sampling)
        """
        query = f"""
            WITH recent_docs AS (
                SELECT xml_documento
                FROM collision_documents
                WHERE status = 'VALID'
                ORDER BY data_criacao DESC
                LIMIT 150
            ),
            factors AS (
                SELECT 
                    unnest(xpath('//col:collision/col:contributingFactors/col:factor/text()', xml_documento, {self.NS_ARRAY}))::text as factor
                FROM recent_docs
            )
            SELECT 
                factor as contributing_factor,
                COUNT(*) as accident_count,
                ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ())::numeric, 2) as percentage
            FROM factors
            WHERE factor IS NOT NULL AND factor != ''
            GROUP BY factor
            ORDER BY accident_count DESC
            LIMIT %s
        """
        
        return db_manager.execute_query(query, (limit,))
    
    def get_time_period_stats_fast(
        self, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "hour"
    ) -> List[Dict[str, Any]]:
        """
        Get accident statistics by time period (optimized)
        """
        # Map group_by to time extraction
        time_extract = {
            "hour": "substring(time_val from 1 for 2)",
            "day": "date_val",
            "month": "substring(date_val from 1 for 7)",
            "year": "substring(date_val from 1 for 4)"
        }
        
        period_expr = time_extract.get(group_by, time_extract["hour"])
        
        query = f"""
            WITH all_docs AS (
                SELECT xml_documento
                FROM collision_documents
                WHERE status = 'VALID'
            ),
            time_data AS (
                SELECT 
                    unnest(xpath('//col:collision/col:crashInfo/col:date/text()', xml_documento, {self.NS_ARRAY}))::text as date_val,
                    unnest(xpath('//col:collision/col:crashInfo/col:time/text()', xml_documento, {self.NS_ARRAY}))::text as time_val,
                    unnest(xpath('//col:collision/col:casualties/col:personsInjured/text()', xml_documento, {self.NS_ARRAY}))::text::integer as injured,
                    unnest(xpath('//col:collision/col:casualties/col:personsKilled/text()', xml_documento, {self.NS_ARRAY}))::text::integer as killed
                FROM all_docs
            )
            SELECT 
                {period_expr} as period,
                COUNT(*) as total_accidents,
                SUM(injured) as total_injured,
                SUM(killed) as total_killed
            FROM time_data
            WHERE date_val IS NOT NULL
            GROUP BY {period_expr}
            ORDER BY period
        """
        
        return db_manager.execute_query(query)
    
    def get_vehicle_types_fast(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Get vehicle type statistics (optimized)
        """
        query = f"""
            WITH recent_docs AS (
                SELECT xml_documento
                FROM collision_documents
                WHERE status = 'VALID'
                ORDER BY data_criacao DESC
                LIMIT 150
            ),
            vehicles AS (
                SELECT 
                    unnest(xpath('//col:collision/col:vehicles/col:vehicle/text()', xml_documento, {self.NS_ARRAY}))::text as vehicle
                FROM recent_docs
            )
            SELECT 
                vehicle as vehicle_type,
                COUNT(*) as involvement_count,
                ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ())::numeric, 2) as percentage
            FROM vehicles
            WHERE vehicle IS NOT NULL AND vehicle != ''
            GROUP BY vehicle
            ORDER BY involvement_count DESC
            LIMIT %s
        """
        
        return db_manager.execute_query(query, (limit,))
    
    def get_latest_collision_date(self) -> Optional[str]:
        """
        Get the most recent collision date in the database
        Used to avoid re-scraping old data
        """
        query = f"""
            WITH recent_docs AS (
                SELECT xml_documento
                FROM collision_documents
                WHERE status = 'VALID'
                ORDER BY data_criacao DESC
                LIMIT 50
            ),
            dates AS (
                SELECT 
                    unnest(xpath('//col:collision/col:crashInfo/col:date/text()', xml_documento, {self.NS_ARRAY}))::text as date_val
                FROM recent_docs
            )
            SELECT MAX(date_val) as latest_date
            FROM dates
            WHERE date_val IS NOT NULL AND date_val ~ '^\d{{4}}-\d{{2}}-\d{{2}}'
        """
        
        result = db_manager.execute_query(query)
        if result and result[0].get('latest_date'):
            return result[0]['latest_date']
        return None


# Singleton instance
analytics_cache = AnalyticsCacheService()
