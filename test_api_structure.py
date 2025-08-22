import requests
import json

# Make a simple API call
response = requests.post(
    "http://localhost:8000/process",
    json={
        "user_input": "I need 16 digital inputs and 8 analog outputs",
        "session_id": "structure_test"
    }
)

print("Status Code:", response.status_code)
print("\nFull Response Structure:")
print(json.dumps(response.json(), indent=2))

# Now let's trace the path to each field
data = response.json()
print("\n\nData Access Paths:")
print(f"Top level keys: {list(data.keys())}")

if "result" in data:
    print(f"data['result'] keys: {list(data['result'].keys())}")
    if "routing" in data['result']:
        print(f"data['result']['routing'] keys: {list(data['result']['routing'].keys())}")

if "routing" in data:
    print(f"data['routing'] keys: {list(data['routing'].keys())}")