# Deployment Guide

## Prerequisites

- AWS Account with administrator access
- AWS CLI configured (`aws configure`)
- AWS CDK installed (`npm install -g aws-cdk`)
- Python 3.12+
- Node.js 18+
- AWS Bedrock Claude model access enabled (for AI fallback)

## Step 1: Clone the Repository

```bash
git clone <repo-url>
cd asm-converter
```

## Step 2: Deploy Backend Services

```bash
cd services
pip install -r requirements.txt
cdk bootstrap    # First time only
cdk deploy --require-approval never
```

This creates:
- 6 Lambda functions (Unified Converter, DVaaS, ATaaS, Multi-Instrument, Custom Converter, History)
- 5 API Gateway endpoints
- 2 DynamoDB tables (ConversionHistory, CustomConverterRegistry)
- 3 S3 buckets (ASM files, validation results, custom converters)
- 3 Lambda Layers (allotropy, reportlab, jsonschema-rs)

**Save the output endpoints** — you'll need them in Step 3.

The deployment will print endpoints like:
```
UnifiedConverterAPIEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
DVaaSAPIEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
CustomConverterAPIEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
ATaaSAPIEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
MultiInstrumentAPIEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
```

## Step 3: Update Dashboard Configuration

Edit `dashboard/src/config.js` with your endpoints from Step 2:

```javascript
export const ENDPOINTS = {
  unifiedConverter: 'https://YOUR_UNIFIED_CONVERTER_ID.execute-api.YOUR_REGION.amazonaws.com/prod',
  dvaas: 'https://YOUR_DVAAS_ID.execute-api.YOUR_REGION.amazonaws.com/prod',
  customConverter: 'https://YOUR_CUSTOM_CONVERTER_ID.execute-api.YOUR_REGION.amazonaws.com/prod',
  ataas: 'https://YOUR_ATAAS_ID.execute-api.YOUR_REGION.amazonaws.com/prod',
  multiInstrument: 'https://YOUR_MULTI_INSTRUMENT_ID.execute-api.YOUR_REGION.amazonaws.com/prod',
}
```

**Or use the helper script:**

```bash
cd dashboard
python update-config.py
```

This reads the CDK outputs automatically and updates config.js.

## Step 4: Deploy Dashboard

```bash
cd dashboard
npm install
npm run build
cdk deploy --require-approval never
```

This creates:
- S3 bucket for static website
- CloudFront distribution with HTTPS

The deployment will print:
```
CloudFrontURL = https://dxxxxxxxxxx.cloudfront.net
```

Open this URL in your browser to access the dashboard.

## Step 5: Download Allotrope Schemas (for validation)

DVaaS validates against official Allotrope JSON schemas. Download them:

```bash
cd services/dvaas
git clone https://gitlab.com/allotrope-public/asm.git temp-schemas
mkdir -p schemas/json-schemas schemas/manifests
cp -r temp-schemas/json-schemas/adm/* schemas/json-schemas/
cp -r temp-schemas/manifests/* schemas/manifests/
rm -rf temp-schemas
```

Then redeploy DVaaS:

```bash
cd services
cdk deploy --require-approval never
```

## Step 6: Enable Bedrock Model Access (optional)

If you want the AI-powered fallback (ATaaS):

1. Open AWS Console → Amazon Bedrock
2. Go to Model access → Manage model access
3. Request access for **Anthropic Claude 3.5 Sonnet**
4. Wait for approval (usually instant)

Without this, the AI fallback route will return an error, but all other routes (custom converters, allotropy) work fine.

## Step 7: Verify Deployment

Open the CloudFront URL and test:

1. **Control Tower tab** — should show empty job history (no errors)
2. **Instrument Registry tab** — should show 18+ instruments
3. **Validate ASM File tab** — upload a test ASM JSON file
4. **Converter Management tab** — should show empty converter list

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

```
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
