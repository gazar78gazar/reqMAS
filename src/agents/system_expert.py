"""
System Expert Agent Implementation for reqMAS Phase 1
System/performance expert with priority 2
"""

from typing import Dict, Any, List
from agents.base_agent import StatelessAgent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json

class SystemExpertAgent(StatelessAgent):
    """
    System/Performance Expert - Secondary domain authority.
    Has priority 2 and focuses on system requirements.
    """
    
    def __init__(self, blackboard, message_bus):
        super().__init__(
            agent_id="system_expert",
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
            ("system", """You are a System and Performance Expert for industrial control systems.
            Your responsibility is determining system requirements like CPU, memory, and performance needs.
            
            Focus on:
            - CPU/processor requirements
            - Memory specifications
            - Performance characteristics
            - Real-time capabilities
            - System redundancy
            
            You must output a JSON with the following structure:
            {"specifications": [{"type": "SR/SSR/CSR", "constraint": "description", "value": "specific value", "strength": 1000, "reasoning": "why this is needed"}], "dependencies": {"io": ["I/O requirements that affect system needs"], "communication": ["communication requirements that affect system needs"]}, "confidence": 0.0-1.0, "requires_clarification": ["list of ambiguous requirements"]}"""),
            ("human", "{input}")
        ])
        
    async def process(self, input_data: Dict, context: Dict) -> Dict:
        """
        Process system requirements with secondary authority.
        """
        # Check for I/O dependencies
        io_dependencies = await self._check_io_dependencies(context)
        
        # Extract system requirements using LLM
        # Format messages and invoke synchronously
        messages = self.prompt.format_messages(input=input_data.get("user_input", ""))
        response = self.llm.invoke(messages)
        
        # Parse LLM response
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback parsing
            result = self._parse_text_response(response.content)
        
        # Add system-specific validations
        result = self._validate_system_requirements(result)
        
        # Calculate system-specific confidence
        result["confidence"] = self._calculate_system_confidence(result)
        
        return result
    
    def get_tools(self) -> List[str]:
        """Tools available to system expert."""
        return [
            "requirement_parser",
            "json_query_tool",
            "system_compatibility_checker"
        ]
    
    async def _check_io_dependencies(self, context: Dict) -> Dict:
        """Check dependencies with I/O requirements."""
        dependencies = {
            "high_speed_io": False,
            "real_time": False
        }
        
        # Check if I/O requirements affect system needs
        requirements = context.get("requirements", {})
        if "real-time" in str(requirements).lower():
            dependencies["real_time"] = True
        
        # Check for high-speed I/O
        if "high-speed" in str(requirements).lower() or "high speed" in str(requirements).lower():
            dependencies["high_speed_io"] = True
        
        return dependencies
    
    def _validate_system_requirements(self, result: Dict) -> Dict:
        """Validate system specifications for consistency."""
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
            if "cpu" in spec.get("constraint", "").lower():
                # Ensure CPU specs are valid
                pass  # Phase 1: Basic validation
            
            if "memory" in spec.get("constraint", "").lower():
                # Ensure memory specifications are valid
                pass  # Phase 1: Basic validation
        
        return result
    
    def _calculate_system_confidence(self, result: Dict) -> float:
        """Calculate confidence specific to system requirements."""
        confidence = 0.0
        
        # Check if we have clear system specifications
        if result.get("specifications"):
            confidence += 0.4
        
        # Check if performance characteristics are specified
        has_performance = any("performance" in str(s).lower() or 
                             "speed" in str(s).lower() or
                             "real-time" in str(s).lower()
                             for s in result.get("specifications", []))
        if has_performance:
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
    print("System Expert Agent module loaded successfully!")
    # Note: Testing requires blackboard and message_bus instances
