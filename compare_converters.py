#!/usr/bin/env python3
"""Compare our Nova FLEX2 converter output with customer's output"""

import json
import requests

DVAAS_ENDPOINT = "https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate"

# Load both files
with open('test_nova_flex2_output.json', 'r') as f:
    our_asm = json.load(f)

with open('merck/SampleResults2025-November-1.json', 'r') as f:
    customer_asm = json.load(f)

print("COMPARISON: Our Converter vs Customer Converter")
print("=" * 70)

# Size comparison
our_size = len(json.dumps(our_asm))
customer_size = len(json.dumps(customer_asm))
print(f"\nFile Size:")
print(f"  Our output:      {our_size:,} bytes")
print(f"  Customer output: {customer_size:,} bytes")
print(f"  Difference:      {abs(our_size - customer_size):,} bytes")

# Validate both
print(f"\n{'='*70}")
print("VALIDATION: Our Output")
print("=" * 70)

response = requests.post(DVAAS_ENDPOINT, json={
    "asm_data": our_asm,
    "validation_level": "comprehensive",
    "use_allotropy_validator": True
}, timeout=60)
our_result = response.json()

print(f"Valid: {our_result.get('valid')}")
print(f"Errors: {len(our_result.get('errors', []))}")
print(f"Warnings: {len(our_result.get('warnings', []))}")

if our_result.get('errors'):
    print("\nErrors:")
    for error in our_result['errors'][:3]:
        print(f"  {error}")

print(f"\n{'='*70}")
print("VALIDATION: Customer Output")
print("=" * 70)

response = requests.post(DVAAS_ENDPOINT, json={
    "asm_data": customer_asm,
    "validation_level": "comprehensive",
    "use_allotropy_validator": True
}, timeout=60)
customer_result = response.json()

print(f"Valid: {customer_result.get('valid')}")
print(f"Errors: {len(customer_result.get('errors', []))}")
print(f"Warnings: {len(customer_result.get('warnings', []))}")

if customer_result.get('errors'):
    print("\nErrors:")
    for error in customer_result['errors'][:3]:
        print(f"  {error}")

# Summary
print(f"\n{'='*70}")
print("SUMMARY")
print("=" * 70)

if our_result.get('valid') == customer_result.get('valid'):
    print("[MATCH] Both have same validation status")
else:
    print("[DIFF] Different validation status")

if len(our_result.get('errors', [])) == len(customer_result.get('errors', [])):
    print("[MATCH] Both have same number of errors")
else:
    print(f"[DIFF] Different error counts: Ours={len(our_result.get('errors', []))}, Customer={len(customer_result.get('errors', []))}")

print(f"\nConclusion: {'MATCH - Both converters produce equivalent ASM' if our_result.get('valid') == customer_result.get('valid') else 'DIFFERENT'}")
