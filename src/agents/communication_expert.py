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
            model="gpt-4o",
            blackboard=blackboard,
            message_bus=message_bus
        )
        
        # Initialize OpenAI model
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=0.2,  # Low temperature for consistency
            max_tokens=1500,
            model_kwargs={
                "response_format": {"type": "json_object"}
            }
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
            {"specifications": [{"type": "SR/SSR/CSR", "constraint": "description", "value": "specific value", "strength": 1000, "reasoning": "why this is needed"}], "dependencies": {"io": ["I/O requirements that affect communication"], "system": ["system requirements that affect communication"]}, "confidence": 0.0-1.0, "requires_clarification": ["list of ambiguous requirements"]}"""),
            ("human", "{input}")
        ])
        
    async def process(self, input_data: Dict, context: Dict) -> Dict:
        """
        Process communication requirements with secondary authority.
        """
        print(f"[COMM_EXPERT] Starting process")
        print(f"[COMM_EXPERT] Input keys: {list(input_data.keys())}")
        
        try:
            # Check for I/O dependencies
            dependencies = await self._check_dependencies(context)
            print(f"[COMM_EXPERT] Got dependencies: {dependencies}")
            
            # Format messages
            user_input = input_data.get("user_input", "")
            print(f"[COMM_EXPERT] User input: {user_input[:100]}")
            
            messages = self.prompt.format_messages(input=user_input)
            print(f"[COMM_EXPERT] Formatted {len(messages)} messages")
            
            # Call LLM
            print(f"[COMM_EXPERT] About to call LLM with model: {self.model}")
            response = self.llm.invoke(messages)  # Using invoke, not ainvoke!
            print(f"[COMM_EXPERT] Got LLM response, type: {type(response)}")
            print(f"[COMM_EXPERT] Response content preview: {str(response.content)[:200]}")
            
            # Parse LLM response
            try:
                result = json.loads(response.content)
                print(f"[COMM_EXPERT] Successfully parsed JSON, keys: {list(result.keys())}")
            except json.JSONDecodeError as e:
                print(f"[COMM_EXPERT] JSON decode failed: {e}")
                print(f"[COMM_EXPERT] Raw content: {response.content}")
                # Fallback parsing
                result = self._parse_text_response(response.content)
                print(f"[COMM_EXPERT] Fallback parsing result: {result}")
            
            # Add communication-specific validations
            result = self._validate_communication_requirements(result)
            print(f"[COMM_EXPERT] After validation, result type: {type(result)}")
            
            # Calculate communication-specific confidence
            result["confidence"] = self._calculate_communication_confidence(result)
            
            print(f"[COMM_EXPERT] Process complete, returning {len(result.get('specifications', []))} specs")
            return result
            
        except Exception as e:
            print(f"[COMM_EXPERT] EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # Return safe fallback
            return {
                "specifications": [],
                "confidence": 0.0,
                "error": str(e),
                "agent": "communication_expert"
            }
    
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
        # Handle case where result might be a string
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                return {"specifications": [], "confidence": 0.0, "error": "Invalid JSON response"}
        
        if not isinstance(result, dict):
            return {"specifications": [], "confidence": 0.0, "error": "Invalid result type"}
            
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
