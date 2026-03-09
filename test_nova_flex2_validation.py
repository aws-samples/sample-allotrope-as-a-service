#!/usr/bin/env python3
"""Test Nova FLEX2 converter output with fixed DVaaS validation"""

import json
import requests

DVAAS_ENDPOINT = "https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate"

# Load a Nova FLEX2 generated ASM file
with open('merck/SampleResults2025-November-1.json', 'r') as f:
    asm_data = json.load(f)

# Test with comprehensive validation
payload = {
    "asm_data": asm_data,
    "validation_level": "comprehensive",
    "use_allotropy_validator": True
}

print("Testing Nova FLEX2 Converter Output")
print("=" * 60)
print(f"File: merck/SampleResults2025-November-1.json")
print(f"Size: {len(json.dumps(asm_data))} bytes\n")

response = requests.post(DVAAS_ENDPOINT, json=payload, timeout=60)
result = response.json()

print(f"Valid: {result.get('valid')}")
print(f"Validator: {result.get('validator')}")
print(f"Errors: {len(result.get('errors', []))}")
print(f"Warnings: {len(result.get('warnings', []))}")

if result.get('errors'):
    print("\nERRORS:")
    for error in result['errors']:
        print(f"  {error}")

if result.get('warnings'):
    print("\nWARNINGS:")
    for warning in result['warnings']:
        print(f"  {warning}")

if result.get('metrics'):
    print("\nMETRICS:")
    for key, value in result['metrics'].items():
        print(f"  {key}: {value}")

print("\n" + "=" * 60)
if result.get('valid'):
    print("PASSED - Nova FLEX2 converter generates valid ASM")
else:
    print("FAILED - Issues found that need fixing")
    print("\nISSUES TO FIX:")
    if result.get('errors'):
        print(f"  - {len(result['errors'])} errors")
    if result.get('warnings'):
        print(f"  - {len(result['warnings'])} warnings")
