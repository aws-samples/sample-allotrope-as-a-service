#!/usr/bin/env python3
"""
Minimal test for ATaaS conversion
"""

import json
import requests

def test_basic_conversion():
    """Test basic conversion without storage"""
    
    print("=== Testing Basic Conversion ===")
    
    ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert"
    
    payload = {
        'file_content': 'Sample,Value\nTest,123',
        'store_results': False  # Disable storage for now
    }
    
    print("Testing basic conversion...")
    response = requests.post(ataas_url, json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    test_basic_conversion()