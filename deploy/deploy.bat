@echo off
echo === ASM POC Deployment Script ===
echo.

echo 1. Installing CDK dependencies...
pip install -r requirements.txt

echo.
echo 2. Bootstrapping CDK (if needed)...
cdk bootstrap

echo.
echo 3. Deploying ASM POC Stack...
cdk deploy --require-approval never

echo.
echo 4. Deployment complete!
echo Check the outputs above for your API Gateway endpoint URL.
echo.
echo To test the service, run: python ..\test_client.py
pause