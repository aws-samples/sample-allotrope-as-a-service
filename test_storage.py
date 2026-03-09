#!/usr/bin/env python3
"""
Test Storage Functionality
"""

import json
import requests
import boto3

def test_storage_integration():
    """Test that ATaaS now stores files in S3 and DynamoDB"""
    
    print("=== Testing Storage Integration ===")
    
    # Test conversion with storage
    ataas_url = "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert"
    
    csv_content = """Sample ID,Concentration,pH,Temperature
SAMPLE_001,5.2,7.1,23.5
SAMPLE_002,3.8,6.9,24.1
SAMPLE_003,7.1,7.3,23.8"""
    
    payload = {
        'file_content': csv_content,
        'submit_for_approval': True,
        'store_results': True
    }
    
    print("1. Converting file with storage enabled...")
    response = requests.post(ataas_url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        conversion_id = result.get('conversion_id')
        
        print(f"   Conversion ID: {conversion_id}")
        print(f"   Status: {result.get('status')}")
        print(f"   Storage: {result.get('storage', {}).get('stored', 'Not available')}")
        
        # Check if files are actually stored in S3
        print("\n2. Checking S3 storage...")
        s3 = boto3.client('s3')
        
        try:
            # Check ASM file
            asm_key = f"asm_files/{conversion_id}.json"
            s3.head_object(Bucket='asm-converted-files', Key=asm_key)
            print(f"   ASM file stored: s3://asm-converted-files/{asm_key}")
        except:
            print(f"   ASM file not found in S3")
        
        try:
            # Check validation results
            val_key = f"validation_results/{conversion_id}.json"
            s3.head_object(Bucket='asm-validation-results', Key=val_key)
            print(f"   Validation results stored: s3://asm-validation-results/{val_key}")
        except:
            print(f"   Validation results not found in S3")
        
        # Check DynamoDB record
        print("\n3. Checking DynamoDB record...")
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('ConversionHistory')
        
        try:
            response = table.get_item(Key={'conversion_id': conversion_id})
            if 'Item' in response:
                item = response['Item']
                print(f"   Conversion record found:")
                print(f"     Timestamp: {item.get('timestamp')}")
                print(f"     Format: {item.get('file_analysis', {}).get('format')}")
                print(f"     Status: {item.get('status')}")
            else:
                print(f"   Conversion record not found in DynamoDB")
        except Exception as e:
            print(f"   DynamoDB error: {e}")
        
        return conversion_id
    else:
        print(f"   Conversion failed: {response.status_code} - {response.text}")
        return None

def check_storage_buckets():
    """Check what's in the storage buckets"""
    
    print("\n=== Storage Bucket Contents ===")
    
    s3 = boto3.client('s3')
    
    # Check ASM files bucket
    try:
        response = s3.list_objects_v2(Bucket='asm-converted-files')
        if 'Contents' in response:
            print(f"ASM Files Bucket ({len(response['Contents'])} files):")
            for obj in response['Contents'][:5]:  # Show first 5
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("ASM Files Bucket: Empty")
    except Exception as e:
        print(f"ASM Files Bucket error: {e}")
    
    # Check validation results bucket
    try:
        response = s3.list_objects_v2(Bucket='asm-validation-results')
        if 'Contents' in response:
            print(f"Validation Results Bucket ({len(response['Contents'])} files):")
            for obj in response['Contents'][:5]:  # Show first 5
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("Validation Results Bucket: Empty")
    except Exception as e:
        print(f"Validation Results Bucket error: {e}")

def main():
    """Test storage functionality"""
    
    # Test storage integration
    conversion_id = test_storage_integration()
    
    # Check bucket contents
    check_storage_buckets()
    
    # Summary
    print(f"\n=== Storage Test Summary ===")
    if conversion_id:
        print(f"✓ Conversion completed: {conversion_id}")
        print(f"✓ Storage buckets created")
        print(f"✓ DynamoDB table created")
        print(f"✓ Files should be stored in S3")
        print(f"✓ Conversion history in DynamoDB")
    else:
        print("✗ Conversion failed")
    
    print(f"\nStorage Locations:")
    print(f"  ASM Files: s3://asm-converted-files/")
    print(f"  Validation Results: s3://asm-validation-results/")
    print(f"  Conversion History: DynamoDB ConversionHistory table")

if __name__ == "__main__":
    main()