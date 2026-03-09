import json
import requests

# Read the generated ASM file
with open('merck/EndoScanV-Export-20230713115550_ASM.json', 'r') as f:
    asm_data = json.load(f)

# Call DVaaS validation service
url = 'https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate'
payload = {
    'asm_data': asm_data,
    'validation_level': 'basic',
    'generate_report': False
}

print("Validating EndoScan-V ASM output...")
print(f"File size: {len(json.dumps(asm_data))} bytes")
print(f"Validation level: comprehensive")
print()

try:
    response = requests.post(url, json=payload, timeout=30)
    result = response.json()
    
    print(f"Status: {result.get('status', 'UNKNOWN')}")
    print(f"Valid: {result.get('is_valid', False)}")
    print(f"Errors: {len(result.get('errors', []))}")
    print(f"Warnings: {len(result.get('warnings', []))}")
    print(f"Info: {len(result.get('info', []))}")
    print()
    
    if result.get('errors'):
        print("ERRORS:")
        for err in result['errors'][:5]:
            print(f"  - {err}")
    
    if result.get('warnings'):
        print("\nWARNINGS:")
        for warn in result['warnings'][:5]:
            print(f"  - {warn}")
            
    # Save full result
    with open('endoscan_validation_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\nFull result saved to: endoscan_validation_result.json")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nNote: Update the DVaaS endpoint URL in the script")
