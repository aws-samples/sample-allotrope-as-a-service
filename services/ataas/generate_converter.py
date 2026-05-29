# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
AI Converter Generator
Analyzes instrument files and generates custom converter code using AWS Bedrock Claude.
Auto-registers the generated converter in the Custom Converter Registry.
"""

import json
import boto3
import os
from datetime import datetime, timezone

bedrock_kwargs = {'region_name': os.environ.get('AWS_REGION', 'us-east-1')}
if os.environ.get('BEDROCK_ENDPOINT_URL'):
    bedrock_kwargs['endpoint_url'] = os.environ['BEDROCK_ENDPOINT_URL']
bedrock = boto3.client('bedrock-runtime', **bedrock_kwargs)
MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-3-5-sonnet-20241022-v2:0')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

REQUIREMENTS_TEMPLATE = """
CRITICAL REQUIREMENTS for the generated converter:

1. Function signature: def convert(file_content):
   - Accepts a single string parameter (raw file content)
   - No file paths, no filesystem access

2. Return format on success:
   return {
       "success": True,
       "asm_output": { ... },      # Complete ASM JSON
       "field_mapping": [ ... ]     # Every source value mapped
   }

3. Return format on failure:
   return {"success": False, "error": "description"}

4. field_mapping REQUIRED - every value from the source must have an entry:
   {"source_field": "pH", "source_value": 7.183, "asm_field": "pH", "asm_value": 7.183, "unit": "pH"}

5. ASM structure must include:
   - "$asm.manifest" with correct URL for the instrument type
   - measurement documents with UUID identifiers (import uuid, str(uuid.uuid4()))
   - ISO 8601 timestamps with timezone
   - sample document with sample identifier
   - device system document and device control documents

6. NO imports of: os, sys, pathlib, subprocess, requests, socket
   ALLOWED imports: json, csv, io, uuid, datetime, re, xml.etree.ElementTree

7. Must handle empty input gracefully (return error, don't crash)

8. Custom fields go in custom information aggregate document as 1:1 transfer
9. Calculated fields go in calculated data aggregate document with data source traceability
"""


def lambda_handler(event, context):
    """Generate a custom converter from an instrument file sample."""
    try:
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        file_content = body.get('file_content', '')
        file_name = body.get('file_name', 'unknown.txt')
        manifest = body.get('manifest', {})
        auto_register = body.get('auto_register', True)

        if not file_content:
            return error_response(400, "No file content provided")

        vendor = manifest.get('vendor', 'UNKNOWN')
        model = manifest.get('model', 'unknown')
        instrument_type = manifest.get('instrument_type', 'unknown')
        file_format = manifest.get('file_format', file_name.split('.')[-1] if '.' in file_name else 'txt')

        # Step 1: Analyze file structure (headers + 3 sample rows)
        lines = file_content.strip().split('\n')
        sample_lines = lines[:min(4, len(lines))]
        sample_content = '\n'.join(sample_lines)
        total_rows = len(lines) - 1  # minus header

        # Step 2: Generate converter code with Claude
        converter_code = generate_converter(sample_content, file_format, instrument_type, vendor, model, total_rows)

        if not converter_code:
            return error_response(500, "Failed to generate converter code")

        # Step 3: Auto-register if requested
        converter_id = f"{vendor.lower().replace(' ', '-')}-{model.lower().replace(' ', '-')}-ai-v1"
        converter_id = ''.join(c if c.isalnum() or c == '-' else '-' for c in converter_id)

        registration = None
        if auto_register:
            registration = register_converter(converter_id, converter_code, vendor, model, instrument_type)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'converter_id': converter_id,
                'converter_code': converter_code,
                'file_analysis': {
                    'file_format': file_format,
                    'instrument_type': instrument_type,
                    'vendor': vendor,
                    'model': model,
                    'sample_rows': len(sample_lines) - 1,
                    'total_rows': total_rows,
                    'columns': sample_lines[0] if sample_lines else ''
                },
                'registration': registration,
                'status': 'success',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

    except Exception as e:
        return error_response(500, f"Error: {str(e)}")


def generate_converter(sample_content, file_format, instrument_type, vendor, model, total_rows):
    """Use Claude to generate converter code following our requirements."""

    manifest_map = {
        'solution_analyzer': 'http://purl.allotrope.org/manifests/solution-analyzer/REC/2025/06/solution-analyzer.manifest',
        'plate_reader': 'http://purl.allotrope.org/manifests/plate-reader/REC/2025/12/plate-reader.manifest',
        'cell_counter': 'http://purl.allotrope.org/manifests/cell-counting/REC/2025/12/cell-counting.manifest',
        'spectrophotometer': 'http://purl.allotrope.org/manifests/uv-vis/REC/2025/12/uv-vis.manifest',
        'chromatography': 'http://purl.allotrope.org/manifests/liquid-chromatography/REC/2025/12/liquid-chromatography.manifest',
    }
    asm_manifest = manifest_map.get(instrument_type, manifest_map.get('solution_analyzer'))

    prompt = f"""Generate a Python converter for a {vendor} {model} ({instrument_type}) instrument that outputs {file_format.upper()} files.

INSTRUMENT FILE SAMPLE (headers + sample rows from a file with {total_rows} total data rows):
{sample_content}

ASM MANIFEST URL: {asm_manifest}
DEVICE INFO: vendor="{vendor}", model="{model}", instrument_type="{instrument_type}"

{REQUIREMENTS_TEMPLATE}

Generate COMPLETE, EXECUTABLE Python code. The converter must:
- Parse ALL rows in the file (not just the sample shown)
- Map EVERY column to either a measurement field, calculated field, or custom field
- Include field_mapping entry for EVERY value
- Use the correct ASM manifest URL shown above
- Set product manufacturer to "{vendor.lower()}" and device identifier to "{model.lower()}"

Respond ONLY with Python code. No explanations, no markdown code blocks."""

    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 8000,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )

        result = json.loads(response['body'].read())
        code = result['content'][0]['text']

        # Clean up code blocks if present
        if '```python' in code:
            code = code.split('```python')[1].split('```')[0].strip()
        elif '```' in code:
            code = code.split('```')[1].split('```')[0].strip()

        return code

    except Exception as e:
        return None


def register_converter(converter_id, converter_code, vendor, model, instrument_type):
    """Register the generated converter in the Custom Converter Registry."""
    try:
        bucket = os.environ.get('CONVERTERS_BUCKET')
        table_name = os.environ.get('CONVERTER_REGISTRY_TABLE')

        if not bucket or not table_name:
            return {'registered': False, 'error': 'Missing environment variables'}

        # Store code in S3
        s3_key = f"converters/{converter_id}.py"
        s3.put_object(Bucket=bucket, Key=s3_key, Body=converter_code)

        # Register in DynamoDB
        table = dynamodb.Table(table_name)
        table.put_item(Item={
            'converter_id': converter_id,
            'vendor': vendor,
            'model': model,
            'instrument_type': instrument_type,
            's3_location': s3_key,
            'status': 'PENDING',
            'generated_by': 'ai-bedrock-claude',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'description': f'AI-generated converter for {vendor} {model} ({instrument_type})'
        })

        return {
            'registered': True,
            'converter_id': converter_id,
            'status': 'PENDING',
            's3_location': s3_key,
            'message': 'Converter registered. Review and approve before use.'
        }

    except Exception as e:
        return {'registered': False, 'error': str(e)}


def error_response(status_code, message):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    }
