from nova_flex2_converter import convert_csv_to_asm_batch
import json
import os

# Read CSV
with open('merck/SampleResults2025-November.csv', 'r') as f:
    csv_content = f.read()

# Convert
results = convert_csv_to_asm_batch(csv_content)

print(f"Converted {len(results)} rows")
print(f"Success: {sum(1 for r in results if r['success'])}")
print(f"Failed: {sum(1 for r in results if not r['success'])}")

# Save to tmp directory
output_dir = 'tmp'
for result in results:
    if result['success']:
        output_file = os.path.join(output_dir, result['filename'])
        with open(output_file, 'w') as f:
            json.dump(result['asm'], f, indent=2)

print(f"\nSaved {sum(1 for r in results if r['success'])} files to {output_dir}/")

# Check file sizes
sizes = []
for i in range(1, 4):
    file_path = os.path.join(output_dir, f'SampleResults-{i}.json')
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        sizes.append(size)
        print(f"  SampleResults-{i}.json: {size:,} bytes")

print(f"\nAverage size: {sum(sizes)//len(sizes):,} bytes")
