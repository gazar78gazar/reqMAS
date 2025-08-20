"""
Integration Tests for reqMAS Phase 1
Tests parallel agent execution with I/O priority
"""

import pytest
import asyncio
import json
import sys
import os

# Add src to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.blackboard import ReflectiveBlackboard
from src.core.message_bus import EventDrivenMessageBus
from src.agents.orchestrator import OrchestratorAgent
from src.agents.io_expert import IOExpertAgent

@pytest.mark.asyncio
async def test_parallel_execution():
    """Test parallel agent execution with I/O priority."""
    
    # Setup
    blackboard = ReflectiveBlackboard()
    message_bus = EventDrivenMessageBus()
    await message_bus.start()
    
    # Initialize agents
    orchestrator = OrchestratorAgent(blackboard, message_bus)
    io_expert = IOExpertAgent(blackboard, message_bus)
    
    # Register agents
    agent_registry = {
        "orchestrator": orchestrator,
        "io_expert": io_expert
    }
    
    # Mock process function to avoid actual LLM calls
    async def mock_process(self, input_data, context):
        if self.agent_id == "io_expert":
            return {
                "specifications": [
                    {
                        "type": "SR",
                        "constraint": "Digital I/O count",
                        "value": "16",
                        "strength": 1000,
                        "reasoning": "Required for sensor connections"
                    }
                ],
                "veto_constraints": ["Digital I/O count"],
                "dependencies": {
                    "communication": ["Modbus RTU"],
                    "performance": ["Standard scan rate"]
                },
                "confidence": 0.8,
                "requires_clarification": []
            }
        else:
            return {
                "routing": {
                    "has_io_content": True,
                    "confidence": 0.7
                },
                "activated_agents": ["io_expert"],
                "status": "complete"
            }
    
    # Patch the process method
    original_io_process = io_expert.process
    original_orch_process = orchestrator.process
    io_expert.process = mock_process.__get__(io_expert)
    orchestrator.process = mock_process.__get__(orchestrator)
    
    try:
        # Test input
        input_data = {
            "user_input": "I need a controller with 16 digital I/O points",
            "source": "test",
            "session_id": "test-session"
        }
        
        # Process with orchestrator
        routing_result = await orchestrator.process(input_data, {})
        
        # Verify routing
        assert routing_result["status"] == "complete"
        assert "io_expert" in routing_result["activated_agents"]
        
        # Process with I/O expert
        io_result = await io_expert.process(input_data, {})
        
        # Verify I/O expert result
        assert io_result["confidence"] >= 0.7
        assert len(io_result["specifications"]) > 0
        assert "Digital I/O count" in io_result["veto_constraints"]
        
        # Test merge with I/O priority
        merged = await blackboard.merge_parallel_outputs({
            "io_expert": io_result,
            "system_expert": {
                "specifications": [
                    {
                        "type": "SR",
                        "constraint": "Digital I/O count",
                        "value": "8",  # Conflicting with I/O expert
                        "strength": 100,
                        "reasoning": "Minimum requirement"
                    }
                ],
                "confidence": 0.6
            }
        })
        
        # Verify I/O priority in merge
        assert "primary" in merged
        assert merged["primary"]["specifications"][0]["value"] == "16"
        
    finally:
        # Restore original methods
        io_expert.process = original_io_process
        orchestrator.process = original_orch_process
        await message_bus.stop()

@pytest.mark.asyncio
async def test_blackboard_operations():
    """Test basic blackboard operations."""
    
    # Setup
    blackboard = ReflectiveBlackboard()
    
    # Test write and read
    assert await blackboard.write("io_expert", "raw", "test_key", {"value": "test_data"})
    result = await blackboard.read("io_expert", "raw", "test_key")
    
    # Verify read result
    assert result is not None
    assert result["value"] == "test_data"
    
    # Test state snapshot
    snapshot = blackboard.get_state_snapshot()
    assert "knowledge_spaces" in snapshot
    assert "raw" in snapshot["knowledge_spaces"]
    assert "test_key" in snapshot["knowledge_spaces"]["raw"]

@pytest.mark.asyncio
async def test_message_bus():
    """Test message bus publish and subscribe."""
    
    # Setup
    message_bus = EventDrivenMessageBus()
    await message_bus.start()
    
    # Test data
    test_messages = []
    
    # Test subscriber
    async def test_callback(message):
        test_messages.append(message)
    
    try:
        # Subscribe to test message
        message_bus.subscribe("test_message", test_callback)
        
        # Publish test message
        message_id = await message_bus.publish(
            sender="test_sender",
            message_type="test_message",
            payload={"data": "test_value"}
        )
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify message received
        assert len(test_messages) == 1
        assert test_messages[0].sender == "test_sender"
        assert test_messages[0].message_type == "test_message"
        assert test_messages[0].payload["data"] == "test_value"
        
    finally:
        await message_bus.stop()

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
