"""
Approval Workflow Service
Manages converter code review and approval process
"""

import json
import boto3
from datetime import datetime
from uuid import uuid4

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Configuration
CONVERTERS_TABLE = 'ConverterApprovals'
APPROVED_BUCKET = 'asm-approved-converters'
PENDING_BUCKET = 'asm-pending-converters'

def lambda_handler(event, context):
    """Main handler for approval workflow operations"""
    
    try:
        # Parse request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        action = body.get('action')
        
        if action == 'submit_for_review':
            return submit_for_review(body)
        elif action == 'get_pending':
            return get_pending_converters()
        elif action == 'approve':
            return approve_converter(body)
        elif action == 'reject':
            return reject_converter(body)
        elif action == 'get_approved':
            return get_approved_converters()
        else:
            return error_response(400, "Invalid action")
            
    except Exception as e:
        return error_response(500, f"Workflow error: {str(e)}")

def submit_for_review(data):
    """Submit generated converter for human review"""
    
    converter_id = str(uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Store converter metadata in DynamoDB
    table = dynamodb.Table(CONVERTERS_TABLE)
    
    converter_item = {
        'converter_id': converter_id,
        'status': 'PENDING_REVIEW',
        'generated_at': timestamp,
        'code': data.get('code', ''),
        'metadata': {
            'language': data.get('language', 'python'),
            'filename': data.get('filename', 'converter.py'),
            'format': data.get('format', 'unknown'),
            'instrument_type': data.get('instrument_type', 'generic'),
            'conversion_id': data.get('conversion_id', '')
        },
        'file_analysis': data.get('file_analysis', {}),
        'test_data': data.get('test_data', '')
    }
    
    table.put_item(Item=converter_item)
    
    # Store code file in S3 for review
    s3.put_object(
        Bucket=PENDING_BUCKET,
        Key=f"{converter_id}/{data.get('filename', 'converter.py')}",
        Body=data.get('code', ''),
        ContentType='text/plain'
    )
    
    return success_response({
        'converter_id': converter_id,
        'status': 'PENDING_REVIEW',
        'message': 'Converter submitted for review'
    })

def get_pending_converters():
    """Get all converters pending review"""
    
    table = dynamodb.Table(CONVERTERS_TABLE)
    
    response = table.query(
        IndexName='StatusIndex',
        KeyConditionExpression='#status = :status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':status': 'PENDING_REVIEW'},
        ScanIndexForward=False  # Latest first
    )
    
    converters = []
    for item in response['Items']:
        converters.append({
            'converter_id': item['converter_id'],
            'generated_at': item['generated_at'],
            'metadata': item.get('metadata', {}),
            'file_analysis': item.get('file_analysis', {}),
            'code_preview': item.get('code', '')[:200] + '...'
        })
    
    return success_response({
        'pending_converters': converters,
        'count': len(converters)
    })

def approve_converter(data):
    """Approve converter and move to library"""
    
    converter_id = data.get('converter_id')
    reviewer_id = data.get('reviewer_id', 'system')
    signature = data.get('signature', '')
    
    if not converter_id:
        return error_response(400, "Missing converter_id")
    
    table = dynamodb.Table(CONVERTERS_TABLE)
    timestamp = datetime.utcnow().isoformat()
    
    # Get converter details
    response = table.get_item(Key={'converter_id': converter_id})
    if 'Item' not in response:
        return error_response(404, "Converter not found")
    
    converter = response['Item']
    
    # Update status to approved
    table.update_item(
        Key={'converter_id': converter_id},
        UpdateExpression='SET #status = :status, reviewed_at = :timestamp, reviewer_id = :reviewer, approval_signature = :signature',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'APPROVED',
            ':timestamp': timestamp,
            ':reviewer': reviewer_id,
            ':signature': signature
        }
    )
    
    # Move code to approved bucket
    filename = converter.get('metadata', {}).get('filename', 'converter.py')
    
    # Copy from pending to approved
    s3.copy_object(
        CopySource={'Bucket': PENDING_BUCKET, 'Key': f"{converter_id}/{filename}"},
        Bucket=APPROVED_BUCKET,
        Key=f"{converter_id}/{filename}"
    )
    
    # Add metadata file
    metadata = {
        'converter_id': converter_id,
        'approved_at': timestamp,
        'reviewer_id': reviewer_id,
        'metadata': converter.get('metadata', {}),
        'file_analysis': converter.get('file_analysis', {})
    }
    
    s3.put_object(
        Bucket=APPROVED_BUCKET,
        Key=f"{converter_id}/metadata.json",
        Body=json.dumps(metadata, indent=2),
        ContentType='application/json'
    )
    
    return success_response({
        'converter_id': converter_id,
        'status': 'APPROVED',
        'approved_at': timestamp,
        'message': 'Converter approved and deployed to library'
    })

def reject_converter(data):
    """Reject converter with feedback"""
    
    converter_id = data.get('converter_id')
    reviewer_id = data.get('reviewer_id', 'system')
    feedback = data.get('feedback', 'No feedback provided')
    
    if not converter_id:
        return error_response(400, "Missing converter_id")
    
    table = dynamodb.Table(CONVERTERS_TABLE)
    timestamp = datetime.utcnow().isoformat()
    
    # Update status to rejected
    table.update_item(
        Key={'converter_id': converter_id},
        UpdateExpression='SET #status = :status, reviewed_at = :timestamp, reviewer_id = :reviewer, feedback = :feedback',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'REJECTED',
            ':timestamp': timestamp,
            ':reviewer': reviewer_id,
            ':feedback': feedback
        }
    )
    
    return success_response({
        'converter_id': converter_id,
        'status': 'REJECTED',
        'feedback': feedback,
        'message': 'Converter rejected'
    })

def get_approved_converters():
    """Get all approved converters in library"""
    
    table = dynamodb.Table(CONVERTERS_TABLE)
    
    response = table.query(
        IndexName='StatusIndex',
        KeyConditionExpression='#status = :status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':status': 'APPROVED'},
        ScanIndexForward=False  # Latest first
    )
    
    converters = []
    for item in response['Items']:
        converters.append({
            'converter_id': item['converter_id'],
            'approved_at': item.get('reviewed_at'),
            'reviewer_id': item.get('reviewer_id'),
            'metadata': item.get('metadata', {}),
            'download_url': f"s3://{APPROVED_BUCKET}/{item['converter_id']}/{item.get('metadata', {}).get('filename', 'converter.py')}"
        })
    
    return success_response({
        'approved_converters': converters,
        'count': len(converters)
    })

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