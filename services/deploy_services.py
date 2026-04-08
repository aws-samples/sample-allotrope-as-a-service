#!/usr/bin/env python3
"""
CDK Stack for Autonomous ATaaS and DVaaS Services
"""

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class AutonomousServicesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda Layer for reportlab
        reportlab_layer = _lambda.LayerVersion(
            self, "ReportlabLayer",
            code=_lambda.Code.from_asset("lambda-layers/reportlab-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="Reportlab for PDF generation"
        )

        # Lambda Layer for jsonschema-rs
        jsonschema_rs_layer = _lambda.LayerVersion(
            self, "JsonschemaRsLayer",
            code=_lambda.Code.from_asset("lambda-layers/jsonschema-rs-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="jsonschema-rs for Allotrope schema validation"
        )

        # DVaaS Lambda Function
        dvaas_lambda = _lambda.Function(
            self, "DVaaSFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("dvaas"),
            layers=[reportlab_layer, jsonschema_rs_layer],
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment={
                "SERVICE_NAME": "DVaaS",
                "CONVERSION_HISTORY_TABLE": "ConversionHistory"
            }
        )

        # ATaaS Lambda Function
        ataas_lambda = _lambda.Function(
            self, "ATaaSFunction", 
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("ataas"),
            timeout=Duration.seconds(300),
            memory_size=2048,
            environment={
                "DVAAS_ENDPOINT": "internal",  # Will be updated after DVaaS API creation
                "SERVICE_NAME": "ATaaS",
                # Optional: set these to route through a custom LLM gateway
                # "BEDROCK_ENDPOINT_URL": "https://your-llm-gateway.internal.company.com",
                # "BEDROCK_MODEL_ID": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            }
        )

        # Add S3 buckets for storage (names include account ID for global uniqueness)
        asm_files_bucket = s3.Bucket(
            self, "ASMConvertedFiles",
            bucket_name=f"asm-converted-files-{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        validation_results_bucket = s3.Bucket(
            self, "ASMValidationResults",
            bucket_name=f"asm-validation-results-{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Add DynamoDB table for conversion history
        conversion_history_table = dynamodb.Table(
            self, "ConversionHistory",
            table_name="ConversionHistory",
            partition_key=dynamodb.Attribute(
                name="conversion_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Validation Rule Sets table
        rule_sets_table = dynamodb.Table(
            self, "ValidationRuleSets",
            table_name="ValidationRuleSets",
            partition_key=dynamodb.Attribute(
                name="rule_set_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Users table for authentication
        users_table = dynamodb.Table(
            self, "UsersTable",
            table_name="ASMUsers",
            partition_key=dynamodb.Attribute(
                name="email",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # JWT secret - auto-generated per deployment (unique per AWS account + stack)
        jwt_secret = f"{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.STACK_NAME}-asm-jwt-secret"

        # Custom Converter Registry table
        converter_registry_table = dynamodb.Table(
            self, "CustomConverterRegistry",
            table_name="CustomConverterRegistry",
            partition_key=dynamodb.Attribute(
                name="converter_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # S3 bucket for custom converters
        converters_bucket = s3.Bucket(
            self, "CustomConvertersBucket",
            bucket_name=f"custom-converters-{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Grant storage permissions to ATaaS
        asm_files_bucket.grant_read_write(ataas_lambda)
        validation_results_bucket.grant_read_write(ataas_lambda)
        conversion_history_table.grant_read_write_data(ataas_lambda)

        # Grant DVaaS write access to store validation jobs
        conversion_history_table.grant_write_data(dvaas_lambda)

        # Multi-Instrument Lambda Function
        multi_instrument_lambda = _lambda.Function(
            self, "MultiInstrumentFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("multi-instrument"),
            timeout=Duration.seconds(300),
            memory_size=512,
            environment={
                "ASM_FILES_BUCKET": asm_files_bucket.bucket_name,
                "CONVERSION_HISTORY_TABLE": conversion_history_table.table_name,
                "SERVICE_NAME": "MultiInstrument"
            }
        )

        # Grant permissions to multi-instrument service
        asm_files_bucket.grant_read_write(multi_instrument_lambda)
        conversion_history_table.grant_read_write_data(multi_instrument_lambda)

        # Update ATaaS environment variables
        ataas_lambda.add_environment("ASM_FILES_BUCKET", asm_files_bucket.bucket_name)
        ataas_lambda.add_environment("VALIDATION_RESULTS_BUCKET", validation_results_bucket.bucket_name)
        ataas_lambda.add_environment("CONVERSION_HISTORY_TABLE", conversion_history_table.table_name)
        ataas_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"]
            )
        )

        # DVaaS API Gateway
        dvaas_api = apigateway.RestApi(
            self, "DVaaSAPI",
            rest_api_name="DVaaS - Data Validation as a Service",
            description="Standalone ASM validation service",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # DVaaS endpoints
        validate_resource = dvaas_api.root.add_resource("validate")
        validate_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(dvaas_lambda),
            method_responses=[{
                "statusCode": "200",
                "responseHeaders": {
                    "Access-Control-Allow-Origin": True
                }
            }]
        )

        # Health check for DVaaS
        health_resource = dvaas_api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[{
                    "statusCode": "200",
                    "responseTemplates": {
                        "application/json": '{"status": "healthy", "service": "DVaaS"}'
                    }
                }],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[{"statusCode": "200"}]
        )

        # ATaaS API Gateway
        ataas_api = apigateway.RestApi(
            self, "ATaaSAPI",
            rest_api_name="ATaaS - ASM Transformation as a Service",
            description="File conversion and code generation service",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # ATaaS endpoints
        convert_resource = ataas_api.root.add_resource("convert")
        convert_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(ataas_lambda),
            method_responses=[{
                "statusCode": "200",
                "responseHeaders": {
                    "Access-Control-Allow-Origin": True
                }
            }]
        )

        # AI Converter Generator Lambda
        generate_converter_lambda = _lambda.Function(
            self, "GenerateConverterFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="generate_converter.lambda_handler",
            code=_lambda.Code.from_asset("ataas"),
            timeout=Duration.seconds(120),
            memory_size=1024,
            environment={
                "CONVERTER_REGISTRY_TABLE": converter_registry_table.table_name,
                "CONVERTERS_BUCKET": converters_bucket.bucket_name,
                "SERVICE_NAME": "GenerateConverter",
                # Optional: set these to route through a custom LLM gateway
                # "BEDROCK_ENDPOINT_URL": "https://your-llm-gateway.internal.company.com",
                # "BEDROCK_MODEL_ID": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            }
        )

        # Grant permissions
        generate_converter_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=["*"]
            )
        )
        converter_registry_table.grant_write_data(generate_converter_lambda)
        converters_bucket.grant_write(generate_converter_lambda)

        # Generate converter endpoint on ATaaS API
        generate_resource = ataas_api.root.add_resource("generate-converter")
        generate_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(generate_converter_lambda),
            method_responses=[{
                "statusCode": "200",
                "responseHeaders": {
                    "Access-Control-Allow-Origin": True
                }
            }]
        )

        # Health check for ATaaS
        ataas_health = ataas_api.root.add_resource("health")
        ataas_health.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[{
                    "statusCode": "200",
                    "responseTemplates": {
                        "application/json": '{"status": "healthy", "service": "ATaaS"}'
                    }
                }],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[{"statusCode": "200"}]
        )

        # Multi-Instrument API Gateway
        multi_instrument_api = apigateway.RestApi(
            self, "MultiInstrumentAPI",
            rest_api_name="Multi-Instrument ASM Converter",
            description="Multi-instrument ASM conversion service",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # Multi-instrument endpoints
        multi_convert_resource = multi_instrument_api.root.add_resource("convert")
        multi_convert_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(multi_instrument_lambda),
            method_responses=[{
                "statusCode": "200",
                "responseHeaders": {
                    "Access-Control-Allow-Origin": True
                }
            }]
        )

        # Health check for multi-instrument
        multi_health = multi_instrument_api.root.add_resource("health")
        multi_health.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[{
                    "statusCode": "200",
                    "responseTemplates": {
                        "application/json": '{"status": "healthy", "service": "MultiInstrument"}'
                    }
                }],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[{"statusCode": "200"}]
        )

        # Custom Converter Service Lambda
        custom_converter_lambda = _lambda.Function(
            self, "CustomConverterFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("custom-converter"),
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                "CONVERTER_REGISTRY_TABLE": converter_registry_table.table_name,
                "CONVERTERS_BUCKET": converters_bucket.bucket_name,
                "SERVICE_NAME": "CustomConverter"
            }
        )

        # Grant permissions
        converter_registry_table.grant_read_data(custom_converter_lambda)
        converters_bucket.grant_read(custom_converter_lambda)

        # Custom Converter API
        custom_converter_api = apigateway.RestApi(
            self, "CustomConverterAPI",
            rest_api_name="Custom Converter Service",
            description="Execute approved custom converters",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # Execute endpoint
        execute_resource = custom_converter_api.root.add_resource("execute")
        execute_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(custom_converter_lambda),
            method_responses=[{
                "statusCode": "200",
                "responseHeaders": {
                    "Access-Control-Allow-Origin": True
                }
            }]
        )

        # Register endpoint (for uploading converters)
        register_resource = custom_converter_api.root.add_resource("register")
        register_lambda = _lambda.Function(
            self, "RegisterConverterFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        
        converter_id = body.get('converter_id')
        converter_code = body.get('converter_code')
        vendor = body.get('vendor')
        model = body.get('model')
        instrument_type = body.get('instrument_type')
        
        if not all([converter_id, converter_code, vendor, model, instrument_type]):
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing required fields'})}
        
        # Store converter in S3
        bucket = os.environ['CONVERTERS_BUCKET']
        s3_key = f"converters/{converter_id}.py"
        s3.put_object(Bucket=bucket, Key=s3_key, Body=converter_code)
        
        # Create registry entry
        table = dynamodb.Table(os.environ['CONVERTER_REGISTRY_TABLE'])
        table.put_item(Item={
            'converter_id': converter_id,
            'vendor': vendor,
            'model': model,
            'instrument_type': instrument_type,
            's3_location': s3_key,
            'status': 'PENDING',
            'created_at': datetime.utcnow().isoformat()
        })
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'converter_id': converter_id, 'status': 'PENDING'})
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
"""),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "CONVERTER_REGISTRY_TABLE": converter_registry_table.table_name,
                "CONVERTERS_BUCKET": converters_bucket.bucket_name
            }
        )
        
        converter_registry_table.grant_write_data(register_lambda)
        converters_bucket.grant_write(register_lambda)
        
        register_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(register_lambda),
            method_responses=[{"statusCode": "200"}]
        )

        # Approve endpoint
        approve_resource = custom_converter_api.root.add_resource("approve")
        approve_lambda = _lambda.Function(
            self, "ApproveConverterFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        converter_id = body.get('converter_id')
        approved_by = body.get('approved_by', 'system')
        status = body.get('status', 'APPROVED')
        comments = body.get('comments', '')
        
        if not converter_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'converter_id required'})}
        
        if status not in ('APPROVED', 'REJECTED'):
            return {'statusCode': 400, 'body': json.dumps({'error': 'status must be APPROVED or REJECTED'})}
        
        table = dynamodb.Table(os.environ['CONVERTER_REGISTRY_TABLE'])
        table.update_item(
            Key={'converter_id': converter_id},
            UpdateExpression='SET #status = :status, approved_by = :approved_by, comments = :comments',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': status, ':approved_by': approved_by, ':comments': comments}
        )
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'converter_id': converter_id, 'status': status})
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
"""),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "CONVERTER_REGISTRY_TABLE": converter_registry_table.table_name
            }
        )
        
        converter_registry_table.grant_write_data(approve_lambda)
        
        approve_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(approve_lambda),
            method_responses=[{"statusCode": "200"}]
        )

        # List endpoint (for dashboard)
        list_lambda = _lambda.Function(
            self, "ListConvertersFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        table = dynamodb.Table(os.environ['CONVERTER_REGISTRY_TABLE'])
        response = table.scan()
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'converters': response.get('Items', [])})
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
"""),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "CONVERTER_REGISTRY_TABLE": converter_registry_table.table_name
            }
        )
        
        converter_registry_table.grant_read_data(list_lambda)
        
        list_resource = custom_converter_api.root.add_resource("list")
        list_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(list_lambda),
            method_responses=[{"statusCode": "200"}]
        )

        # --- Validation Rule Sets CRUD ---
        rule_sets_resource = custom_converter_api.root.add_resource("rule-sets")

        # Save/update rule set
        save_rule_set_lambda = _lambda.Function(
            self, "SaveRuleSetFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        rule_set_id = body.get('rule_set_id')
        if not rule_set_id:
            return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'rule_set_id required'})}
        body['updated_at'] = datetime.utcnow().isoformat()
        # DynamoDB doesn't accept float, convert to Decimal
        item = json.loads(json.dumps(body), parse_float=Decimal)
        table = dynamodb.Table(os.environ['RULE_SETS_TABLE'])
        table.put_item(Item=item)
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'rule_set_id': rule_set_id, 'status': 'saved'})
        }
    except Exception as e:
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': str(e)})}
"""),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={"RULE_SETS_TABLE": rule_sets_table.table_name}
        )
        rule_sets_table.grant_write_data(save_rule_set_lambda)
        rule_sets_resource.add_method("PUT", apigateway.LambdaIntegration(save_rule_set_lambda), method_responses=[{"statusCode": "200"}])

        # List rule sets
        list_rule_sets_lambda = _lambda.Function(
            self, "ListRuleSetsFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def lambda_handler(event, context):
    try:
        table = dynamodb.Table(os.environ['RULE_SETS_TABLE'])
        response = table.scan()
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'rule_sets': response.get('Items', [])}, cls=DecimalEncoder)
        }
    except Exception as e:
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': str(e)})}
"""),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={"RULE_SETS_TABLE": rule_sets_table.table_name}
        )
        rule_sets_table.grant_read_data(list_rule_sets_lambda)
        rule_sets_resource.add_method("GET", apigateway.LambdaIntegration(list_rule_sets_lambda), method_responses=[{"statusCode": "200"}])

        # Delete rule set
        delete_rule_set_lambda = _lambda.Function(
            self, "DeleteRuleSetFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        rule_set_id = body.get('rule_set_id')
        if not rule_set_id:
            return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'rule_set_id required'})}
        table = dynamodb.Table(os.environ['RULE_SETS_TABLE'])
        table.delete_item(Key={'rule_set_id': rule_set_id})
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'rule_set_id': rule_set_id, 'status': 'deleted'})
        }
    except Exception as e:
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': str(e)})}
"""),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={"RULE_SETS_TABLE": rule_sets_table.table_name}
        )
        rule_sets_table.grant_write_data(delete_rule_set_lambda)
        rule_sets_resource.add_method("DELETE", apigateway.LambdaIntegration(delete_rule_set_lambda), method_responses=[{"statusCode": "200"}])

        # --- Authentication ---
        auth_resource = custom_converter_api.root.add_resource("auth")

        # Register endpoint
        register_user_lambda = _lambda.Function(
            self, "RegisterUserFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os
import hashlib
import secrets
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')

def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    return salt, hashed

def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        email = (body.get('email') or '').strip().lower()
        password = body.get('password') or ''
        if not email or not password:
            return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Email and password required'})}
        if len(password) < 8:
            return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Password must be at least 8 characters'})}
        table = dynamodb.Table(os.environ['USERS_TABLE'])
        existing = table.get_item(Key={'email': email}).get('Item')
        if existing:
            return {'statusCode': 409, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'User already exists'})}
        salt, hashed = hash_password(password)
        table.put_item(Item={'email': email, 'password_hash': hashed, 'salt': salt, 'created_at': datetime.now(timezone.utc).isoformat()})
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'email': email, 'status': 'registered'})}
    except Exception as e:
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': str(e)})}
"""),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={"USERS_TABLE": users_table.table_name}
        )
        users_table.grant_read_write_data(register_user_lambda)
        register_user_resource = auth_resource.add_resource("register")
        register_user_resource.add_method("POST", apigateway.LambdaIntegration(register_user_lambda), method_responses=[{"statusCode": "200"}])

        # Login endpoint
        login_lambda = _lambda.Function(
            self, "LoginFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os
import hashlib
import hmac
import base64
import time

dynamodb = boto3.resource('dynamodb')

def verify_password(password, salt, stored_hash):
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    return hashed == stored_hash

def create_jwt(email, secret):
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b'=').decode()
    payload = base64.urlsafe_b64encode(json.dumps({"email": email, "exp": int(time.time()) + 86400}).encode()).rstrip(b'=').decode()
    signature = base64.urlsafe_b64encode(hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()).rstrip(b'=').decode()
    return f"{header}.{payload}.{signature}"

def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        email = (body.get('email') or '').strip().lower()
        password = body.get('password') or ''
        if not email or not password:
            return {'statusCode': 400, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Email and password required'})}
        table = dynamodb.Table(os.environ['USERS_TABLE'])
        user = table.get_item(Key={'email': email}).get('Item')
        if not user or not verify_password(password, user['salt'], user['password_hash']):
            return {'statusCode': 401, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Invalid email or password'})}
        token = create_jwt(email, os.environ['JWT_SECRET'])
        return {'statusCode': 200, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'token': token, 'email': email})}
    except Exception as e:
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': str(e)})}
"""),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={"USERS_TABLE": users_table.table_name, "JWT_SECRET": jwt_secret}
        )
        users_table.grant_read_data(login_lambda)
        login_resource = auth_resource.add_resource("login")
        login_resource.add_method("POST", apigateway.LambdaIntegration(login_lambda), method_responses=[{"statusCode": "200"}])

        # Lambda Layer for allotropy + dependencies
        allotropy_layer = _lambda.LayerVersion(
            self, "AllotropyLayer",
            code=_lambda.Code.from_asset("lambda-layers/allotropy-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="Allotropy library for multi-instrument ASM conversion"
        )

        # Unified Converter Lambda (tries Multi-Instrument first, falls back to ATaaS)
        unified_lambda = _lambda.Function(
            self, "UnifiedConverterFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("unified-converter"),
            layers=[allotropy_layer],
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment={
                "MULTI_INSTRUMENT_ENDPOINT": multi_instrument_api.url + "convert",
                "ATAAS_ENDPOINT": ataas_api.url + "convert",
                "CUSTOM_CONVERTER_ENDPOINT": custom_converter_api.url + "execute",
                "CONVERTER_REGISTRY_TABLE": converter_registry_table.table_name,
                "ASM_FILES_BUCKET": asm_files_bucket.bucket_name,
                "CONVERSION_HISTORY_TABLE": conversion_history_table.table_name,
                "SERVICE_NAME": "UnifiedConverter"
            }
        )

        # Grant permissions
        asm_files_bucket.grant_read_write(unified_lambda)
        conversion_history_table.grant_read_write_data(unified_lambda)
        converter_registry_table.grant_read_data(unified_lambda)

        # Unified Converter API
        unified_api = apigateway.RestApi(
            self, "UnifiedConverterAPI",
            rest_api_name="Unified ASM Converter",
            description="Intelligent converter with automatic fallback (Multi-Instrument -> AI)",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        unified_convert = unified_api.root.add_resource("convert")
        unified_convert.add_method(
            "POST",
            apigateway.LambdaIntegration(unified_lambda),
            method_responses=[{
                "statusCode": "200",
                "responseHeaders": {
                    "Access-Control-Allow-Origin": True
                }
            }]
        )

        # History endpoint for Control Tower
        history_lambda = _lambda.Function(
            self, "ConversionHistoryFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_inline("""
import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

def lambda_handler(event, context):
    try:
        table = dynamodb.Table(os.environ['CONVERSION_HISTORY_TABLE'])
        response = table.scan()
        items = response.get('Items', [])
        items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
            'body': json.dumps({'jobs': items[:100]}, cls=DecimalEncoder)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
"""),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "CONVERSION_HISTORY_TABLE": conversion_history_table.table_name
            }
        )
        conversion_history_table.grant_read_data(history_lambda)

        history_resource = unified_api.root.add_resource("history")
        history_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(history_lambda),
            method_responses=[{"statusCode": "200"}]
        )

        # Output the API endpoints
        cdk.CfnOutput(
            self, "DVaaSAPIEndpoint",
            value=dvaas_api.url,
            description="DVaaS API Gateway endpoint"
        )

        cdk.CfnOutput(
            self, "ATaaSAPIEndpoint", 
            value=ataas_api.url,
            description="ATaaS API Gateway endpoint"
        )

        cdk.CfnOutput(
            self, "ASMFilesBucket",
            value=asm_files_bucket.bucket_name,
            description="S3 bucket for converted ASM files"
        )

        cdk.CfnOutput(
            self, "MultiInstrumentAPIEndpoint",
            value=multi_instrument_api.url,
            description="Multi-Instrument API Gateway endpoint"
        )

        cdk.CfnOutput(
            self, "UnifiedConverterAPIEndpoint",
            value=unified_api.url,
            description="Unified Converter API (Multi-Instrument + AI fallback)"
        )

        cdk.CfnOutput(
            self, "CustomConverterAPIEndpoint",
            value=custom_converter_api.url,
            description="Custom Converter Service API"
        )

        cdk.CfnOutput(
            self, "ConverterRegistryTable",
            value=converter_registry_table.table_name,
            description="Custom Converter Registry DynamoDB table"
        )

        cdk.CfnOutput(
            self, "ConvertersBucket",
            value=converters_bucket.bucket_name,
            description="S3 bucket for custom converter code"
        )

app = cdk.App()
AutonomousServicesStack(app, "AutonomousServicesStack")
app.synth()