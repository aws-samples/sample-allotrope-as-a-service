#!/usr/bin/env python3
"""
CDK Stack for Approval Workflow System
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

class ApprovalWorkflowStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table for Converter Approvals
        converters_table = dynamodb.Table(
            self, "ConverterApprovals",
            table_name="ConverterApprovals",
            partition_key=dynamodb.Attribute(
                name="converter_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Add GSI for status queries
        converters_table.add_global_secondary_index(
            index_name="StatusIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="generated_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # S3 Buckets for converter storage
        pending_bucket = s3.Bucket(
            self, "PendingConverters",
            bucket_name="asm-pending-converters",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        approved_bucket = s3.Bucket(
            self, "ApprovedConverters", 
            bucket_name="asm-approved-converters",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Approval Workflow Lambda
        approval_lambda = _lambda.Function(
            self, "ApprovalWorkflowFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("backend"),
            timeout=Duration.seconds(300),
            memory_size=512,
            environment={
                "CONVERTERS_TABLE": converters_table.table_name,
                "PENDING_BUCKET": pending_bucket.bucket_name,
                "APPROVED_BUCKET": approved_bucket.bucket_name
            }
        )

        # Grant permissions
        converters_table.grant_read_write_data(approval_lambda)
        pending_bucket.grant_read_write(approval_lambda)
        approved_bucket.grant_read_write(approval_lambda)

        # API Gateway for Approval Workflow
        approval_api = apigateway.RestApi(
            self, "ApprovalWorkflowAPI",
            rest_api_name="Approval Workflow Service",
            description="Converter code review and approval system",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # API endpoints
        workflow_resource = approval_api.root.add_resource("workflow")
        workflow_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(approval_lambda),
            method_responses=[{
                "statusCode": "200",
                "responseHeaders": {
                    "Access-Control-Allow-Origin": True
                }
            }]
        )

        # Health check
        health_resource = approval_api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[{
                    "statusCode": "200",
                    "responseTemplates": {
                        "application/json": '{"status": "healthy", "service": "ApprovalWorkflow"}'
                    }
                }],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[{"statusCode": "200"}]
        )

        # S3 Bucket for hosting approval dashboard
        dashboard_bucket = s3.Bucket(
            self, "ApprovalDashboard",
            bucket_name="asm-approval-dashboard",
            website_index_document="approval-dashboard.html",
            public_read_access=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Output the endpoints
        cdk.CfnOutput(
            self, "ApprovalAPIEndpoint",
            value=approval_api.url,
            description="Approval Workflow API Gateway endpoint"
        )

        cdk.CfnOutput(
            self, "DashboardURL",
            value=dashboard_bucket.bucket_website_url,
            description="Approval Dashboard URL"
        )

        cdk.CfnOutput(
            self, "PendingBucket",
            value=pending_bucket.bucket_name,
            description="S3 bucket for pending converters"
        )

        cdk.CfnOutput(
            self, "ApprovedBucket", 
            value=approved_bucket.bucket_name,
            description="S3 bucket for approved converters"
        )

app = cdk.App()
ApprovalWorkflowStack(app, "ApprovalWorkflowStack")
app.synth()