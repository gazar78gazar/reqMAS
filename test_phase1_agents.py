# test_phase1_agents.py
import requests
import json
import time

def test_phase1_activation():
    print("\n=== PHASE 1 AGENT ACTIVATION TEST ===\n")
    
    # Test different types of input to trigger different agents
    test_cases = [
        {
            "name": "I/O Test",
            "input": "I need 16 digital inputs and 8 analog outputs",
            "expected_agent": "io_expert"
        },
        {
            "name": "System Test", 
            "input": "I need high performance CPU with real-time processing",
            "expected_agent": "system_expert"
        },
        {
            "name": "Communication Test",
            "input": "I need Modbus TCP protocol with Ethernet connectivity",
            "expected_agent": "communication_expert"
        },
        {
            "name": "Mixed Test",
            "input": "4 RTD sensors with Modbus communication and fast processor",
            "expected_agents": ["io_expert", "system_expert", "communication_expert"]
        }
    ]
    
    results_summary = []
    
    for test in test_cases:
        print(f"Testing: {test['name']}")
        print(f"Input: {test['input']}")
        
        try:
            response = requests.post(
                "http://localhost:8000/process",
                json={"input": test['input'], "session_id": f"test_{test['name']}_{int(time.time())}"},
                timeout=35  # Increased to account for diagnostic timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                
                # Check which agents were activated
                routing = result.get('routing', {})
                activated = routing.get('activated_agents', [])
                
                print(f"  Routing Decision:")
                print(f"    - Has I/O content: {routing.get('has_io_content', False)}")
                print(f"    - Has System content: {routing.get('has_system_content', False)}")
                print(f"    - Has Comm content: {routing.get('has_comm_content', False)}")
                print(f"  Activated Agents: {activated}")
                
                # Check conversational response
                conv_response = result.get('conversational_response', 'MISSING')
                print(f"  Conversational Response: {conv_response[:100] if conv_response != 'MISSING' else 'MISSING'}...")
                
                # Validate expectations
                if 'expected_agents' in test:
                    expected = set(test['expected_agents'])
                    actual = set(activated)
                    if expected == actual:
                        print(f"  ✓ Correct agents activated")
                        results_summary.append((test['name'], True))
                    else:
                        print(f"  ✗ Wrong agents - Expected: {expected}, Got: {actual}")
                        results_summary.append((test['name'], False))
                elif 'expected_agent' in test:
                    if test['expected_agent'] in activated:
                        print(f"  ✓ Expected agent activated")
                        results_summary.append((test['name'], True))
                    else:
                        print(f"  ✗ Expected {test['expected_agent']}, got {activated}")
                        results_summary.append((test['name'], False))
                
                # Check specifications extracted
                specs = result.get('session_context', {}).get('accumulated_specifications', [])
                if specs:
                    print(f"  Specifications Found: {len(specs)}")
                    for spec in specs[:2]:  # Show first 2 specs
                        print(f"    - {spec.get('constraint', 'N/A')}: {spec.get('value', 'N/A')}")
                
                print()
            else:
                print(f"  ✗ Error: {response.status_code}")
                print(f"  Response: {response.text[:200]}...")
                results_summary.append((test['name'], False))
                print()
                
        except requests.exceptions.Timeout:
            print(f"  ✗ Request timed out")
            results_summary.append((test['name'], False))
            print()
        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")
            results_summary.append((test['name'], False))
            print()
    
    # Print summary
    print("=== TEST SUMMARY ===")
    passed = sum(1 for _, result in results_summary if result)
    total = len(results_summary)
    
    for name, result in results_summary:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️ {total - passed} test(s) failed")

def test_phase1_specifications():
    """Test that specifications are properly extracted and accumulated."""
    print("\n=== PHASE 1 SPECIFICATION EXTRACTION TEST ===\n")
    
    session_id = f"spec_test_{int(time.time())}"
    
    # Send multiple messages to accumulate specifications
    messages = [
        "I need 8 analog inputs for temperature monitoring",
        "Also need 4 digital outputs for relay control",
        "The system should have Modbus RTU communication",
        "What are my total requirements?"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"Message {i}: {msg}")
        
        try:
            response = requests.post(
                "http://localhost:8000/process",
                json={"input": msg, "session_id": session_id},
                timeout=35
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                
                # Get accumulated specs
                total_specs = result.get('session_context', {}).get('total_specs', 0)
                conv_response = result.get('conversational_response', 'MISSING')
                
                print(f"  Total Specs: {total_specs}")
                print(f"  Response: {conv_response[:150]}...")
                
                # For the last message, check if we get a summary
                if i == len(messages):
                    if "total requirements" in conv_response.lower() or str(total_specs) in conv_response:
                        print(f"  ✓ Summary provided with {total_specs} specifications")
                    else:
                        print(f"  ✗ Summary expected but not found")
                
                print()
            else:
                print(f"  ✗ Error: {response.status_code}")
                print()
                
        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")
            print()

def test_phase1_conversation_context():
    """Test that conversation context is maintained across messages."""
    print("\n=== PHASE 1 CONVERSATION CONTEXT TEST ===\n")
    
    session_id = f"context_test_{int(time.time())}"
    
    # Test conversation continuity
    conversation = [
        ("I need temperature monitoring", "Should mention capturing requirements"),
        ("How many sensors?", "Should ask for clarification"),
        ("4 sensors", "Should acknowledge 4 sensors"),
        ("What else do I need?", "Should reference previous requirements")
    ]
    
    for i, (msg, expectation) in enumerate(conversation, 1):
        print(f"Turn {i}: {msg}")
        print(f"  Expected: {expectation}")
        
        try:
            response = requests.post(
                "http://localhost:8000/process",
                json={"input": msg, "session_id": session_id},
                timeout=35
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                
                conv_response = result.get('conversational_response', 'MISSING')
                turn = result.get('session_context', {}).get('turn', 0)
                
                print(f"  Turn Number: {turn}")
                print(f"  Response: {conv_response[:150]}...")
                
                if turn == i:
                    print(f"  ✓ Correct turn tracking")
                else:
                    print(f"  ✗ Turn mismatch - Expected: {i}, Got: {turn}")
                
                print()
            else:
                print(f"  ✗ Error: {response.status_code}")
                print()
                
        except Exception as e:
            print(f"  ✗ Exception: {str(e)}")
            print()

if __name__ == "__main__":
    print("="*60)
    print("PHASE 1 COMPREHENSIVE TESTING")
    print("="*60)
    
    # Run all tests
    test_phase1_activation()
    test_phase1_specifications()
    test_phase1_conversation_context()
    
    print("\n" + "="*60)
    print("PHASE 1 TESTING COMPLETE")
    print("="*60)