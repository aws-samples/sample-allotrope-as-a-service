"""
ASM Reference Comparison Tool
Compares generated ASM against Merck reference files
"""

import json

def compare_asm_files(generated_asm, reference_asm, tolerance=0.01):
    """Compare two ASM files and report differences"""
    
    differences = []
    matches = []
    
    def compare_values(path, gen_val, ref_val):
        """Compare two values with tolerance for floats"""
        if isinstance(gen_val, (int, float)) and isinstance(ref_val, (int, float)):
            if abs(gen_val - ref_val) > tolerance:
                differences.append({
                    'path': path,
                    'generated': gen_val,
                    'reference': ref_val,
                    'diff': abs(gen_val - ref_val)
                })
            else:
                matches.append(path)
        elif gen_val != ref_val:
            differences.append({
                'path': path,
                'generated': gen_val,
                'reference': ref_val
            })
        else:
            matches.append(path)
    
    def traverse(path, gen, ref):
        """Recursively traverse and compare structures"""
        if isinstance(gen, dict) and isinstance(ref, dict):
            all_keys = set(gen.keys()) | set(ref.keys())
            for key in all_keys:
                new_path = f"{path}.{key}" if path else key
                if key not in gen:
                    differences.append({'path': new_path, 'generated': 'MISSING', 'reference': ref[key]})
                elif key not in ref:
                    differences.append({'path': new_path, 'generated': gen[key], 'reference': 'MISSING'})
                else:
                    traverse(new_path, gen[key], ref[key])
        elif isinstance(gen, list) and isinstance(ref, list):
            if len(gen) != len(ref):
                differences.append({'path': f"{path}[length]", 'generated': len(gen), 'reference': len(ref)})
            for i in range(min(len(gen), len(ref))):
                traverse(f"{path}[{i}]", gen[i], ref[i])
        else:
            compare_values(path, gen, ref)
    
    traverse('', generated_asm, reference_asm)
    
    return {
        'total_fields': len(matches) + len(differences),
        'matches': len(matches),
        'differences': len(differences),
        'match_rate': len(matches) / (len(matches) + len(differences)) * 100 if (len(matches) + len(differences)) > 0 else 0,
        'details': differences
    }

def generate_comparison_report(comparison_result):
    """Generate human-readable comparison report"""
    
    report = []
    report.append("="*80)
    report.append("ASM COMPARISON REPORT")
    report.append("="*80)
    report.append(f"Total Fields Compared: {comparison_result['total_fields']}")
    report.append(f"Matches: {comparison_result['matches']}")
    report.append(f"Differences: {comparison_result['differences']}")
    report.append(f"Match Rate: {comparison_result['match_rate']:.2f}%")
    report.append("")
    
    if comparison_result['differences'] == 0:
        report.append("PERFECT MATCH - All fields identical!")
    else:
        report.append("DIFFERENCES FOUND:")
        report.append("-"*80)
        for diff in comparison_result['details'][:20]:  # Show first 20
            report.append(f"\nPath: {diff['path']}")
            report.append(f"  Generated: {diff['generated']}")
            report.append(f"  Reference: {diff['reference']}")
            if 'diff' in diff:
                report.append(f"  Difference: {diff['diff']:.6f}")
        
        if len(comparison_result['details']) > 20:
            report.append(f"\n... and {len(comparison_result['details']) - 20} more differences")
    
    report.append("\n" + "="*80)
    
    return "\n".join(report)

def certify_asm(generated_asm, reference_asm, threshold=95.0):
    """Certify ASM if it meets threshold"""
    
    comparison = compare_asm_files(generated_asm, reference_asm)
    
    certification = {
        'certified': comparison['match_rate'] >= threshold,
        'match_rate': comparison['match_rate'],
        'threshold': threshold,
        'total_fields': comparison['total_fields'],
        'matches': comparison['matches'],
        'differences': comparison['differences'],
        'status': 'CERTIFIED' if comparison['match_rate'] >= threshold else 'FAILED',
        'details': comparison['details']
    }
    
    return certification

if __name__ == "__main__":
    # Load generated ASM
    with open('test_nova_flex2_output.json', 'r') as f:
        generated = json.load(f)
    
    # Load Merck reference
    with open('merck/SampleResults2025-November-1.json', 'r') as f:
        reference = json.load(f)
    
    # Compare
    comparison = compare_asm_files(generated, reference)
    report = generate_comparison_report(comparison)
    
    print(report)
    
    # Certification
    cert = certify_asm(generated, reference, threshold=90.0)
    print(f"\nCERTIFICATION STATUS: {cert['status']}")
    print(f"Match Rate: {cert['match_rate']:.2f}% (Threshold: {cert['threshold']}%)")
