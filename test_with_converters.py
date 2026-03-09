#!/usr/bin/env python3
"""
Test with Converter Generation and Saving
"""

import json
import requests
import os

def test_with_converters():
    """Test conversion and save converter files"""
    
    print("=== Testing with Converter Generation ===")
    
    # Test files
    test_files = [
        'test_data_plate_reader_tecan.csv',
        'test_data_cell_counter_beckman.csv', 
        'test_data_solution_analyzer_agilent.csv'
    ]
    
    ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod"
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            continue
            
        print(f"\n--- Processing: {file_path} ---")
        
        # Read file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Convert with ATaaS
        response = requests.post(f"{ataas_url}/convert", json={
            'file_content': content,
            'store_results': True
        })
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"Conversion ID: {result['conversion_id']}")
            
            # Save converter code if available
            converter = result.get('converter_code')
            if converter:
                converter_filename = f"converter_{os.path.basename(file_path).replace('.csv', '.py')}"
                
                with open(converter_filename, 'w') as f:
                    f.write(converter['code'])
                
                print(f"Converter saved: {converter_filename}")
                print(f"Language: {converter['language']}")
            else:
                print("No converter code generated")
            
            # Save ASM output
            asm_filename = f"asm_{os.path.basename(file_path).replace('.csv', '.json')}"
            with open(asm_filename, 'w') as f:
                json.dump(result['asm_output'], f, indent=2)
            
            print(f"ASM saved: {asm_filename}")
            
        else:
            print(f"FAILED: {response.status_code}")
    
    print(f"\n=== Files Generated ===")
    print("Source files: test_data_*.csv")
    print("Converter files: converter_*.py") 
    print("ASM files: asm_*.json")

if __name__ == "__main__":
    test_with_converters()