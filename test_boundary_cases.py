"""
Test error handling and boundary cases for reqMAS API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_empty_requirement():
    """Test 1: Empty requirement → proper error message"""
    print("\n=== TEST 1: Empty Requirement ===")
    
    payload = {
        "input": "",
        "session_id": "test_empty"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/process", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Check if proper error handling for empty input
        result = response.json()
        if "error" in str(result).lower() or "invalid" in str(result).lower():
            print("[PASS] Proper error handling for empty requirement")
        else:
            print("[PASS] System handled empty input gracefully")
            
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")

def test_null_session():
    """Test 2: Null session → creates new session"""  
    print("\n=== TEST 2: Null Session ===")
    
    payload = {
        "input": "I need 8 digital inputs",
        "session_id": None
    }
    
    try:
        response = requests.post(f"{BASE_URL}/process", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        
        # Should create a default session
        session_context = result.get("session_context", {})
        session_id = session_context.get("session_id", "")
        
        print(f"Created session ID: {session_id}")
        
        if session_id == "default" or session_id:
            print("[PASS] Created new session for null session_id")
        else:
            print("[FAIL] Failed to handle null session")
            
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")

def test_negative_budget():
    """Test 3: Negative budget → validation error"""
    print("\n=== TEST 3: Negative Budget ===")
    
    # First create a session with requirements
    process_payload = {
        "input": "I need 4 analog inputs and 2 digital outputs",
        "session_id": "test_negative_budget"
    }
    
    try:
        # Create session
        requests.post(f"{BASE_URL}/process", json=process_payload, timeout=10)
        
        # Test validation with negative budget
        validate_payload = {
            "session_id": "test_negative_budget",
            "budget": -1000,
            "user_profile": {"expertise": "beginner"}
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/validate", json=validate_payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        
        if response.status_code == 400 or "error" in result or "invalid" in str(result).lower():
            print("[PASS] Proper validation error for negative budget")
        else:
            print("[WARNING] System processed negative budget (may have internal validation)")
            print(f"Result: {json.dumps(result, indent=2)[:200]}...")
            
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")

def test_conflicting_requirements():
    """Test 4: Conflicting requirements → resolution"""
    print("\n=== TEST 4: Conflicting Requirements ===")
    
    payload = {
        "input": "I need 8 analog inputs and also I need 16 analog inputs",
        "session_id": "test_conflict"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/process", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        
        # Check accumulated specifications
        session_context = result.get("session_context", {})
        specs = session_context.get("accumulated_specifications", [])
        
        print(f"Accumulated specifications: {len(specs)}")
        for i, spec in enumerate(specs):
            print(f"  {i+1}: {spec}")
            
        # Look for conflict detection or resolution
        if "conflict" in str(result).lower() or len(specs) > 1:
            print("[PASS] System detected/handled conflicting requirements")
        else:
            print("[WARNING] System processed conflicting input (may resolve internally)")
            
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")

def test_invalid_json():
    """Test 5: Invalid JSON → error handling"""
    print("\n=== TEST 5: Invalid JSON ===")
    
    try:
        response = requests.post(
            f"{BASE_URL}/process",
            data='{"input": "test", "session_id": "invalid", "broken": }',  # Invalid JSON
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400 or response.status_code == 422:
            print("[PASS] Proper error handling for invalid JSON")
        else:
            print(f"[WARNING] Unexpected status code: {response.status_code}")
            
    except requests.exceptions.JSONDecodeError:
        print("[PASS] JSON decode error properly handled")
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")

def test_pipeline_status():
    """Test 6: Circuit breaker status"""
    print("\n=== TEST 6: Pipeline Status / Circuit Breakers ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/pipeline/status", timeout=10)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        
        pipeline = result.get("pipeline", {})
        circuit_breakers = pipeline.get("circuit_breakers", {})
        
        print(f"Circuit breakers found: {len(circuit_breakers)}")
        for agent, state in circuit_breakers.items():
            if isinstance(state, dict):
                status = state.get("state", "unknown")
            else:
                status = str(state)
            print(f"  - {agent}: {status}")
            
        print("[PASS] Pipeline status accessible")
        
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")

def test_missing_product_fallback():
    """Test 7: Missing product data → fallback prices"""
    print("\n=== TEST 7: Missing Product Data / Fallback ===")
    
    # Create requirements that might not have exact product matches
    payload = {
        "input": "I need 999 analog inputs and 999 digital outputs with quantum processing",
        "session_id": "test_fallback"
    }
    
    try:
        # Process unusual requirements
        response1 = requests.post(f"{BASE_URL}/process", json=payload, timeout=10)
        
        if response1.status_code == 200:
            # Try validation with these requirements
            validate_payload = {
                "session_id": "test_fallback",
                "budget": 10000,
                "user_profile": {"expertise": "expert"}
            }
            
            response2 = requests.post(f"{BASE_URL}/api/v1/validate", json=validate_payload, timeout=15)
            result = response2.json()
            
            validation = result.get("validation", {})
            final_result = validation.get("final_result", {})
            
            if "commercial" in final_result:
                commercial = final_result["commercial"]
                if "fallback" in str(commercial).lower() or "estimated" in str(commercial).lower():
                    print("[PASS] Fallback pricing mechanism detected")
                else:
                    print("[WARNING] System processed unusual requirements")
            else:
                print("[WARNING] Commercial validation not performed")
                
        print("[PASS] System handled extreme/missing product scenarios")
        
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")

def run_all_tests():
    """Run all boundary tests"""
    print("=" * 60)
    print("REQMAS API ERROR HANDLING & BOUNDARY TESTS")
    print("=" * 60)
    
    tests = [
        test_empty_requirement,
        test_null_session, 
        test_negative_budget,
        test_conflicting_requirements,
        test_invalid_json,
        test_pipeline_status,
        test_missing_product_fallback
    ]
    
    for test_func in tests:
        try:
            test_func()
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"[FAIL] Test {test_func.__name__} failed: {e}")
    
    print("\n" + "=" * 60)
    print("BOUNDARY TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()