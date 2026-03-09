#!/usr/bin/env python3
"""
Test the Generated Converter Code
"""

import json
from pathlib import Path

def test_generated_converter():
    """Test the generated CSV converter"""
    
    # Create test CSV data
    test_csv = Path("test_data.csv")
    csv_content = """Sample ID,Concentration,pH,Temperature
SAMPLE_001,5.2,7.1,23.5
SAMPLE_002,3.8,6.9,24.1
SAMPLE_003,7.1,7.3,23.8
SAMPLE_004,4.5,7.0,24.0"""
    
    with open(test_csv, 'w') as f:
        f.write(csv_content)
    
    print("Created test CSV file:")
    print(csv_content)
    
    # Find the generated converter
    converter_dir = Path("generated_converters")
    csv_converters = list(converter_dir.glob("csv_converter_*.py"))
    
    if csv_converters:
        converter_file = csv_converters[0]
        print(f"\nUsing converter: {converter_file}")
        
        # Import and run the converter
        import sys
        sys.path.append(str(converter_dir))
        
        # Import the converter module
        module_name = converter_file.stem
        spec = __import__(module_name)
        
        # Run the conversion
        result = spec.convert_to_asm(str(test_csv))
        
        # Save ASM output
        asm_file = Path("converted_output.json")
        with open(asm_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\nASM output saved to: {asm_file}")
        print(f"Generated {len(result['measurement document'])} measurements")
        
        # Show first measurement
        if result['measurement document']:
            first_measurement = result['measurement document'][0]
            print(f"\nFirst measurement:")
            print(f"  ID: {first_measurement['measurement identifier']}")
            print(f"  Time: {first_measurement['measurement time']}")
            print(f"  Data: {first_measurement['processed data document'][0]}")
        
        # Cleanup
        test_csv.unlink()
        
        return asm_file
    else:
        print("No CSV converter found. Run extract_generated_code.py first.")
        return None

if __name__ == "__main__":
    test_generated_converter()