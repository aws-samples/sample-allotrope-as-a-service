#!/usr/bin/env python3
"""
Verify Storage - Check S3 and DynamoDB
"""

import boto3
import json

def check_s3_storage():
    """Check what's stored in S3"""
    
    print("=== Checking S3 Storage ===")
    
    s3 = boto3.client('s3')
    
    # Check ASM files bucket
    try:
        response = s3.list_objects_v2(Bucket='asm-converted-files')
        if 'Contents' in response:
            print(f"ASM Files Bucket ({len(response['Contents'])} files):")
            for obj in response['Contents']:
                print(f"  - {obj['Key']} ({obj['Size']} bytes, {obj['LastModified']})")
        else:
            print("ASM Files Bucket: Empty")
    except Exception as e:
        print(f"ASM Files Bucket error: {e}")

def check_dynamodb_storage():
    """Check what's stored in DynamoDB"""
    
    print("\n=== Checking DynamoDB Storage ===")
    
    dynamodb = boto3.resource('dynamodb')
    
    try:
        table = dynamodb.Table('ConversionHistory')
        response = table.scan(Limit=10)
        
        if 'Items' in response and response['Items']:
            print(f"Conversion History ({len(response['Items'])} records):")
            for item in response['Items']:
                print(f"  - {item['conversion_id']}: {item['timestamp']} ({item['status']})")
                if item.get('asm_s3_key'):
                    print(f"    ASM File: {item['asm_s3_key']}")
        else:
            print("Conversion History: Empty")
    except Exception as e:
        print(f"DynamoDB error: {e}")

def get_sample_file():
    """Get a sample stored file"""
    
    print("\n=== Sample Stored File ===")
    
    s3 = boto3.client('s3')
    
    try:
        # List files and get the latest one
        response = s3.list_objects_v2(Bucket='asm-converted-files')
        if 'Contents' in response:
            latest_file = sorted(response['Contents'], key=lambda x: x['LastModified'])[-1]
            key = latest_file['Key']
            
            # Get file content
            file_response = s3.get_object(Bucket='asm-converted-files', Key=key)
            content = file_response['Body'].read().decode('utf-8')
            
            print(f"Latest file: {key}")
            print("Content:")
            print(json.dumps(json.loads(content), indent=2))
        else:
            print("No files found")
    except Exception as e:
        print(f"Error getting sample file: {e}")

def main():
    """Check storage"""
    
    check_s3_storage()
    check_dynamodb_storage()
    get_sample_file()
    
    print(f"\n=== Storage Verification Complete ===")

if __name__ == "__main__":
    main()