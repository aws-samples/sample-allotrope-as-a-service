#!/usr/bin/env python3
"""
Complete System Test - All Services
"""

import json
import requests

def test_complete_system():
    """Test all services working together"""
    
    print("=== Complete ASM System Test ===")
    
    # Service endpoints
    ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod"
    dvaas_url = "https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod"
    multi_url = "https://6uogqq4zb5.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test data for different instruments
    test_files = {
        'plate_reader': "Well,Absorbance\nA1,0.234\nA2,0.456\nA3,0.789",
        'cell_counter': "Sample,Count,Viability\nSAMPLE_1,150000,95.2\nSAMPLE_2,180000,94.8",
        'solution_analyzer': "Sample,Concentration,pH,Temperature\nSOL_1,5.2,7.1,23.5\nSOL_2,3.8,6.9,24.1"
    }
    
    results = []
    
    # Test each instrument type
    for instrument_type, file_content in test_files.items():
        print(f"\n--- Testing {instrument_type} ---")
        
        # Test multi-instrument service
        response = requests.post(f"{multi_url}/convert", json={
            'file_content': file_content,
            'instrument_type': instrument_type,
            'vendor': 'test_vendor'
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS {instrument_type}: {result['conversion_id']}")
            results.append(result)
        else:
            print(f"ERROR {instrument_type}: {response.status_code}")
    
    # Test ATaaS service
    print(f"\n--- Testing ATaaS ---")
    response = requests.post(f"{ataas_url}/convert", json={
        'file_content': test_files['solution_analyzer'],
        'store_results': True
    })
    
    if response.status_code == 200:
        ataas_result = response.json()
        print(f"SUCCESS ATaaS: {ataas_result['conversion_id']}")
        
        # Test DVaaS validation
        print(f"\n--- Testing DVaaS ---")
        dvaas_response = requests.post(f"{dvaas_url}/validate", json={
            'asm_data': ataas_result['asm_output'],
            'validation_level': 'certification'
        })
        
        if dvaas_response.status_code == 200:
            dvaas_result = dvaas_response.json()
            print(f"SUCCESS DVaaS: {dvaas_result.get('certification', {}).get('status', 'VALIDATED')}")
        else:
            print(f"ERROR DVaaS: {dvaas_response.status_code}")
    else:
        print(f"ERROR ATaaS: {response.status_code}")
    
    # Summary
    print(f"\n=== System Test Summary ===")
    print(f"Multi-Instrument Service: https://6uogqq4zb5.execute-api.us-east-1.amazonaws.com/prod/")
    print(f"ATaaS Service: https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/")
    print(f"DVaaS Service: https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/")
    print(f"Dashboard: file:///C:/app/asm2agent/dashboard/index.html")
    print(f"Conversions completed: {len(results)}")
    
    return results

if __name__ == "__main__":
    test_complete_system()