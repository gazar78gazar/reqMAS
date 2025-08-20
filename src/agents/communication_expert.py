"""
Communication Expert Agent Implementation for reqMAS Phase 1
Communication expert with priority 2
"""

from typing import Dict, Any, List
from agents.base_agent import StatelessAgent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json

class CommunicationExpertAgent(StatelessAgent):
    """
    Communication Expert - Secondary domain authority.
    Has priority 2 and focuses on communication protocols and interfaces.
    """
    
    def __init__(self, blackboard, message_bus):
        super().__init__(
            agent_id="communication_expert",
            model="gpt-4o-mini",
            blackboard=blackboard,
            message_bus=message_bus
        )
        
        # Initialize OpenAI model
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=0.2,  # Low temperature for consistency
            max_tokens=1500
        )
        
        # Define prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Communication Protocol Expert for industrial control systems.
            Your responsibility is determining communication requirements and protocols.
            
            Focus on:
            - Communication protocols (Modbus, Ethernet/IP, Profinet, etc.)
            - Network interfaces and ports
            - Communication speeds and latency
            - Data formats and structures
            - Integration requirements
            
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
                "dependencies": {
                    "io": ["I/O requirements that affect communication"],
                    "system": ["system requirements that affect communication"]
                },
                "confidence": 0.0-1.0,
                "requires_clarification": ["list of ambiguous requirements"]
            }"""),
            ("human", "{input}")
        ])
        
    async def process(self, input_data: Dict, context: Dict) -> Dict:
        """
        Process communication requirements with secondary authority.
        """
        # Check for I/O dependencies
        dependencies = await self._check_dependencies(context)
        
        # Extract communication requirements using LLM
        response = await self.llm.ainvoke(
            self.prompt.format_messages(input=input_data.get("user_input", ""))
        )
        
        # Parse LLM response
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback parsing
            result = self._parse_text_response(response.content)
        
        # Add communication-specific validations
        result = self._validate_communication_requirements(result)
        
        # Calculate communication-specific confidence
        result["confidence"] = self._calculate_communication_confidence(result)
        
        return result
    
    def get_tools(self) -> List[str]:
        """Tools available to communication expert."""
        return [
            "requirement_parser",
            "json_query_tool",
            "protocol_compatibility_checker"
        ]
    
    async def _check_dependencies(self, context: Dict) -> Dict:
        """Check dependencies with I/O and system requirements."""
        dependencies = {
            "io_dependent": False,
            "system_dependent": False
        }
        
        # Check if I/O requirements affect communication needs
        requirements = context.get("requirements", {})
        if any(protocol in str(requirements).lower() for protocol in 
               ["modbus", "profinet", "ethernet/ip", "canopen"]):
            dependencies["io_dependent"] = True
        
        # Check for system dependencies
        if "real-time" in str(requirements).lower() or "high-speed" in str(requirements).lower():
            dependencies["system_dependent"] = True
        
        return dependencies
    
    def _validate_communication_requirements(self, result: Dict) -> Dict:
        """Validate communication specifications for consistency."""
        specs = result.get("specifications", [])
        
        # Basic validation for Phase 1
        for spec in specs:
            if "protocol" in spec.get("constraint", "").lower():
                # Ensure protocol specs are valid
                pass  # Phase 1: Basic validation
            
            if "network" in spec.get("constraint", "").lower():
                # Ensure network specifications are valid
                pass  # Phase 1: Basic validation
        
        return result
    
    def _calculate_communication_confidence(self, result: Dict) -> float:
        """Calculate confidence specific to communication requirements."""
        confidence = 0.0
        
        # Check if we have clear communication specifications
        if result.get("specifications"):
            confidence += 0.4
        
        # Check if protocol is specified
        has_protocol = any("protocol" in str(s).lower() or 
                          any(p in str(s).lower() for p in 
                             ["modbus", "profinet", "ethernet/ip", "canopen"])
                          for s in result.get("specifications", []))
        if has_protocol:
            confidence += 0.3
        
        # Check for ambiguities
        if not result.get("requires_clarification"):
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def _parse_text_response(self, text: str) -> Dict:
        """Fallback parser for non-JSON responses."""
        # Phase 1: Basic text parsing
        return {
            "specifications": [],
            "dependencies": {},
            "confidence": 0.3,
            "requires_clarification": ["Could not parse LLM response"]
        }

if __name__ == "__main__":
    print("Communication Expert Agent module loaded successfully!")
    # Note: Testing requires blackboard and message_bus instances
