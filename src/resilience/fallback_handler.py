"""
Fallback Handler - Provides fallback responses when agents fail
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re

class FallbackHandler:
    """
    Provides fallback responses when primary agents fail.
    Uses default configurations and cached responses.
    """
    
    def __init__(self):
        self.default_responses = {
            "technical_validator": {
                "valid": False,
                "confidence": 0.1,
                "message": "Technical validation unavailable - using defaults",
                "controller": {
                    "valid": True,
                    "suitable_controllers": [{"id": "UNO-137", "capacity": 16}]
                },
                "modules": {
                    "valid": True,
                    "modules_required": []
                }
            },
            "commercial_validator": {
                "valid": True,
                "confidence": 0.5,
                "message": "Commercial validation unavailable - estimated pricing",
                "pricing": {
                    "final_price": 1000,
                    "currency": "USD",
                    "confidence": 0.5
                }
            },
            "decision_coordinator": {
                "type": "fallback_response",
                "message": "Decision coordinator unavailable - continue with manual selection"
            }
        }
        
        self.response_cache = {}
    
    def get_fallback_response(self, agent_id: str, input_data: Dict = None) -> Dict:
        """Get fallback response for failed agent."""
        
        # Check cache first
        cache_key = f"{agent_id}_{hash(str(input_data))}"
        if cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key].copy()
            cached_response["cached"] = True
            cached_response["cache_time"] = self.response_cache[cache_key].get("timestamp")
            return cached_response
        
        # Get default response
        fallback = self.default_responses.get(agent_id, {
            "valid": False,
            "confidence": 0.0,
            "message": f"Agent {agent_id} unavailable"
        }).copy()
        
        # Customize based on input if available
        if input_data:
            fallback = self._customize_fallback(agent_id, fallback, input_data)
        
        # Add metadata
        fallback["fallback"] = True
        fallback["agent_id"] = agent_id
        fallback["timestamp"] = datetime.now().isoformat()
        
        # Cache the response
        self.response_cache[cache_key] = fallback.copy()
        
        return fallback
    
    def _customize_fallback(self, agent_id: str, fallback: Dict, input_data: Dict) -> Dict:
        """Customize fallback response based on input data."""
        
        if agent_id == "technical_validator":
            return self._customize_technical_fallback(fallback, input_data)
        elif agent_id == "commercial_validator":
            return self._customize_commercial_fallback(fallback, input_data)
        elif agent_id == "decision_coordinator":
            return self._customize_decision_fallback(fallback, input_data)
        
        return fallback
    
    def _customize_technical_fallback(self, fallback: Dict, input_data: Dict) -> Dict:
        """Customize technical validator fallback."""
        specifications = input_data.get("specifications", [])
        
        # Extract basic I/O requirements
        total_io = 0
        for spec in specifications:
            if "io" in spec.get("constraint", "").lower():
                value = spec.get("value", 0)
                # Extract numeric value from string
                numeric_match = re.findall(r'\d+', str(value))
                if numeric_match:
                    total_io += int(numeric_match[0])
        
        # Select appropriate controller
        if total_io <= 16:
            controller_id = "UNO-137"
        elif total_io <= 32:
            controller_id = "UNO-148"
        else:
            controller_id = "UNO-148"  # Default to largest
        
        fallback["controller"]["suitable_controllers"] = [
            {"id": controller_id, "capacity": 32 if "148" in controller_id else 16}
        ]
        
        return fallback
    
    def _customize_commercial_fallback(self, fallback: Dict, input_data: Dict) -> Dict:
        """Customize commercial validator fallback."""
        # Basic price estimation
        tech_validation = input_data.get("technical_validation", {})
        controllers = tech_validation.get("controller", {}).get("suitable_controllers", [])
        
        if controllers:
            controller_id = controllers[0].get("id", "UNO-137")
            if "148" in controller_id:
                estimated_price = 1200
            else:
                estimated_price = 800
        else:
            estimated_price = 1000
        
        fallback["pricing"]["final_price"] = estimated_price
        
        return fallback
    
    def _customize_decision_fallback(self, fallback: Dict, input_data: Dict) -> Dict:
        """Customize decision coordinator fallback."""
        action_type = input_data.get("action_type", "unknown")
        
        if action_type == "generate_abq":
            fallback["question"] = {
                "question": "Please choose the best option for your needs:",
                "option_a": {"label": "Option A", "description": "First choice"},
                "option_b": {"label": "Option B", "description": "Second choice"}
            }
        elif action_type == "check_autofill":
            fallback["triggered"] = False
            fallback["message"] = "Autofill unavailable - manual entry required"
        
        return fallback
    
    def clear_cache(self):
        """Clear response cache."""
        self.response_cache.clear()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "cache_size": len(self.response_cache),
            "agents_cached": list(set(key.split("_")[0] for key in self.response_cache.keys()))
        }