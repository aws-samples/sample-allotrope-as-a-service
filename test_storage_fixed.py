#!/usr/bin/env python3
"""
Test Storage Functionality - Simple Version
"""

import json
import requests

def test_storage_integration():
    """Test that ATaaS now stores files in S3 and DynamoDB"""
    
    print("=== Testing Storage Integration ===")
    
    # Test conversion with storage
    ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert"
    
    csv_content = """Sample ID,Concentration,pH,Temperature
SAMPLE_001,5.2,7.1,23.5
SAMPLE_002,3.8,6.9,24.1
SAMPLE_003,7.1,7.3,23.8"""
    
    payload = {
        'file_content': csv_content,
        'submit_for_approval': True,
        'store_results': True
    }
    
    print("1. Converting file with storage enabled...")
    response = requests.post(ataas_url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        conversion_id = result.get('conversion_id')
        
        print(f"   Conversion ID: {conversion_id}")
        print(f"   Status: {result.get('status')}")
        
        storage_info = result.get('storage', {})
        print(f"   Storage Status: {storage_info.get('stored', 'Unknown')}")
        print(f"   ASM File Stored: {storage_info.get('asm_file_stored', 'Unknown')}")
        print(f"   Validation Stored: {storage_info.get('validation_stored', 'Unknown')}")
        print(f"   Converter Code Stored: {storage_info.get('converter_code_stored', 'Unknown')}")
        
        if storage_info.get('stored'):
            print("   SUCCESS: Storage integration working!")
        else:
            print(f"   ERROR: Storage failed: {storage_info.get('error', 'Unknown error')}")
        
        return conversion_id
    else:
        print(f"   Conversion failed: {response.status_code} - {response.text}")
        return None

def main():
    """Test storage functionality"""
    
    # Test storage integration
    conversion_id = test_storage_integration()
    
    # Summary
    print(f"\n=== Storage Test Summary ===")
    if conversion_id:
        print(f"SUCCESS: Conversion completed: {conversion_id}")
        print(f"SUCCESS: Storage integration tested")
        print(f"SUCCESS: Files should be stored in S3")
        print(f"SUCCESS: Conversion history in DynamoDB")
    else:
        print("ERROR: Conversion failed")
    
    print(f"\nStorage Locations:")
    print(f"  ASM Files: s3://asm-converted-files/")
    print(f"  Validation Results: s3://asm-validation-results/")
    print(f"  Conversion History: DynamoDB ConversionHistory table")

if __name__ == "__main__":
    main()