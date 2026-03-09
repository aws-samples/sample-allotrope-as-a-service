"""
Test with original Nova FLEX2 converter
"""

import sys
sys.path.insert(0, '.')

from nova_flex2_converter import convert_csv_to_asm
import json
import os

csv_file = 'merck/SampleResults2025-November.csv'
output_dir = 'tmp'

print("Processing with Nova FLEX2 Converter")
print("=" * 60)

# Use the original converter
asm_files = convert_csv_to_asm(csv_file, output_dir)

print(f"\nGenerated {len(asm_files)} ASM files")
print(f"Output directory: {output_dir}/")

# Check file sizes
for i, asm_file in enumerate(asm_files[:3], 1):
    size = os.path.getsize(asm_file)
    print(f"  {os.path.basename(asm_file)}: {size:,} bytes")

print("\nComparing with original...")
original_dir = 'output/november'
if os.path.exists(original_dir):
    original_files = [f for f in os.listdir(original_dir) if f.startswith('SampleResults-') and f.endswith('.json')]
    print(f"Original: {len(original_files)} files")
    print(f"New: {len(asm_files)} files")
    
    if len(original_files) == len(asm_files):
        print("OK Same count")
    else:
        print(f"DIFF {len(original_files)} vs {len(asm_files)}")
