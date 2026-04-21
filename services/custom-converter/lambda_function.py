# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at http://aws.amazon.com/apache2.0/
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
"""
Custom Converter Service
Loads and executes approved custom converters from S3
"""

import json
import boto3
import os
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """Execute custom converter"""
    
    try:
        # Parse request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        converter_id = body.get('converter_id')
        file_content = body.get('file_content')
        
        if not converter_id or not file_content:
            return error_response(400, "converter_id and file_content required")
        
        # Get converter from registry
        registry_table = dynamodb.Table(os.environ.get('CONVERTER_REGISTRY_TABLE'))
        response = registry_table.get_item(Key={'converter_id': converter_id})
        
        if 'Item' not in response:
            return error_response(404, f"Converter {converter_id} not found")
        
        converter = response['Item']
        
        if converter.get('status') != 'APPROVED':
            return error_response(403, f"Converter {converter_id} not approved")
        
        # Load converter code from S3
        bucket = os.environ.get('CONVERTERS_BUCKET')
        s3_key = converter.get('s3_location')
        
        converter_code = s3.get_object(Bucket=bucket, Key=s3_key)['Body'].read().decode('utf-8')
        
        # Execute converter
        result = execute_converter(converter_code, file_content)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'converter_id': converter_id,
                'asm_output': result,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        return error_response(500, str(e))

def execute_converter(converter_code, file_content):
    """Execute converter code in sandboxed environment"""
    
    # Create namespace for execution
    namespace = {'file_content': file_content}
    
    # Execute converter code
    exec(converter_code, namespace)
    
    # Call convert function
    if 'convert' not in namespace:
        raise Exception("Converter must define 'convert' function")
    
    return namespace['convert'](file_content)

def error_response(status_code, message):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }
