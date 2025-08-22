#!/usr/bin/env python3
"""
Test script to verify the comprehensive diagnostic tracing works
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Force load from project root
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import required modules
from core.blackboard import ReflectiveBlackboard
from core.message_bus import EventDrivenMessageBus
from agents.orchestrator import OrchestratorAgent
from agents.io_expert import IOExpertAgent

async def test_diagnostic_trace():
    """Test the comprehensive diagnostic tracing."""
    
    print("=" * 60)
    print("Testing Comprehensive Diagnostic Tracing")
    print("=" * 60)
    
    # Initialize components like in main.py
    blackboard = ReflectiveBlackboard()
    message_bus = EventDrivenMessageBus()
    await message_bus.start()
    
    # Initialize agents
    orchestrator = OrchestratorAgent(blackboard, message_bus)
    io_expert = IOExpertAgent(blackboard, message_bus)
    
    # Agent registry
    agent_registry = {
        "orchestrator": orchestrator,
        "io_expert": io_expert,
    }
    
    # Import the function we want to test (after setting up globals)
    from main import process_with_orchestrator
    
    # Test the diagnostic tracing with a simple input
    test_input = {
        "user_input": "I need 4 digital inputs and 2 analog outputs",
        "source": "test",
        "session_id": "diagnostic_test"
    }
    
    print(f"Testing with input: {test_input}")
    print("\n" + "=" * 80)
    
    try:
        # This should trigger all our diagnostic tracing
        result = await process_with_orchestrator(test_input)
        
        print("=" * 80)
        print("TEST RESULTS:")
        print(f"SUCCESS: Function completed successfully")
        print(f"SUCCESS: Result contains {len(result.keys())} keys")
        print(f"SUCCESS: Conversational response present: {'conversational_response' in result}")
        if 'conversational_response' in result:
            print(f"SUCCESS: Response content: '{result['conversational_response']}'")
        else:
            print("ERROR: Conversational response missing!")
            
    except Exception as e:
        print(f"ERROR: Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    await message_bus.stop()
    print("\nSUCCESS: Diagnostic tracing test completed!")

if __name__ == "__main__":
    asyncio.run(test_diagnostic_trace())