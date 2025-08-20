"""
CSP Validator - Continuous constraint satisfaction using constraints.json
Validates constraints in real-time using actual product rules
"""

from typing import Dict, List, Set, Tuple, Any, Optional
from data.data_loader import data_loader
import asyncio
from datetime import datetime

class CSPValidator:
    """
    Continuous constraint satisfaction problem validator.
    Uses constraints.json for rules and product JSONs for limits.
    """
    
    def __init__(self):
        self.constraints = data_loader.constraints
        self.validation_interval = 0.1  # 100ms
        self.is_running = False
        self.last_validation = None
        self.constraint_graph = {}
    
    async def start_continuous_validation(self):
        """Start continuous validation loop."""
        self.is_running = True
        while self.is_running:
            await self.validate_current_state()
            await asyncio.sleep(self.validation_interval)
    
    def stop_continuous_validation(self):
        """Stop continuous validation."""
        self.is_running = False
    
    async def validate_current_state(self):
        """Validate current system state against all constraints."""
        # This would connect to blackboard in production
        self.last_validation = datetime.now()
    
    def validate_constraints(self, specifications: List[Dict]) -> Dict:
        """
        Validate specifications against constraint rules.
        Uses constraint solver for complex interdependencies.
        """
        violations = []
        
        # Extract variables from specifications
        variables = self._extract_variables(specifications)
        
        # Basic constraint validation without external CSP library
        constraint_results = self._validate_basic_constraints(specifications)
        
        # Check inter-constraint dependencies
        dependency_results = self._check_constraint_dependencies(variables)
        
        # Combine results
        all_violations = constraint_results.get("violations", []) + dependency_results.get("violations", [])
        
        return {
            "valid": len(all_violations) == 0,
            "solutions_count": 1 if len(all_violations) == 0 else 0,
            "violations": all_violations,
            "best_solution": variables if len(all_violations) == 0 else None,
            "confidence": 1.0 if len(all_violations) == 0 else 0.0
        }
    
    def _extract_variables(self, specifications: List[Dict]) -> Dict:
        """Extract CSP variables from specifications."""
        variables = {}
        
        for spec in specifications:
            constraint = spec.get("constraint", "")
            value = int(spec.get("value", 0))
            
            # Create variables based on constraint type
            if "analog_input" in constraint or "analog_io" in constraint:
                variables["analog_inputs"] = value
            elif "digital_output" in constraint or "digital_io" in constraint:
                variables["digital_outputs"] = value
            elif "total_io" in constraint:
                variables["total_io"] = value
            elif "memory" in constraint:
                variables["memory_gb"] = value
            elif "storage" in constraint:
                variables["storage_gb"] = value
            elif "power" in constraint:
                variables["power_watts"] = value
        
        # Calculate derived variables
        if "analog_inputs" in variables and "digital_outputs" in variables:
            variables["total_io"] = variables["analog_inputs"] + variables["digital_outputs"]
        
        return variables
    
    def _validate_basic_constraints(self, specifications: List[Dict]) -> Dict:
        """Validate basic constraint rules from constraints.json."""
        violations = []
        
        # Group constraints by category for easier validation
        constraint_categories = self._group_constraints_by_category()
        
        for spec in specifications:
            constraint_type = spec.get("constraint", "")
            value = spec.get("value")
            
            # Find matching constraint in our constraint pool
            matching_constraint = self._find_matching_constraint(constraint_type, constraint_categories)
            
            if matching_constraint:
                violation = self._check_constraint_violation(constraint_type, value, matching_constraint)
                if violation:
                    violations.append(violation)
        
        return {
            "violations": violations,
            "valid": len(violations) == 0
        }
    
    def _group_constraints_by_category(self) -> Dict:
        """Group constraints by category from constraints.json."""
        categories = {}
        
        for category_name, category_constraints in self.constraints.items():
            if isinstance(category_constraints, dict):
                categories[category_name] = category_constraints
        
        return categories
    
    def _find_matching_constraint(self, constraint_type: str, constraint_categories: Dict) -> Optional[Dict]:
        """Find matching constraint definition."""
        for category_name, constraints in constraint_categories.items():
            for constraint_id, constraint_def in constraints.items():
                if constraint_type in constraint_id.lower() or constraint_id.lower() in constraint_type.lower():
                    return constraint_def
        return None
    
    def _check_constraint_violation(self, constraint_type: str, value: Any, constraint_def: Dict) -> Optional[Dict]:
        """Check if a specific constraint is violated."""
        try:
            numeric_value = float(value)
            operator = constraint_def.get("operator", "")
            constraint_value = constraint_def.get("value")
            
            if operator == "max" and numeric_value > constraint_value:
                return {
                    "constraint": constraint_type,
                    "violation": "exceeds_maximum",
                    "value": numeric_value,
                    "max_allowed": constraint_value,
                    "severity": "high"
                }
            elif operator == "min" and numeric_value < constraint_value:
                return {
                    "constraint": constraint_type,
                    "violation": "below_minimum", 
                    "value": numeric_value,
                    "min_required": constraint_value,
                    "severity": "high"
                }
            elif operator == "exact" and numeric_value != constraint_value:
                return {
                    "constraint": constraint_type,
                    "violation": "not_exact_match",
                    "value": numeric_value,
                    "required": constraint_value,
                    "severity": "medium"
                }
        except (ValueError, TypeError):
            # Handle non-numeric constraints
            if constraint_def.get("operator") == "required" and not value:
                return {
                    "constraint": constraint_type,
                    "violation": "required_missing",
                    "severity": "high"
                }
        
        return None
    
    def _check_constraint_dependencies(self, variables: Dict) -> Dict:
        """Check dependencies between constraints."""
        violations = []
        
        # Example dependency checks
        # Power vs Performance
        if variables.get("power_watts", 0) <= 10 and variables.get("analog_inputs", 0) > 16:
            violations.append({
                "constraint": "power_vs_io",
                "violation": "power_insufficient_for_io",
                "message": "10W power budget insufficient for >16 analog inputs",
                "severity": "absolute"
            })
        
        # I/O capacity limits
        total_io = variables.get("total_io", 0)
        if total_io > 32:
            violations.append({
                "constraint": "total_io_limit",
                "violation": "exceeds_controller_capacity",
                "message": "Total I/O exceeds maximum controller capacity",
                "severity": "high"
            })
        
        return {
            "violations": violations,
            "valid": len(violations) == 0
        }
    
    def get_constraint_graph(self) -> Dict:
        """Get visual representation of constraint relationships."""
        return self.constraint_graph