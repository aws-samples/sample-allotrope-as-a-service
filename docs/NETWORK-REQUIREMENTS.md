# Network Requirements & Air-Gapped Deployment Guide

## Overview

The ASM Transformation Service requires internet access **only during initial build and deployment** — not at runtime. Once deployed, all Lambda functions, layers, and schemas are self-contained within your AWS account. This document explains exactly when internet access is needed, what is downloaded, and how to deploy in environments with no internet access.

## Runtime — No Internet Required

Once deployed, the service runs entirely within AWS with no external dependencies:

| Component | Connectivity | Notes |
|-----------|-------------|-------|
| Lambda functions | AWS internal | Invoke via API Gateway |
| DynamoDB | AWS internal | VPC Endpoint available |
| S3 | AWS internal | VPC Endpoint available |
| API Gateway | AWS internal | Regional endpoint |
| CloudFront | AWS internal | Edge distribution |
| Bedrock (Claude) | AWS internal | VPC Endpoint available |
| Allotrope schemas | Bundled | Packaged inside DVaaS Lambda |
| Lambda layers | Bundled | allotropy, jsonschema-rs, reportlab pre-built in repo |

**No ports need to be opened for the running application.** If your Lambda functions are deployed inside a VPC, you will need VPC Endpoints for the AWS services listed above (see "VPC Endpoints" section below).

## Build & Deploy — Internet Required (One-Time)

Internet access is needed in two places during initial setup. Both are one-time operations.

### 1. Python Packages (Backend CDK Deployment)

**When:** `pip install -r requirements.txt` in the `services/` directory

**What is downloaded:**

| Package | Source | Purpose |
|---------|--------|---------|
| aws-cdk-lib | PyPI (pypi.org) | AWS CDK infrastructure-as-code framework |
| constructs | PyPI (pypi.org) | CDK constructs library |

**Size:** ~50 MB

### 2. Node.js Packages (Dashboard Build)

**When:** `npm install` in the `dashboard/` directory

**What is downloaded:**

