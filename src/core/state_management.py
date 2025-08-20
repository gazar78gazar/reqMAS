"""
State Management for reqMAS Phase 1
Core requirement state structure with LangGraph integration
"""

from typing import Dict, List, Any, Optional, Annotated
from langgraph.graph import StateGraph
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from datetime import datetime
import operator
import json
import uuid


class RequirementState(BaseModel):
    """Core requirement state structure"""
    raw: List[str] = Field(default_factory=list)
    processed: Dict[str, List] = Field(default_factory=dict)
    validated: Dict[str, Any] = Field(default_factory=dict)
    consolidated: Dict[str, Any] = Field(default_factory=dict)


class SessionState(BaseModel):
    """Session state for conversation continuity"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Dict[str, str]] = Field(default_factory=list)
    requirements: RequirementState = Field(default_factory=RequirementState)
    user_profile: str = Field(default="intermediate")  # novice, intermediate, expert
    confidence_history: List[float] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

class BlackboardState(BaseModel):
    """Main blackboard state for the MAS with LangGraph integration"""
    
    # Message history for LangGraph
    messages: Annotated[List[BaseMessage], operator.add] = Field(default_factory=list)
    
    # Requirements tracking
    requirements: RequirementState = Field(default_factory=RequirementState)
    
    # Agent priorities for merging
    agent_priorities: Dict[str, int] = Field(
        default_factory=lambda: {
            "io_expert": 3,
            "system_expert": 2,
            "communication_expert": 2,
            "decision_coordinator": 1
        }
    )
    
    # Conflict tracking
    conflicts: List[Dict] = Field(default_factory=list)
    
    # Agent contributions
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Session metadata
    session_id: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Vector clocks for CRDT
    vector_clocks: Dict[str, int] = Field(default_factory=dict)
    
    # Session states
    sessions: Dict[str, SessionState] = Field(default_factory=dict)


def merge_with_io_priority(current: Dict, update: Dict) -> Dict:
    """
    Merge function that respects I/O agent priority.
    This is the core reducer for parallel agent outputs.
    """
    merged = current.copy()
    
    # Get priority order
    priority_order = ["io_expert", "communication_expert", "system_expert"]
    
    # Process updates in priority order
    for agent_id in priority_order:
        if agent_id in update:
            agent_update = update[agent_id]
            
            # For I/O expert, always take its constraints as primary
            if agent_id == "io_expert":
                merged["primary_constraints"] = agent_update.get("constraints", [])
                merged["veto_flags"] = agent_update.get("veto_flags", [])
            
            # For other agents, merge if no conflicts with I/O
            else:
                if not conflicts_with_io(agent_update, merged.get("primary_constraints", [])):
                    merged[agent_id] = agent_update
                else:
                    # Flag conflict for validation
                    merged.setdefault("conflicts", []).append({
                        "agent": agent_id,
                        "conflict_type": "io_incompatible",
                        "details": agent_update
                    })
    
    return merged


def conflicts_with_io(update: Dict, io_constraints: List) -> bool:
    """Check if an update conflicts with I/O constraints"""
    for constraint in update.get("constraints", []):
        for io_constraint in io_constraints:
            if constraint.get("type") == io_constraint.get("type"):
                if constraint.get("value") != io_constraint.get("value"):
                    return True
    return False


def create_graph_state():
    """Create the LangGraph state with reducers"""
    return BlackboardState


if __name__ == "__main__":
    print("State management module loaded successfully!")
    # Test state creation
    state = BlackboardState()
    print(f"Created state with session: {state.session_id}")
    print(f"Agent priorities: {state.agent_priorities}")