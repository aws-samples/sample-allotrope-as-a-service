#!/usr/bin/env python3
"""Test fixed Nova FLEX2 converter with traceability"""

import json
import requests

DVAAS_ENDPOINT = "https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate"

with open('test_nova_flex2_output.json', 'r') as f:
    asm_data = json.load(f)

print("Testing FIXED Nova FLEX2 Converter")
print("=" * 60)

response = requests.post(DVAAS_ENDPOINT, json={
    "asm_data": asm_data,
    "validation_level": "comprehensive",
    "use_allotropy_validator": True
}, timeout=60)

result = response.json()

print(f"Valid: {result.get('valid')}")
print(f"Errors: {len(result.get('errors', []))}")
print(f"Warnings: {len(result.get('warnings', []))}")

if result.get('errors'):
    print("\nErrors:")
    for error in result['errors']:
        print(f"  {error}")

if result.get('warnings'):
    print("\nWarnings (first 3):")
    for warning in result['warnings'][:3]:
        print(f"  {warning}")

print("\n" + "=" * 60)
if result.get('valid'):
    print("SUCCESS - Our converter now generates VALID ASM!")
else:
    print("FAILED - Still has issues")
