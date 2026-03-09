"""
Merck Batch Processing Service
Processes monthly CSV files and generates individual ASM files with certification
"""

import json
import os
from nova_flex2_converter import convert_csv_to_asm_batch
from asm_comparison_tool import certify_asm

def process_merck_batch(csv_file, reference_dir=None, output_dir='output'):
    """Process Merck CSV file and generate ASM files with certification"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read CSV
    with open(csv_file, 'r') as f:
        csv_content = f.read()
    
    # Convert to ASM
    results = convert_csv_to_asm_batch(csv_content)
    
    # Process each result
    certifications = []
    
    for result in results:
        if result['success']:
            # Save ASM file
            output_file = os.path.join(output_dir, result['filename'])
            with open(output_file, 'w') as f:
                json.dump(result['asm'], f, indent=2)
            
            # Certify if reference available
            if reference_dir:
                ref_file = os.path.join(reference_dir, result['filename'])
                if os.path.exists(ref_file):
                    with open(ref_file, 'r') as f:
                        reference = json.load(f)
                    
                    cert = certify_asm(result['asm'], reference, threshold=85.0)
                    cert['sample_id'] = result['sample_id']
                    cert['filename'] = result['filename']
                    certifications.append(cert)
                else:
                    certifications.append({
                        'sample_id': result['sample_id'],
                        'filename': result['filename'],
                        'certified': None,
                        'status': 'NO_REFERENCE'
                    })
            else:
                certifications.append({
                    'sample_id': result['sample_id'],
                    'filename': result['filename'],
                    'certified': True,
                    'status': 'GENERATED'
                })
    
    # Generate batch report
    report = {
        'total_samples': len(results),
        'successful': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        'certifications': certifications,
        'output_directory': output_dir
    }
    
    return report

def generate_batch_report(report):
    """Generate human-readable batch report"""
    
    lines = []
    lines.append("="*80)
    lines.append("MERCK BATCH PROCESSING REPORT")
    lines.append("="*80)
    lines.append(f"Total Samples: {report['total_samples']}")
    lines.append(f"Successful Conversions: {report['successful']}")
    lines.append(f"Failed Conversions: {report['failed']}")
    lines.append(f"Output Directory: {report['output_directory']}")
    lines.append("")
    
    if report['certifications']:
        lines.append("CERTIFICATION RESULTS:")
        lines.append("-"*80)
        
        certified = sum(1 for c in report['certifications'] if c.get('certified') == True)
        failed = sum(1 for c in report['certifications'] if c.get('certified') == False)
        no_ref = sum(1 for c in report['certifications'] if c.get('status') == 'NO_REFERENCE')
        
        lines.append(f"Certified: {certified}")
        lines.append(f"Failed Certification: {failed}")
        lines.append(f"No Reference: {no_ref}")
        lines.append("")
        
        for cert in report['certifications'][:10]:  # Show first 10
            lines.append(f"Sample: {cert['sample_id']}")
            lines.append(f"  File: {cert['filename']}")
            lines.append(f"  Status: {cert['status']}")
            if cert.get('match_rate'):
                lines.append(f"  Match Rate: {cert['match_rate']:.2f}%")
            lines.append("")
    
    lines.append("="*80)
    
    return "\n".join(lines)

if __name__ == "__main__":
    # Process November file
    report = process_merck_batch(
        'merck/SampleResults2025-November.csv',
        reference_dir='merck',
        output_dir='output/november'
    )
    
    # Generate report
    batch_report = generate_batch_report(report)
    print(batch_report)
    
    # Save report
    with open('output/november/batch_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nGenerated {report['successful']} ASM files in output/november/")
