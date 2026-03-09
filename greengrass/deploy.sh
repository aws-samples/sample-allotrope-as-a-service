#!/bin/bash
# Deploy ASM Edge Client to AWS Greengrass

# Configuration
COMPONENT_NAME="com.aws.asm.EdgeClient"
COMPONENT_VERSION="1.0.0"
S3_BUCKET="asm-greengrass-artifacts"
REGION="us-east-1"

echo "Deploying ASM Edge Client to Greengrass..."

# Create S3 bucket for artifacts
aws s3 mb s3://$S3_BUCKET --region $REGION 2>/dev/null || true

# Upload component artifacts
echo "Uploading artifacts to S3..."
aws s3 cp asm_edge_client.py s3://$S3_BUCKET/
aws s3 cp requirements.txt s3://$S3_BUCKET/

# Create component version
echo "Creating Greengrass component..."
aws greengrassv2 create-component-version \
    --inline-recipe file://recipe.json \
    --region $REGION

echo "Component created successfully!"
echo "To deploy to devices, create a deployment with component: $COMPONENT_NAME"

# Example deployment command (uncomment to auto-deploy)
# aws greengrassv2 create-deployment \
#     --target-arn "arn:aws:iot:$REGION:ACCOUNT:thinggroup/LabDevices" \
#     --components "{\"$COMPONENT_NAME\":{\"componentVersion\":\"$COMPONENT_VERSION\"}}"