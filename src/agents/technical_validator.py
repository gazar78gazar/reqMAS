"""
Technical Validator - Validates requirements against actual product constraints
Uses constraints.json and product JSON files for real validation
"""

from typing import Dict, List, Any, Optional
from agents.base_agent import StatelessAgent
from data.data_loader import data_loader
import asyncio

class TechnicalValidator(StatelessAgent):
    """
    Validates technical feasibility using actual product specifications.
    Checks I/O limits, compatibility, and physical constraints.
    """
    
    def __init__(self, blackboard=None, message_bus=None):
        super().__init__(
            agent_id="technical_validator",
            model="gpt-4o-mini",  # Lightweight model for validation
            blackboard=blackboard,
            message_bus=message_bus
        )
        self.constraints = data_loader.constraints
        self.uno_products = data_loader.uno_products if hasattr(data_loader, 'uno_products') else {}
        self.adam_products = data_loader.adam_products if hasattr(data_loader, 'adam_products') else {}
    
    async def process(self, input_data: Dict, context: Dict) -> Dict:
        """
        Validate technical requirements against actual product constraints.
        """
        specifications = input_data.get("specifications", [])
        
        # Extract I/O counts from specifications
        io_requirements = self._extract_io_requirements(specifications)
        
        # Check if I/O requirements extraction failed (exceeded limit)
        if isinstance(io_requirements, dict) and io_requirements.get("valid") is False:
            return {
                "valid": False,
                "confidence": 0.0,
                "error": io_requirements.get("error"),
                "io_requirements": io_requirements,
                "controller": {"valid": False, "message": io_requirements.get("error")},
                "modules": {"valid": False, "message": io_requirements.get("error")},
                "constraints": {"valid": False},
                "conflicts": [{"type": "technical", "message": io_requirements.get("error"), "severity": "high"}],
                "recommendations": []
            }
        
        # Select appropriate controller
        controller_validation = self._validate_controller_selection(io_requirements)
        
        # Check I/O module requirements
        module_validation = self._validate_module_requirements(io_requirements)
        
        # Check constraints from constraints.json
        constraint_validation = self._validate_constraints(specifications)
        
        # Calculate overall validation result
        all_validations = [controller_validation, module_validation, constraint_validation]
        
        return {
            "valid": all(v["valid"] for v in all_validations),
            "confidence": min(v["confidence"] for v in all_validations),
            "controller": controller_validation,
            "modules": module_validation,
            "constraints": constraint_validation,
            "conflicts": self._extract_conflicts(all_validations),
            "recommendations": self._generate_recommendations(io_requirements),
            "io_requirements": io_requirements
        }
    
    def _extract_io_requirements(self, specifications: List[Dict]) -> Dict:
        """Extract I/O counts and other requirements from specifications."""
        io_counts = {
            "analog_input": 0,
            "analog_output": 0,
            "digital_input": 0,
            "digital_output": 0,
            "total_io": 0
        }
        
        for spec in specifications:
            constraint = spec.get("constraint", "")
            value = spec.get("value", 0)
            
            if "analog_input" in constraint or "analog_io" in constraint:
                io_counts["analog_input"] += int(value)
            elif "analog_output" in constraint:
                io_counts["analog_output"] += int(value)
            elif "digital_input" in constraint or "digital_io" in constraint:
                io_counts["digital_input"] += int(value)
            elif "digital_output" in constraint:
                io_counts["digital_output"] += int(value)
            elif "operating_temperature_min" in constraint:
                io_counts["min_operating_temp"] = int(value)
            elif "operating_temperature_max" in constraint:
                io_counts["max_operating_temp"] = int(value)
        
        io_counts["total_io"] = sum(v for k, v in io_counts.items() 
                                   if k in ["analog_input", "analog_output", "digital_input", "digital_output"])
        
        # Check I/O count limit
        if io_counts["total_io"] > 256:
            return {
                "valid": False,
                "error": "I/O count exceeds maximum of 256",
                "total_io": io_counts["total_io"],
                "analog_input": io_counts["analog_input"],
                "analog_output": io_counts["analog_output"],
                "digital_input": io_counts["digital_input"],
                "digital_output": io_counts["digital_output"]
            }
        
        return io_counts
    
    def _validate_controller_selection(self, io_requirements: Dict) -> Dict:
        """Validate if any controller can handle requirements."""
        suitable_controllers = []
        
        for controller_id, specs in self.uno_products.items():
            if self._controller_meets_requirements(specs, io_requirements):
                suitable_controllers.append({
                    "id": controller_id,
                    "capacity": specs.get("builtin_total_digital_io", specs.get("max_io", 0)),
                    "price": specs.get("price", 0)
                })
        
        if not self.uno_products:
            # Fallback if no product data
            if io_requirements["total_io"] <= 16:
                suitable_controllers.append({"id": "UNO-137", "capacity": 16})
            elif io_requirements["total_io"] <= 32:
                suitable_controllers.append({"id": "UNO-148", "capacity": 32})
        
        return {
            "valid": len(suitable_controllers) > 0,
            "confidence": 0.95 if suitable_controllers else 0.0,
            "suitable_controllers": suitable_controllers,
            "message": f"Found {len(suitable_controllers)} suitable controllers"
        }
    
    def _controller_meets_requirements(self, controller_specs: Dict, io_requirements: Dict) -> bool:
        """Check if controller meets I/O and temperature requirements."""
        # Check I/O requirements
        max_io = controller_specs.get("builtin_total_digital_io", controller_specs.get("max_io", 0))
        if io_requirements["total_io"] > max_io:
            return False
        
        # Check temperature requirements if specified
        min_temp_req = io_requirements.get("min_operating_temp")
        max_temp_req = io_requirements.get("max_operating_temp")
        
        if min_temp_req is not None:
            controller_min_temp = controller_specs.get("operating_temp_min_c", 0)
            if controller_min_temp > min_temp_req:
                return False
        
        if max_temp_req is not None:
            controller_max_temp = controller_specs.get("operating_temp_max_c", 85)
            if controller_max_temp < max_temp_req:
                return False
        
        return True
    
    def _validate_module_requirements(self, io_requirements: Dict) -> Dict:
        """Validate I/O module requirements."""
        modules_needed = []
        
        # Calculate ADAM modules needed
        if io_requirements["analog_input"] > 0:
            modules_needed.append({
                "type": "ADAM-4017",
                "quantity": (io_requirements["analog_input"] + 7) // 8,
                "purpose": "8-channel analog input"
            })
        
        if io_requirements["digital_output"] > 0:
            modules_needed.append({
                "type": "ADAM-4050",
                "quantity": (io_requirements["digital_output"] + 15) // 16,
                "purpose": "16-channel digital I/O"
            })
        
        return {
            "valid": True,
            "confidence": 0.9,
            "modules_required": modules_needed,
            "total_modules": sum(m["quantity"] for m in modules_needed)
        }
    
    def _validate_constraints(self, specifications: List[Dict]) -> Dict:
        """Validate against constraints.json rules."""
        violations = []
        
        for spec in specifications:
            constraint_type = spec.get("constraint")
            value = spec.get("value")
            
            # Check against constraint rules
            if constraint_type in self.constraints:
                rule = self.constraints[constraint_type]
                if "max" in rule and int(value) > rule["max"]:
                    violations.append(f"{constraint_type} exceeds max: {rule['max']}")
                if "min" in rule and int(value) < rule["min"]:
                    violations.append(f"{constraint_type} below min: {rule['min']}")
        
        return {
            "valid": len(violations) == 0,
            "confidence": 1.0 if not violations else 0.5,
            "violations": violations
        }
    
    def _extract_conflicts(self, validations: List[Dict]) -> List[Dict]:
        """Extract all conflicts from validations."""
        conflicts = []
        for validation in validations:
            if not validation["valid"]:
                conflicts.append({
                    "type": "technical",
                    "message": validation.get("message", "Validation failed"),
                    "severity": "high" if validation["confidence"] < 0.3 else "medium"
                })
        return conflicts
    
    def _generate_recommendations(self, io_requirements: Dict) -> List[str]:
        """Generate recommendations based on requirements."""
        recommendations = []
        
        if io_requirements["total_io"] > 16:
            recommendations.append("Consider UNO-148 for higher I/O capacity")
        
        if io_requirements["analog_input"] > 8:
            recommendations.append("Multiple ADAM-4017 modules will be required")
        
        return recommendations
    
    def get_tools(self) -> List[str]:
        return ["constraint_checker", "compatibility_validator"]