| Package | Source | Purpose |
|---------|--------|---------|
| @cloudscape-design/* | npm (npmjs.com) | AWS Cloudscape UI components |
| react, react-dom | npm (npmjs.com) | React framework |
| vite | npm (npmjs.com) | Build tool |
| aws-cdk-lib | npm (npmjs.com) | CDK for dashboard stack |

**Size:** ~200 MB (node_modules)

### 3. CDK Bootstrap (First-Time Only)

**When:** `cdk bootstrap` on a new AWS account/region

**What is downloaded:** CDK bootstrap assets from public ECR (`public.ecr.aws/cdk`)

**Size:** ~30 MB

### What Does NOT Need Internet

These are already bundled in the repository:

- Lambda layers (allotropy, jsonschema-rs, reportlab) — pre-built in `services/lambda-layers/`
- DVaaS bundle (boto3, jsonschema, etc.) — pre-built in `services/dvaas-bundle/`
- Unified converter dependencies (requests, urllib3, etc.) — pre-built in `services/unified-converter/`
- Allotrope JSON schemas — downloaded separately (see Step 5 in DEPLOYMENT.md) but only needed once
- Dashboard source code — all JSX/JS files included

## Deployment Options for Restricted Environments

### Option A: Build Outside, Deploy Inside (Recommended)

Use a machine with internet access to install dependencies, then transfer everything to the restricted environment.

**On a machine with internet access:**

```bash
# 1. Extract the tarball
tar -xzf asm-converter-v1.0.tar.gz
cd asm-converter

# 2. Install Python CDK dependencies
cd services
pip install -r requirements.txt --target ./cdk-deps
cd ..

# 3. Install Node.js dashboard dependencies
cd dashboard
npm install
npm run build
cd ..

# 4. Re-package everything
cd ..
tar -czf asm-converter-v1.0-bundled.tar.gz asm-converter/
```

**Transfer `asm-converter-v1.0-bundled.tar.gz` to the restricted environment, then:**

```bash
tar -xzf asm-converter-v1.0-bundled.tar.gz
cd asm-converter

# Deploy backend (Python deps already installed)
cd services
PYTHONPATH=./cdk-deps cdk deploy --require-approval never
cd ..

# Deploy dashboard (already built)
cd dashboard
cdk deploy --require-approval never
```

### Option B: Internal Package Repository

If your organization has an internal PyPI mirror (e.g., Artifactory, Nexus, CodeArtifact) and/or npm registry, configure pip and npm to use them.

**For pip (Python/CDK):**

```bash
# Using pip.conf or command line
pip install -r requirements.txt --index-url https://your-internal-pypi.company.com/simple/

# Or set globally
pip config set global.index-url https://your-internal-pypi.company.com/simple/
```

**Required Python packages in your internal PyPI:**
- aws-cdk-lib (>=2.100.0)
- constructs (>=10.0.0)

**For npm (Dashboard):**

```bash
# Set registry
npm config set registry https://your-internal-npm.company.com/

# Then install normally
npm install
```

**Required npm packages in your internal registry:**
- @cloudscape-design/components
- @cloudscape-design/global-styles
- react, react-dom
- vite
- aws-cdk-lib, constructs

The full list is in `dashboard/package.json` and `dashboard/package-lock.json`.

### Option C: AWS CodeArtifact

Set up AWS CodeArtifact as a managed package proxy within your AWS account. CodeArtifact can mirror public PyPI and npm registries through a controlled connection.

```bash
# Create CodeArtifact domain and repositories
aws codeartifact create-domain --domain my-company
aws codeartifact create-repository --domain my-company --repository pypi-store \
    --description "PyPI mirror" --upstreams repositoryName=pypi-store
aws codeartifact create-repository --domain my-company --repository npm-store \
    --description "npm mirror" --upstreams repositoryName=npm-store

# Associate with public upstream
aws codeartifact associate-external-connection --domain my-company \
    --repository pypi-store --external-connection public:pypi
aws codeartifact associate-external-connection --domain my-company \
    --repository npm-store --external-connection public:npmjs

# Configure pip
aws codeartifact login --tool pip --domain my-company --repository pypi-store

# Configure npm
aws codeartifact login --tool npm --domain my-company --repository npm-store
```

Then run `pip install` and `npm install` as normal — CodeArtifact fetches from public registries and caches locally.

### Option D: Pre-Bundled Tarball (Fully Air-Gapped)

If you need a tarball that requires zero internet access, contact your AWS account team. We can provide a version with all Python and Node.js dependencies pre-installed (~400 MB). This is the largest option but requires no network access at all during deployment.

## VPC Endpoints (For VPC-Deployed Lambdas)

If you deploy Lambda functions inside a VPC (see Security Hardening in DEPLOYMENT.md), you need VPC Endpoints for the AWS services the application uses:

| Service | VPC Endpoint Type | Required By |
|---------|------------------|-------------|
| DynamoDB | Gateway | All Lambdas (converter registry, history, users, rule sets) |
| S3 | Gateway | Unified Converter, Custom Converter, ATaaS |
| Bedrock Runtime | Interface | ATaaS, Generate Converter |
| CloudWatch Logs | Interface | All Lambdas (logging) |

**DynamoDB and S3** use Gateway endpoints (free, no per-hour charge).
**Bedrock and CloudWatch** use Interface endpoints (charged per hour + per GB).

Example CDK configuration:

```python
from aws_cdk import aws_ec2 as ec2

vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id="vpc-xxxxxxxx")

# Gateway endpoints (free)
vpc.add_gateway_endpoint("DynamoDBEndpoint",
    service=ec2.GatewayVpcEndpointAwsService.DYNAMODB)
vpc.add_gateway_endpoint("S3Endpoint",
    service=ec2.GatewayVpcEndpointAwsService.S3)

# Interface endpoints (charged)
vpc.add_interface_endpoint("BedrockEndpoint",
    service=ec2.InterfaceVpcEndpointAwsService("bedrock-runtime"))
vpc.add_interface_endpoint("CloudWatchLogsEndpoint",
    service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS)
```

## Allotrope Schemas (One-Time Download)

Step 5 in DEPLOYMENT.md requires cloning the Allotrope public schema repository from GitLab. This is a one-time download (~5 MB).

**If GitLab is not accessible:**

1. Download the schemas from a machine with internet access:
   ```bash
   git clone https://gitlab.com/allotrope-public/asm.git
   ```

2. Copy the `json-schemas/adm/` and `manifests/` directories to a USB drive or file transfer

3. Place them in `services/dvaas/schemas/json-schemas/` and `services/dvaas/schemas/manifests/`

4. Redeploy DVaaS: `cd services && cdk deploy --require-approval never`

## Summary

| Phase | Internet Required | What For | Alternative |
|-------|------------------|----------|-------------|
| Build (one-time) | Yes | pip install, npm install | Internal repo, CodeArtifact, or pre-bundled tarball |
| CDK Bootstrap (one-time) | Yes | CDK assets from public ECR | Pre-bootstrap from connected machine |
| Schema download (one-time) | Yes | Allotrope GitLab repo | Manual file transfer |
| Runtime | No | Everything runs within AWS | VPC Endpoints if Lambdas are in VPC |
| Dashboard access | No | CloudFront serves static files | Users need network path to CloudFront URL |
