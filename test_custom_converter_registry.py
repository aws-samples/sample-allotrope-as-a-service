"""
Test Custom Converter Registry
"""

import requests
import json

# Deployed endpoints
REGISTER_ENDPOINT = "https://tfv79s08rl.execute-api.us-east-1.amazonaws.com/prod/register"
APPROVE_ENDPOINT = "https://tfv79s08rl.execute-api.us-east-1.amazonaws.com/prod/approve"
UNIFIED_ENDPOINT = "https://tqzatn5bse.execute-api.us-east-1.amazonaws.com/prod/convert"

# Sample converter code
SAMPLE_CONVERTER = """
import json
import csv
import io

def convert(file_content):
    '''Convert sample CSV to ASM'''
    
    reader = csv.DictReader(io.StringIO(file_content))
    rows = list(reader)
    
    if not rows:
        raise Exception("No data found")
    
    # Simple ASM structure
    asm = {
        "$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/REC/2025/06/solution-analyzer.manifest",
        "solution analyzer aggregate document": {
            "data system document": {
                "ASM converter name": "test-converter",
                "ASM converter version": "1.0.0"
            },
            "solution analyzer document": [{
                "measurement aggregate document": {
                    "measurement document": [
                        {
                            "measurement identifier": "test-1",
                            "sample document": {
                                "sample identifier": rows[0].get('Sample ID', 'unknown')
                            }
                        }
                    ]
                }
            }]
        }
    }
    
    return asm
"""

def test_register_converter():
    """Test registering a new converter"""
    
    print("\\n=== Testing Converter Registration ===")
    
    payload = {
        "converter_id": "test-instrument-v1",
        "converter_code": SAMPLE_CONVERTER,
        "vendor": "TEST_VENDOR",
        "model": "TEST_MODEL",
        "instrument_type": "solution_analyzer"
    }
    
    response = requests.post(REGISTER_ENDPOINT, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200

def test_approve_converter():
    """Test approving a converter"""
    
    print("\\n=== Testing Converter Approval ===")
    
    payload = {
        "converter_id": "test-instrument-v1",
        "approved_by": "test-user@example.com"
    }
    
    response = requests.post(APPROVE_ENDPOINT, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200

def test_unified_converter():
    """Test conversion using registered converter"""
    
    print("\\n=== Testing Unified Converter with Custom Converter ===")
    
    # Sample CSV data
    sample_csv = """Sample ID,pH,Temperature
SAMPLE-001,7.2,37.0
SAMPLE-002,7.4,37.0"""
    
    payload = {
        "file_content": sample_csv,
        "file_name": "test.csv",
        "manifest": {
            "vendor": "TEST_VENDOR",
            "model": "TEST_MODEL",
            "instrument_type": "solution_analyzer"
        }
    }
    
    response = requests.post(UNIFIED_ENDPOINT, json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Method: {result.get('method')}")
        print(f"Converter: {result.get('converter_used')}")
        print(f"ASM Output: {json.dumps(result.get('asm_output'), indent=2)[:500]}...")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("Custom Converter Registry Test")
    print("=" * 50)
    print(f"\nREGISTER: {REGISTER_ENDPOINT}")
    print(f"APPROVE: {APPROVE_ENDPOINT}")
    print(f"UNIFIED: {UNIFIED_ENDPOINT}")
    
    test_register_converter()
    test_approve_converter()
    test_unified_converter()
