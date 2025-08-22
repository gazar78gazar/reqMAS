"""
Quick Diagnostic to see actual API response
"""

import requests
import json

def quick_check():
    """Quick check of API response structure"""
    response = requests.post(
        "http://localhost:8000/process",
        json={"input": "I need 4 temperature sensors", "session_id": "diagnostic"}
    )
    
    print("="*60)
    print("QUICK DIAGNOSTIC")
    print("="*60)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print("\nResponse structure:")
        print(json.dumps(data, indent=2))
        
        # Check key paths
        print("\n[KEY PATHS]")
        
        # Direct path
        if "routing" in data:
            print("✓ Direct: data['routing'] exists")
        else:
            print("✗ Direct: data['routing'] NOT found")
        
        # Nested path
        if "result" in data and "routing" in data["result"]:
            print("✓ Nested: data['result']['routing'] exists")
        else:
            print("✗ Nested: data['result']['routing'] NOT found")
        
        # Check for specifications
        def find_specs(obj, path=""):
            """Find specifications anywhere in response"""
            if isinstance(obj, dict):
                if "specifications" in obj:
                    specs = obj["specifications"]
                    if isinstance(specs, list) and specs:
                        print(f"✓ Found {len(specs)} specifications at: {path}")
                        return True
                for key, value in obj.items():
                    if find_specs(value, f"{path}['{key}']"):
                        return True
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if find_specs(item, f"{path}[{i}]"):
                        return True
            return False
        
        print("\n[SPECIFICATIONS SEARCH]")
        found = find_specs(data, "data")
        if not found:
            print("✗ No specifications found anywhere in response")
    else:
        print(f"Error: {response.text[:200]}")

if __name__ == "__main__":
    quick_check()