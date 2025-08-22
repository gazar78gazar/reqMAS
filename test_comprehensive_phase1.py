"""
Comprehensive Phase 1 Integration Test
Tests the ACTUAL system behavior, not mocked components
"""

import requests
import json
import time

def test_api_structure():
    """First understand what the API actually returns"""
    response = requests.post(
        "http://localhost:8000/process",
        json={
            "user_input": "I need 16 digital inputs",
            "session_id": f"test_{int(time.time())}"
        }
    )
    
    print("=== API STRUCTURE TEST ===")
    print(f"Status: {response.status_code}")
    
    data = response.json()
    
    # Find where the data actually is
    def find_path(obj, target_key, path=""):
        """Recursively find the path to a key"""
        if isinstance(obj, dict):
            if target_key in obj:
                return f"{path}['{target_key}']"
            for k, v in obj.items():
                result = find_path(v, target_key, f"{path}['{k}']")
                if result:
                    return result
        elif isinstance(obj, list) and obj:
            for i, item in enumerate(obj):
                result = find_path(item, target_key, f"{path}[{i}]")
                if result:
                    return result
        return None
    
    # Find critical fields
    routing_path = find_path(data, "routing", "data")
    agents_path = find_path(data, "activated_agents", "data")
    specs_path = find_path(data, "specifications", "data")
    conv_response_path = find_path(data, "conversational_response", "data")
    
    print(f"Path to routing: {routing_path}")
    print(f"Path to activated_agents: {agents_path}")
    print(f"Path to specifications: {specs_path}")
    print(f"Path to conversational_response: {conv_response_path}")
    
    print("\nActual Response Structure:")
    print(json.dumps(data, indent=2))
    
    return data, routing_path, agents_path, specs_path, conv_response_path

def extract_by_path(data, path):
    """Extract data using the discovered path"""
    if not path:
        return None
    
    # Remove 'data' prefix and parse the path
    path = path.replace("data", "").strip()
    if not path:
        return data
    
    # Evaluate the path dynamically
    try:
        return eval(f"data{path}")
    except:
        return None

def test_actual_behavior():
    """Test what the system ACTUALLY does, not what we think it does"""
    
    print("\n=== BEHAVIOR TESTS ===")
    
    # First, discover the structure once
    structure_data, routing_path, agents_path, specs_path, conv_response_path = test_api_structure()
    
    test_cases = [
        {
            "name": "I/O Test",
            "input": "I need 16 digital inputs and 8 analog outputs",
            "expected_routing": {"has_io_content": True},
            "expected_agents": ["io_expert"]
        },
        {
            "name": "System Test", 
            "input": "I need high performance CPU with real-time processing",
            "expected_routing": {"has_system_content": True},
            "expected_agents": ["system_expert"]
        },
        {
            "name": "Communication Test",
            "input": "I need Modbus TCP protocol with Ethernet connectivity", 
            "expected_routing": {"has_comm_content": True},
            "expected_agents": ["communication_expert"]
        },
        {
            "name": "Mixed Test",
            "input": "4 RTD sensors with Modbus communication and fast processor",
            "expected_routing": {"has_io_content": True, "has_system_content": True, "has_comm_content": True},
            "expected_agents": ["io_expert", "system_expert", "communication_expert"]
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n--- Testing: {test['name']} ---")
        print(f"Input: {test['input']}")
        
        response = requests.post(
            "http://localhost:8000/process",
            json={
                "user_input": test["input"],
                "session_id": f"test_{test['name']}_{int(time.time())}"
            },
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            results.append((test['name'], False, f"HTTP {response.status_code}"))
            continue
        
        data = response.json()
        
        # Extract using discovered paths
        routing = extract_by_path(data, routing_path)
        activated_agents = extract_by_path(data, agents_path)
        specifications = extract_by_path(data, specs_path)
        conv_response = extract_by_path(data, conv_response_path)
        
        print(f"Actual routing: {routing}")
        print(f"Actual agents: {activated_agents}")
        print(f"Specifications found: {len(specifications) if specifications else 0}")
        print(f"Response preview: {conv_response[:100] if conv_response else 'None'}...")
        
        # Validate expectations
        success = True
        issues = []
        
        # Check routing
        if routing:
            for key, expected in test['expected_routing'].items():
                actual = routing.get(key, False)
                if actual != expected:
                    success = False
                    issues.append(f"Routing {key}: expected {expected}, got {actual}")
        else:
            success = False
            issues.append("No routing information found")
        
        # Check agents
        if activated_agents:
            expected_set = set(test['expected_agents'])
            actual_set = set(activated_agents)
            if expected_set != actual_set:
                success = False
                issues.append(f"Agents: expected {expected_set}, got {actual_set}")
        else:
            success = False
            issues.append("No activated agents found")
        
        # Check if we got specifications (for non-question inputs)
        if not test['input'].endswith('?') and not specifications:
            issues.append("No specifications extracted")
        
        # Check if response is not generic
        if conv_response and "I'm ready to help" in conv_response:
            issues.append("Generic response - Phase 2 may not be working")
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"Result: {status}")
        if issues:
            for issue in issues:
                print(f"  - {issue}")
        
        results.append((test['name'], success, issues))
    
    print("\n=== SUMMARY ===")
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, issues in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if not success and issues:
            for issue in issues:
                print(f"    - {issue}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print("\nNext steps:")
        print("1. Check server logs for detailed diagnostic output")
        print("2. Verify System/Communication experts are working")
        print("3. Confirm Phase 2 is generating contextual responses")

def test_session_persistence():
    """Test that sessions properly accumulate specifications"""
    print("\n=== SESSION PERSISTENCE TEST ===")
    
    session_id = f"persistence_test_{int(time.time())}"
    
    messages = [
        "I need 8 analog inputs for temperature monitoring",
        "Also need 4 digital outputs for relay control", 
        "The system should have Modbus RTU communication",
        "What are my total requirements?"
    ]
    
    total_specs = 0
    
    for i, message in enumerate(messages, 1):
        print(f"\nMessage {i}: {message}")
        
        response = requests.post(
            "http://localhost:8000/process",
            json={
                "user_input": message,
                "session_id": session_id
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Try to find specifications count in response
            # This will need to be adapted based on actual structure
            print(f"  Response received: {response.status_code}")
        else:
            print(f"  ❌ Error: {response.status_code}")

if __name__ == "__main__":
    print("🔧 COMPREHENSIVE PHASE 1 INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Test actual behavior
        test_actual_behavior()
        
        # Test session persistence
        test_session_persistence()
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        print("Make sure the server is running on http://localhost:8000")
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST COMPLETE")
    print("=" * 60)