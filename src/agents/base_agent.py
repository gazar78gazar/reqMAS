"""
Base Agent Implementation for reqMAS Phase 1
Abstract stateless agent class for all expert agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

class StatelessAgent(ABC):
    """
    Abstract base class for all stateless agents.
    Agents receive full context and return results without maintaining state.
    """
    
    def __init__(self, agent_id: str, model: str, blackboard, message_bus):
        self.agent_id = agent_id
        self.model = model
        self.blackboard = blackboard
        self.message_bus = message_bus
        self.processing = False
        
    @abstractmethod
    async def process(self, input_data: Dict, context: Dict) -> Dict:
        """
        Process input with given context.
        Must be implemented by each agent.
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List[str]:
        """Return list of tools this agent can access."""
        pass
    
    async def execute(self, input_data: Dict) -> Dict:
        """
        Execute agent processing with timeout and error handling.
        """
        if self.processing:
            raise Exception(f"{self.agent_id} is already processing")
        
        self.processing = True
        
        try:
            # Get context from blackboard
            context = await self._get_context()
            
            # Process with timeout (3 seconds for Phase 1)
            result = await asyncio.wait_for(
                self.process(input_data, context),
                timeout=3.0
            )
            
            # Write results to blackboard
            await self._write_results(result)
            
            # Publish completion event
            await self.message_bus.publish(
                sender=self.agent_id,
                message_type="processing_complete",
                payload=result
            )
            
            return result
            
        except asyncio.TimeoutError:
            print(f"{self.agent_id} processing timeout")
            return {
                "status": "timeout",
                "partial_results": None,
                "confidence": 0.0
            }
        except Exception as e:
            print(f"{self.agent_id} processing error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "confidence": 0.0
            }
        finally:
            self.processing = False
    
    async def _get_context(self) -> Dict:
        """Get relevant context from blackboard."""
        context = {
            "requirements": await self.blackboard.read(self.agent_id, "raw"),
            "user_profile": await self.blackboard.read(self.agent_id, "user_profile"),
            "session_id": await self.blackboard.read(self.agent_id, "session_id")
        }
        
        # Add agent-specific context
        if self.agent_id != "orchestrator":
            context["other_agents"] = await self.blackboard.read(self.agent_id, "processed")
        
        return context
    
    async def _write_results(self, results: Dict):
        """Write results to blackboard."""
        await self.blackboard.write(
            agent_id=self.agent_id,
            space="processed",
            key=self.agent_id,
            value=results
        )
    
    def calculate_confidence(self, results: Dict) -> float:
        """
        Calculate confidence score for results.
        Override in specific agents for custom calculation.
        """
        # Basic confidence calculation for Phase 1
        if not results:
            return 0.0
        
        factors = []
        
        # Check completeness
        if results.get("specifications"):
            factors.append(0.3)
        
        # Check for conflicts
        if not results.get("conflicts"):
            factors.append(0.3)
        
        # Check for missing data
        if not results.get("requires_clarification"):
            factors.append(0.4)
        
        return sum(factors)

if __name__ == "__main__":
    print("Base Agent module loaded successfully!")
    
    # Cannot test directly as this is an abstract class
    print("Note: This is an abstract class and cannot be instantiated directly.")
