"""
Test to verify all_specs is being passed through Phase 2
"""

import requests
import json

def test_allspecs():
    """Test that specifications are accumulated and passed to Phase 2"""
    
    print("="*60)
    print("TESTING ALL_SPECS PASS-THROUGH")
    print("="*60)
    
    session_id = "allspecs_test"
    
    # Test 1: Send a request with specifications
    print("\n[TEST 1] Sending request with specifications...")
    response = requests.post(
        "http://localhost:8000/process",
        json={
            "input": "I need 4 temperature sensors",
            "session_id": session_id
        }
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Look for specs in the response
        def find_specs_count(obj, path=""):
            """Find and count specifications"""
            if isinstance(obj, dict):
                if "specifications" in obj and isinstance(obj["specifications"], list):
                    count = len(obj["specifications"])
                    if count > 0:
                        print(f"  Found {count} specifications at: {path}")
                        return count
                
                for key, value in obj.items():
                    result = find_specs_count(value, f"{path}/{key}")
                    if result:
                        return result
            return 0
        
        spec_count = find_specs_count(data)
        
        # Check conversational response
        conv_response = data.get("result", {}).get("conversational_response", "")
        if not conv_response:
            conv_response = data.get("conversational_response", "")
        
        # Handle potential encoding issues
        try:
            print(f"\nResponse preview: {conv_response[:150]}...")
        except UnicodeEncodeError:
            # Fallback to ASCII-safe output
            safe_response = conv_response.encode('ascii', 'ignore').decode('ascii')
            print(f"\nResponse preview (ascii): {safe_response[:150]}...")
        
        if "Based on your requirements" in conv_response:
            print("[SUCCESS] Phase 2 is generating contextual responses!")
            print("[SUCCESS] all_specs is being passed through correctly!")
        elif "I'm ready to help" in conv_response:
            print("[FAIL] Still getting generic response")
            print("[FAIL] Check server logs for:")
            print("   - [SPECS] messages showing spec counts")
            print("   - [PHASE2] messages showing if Phase 2 runs")
            print("   - [DecisionCoord] messages showing specs received")
        else:
            print("[INFO] Unknown response type")
    
    print("\n" + "="*60)
    print("CHECK SERVER LOGS FOR DETAILED DEBUG OUTPUT")
    print("="*60)
    print("\nLook for these key messages:")
    print("1. [AGENT] io_expert: X specs")
    print("2. [SPECS] Total current turn specs: X")
    print("3. [PHASE2] all_specs count: X")
    print("4. [DecisionCoord] Received X specifications")
    print("5. [ValidationPipeline] ENTER validate")
    print("6. [ValidationPipeline] Specifications count: X")

if __name__ == "__main__":
    test_allspecs()