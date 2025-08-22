import requests
import json
import time

def test_with_diagnostics():
    """Test the API with diagnostic output."""
    print("\n" + "="*60)
    print("STARTING DIAGNOSTIC TEST")
    print("="*60)
    
    url = "http://localhost:8000/process"
    
    test_data = {
        "input": "I need a simple monitoring system for 4 temperature sensors in my warehouse. They're analog RTD sensors, normal indoor environment. What's the cheapest option? My budget is under $1000",
        "session_id": f"diagnostic_test_{int(time.time())}"
    }
    
    print(f"Sending request to: {url}")
    print(f"Session ID: {test_data['session_id']}")
    print(f"Input preview: {test_data['input'][:50]}...")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=test_data, timeout=60)
        elapsed = time.time() - start_time
        
        print(f"\nResponse received in {elapsed:.2f}s")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse structure:")
            print(f"  - Keys: {list(data.keys())}")
            print(f"  - Has result: {'result' in data}")
            
            if 'result' in data:
                result = data['result']
                print(f"  - Result keys: {list(result.keys())}")
                print(f"  - Has conversational_response: {'conversational_response' in result}")
                
                if 'conversational_response' in result:
                    print(f"  - Response: '{result['conversational_response']}'")
                else:
                    print("  - ERROR: conversational_response MISSING in result")
            
            # Save full response for analysis
            with open('diagnostic_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\nFull response saved to: diagnostic_response.json")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"ERROR: Request timed out after 60 seconds")
    except Exception as e:
        print(f"ERROR: Error: {e}")
    
    print("="*60)
    print("DIAGNOSTIC TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_with_diagnostics()