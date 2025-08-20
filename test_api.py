"""Simple test script to check API endpoints"""
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"

print("Testing reqMAS API...")
print("-" * 50)

# Test 1: Health endpoint
print("\n1. Testing Health Endpoint (/health):")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 2: List all available endpoints
print("\n2. Testing root endpoint (/):")
try:
    response = requests.get(BASE_URL)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 404:
        print("   Root endpoint not found (this is normal)")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 3: Process endpoint with sample data
print("\n3. Testing Process Endpoint (/process):")
test_data = {
    "input": "I need 16 digital inputs and 8 analog outputs",
    "session_id": "test123"
}

try:
    response = requests.post(
        f"{BASE_URL}/process",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 500:
        print(f"   Error Response: {response.text}")
    else:
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "-" * 50)
print("Test complete!")