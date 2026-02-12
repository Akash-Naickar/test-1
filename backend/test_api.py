
import requests
import json

url = "http://127.0.0.1:8000/explain"

payload = {
    "code_snippet": "def retry_payment():\n    # Implement retry logic\n    pass",
    "file_path": "backend/payment.py",
    "line_numbers": "10-15"
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("Success! /explain Response:")
        print(response.json())
    else:
        print(f"Failed /explain with status {response.status_code}:")
        print(response.text)

    # Test /context/retrieve
    retrieve_url = "http://127.0.0.1:8000/context/retrieve"
    print(f"\nSending request to {retrieve_url}...")
    response = requests.post(retrieve_url, json=payload)
    
    if response.status_code == 200:
        print("Success! /context/retrieve Response:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Failed /context/retrieve with status {response.status_code}:")
        print(response.text)

except Exception as e:
    print(f"Error: {e}")
