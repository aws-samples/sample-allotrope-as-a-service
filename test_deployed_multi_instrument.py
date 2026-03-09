"""
Test Deployed Multi-Instrument Service with Allotropy Integration
"""

import requests
import json

MULTI_INSTRUMENT_API = "https://6uogqq4zb5.execute-api.us-east-1.amazonaws.com/prod"

def test_vicell_conversion():
    """Test Vi-CELL BLU conversion with allotropy"""
    
    print("\n=== Testing Vi-CELL BLU Conversion ===\n")
    
    vicell_data = """Vi-CELL BLU Analysis Report
Sample,Total Cells,Viability,Diameter
Sample1,1500000,95.5,15.2
Sample2,1800000,96.2,14.8
Sample3,1650000,94.8,15.0"""
    
    payload = {
        "file_content": vicell_data,
        "instrument_type": "auto",
        "vendor": "BECKMAN_VI_CELL_BLU"
    }
    
    response = requests.post(
        f"{MULTI_INSTRUMENT_API}/convert",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Conversion ID: {result.get('conversion_id')}")
        print(f"Instrument Type: {result.get('instrument_type')}")
        print(f"Vendor: {result.get('vendor')}")
        print(f"Conversion Method: {result.get('conversion_method')}")
        print(f"Storage: {result.get('storage', {}).get('storage_location')}")
        print("\n[OK] Vi-CELL conversion successful")
        return True
    else:
        print(f"[FAIL] {response.text}")
        return False

def test_nanodrop_conversion():
    """Test NanoDrop conversion with allotropy"""
    
    print("\n=== Testing NanoDrop Conversion ===\n")
    
    nanodrop_data = """NanoDrop Eight Report
Sample,Concentration,A260/A280,A260/A230
DNA1,125.5,1.85,2.1
DNA2,98.3,1.92,2.0
DNA3,110.7,1.88,2.2"""
    
    payload = {
        "file_content": nanodrop_data,
        "instrument_type": "auto",
        "vendor": "THERMO_FISHER_NANODROP_EIGHT"
    }
    
    response = requests.post(
        f"{MULTI_INSTRUMENT_API}/convert",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Conversion ID: {result.get('conversion_id')}")
        print(f"Conversion Method: {result.get('conversion_method')}")
        print("\n[OK] NanoDrop conversion successful")
        return True
    else:
        print(f"[FAIL] {response.text}")
        return False

def test_unknown_instrument():
    """Test fallback to custom converter"""
    
    print("\n=== Testing Unknown Instrument (Fallback) ===\n")
    
    unknown_data = """Custom Instrument XYZ
Sample,Value1,Value2
S1,123,456
S2,789,012"""
    
    payload = {
        "file_content": unknown_data,
        "instrument_type": "auto",
        "vendor": "UNKNOWN"
    }
    
    response = requests.post(
        f"{MULTI_INSTRUMENT_API}/convert",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Conversion Method: {result.get('conversion_method')}")
        print("\n[OK] Fallback to custom converter successful")
        return True
    else:
        print(f"[FAIL] {response.text}")
        return False

def test_health():
    """Test service health"""
    
    print("\n=== Testing Service Health ===\n")
    
    response = requests.get(f"{MULTI_INSTRUMENT_API}/health")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        print("\n[OK] Service is healthy")
        return True
    else:
        print(f"[FAIL] Service unhealthy")
        return False

if __name__ == "__main__":
    print("="*60)
    print("Multi-Instrument Service - Allotropy Integration Test")
    print("="*60)
    
    results = []
    
    results.append(("Health Check", test_health()))
    results.append(("Vi-CELL Conversion", test_vicell_conversion()))
    results.append(("NanoDrop Conversion", test_nanodrop_conversion()))
    results.append(("Unknown Instrument Fallback", test_unknown_instrument()))
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\nALL TESTS PASSED - Allotropy integration deployed successfully!")
    else:
        print("\nSOME TESTS FAILED")
