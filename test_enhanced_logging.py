#!/usr/bin/env python3
"""
Test script for the enhanced logging system in IO Expert Agent
"""

import asyncio
import sys
import os
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
from agents.io_expert import IOExpertAgent

async def test_enhanced_logging():
    """Test the enhanced logging system with various inputs."""
    
    print("=" * 60)
    print("Testing Enhanced Logging System for IO Expert Agent")
    print("=" * 60)
    
    # Initialize components
    blackboard = ReflectiveBlackboard()
    message_bus = EventDrivenMessageBus()
    await message_bus.start()
    
    # Create IO Expert Agent
    io_expert = IOExpertAgent(blackboard, message_bus)
    
    # Test cases with different complexity levels
    test_cases = [
        {
            "name": "Simple I/O Request",
            "input": "I need 4 digital inputs and 2 analog outputs"
        },
        {
            "name": "Complex Industrial Setup",
            "input": "Monitor temperature and pressure in 3 tanks with RS485 communication"
        },
        {
            "name": "Minimal Input", 
            "input": "sensors"
        },
        {
            "name": "Mixed Requirements",
            "input": "Need USB port, 8 digital I/O, and Ethernet connectivity for monitoring system"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*20} Test Case {i}: {test_case['name']} {'='*20}")
        print(f"Input: '{test_case['input']}'")
        print("-" * 80)
        
        try:
            # Process the input
            result = await io_expert.process({
                "user_input": test_case['input']
            }, {})
            
            # Display summary results
            print(f"\nSUMMARY RESULTS:")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Extraction Method: {result.get('extraction_method', 'unknown')}")
            print(f"   Specifications Found: {len(result.get('specifications', []))}")
            print(f"   Overall Confidence: {result.get('confidence', 0):.2f}")
            
            # Show performance metrics if available
            if 'performance_metrics' in result:
                metrics = result['performance_metrics']
                print(f"   Performance Metrics:")
                print(f"     - Response Time: {metrics.get('response_time', 0):.2f}s")
                print(f"     - Parsing Strategy: {metrics.get('parsing_strategy_used', 'N/A')}")
                print(f"     - Model Used: {result.get('model_used', 'N/A')}")
            
        except Exception as e:
            print(f"ERROR: Test failed: {str(e)}")
        
        print("\n" + "="*80)
    
    # Cleanup
    await message_bus.stop()
    print("\nSUCCESS: Enhanced logging system test completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_logging())