#!/usr/bin/env python3
"""
Simple test client for ASM POC service
"""
import requests
import json
import base64

def test_asm_conversion():
    """Test the ASM conversion service"""
    
    # Sample CSV data (HPLC-like)
    sample_csv = """Time,Concentration,Absorbance,Peak_Area
0.5,0.1,0.234,1250
1.0,0.2,0.456,2340
1.5,0.3,0.678,3120
2.0,0.4,0.890,4560
2.5,0.5,1.123,5780"""
    
    # Encode file data
    file_data_b64 = base64.b64encode(sample_csv.encode()).decode()
    
    # Prepare request
    payload = {
        "filename": "sample_hplc_data.csv",
        "file_data": file_data_b64
    }
    
    # API endpoint (replace with your deployed endpoint)
    api_endpoint = input("Enter your API Gateway endpoint URL: ").strip()
    if not api_endpoint.endswith('/'):
        api_endpoint += '/'
    
    convert_url = f"{api_endpoint}convert"
    health_url = f"{api_endpoint}health"
    
    print("=== ASM POC Test Client ===\n")
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    try:
        health_response = requests.get(health_url)
        print(f"Health Status: {health_response.status_code}")
        print(f"Response: {health_response.json()}\n")
    except Exception as e:
        print(f"Health check failed: {e}\n")
    
    # Test conversion
    print("2. Testing ASM conversion...")
    print(f"Converting file: {payload['filename']}")
    print(f"Sample data preview: {sample_csv[:100]}...\n")
    
    try:
        response = requests.post(
            convert_url,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Conversion successful!")
            print(f"File analyzed as: {result['analysis']['format']}")
            print(f"File size: {result['analysis']['size']} bytes")
            print(f"Generated at: {result['timestamp']}")
            
            # Display ASM output structure
            asm_output = result['asm_output']
            print(f"\n📋 ASM Output Structure:")
            print(f"  Version: {asm_output.get('version')}")
            print(f"  Schema: {asm_output.get('schema')}")
            print(f"  Measurements: {len(asm_output.get('data', {}).get('measurements', []))}")
            print(f"  Samples: {len(asm_output.get('data', {}).get('samples', []))}")
            print(f"  Methods: {len(asm_output.get('data', {}).get('methods', []))}")
            print(f"  Instruments: {len(asm_output.get('data', {}).get('instruments', []))}")
            
            # Save full result
            with open('asm_conversion_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Full result saved to: asm_conversion_result.json")
            
        else:
            print("❌ Conversion failed!")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_asm_conversion()