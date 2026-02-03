#!/usr/bin/env python3
"""
Test client for autonomous ATaaS and DVaaS services
"""

import json
import requests
import time

class AutonomousServicesClient:
    def __init__(self, ataas_url, dvaas_url):
        self.ataas_url = ataas_url.rstrip('/')
        self.dvaas_url = dvaas_url.rstrip('/')
    
    def test_dvaas_health(self):
        """Test DVaaS health endpoint"""
        try:
            response = requests.get(f"{self.dvaas_url}/health")
            print(f"DVaaS Health: {response.status_code} - {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"DVaaS Health Error: {e}")
            return False
    
    def test_ataas_health(self):
        """Test ATaaS health endpoint"""
        try:
            response = requests.get(f"{self.ataas_url}/health")
            print(f"ATaaS Health: {response.status_code} - {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"ATaaS Health Error: {e}")
            return False
    
    def validate_asm(self, asm_data, validation_level="basic"):
        """Test DVaaS validation"""
        try:
            response = requests.post(
                f"{self.dvaas_url}/validate",
                json={
                    "asm_data": asm_data,
                    "validation_level": validation_level
                }
            )
            
            print(f"DVaaS Validation: {response.status_code}")
            result = response.json()
            print(f"Valid: {result.get('valid')}")
            
            if result.get('errors'):
                print("Errors:")
                for error in result['errors']:
                    print(f"  - {error['field']}: {error['message']}")
            
            if result.get('certification'):
                print(f"Certification: {result['certification']['status']}")
            
            return result
            
        except Exception as e:
            print(f"DVaaS Validation Error: {e}")
            return None
    
    def convert_file(self, file_content):
        """Test ATaaS conversion with code generation"""
        try:
            response = requests.post(
                f"{self.ataas_url}/convert",
                json={"file_content": file_content}
            )
            
            print(f"ATaaS Conversion: {response.status_code}")
            result = response.json()
            
            print(f"Conversion ID: {result.get('conversion_id')}")
            print(f"Status: {result.get('status')}")
            
            # Show file analysis
            analysis = result.get('file_analysis', {})
            print(f"Detected Format: {analysis.get('format')}")
            print(f"Instrument Type: {analysis.get('instrument_type')}")
            
            # Show ASM output
            asm_output = result.get('asm_output')
            if asm_output:
                print(f"ASM Manifest: {asm_output.get('$asm.manifest')}")
                measurements = asm_output.get('measurement document', [])
                print(f"Measurements: {len(measurements)}")
            
            # Show generated converter code
            converter = result.get('converter_code')
            if converter:
                print(f"Generated Converter: {converter.get('language')} - {converter.get('filename')}")
                print("Code preview:")
                print(converter.get('code', '')[:200] + "...")
            
            # Show validation result
            validation = result.get('validation', {})
            print(f"Validation: {'PASSED' if validation.get('valid') else 'FAILED'}")
            
            return result
            
        except Exception as e:
            print(f"ATaaS Conversion Error: {e}")
            return None

def main():
    """Test autonomous services"""
    
    # Service URLs (update with actual deployed endpoints)
    ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod"
    dvaas_url = "https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod"
    
    client = AutonomousServicesClient(ataas_url, dvaas_url)
    
    print("=== Testing Autonomous Services ===\n")
    
    # Test health endpoints
    print("1. Health Checks:")
    dvaas_healthy = client.test_dvaas_health()
    ataas_healthy = client.test_ataas_health()
    
    if not (dvaas_healthy and ataas_healthy):
        print("Services not healthy, exiting...")
        return
    
    print("\n2. Testing DVaaS Validation:")
    
    # Test valid ASM
    valid_asm = {
        "$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/BENCHLING/2023/09/solution-analyzer.manifest",
        "measurement document": [{
            "measurement identifier": "TEST_001",
            "measurement time": "2024-12-01T10:00:00Z",
            "processed data document": {
                "concentration": 5.2,
                "pH": 7.1
            }
        }]
    }
    
    client.validate_asm(valid_asm, "certification")
    
    print("\n3. Testing ATaaS Conversion:")
    
    # Test CSV conversion
    csv_content = """Sample ID,Concentration,pH,Temperature
SAMPLE_001,5.2,7.1,23.5
SAMPLE_002,3.8,6.9,24.1
SAMPLE_003,7.1,7.3,23.8"""
    
    result = client.convert_file(csv_content)
    
    if result and result.get('converter_code'):
        print(f"\n4. Generated Converter Code:")
        converter = result['converter_code']
        print(f"Language: {converter['language']}")
        print(f"Filename: {converter['filename']}")
        print("Full code:")
        print(converter['code'])

if __name__ == "__main__":
    main()