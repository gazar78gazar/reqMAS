"""
Vector Clock Implementation for reqMAS Phase 1
CRDT-based conflict detection for distributed agent coordination
"""

from typing import Dict, Any, List, Optional, Tuple
import copy

class VectorClock:
    """
    Vector clock implementation for CRDT-based conflict detection.
    Enables causal ordering and concurrent operation detection.
    """
    
    def __init__(self):
        # Initialize empty vector clock
        self.clock = {}
        
    def increment(self, agent_id: str) -> Dict[str, int]:
        """
        Increment the clock for a specific agent.
        Returns the updated clock.
        """
        if agent_id not in self.clock:
            self.clock[agent_id] = 0
        
        self.clock[agent_id] += 1
        return copy.deepcopy(self.clock)
    
    def update(self, other_clock: Dict[str, int]) -> None:
        """
        Update this clock with values from another clock.
        Takes the max of each component.
        """
        for agent_id, value in other_clock.items():
            self.clock[agent_id] = max(self.clock.get(agent_id, 0), value)
    
    def merge(self, other_clock: Dict[str, int]) -> Dict[str, int]:
        """
        Merge this clock with another clock.
        Returns a new clock with the max of each component.
        """
        merged = copy.deepcopy(self.clock)
        
        for agent_id, value in other_clock.items():
            merged[agent_id] = max(merged.get(agent_id, 0), value)
        
        return merged
    
    def compare(self, other_clock: Dict[str, int]) -> str:
        """
        Compare this clock with another clock.
        Returns:
        - "before": if this clock is causally before other_clock
        - "after": if this clock is causally after other_clock
        - "concurrent": if the clocks are concurrent (neither before nor after)
        - "equal": if the clocks are equal
        """
        if self.clock == other_clock:
            return "equal"
        
        # Check if this clock is less than or equal to other_clock in all components
        less_or_equal = True
        for agent_id, value in self.clock.items():
            if value > other_clock.get(agent_id, 0):
                less_or_equal = False
                break
        
        # Check if this clock is greater than or equal to other_clock in all components
        greater_or_equal = True
        for agent_id, value in other_clock.items():
            if value > self.clock.get(agent_id, 0):
                greater_or_equal = False
                break
        
        if less_or_equal and not greater_or_equal:
            return "before"
        elif greater_or_equal and not less_or_equal:
            return "after"
        else:
            return "concurrent"
    
    def is_concurrent(self, other_clock: Dict[str, int]) -> bool:
        """
        Check if this clock is concurrent with another clock.
        Two clocks are concurrent if neither happened before the other.
        """
        return self.compare(other_clock) == "concurrent"
    
    def detect_conflicts(self, updates: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Detect conflicts between multiple updates based on vector clocks.
        Returns pairs of conflicting updates.
        """
        conflicts = []
        
        # Compare each pair of updates
        for i in range(len(updates)):
            for j in range(i + 1, len(updates)):
                update1 = updates[i]
                update2 = updates[j]
                
                # Extract vector clocks
                clock1 = update1.get("vector_clock", {})
                clock2 = update2.get("vector_clock", {})
                
                # Check if clocks are concurrent
                if self._is_concurrent(clock1, clock2):
                    conflicts.append((update1, update2))
        
        return conflicts
    
    def _is_concurrent(self, clock1: Dict[str, int], clock2: Dict[str, int]) -> bool:
        """
        Check if two clocks are concurrent.
        """
        all_keys = set(clock1.keys()) | set(clock2.keys())
        
        clock1_ahead = False
        clock2_ahead = False
        
        for key in all_keys:
            if clock1.get(key, 0) > clock2.get(key, 0):
                clock1_ahead = True
            elif clock2.get(key, 0) > clock1.get(key, 0):
                clock2_ahead = True
        
        # If both are ahead in some dimension, they're concurrent
        return clock1_ahead and clock2_ahead
    
    def to_dict(self) -> Dict[str, int]:
        """
        Return the clock as a dictionary.
        """
        return copy.deepcopy(self.clock)
    
    def __str__(self) -> str:
        """
        String representation of the vector clock.
        """
        return str(self.clock)


if __name__ == "__main__":
    print("Vector Clock module loaded successfully!")
    
    # Test vector clock
    clock1 = VectorClock()
    clock1.increment("agent1")
    clock1.increment("agent2")
    
    clock2 = VectorClock()
    clock2.increment("agent1")
    clock2.increment("agent3")
    
    print(f"Clock1: {clock1}")
    print(f"Clock2: {clock2}")
    print(f"Comparison: {clock1.compare(clock2.to_dict())}")
    print(f"Is concurrent: {clock1.is_concurrent(clock2.to_dict())}")
