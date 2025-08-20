"""
Requirement Parser Tool for reqMAS Phase 1
NL to constraint mapping utility
"""

from typing import Dict, List, Any, Optional, Tuple
import re
import json

class RequirementParser:
    """
    Parser for natural language requirements to structured constraints.
    Maps NL statements to formal requirement specifications.
    """
    
    def __init__(self):
        # Requirement type patterns
        self.type_patterns = {
            "SR": [  # System Requirements
                r"system\s+must",
                r"performance\s+requirement",
                r"shall\s+be\s+capable",
                r"processor|memory|cpu"
            ],
            "SSR": [  # Subsystem Requirements
                r"subsystem\s+must",
                r"module\s+shall",
                r"component\s+requirement"
            ],
            "CSR": [  # Component-Specific Requirements
                r"component\s+must",
                r"specific\s+requirement",
                r"individual\s+module"
            ]
        }
        
        # I/O related patterns
        self.io_patterns = [
            r"(\d+)\s*(?:digital|analog|input|output|I\/O|IO)\s*(?:points|channels)",
            r"(?:digital|analog|input|output|I\/O|IO)\s*(?:points|channels).*?(\d+)",
            r"(\d+)[-\s]point\s*(?:digital|analog|input|output|I\/O|IO)"
        ]
        
        # Communication patterns
        self.comm_patterns = [
            r"(modbus|profinet|ethernet\/ip|canopen|devicenet|profibus)",
            r"(serial|ethernet|usb|rs-?232|rs-?485)\s*(?:interface|connection|port)",
            r"(communication|protocol)\s*(?:speed|rate)\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*(kbps|mbps|gbps)"
        ]
        
        # System patterns
        self.system_patterns = [
            r"(cpu|processor).*?(\d+(?:\.\d+)?)\s*(mhz|ghz)",
            r"(memory|ram).*?(\d+(?:\.\d+)?)\s*(kb|mb|gb)",
            r"(real-time|realtime)",
            r"(response time).*?(\d+(?:\.\d+)?)\s*(ms|s)"
        ]
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse natural language text into structured requirements.
        Returns a dictionary with categorized requirements.
        """
        result = {
            "io_requirements": [],
            "system_requirements": [],
            "communication_requirements": [],
            "uncategorized": [],
            "confidence": 0.0
        }
        
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        # Process each sentence
        for sentence in sentences:
            req_type = self._determine_requirement_type(sentence)
            category, requirement = self._extract_requirement(sentence, req_type)
            
            if category == "io":
                result["io_requirements"].append(requirement)
            elif category == "system":
                result["system_requirements"].append(requirement)
            elif category == "communication":
                result["communication_requirements"].append(requirement)
            else:
                result["uncategorized"].append({
                    "text": sentence,
                    "possible_type": req_type
                })
        
        # Calculate confidence
        result["confidence"] = self._calculate_confidence(result)
        
        return result
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Basic sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _determine_requirement_type(self, sentence: str) -> str:
        """Determine requirement type (SR, SSR, CSR)."""
        for req_type, patterns in self.type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    return req_type
        
        # Default to SR if no match
        return "SR"
    
    def _extract_requirement(self, sentence: str, req_type: str) -> Tuple[str, Dict]:
        """Extract structured requirement from sentence."""
        # Check for I/O requirements
        for pattern in self.io_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return "io", {
                    "type": req_type,
                    "constraint": sentence,
                    "value": match.group(1) if len(match.groups()) >= 1 else "unspecified",
                    "strength": 100,
                    "category": "io"
                }
        
        # Check for communication requirements
        for pattern in self.comm_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return "communication", {
                    "type": req_type,
                    "constraint": sentence,
                    "value": match.group(1) if len(match.groups()) >= 1 else "unspecified",
                    "strength": 100,
                    "category": "communication"
                }
        
        # Check for system requirements
        for pattern in self.system_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return "system", {
                    "type": req_type,
                    "constraint": sentence,
                    "value": match.group(1) if len(match.groups()) >= 1 else "unspecified",
                    "strength": 100,
                    "category": "system"
                }
        
        # Uncategorized
        return "uncategorized", {
            "type": req_type,
            "constraint": sentence,
            "value": "unspecified",
            "strength": 10,
            "category": "uncategorized"
        }
    
    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate confidence in parsing results."""
        total_requirements = (
            len(result["io_requirements"]) +
            len(result["system_requirements"]) +
            len(result["communication_requirements"]) +
            len(result["uncategorized"])
        )
        
        if total_requirements == 0:
            return 0.0
        
        categorized = (
            len(result["io_requirements"]) +
            len(result["system_requirements"]) +
            len(result["communication_requirements"])
        )
        
        return min(categorized / total_requirements, 1.0)
    
    def extract_constraints(self, text: str) -> List[Dict]:
        """
        Extract constraints from text as a flat list.
        Useful for direct constraint extraction.
        """
        parsed = self.parse(text)
        
        constraints = []
        constraints.extend(parsed["io_requirements"])
        constraints.extend(parsed["system_requirements"])
        constraints.extend(parsed["communication_requirements"])
        
        return constraints

if __name__ == "__main__":
    parser = RequirementParser()
    
    # Test parsing
    test_text = """
    The system must have at least 16 digital I/O points.
    It should support Modbus RTU protocol for communication.
    The processor should run at 1.5 GHz minimum with 4GB RAM.
    Response time must be under 10ms for critical operations.
    """
    
    result = parser.parse(test_text)
    print(json.dumps(result, indent=2))
    
    # Test constraint extraction
    constraints = parser.extract_constraints(test_text)
    print("\nExtracted constraints:")
    print(json.dumps(constraints, indent=2))
