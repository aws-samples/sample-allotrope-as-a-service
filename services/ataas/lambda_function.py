"""
ATaaS - ASM Transformation as a Service with Storage
AI-Powered with AWS Bedrock Claude
"""

import json
import boto3
import os
from datetime import datetime

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

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
        
        # AI-powered file analysis
        file_analysis = analyze_file_with_claude(file_content)
        
        # AI-powered ASM conversion
        asm_output = convert_to_asm_with_claude(file_content, file_analysis)
        
        # AI-powered converter code generation
        converter_code = generate_converter_with_claude(file_content, file_analysis)
        
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

def analyze_file_with_claude(file_content):
    """Use Claude to analyze file format and structure"""
    
    # Optimize: Send only headers + first 3 rows for analysis
    lines = file_content.strip().split('\n')[:4]  # Header + 3 sample rows
    sample_content = '\n'.join(lines)
    
    prompt = f"""Analyze this laboratory instrument data file and provide a JSON response with:
1. file_format (CSV, XML, JSON, etc.)
2. instrument_type (plate reader, cell counter, spectrophotometer, solution analyzer, etc.)
3. vendor (if identifiable)
4. data_structure (description of columns/fields)
5. sample_count (estimated from structure)

File sample (headers + first 3 rows):
{sample_content}

Respond ONLY with valid JSON, no other text."""
    
    try:
        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        analysis_text = result['content'][0]['text']
        
        # Extract JSON from response
        if '{' in analysis_text:
            json_start = analysis_text.index('{')
            json_end = analysis_text.rindex('}') + 1
            analysis = json.loads(analysis_text[json_start:json_end])
        else:
            analysis = {'file_format': 'UNKNOWN', 'instrument_type': 'unknown'}
        
        return analysis
        
    except Exception as e:
        return {
            'file_format': 'UNKNOWN',
            'instrument_type': 'unknown',
            'error': str(e)
        }

def convert_to_asm_with_claude(file_content, analysis):
    """Use Claude to convert file to ASM format"""
    
    instrument_type = analysis.get('instrument_type', 'solution analyzer')
    
    # Map instrument type to ASM manifest
    manifest_map = {
        'plate reader': 'http://purl.allotrope.org/manifests/plate-reader/REC/2024/09/plate-reader.manifest',
        'cell counter': 'http://purl.allotrope.org/manifests/cell-counter/REC/2024/09/cell-counter.manifest',
        'spectrophotometer': 'http://purl.allotrope.org/manifests/uv-vis-spectroscopy/REC/2024/09/uv-vis-spectroscopy.manifest',
        'solution analyzer': 'http://purl.allotrope.org/manifests/solution-analyzer/BENCHLING/2023/09/solution-analyzer.manifest'
    }
    
    manifest = manifest_map.get(instrument_type, manifest_map['solution analyzer'])
    
    # Optimize: Send only first 2 rows for conversion example
    lines = file_content.strip().split('\n')[:3]  # Header + 2 rows
    sample_content = '\n'.join(lines)
    
    prompt = f"""Convert this laboratory instrument data to Allotrope Simple Model (ASM) JSON format.

Instrument Type: {instrument_type}
ASM Manifest: {manifest}

File sample (first 2 data rows):
{sample_content}

Generate valid ASM JSON with:
- Correct manifest URL
- measurement document array
- measurement identifier, measurement time for each
- appropriate data fields based on instrument type
- proper units for all measurements

IMPORTANT: Generate structure for ONLY the 2 sample rows shown. The converter code will handle all rows.

Respond ONLY with valid JSON, no other text."""
    
    try:
        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 8000,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        asm_text = result['content'][0]['text']
        
        # Extract JSON from response
        if '{' in asm_text:
            json_start = asm_text.index('{')
            json_end = asm_text.rindex('}') + 1
            asm_output = json.loads(asm_text[json_start:json_end])
        else:
            asm_output = create_fallback_asm(manifest)
        
        return asm_output
        
    except Exception as e:
        return create_fallback_asm(manifest)

def generate_converter_with_claude(file_content, analysis):
    """Use Claude to generate converter code"""
    
    file_format = analysis.get('file_format', 'CSV')
    instrument_type = analysis.get('instrument_type', 'unknown')
    
    # Optimize: Send only headers + 2 sample rows
    lines = file_content.strip().split('\n')[:3]
    sample_content = '\n'.join(lines)
    
    prompt = f"""Generate a Python converter script that converts {file_format} files from {instrument_type} instruments to ASM format.

Example input (headers + 2 sample rows):
{sample_content}

Requirements:
1. Parse the {file_format} format
2. Extract all measurements/samples from ANY number of rows
3. Convert to proper ASM JSON structure
4. Include proper manifest URL for {instrument_type}
5. Handle errors gracefully
6. Make it reusable for similar files
7. Process ALL rows in the file, not just the sample shown

Generate complete, executable Python code with:
- Proper imports
- Function to convert entire file
- Error handling
- Comments explaining key sections

Respond ONLY with Python code, no explanations."""
    
    try:
        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-3-5-sonnet-20241022-v2:0',
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
        
        return {
            'language': 'python',
            'code': code,
            'filename': f'{file_format.lower()}_{instrument_type.replace(" ", "_")}_converter_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.py',
            'generated_by': 'claude-3.5-sonnet'
        }
        
    except Exception as e:
        return {
            'language': 'python',
            'code': f'# Error generating converter: {str(e)}',
            'filename': f'converter_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.py',
            'error': str(e)
        }

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