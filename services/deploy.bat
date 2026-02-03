@echo off
echo Deploying Autonomous ATaaS and DVaaS Services...

REM Install CDK dependencies
echo Installing CDK dependencies...
pip install -r requirements.txt

REM Bootstrap CDK (if not already done)
echo Bootstrapping CDK...
cdk bootstrap

REM Deploy the stack
echo Deploying services stack...
cdk deploy AutonomousServicesStack --require-approval never

echo Deployment complete!
echo Check the outputs for API endpoints.