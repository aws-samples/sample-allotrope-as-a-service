#!/usr/bin/env python3
"""
Extract and Save Generated Converter Code
"""

import json
import requests
from pathlib import Path

def test_and_save_generated_code():
    """Test ATaaS and save the generated converter code"""
    
    # Test with sample CSV data
    csv_content = """Sample ID,Concentration,pH,Temperature
SAMPLE_001,5.2,7.1,23.5
SAMPLE_002,3.8,6.9,24.1
SAMPLE_003,7.1,7.3,23.8"""
    
    # Call ATaaS
    ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert"
    
    payload = {
        'file_content': csv_content,
        'submit_for_approval': True
    }
    
    print("Calling ATaaS to generate converter code...")
    response = requests.post(ataas_url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        
        # Extract converter code
        converter_code = result.get('converter_code', {})
        code = converter_code.get('code', '')
        filename = converter_code.get('filename', 'converter.py')
        
        if code:
            # Create output directory
            output_dir = Path("generated_converters")
            output_dir.mkdir(exist_ok=True)
            
            # Save the generated code
            code_file = output_dir / filename
            with open(code_file, 'w') as f:
                f.write(code)
            
            print(f"Generated converter saved to: {code_file}")
            print(f"File size: {len(code)} characters")
            
            # Also save metadata
            metadata = {
                'conversion_id': result.get('conversion_id'),
                'timestamp': result.get('timestamp'),
                'file_analysis': result.get('file_analysis'),
                'converter_info': converter_code,
                'approval_workflow': result.get('approval_workflow')
            }
            
            metadata_file = output_dir / f"{filename}.metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Metadata saved to: {metadata_file}")
            
            # Show the generated code
            print(f"\n=== Generated Converter Code ===")
            print(f"Filename: {filename}")
            print(f"Language: {converter_code.get('language')}")
            print(f"\nCode Preview (first 500 chars):")
            print("-" * 50)
            print(code[:500] + "..." if len(code) > 500 else code)
            print("-" * 50)
            
            return code_file, metadata_file
        else:
            print("No converter code found in response")
            return None, None
    else:
        print(f"ATaaS call failed: {response.status_code} - {response.text}")
        return None, None

def test_json_converter():
    """Test with JSON data to get different converter"""
    
    json_content = {
        "instrument": "PlateReader_Test",
        "run_id": "RUN_001",
        "timestamp": "2024-12-22T14:30:00Z",
        "wells": [
            {"well": "A1", "absorbance": 1.234, "wavelength": 450},
            {"well": "A2", "absorbance": 0.987, "wavelength": 450}
        ]
    }
    
    # Call ATaaS
    ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert"
    
    payload = {
        'file_content': json.dumps(json_content, indent=2),
        'submit_for_approval': True
    }
    
    print("\nGenerating JSON converter...")
    response = requests.post(ataas_url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        converter_code = result.get('converter_code', {})
        code = converter_code.get('code', '')
        filename = converter_code.get('filename', 'json_converter.py')
        
        if code:
            output_dir = Path("generated_converters")
            code_file = output_dir / filename
            
            with open(code_file, 'w') as f:
                f.write(code)
            
            print(f"JSON converter saved to: {code_file}")
            return code_file
    
    return None

def main():
    """Generate and save converter codes"""
    
    print("=== Generating and Saving Converter Code ===")
    
    # Test CSV converter
    csv_file, metadata_file = test_and_save_generated_code()
    
    # Test JSON converter  
    json_file = test_json_converter()
    
    # List all generated files
    output_dir = Path("generated_converters")
    if output_dir.exists():
        print(f"\n=== Generated Files ===")
        for file in output_dir.iterdir():
            print(f"  {file.name} ({file.stat().st_size} bytes)")
        
        print(f"\nAll files saved in: {output_dir.absolute()}")
    
    # Show how to use the generated converter
    if csv_file and csv_file.exists():
        print(f"\n=== How to Use Generated Converter ===")
        print(f"1. Save your CSV data to a file (e.g., 'data.csv')")
        print(f"2. Run: python {csv_file} data.csv")
        print(f"3. The converter will output ASM JSON format")

if __name__ == "__main__":
    main()