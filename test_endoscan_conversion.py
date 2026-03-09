"""
Test EndoScan-V XML Conversion
Converts endotoxin testing XML file to ASM format
"""

import requests
import json

# Multi-Instrument Service endpoint
MULTI_INSTRUMENT_URL = "https://6uogqq4zb5.execute-api.us-east-1.amazonaws.com/prod/convert"

# Read XML file
with open("merck/EndoScanV-Export-20230713115550.xml", "r", encoding="utf-8") as f:
    xml_content = f.read()

# Prepare request
payload = {
    "file_content": xml_content,
    "file_name": "EndoScanV-Export-20230713115550.xml",
    "file_type": "xml"
}

print("Converting EndoScan-V XML file...")
print(f"File size: {len(xml_content)} bytes")
print(f"Endpoint: {MULTI_INSTRUMENT_URL}")
print()

# Call Multi-Instrument service
try:
    response = requests.post(MULTI_INSTRUMENT_URL, json=payload, timeout=60)
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        
        print("=== CONVERSION RESULT ===")
        print(f"Success: {result.get('success', False)}")
        print(f"Vendor: {result.get('vendor', 'Unknown')}")
        print(f"Instrument: {result.get('instrument_type', 'Unknown')}")
        print(f"Converter: {result.get('converter_used', 'Unknown')}")
        print()
        
        if result.get('success'):
            asm_data = result.get('asm_data', {})
            
            # Save ASM output
            output_file = "merck/EndoScanV-Export-20230713115550_ASM.json"
            with open(output_file, "w") as f:
                json.dump(asm_data, f, indent=2)
            
            print(f"[PASS] ASM file saved: {output_file}")
            print()
            
            # Display summary
            manifest = asm_data.get('$asm.manifest', 'N/A')
            print(f"Manifest: {manifest}")
            
            # Count measurements
            for key in asm_data.keys():
                if 'aggregate document' in key.lower():
                    print(f"Technique: {key}")
                    
        else:
            print(f"[FAIL] Conversion failed: {result.get('error', 'Unknown error')}")
            print(f"Message: {result.get('message', 'N/A')}")
            
    else:
        print(f"✗ HTTP Error: {response.text}")
        
except Exception as e:
    print(f"[ERROR] Exception: {str(e)}")
