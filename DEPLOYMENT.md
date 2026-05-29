# Deployment Guide

## Prerequisites

- AWS Account with administrator access
- AWS CLI configured (`aws configure`)
- AWS CDK installed (`npm install -g aws-cdk`)
- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Node.js 18+
- Docker or [Finch](https://runfinch.com/) (required for building Lambda layers during `cdk deploy`)
- AWS Bedrock Claude model access enabled (for AI fallback)

## Step 1: Clone the Repository

```bash
git clone <repo-url>
cd asm-converter
```

## Step 2: Deploy Backend Services

The Lambda layers (`allotropy`, `reportlab`, `jsonschema-rs`) are built from `requirements.txt` during deployment using a container runtime. Make sure Docker or Finch is running before you deploy. If you use Finch, set `CDK_DOCKER=finch` so CDK uses it instead of Docker:

```bash
export CDK_DOCKER=finch   # only if using Finch instead of Docker
```

```bash
cd services
uv sync          # install CDK tooling deps
cdk bootstrap    # First time only
cdk deploy --require-approval never
```

This creates:

- 14 Lambda functions (Unified Converter, DVaaS, ATaaS, Multi-Instrument, Custom Converter, History, Register, Approve, List, Generate Converter, JWT Authorizer, Login, Register User, plus rule set functions)
- 5 API Gateway endpoints
- 4 DynamoDB tables (ConversionHistory, CustomConverterRegistry, ValidationRuleSets, ASMUsers)
- 3 S3 buckets (ASM files, validation results, custom converters)
- 3 Lambda Layers (allotropy, reportlab, jsonschema-rs)

Authentication is automatically configured:

- A unique JWT signing secret is generated from your AWS account ID and stack name
- A JWT Lambda Authorizer is attached to all API endpoints (except login, register, and health checks)
- Unauthenticated API requests receive `403 Forbidden` before reaching any backend Lambda
- No manual secret management needed

**Save the output endpoints** — you'll need them in Step 3.

The deployment will print endpoints like:

```text
UnifiedConverterAPIEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
DVaaSAPIEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
CustomConverterAPIEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
ATaaSAPIEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
MultiInstrumentAPIEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
```

## Step 3: Update Dashboard Configuration

Run the following helper script to update `dashboard/src/config.js` with your endpoints from Step 2:

```bash
cd ../dashboard
uv run update-config.py
```

Alternatively, you may manually update the following values in `dashboard/src/config.js`:

```javascript
export const ENDPOINTS = {
  unifiedConverter: 'https://YOUR_UNIFIED_CONVERTER_ID.execute-api.YOUR_REGION.amazonaws.com/prod',
  dvaas: 'https://YOUR_DVAAS_ID.execute-api.YOUR_REGION.amazonaws.com/prod',
  customConverter: 'https://YOUR_CUSTOM_CONVERTER_ID.execute-api.YOUR_REGION.amazonaws.com/prod',
  ataas: 'https://YOUR_ATAAS_ID.execute-api.YOUR_REGION.amazonaws.com/prod',
  multiInstrument: 'https://YOUR_MULTI_INSTRUMENT_ID.execute-api.YOUR_REGION.amazonaws.com/prod',
}
```

## Step 4: Deploy Dashboard

```bash
# From dashboard/
npm install
npm run build && cdk deploy --require-approval never
```

This creates:

- S3 bucket for static website
- CloudFront distribution with HTTPS

The deployment will print:

```text
CloudFrontURL = https://dxxxxxxxxxx.cloudfront.net
```

Open this URL in your browser to access the dashboard.

## Step 5: Download Allotrope Schemas (for validation)

DVaaS validates against official Allotrope JSON schemas. The `adm/` tree holds the per-technique schemas; the `qudt/` tree holds the QUDT unit schemas that ADM schemas `$ref` into (e.g. `http://purl.allotrope.org/json-schemas/qudt/REC/2025/06/units.schema`). Both trees must be present or validation will log warnings like `Schema not found: http://purl.allotrope.org/json-schemas/qudt/...`.

Download them:

```bash
cd ../services/dvaas
git clone https://gitlab.com/allotrope-public/asm.git --depth 1 temp-schemas
mkdir -p schemas/json-schemas schemas/manifests
cp -r temp-schemas/json-schemas/adm/* schemas/json-schemas/
cp -r temp-schemas/json-schemas/qudt schemas/json-schemas/
cp -r temp-schemas/manifests/* schemas/manifests/
rm -rf temp-schemas
```

The ADM subfolders are flattened into `schemas/json-schemas/` (e.g. `absorbance/`, `core/`). The `qudt/` folder is kept as a sibling so the `$ref` URIs resolve correctly. The validator indexes every `*.schema.json` by its `$id`, so filesystem layout doesn't matter as long as both trees are present.

Then redeploy DVaaS:

```bash
cd ..
# From services/
cdk deploy --require-approval never
```

## Step 6: Create Your First User Account

Open the CloudFront URL. You'll see a login page. Click **"Need an account? Create one"** to register with your email and a password (minimum 8 characters). After registering, sign in to access the dashboard.

All users are stored in the `ASMUsers` DynamoDB table. Each deployment has its own user database.

## Step 7: Verify Deployment

Open the CloudFront URL and test:

1. **Login page** — should show sign in form
2. **Register** — create an account and sign in
3. **Control Tower tab** — should show empty job history (no errors)
4. **Instrument Registry tab** — should show 18+ instruments
5. **Validate ASM File tab** — upload a test ASM JSON file
6. **Converter Management tab** — should show empty converter list

## Post-Deployment

### Register Your First Converter

1. Go to **Converter Management** tab
2. Click **Register New Converter**
3. Upload your Python converter file
4. Fill in vendor, model, instrument type
5. Click **Upload for Approval**
6. Review and approve the converter

### Create Your First Instrument Config

1. Go to **Instrument Config Creator** tab
2. Select your instrument or choose Custom
3. Fill in serial number, location, source file path, timezone
4. Download the JSON config file

### Convert Your First File

1. Go to **Convert Instrument File** tab
2. Upload your instrument output file
3. Upload the instrument config JSON
4. Click **Convert to ASM & Validate**

## Troubleshooting

### Dashboard shows blank page

- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Check browser console for errors (F12 → Console)
- Verify config.js has correct endpoints

### API returns CORS error

- Verify the API Gateway has CORS enabled (CDK handles this automatically)
- Check that you're using the `/prod/` path in endpoints

### Conversion fails with "Both conversion methods failed"

- Check if your instrument has an approved custom converter
- Check if the file format matches what the converter expects
- Check the instrument config vendor/model matches the converter registration

### Validation returns "No matching schema found"

- Ensure Allotrope schemas are downloaded (Step 5)
- Check that the `$asm.manifest` URL in your ASM matches a schema version you have locally

### Bedrock returns access denied

- Complete Step 6 (enable model access)
- Verify the Lambda IAM role has `bedrock:InvokeModel` permission (CDK adds this automatically)

## Architecture

```text
CloudFront (Dashboard)
    ↓
API Gateway (5 endpoints)
    ↓
Lambda Functions
    ├── Unified Converter (routes to best converter)
    ├── DVaaS (validates ASM against Allotrope schemas)
    ├── ATaaS (AI-powered conversion via Bedrock Claude)
    ├── Custom Converter Service (executes registered converters)
    └── Multi-Instrument (allotropy library, 31 instruments)
    ↓
DynamoDB (converter registry, job history)
S3 (ASM files, converter code, validation results)
```

## Security Hardening

The default deployment is functional but open. For production/enterprise environments, apply these hardening steps:

### 1. Restrict CORS (Required)

After your first deployment, update `allowed_origin` in `services/deploy_services.py` from `"*"` to your CloudFront URL:

```python
allowed_origin = "https://dxxxxxxxxxx.cloudfront.net"
```

Then redeploy: `cd services && cdk deploy --require-approval never`

### 2. Enable API Key Protection (Recommended)

An API key and usage plan are created automatically. To require the key on API calls:

1. Retrieve your API key value:

   ```bash
   aws apigateway get-api-key --api-key <ApiKeyId from CDK output> --include-value
   ```

2. Set the key in `dashboard/src/config.js`:

   ```javascript
   export const API_KEY = 'your-api-key-value'
   ```

3. Add `api_key_required=True` to API Gateway methods in `deploy_services.py` and redeploy

4. Rebuild and redeploy the dashboard

### 3. VPC Deployment (Enterprise)

For private network deployment, add VPC configuration to Lambda functions in `deploy_services.py`:

```python
vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id="vpc-xxxxxxxx")

# Add to each Lambda function:
vpc=vpc,
vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
```

This requires importing `aws_ec2 as ec2` in the CDK stack.

### 4. KMS Encryption (Enterprise)

To use customer-managed KMS keys for DynamoDB and S3:

```python
from aws_cdk import aws_kms as kms

key = kms.Key(self, "ASMEncryptionKey")

# Add to DynamoDB tables:
encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
encryption_key=key,

# Add to S3 buckets:
encryption=s3.BucketEncryption.KMS,
encryption_key=key,
```

### 5. WAF (Enterprise)

Add AWS WAF to CloudFront and API Gateway for rate limiting, IP filtering, and bot protection. Configure via AWS Console or add `aws_wafv2` constructs to the CDK stack.

### 6. Identity Provider Swap (Enterprise)

The built-in auth uses email/password stored in DynamoDB. To integrate with your organization's identity provider (PingFederate, Okta, Azure AD, Cognito):

1. Have your IdP issue JWT tokens with an `email` and `exp` claim
2. Replace the `JWTAuthorizerFunction` Lambda code to validate tokens against your provider's JWKS endpoint instead of the built-in HMAC secret
3. Remove or repurpose the `/auth/login` and `/auth/register` endpoints
4. Update the dashboard `LoginPage.jsx` to redirect to your IdP's login page

The API Gateway authorizer pattern stays the same — only the token validation logic changes.

### 7. Private API Gateway (Enterprise)

To make APIs accessible only from within your VPC:

```python
endpoint_configuration=apigateway.EndpointConfiguration(
    types=[apigateway.EndpointType.PRIVATE]
),
policy=iam.PolicyDocument(...)
```

This removes public internet access entirely — APIs are only reachable from within the VPC.

## Custom LLM Gateway (Optional)

If your organization uses a gateway or load balancer in front of Bedrock, you can route AI requests through it. In `services/deploy_services.py`, uncomment and set these environment variables on the ATaaS and GenerateConverter Lambda definitions:

```python
"BEDROCK_ENDPOINT_URL": "https://your-llm-gateway.internal.company.com",
"BEDROCK_MODEL_ID": "global.anthropic.claude-sonnet-4-6",
```

Then redeploy: `cd services && cdk deploy --require-approval never`

If left commented out, the service calls Bedrock directly (default).

## Updating

### Update backend services

```bash
cd services
cdk deploy --require-approval never
```

### Update dashboard

```bash
cd dashboard
npm run build
cdk deploy --require-approval never
```

### Update Allotrope schemas

Repeat Step 5 with the latest schemas from the Allotrope GitLab repository.
