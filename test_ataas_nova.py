import csv
import json
import requests

# Read first row from Nova FLEX2 CSV
with open('merck/SampleResults2025-November.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    row = list(reader)[0]

# Create CSV content
headers = list(row.keys())
csv_content = ','.join(headers) + '\n'
csv_content += ','.join([row[h] for h in headers])

print("Testing ATaaS with Nova FLEX2 CSV")
print("=" * 60)
print(f"Sample: {row['Sample ID']}")
print()

# Call ATaaS directly
url = 'https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert'

response = requests.post(url, json={'file_content': csv_content}, timeout=180)
result = response.json()

print(f"Status: {response.status_code}")
print(f"\nFile Analysis:")
print(json.dumps(result.get('file_analysis', {}), indent=2))

# Save ASM output
asm_output = result.get('asm_output', {})
with open('tmp/ataas_test.json', 'w') as f:
    json.dump(asm_output, f, indent=2)

import os
size = os.path.getsize('tmp/ataas_test.json')
print(f"\nASM Output saved: tmp/ataas_test.json ({size:,} bytes)")

# Check manifest
manifest = asm_output.get('$asm.manifest', asm_output.get('manifest', 'N/A'))
print(f"Manifest: {manifest}")

# Compare with original
with open('output/november/SampleResults-1.json', 'r') as f:
    original = json.load(f)
    original_size = len(json.dumps(original))
    print(f"\nOriginal file: {original_size:,} bytes")
    print(f"New file: {size:,} bytes")
