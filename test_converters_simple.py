"""
Test custom converters through DVaaS validation
"""
import requests
import json

# DVaaS endpoint
dvaas_url = "https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate"

# Test files that actually exist
test_files = [
    {
        "name": "Nova FLEX2",
        "file": r"C:\app\asm2agent\output\november\SampleResults-1.json",
        "converter": "nova_flex2_converter.py"
    },
    {
        "name": "Wyatt ASTRA",
        "file": r"C:\app\asm2agent\output\wyatt_astra_(01)(1225497)(0001503570 01M)(Inj1).json",
        "converter": "wyatt_astra_converter.py"
    }
]

print("=" * 80)
print("VALIDATING CUSTOM CONVERTERS THROUGH DVaaS")
print("=" * 80)
print()

results = []

for test in test_files:
    print(f"Testing: {test['name']}")
    print(f"File: {test['file']}")
    print("-" * 80)
    
    # Read ASM file
    with open(test['file'], 'r') as f:
        asm_content = json.load(f)
    
    # Send to DVaaS for validation
    payload = {
        "asm_data": asm_content,
        "validation_level": "comprehensive"
    }
    
    try:
        response = requests.post(dvaas_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            is_valid = result.get('valid', False)
            status = result.get('status', 'UNKNOWN')
            errors = result.get('errors', [])
            warnings = result.get('warnings', [])
            
            if is_valid:
                print(f"VALID ASM - Status: {status}")
            else:
                print(f"INVALID ASM - Status: {status}")
            
            print(f"Errors: {len(errors)}")
            print(f"Warnings: {len(warnings)}")
            
            if errors:
                print("\nFirst 5 Errors:")
                for i, error in enumerate(errors[:5], 1):
                    print(f"  {i}. {error}")
                if len(errors) > 5:
                    print(f"  ... and {len(errors) - 5} more errors")
            
            if warnings:
                print("\nFirst 3 Warnings:")
                for i, warning in enumerate(warnings[:3], 1):
                    print(f"  {i}. {warning}")
                if len(warnings) > 3:
                    print(f"  ... and {len(warnings) - 3} more warnings")
            
            results.append({
                'name': test['name'],
                'converter': test['converter'],
                'status': status,
                'valid': is_valid,
                'errors': len(errors),
                'warnings': len(warnings)
            })
            
        else:
            print(f"DVaaS ERROR: {response.status_code}")
            print(response.text)
            results.append({
                'name': test['name'],
                'status': 'DVAAS_ERROR',
                'valid': False
            })
    
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")
        results.append({
            'name': test['name'],
            'status': 'EXCEPTION',
            'valid': False,
            'error': str(e)
        })
    
    print()

# Summary
print("=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
print()

for result in results:
    status_text = "VALID" if result.get('valid') else "INVALID"
    print(f"{status_text} - {result['name']}: {result.get('status', 'UNKNOWN')}")
    if 'errors' in result:
        print(f"         Errors: {result['errors']}, Warnings: {result['warnings']}")

print()
print(f"Total Tested: {len(results)}")
print(f"Valid: {sum(1 for r in results if r.get('valid'))}")
print(f"Invalid: {sum(1 for r in results if not r.get('valid'))}")
