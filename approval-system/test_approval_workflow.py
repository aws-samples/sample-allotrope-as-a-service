#!/usr/bin/env python3
"""
Test client for Approval Workflow System
"""

import json
import requests
import time

class ApprovalWorkflowClient:
    def __init__(self, api_url):
        self.api_url = api_url.rstrip('/')
    
    def submit_converter_for_review(self, converter_data):
        """Submit a converter for human review"""
        
        payload = {
            'action': 'submit_for_review',
            **converter_data
        }
        
        try:
            response = requests.post(f"{self.api_url}/workflow", json=payload)
            print(f"Submit for Review: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Converter ID: {result.get('converter_id')}")
                print(f"Status: {result.get('status')}")
                return result
            else:
                print(f"Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"Submit Error: {e}")
            return None
    
    def get_pending_converters(self):
        """Get all converters pending review"""
        
        payload = {'action': 'get_pending'}
        
        try:
            response = requests.post(f"{self.api_url}/workflow", json=payload)
            print(f"Get Pending: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                converters = result.get('pending_converters', [])
                print(f"Pending Converters: {len(converters)}")
                
                for converter in converters:
                    print(f"  - {converter['converter_id']}: {converter['metadata'].get('format')} → ASM")
                
                return converters
            else:
                print(f"Error: {response.text}")
                return []
                
        except Exception as e:
            print(f"Get Pending Error: {e}")
            return []
    
    def approve_converter(self, converter_id, reviewer_id, signature):
        """Approve a converter"""
        
        payload = {
            'action': 'approve',
            'converter_id': converter_id,
            'reviewer_id': reviewer_id,
            'signature': signature
        }
        
        try:
            response = requests.post(f"{self.api_url}/workflow", json=payload)
            print(f"Approve Converter: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Approved: {result.get('converter_id')}")
                print(f"Status: {result.get('status')}")
                return result
            else:
                print(f"Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"Approve Error: {e}")
            return None
    
    def reject_converter(self, converter_id, reviewer_id, feedback):
        """Reject a converter"""
        
        payload = {
            'action': 'reject',
            'converter_id': converter_id,
            'reviewer_id': reviewer_id,
            'feedback': feedback
        }
        
        try:
            response = requests.post(f"{self.api_url}/workflow", json=payload)
            print(f"Reject Converter: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Rejected: {result.get('converter_id')}")
                print(f"Feedback: {result.get('feedback')}")
                return result
            else:
                print(f"Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"Reject Error: {e}")
            return None
    
    def get_approved_converters(self):
        """Get all approved converters"""
        
        payload = {'action': 'get_approved'}
        
        try:
            response = requests.post(f"{self.api_url}/workflow", json=payload)
            print(f"Get Approved: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                converters = result.get('approved_converters', [])
                print(f"Approved Converters: {len(converters)}")
                
                for converter in converters:
                    print(f"  - {converter['converter_id']}: Approved by {converter.get('reviewer_id')}")
                
                return converters
            else:
                print(f"Error: {response.text}")
                return []
                
        except Exception as e:
            print(f"Get Approved Error: {e}")
            return []

def main():
    """Test the approval workflow system"""
    
    # API URL (update with actual deployed endpoint)
    api_url = "https://your-approval-api.execute-api.us-east-1.amazonaws.com/prod"
    
    client = ApprovalWorkflowClient(api_url)
    
    print("=== Testing Approval Workflow System ===\n")
    
    # Test 1: Submit converter for review
    print("1. Submitting Converter for Review:")
    
    sample_converter = {
        'code': '''#!/usr/bin/env python3
"""
Generated ASM Converter for CSV files
Auto-generated by ATaaS
"""

import csv
import json
from datetime import datetime

def convert_to_asm(file_path):
    """Convert CSV file to ASM format"""
    
    asm_output = {
        "$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/BENCHLING/2023/09/solution-analyzer.manifest",
        "measurement document": []
    }
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            measurement = {
                "measurement identifier": row.get("Sample ID", f"SAMPLE_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                "measurement time": datetime.now().isoformat(),
                "processed data document": [{
                    "concentration": float(row.get("Concentration", 0)),
                    "pH": float(row.get("pH", 7.0)),
                    "temperature": float(row.get("Temperature", 25.0))
                }]
            }
            asm_output["measurement document"].append(measurement)
    
    return asm_output

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = convert_to_asm(sys.argv[1])
        print(json.dumps(result, indent=2))
''',
        'language': 'python',
        'filename': 'csv_converter_test.py',
        'format': 'CSV',
        'instrument_type': 'solution_analyzer',
        'conversion_id': 'CONV-TEST-001',
        'file_analysis': {
            'format': 'CSV',
            'instrument_type': 'solution_analyzer',
            'confidence': 0.9
        },
        'test_data': 'Sample ID,Concentration,pH,Temperature\nSAMPLE_001,5.2,7.1,23.5'
    }
    
    submit_result = client.submit_converter_for_review(sample_converter)
    
    if submit_result:
        converter_id = submit_result.get('converter_id')
        
        print(f"\n2. Getting Pending Converters:")
        pending = client.get_pending_converters()
        
        print(f"\n3. Approving Converter:")
        approve_result = client.approve_converter(
            converter_id, 
            "dr.smith@company.com", 
            "ElectronicSignature123"
        )
        
        print(f"\n4. Getting Approved Converters:")
        approved = client.get_approved_converters()
        
        print(f"\n5. Testing Rejection (with new converter):")
        # Submit another converter to reject
        sample_converter['conversion_id'] = 'CONV-TEST-002'
        reject_result = client.submit_converter_for_review(sample_converter)
        
        if reject_result:
            reject_id = reject_result.get('converter_id')
            client.reject_converter(
                reject_id,
                "dr.jones@company.com",
                "Incorrect field mapping for temperature units"
            )

if __name__ == "__main__":
    main()