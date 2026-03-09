#!/usr/bin/env python3
"""
CDK Stack for ASM Storage Service
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

class StorageServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Buckets for file storage
        asm_files_bucket = s3.Bucket(
            self, "ASMConvertedFiles",
            bucket_name="asm-converted-files",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        validation_results_bucket = s3.Bucket(
            self, "ASMValidationResults",
            bucket_name="asm-validation-results", 
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # DynamoDB Table for conversion history
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

        # Add GSI for timestamp queries
        conversion_history_table.add_global_secondary_index(
            index_name="TimestampIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Storage Service Lambda
        storage_lambda = _lambda.Function(
            self, "StorageServiceFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("."),
            timeout=Duration.seconds(300),
            memory_size=512,
            environment={
                "ASM_FILES_BUCKET": asm_files_bucket.bucket_name,
                "VALIDATION_RESULTS_BUCKET": validation_results_bucket.bucket_name,
                "CONVERSION_HISTORY_TABLE": conversion_history_table.table_name
            }
        )

        # Grant permissions
        asm_files_bucket.grant_read_write(storage_lambda)
        validation_results_bucket.grant_read_write(storage_lambda)
        conversion_history_table.grant_read_write_data(storage_lambda)

        # API Gateway for Storage Service
        storage_api = apigateway.RestApi(
            self, "StorageServiceAPI",
            rest_api_name="ASM Storage Service",
            description="Storage service for ASM files and conversion history",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # API endpoints
        storage_resource = storage_api.root.add_resource("storage")
        storage_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(storage_lambda),
            method_responses=[{
                "statusCode": "200",
                "responseHeaders": {
                    "Access-Control-Allow-Origin": True
                }
            }]
        )

        # Health check
        health_resource = storage_api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[{
                    "statusCode": "200",
                    "responseTemplates": {
                        "application/json": '{"status": "healthy", "service": "StorageService"}'
                    }
                }],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[{"statusCode": "200"}]
        )

        # Output the endpoints
        cdk.CfnOutput(
            self, "StorageAPIEndpoint",
            value=storage_api.url,
            description="Storage Service API Gateway endpoint"
        )

        cdk.CfnOutput(
            self, "ASMFilesBucket",
            value=asm_files_bucket.bucket_name,
            description="S3 bucket for ASM files"
        )

        cdk.CfnOutput(
            self, "ValidationResultsBucket",
            value=validation_results_bucket.bucket_name,
            description="S3 bucket for validation results"
        )

app = cdk.App()
StorageServiceStack(app, "StorageServiceStack")
app.synth()