"""
XML Validator - Validates XML documents against schema
"""
from lxml import etree
from typing import Tuple, Optional
import os


class XMLValidator:
    """Validates XML documents against XSD schema"""
    
    def __init__(self, schema_path: str = None):
        if schema_path is None:
            schema_path = os.path.join(
                os.path.dirname(__file__),
                "schema",
                "collision_schema.xsd"
            )
        self.schema_path = schema_path
        self._schema = None
    
    @property
    def schema(self) -> etree.XMLSchema:
        """Lazy load schema"""
        if self._schema is None:
            with open(self.schema_path, 'rb') as f:
                schema_doc = etree.parse(f)
                self._schema = etree.XMLSchema(schema_doc)
        return self._schema
    
    def validate(self, xml_content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate XML string against schema
        
        Args:
            xml_content: XML content as string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            xml_doc = etree.fromstring(xml_content.encode('utf-8'))
            self.schema.assertValid(xml_doc)
            return True, None
        except etree.XMLSyntaxError as e:
            return False, f"XML Syntax Error: {str(e)}"
        except etree.DocumentInvalid as e:
            return False, f"Schema Validation Error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected Error: {str(e)}"
    
    def validate_element(self, xml_element: etree.Element) -> Tuple[bool, Optional[str]]:
        """
        Validate XML element against schema
        
        Args:
            xml_element: lxml Element object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.schema.assertValid(xml_element)
            return True, None
        except etree.DocumentInvalid as e:
            return False, f"Schema Validation Error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected Error: {str(e)}"
    
    def get_validation_errors(self, xml_content: str) -> list:
        """
        Get list of all validation errors
        
        Args:
            xml_content: XML content as string
            
        Returns:
            List of validation error messages
        """
        errors = []
        try:
            xml_doc = etree.fromstring(xml_content.encode('utf-8'))
            self.schema.validate(xml_doc)
            for error in self.schema.error_log:
                errors.append({
                    "line": error.line,
                    "column": error.column,
                    "message": error.message,
                    "level": error.level_name
                })
        except etree.XMLSyntaxError as e:
            errors.append({
                "line": e.lineno,
                "column": e.offset,
                "message": str(e),
                "level": "FATAL"
            })
        except Exception as e:
            errors.append({
                "line": 0,
                "column": 0,
                "message": str(e),
                "level": "FATAL"
            })
        
        return errors


# Singleton instance
xml_validator = XMLValidator()
