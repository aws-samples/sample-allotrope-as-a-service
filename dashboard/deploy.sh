#!/bin/bash
# Deploy ASM Dashboard to S3

echo "Building dashboard..."
npm run build

echo "Deploying to S3..."
cdk deploy --require-approval never

echo "Deployment complete!"
echo "Check outputs for website URL"
