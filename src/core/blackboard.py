"""
Simplified Reflective Blackboard Implementation
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import asyncio


class ReflectiveBlackboard:
    """
    Reflective blackboard with async operations for concurrent access
    """
    
    def __init__(self):
        # Three-level knowledge spaces
        self.knowledge_spaces = {
            "raw": {},
            "processed": {},
            "validated": {},
            "consolidated": {}
        }
        
        # Agent spaces with priorities
        self.agent_spaces = {
            "io_expert": {
                "priority": 3,
                "buffer": {},
                "permissions": ["read-all", "write-requirements", "write-conflicts"]
            },
            "system_expert": {
                "priority": 2,
                "analysis": {},
                "permissions": ["read-requirements", "read-io", "write-processed"]
            },
            "communication_expert": {
                "priority": 2,
                "recommendations": {},
                "permissions": ["read-validated", "write-consolidated"]
            }
        }
        
        # Conflict registry
        self.conflicts = []
        
        # Vector clocks for conflict detection
        self.vector_clocks = {}
        
        # Add async lock
        self.lock = asyncio.Lock()
        
        print("Blackboard initialized")
    
    async def write(self, agent_id: str, space: str, key: str, value: Any) -> bool:
        """Async write as per original design"""
        async with self.lock:
            if space in self.knowledge_spaces:
                self.knowledge_spaces[space][key] = {
                    "value": value,
                    "agent": agent_id,
                    "timestamp": datetime.now().isoformat()
                }
                return True
            return False
    
    async def read(self, agent_id: str, space: str, key: Optional[str] = None) -> Any:
        """Async read as per original design"""
        async with self.lock:
            if space in self.knowledge_spaces:
                if key:
                    entry = self.knowledge_spaces[space].get(key, {})
                    return entry.get("value") if entry else None
                return {k: v.get("value") for k, v in self.knowledge_spaces[space].items()}
            return None
    
    def merge_parallel_outputs(self, outputs: Dict[str, Any]) -> Dict:
        """Merge outputs with I/O priority"""
        merged = {}
        
        # Sort by priority (I/O first)
        priority_order = ["io_expert", "system_expert", "communication_expert"]
        
        for agent_id in priority_order:
            if agent_id in outputs:
                if agent_id == "io_expert":
                    # I/O gets priority
                    merged["primary"] = outputs[agent_id]
                else:
                    # Others get added if no conflict
                    merged[agent_id] = outputs[agent_id]
        
        return merged
    
    def get_state_snapshot(self) -> Dict:
        """Get complete blackboard state snapshot"""
        return {
            "knowledge_spaces": self.knowledge_spaces,
            "conflicts": self.conflicts
        }


async def main():
    print("Reflective Blackboard loaded successfully!")
    
    # Test blackboard
    bb = ReflectiveBlackboard()
    await bb.write("io_expert", "raw", "test", {"data": "test_value"})
    result = await bb.read("io_expert", "raw", "test")
    print(f"Blackboard test result: {result}")


if __name__ == "__main__":
    asyncio.run(main())