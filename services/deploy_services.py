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
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description="Reportlab for PDF generation"
        )

        # DVaaS Lambda Function
        dvaas_lambda = _lambda.Function(
            self, "DVaaSFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("dvaas"),
            layers=[reportlab_layer],
            timeout=Duration.seconds(300),
            memory_size=512,
            environment={
                "SERVICE_NAME": "DVaaS"
            }
        )

        # ATaaS Lambda Function
        ataas_lambda = _lambda.Function(
            self, "ATaaSFunction", 
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("ataas"),
            timeout=Duration.seconds(300),
            memory_size=2048,
            environment={
                "DVAAS_ENDPOINT": "internal",  # Will be updated after DVaaS API creation
                "SERVICE_NAME": "ATaaS"
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

        # Grant storage permissions to ATaaS
        asm_files_bucket.grant_read_write(ataas_lambda)
        validation_results_bucket.grant_read_write(ataas_lambda)
        conversion_history_table.grant_read_write_data(ataas_lambda)

        # Multi-Instrument Lambda Function
        multi_instrument_lambda = _lambda.Function(
            self, "MultiInstrumentFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
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

        # Unified Converter Lambda (tries Multi-Instrument first, then ATaaS)
        unified_lambda = _lambda.Function(
            self, "UnifiedConverterFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("unified-converter"),
            timeout=Duration.seconds(300),
            memory_size=512,
            environment={
                "MULTI_INSTRUMENT_ENDPOINT": multi_instrument_api.url + "convert",
                "ATAAS_ENDPOINT": ataas_api.url + "convert",
                "ASM_FILES_BUCKET": asm_files_bucket.bucket_name,
                "CONVERSION_HISTORY_TABLE": conversion_history_table.table_name,
                "SERVICE_NAME": "UnifiedConverter"
            }
        )

        # Grant permissions
        asm_files_bucket.grant_read_write(unified_lambda)
        conversion_history_table.grant_read_write_data(unified_lambda)

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

app = cdk.App()
AutonomousServicesStack(app, "AutonomousServicesStack")
app.synth()