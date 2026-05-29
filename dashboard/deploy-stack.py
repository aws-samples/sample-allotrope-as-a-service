#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
CDK Stack for ASM Dashboard S3 Website Deployment
"""

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class DashboardStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket (private, served via CloudFront)
        website_bucket = s3.Bucket(
            self, "DashboardBucket",
            bucket_name=f"asm-dashboard-website-{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Origin Access Identity for CloudFront
        oai = cloudfront.OriginAccessIdentity(self, "OAI")
        website_bucket.grant_read(oai)

        # CloudFront distribution
        distribution = cloudfront.Distribution(
            self, "DashboardDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    website_bucket,
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html"
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html"
                )
            ]
        )

        # Deploy website files
        s3deploy.BucketDeployment(
            self, "DeployWebsite",
            sources=[s3deploy.Source.asset("./dist")],
            destination_bucket=website_bucket,
            distribution=distribution,
            distribution_paths=["/*"]
        )

        # Outputs
        CfnOutput(
            self, "WebsiteURL",
            value=website_bucket.bucket_website_url,
            description="S3 Website URL"
        )

        CfnOutput(
            self, "CloudFrontURL",
            value=f"https://{distribution.distribution_domain_name}",
            description="CloudFront Distribution URL"
        )

        CfnOutput(
            self, "BucketName",
            value=website_bucket.bucket_name,
            description="S3 Bucket Name"
        )

app = cdk.App()
DashboardStack(app, "ASMDashboardStack")
app.synth()
