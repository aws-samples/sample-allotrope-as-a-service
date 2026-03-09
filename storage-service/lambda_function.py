"""
ASM Storage Service
Stores converted ASM files, validation results, and conversion history
"""

import json
import boto3
from datetime import datetime
from uuid import uuid4

def lambda_handler(event, context):
    """Storage service entry point"""
    
    try:
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        action = body.get('action')
        
        if action == 'store_conversion':
            return store_conversion_result(body)
        elif action == 'get_conversion_history':
            return get_conversion_history()
        elif action == 'get_asm_file':
            return get_asm_file(body)
        else:
            return error_response(400, "Invalid action")
            
    except Exception as e:
        return error_response(500, f"Storage error: {str(e)}")

def store_conversion_result(data):
    """Store complete conversion result"""
    
    # AWS clients
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    
    conversion_id = data.get('conversion_id', str(uuid4()))
    timestamp = datetime.utcnow().isoformat()
    
    # Store ASM file in S3
    asm_output = data.get('asm_output', {})
    asm_key = None
    if asm_output:
        asm_key = f"asm_files/{conversion_id}.json"
        s3.put_object(
            Bucket='asm-converted-files',
            Key=asm_key,
            Body=json.dumps(asm_output, indent=2),
            ContentType='application/json'
        )
    
    # Store validation results in S3
    validation_result = data.get('validation', {})
    validation_key = None
    if validation_result:
        validation_key = f"validation_results/{conversion_id}.json"
        s3.put_object(
            Bucket='asm-validation-results',
            Key=validation_key,
            Body=json.dumps(validation_result, indent=2),
            ContentType='application/json'
        )
    
    # Store conversion record in DynamoDB
    table = dynamodb.Table('ConversionHistory')
    
    conversion_record = {
        'conversion_id': conversion_id,
        'timestamp': timestamp,
        'file_analysis': data.get('file_analysis', {}),
        'asm_s3_key': asm_key,
        'validation_s3_key': validation_key,
        'converter_code_info': data.get('converter_code', {}),
        'source': data.get('source', 'unknown'),
        'status': 'completed'
    }
    
    table.put_item(Item=conversion_record)
    
    return success_response({
        'conversion_id': conversion_id,
        'asm_file_stored': asm_key is not None,
        'validation_stored': validation_key is not None,
        'stored_at': timestamp
    })

def get_conversion_history():
    """Get recent conversion history"""
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ConversionHistory')
    
    response = table.scan(Limit=50)
    
    conversions = []
    for item in response['Items']:
        conversions.append({
            'conversion_id': item['conversion_id'],
            'timestamp': item['timestamp'],
            'format': item.get('file_analysis', {}).get('format'),
            'instrument_type': item.get('file_analysis', {}).get('instrument_type'),
            'asm_available': item.get('asm_s3_key') is not None,
            'validation_available': item.get('validation_s3_key') is not None
        })
    
    conversions.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return success_response({
        'conversions': conversions,
        'count': len(conversions)
    })

def get_asm_file(data):
    """Get ASM file content"""
    
    conversion_id = data.get('conversion_id')
    if not conversion_id:
        return error_response(400, "Missing conversion_id")
    
    try:
        s3 = boto3.client('s3')
        asm_key = f"asm_files/{conversion_id}.json"
        response = s3.get_object(Bucket='asm-converted-files', Key=asm_key)
        asm_content = response['Body'].read().decode('utf-8')
        
        return success_response({
            'conversion_id': conversion_id,
            'asm_content': json.loads(asm_content)
        })
        
    except Exception as e:
        return error_response(404, f"ASM file not found: {str(e)}")

def success_response(data):
    """Return success response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            **data,
            'timestamp': datetime.utcnow().isoformat()
        })
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