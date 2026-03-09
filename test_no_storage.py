#!/usr/bin/env python3
"""
Test ATaaS without storage
"""

import json
import requests

def test_without_storage():
    """Test conversion without storage"""
    
    print("=== Testing Conversion Without Storage ===")
    
    ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert"
    
    payload = {
        'file_content': 'Sample,Value\nTest,123',
        'store_results': False
    }
    
    print("Testing conversion...")
    response = requests.post(ataas_url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Conversion ID: {result.get('conversion_id')}")
        print(f"Status: {result.get('status')}")
        print("SUCCESS: Basic conversion working!")
        return True
    else:
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    test_without_storage()