"""
XPath Query Service - Executes XPath queries on stored XML documents
This is the core service that the BI Service will call for data retrieval
"""
from typing import List, Dict, Any, Optional
from database.connection import db_manager
from lxml import etree


class XPathQueryService:
    """Service for executing XPath queries on XML documents in PostgreSQL"""
    
    NAMESPACE = "http://collision.data/schema"
    NS_ARRAY = f"ARRAY[ARRAY['col', '{NAMESPACE}']]"
    
    def execute_xpath(
        self, 
        xpath_expression: str, 
        document_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute XPath query on stored XML documents
        
        Args:
            xpath_expression: XPath expression to execute
            document_id: Optional specific document ID
            
        Returns:
            List of results
        """
        if document_id:
            query = f"""
                SELECT id as document_id,
                       xpath(%s, xml_documento, {self.NS_ARRAY})::text[] as result
                FROM collision_documents
                WHERE id = %s AND status = 'VALID'
            """
            return db_manager.execute_query(query, (xpath_expression, document_id))
        else:
            query = f"""
                SELECT id as document_id,
                       xpath(%s, xml_documento, {self.NS_ARRAY})::text[] as result
                FROM collision_documents
                WHERE status = 'VALID'
            """
            return db_manager.execute_query(query, (xpath_expression,))
    
    # ============================================================
    # COMPLEX QUERY 1: Casualties by Weather Condition
    # ============================================================
    def get_casualties_by_weather(
        self, 
        weather_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get total casualties grouped by weather condition
        Uses XPath to extract and aggregate data
        
        Args:
            weather_filter: Optional filter for specific weather condition
            
        Returns:
            List of weather conditions with casualty counts
        """
        if weather_filter:
            query = f"""
                WITH extracted_data AS (
                    SELECT 
                        unnest(xpath('//col:collision[col:weather/col:condition[contains(text(), $1)]]/col:weather/col:condition/text()', 
                               xml_documento, {self.NS_ARRAY}))::text as weather,
                        unnest(xpath('//col:collision[col:weather/col:condition[contains(text(), $1)]]/col:casualties/col:personsInjured/text()', 
                               xml_documento, {self.NS_ARRAY}))::text::integer as injured,
                        unnest(xpath('//col:collision[col:weather/col:condition[contains(text(), $1)]]/col:casualties/col:personsKilled/text()', 
                               xml_documento, {self.NS_ARRAY}))::text::integer as killed
                    FROM collision_documents
                    WHERE status = 'VALID'
                )
                SELECT 
                    weather as weather_condition,
                    COUNT(*) as total_accidents,
                    SUM(injured) as total_injured,
                    SUM(killed) as total_killed,
                    ROUND(AVG(injured + killed)::numeric, 2) as avg_casualties_per_accident
                FROM extracted_data
                WHERE weather IS NOT NULL AND weather != ''
                GROUP BY weather
                ORDER BY total_accidents DESC
            """
            # Use LATERAL and parameter binding properly
            query = f"""
                WITH collision_data AS (
                    SELECT 
                        c.id,
                        (xpath('//col:collision/col:weather/col:condition/text()', xml_documento, {self.NS_ARRAY})) as weather_nodes,
                        (xpath('//col:collision/col:casualties/col:personsInjured/text()', xml_documento, {self.NS_ARRAY})) as injured_nodes,
                        (xpath('//col:collision/col:casualties/col:personsKilled/text()', xml_documento, {self.NS_ARRAY})) as killed_nodes
                    FROM collision_documents c
                    WHERE status = 'VALID'
                ),
                expanded AS (
                    SELECT 
                        weather_nodes[i]::text as weather,
                        COALESCE(injured_nodes[i]::text::integer, 0) as injured,
                        COALESCE(killed_nodes[i]::text::integer, 0) as killed
                    FROM collision_data,
                         generate_series(1, array_length(weather_nodes, 1)) as i
                )
                SELECT 
                    weather as weather_condition,
                    COUNT(*) as total_accidents,
                    SUM(injured) as total_injured,
                    SUM(killed) as total_killed,
                    ROUND(AVG(injured + killed)::numeric, 2) as avg_casualties_per_accident
                FROM expanded
                WHERE weather IS NOT NULL AND weather != '' AND weather ILIKE %s
                GROUP BY weather
                ORDER BY total_accidents DESC
            """
            return db_manager.execute_query(query, (f"%{weather_filter}%",))
        else:
            query = f"""
                WITH collision_data AS (
                    SELECT 
                        (xpath('//col:collision/col:weather/col:condition/text()', xml_documento, {self.NS_ARRAY})) as weather_nodes,
                        (xpath('//col:collision/col:casualties/col:personsInjured/text()', xml_documento, {self.NS_ARRAY})) as injured_nodes,
                        (xpath('//col:collision/col:casualties/col:personsKilled/text()', xml_documento, {self.NS_ARRAY})) as killed_nodes
                    FROM collision_documents
                    WHERE status = 'VALID'
                ),
                expanded AS (
                    SELECT 
                        weather_nodes[i]::text as weather,
                        COALESCE(injured_nodes[i]::text::integer, 0) as injured,
                        COALESCE(killed_nodes[i]::text::integer, 0) as killed
                    FROM collision_data,
                         generate_series(1, GREATEST(array_length(weather_nodes, 1), 1)) as i
                    WHERE array_length(weather_nodes, 1) > 0
                )
                SELECT 
                    weather as weather_condition,
                    COUNT(*) as total_accidents,
                    SUM(injured) as total_injured,
                    SUM(killed) as total_killed,
                    ROUND(AVG(injured + killed)::numeric, 2) as avg_casualties_per_accident
                FROM expanded
                WHERE weather IS NOT NULL AND weather != ''
                GROUP BY weather
                ORDER BY total_accidents DESC
            """
            return db_manager.execute_query(query)
    
    # ============================================================
    # COMPLEX QUERY 2: Accidents by Contributing Factor
    # ============================================================
    def get_accidents_by_contributing_factor(
        self, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get accident counts grouped by contributing factor
        Uses XPath to extract factors and aggregate
        
        Args:
            limit: Maximum number of factors to return
            
        Returns:
            List of contributing factors with accident counts
        """
        query = f"""
            WITH factors AS (
                SELECT 
                    unnest(xpath('//col:collision/col:contributingFactors/col:factor/text()', 
                           xml_documento, {self.NS_ARRAY}))::text as factor
                FROM collision_documents
                WHERE status = 'VALID'
            )
            SELECT 
                factor as contributing_factor,
                COUNT(*) as accident_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM factors
            WHERE factor IS NOT NULL AND factor != '' AND factor != 'Unspecified'
            GROUP BY factor
            ORDER BY accident_count DESC
            LIMIT %s
        """
        return db_manager.execute_query(query, (limit,))
    
    # ============================================================
    # COMPLEX QUERY 3: Time-based Analysis (Accidents by Hour/Date)
    # ============================================================
    def get_accidents_by_time_period(
        self, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "hour"  # "hour", "date", "month"
    ) -> List[Dict[str, Any]]:
        """
        Get accidents grouped by time period with filtering
        Uses XPath for extraction and SQL for aggregation
        
        Args:
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            group_by: Grouping level - hour, date, or month
            
        Returns:
            List of time periods with accident counts and casualties
        """
        if group_by == "hour":
            time_expr = "SUBSTRING(time FROM 1 FOR 2)"
            group_name = "hour"
        elif group_by == "month":
            time_expr = "SUBSTRING(date FROM 1 FOR 7)"
            group_name = "month"
        else:  # date
            time_expr = "date"
            group_name = "date"
        
        date_filter = ""
        params = []
        
        if start_date and end_date:
            date_filter = "AND date >= %s AND date <= %s"
            params = [start_date, end_date]
        elif start_date:
            date_filter = "AND date >= %s"
            params = [start_date]
        elif end_date:
            date_filter = "AND date <= %s"
            params = [end_date]
        
        query = f"""
            WITH collision_data AS (
                SELECT 
                    (xpath('//col:collision/col:crashInfo/col:date/text()', xml_documento, {self.NS_ARRAY})) as date_nodes,
                    (xpath('//col:collision/col:crashInfo/col:time/text()', xml_documento, {self.NS_ARRAY})) as time_nodes,
                    (xpath('//col:collision/col:casualties/col:personsInjured/text()', xml_documento, {self.NS_ARRAY})) as injured_nodes,
                    (xpath('//col:collision/col:casualties/col:personsKilled/text()', xml_documento, {self.NS_ARRAY})) as killed_nodes
                FROM collision_documents
                WHERE status = 'VALID'
            ),
            expanded AS (
                SELECT 
                    date_nodes[i]::text as date,
                    time_nodes[i]::text as time,
                    COALESCE(injured_nodes[i]::text::integer, 0) as injured,
                    COALESCE(killed_nodes[i]::text::integer, 0) as killed
                FROM collision_data,
                     generate_series(1, GREATEST(array_length(date_nodes, 1), 1)) as i
                WHERE array_length(date_nodes, 1) > 0
            )
            SELECT 
                {time_expr} as {group_name},
                COUNT(*) as total_accidents,
                SUM(injured) as total_injured,
                SUM(killed) as total_killed
            FROM expanded
            WHERE date IS NOT NULL {date_filter}
            GROUP BY {time_expr}
            ORDER BY {group_name}
        """
        return db_manager.execute_query(query, params if params else None)
    
    # ============================================================
    # COMPLEX QUERY 4: Vehicle Type Analysis
    # ============================================================
    def get_accidents_by_vehicle_type(
        self, 
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Get accident statistics by vehicle type involved
        
        Args:
            limit: Maximum number of vehicle types to return
            
        Returns:
            List of vehicle types with accident statistics
        """
        query = f"""
            WITH vehicles AS (
                SELECT 
                    unnest(xpath('//col:collision/col:vehicles/col:vehicle/text()', 
                           xml_documento, {self.NS_ARRAY}))::text as vehicle_type
                FROM collision_documents
                WHERE status = 'VALID'
            )
            SELECT 
                vehicle_type,
                COUNT(*) as involvement_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM vehicles
            WHERE vehicle_type IS NOT NULL AND vehicle_type != ''
            GROUP BY vehicle_type
            ORDER BY involvement_count DESC
            LIMIT %s
        """
        return db_manager.execute_query(query, (limit,))
    
    # ============================================================
    # COMPLEX QUERY 5: Weather-Accident Correlation
    # ============================================================
    def get_weather_accident_correlation(self) -> List[Dict[str, Any]]:
        """
        Get correlation data between weather conditions and accident severity
        This is the key query for the front-end correlation visualization
        
        Returns:
            List of weather conditions with severity metrics
        """
        query = f"""
            WITH collision_data AS (
                SELECT 
                    (xpath('//col:collision/col:weather/col:condition/text()', xml_documento, {self.NS_ARRAY})) as weather_nodes,
                    (xpath('//col:collision/col:casualties/col:personsInjured/text()', xml_documento, {self.NS_ARRAY})) as injured_nodes,
                    (xpath('//col:collision/col:casualties/col:personsKilled/text()', xml_documento, {self.NS_ARRAY})) as killed_nodes,
                    (xpath('//col:collision/col:casualties/col:pedestriansInjured/text()', xml_documento, {self.NS_ARRAY})) as ped_injured,
                    (xpath('//col:collision/col:casualties/col:cyclistsInjured/text()', xml_documento, {self.NS_ARRAY})) as cyc_injured
                FROM collision_documents
                WHERE status = 'VALID'
            ),
            expanded AS (
                SELECT 
                    weather_nodes[i]::text as weather,
                    COALESCE(injured_nodes[i]::text::integer, 0) as injured,
                    COALESCE(killed_nodes[i]::text::integer, 0) as killed,
                    COALESCE(ped_injured[i]::text::integer, 0) as pedestrians_injured,
                    COALESCE(cyc_injured[i]::text::integer, 0) as cyclists_injured
                FROM collision_data,
                     generate_series(1, GREATEST(array_length(weather_nodes, 1), 1)) as i
                WHERE array_length(weather_nodes, 1) > 0
            )
            SELECT 
                COALESCE(weather, 'Unknown') as weather_condition,
                COUNT(*) as total_accidents,
                SUM(injured) as total_injured,
                SUM(killed) as total_killed,
                SUM(pedestrians_injured) as pedestrians_injured,
                SUM(cyclists_injured) as cyclists_injured,
                ROUND(AVG(injured)::numeric, 2) as avg_injured_per_accident,
                ROUND(AVG(killed)::numeric, 4) as avg_killed_per_accident,
                ROUND((SUM(killed)::numeric / NULLIF(COUNT(*), 0)) * 1000, 2) as fatality_rate_per_1000
            FROM expanded
            WHERE weather IS NOT NULL AND weather != ''
            GROUP BY weather
            ORDER BY total_accidents DESC
        """
        return db_manager.execute_query(query)
    
    # ============================================================
    # SUMMARY STATISTICS
    # ============================================================
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get overall summary statistics from all documents
        
        Returns:
            Dictionary with summary statistics
        """
        query = f"""
            WITH collision_stats AS (
                SELECT 
                    SUM((xpath('count(//col:collision)', xml_documento, {self.NS_ARRAY}))[1]::text::integer) as total_collisions,
                    SUM((xpath('sum(//col:collision/col:casualties/col:personsInjured)', xml_documento, {self.NS_ARRAY}))[1]::text::integer) as total_injured,
                    SUM((xpath('sum(//col:collision/col:casualties/col:personsKilled)', xml_documento, {self.NS_ARRAY}))[1]::text::integer) as total_killed
                FROM collision_documents
                WHERE status = 'VALID'
            )
            SELECT 
                COALESCE(total_collisions, 0) as total_collisions,
                COALESCE(total_injured, 0) as total_injured,
                COALESCE(total_killed, 0) as total_killed,
                (SELECT COUNT(*) FROM collision_documents WHERE status = 'VALID') as total_documents
            FROM collision_stats
        """
        result = db_manager.execute_query(query)
        return result[0] if result else {
            "total_collisions": 0,
            "total_injured": 0,
            "total_killed": 0,
            "total_documents": 0
        }


# Singleton instance
xpath_query_service = XPathQueryService()
