"""
XML Mapper - Manually maps collision data to XML structure
This mapper creates XML documents following the collision_schema.xsd
"""
from lxml import etree
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
import os


class CollisionXMLMapper:
    """
    Maps collision data to XML format following the defined schema.
    This is a manual mapper - not auto-generated.
    """
    
    NAMESPACE = "http://collision.data/schema"
    NSMAP = {None: NAMESPACE, "col": NAMESPACE}
    
    def __init__(self):
        self.schema_path = os.path.join(
            os.path.dirname(__file__), 
            "schema", 
            "collision_schema.xsd"
        )
        self._schema = None
    
    @property
    def schema(self):
        """Lazy load the XML schema"""
        if self._schema is None:
            with open(self.schema_path, 'rb') as f:
                schema_doc = etree.parse(f)
                self._schema = etree.XMLSchema(schema_doc)
        return self._schema
    
    def _create_element(self, tag: str, text: Optional[str] = None, attrib: Dict = None) -> etree.Element:
        """Create an XML element with namespace"""
        element = etree.Element(f"{{{self.NAMESPACE}}}{tag}", nsmap=self.NSMAP)
        if text is not None:
            element.text = str(text)
        if attrib:
            for key, value in attrib.items():
                element.set(key, str(value))
        return element
    
    def _sub_element(self, parent: etree.Element, tag: str, text: Optional[str] = None) -> etree.Element:
        """Create a sub-element with namespace"""
        element = etree.SubElement(parent, f"{{{self.NAMESPACE}}}{tag}")
        if text is not None:
            element.text = str(text)
        return element
    
    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert value to integer"""
        try:
            if value is None or value == '' or str(value).lower() == 'nan':
                return default
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    def _safe_str(self, value: Any, default: str = "") -> str:
        """Safely convert value to string"""
        if value is None or str(value).lower() == 'nan' or str(value).lower() == 'none':
            return default
        return str(value).strip()
    
    def _format_date(self, date_str: str) -> str:
        """Format date string to ISO format (YYYY-MM-DD)"""
        try:
            if not date_str or str(date_str).lower() in ['nan', 'none', '']:
                return ""  # Return empty string instead of today's date
            
            # Handle various date formats
            date_str = str(date_str).strip()
            if 'T' in date_str:
                date_str = date_str.split('T')[0]
            
            # Validate it's a proper date format (YYYY-MM-DD)
            if len(date_str) >= 10:
                # Try to parse to validate
                datetime.strptime(date_str[:10], "%Y-%m-%d")
                return date_str[:10]
            
            return ""  # Return empty string if can't parse
        except Exception as e:
            print(f"⚠️  Date parsing error for '{date_str}': {e}")
            return ""  # Return empty string instead of today's date
    
    def map_collision_to_xml(self, collision_data: Dict[str, Any], collision_id: str) -> etree.Element:
        """
        Map a single collision record to XML element
        
        Args:
            collision_data: Dictionary containing collision data
            collision_id: Unique identifier for the collision
            
        Returns:
            XML Element representing the collision
        """
        # Create collision element
        collision = self._create_element("collision", attrib={"id": collision_id})
        
        # Crash Info
        crash_info = self._sub_element(collision, "crashInfo")
        self._sub_element(crash_info, "date", self._format_date(collision_data.get("crash_date", "")))
        self._sub_element(crash_info, "time", self._safe_str(collision_data.get("crash_time", "00:00")))
        
        # Casualties
        casualties = self._sub_element(collision, "casualties")
        self._sub_element(casualties, "personsInjured", str(self._safe_int(collision_data.get("persons_injured", 0))))
        self._sub_element(casualties, "personsKilled", str(self._safe_int(collision_data.get("persons_killed", 0))))
        self._sub_element(casualties, "pedestriansInjured", str(self._safe_int(collision_data.get("pedestrians_injured", 0))))
        self._sub_element(casualties, "pedestriansKilled", str(self._safe_int(collision_data.get("pedestrians_killed", 0))))
        self._sub_element(casualties, "cyclistsInjured", str(self._safe_int(collision_data.get("cyclists_injured", 0))))
        self._sub_element(casualties, "cyclistsKilled", str(self._safe_int(collision_data.get("cyclists_killed", 0))))
        self._sub_element(casualties, "motoristsInjured", str(self._safe_int(collision_data.get("motorists_injured", 0))))
        self._sub_element(casualties, "motoristsKilled", str(self._safe_int(collision_data.get("motorists_killed", 0))))
        
        # Contributing Factors
        factors = self._sub_element(collision, "contributingFactors")
        for i in range(1, 6):
            factor_value = self._safe_str(collision_data.get(f"factor_{i}", ""))
            if factor_value:
                self._sub_element(factors, "factor", factor_value)
        
        # Vehicles
        vehicles = self._sub_element(collision, "vehicles")
        for i in range(1, 6):
            vehicle_value = self._safe_str(collision_data.get(f"vehicle_{i}", ""))
            if vehicle_value:
                self._sub_element(vehicles, "vehicle", vehicle_value)
        
        # Weather data (from enriched collision data)
        weather = self._sub_element(collision, "weather")
        weather_condition = self._safe_str(collision_data.get("weather_condition", ""))
        if weather_condition:
            self._sub_element(weather, "condition", weather_condition)
        weather_detail = self._safe_str(collision_data.get("weather_detail", ""))
        if weather_detail:
            self._sub_element(weather, "detail", weather_detail)
        
        # Temperature
        temp_f = collision_data.get("temperature_f")
        if temp_f is not None and str(temp_f).lower() not in ['nan', 'none', '']:
            self._sub_element(weather, "temperatureF", f"{float(temp_f):.1f}")
        temp_c = collision_data.get("temperature_c")
        if temp_c is not None and str(temp_c).lower() not in ['nan', 'none', '']:
            self._sub_element(weather, "temperatureC", f"{float(temp_c):.1f}")
        
        # Humidity
        humidity = collision_data.get("humidity")
        if humidity is not None and str(humidity).lower() not in ['nan', 'none', '']:
            self._sub_element(weather, "humidity", f"{float(humidity):.1f}")
        
        # Precipitation
        precipitation = collision_data.get("precipitation")
        if precipitation is not None and str(precipitation).lower() not in ['nan', 'none', '']:
            self._sub_element(weather, "precipitation", f"{float(precipitation):.1f}")
        
        # Wind speed
        wind_speed = collision_data.get("wind_speed")
        if wind_speed is not None and str(wind_speed).lower() not in ['nan', 'none', '']:
            self._sub_element(weather, "windSpeed", f"{float(wind_speed):.1f}")
        
        # Visibility
        visibility = collision_data.get("visibility")
        if visibility is not None and str(visibility).lower() not in ['nan', 'none', '']:
            self._sub_element(weather, "visibility", f"{float(visibility):.1f}")
        
        return collision
    
    def create_collision_dataset(
        self, 
        collisions: List[Dict[str, Any]], 
        request_id: Optional[str] = None,
        source: str = "NYC Open Data"
    ) -> etree.Element:
        """
        Create a complete collision dataset XML document
        
        Args:
            collisions: List of collision dictionaries
            request_id: Optional request identifier
            source: Data source name
            
        Returns:
            Root XML Element for the dataset
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        # Create root element
        root = self._create_element("collisionDataset", attrib={"version": "1.0"})
        
        # Metadata
        metadata = self._sub_element(root, "metadata")
        self._sub_element(metadata, "source", source)
        self._sub_element(metadata, "generatedAt", datetime.utcnow().isoformat())
        self._sub_element(metadata, "totalRecords", str(len(collisions)))
        self._sub_element(metadata, "requestId", request_id)
        
        # Collisions container
        collisions_container = self._sub_element(root, "collisions")
        
        # Add each collision
        for idx, collision_data in enumerate(collisions):
            collision_id = f"COL-{request_id[:8]}-{idx:05d}"
            collision_element = self.map_collision_to_xml(collision_data, collision_id)
            collisions_container.append(collision_element)
        
        return root
    
    def to_xml_string(self, element: etree.Element, pretty_print: bool = True) -> str:
        """Convert XML element to string"""
        return etree.tostring(
            element, 
            encoding='unicode', 
            pretty_print=pretty_print
        )
    
    def validate_xml(self, xml_element: etree.Element) -> tuple[bool, Optional[str]]:
        """
        Validate XML against the schema
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.schema.assertValid(xml_element)
            return True, None
        except etree.DocumentInvalid as e:
            return False, str(e)
    
    def parse_xml_string(self, xml_string: str) -> etree.Element:
        """Parse XML string to element"""
        return etree.fromstring(xml_string.encode('utf-8'))


# Singleton instance
xml_mapper = CollisionXMLMapper()
