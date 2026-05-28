# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at http://aws.amazon.com/apache2.0/
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
"""
ATaaS - ASM Transformation as a Service with Storage
AI-Powered with AWS Bedrock Claude
"""

import json
import logging
import boto3
from botocore.config import Config
import os
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-6')

def _bedrock_client():
    kwargs = {
        'region_name': os.environ.get('AWS_REGION', 'us-east-1'),
        'config': Config(connect_timeout=5, read_timeout=25, retries={'max_attempts': 1}),
    }
    if os.environ.get('BEDROCK_ENDPOINT_URL'):
        kwargs['endpoint_url'] = os.environ['BEDROCK_ENDPOINT_URL']
    return boto3.client('bedrock-runtime', **kwargs)

def lambda_handler(event, context):
    """Minimal ATaaS entry point"""
    
    try:
        # Parse request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            file_content = body.get('file_content', '')
            store_results = body.get('store_results', False)
        else:
            file_content = event.get('file_content', '')
            store_results = event.get('store_results', False)
        
        if not file_content:
            return error_response(400, "No file content provided")
        
        # Single Bedrock call for analysis + conversion + code generation
        file_analysis, asm_output, converter_code = analyze_and_convert_with_claude(file_content)
        
        conversion_id = f"CONV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Simple response
        response = {
            'conversion_id': conversion_id,
            'timestamp': datetime.utcnow().isoformat(),
            'file_analysis': file_analysis,
            'asm_output': asm_output,
            'converter_code': converter_code,
            'status': 'success'
        }
        
        # Store results if requested
        if store_results:
            storage_result = store_conversion_results(response)
            response['storage'] = storage_result
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        return error_response(500, f"Error: {str(e)}")

def store_conversion_results(conversion_data):
    """Store conversion results in S3 and DynamoDB"""
    
    try:
        s3 = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        
        conversion_id = conversion_data.get('conversion_id')
        timestamp = datetime.utcnow().isoformat()
        
        # Get bucket names from environment
        asm_bucket = os.environ.get('ASM_FILES_BUCKET', 'asm-converted-files')
        table_name = os.environ.get('CONVERSION_HISTORY_TABLE', 'ConversionHistory')
        
        # Store ASM file in S3
        asm_key = f"asm_files/{conversion_id}.json"
        s3.put_object(
            Bucket=asm_bucket,
            Key=asm_key,
            Body=json.dumps(conversion_data['asm_output'], indent=2),
            ContentType='application/json'
        )
        
        # Store converter code in S3
        code_stored = False
        if conversion_data.get('converter_code'):
            code_key = f"converter_code/{conversion_id}.py"
            s3.put_object(
                Bucket=asm_bucket,
                Key=code_key,
                Body=conversion_data['converter_code'].get('code', ''),
                ContentType='text/plain'
            )
            code_stored = True
        
        # Store metadata in DynamoDB
        table = dynamodb.Table(table_name)
        table.put_item(
            Item={
                'conversion_id': conversion_id,
                'timestamp': timestamp,
                'file_analysis': conversion_data.get('file_analysis', {}),
                'asm_s3_key': asm_key,
                'converter_s3_key': f"converter_code/{conversion_id}.py" if code_stored else None,
                'source': 'ataas_service',
                'status': 'completed'
            }
        )
        
        return {
            'stored': True,
            'conversion_id': conversion_id,
            'asm_file_stored': True,
            'converter_code_stored': code_stored,
            'storage_location': f's3://{asm_bucket}/{asm_key}',
            'message': 'Results stored successfully'
        }
        
    except Exception as e:
        return {
            'stored': False,
            'error': str(e),
            'message': 'Failed to store results'
        }

