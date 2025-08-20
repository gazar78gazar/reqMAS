"""
I/O Expert Agent Implementation for reqMAS Phase 1
Primary domain authority with priority 3 and veto power
"""

from typing import Dict, Any, List
from agents.base_agent import StatelessAgent
import json
import re
import os

# Optional LLM imports - gracefully handle if not available
try:
    from langchain_anthropic import ChatAnthropic
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatAnthropic = None
    ChatPromptTemplate = None

class IOExpertAgent(StatelessAgent):
    """
    I/O Configuration Expert - Primary domain authority.
    Has priority 3 and veto power over conflicting constraints.
    """
    
    def __init__(self, blackboard, message_bus):
        super().__init__(
            agent_id="io_expert",
            model="claude-3-opus-20240229",
            blackboard=blackboard,
            message_bus=message_bus
        )
        
        # Initialize Claude model if API key is available
        self.llm = None
        self.prompt = None
        
        try:
            if LANGCHAIN_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
                self.llm = ChatAnthropic(
                    model="claude-3-sonnet-20240229",
                    temperature=0.3,
                    max_tokens=500
                )
                
                # Define prompt template
                self.prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are an I/O Configuration Expert for industrial IoT systems.
                    Your PRIMARY responsibility is determining I/O requirements that drive controller selection.
                    You have VETO POWER over constraints that conflict with I/O requirements.
                    
                    Focus on:
                    - Digital/Analog I/O specifications
                    - Channel counts and types
                    - Expansion requirements
                    - I/O-related communication protocols
                    
                    You must output a JSON with the following structure:
                    {
                        "specifications": [
                            {
                                "type": "SR/SSR/CSR",
                                "constraint": "description",
                                "value": "specific value",
                                "strength": 1000/100/10/1,
                                "reasoning": "why this is needed"
                            }
                        ],
                        "veto_constraints": ["list of non-negotiable I/O requirements"],
                        "dependencies": {
                            "communication": ["required protocols based on I/O"],
                            "performance": ["performance needs based on I/O count"]
                        },
                        "confidence": 0.0-1.0,
                        "requires_clarification": ["list of ambiguous requirements"]
                    }"""),
                    ("human", "{input}")
                ])
        except Exception as e:
            print(f"LLM initialization failed: {e}")
        
        self.coordination_lease = 3000  # 3 second coordination window
        
    async def process(self, input_data: Dict, context: Dict) -> Dict:
        """
        Process I/O requirements with LLM-first, pattern-matching fallback architecture.
        """
        user_input = input_data.get("user_input", "")
        
        # PRIMARY: Try LLM extraction first if available
        if self.llm:
            try:
                llm_result = await self._extract_with_llm(user_input)
                if llm_result.get("confidence", 0) > 0.7:
                    print(f"Using LLM extraction (confidence: {llm_result['confidence']:.2f})")
                    return llm_result
                else:
                    print(f"LLM confidence too low ({llm_result['confidence']:.2f}), falling back")
            except Exception as e:
                print(f"LLM extraction failed: {e}")
        
        # FALLBACK: Use the robust pattern matching system
        fallback_result = self._extract_requirements_fallback(user_input)
        print(f"Using pattern matching fallback: {len(fallback_result.get('specifications', []))} specifications")
        
        return fallback_result
    
    def get_tools(self) -> List[str]:
        """Tools available to I/O expert."""
        return [
            "requirement_parser",
            "json_query_tool",
            "io_compatibility_checker"
        ]
    
    def _check_dependencies(self, context: Dict) -> Dict:
        """Check bidirectional dependencies with Comm and Performance."""
        dependencies = {
            "io_communication": False,
            "io_performance": False
        }
        
        # Check if communication protocols affect I/O selection
        if "modbus" in str(context.get("requirements", "")).lower():
            dependencies["io_communication"] = True
        
        # Check if performance requirements affect I/O
        if "real-time" in str(context.get("requirements", "")).lower():
            dependencies["io_performance"] = True
        
        return dependencies
    
    def _validate_io_requirements(self, result: Dict) -> Dict:
        """Validate I/O specifications for consistency."""
        specs = result.get("specifications", [])
        
        # Check for valid I/O counts
        for spec in specs:
            if "digital" in spec.get("constraint", "").lower():
                # Ensure digital I/O counts are valid (multiples of 8 typically)
                pass  # Phase 1: Basic validation
            
            if "analog" in spec.get("constraint", "").lower():
                # Ensure analog specifications include resolution
                pass  # Phase 1: Basic validation
        
        return result
    
    def _identify_veto_constraints(self, result: Dict) -> List[str]:
        """Identify non-negotiable I/O requirements."""
        veto_list = []
        
        for spec in result.get("specifications", []):
            # High-strength I/O constraints are veto-capable
            if spec.get("strength", 0) >= 1000:
                if any(keyword in spec.get("constraint", "").lower() 
                      for keyword in ["channel", "i/o", "input", "output"]):
                    veto_list.append(spec["constraint"])
        
        return veto_list
    
    def _calculate_io_confidence(self, result: Dict) -> float:
        """Calculate confidence specific to I/O requirements."""
        confidence = 0.0
        
        # Check if we have clear I/O specifications
        if result.get("specifications"):
            confidence += 0.4
        
        # Check if channel counts are specified
        has_counts = any("count" in str(s).lower() or 
                        any(char.isdigit() for char in str(s))
                        for s in result.get("specifications", []))
        if has_counts:
            confidence += 0.3
        
        # Check for ambiguities
        if not result.get("requires_clarification"):
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    async def _extract_with_llm(self, user_input: str) -> Dict:
        """Extract I/O requirements using LLM as primary method."""
        try:
            if not (hasattr(self, 'llm') and self.llm and self.prompt and os.getenv("ANTHROPIC_API_KEY")):
                raise Exception("LLM not available")
            
            # Use the existing LLM setup
            response = await self.llm.ainvoke(
                self.prompt.format_messages(input=user_input)
            )
            
            # Parse LLM response
            try:
                result = json.loads(response.content)
                
                # Validate LLM response structure
                if not isinstance(result, dict) or "specifications" not in result:
                    raise json.JSONDecodeError("Invalid response structure", "", 0)
                
                # Ensure specifications have the right format
                specifications = result.get("specifications", [])
                for spec in specifications:
                    # Ensure required fields exist
                    if not all(key in spec for key in ["type", "constraint", "value", "strength"]):
                        raise ValueError("Missing required specification fields")
                
                # Add I/O-specific validations
                result = self._validate_io_requirements(result)
                
                # Mark veto constraints  
                result["veto_constraints"] = self._identify_veto_constraints(result)
                
                # Calculate I/O-specific confidence
                result["confidence"] = self._calculate_io_confidence(result)
                
                # Add metadata to indicate LLM extraction
                result["extraction_method"] = "llm"
                result["status"] = "success"
                
                print(f"LLM extraction successful: {len(specifications)} specifications")
                return result
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"LLM response parsing failed: {e}")
                raise Exception("LLM response parsing failed")
                
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            # Re-raise to trigger fallback
            raise
    
    def _extract_requirements_fallback(self, user_input: str) -> Dict:
        """Extract I/O requirements using enhanced keyword detection."""
        specifications = []
        detected_keywords = []
        user_input_lower = user_input.lower()
        
        # Extract all numbers from input
        numbers = [int(n) for n in re.findall(r'\b\d+\b', user_input)]
        
        # Define comprehensive keyword categories
        sensor_keywords = {
            "temperature": ["temperature", "temp", "thermal", "thermocouple", "rtd", "pt100"],
            "pressure": ["pressure", "psi", "bar", "pascal", "manometer"],
            "flow": ["flow", "flowmeter", "gpm", "lpm", "cfm"],
            "level": ["level", "tank level", "fluid level", "depth"],
            "humidity": ["humidity", "moisture", "rh%"],
            "ph": ["ph", "acidity", "alkalinity"]
        }
        
        # Communication port keywords (NOT I/O - should route to other experts)
        comm_keywords = {
            "usb": ["usb", "usb 3.0", "usb3", "usb-c"],
            "ethernet": ["rj45", "ethernet", "network", "lan"],
            "serial": ["rs485", "rs232", "combus", "modbus", "profibus", "serial"],
            "wifi": ["wifi", "wireless", "bluetooth", "zigbee"]
        }
        
        # Physical monitoring keywords
        container_keywords = ["tank", "tanks", "vessel", "vessels", "container", "containers", "reactor", "reactors"]
        
        # Detect sensor types and quantities
        sensor_specs = self._detect_sensor_requirements(user_input_lower, numbers, sensor_keywords, container_keywords)
        specifications.extend(sensor_specs)
        
        # Detect communication requirements and CREATE specifications
        comm_specs, comm_detected = self._detect_communication_requirements(user_input_lower, comm_keywords)
        specifications.extend(comm_specs)
        
        # Traditional I/O detection (for explicit I/O mentions)
        io_specs = self._detect_traditional_io(user_input_lower, numbers)
        specifications.extend(io_specs)
        
        # Calculate total analog inputs needed and add aggregate specification
        analog_inputs_needed = sum(int(spec["value"]) for spec in specifications if "input" in spec["constraint"] and "monitoring" in spec["constraint"])
        if analog_inputs_needed > 0 and not any(spec["constraint"] == "Analog input count" for spec in specifications):
            specifications.append({
                "type": "SR",
                "constraint": "Analog input count",
                "value": str(analog_inputs_needed),
                "strength": 1000,
                "reasoning": f"Total of {analog_inputs_needed} analog inputs required for sensor monitoring"
            })
        
        # Collect all detected keywords
        detected_keywords = self._collect_detected_keywords(user_input_lower, sensor_keywords, comm_keywords)
        
        # Build veto constraints (non-negotiable I/O requirements)
        veto_constraints = [spec["constraint"] for spec in specifications if spec["strength"] >= 1000]
        
        # Determine if this should route to other experts
        routing_suggestions = []
        if comm_detected["has_communication"]:
            routing_suggestions.append("communication_expert")
        if comm_detected["has_system_ports"]:
            routing_suggestions.append("system_expert")
        
        return {
            "specifications": specifications,
            "confidence": min(len(detected_keywords) * 0.15 + len(specifications) * 0.2, 1.0),
            "status": "success",
            "extraction_method": "pattern_matching",
            "detected_keywords": detected_keywords,
            "veto_constraints": veto_constraints,
            "routing_suggestions": routing_suggestions,
            "communication_detected": comm_detected,
            "dependencies": {
                "communication": comm_detected["protocols"],
                "performance": ["Real-time monitoring"] if any("monitor" in kw for kw in detected_keywords) else []
            },
            "requires_clarification": [] if specifications else self._generate_clarification_requests(user_input_lower)
        }
    
    def _detect_sensor_requirements(self, user_input: str, numbers: list, sensor_keywords: dict, container_keywords: list) -> list:
        """Detect sensor requirements with multiplication for containers."""
        specifications = []
        
        # Find container count (tanks, vessels, etc.)
        container_count = 1
        for keyword in container_keywords:
            if keyword in user_input:
                # Look for numbers before the container keyword
                pattern = rf'(\d+)\s+{keyword}'
                matches = re.findall(pattern, user_input)
                if matches:
                    container_count = int(matches[0])
                    break
        
        # Detect each sensor type
        for sensor_type, keywords in sensor_keywords.items():
            for keyword in keywords:
                if keyword in user_input:
                    # Calculate total sensors needed
                    sensors_per_container = 1
                    if sensor_type in ["temperature", "pressure", "flow", "level"] and "monitor" in user_input:
                        # Monitoring implies continuous measurement
                        total_sensors = container_count * sensors_per_container
                        
                        specifications.append({
                            "type": "SR",
                            "constraint": f"{sensor_type.title()} monitoring inputs",
                            "value": str(total_sensors),
                            "strength": 900,
                            "reasoning": f"Detected {sensor_type} monitoring for {container_count} container(s), requiring {total_sensors} analog input(s)"
                        })
                        
                        # Track analog inputs separately to avoid adding at every sensor detection
                        pass
                    break
        
        return specifications
    
    def _detect_communication_requirements(self, user_input: str, comm_keywords: dict) -> tuple:
        """Detect communication requirements and CREATE specifications."""
        specifications = []
        detected_protocols = []
        has_system_ports = False
        has_communication = False
        processed_ranges = []  # Track processed ranges to avoid duplicates
        
        # Text number mapping
        text_numbers = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        # Communication port patterns with quantity extraction
        comm_patterns = [
            # USB patterns (most specific first)
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*usb\s*3\.?0?\s*ports?', 'usb_3_ports', 'USB 3.0 port', 'usb'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*usb-c\s*ports?', 'usb_c_ports', 'USB-C port', 'usb'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*usb\s*ports?', 'usb_ports', 'USB port', 'usb'),
            
            # Ethernet patterns
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*rj45\s*ports?', 'rj45_ports', 'RJ45 port', 'ethernet'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*ethernet\s*ports?', 'ethernet_ports', 'Ethernet port', 'ethernet'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*network\s*ports?', 'network_ports', 'Network port', 'ethernet'),
            
            # Serial patterns - more flexible matching
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*rs485(?:\s+port)?(?:\s+communication)?', 'rs485_ports', 'RS485 port', 'serial'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*rs232(?:\s+port)?(?:\s+communication)?', 'rs232_ports', 'RS232 port', 'serial'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*modbus(?:\s+port)?(?:\s+communication)?', 'modbus_ports', 'Modbus port', 'serial'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*combus(?:\s+port)?(?:\s+communication)?', 'combus_ports', 'Combus port', 'serial'),
            
            # Wireless patterns
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*wifi\s*modules?', 'wifi_module', 'WiFi module', 'wifi'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*bluetooth\s*modules?', 'bluetooth_module', 'Bluetooth module', 'wifi'),
        ]
        
        # Look for communication patterns and create specifications
        for pattern, constraint, description, category in comm_patterns:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                # Check if this range overlaps with already processed ranges
                start, end = match.span()
                if any(start < proc_end and end > proc_start for proc_start, proc_end in processed_ranges):
                    continue  # Skip overlapping matches
                
                has_communication = True
                
                # Extract quantity from regex groups or text numbers
                quantity = 1
                for group in match.groups():
                    if group:
                        if group.isdigit():
                            quantity = int(group)
                            break
                        elif group.lower() in text_numbers:
                            quantity = text_numbers[group.lower()]
                            break
                
                # Create specification
                strength = 100  # Lower strength than I/O since these are system requirements
                if category == "usb":
                    has_system_ports = True
                    strength = 200  # System ports have higher priority than other communication
                
                specifications.append({
                    "type": "SR",
                    "constraint": constraint,
                    "value": str(quantity),
                    "strength": strength,
                    "reasoning": f"Detected {description} requirement (quantity: {quantity})"
                })
                
                # Mark this range as processed
                processed_ranges.append((start, end))
                
                # Track protocols for routing
                if category == "usb":
                    detected_protocols.append("USB connectivity")
                elif category == "ethernet":
                    detected_protocols.append("Ethernet/IP")
                elif category == "serial":
                    detected_protocols.append(constraint.upper())
                elif category == "wifi":
                    detected_protocols.append("Wireless connectivity")
        
        detection_info = {
            "has_communication": has_communication,
            "has_system_ports": has_system_ports,
            "protocols": detected_protocols
        }
        
        return specifications, detection_info
    
    def _detect_traditional_io(self, user_input: str, numbers: list) -> list:
        """Detect traditional I/O requirements and CREATE specifications."""
        specifications = []
        processed_ranges = []  # Track processed text ranges to avoid duplicates
        
        # Text number mapping
        text_numbers = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        # Specific I/O patterns with quantity extraction (most specific first to avoid overlaps)
        io_patterns = [
            # Most specific patterns first (digital outputs for relays)
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*digital\s+(outputs?|outs?)\s+for\s+(relays?|relay)', 'digital_output', 'Digital output'),
            
            # Analog patterns
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*analog\s+(inputs?|ins?)', 'analog_input', 'Analog input'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*analog\s+(outputs?|outs?)', 'analog_output', 'Analog output'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*4-20\s*ma', 'analog_input', '4-20mA input'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*0-10\s*v', 'analog_input', '0-10V input'),
            
            # Digital patterns (general)
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*digital\s+(inputs?|ins?)', 'digital_input', 'Digital input'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*digital\s+(outputs?|outs?)', 'digital_output', 'Digital output'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*digital\s+i/?o', 'digital_io', 'Digital I/O'),
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*i/?o\s+points?', 'digital_io', 'Digital I/O points'),
            
            # Traditional terms (only if not already covered)
            (r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten)?\s*(switches?)', 'digital_input', 'Switch input'),
        ]
        
        for pattern, constraint, description in io_patterns:
            matches = re.finditer(pattern, user_input, re.IGNORECASE)
            for match in matches:
                # Check if this range overlaps with already processed ranges
                start, end = match.span()
                if any(start < proc_end and end > proc_start for proc_start, proc_end in processed_ranges):
                    continue  # Skip overlapping matches
                
                # Extract quantity from regex groups or text numbers
                quantity = 1
                for group in match.groups():
                    if group:
                        if group.isdigit():
                            quantity = int(group)
                            break
                        elif group.lower() in text_numbers:
                            quantity = text_numbers[group.lower()]
                            break
                
                specifications.append({
                    "type": "SR",
                    "constraint": constraint,
                    "value": str(quantity),
                    "strength": 1000,
                    "reasoning": f"Detected {description} requirement (quantity: {quantity})"
                })
                
                # Mark this range as processed
                processed_ranges.append((start, end))
        
        return specifications
    
    def _collect_detected_keywords(self, user_input: str, sensor_keywords: dict, comm_keywords: dict) -> list:
        """Collect all detected keywords for confidence calculation."""
        detected = []
        
        # Add sensor keywords
        for category, keywords in sensor_keywords.items():
            for keyword in keywords:
                if keyword in user_input:
                    detected.append(keyword)
        
        # Add communication keywords
        for category, keywords in comm_keywords.items():
            for keyword in keywords:
                if keyword in user_input:
                    detected.append(keyword)
        
        # Add general I/O terms
        general_terms = ["monitor", "control", "sensor", "input", "output", "i/o", "io"]
        for term in general_terms:
            if term in user_input:
                detected.append(term)
        
        return list(set(detected))  # Remove duplicates
    
    def _generate_clarification_requests(self, user_input: str) -> list:
        """Generate specific clarification requests based on ambiguous input."""
        clarifications = []
        
        # Check for non-English text
        english_words = ["the", "and", "or", "with", "for", "in", "on", "at", "to", "is", "are", "have", "need", "want"]
        if not any(word in user_input for word in english_words) and len(user_input) > 10:
            clarifications.append("Please provide technical specifications in English for better analysis")
        
        # Check for vague requirements  
        if len(user_input.split()) < 3:
            clarifications.append("Please provide more detailed requirements")
        
        if not clarifications:
            clarifications.append("No clear I/O requirements detected. Please specify sensors, controls, or monitoring needs.")
        
        return clarifications

if __name__ == "__main__":
    print("I/O Expert Agent module loaded successfully!")
    # Note: Testing requires blackboard and message_bus instances
