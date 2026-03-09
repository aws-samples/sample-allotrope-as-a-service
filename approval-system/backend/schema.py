"""
DynamoDB Schema for Converter Approval Workflow

Table: ConverterApprovals
- converter_id (PK): Unique ID for each generated converter
- status: PENDING_REVIEW | APPROVED | REJECTED
- generated_at: Timestamp
- reviewed_at: Timestamp (optional)
- reviewer_id: User who reviewed (optional)
- code: Generated converter code
- metadata: File format, instrument type, etc.
- approval_signature: Electronic signature (optional)
"""

CONVERTER_STATUS = {
    'PENDING_REVIEW': 'Awaiting human review',
    'APPROVED': 'Approved and deployed to library',
    'REJECTED': 'Rejected with feedback'
}

SCHEMA = {
    'TableName': 'ConverterApprovals',
    'KeySchema': [
        {'AttributeName': 'converter_id', 'KeyType': 'HASH'}
    ],
    'AttributeDefinitions': [
        {'AttributeName': 'converter_id', 'AttributeType': 'S'},
        {'AttributeName': 'status', 'AttributeType': 'S'},
        {'AttributeName': 'generated_at', 'AttributeType': 'S'}
    ],
    'GlobalSecondaryIndexes': [
        {
            'IndexName': 'StatusIndex',
            'KeySchema': [
                {'AttributeName': 'status', 'KeyType': 'HASH'},
                {'AttributeName': 'generated_at', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }
    ]
}