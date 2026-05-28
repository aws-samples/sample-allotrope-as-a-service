# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at http://aws.amazon.com/apache2.0/
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
"""
Custom Converter Service
Loads and executes approved custom converters from S3.

Security layers applied to exec():
  Layer B — STS zero-permission session strips AWS credentials before exec()
  Layer D — Scrubbed namespace removes open(), os.environ, and restricts builtins
"""

import json
import builtins
import boto3
import os
from datetime import datetime

s3 = boto3.client('s3')
sts = boto3.client('sts')
dynamodb = boto3.resource('dynamodb')

# Read config once at module load (before any exec() call)
REGISTRY_TABLE = os.environ.get('CONVERTER_REGISTRY_TABLE')
CONVERTERS_BUCKET = os.environ.get('CONVERTERS_BUCKET')
ZERO_PERMISSION_ROLE_ARN = os.environ.get('ZERO_PERMISSION_ROLE_ARN', '')

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
        
        # --- All AWS calls happen here, BEFORE exec() ---

        # Get converter from registry
        registry_table = dynamodb.Table(REGISTRY_TABLE)
        response = registry_table.get_item(Key={'converter_id': converter_id})

        if 'Item' not in response:
            return error_response(404, f"Converter {converter_id} not found")

        converter = response['Item']

        if converter.get('status') != 'APPROVED':
            return error_response(403, f"Converter {converter_id} not approved")

        # Load converter code from S3
        s3_key = converter.get('s3_location')
        converter_code = s3.get_object(Bucket=CONVERTERS_BUCKET, Key=s3_key)['Body'].read().decode('utf-8')
        
        # Execute converter
        result = execute_converter(converter_code, file_content)
        
        # result may be the raw ASM dict or a {'success': bool, 'asm_output': ..., 'field_mapping': ...} wrapper
        if isinstance(result, dict) and 'success' in result:
            if not result.get('success'):
                return error_response(500, result.get('error', 'Converter returned failure'))
            asm_output = result.get('asm_output', result)
            field_mapping = result.get('field_mapping', [])
        else:
            asm_output = result
            field_mapping = []
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'converter_id': converter_id,
                'asm_output': asm_output,
                'field_mapping': field_mapping,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        return error_response(500, str(e))

# Standard library modules converters are permitted to import.
_ALLOWED_IMPORTS = frozenset({
    'csv', 'io', 're', 'uuid', 'datetime', 'math', 'json',
    'collections', 'itertools', 'functools', 'operator',
    'string', 'textwrap', 'decimal', 'fractions',
    'enum', 'dataclasses', 'typing', 'types', 'copy',
})

_builtin_import = builtins.__import__

def _safe_import(name, *args, **kwargs):
    if name.split('.')[0] not in _ALLOWED_IMPORTS:
        raise ImportError(f"Import of '{name}' is not permitted in converters")
    return _builtin_import(name, *args, **kwargs)


def execute_converter(converter_code, file_content):
    """Execute converter code with minimized blast radius.

    Layer B: Assume a zero-permission IAM role so exec'd code has no AWS access.
    Layer D: Scrub the namespace — remove open(), os.environ, restrict builtins.
    """

    # Layer B — Assume zero-permission role to strip AWS credentials
    original_credentials = None
    if ZERO_PERMISSION_ROLE_ARN:
        try:
            assumed = sts.assume_role(
                RoleArn=ZERO_PERMISSION_ROLE_ARN,
                RoleSessionName='converter-sandbox',
                Policy='{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"*","Resource":"*"}]}'
            )
            # Overwrite environment credentials so boto3 inside exec() gets denied
            original_credentials = {
                'AWS_ACCESS_KEY_ID': os.environ.get('AWS_ACCESS_KEY_ID', ''),
                'AWS_SECRET_ACCESS_KEY': os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
                'AWS_SESSION_TOKEN': os.environ.get('AWS_SESSION_TOKEN', ''),
            }
            os.environ['AWS_ACCESS_KEY_ID'] = assumed['Credentials']['AccessKeyId']
            os.environ['AWS_SECRET_ACCESS_KEY'] = assumed['Credentials']['SecretAccessKey']
            os.environ['AWS_SESSION_TOKEN'] = assumed['Credentials']['SessionToken']
        except Exception:
            pass  # If role assumption fails, continue with namespace scrubbing only

    # Layer D — Clear environment variables (wrapper already read what it needs)
    saved_environ = os.environ.copy()
    os.environ.clear()

    try:
        # Layer D — Build restricted builtins. Replace __import__ with an
        # allowlist version so converters can use standard library modules
        # (csv, re, datetime, etc.) but cannot import boto3, subprocess, etc.
        safe_builtins = vars(builtins).copy()
        for dangerous in ('open', 'exec', 'eval', 'compile'):
            safe_builtins.pop(dangerous, None)
        safe_builtins['__import__'] = _safe_import

        # Create sandboxed namespace
        namespace = {
            '__builtins__': safe_builtins,
            'file_content': file_content,
        }

        # Execute converter code
        exec(converter_code, namespace)  # nosec B102

        # Call convert function
        if 'convert' not in namespace:
            raise Exception("Converter must define 'convert' function")

        return namespace['convert'](file_content)

    finally:
        # Restore environment variables
        os.environ.clear()
        os.environ.update(saved_environ)

        # Restore original credentials if we swapped them
        if original_credentials:
            for key, value in original_credentials.items():
                if value:
                    os.environ[key] = value

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
