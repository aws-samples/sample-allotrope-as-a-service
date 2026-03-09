import json
import boto3
import base64
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """Simple ASM conversion Lambda handler"""
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        
        # Get file data
        if 'file_data' in body:
            file_data = base64.b64decode(body['file_data'])
            filename = body.get('filename', 'unknown.csv')
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'No file_data provided'})
            }
        
        # Analyze file
        analysis = analyze_file(file_data, filename)
        
        # Generate ASM conversion
        asm_result = generate_asm_conversion(file_data, filename, analysis)
        
        # Return result
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'filename': filename,
                'analysis': analysis,
                'asm_output': asm_result,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def analyze_file(file_data: bytes, filename: str) -> dict:
    """Analyze file format and structure"""
    
    # Basic file analysis
    file_size = len(file_data)
    
    # Try to decode as text
    try:
        text_content = file_data.decode('utf-8')
        is_text = True
        
        # Detect format
        if filename.endswith('.csv') or ',' in text_content[:1000]:
            file_format = 'csv'
        elif filename.endswith('.json') or text_content.strip().startswith('{'):
            file_format = 'json'
        elif filename.endswith('.xml') or '<' in text_content[:100]:
            file_format = 'xml'
        else:
            file_format = 'text'
            
    except UnicodeDecodeError:
        is_text = False
        file_format = 'binary'
        text_content = None
    
    return {
        'format': file_format,
        'size': file_size,
        'is_text': is_text,
        'sample': text_content[:500] if text_content else None
    }

def generate_asm_conversion(file_data: bytes, filename: str, analysis: dict) -> dict:
    """Generate ASM conversion using Bedrock Claude"""
    
    try:
        # Prepare prompt for Claude
        sample_data = analysis.get('sample', '')[:1000]  # Limit sample size
        
        prompt = f"""Convert this laboratory data file to ASM (Allotrope Simple Model) format.

File: {filename}
Format: {analysis['format']}
Size: {analysis['size']} bytes

Sample data:
{sample_data}

Generate a valid ASM JSON structure with:
1. version: "1.0.0"
2. schema: "asm-1.0.0" 
3. data section with measurements, samples, methods, instruments
4. metadata with provenance and timestamp

Return only valid JSON."""

        # Call Bedrock Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        claude_response = response_body['content'][0]['text']
        
        # Extract JSON from Claude response
        try:
            # Find JSON in response
            start_idx = claude_response.find('{')
            end_idx = claude_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = claude_response[start_idx:end_idx]
                asm_data = json.loads(json_str)
            else:
                # Fallback: create basic ASM structure
                asm_data = create_basic_asm(filename, analysis)
                
        except json.JSONDecodeError:
            # Fallback: create basic ASM structure
            asm_data = create_basic_asm(filename, analysis)
        
        return asm_data
        
    except Exception as e:
        logger.error(f"Error generating ASM conversion: {str(e)}")
        return create_basic_asm(filename, analysis)

def create_basic_asm(filename: str, analysis: dict) -> dict:
    """Create basic ASM structure as fallback"""
    
    return {
        "version": "1.0.0",
        "schema": "asm-1.0.0",
        "data": {
            "measurements": [
                {
                    "id": "measurement_1",
                    "type": "laboratory_measurement",
                    "value": 0.0,
                    "unit": "unknown",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "samples": [
                {
                    "id": "sample_1",
                    "name": "Sample from " + filename,
                    "type": "laboratory_sample"
                }
            ],
            "methods": [
                {
                    "id": "method_1",
                    "name": "File Conversion Method",
                    "type": "data_conversion"
                }
            ],
            "instruments": [
                {
                    "id": "instrument_1",
                    "name": "Unknown Instrument",
                    "manufacturer": "Unknown",
                    "model": "Unknown"
                }
            ]
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "source_file": filename,
            "source_format": analysis['format'],
            "converter": "ASM POC Service",
            "provenance": {
                "conversion_method": "AI-powered conversion",
                "service_version": "1.0.0"
            }
        }
    }