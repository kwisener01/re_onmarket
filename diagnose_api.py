"""
Diagnostic script to inspect actual Zillow API responses
This will help us fix the field extraction bug
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import http.client
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ZILLOW_API_KEY')
api_host = "zillow-working-api.p.rapidapi.com"

# Test address
address = "2598 Hencley Cir SW, Marietta, GA 30008"

print(f"Testing API with address: {address}")
print(f"API Host: {api_host}\n")

try:
    conn = http.client.HTTPSConnection(api_host)

    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host
    }

    # Encode address
    encoded_address = address.replace(" ", "%20").replace(",", "%2C")
    endpoint = f"/pro/byaddress?propertyaddress={encoded_address}"

    print(f"Endpoint: {endpoint}\n")
    print("Making API request...\n")

    conn.request("GET", endpoint, headers=headers)
    response = conn.getresponse()
    data = response.read()

    print(f"Status Code: {response.status}\n")

    if response.status == 200:
        json_data = json.loads(data.decode('utf-8'))

        # Pretty print the entire response
        print("="*80)
        print("FULL API RESPONSE:")
        print("="*80)
        print(json.dumps(json_data, indent=2))
        print("\n" + "="*80)

        # Save to file for inspection
        with open('api_response_sample.json', 'w') as f:
            json.dump(json_data, f, indent=2)
        print("\n✅ Response saved to: api_response_sample.json")

        # Try to identify key fields
        print("\n" + "="*80)
        print("ANALYZING STRUCTURE:")
        print("="*80)

        def find_keys_recursive(obj, prefix=""):
            """Recursively find all keys in the JSON"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (str, int, float, bool)):
                        print(f"{full_key}: {value}")
                    elif isinstance(value, dict):
                        print(f"{full_key}: {{...}}")
                        find_keys_recursive(value, full_key)
                    elif isinstance(value, list) and value:
                        print(f"{full_key}: [...] (length: {len(value)})")
                        if isinstance(value[0], dict):
                            find_keys_recursive(value[0], f"{full_key}[0]")

        find_keys_recursive(json_data)

    else:
        print(f"❌ Error: HTTP {response.status}")
        print(data.decode('utf-8'))

except Exception as e:
    print(f"❌ Exception: {e}")
