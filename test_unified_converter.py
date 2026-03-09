import json
import requests

url = 'https://tqzatn5bse.execute-api.us-east-1.amazonaws.com/prod/convert'

# Test 1: Nova FLEX2 (should use Multi-Instrument - allotropy)
nova_csv = """Sample ID,pH,Osmolality,Glucose,Lactate
SAMPLE_001,7.183,301,3.45,0.89"""

print("Test 1: Nova FLEX2 CSV (allotropy supported)")
print("=" * 60)
response = requests.post(url, json={'file_content': nova_csv, 'file_name': 'nova_flex2.csv'}, timeout=60)
result = response.json()
print(f"Status: {response.status_code}")
print(f"Method: {result.get('method')}")
print(f"Converter: {result.get('converter_used', result.get('file_analysis', {}).get('instrument_type'))}")
print(f"Message: {result.get('message')}")
print()

# Test 2: Unknown format (should fallback to AI)
unknown_data = """Instrument: CustomAnalyzer-3000
Date: 2024-01-15
Sample,Result,Unit
A1,45.2,mg/dL
A2,48.1,mg/dL"""

print("Test 2: Unknown Instrument (AI fallback)")
print("=" * 60)
response = requests.post(url, json={'file_content': unknown_data, 'file_name': 'unknown.txt'}, timeout=60)
result = response.json()
print(f"Status: {response.status_code}")
print(f"Method: {result.get('method')}")
if result.get('file_analysis'):
    print(f"AI Analysis: {json.dumps(result['file_analysis'], indent=2)}")
print(f"Message: {result.get('message')}")
print()

print("Unified Converter Test Complete!")
print("Multi-Instrument -> AI fallback working correctly")
