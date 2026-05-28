# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend services

```bash
cd services
pip install -r requirements.txt
cdk bootstrap          # first time only
cdk deploy             # deploy all Lambda functions and APIs
cdk synth              # synthesize CloudFormation (validates CDK without deploying)
```

Lambda layers (allotropy, reportlab, jsonschema-rs) are built from `requirements.txt` at deploy time using Docker or Finch. Docker must be running. If using Finch: `export CDK_DOCKER=finch` before `cdk deploy`.

### Dashboard

```bash
cd dashboard
npm install
npm run dev            # dev server on localhost:3000
npm run build          # production build to dist/
cdk deploy             # deploy dist/ to S3 + CloudFront
```

After backend deployment, update API endpoints in `dashboard/src/config.js` from CDK outputs, or run `python dashboard/update-config.py`.

### Local tests

```bash
python services/simple_test.py
python services/test_autonomous_services.py
```

## Architecture

### Conversion pipeline

Requests enter through the **Unified Converter** (`services/unified-converter/lambda_function.py`), which tries three routes in order:

1. **Multi-Instrument** (`services/multi-instrument/`) — rule-based conversion via the allotropy library (50+ instruments)
2. **Custom Converter** (`services/custom-converter/`) — runs customer-uploaded Python converters fetched from S3
3. **ATaaS** (`services/ataas/`) — AI fallback using Bedrock Claude 4.6 Sonnet (`global.anthropic.claude-sonnet-4-6`)

Converted output is stored in S3 and logged to DynamoDB (`ConversionHistory`).

**DVaaS** (`services/dvaas/`) is a separate service for validating ASM JSON against Allotrope schemas and optional rule sets. It can generate PDF certification reports via reportlab. Allotrope JSON schemas must be downloaded separately (see DEPLOYMENT.md Step 5) — both the `adm/` and `qudt/` trees are required.

### CDK stack

Everything is defined in a single CDK stack: `services/deploy_services.py` → `AutonomousServicesStack`. This creates 5 API Gateways, ~14 Lambda functions, 4 DynamoDB tables, 3 S3 buckets, and 3 Lambda layers. Many simple CRUD/auth Lambdas are defined inline using `Code.from_inline()` rather than as separate files.

The dashboard is a separate CDK stack: `dashboard/deploy-stack.py` → `DashboardStack` (S3 + CloudFront).

Lambda layers use `PythonLayerVersion` (builds via Docker at deploy time). The allotropy layer uses `_AllotropyLayerHooks` (defined at top of `deploy_services.py`) to strip unused packages (matplotlib, lxml, scipy, etc.) that would otherwise exceed Lambda's 250 MB layer limit.

### Custom converter sandbox

`services/custom-converter/lambda_function.py` runs `exec()` on customer code with three defense-in-depth layers:
- **Layer B** — Assumes a zero-permission STS role before exec(), swapping process credentials so any boto3 inside exec() is denied
- **Layer C** — Lambda runs in an isolated VPC with no NAT gateway; VPC endpoints for S3, DynamoDB, STS allow the wrapper to function
- **Layer D** — Clears `os.environ` and removes dangerous builtins (`open`, `exec`, `eval`, `compile`, `__import__`) before exec(); both are restored in `finally`

### Authentication

Self-contained JWT auth (HMAC-SHA256). The JWT secret is auto-generated per deployment as `{ACCOUNT_ID}-{STACK_NAME}-asm-jwt-secret`. A shared `JWTAuthorizerFunction` Lambda validates tokens across all protected API Gateway routes. Login/register endpoints on the Custom Converter API are unprotected; everything else requires `Authorization: Bearer <token>`.

In the dashboard, `config.js` provides `apiHeaders()` and `authFetch()` — use `authFetch()` for all API calls; it reads the token from `localStorage` and handles 401 redirects.

### Dashboard

React 18 + AWS Cloudscape Design System + Vite. `CombinedApp.jsx` is the top-level router; it shows `LoginPage` or the tabbed dashboard. Each tab is a standalone component (`ConvertInstrumentApp`, `ValidateASMApp`, `ConverterManagementApp`, `ControlTowerApp`, etc.). API endpoints are centralized in `dashboard/src/config.js`.

## Key environment variables (Lambda)

| Variable | Purpose |
|---|---|
| `CONVERTER_REGISTRY_TABLE` | DynamoDB table for custom converter registry |
| `CONVERTERS_BUCKET` | S3 bucket for custom converter Python code |
| `ZERO_PERMISSION_ROLE_ARN` | IAM role assumed during exec() sandbox (Layer B) |
| `ASM_FILES_BUCKET` | S3 bucket for converted ASM output |
| `CONVERSION_HISTORY_TABLE` | DynamoDB table for job history |
| `DVAAS_ENDPOINT` / `MULTI_INSTRUMENT_ENDPOINT` / `ATAAS_ENDPOINT` | Inter-service URLs |
| `JWT_SECRET` | Token signing key (auto-generated per deployment) |
| `BEDROCK_MODEL_ID` | Override Bedrock model (default: Claude 4.6 Sonnet) |
| `BEDROCK_ENDPOINT_URL` | Optional custom LLM gateway URL |
