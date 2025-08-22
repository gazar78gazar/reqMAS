"""
Orchestrator Agent Implementation for reqMAS Phase 1
Pure routing and coordination agent for expert orchestration
"""

from typing import Dict, List, Any, Optional
from agents.base_agent import StatelessAgent
from langchain_openai import ChatOpenAI
import asyncio

class OrchestratorAgent(StatelessAgent):
    """
    Pure routing and coordination agent.
    No domain analysis, only routing decisions.
    """
    
    def __init__(self, blackboard, message_bus):
        super().__init__(
            agent_id="orchestrator",
            model="gpt-4",
            blackboard=blackboard,
            message_bus=message_bus
        )
        
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=0.1  # Very low for consistent routing
        )
        
        # Routing configuration
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
        
        self.active_agents = []
        
    async def process(self, input_data: Dict, context: Dict) -> Dict:
        """
        Route input to appropriate agents based on content and confidence.
        """
        # Analyze input for routing
        routing_decision = await self._analyze_for_routing(input_data)
        
        # Determine which agents to activate
        agents_to_activate = self._select_agents(routing_decision)
        
        # Execute agents in parallel
        if agents_to_activate:
            results = await self._execute_parallel(agents_to_activate, input_data)
            
            # Merge results
            merged = self.blackboard.merge_parallel_outputs(results)
            
            # Determine next action based on confidence
            next_action = self._determine_next_action(merged)
            
            return {
                "routing": routing_decision,
                "activated_agents": agents_to_activate,
                "merged_results": merged,
                "next_action": next_action,
                "status": "complete"
            }
        
        return {
            "status": "no_agents_activated",
            "routing": routing_decision
        }
    
    def get_tools(self) -> List[str]:
        """Orchestrator has no tools, only routing."""
        return []
    
    async def _analyze_for_routing(self, input_data: Dict) -> Dict:
        """Analyze input to determine routing."""
        user_input = input_data.get("user_input", "").lower()
        
        routing = {
            "has_io_content": False,
            "has_system_content": False,
            "has_comm_content": False,
            "confidence": 0.5,
            "input_type": "unknown"
        }
        
        # Check for I/O content (primary)
        io_keywords = ["input", "output", "channel", "digital", "analog", "i/o", "dio", "aio"]
        if any(keyword in user_input for keyword in io_keywords):
            routing["has_io_content"] = True
            routing["confidence"] += 0.2
        
        # Check for system content
        system_keywords = ["processor", "memory", "performance", "speed", "cpu", "ram"]
        if any(keyword in user_input for keyword in system_keywords):
            routing["has_system_content"] = True
            routing["confidence"] += 0.15
        
        # Check for communication content
        comm_keywords = ["protocol", "modbus", "ethernet", "network", "communication"]
        if any(keyword in user_input for keyword in comm_keywords):
            routing["has_comm_content"] = True
            routing["confidence"] += 0.15
        
        # Determine input type
        if "?" in user_input:
            routing["input_type"] = "question"
        elif any(char.isdigit() for char in user_input):
            routing["input_type"] = "specification"
        else:
            routing["input_type"] = "description"
        
        return routing
    
    def _select_agents(self, routing: Dict) -> List[str]:
        """Select which agents to activate based on routing analysis."""
        agents = []
        
        # Always start with I/O if no specific content detected
        if not any([routing["has_io_content"], 
                   routing["has_system_content"], 
                   routing["has_comm_content"]]):
            agents.append("io_expert")
        else:
            # Add agents based on content
            if routing["has_io_content"]:
                agents.append("io_expert")
            if routing["has_system_content"]:
                agents.append("system_expert")
            if routing["has_comm_content"]:
                agents.append("communication_expert")
        
        return agents
    
    async def _execute_parallel(self, agents: List[str], input_data: Dict) -> Dict:
        """Execute selected agents in parallel with timeout."""
        results = {}
        
        # Create tasks for parallel execution
        tasks = []
        for agent_id in agents:
            # Get agent instance (would be injected in real implementation)
            agent = await self._get_agent_instance(agent_id)
            if agent:
                tasks.append(self._execute_with_timeout(agent, input_data, agent_id))
        
        # Execute all tasks in parallel
        if tasks:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for agent_id, result in zip(agents, completed):
                if isinstance(result, Exception):
                    results[agent_id] = {
                        "status": "error",
                        "error": str(result),
                        "confidence": 0.0
                    }
                else:
                    results[agent_id] = result
        
        return results
    
    async def _execute_with_timeout(self, agent, input_data: Dict, agent_id: str):
        """Execute agent with timeout and diagnostic logging."""
        import time
        start_time = time.time()
        
        TIMEOUT_VALUE = 30.0  # INCREASED from 3.0 for diagnostics
        print(f"   Executing {agent_id} with {TIMEOUT_VALUE}s timeout...")
        
        try:
            result = await asyncio.wait_for(
                agent.execute(input_data),
                timeout=TIMEOUT_VALUE
            )
            elapsed = time.time() - start_time
            print(f"   SUCCESS: {agent_id} completed in {elapsed:.2f}s")
            return result
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f"   ERROR: {agent_id} TIMEOUT after {elapsed:.2f}s")
            return {
                "status": "timeout",
                "agent": agent_id,
                "confidence": 0.0
            }
    
    async def _get_agent_instance(self, agent_id: str):
        """Get agent instance by ID (placeholder for Phase 1)."""
        # In real implementation, this would return actual agent instances
        # For Phase 1, we'll handle this in main.py
        return None
    
    def _determine_next_action(self, merged_results: Dict) -> str:
        """Determine next action based on merged results and confidence."""
        # Calculate overall confidence
        confidence_values = []
        
        for key, value in merged_results.items():
            if isinstance(value, dict) and "confidence" in value:
                confidence_values.append(value["confidence"])
        
        if confidence_values:
            avg_confidence = sum(confidence_values) / len(confidence_values)
        else:
            avg_confidence = 0.0
        
        # Determine action based on confidence thresholds
        if avg_confidence >= self.confidence_thresholds["high"]:
            return "direct_to_form"
        elif avg_confidence >= self.confidence_thresholds["medium"]:
            return "auto_deduce_notify"
        else:
            return "require_clarification"

if __name__ == "__main__":
    print("Orchestrator Agent module loaded successfully!")
    # Note: Testing requires blackboard and message_bus instances
