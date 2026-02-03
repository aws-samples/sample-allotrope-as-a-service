#!/usr/bin/env python3
"""
Simple health test for deployed services
"""

import requests

def test_health():
    """Test health endpoints"""
    
    ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod"
    dvaas_url = "https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod"
    
    print("Testing DVaaS Health...")
    try:
        response = requests.get(f"{dvaas_url}/health")
        print(f"DVaaS: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"DVaaS Error: {e}")
    
    print("\nTesting ATaaS Health...")
    try:
        response = requests.get(f"{ataas_url}/health")
        print(f"ATaaS: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"ATaaS Error: {e}")
    
    print("\nTesting DVaaS Validation...")
    try:
        test_data = {
            "asm_data": {
                "$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/BENCHLING/2023/09/solution-analyzer.manifest",
                "measurement document": [{
                    "measurement identifier": "TEST_001"
                }]
            }
        }
        response = requests.post(f"{dvaas_url}/validate", json=test_data)
        print(f"DVaaS Validate: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"DVaaS Validate Error: {e}")

if __name__ == "__main__":
    test_health()