#!/usr/bin/env python3
"""
End-to-End Test Client
Source File → API → ASM File → Validation
"""

import json
import requests
import os
from datetime import datetime

class ASMTestClient:
    def __init__(self):
        self.ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod"
        self.dvaas_url = "https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod"
        self.multi_url = "https://6uogqq4zb5.execute-api.us-east-1.amazonaws.com/prod"
        
    def process_file_complete(self, file_path, instrument_type=None, vendor=None):
        """Complete file processing: Source → ASM → Validation"""
        
        print(f"\n=== Processing: {file_path} ===")
        
        # Read source file
        with open(file_path, 'r') as f:
            source_content = f.read()
        
        print(f"Source file size: {len(source_content)} characters")
        
        # Step 1: Convert to ASM
        if instrument_type:
            # Use multi-instrument service
            convert_response = requests.post(f"{self.multi_url}/convert", json={
                'file_content': source_content,
                'instrument_type': instrument_type,
                'vendor': vendor or 'test_vendor'
            })
        else:
            # Use ATaaS service
            convert_response = requests.post(f"{self.ataas_url}/convert", json={
                'file_content': source_content,
                'store_results': True
            })
        
        if convert_response.status_code != 200:
            print(f"CONVERSION FAILED: {convert_response.status_code}")
            return None
        
        convert_result = convert_response.json()
        asm_output = convert_result['asm_output']
        
        print(f"Conversion ID: {convert_result['conversion_id']}")
        print(f"Detected type: {convert_result.get('instrument_type', convert_result.get('file_analysis', {}).get('instrument_type'))}")
        
        # Step 2: Save ASM file
        asm_filename = f"asm_{os.path.basename(file_path).replace('.csv', '.json')}"
        with open(asm_filename, 'w') as f:
            json.dump(asm_output, f, indent=2)
        
        print(f"ASM file saved: {asm_filename}")
        
        # Step 3: Validate ASM
        validate_response = requests.post(f"{self.dvaas_url}/validate", json={
            'asm_data': asm_output,
            'validation_level': 'certification'
        })
        
        if validate_response.status_code != 200:
            print(f"VALIDATION FAILED: {validate_response.status_code}")
            return None
        
        validate_result = validate_response.json()
        
        print(f"Validation: {'PASSED' if validate_result['valid'] else 'FAILED'}")
        print(f"Errors: {len(validate_result.get('errors', []))}")
        print(f"Warnings: {len(validate_result.get('warnings', []))}")
        
        certification = validate_result.get('certification', {})
        if certification:
            print(f"Certification: {certification.get('status', 'N/A')}")
        
        # Step 4: Save validation results
        validation_filename = f"validation_{os.path.basename(file_path).replace('.csv', '.json')}"
        with open(validation_filename, 'w') as f:
            json.dump(validate_result, f, indent=2)
        
        print(f"Validation saved: {validation_filename}")
        
        return {
            'source_file': file_path,
            'asm_file': asm_filename,
            'validation_file': validation_filename,
            'conversion_result': convert_result,
            'validation_result': validate_result
        }

def main():
    """Run comprehensive tests"""
    
    # Generate test data first
    print("Using existing synthetic test data...")
    # exec(open('generate_test_data.py').read())
    
    client = ASMTestClient()
    results = []
    
    # Test configurations
    test_configs = [
        ('test_data_plate_reader_tecan.csv', 'plate_reader', 'tecan'),
        ('test_data_cell_counter_beckman.csv', 'cell_counter', 'beckman'),
        ('test_data_solution_analyzer_agilent.csv', 'solution_analyzer', 'agilent'),
        ('test_data_hplc_waters.csv', None, None),  # Use ATaaS auto-detect
        ('test_data_mass_spec_thermo.csv', None, None)  # Use ATaaS auto-detect
    ]
    
    print(f"\n{'='*60}")
    print("COMPREHENSIVE ASM TESTING")
    print(f"{'='*60}")
    
    for file_path, instrument_type, vendor in test_configs:
        if os.path.exists(file_path):
            result = client.process_file_complete(file_path, instrument_type, vendor)
            if result:
                results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Files processed: {len(results)}")
    
    for result in results:
        print(f"\nSource: {result['source_file']}")
        print(f"ASM: {result['asm_file']}")
        print(f"Validation: {result['validation_file']}")
        print(f"Status: {'SUCCESS' if result['validation_result']['valid'] else 'FAILED'}")
    
    print(f"\nAll files available in current directory:")
    print("- Source files: test_data_*.csv")
    print("- ASM files: asm_*.json") 
    print("- Validation files: validation_*.json")

if __name__ == "__main__":
    main()