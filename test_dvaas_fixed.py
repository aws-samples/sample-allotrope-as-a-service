#!/usr/bin/env python3
"""Test DVaaS validation after fix"""

import json
import requests

DVAAS_ENDPOINT = "https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate"

# Load a customer ASM file
with open('merck/SampleResults2025-November-1.json', 'r') as f:
    asm_data = json.load(f)

# Test with comprehensive validation
payload = {
    "asm_data": asm_data,
    "validation_level": "comprehensive",
    "use_allotropy_validator": True
}

print("Testing DVaaS with comprehensive validation...")
print(f"Endpoint: {DVAAS_ENDPOINT}")
print(f"File size: {len(json.dumps(asm_data))} bytes\n")

response = requests.post(DVAAS_ENDPOINT, json=payload, timeout=60)

print(f"Status: {response.status_code}")
result = response.json()

print(f"\nValid: {result.get('valid')}")
print(f"Validator: {result.get('validator')}")
print(f"Errors: {len(result.get('errors', []))}")
print(f"Warnings: {len(result.get('warnings', []))}")

if result.get('errors'):
    print("\nErrors:")
    for error in result['errors'][:5]:
        print(f"  - {error}")

if result.get('warnings'):
    print("\nWarnings:")
    for warning in result['warnings'][:5]:
        print(f"  - {warning}")

if result.get('metrics'):
    print("\nMetrics:")
    for key, value in result['metrics'].items():
        print(f"  {key}: {value}")

print("\nDVaaS validation is now working!" if result.get('validator') == 'allotropy' else "\nStill using basic validation")
