"""
Autofill Mapper - Maps validated requirements to form fields using form_fields.json
"""

from typing import Dict, List, Any
from data.data_loader import data_loader

class AutofillMapper:
    """Map system configuration to form fields."""
    
    def __init__(self):
        self.form_fields = data_loader.form_fields if hasattr(data_loader, 'form_fields') else {}
    
    def generate_autofill(self, validated_config: Dict, confidence: float) -> Dict:
        """
        Generate autofill suggestions for form fields.
        Only triggers if confidence > threshold.
        """
        if confidence < 0.85:
            return {
                "should_autofill": False,
                "confidence": confidence,
                "message": "Confidence too low for autofill"
            }
        
        # Map configuration to form fields
        field_mappings = {}
        
        # Controller selection
        if "controller" in validated_config:
            suitable_controllers = validated_config["controller"].get("suitable_controllers", [])
            if suitable_controllers:
                controller_id = suitable_controllers[0]["id"]
                field_mappings["controller_type"] = {
                    "value": controller_id,
                    "field_id": self._get_field_id("controller_type"),
                    "confidence": 0.95
                }
        
        # I/O configuration
        if "io_requirements" in validated_config:
            io_reqs = validated_config["io_requirements"]
            
            field_mappings["analog_inputs"] = {
                "value": io_reqs.get("analog_input", 0),
                "field_id": self._get_field_id("analog_inputs"),
                "confidence": 0.9
            }
            
            field_mappings["digital_outputs"] = {
                "value": io_reqs.get("digital_output", 0),
                "field_id": self._get_field_id("digital_outputs"),
                "confidence": 0.9
            }
        
        # Module configuration
        if "modules" in validated_config:
            modules = validated_config["modules"].get("modules_required", [])
            field_mappings["io_modules"] = {
                "value": [m["type"] for m in modules],
                "field_id": self._get_field_id("io_modules"),
                "confidence": 0.85
            }
        
        # Map specific form fields from form_fields.json
        self._map_performance_fields(validated_config, field_mappings)
        self._map_connectivity_fields(validated_config, field_mappings)
        self._map_environment_fields(validated_config, field_mappings)
        
        return {
            "should_autofill": True,
            "confidence": confidence,
            "field_mappings": field_mappings,
            "message": f"Ready to autofill {len(field_mappings)} fields"
        }
    
    def _get_field_id(self, field_name: str) -> str:
        """Get form field ID from form_fields.json."""
        # Check all sections for the field
        for section_name, section_fields in self.form_fields.items():
            if field_name in section_fields:
                return section_fields[field_name].get("id", field_name)
        return field_name
    
    def _map_performance_fields(self, validated_config: Dict, field_mappings: Dict):
        """Map performance computing fields."""
        # Map processor tier based on requirements
        io_total = validated_config.get("io_requirements", {}).get("total_io", 0)
        if io_total > 32:
            field_mappings["processorTier"] = {
                "value": "Performance (Intel Core i5)",
                "field_id": self._get_field_id("processorTier"),
                "confidence": 0.8
            }
        elif io_total > 16:
            field_mappings["processorTier"] = {
                "value": "Standard (Intel Core i3)",
                "field_id": self._get_field_id("processorTier"),
                "confidence": 0.85
            }
        
        # Map memory based on system complexity
        if io_total > 24:
            field_mappings["memoryCapacity"] = {
                "value": "16GB",
                "field_id": self._get_field_id("memoryCapacity"),
                "confidence": 0.8
            }
        elif io_total > 8:
            field_mappings["memoryCapacity"] = {
                "value": "8GB",
                "field_id": self._get_field_id("memoryCapacity"),
                "confidence": 0.85
            }
    
    def _map_connectivity_fields(self, validated_config: Dict, field_mappings: Dict):
        """Map I/O and connectivity fields."""
        io_reqs = validated_config.get("io_requirements", {})
        
        # Map digital I/O
        if io_reqs.get("digital_input", 0) > 0 or io_reqs.get("digital_output", 0) > 0:
            total_digital = io_reqs.get("digital_input", 0) + io_reqs.get("digital_output", 0)
            field_mappings["digitalIO"] = {
                "value": total_digital,
                "field_id": self._get_field_id("digitalIO"),
                "confidence": 0.95
            }
        
        # Map analog I/O
        if io_reqs.get("analog_input", 0) > 0 or io_reqs.get("analog_output", 0) > 0:
            total_analog = io_reqs.get("analog_input", 0) + io_reqs.get("analog_output", 0)
            field_mappings["analogIO"] = {
                "value": total_analog,
                "field_id": self._get_field_id("analogIO"),
                "confidence": 0.95
            }
        
        # Default network ports recommendation
        field_mappings["networkPorts"] = {
            "value": "2 x RJ45",
            "field_id": self._get_field_id("networkPorts"),
            "confidence": 0.8
        }
    
    def _map_environment_fields(self, validated_config: Dict, field_mappings: Dict):
        """Map environmental fields."""
        # Default environmental settings for industrial use
        field_mappings["operatingTemperature"] = {
            "value": "Extended (-20°C to 60°C)",
            "field_id": self._get_field_id("operatingTemperature"),
            "confidence": 0.7
        }
        
        field_mappings["ingressProtection"] = {
            "value": "IP54 (Dust/splash resistant)",
            "field_id": self._get_field_id("ingressProtection"),
            "confidence": 0.7
        }