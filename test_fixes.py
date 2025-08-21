"""
Test the 3 fixes applied to the reqMAS system
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_null_session_fix():
    """Test 1: Null session should default to 'default'"""
    print("\n=== TEST 1: Null Session Fix ===")
    
    payload = {
        "input": "I need 4 analog inputs",
        "session_id": None  # Explicitly pass None
    }
    
    try:
        response = requests.post(f"{BASE_URL}/process", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            session_context = result.get("result", {}).get("session_context", {})
            session_id = session_context.get("session_id", "")
            
            print(f"Session ID received: '{session_id}'")
            
            if session_id == "default":
                print("[PASS] Null session correctly defaulted to 'default'")
                return True
            else:
                print(f"[FAIL] Expected 'default', got '{session_id}'")
                return False
        else:
            print(f"[FAIL] Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")
        return False

def test_negative_budget_validation():
    """Test 2: Negative budget should return validation error"""
    print("\n=== TEST 2: Negative Budget Validation ===")
    
    # First create a session with requirements
    setup_payload = {
        "input": "I need 4 analog inputs and 2 digital outputs",
        "session_id": "test_negative_budget_fix"
    }
    
    try:
        # Create session
        requests.post(f"{BASE_URL}/process", json=setup_payload, timeout=10)
        
        # Test validation with negative budget
        validate_payload = {
            "session_id": "test_negative_budget_fix",
            "budget": -1000,
            "user_profile": {"expertise": "intermediate"}
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/validate", json=validate_payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            validation = result.get("validation", {})
            final_result = validation.get("final_result", {})
            commercial = final_result.get("commercial", {})
            budget_validation = commercial.get("budget_validation", {})
            
            error_msg = budget_validation.get("error", "")
            within_budget = budget_validation.get("within_budget", True)
            
            print(f"Within budget: {within_budget}")
            print(f"Error message: {error_msg}")
            
            if not within_budget and "negative" in error_msg.lower():
                print("[PASS] Negative budget properly rejected with error message")
                return True
            else:
                print("[FAIL] Negative budget not properly handled")
                return False
        else:
            print(f"[FAIL] Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")
        return False

def test_io_limit_validation():
    """Test 3: I/O count > 256 should return validation error"""
    print("\n=== TEST 3: I/O Limit Validation ===")
    
    payload = {
        "input": "I need 999 analog inputs and 999 digital outputs",
        "session_id": "test_io_limit_fix"
    }
    
    try:
        # Process the extreme requirements
        response = requests.post(f"{BASE_URL}/process", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Now validate
            validate_payload = {
                "session_id": "test_io_limit_fix",
                "budget": 100000,
                "user_profile": {"expertise": "expert"}
            }
            
            val_response = requests.post(f"{BASE_URL}/api/v1/validate", json=validate_payload, timeout=10)
            
            if val_response.status_code == 200:
                result = val_response.json()
                validation = result.get("validation", {})
                final_result = validation.get("final_result", {})
                technical = final_result.get("technical", {})
                
                valid = technical.get("valid", True)
                error = technical.get("error", "")
                io_requirements = technical.get("io_requirements", {})
                
                print(f"Technical valid: {valid}")
                print(f"Error message: {error}")
                print(f"Total I/O: {io_requirements.get('total_io', 0)}")
                
                if not valid and "exceeds maximum of 256" in error:
                    print("[PASS] I/O limit properly enforced with error message")
                    return True
                else:
                    print("[FAIL] I/O limit not properly enforced")
                    return False
            else:
                print(f"[FAIL] Validation failed with status {val_response.status_code}")
                return False
        else:
            print(f"[FAIL] Process failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Request failed: {e}")
        return False

def run_fix_tests():
    """Run all fix verification tests"""
    print("=" * 60)
    print("TESTING FIXES APPLIED TO REQMAS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Null session fix
    results.append(("Null session handling", test_null_session_fix()))
    time.sleep(1)
    
    # Test 2: Negative budget validation
    results.append(("Negative budget validation", test_negative_budget_validation()))
    time.sleep(1)
    
    # Test 3: I/O limit validation
    results.append(("I/O count limit check", test_io_limit_validation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("FIX VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    for fix_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{fix_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} fixes verified")
    
    if passed == len(results):
        print("\nALL FIXES SUCCESSFULLY APPLIED AND VERIFIED!")
    else:
        print(f"\n{len(results) - passed} fixes need attention")

if __name__ == "__main__":
    run_fix_tests()