"""
Compatibility Checker Tool for reqMAS Phase 1
Validates compatibility between different requirement constraints
"""

from typing import Dict, List, Any, Tuple, Set
import json
import os

class CompatibilityChecker:
    """
    Validates compatibility between different requirement constraints.
    Checks for conflicts and dependencies between requirements.
    """
    
    def __init__(self, rules_file: str = None):
        """
        Initialize with optional rules file path.
        If not provided, will use default rules.
        """
        self.rules = {}
        
        if rules_file:
            self._load_rules(rules_file)
        else:
            self._load_default_rules()
    
    def _load_rules(self, rules_file: str):
        """Load compatibility rules from file."""
        try:
            with open(rules_file, 'r') as f:
                self.rules = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Error loading rules from {rules_file}, using defaults")
            self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default compatibility rules."""
        self.rules = {
            "io": {
                "digital_io": {
                    "min": 0,
                    "max": 64,
                    "conflicts": [],
                    "dependencies": []
                },
                "analog_io": {
                    "min": 0,
                    "max": 32,
                    "conflicts": [],
                    "dependencies": []
                }
            },
            "communication": {
                "protocols": {
                    "modbus_rtu": {
                        "conflicts": ["profinet", "ethernet_ip"],
                        "dependencies": ["rs485"]
                    },
                    "modbus_tcp": {
                        "conflicts": [],
                        "dependencies": ["ethernet"]
                    },
                    "profinet": {
                        "conflicts": ["modbus_rtu"],
                        "dependencies": ["ethernet"]
                    },
                    "ethernet_ip": {
                        "conflicts": ["modbus_rtu"],
                        "dependencies": ["ethernet"]
                    }
                },
                "interfaces": {
                    "rs485": {
                        "conflicts": [],
                        "dependencies": []
                    },
                    "ethernet": {
                        "conflicts": [],
                        "dependencies": []
                    },
                    "usb": {
                        "conflicts": [],
                        "dependencies": []
                    }
                }
            },
            "system": {
                "cpu": {
                    "min": 100,  # MHz
                    "max": 5000,  # MHz
                    "conflicts": [],
                    "dependencies": []
                },
                "memory": {
                    "min": 1,  # MB
                    "max": 16384,  # MB
                    "conflicts": [],
                    "dependencies": []
                },
                "real_time": {
                    "conflicts": [],
                    "dependencies": ["cpu.min:500"]
                }
            }
        }
    
    def check_compatibility(self, requirements: List[Dict]) -> Dict:
        """
        Check compatibility between requirements.
        Returns a dictionary with conflicts and dependencies.
        """
        result = {
            "conflicts": [],
            "missing_dependencies": [],
            "valid": True
        }
        
        # Extract normalized constraints
        constraints = self._normalize_constraints(requirements)
        
        # Check for conflicts
        conflicts = self._check_conflicts(constraints)
        if conflicts:
            result["conflicts"] = conflicts
            result["valid"] = False
        
        # Check for missing dependencies
        missing = self._check_dependencies(constraints)
        if missing:
            result["missing_dependencies"] = missing
            result["valid"] = False
        
        return result
    
    def _normalize_constraints(self, requirements: List[Dict]) -> Dict:
        """
        Normalize requirements to constraints format.
        Maps requirements to internal constraint representation.
        """
        constraints = {}
        
        for req in requirements:
            constraint = req.get("constraint", "").lower()
            value = req.get("value", "")
            
            # Extract I/O constraints
            if "digital" in constraint and "i/o" in constraint or "io" in constraint:
                constraints["io.digital_io"] = self._parse_numeric_value(value)
            
            elif "analog" in constraint and "i/o" in constraint or "io" in constraint:
                constraints["io.analog_io"] = self._parse_numeric_value(value)
            
            # Extract communication constraints
            elif "modbus rtu" in constraint:
                constraints["communication.protocols.modbus_rtu"] = True
            
            elif "modbus tcp" in constraint:
                constraints["communication.protocols.modbus_tcp"] = True
            
            elif "profinet" in constraint:
                constraints["communication.protocols.profinet"] = True
            
            elif "ethernet/ip" in constraint or "ethernet ip" in constraint:
                constraints["communication.protocols.ethernet_ip"] = True
            
            elif "rs485" in constraint or "rs-485" in constraint:
                constraints["communication.interfaces.rs485"] = True
            
            elif "ethernet" in constraint:
                constraints["communication.interfaces.ethernet"] = True
            
            elif "usb" in constraint:
                constraints["communication.interfaces.usb"] = True
            
            # Extract system constraints
            elif "cpu" in constraint or "processor" in constraint:
                constraints["system.cpu"] = self._parse_numeric_value(value)
            
            elif "memory" in constraint or "ram" in constraint:
                constraints["system.memory"] = self._parse_numeric_value(value)
            
            elif "real-time" in constraint or "realtime" in constraint:
                constraints["system.real_time"] = True
        
        return constraints
    
    def _parse_numeric_value(self, value: str) -> int:
        """Parse numeric value from string."""
        try:
            # Extract digits
            import re
            digits = re.search(r'\d+', str(value))
            if digits:
                return int(digits.group())
            return 0
        except (ValueError, TypeError):
            return 0
    
    def _check_conflicts(self, constraints: Dict) -> List[Dict]:
        """Check for conflicts between constraints."""
        conflicts = []
        
        # Check each constraint against rules
        for path, value in constraints.items():
            parts = path.split('.')
            
            # Skip if less than 2 parts (category.item)
            if len(parts) < 2:
                continue
            
            category, item = parts[0], '.'.join(parts[1:])
            
            # Check numeric ranges
            if isinstance(value, (int, float)):
                if category in self.rules and item in self.rules[category]:
                    min_val = self.rules[category][item].get("min")
                    max_val = self.rules[category][item].get("max")
                    
                    if min_val is not None and value < min_val:
                        conflicts.append({
                            "constraint": path,
                            "value": value,
                            "reason": f"Value below minimum ({min_val})"
                        })
                    
                    if max_val is not None and value > max_val:
                        conflicts.append({
                            "constraint": path,
                            "value": value,
                            "reason": f"Value above maximum ({max_val})"
                        })
            
            # Check protocol conflicts
            if len(parts) >= 3 and parts[0] == "communication" and parts[1] == "protocols":
                protocol = parts[2]
                if protocol in self.rules["communication"]["protocols"]:
                    conflict_list = self.rules["communication"]["protocols"][protocol].get("conflicts", [])
                    
                    for conflict in conflict_list:
                        conflict_path = f"communication.protocols.{conflict}"
                        if conflict_path in constraints and constraints[conflict_path]:
                            conflicts.append({
                                "constraint": path,
                                "conflicting_constraint": conflict_path,
                                "reason": f"Protocol {protocol} conflicts with {conflict}"
                            })
        
        return conflicts
    
    def _check_dependencies(self, constraints: Dict) -> List[Dict]:
        """Check for missing dependencies."""
        missing = []
        
        # Check each constraint against rules
        for path, value in constraints.items():
            parts = path.split('.')
            
            # Skip if less than 2 parts (category.item)
            if len(parts) < 2:
                continue
            
            category, item = parts[0], '.'.join(parts[1:])
            
            # Check protocol dependencies
            if len(parts) >= 3 and parts[0] == "communication" and parts[1] == "protocols":
                protocol = parts[2]
                if protocol in self.rules["communication"]["protocols"]:
                    dep_list = self.rules["communication"]["protocols"][protocol].get("dependencies", [])
                    
                    for dep in dep_list:
                        dep_path = f"communication.interfaces.{dep}"
                        if dep_path not in constraints or not constraints[dep_path]:
                            missing.append({
                                "constraint": path,
                                "missing_dependency": dep_path,
                                "reason": f"Protocol {protocol} requires {dep}"
                            })
            
            # Check system dependencies
            if path == "system.real_time" and value:
                for dep in self.rules["system"]["real_time"].get("dependencies", []):
                    if ":" in dep:
                        dep_path, dep_value = dep.split(":")
                        if dep_path not in constraints or constraints[dep_path] < int(dep_value):
                            missing.append({
                                "constraint": path,
                                "missing_dependency": dep_path,
                                "reason": f"Real-time requires {dep_path} >= {dep_value}"
                            })
        
        return missing

if __name__ == "__main__":
    # Test the compatibility checker
    checker = CompatibilityChecker()
    
    # Example requirements
    test_requirements = [
        {
            "constraint": "Digital I/O count",
            "value": "16",
            "type": "SR"
        },
        {
            "constraint": "The system must support Modbus RTU protocol",
            "value": "Modbus RTU",
            "type": "SR"
        },
        {
            "constraint": "CPU speed",
            "value": "1.5 GHz",
            "type": "SR"
        }
    ]
    
    # Check compatibility
    result = checker.check_compatibility(test_requirements)
    print(json.dumps(result, indent=2))