def analyze_and_convert_with_claude(file_content):
    """Single Bedrock call: analyze file, produce ASM output, and generate converter code."""

    lines = file_content.strip().split('\n')
    sample_content = '\n'.join(lines[:4])  # header + up to 3 rows

    prompt = f"""You are a laboratory instrument data expert. Analyze the following data file and respond with a single JSON object containing three keys: "file_analysis", "asm_output", and "converter_code".

FILE SAMPLE (header + first 3 rows):
{sample_content}

"file_analysis" must be a JSON object with:
  - file_format: string (CSV, XML, JSON, etc.)
  - instrument_type: string (plate reader, cell counter, spectrophotometer, solution analyzer, etc.)
  - vendor: string or null
  - data_structure: string description of columns/fields
  - sample_count: estimated integer

"asm_output" must be valid Allotrope Simple Model (ASM) JSON for the 2 sample data rows shown, with:
  - $asm.manifest: correct manifest URL for the instrument type
  - measurement document array with measurement identifier, measurement time, and appropriate fields/units

"converter_code" must be a complete executable Python script (as a JSON string) that:
  - Parses this file format
  - Processes ALL rows (not just the sample)
  - Returns proper ASM JSON structure
  - Uses the correct manifest URL
  - Has error handling
  - Defines a convert(file_content) function

Respond ONLY with the JSON object, no other text."""

    manifest_map = {
        'plate reader': 'http://purl.allotrope.org/manifests/plate-reader/REC/2024/09/plate-reader.manifest',
        'cell counter': 'http://purl.allotrope.org/manifests/cell-counter/REC/2024/09/cell-counter.manifest',
        'spectrophotometer': 'http://purl.allotrope.org/manifests/uv-vis-spectroscopy/REC/2024/09/uv-vis-spectroscopy.manifest',
        'solution analyzer': 'http://purl.allotrope.org/manifests/solution-analyzer/BENCHLING/2023/09/solution-analyzer.manifest',
    }

    try:
        response = _bedrock_client().invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 16000,
                "messages": [{"role": "user", "content": prompt}]
            })
        )

        result = json.loads(response['body'].read())
        text = result['content'][0]['text']

        if '{' in text:
            json_start = text.index('{')
            json_end = text.rindex('}') + 1
            parsed = json.loads(text[json_start:json_end])
        else:
            raise ValueError("No JSON in response")

        file_analysis = parsed.get('file_analysis', {'file_format': 'UNKNOWN', 'instrument_type': 'unknown'})
        asm_output = parsed.get('asm_output', create_fallback_asm(manifest_map['solution analyzer']))

        raw_code = parsed.get('converter_code', '')
        if isinstance(raw_code, str):
            code = raw_code
            if '```python' in code:
                code = code.split('```python')[1].split('```')[0].strip()
            elif '```' in code:
                code = code.split('```')[1].split('```')[0].strip()
        else:
            code = str(raw_code)

        file_format = file_analysis.get('file_format', 'CSV')
        instrument_type = file_analysis.get('instrument_type', 'unknown')
        converter_code = {
            'language': 'python',
            'code': code,
            'filename': f'{file_format.lower()}_{instrument_type.replace(" ", "_")}_converter_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.py',
            'generated_by': 'claude-4.6-sonnet'
        }

        return file_analysis, asm_output, converter_code

    except Exception as e:
        logger.error("analyze_and_convert_with_claude failed: %s", e)
        fallback_manifest = manifest_map['solution analyzer']
        return (
            {'file_format': 'UNKNOWN', 'instrument_type': 'unknown', 'error': str(e)},
            create_fallback_asm(fallback_manifest),
            {'language': 'python', 'code': f'# Error: {e}', 'filename': 'converter.py', 'error': str(e)}
        )

def create_fallback_asm(manifest):
    """Create basic ASM structure as fallback"""
    return {
        "$asm.manifest": manifest,
        "measurement document": [{
            "measurement identifier": "SAMPLE_001",
            "measurement time": datetime.utcnow().isoformat(),
            "note": "Fallback ASM structure - manual conversion may be required"
        }]
    }

def error_response(status_code, message):
    """Return error response"""
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