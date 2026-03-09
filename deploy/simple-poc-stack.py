#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_iam as iam,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class SimpleASMPOCStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket for file uploads
        upload_bucket = s3.Bucket(
            self, "ASMUploadBucket",
            bucket_name=f"asm-poc-uploads-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[s3.CorsRule(
                allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.POST, s3.HttpMethods.PUT],
                allowed_origins=["*"],
                allowed_headers=["*"]
            )]
        )

        # Lambda function for ASM conversion
        conversion_lambda = _lambda.Function(
            self, "ASMConversionFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                "UPLOAD_BUCKET": upload_bucket.bucket_name
            }
        )

        # Grant Lambda permissions
        upload_bucket.grant_read_write(conversion_lambda)
        
        # Add Bedrock permissions
        conversion_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=["*"]
            )
        )

        # API Gateway
        api = apigw.RestApi(
            self, "ASMPOCAPI",
            rest_api_name="ASM POC Service",
            description="Simple ASM transformation POC",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # API endpoints
        convert_resource = api.root.add_resource("convert")
        convert_resource.add_method(
            "POST", 
            apigw.LambdaIntegration(conversion_lambda)
        )

        # Health check
        health_resource = api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigw.MockIntegration(
                integration_responses=[{
                    "statusCode": "200",
                    "responseTemplates": {
                        "application/json": '{"status": "healthy", "service": "ASM POC"}'
                    }
                }],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[{"statusCode": "200"}]
        )

        # Outputs
        cdk.CfnOutput(self, "APIEndpoint", value=api.url)
        cdk.CfnOutput(self, "UploadBucket", value=upload_bucket.bucket_name)

app = cdk.App()
SimpleASMPOCStack(app, "SimpleASMPOCStack")
app.synth()