"""
Test ATaaS with Wyatt ASTRA XML file
"""
import requests
import json
import base64

# Read the XML file
xml_file = r"C:\app\asm2agent\merck\ASTRA Report BSA - Result Over 2 Lines - EDITED.xml"
with open(xml_file, 'rb') as f:
    file_bytes = f.read()
    # Try to decode with different encodings
    try:
        file_content = file_bytes.decode('utf-8')
    except:
        file_content = file_bytes.decode('latin-1')

print(f"File size: {len(file_content)} bytes")
print(f"File type: XML")
print(f"Instrument: Wyatt ASTRA (SEC-MALS)")
print()

# ATaaS endpoint
ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert"

# Prepare request
payload = {
    "file_content": file_content,
    "file_name": "ASTRA Report BSA - Result Over 2 Lines - EDITED.xml"
}

print("Sending to ATaaS...")
print("=" * 80)

try:
    response = requests.post(ataas_url, json=payload, timeout=180)
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ SUCCESS!")
        print()
        
        # Show analysis
        if 'analysis' in result:
            print("AI Analysis:")
            print("-" * 80)
            print(result['analysis'])
            print()
        
        # Show ASM output size
        if 'asm_output' in result:
            asm_size = len(json.dumps(result['asm_output']))
            print(f"ASM Output Size: {asm_size} bytes")
            print()
        
        # Show converter code size
        if 'converter_code' in result:
            converter_size = len(result['converter_code'])
            print(f"Converter Code Size: {converter_size} characters")
            print()
            print("Converter Code Preview:")
            print("-" * 80)
            print(result['converter_code'][:500] + "...")
            print()
        
    else:
        print(f"❌ FAILED: {response.status_code}")
        print(response.text)
        
except requests.exceptions.Timeout:
    print("❌ TIMEOUT: Request exceeded 180 seconds")
    print("This file is too complex for ATaaS to handle in real-time")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
