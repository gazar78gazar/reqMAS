#!/usr/bin/env python3
"""
Test Scenario 4: Mixed Language Support (Hebrew/English)
Tests the system's ability to handle multilingual inputs and extract requirements
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

async def test_mixed_language():
    """Test mixed Hebrew/English language support."""
    
    print("=" * 80)
    print("SCENARIO 4: MIXED LANGUAGE SUPPORT (HEBREW/ENGLISH)")
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
    
    # Test messages sequence with Hebrew and English
    test_messages = [
        {
            "message": "אני צריך מערכת בקרה עם 8 כניסות אנלוגיות",
            "expected": "Process Hebrew, extract 8 analog inputs",
            "description": "Hebrew input - control system with 8 analog inputs",
            "translation": "I need a control system with 8 analog inputs"
        },
        {
            "message": "Also need digital outputs for relay control, כמה זה יעלה?",
            "expected": "Handle mixed language, provide pricing",
            "description": "Mixed language - digital outputs and pricing question",
            "translation": "Also need digital outputs for relay control, how much will it cost?"
        },
        {
            "message": "הסביבה היא מפעל עם לחות גבוהה and dust",
            "expected": "Extract environmental requirements, suggest IP-rated solution",
            "description": "Mixed language - environmental conditions",
            "translation": "The environment is a factory with high humidity and dust"
        }
    ]
    
    session_id = "mixed_language_session"
    
    for i, test_msg in enumerate(test_messages, 1):
        print(f"\n{'='*40}")
        print(f"MESSAGE {i}: {test_msg['description']}")
        print(f"{'='*40}")
        print(f"User Input: '{test_msg['message']}'")
        print(f"Translation: {test_msg['translation']}")
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
            
            # Check for specific expected behaviors based on message number
            if i == 1:
                # Check if 8 analog inputs were identified
                analog_specs = [s for s in specs if 'analog' in str(s).lower() or '8' in str(s)]
                if analog_specs:
                    print(f"SUCCESS: Identified analog input requirement from Hebrew")
                    for spec in analog_specs:
                        print(f"  - {spec.get('constraint')}: {spec.get('value')}")
                else:
                    print("INFO: Hebrew text may need clarification")
                    # Check if system asked for clarification
                    if 'clarif' in conversational_response.lower() or '?' in conversational_response:
                        print("SUCCESS: System requested clarification for Hebrew input")
                    
            elif i == 2:
                # Check for digital outputs and pricing
                digital_specs = [s for s in specs if 'digital' in str(s).lower() or 'relay' in str(s).lower()]
                if digital_specs:
                    print(f"SUCCESS: Identified digital output requirement")
                    for spec in digital_specs:
                        print(f"  - {spec.get('constraint')}: {spec.get('value')}")
                
                # Check for pricing mention
                if any(word in conversational_response.lower() for word in ['price', 'cost', 'budget', '$']):
                    print(f"SUCCESS: Pricing information addressed")
                    
            elif i == 3:
                # Check for environmental requirements
                env_keywords = ['humidity', 'dust', 'environment', 'ip', 'rating', 'protection']
                if any(keyword in conversational_response.lower() for keyword in env_keywords):
                    print(f"SUCCESS: Environmental requirements acknowledged")
                
                # Check for IP rating suggestion
                if 'ip' in conversational_response.lower() and any(char.isdigit() for char in conversational_response):
                    print(f"SUCCESS: IP-rated solution suggested")
            
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
    print("SCENARIO 4 SUMMARY")
    print(f"{'='*80}")
    
    # Get final session state
    session_key = f"session_{session_id}"
    final_state = await blackboard.read("orchestrator", "consolidated", session_key)
    
    if final_state:
        all_specs = final_state.get('accumulated_specs', [])
        print(f"Total Specifications Accumulated: {len(all_specs)}")
        print(f"Total Conversation Turns: {final_state.get('conversation_turn', 0)}")
        
        # Analyze language handling
        print(f"\nLanguage Processing Analysis:")
        
        # Check for analog inputs (from Hebrew)
        analog_specs = [s for s in all_specs if 'analog' in str(s).lower() or 'אנלוגי' in str(s)]
        print(f"  - Analog Input Specs: {len(analog_specs)}")
        
        # Check for digital outputs (from mixed)
        digital_specs = [s for s in all_specs if 'digital' in str(s).lower() or 'relay' in str(s).lower()]
        print(f"  - Digital Output Specs: {len(digital_specs)}")
        
        # Check for environmental specs (from mixed)
        env_specs = [s for s in all_specs if any(word in str(s).lower() for word in ['humidity', 'dust', 'ip', 'environment'])]
        print(f"  - Environmental Specs: {len(env_specs)}")
        
        if all_specs:
            print(f"\nAll Captured Specifications:")
            for i, spec in enumerate(all_specs, 1):
                print(f"  {i}. {spec.get('constraint', 'N/A')}: {spec.get('value', 'N/A')} (strength: {spec.get('strength', 0)})")
        
        # Check if clarifications were needed
        messages = final_state.get('messages', [])
        clarification_count = sum(1 for msg in messages if 'clarif' in str(msg).lower())
        print(f"\nClarification Requests: {clarification_count}")
    
    # Cleanup
    await message_bus.stop()
    print(f"\n{'='*80}")
    print("SUCCESS: Mixed Language Support Test Completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_mixed_language())