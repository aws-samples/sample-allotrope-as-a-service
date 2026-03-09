#!/usr/bin/env python3
"""
Test Script for Three Scenarios
"""

import json
import requests

def test_1_unknown_format():
    """Test 1: Convert new file with unknown format"""
    
    print("=== Test 1: Unknown Format Conversion ===")
    
    # Create unknown format data (tab-separated with unusual headers)
    unknown_data = """Timestamp\tReading\tStatus\tNotes
2024-01-01T10:00:00\t123.45\tOK\tBaseline measurement
2024-01-01T10:05:00\t125.67\tOK\tSample A
2024-01-01T10:10:00\t127.89\tWARN\tSample B - check calibration"""
    
    # Send to ATaaS (handles unknown formats)
    response = requests.post('https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert', json={
        'file_content': unknown_data,
        'store_results': True
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"SUCCESS: Converted unknown format")
        print(f"Conversion ID: {result['conversion_id']}")
        print(f"Detected as: {result['file_analysis']['format']}")
        return result
    else:
        print(f"FAILED: {response.status_code} - {response.text}")
        return None

def test_2_validate_converted():
    """Test 2: Validate converted file"""
    
    print("\n=== Test 2: Validate Converted File ===")
    
    # First convert a file
    csv_data = "Sample,Value,Unit\nTEST_001,42.5,mg/L\nTEST_002,38.1,mg/L"
    
    convert_response = requests.post('https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert', json={
        'file_content': csv_data
    })
    
    if convert_response.status_code == 200:
        convert_result = convert_response.json()
        asm_output = convert_result['asm_output']
        
        # Now validate the converted ASM
        validate_response = requests.post('https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate', json={
            'asm_data': asm_output,
            'validation_level': 'certification'
        })
        
        if validate_response.status_code == 200:
            validate_result = validate_response.json()
            print(f"SUCCESS: Validation completed")
            print(f"Valid: {validate_result['valid']}")
            print(f"Certification: {validate_result.get('certification', {}).get('status', 'N/A')}")
            return validate_result
        else:
            print(f"VALIDATION FAILED: {validate_response.status_code}")
    else:
        print(f"CONVERSION FAILED: {convert_response.status_code}")
    
    return None

def test_3_validate_existing_asm():
    """Test 3: Validate existing ASM file"""
    
    print("\n=== Test 3: Validate Existing ASM ===")
    
    # Create a valid ASM structure
    existing_asm = {
        "$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/BENCHLING/2023/09/solution-analyzer.manifest",
        "measurement document": [
            {
                "measurement identifier": "EXISTING_001",
                "measurement time": "2024-12-23T15:30:00Z",
                "processed data document": {
                    "concentration": 5.2,
                    "pH": 7.1,
                    "temperature": 25.0
                }
            },
            {
                "measurement identifier": "EXISTING_002", 
                "measurement time": "2024-12-23T15:35:00Z",
                "processed data document": {
                    "concentration": 4.8,
                    "pH": 7.0,
                    "temperature": 25.2
                }
            }
        ]
    }
    
    # Validate the existing ASM
    response = requests.post('https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate', json={
        'asm_data': existing_asm,
        'validation_level': 'certification'
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"SUCCESS: Existing ASM validated")
        print(f"Valid: {result['valid']}")
        print(f"Errors: {len(result.get('errors', []))}")
        print(f"Warnings: {len(result.get('warnings', []))}")
        print(f"Certification: {result.get('certification', {}).get('status', 'N/A')}")
        return result
    else:
        print(f"FAILED: {response.status_code} - {response.text}")
        return None

def main():
    """Run all three tests"""
    
    print("ASM System - Three Test Scenarios")
    print("=" * 50)
    
    # Run tests
    test_1_unknown_format()
    test_2_validate_converted() 
    test_3_validate_existing_asm()
    
    print("\n" + "=" * 50)
    print("Test Instructions:")
    print("1. Unknown Format: Send any text file to ATaaS /convert")
    print("2. Validate Converted: Send ASM output from step 1 to DVaaS /validate")
    print("3. Validate Existing: Send pre-made ASM JSON to DVaaS /validate")
    print("\nAPI Endpoints:")
    print("ATaaS: https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert")
    print("DVaaS: https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate")

if __name__ == "__main__":
    main()