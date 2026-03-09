"""
Test Unified Converter with Merck November CSV
Compare output with original batch processing results
"""

import csv
import json
import requests
import os
from datetime import datetime

# Read the November CSV
csv_file = 'merck/SampleResults2025-November.csv'
output_dir = 'tmp'

print("Testing Unified Converter with Merck November Data")
print("=" * 60)

# Read CSV
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total samples in CSV: {len(rows)}")
print()

# Process each row through Unified Converter
unified_url = 'https://tqzatn5bse.execute-api.us-east-1.amazonaws.com/prod/convert'

successful = 0
failed = 0
results = []

for i, row in enumerate(rows, 1):
    sample_id = row.get('Sample ID', f'Sample_{i}')
    print(f"Processing {i}/{len(rows)}: {sample_id}...", end=' ')
    
    # Create CSV content for this row
    headers = list(row.keys())
    csv_content = ','.join(headers) + '\n'
    csv_content += ','.join([row[h] for h in headers])
    
    try:
        response = requests.post(
            unified_url,
            json={
                'file_content': csv_content,
                'file_name': f'{sample_id}.csv'
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Save ASM output
            output_file = os.path.join(output_dir, f'SampleResults-{i}.json')
            with open(output_file, 'w') as f:
                json.dump(result.get('asm_output', {}), f, indent=2)
            
            method = result.get('method', 'unknown')
            print(f"OK ({method})")
            
            results.append({
                'sample_id': sample_id,
                'row_number': i,
                'method': method,
                'status': 'success',
                'output_file': output_file
            })
            successful += 1
        else:
            print(f"FAIL HTTP {response.status_code}")
            failed += 1
            results.append({
                'sample_id': sample_id,
                'row_number': i,
                'status': 'failed',
                'error': response.text[:100]
            })
    
    except Exception as e:
        print(f"FAIL {str(e)[:50]}")
        failed += 1
        results.append({
            'sample_id': sample_id,
            'row_number': i,
            'status': 'failed',
            'error': str(e)[:100]
        })

print()
print("=" * 60)
print("RESULTS:")
print(f"Total: {len(rows)}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")
print()

# Check which method was used
methods = {}
for r in results:
    if r['status'] == 'success':
        method = r.get('method', 'unknown')
        methods[method] = methods.get(method, 0) + 1

print("Methods used:")
for method, count in methods.items():
    print(f"  {method}: {count}")
print()

# Save summary
summary = {
    'timestamp': datetime.utcnow().isoformat(),
    'csv_file': csv_file,
    'output_dir': output_dir,
    'total_samples': len(rows),
    'successful': successful,
    'failed': failed,
    'methods': methods,
    'results': results
}

with open(os.path.join(output_dir, 'test_summary.json'), 'w') as f:
    json.dump(summary, f, indent=2)

print(f"Output saved to: {output_dir}/")
print(f"Summary saved to: {output_dir}/test_summary.json")
print()

# Compare with original output
print("Comparing with original output...")
original_dir = 'output/november'
if os.path.exists(original_dir):
    original_files = [f for f in os.listdir(original_dir) if f.endswith('.json')]
    print(f"Original output: {len(original_files)} files")
    print(f"New output: {successful} files")
    
    if len(original_files) == successful:
        print("OK Same number of files generated")
    else:
        print(f"FAIL Different count: {len(original_files)} vs {successful}")
else:
    print("Original output directory not found")
