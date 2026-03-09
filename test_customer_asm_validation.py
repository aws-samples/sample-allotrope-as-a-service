"""
Test customer-provided ASM file through DVaaS
"""
import requests
import json

dvaas_url = "https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate"

# Customer-provided ASM file
customer_file = r"C:\app\asm2agent\merck\SampleResults2025-November-1.json"

print("Testing customer-provided ASM file through DVaaS")
print("=" * 80)

with open(customer_file, 'r') as f:
    asm_data = json.load(f)

print(f"File: {customer_file}")
print(f"Manifest: {asm_data.get('$asm.manifest', 'MISSING')}")
print(f"Top-level keys: {list(asm_data.keys())}")
print()

payload = {
    "asm_data": asm_data,
    "validation_level": "comprehensive"
}

response = requests.post(dvaas_url, json=payload, timeout=30)

print(f"Status Code: {response.status_code}")
print()

if response.status_code == 200:
    result = response.json()
    
    print(f"Valid: {result.get('valid')}")
    print(f"Validator: {result.get('validator', 'unknown')}")
    print(f"Errors: {len(result.get('errors', []))}")
    print(f"Warnings: {len(result.get('warnings', []))}")
    
    if result.get('errors'):
        print("\nErrors:")
        for error in result['errors'][:3]:
            print(f"  - {error}")
    
    if result.get('certification'):
        print(f"\nCertification: {result['certification'].get('status')}")
else:
    print(f"ERROR: {response.text}")
