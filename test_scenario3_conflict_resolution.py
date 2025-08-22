#!/usr/bin/env python3
"""
Test Scenario 3: Conflicting Requirements Resolution
Tests the system's ability to handle budget conflicts and suggest alternatives
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

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
from main import process_with_orchestrator

async def test_conflict_resolution():
    """Test conflict resolution with budget constraints."""
    
    print("=" * 80)
    print("SCENARIO 3: CONFLICTING REQUIREMENTS RESOLUTION")
    print("=" * 80)
    
    # Initialize components
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
    
    # Test messages sequence
    test_messages = [
        {
            "message": "I need 32 analog inputs for vibration monitoring",
            "expected": "Identify high I/O requirement",
            "description": "Initial high I/O requirement"
        },
        {
            "message": "Budget is $1500 maximum",
            "expected": "Detect budget conflict, generate A/B question",
            "description": "Budget constraint introduction"
        },
        {
            "message": "B - reduce the inputs",
            "expected": "Suggest 16 inputs configuration within budget",
            "description": "User choice to reduce inputs"
        },
        {
            "message": "Actually, the 32 inputs are mandatory for safety compliance",
            "expected": "Re-evaluate, suggest phased implementation or budget increase",
            "description": "Mandatory requirement override"
        }
    ]
    
    session_id = "conflict_test_session"
    
    for i, test_msg in enumerate(test_messages, 1):
        print(f"\n{'='*40}")
        print(f"MESSAGE {i}: {test_msg['description']}")
        print(f"{'='*40}")
        print(f"User Input: '{test_msg['message']}'")
        print(f"Expected: {test_msg['expected']}")
        print("-" * 40)
        
        try:
            # Process the message
            result = await process_with_orchestrator({
                "user_input": test_msg['message'],
                "source": "test",
                "session_id": session_id
            })
            
            # Extract key information
            conversational_response = result.get('conversational_response', 'No response')
            specs = result.get('session_context', {}).get('accumulated_specifications', [])
            confidence = result.get('aggregate_confidence', 0)
            
            print(f"\nRESPONSE:")
            print(f"Conversational: {conversational_response}")
            print(f"Total Specifications: {len(specs)}")
            print(f"Confidence: {confidence:.2f}")
            
            # Check for specific expected behaviors
            if i == 1:
                # Check if 32 analog inputs were identified
                analog_specs = [s for s in specs if 'analog' in str(s).lower()]
                if analog_specs:
                    print(f"SUCCESS: Identified analog input requirement")
                    for spec in analog_specs:
                        print(f"  - {spec.get('constraint')}: {spec.get('value')}")
                else:
                    print("WARNING: No analog input specifications found")
                    
            elif i == 2:
                # Check for budget conflict detection
                if 'budget' in conversational_response.lower() or 'cost' in conversational_response.lower():
                    print(f"SUCCESS: Budget consideration detected")
                if any(word in conversational_response.lower() for word in ['option', 'choice', 'alternative', 'reduce']):
                    print(f"SUCCESS: Conflict resolution suggested")
                    
            elif i == 3:
                # Check for reduced configuration
                if '16' in conversational_response or 'reduce' in conversational_response.lower():
                    print(f"SUCCESS: Reduced configuration suggested")
                    
            elif i == 4:
                # Check for phased or budget increase suggestion
                if any(word in conversational_response.lower() for word in ['phase', 'staged', 'budget', 'increase', 'safety', 'compliance']):
                    print(f"SUCCESS: Addressed mandatory requirement")
            
            # Show specifications accumulated
            if specs:
                print(f"\nAccumulated Specifications:")
                for spec in specs[-3:]:  # Show last 3 specs
                    print(f"  - {spec.get('constraint', 'N/A')}: {spec.get('value', 'N/A')} (strength: {spec.get('strength', 0)})")
                    
        except Exception as e:
            print(f"ERROR: Processing failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print(f"\n{'='*80}")
    print("SCENARIO 3 SUMMARY")
    print(f"{'='*80}")
    
    # Get final session state
    session_key = f"session_{session_id}"
    final_state = await blackboard.read("orchestrator", "consolidated", session_key)
    
    if final_state:
        all_specs = final_state.get('accumulated_specs', [])
        print(f"Total Specifications Accumulated: {len(all_specs)}")
        print(f"Total Conversation Turns: {final_state.get('conversation_turn', 0)}")
        
        # Analyze conflict resolution
        analog_specs = [s for s in all_specs if 'analog' in str(s).lower()]
        budget_specs = [s for s in all_specs if 'budget' in str(s).lower() or '$' in str(s)]
        
        print(f"\nConflict Analysis:")
        print(f"  - Analog Input Specs: {len(analog_specs)}")
        print(f"  - Budget-related Specs: {len(budget_specs)}")
        
        if analog_specs:
            print(f"\nAnalog Requirements:")
            for spec in analog_specs:
                print(f"  - {spec.get('constraint')}: {spec.get('value')} (strength: {spec.get('strength')})")
                
        if budget_specs:
            print(f"\nBudget Constraints:")
            for spec in budget_specs:
                print(f"  - {spec.get('constraint')}: {spec.get('value')} (strength: {spec.get('strength')})")
    
    # Cleanup
    await message_bus.stop()
    print(f"\n{'='*80}")
    print("SUCCESS: Conflict Resolution Test Completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_conflict_resolution())