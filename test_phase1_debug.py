"""
Phase 1 Test with Comprehensive Debugging
"""

import requests
import json
import time

def test_with_full_debug():
    """Test with full debugging output"""
    
    test_cases = [
        {
            "name": "I/O Test",
            "input": "I need 16 digital inputs and 8 analog outputs",
            "expected": {"has_io_content": True}
        },
        {
            "name": "System Test",
            "input": "I need high performance CPU with real-time processing",
            "expected": {"has_system_content": True}
        },
        {
            "name": "Communication Test",
            "input": "I need Modbus TCP protocol with Ethernet connectivity",
            "expected": {"has_comm_content": True}
        }
    ]
    
    for test in test_cases:
        print(f"\n" + "="*60)
        print(f"TEST: {test['name']}")
        print(f"Input: {test['input']}")
        print("="*60)
        
        response = requests.post(
            "http://localhost:8000/process",
            json={
                "user_input": test['input'],
                "session_id": f"debug_{test['name']}_{int(time.time())}"
            },
            timeout=60
        )
        
        print(f"\n[TEST DEBUG] Status code: {response.status_code}")
        
        if response.status_code == 200:
            # Get raw data
            data = response.json()
            print(f"[TEST DEBUG] Raw response keys: {list(data.keys())}")
            
            # Try different extraction paths
            if "result" in data:
                actual_data = data["result"]
                print(f"[TEST DEBUG] Found 'result' key, inner keys: {list(actual_data.keys())}")
            else:
                actual_data = data
                print(f"[TEST DEBUG] No 'result' key, using direct data")
            
            # Extract routing
            routing = actual_data.get("routing", {})
            print(f"[TEST DEBUG] Routing extracted: {routing}")
            
            # Extract agents
            activated_agents = actual_data.get("activated_agents", [])
            print(f"[TEST DEBUG] Activated agents: {activated_agents}")
            
            # Extract specs
            merged_results = actual_data.get("merged_results", {})
            if merged_results:
                print(f"[TEST DEBUG] Merged results keys: {list(merged_results.keys())}")
                if "primary" in merged_results:
                    primary = merged_results["primary"]
                    if isinstance(primary, dict) and "specifications" in primary:
                        specs = primary["specifications"]
                        print(f"[TEST DEBUG] Found {len(specs)} specifications")
                        for spec in specs[:2]:
                            print(f"  - {spec.get('constraint', 'N/A')}: {spec.get('value', 'N/A')}")
            
            # Extract conversational response
            conv_response = actual_data.get("conversational_response", "")
            print(f"[TEST DEBUG] Response preview: {conv_response[:100]}...")
            
            # Check if response is generic
            if "I'm ready to help" in conv_response:
                print("[TEST DEBUG] WARNING: Generic response detected!")
            elif "Based on your requirements" in conv_response:
                print("[TEST DEBUG] SUCCESS: Contextual response detected!")
            
            # Validate expectations
            for key, expected_value in test['expected'].items():
                actual_value = routing.get(key, False)
                if actual_value == expected_value:
                    print(f"[TEST RESULT] ✓ {key}: {actual_value}")
                else:
                    print(f"[TEST RESULT] ✗ {key}: expected {expected_value}, got {actual_value}")
        else:
            print(f"[TEST ERROR] HTTP {response.status_code}")
            print(f"[TEST ERROR] Response: {response.text[:200]}")

def test_api_structure():
    """Test to understand the exact API structure"""
    print("\n" + "="*60)
    print("API STRUCTURE TEST")
    print("="*60)
    
    response = requests.post(
        "http://localhost:8000/process",
        json={"user_input": "Test", "session_id": "structure_test"}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("\nFull Response Structure:")
        print(json.dumps(data, indent=2))
        
        print("\n[STRUCTURE ANALYSIS]")
        
        def analyze_structure(obj, path="root"):
            """Recursively analyze structure"""
            if isinstance(obj, dict):
                print(f"{path}: dict with {len(obj)} keys: {list(obj.keys())[:5]}")
                for key in ["result", "routing", "specifications", "conversational_response", "activated_agents"]:
                    if key in obj:
                        analyze_structure(obj[key], f"{path}.{key}")
            elif isinstance(obj, list):
                print(f"{path}: list with {len(obj)} items")
                if obj and isinstance(obj[0], dict):
                    print(f"  First item keys: {list(obj[0].keys())}")
        
        analyze_structure(data)

if __name__ == "__main__":
    print("PHASE 1 DEBUG TEST")
    print("=" * 60)
    
    # First understand structure
    test_api_structure()
    
    # Then run tests with debugging
    test_with_full_debug()
    
    print("\n" + "=" * 60)
    print("DEBUG TEST COMPLETE")
    print("Check server logs for [SYSTEM_EXPERT] and [COMM_EXPERT] messages")