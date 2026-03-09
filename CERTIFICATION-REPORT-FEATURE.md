# Certification Report Feature

## Overview

The DVaaS (Data Validation as a Service) now generates professional PDF certification reports suitable for regulatory submission (FDA, EMA, etc.).

## Features

- **Professional PDF format** with branding and formatting
- **Certificate ID and timestamp** for audit trail
- **Validation metrics** including technique, measurement count, etc.
- **Detailed results** with errors, warnings, and info
- **Pass/Fail status** with color-coded indicators
- **Regulatory-ready** suitable for FDA/EMA submission

## How to Use

### API Request

```bash
POST https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate
Content-Type: application/json

{
  "asm_data": { ... ASM JSON content ... },
  "validation_level": "certification",
  "generate_report": true,
  "file_name": "SampleResults-1.json"
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `asm_data` | object | Yes | ASM JSON data to validate |
| `validation_level` | string | No | "basic", "comprehensive", or "certification" (default: "basic") |
| `generate_report` | boolean | No | Generate PDF certification report (default: false) |
| `file_name` | string | No | Name of file being validated (for report) |

### Response

```json
{
  "valid": true,
  "validation_level": "certification",
  "timestamp": "2026-01-14T20:30:00.000Z",
  "errors": [],
  "warnings": ["WARNING: Temperature value is null in pH measurement"],
  "info": [
    "INFO: Detected technique: solution analyzer",
    "INFO: Measurement count: 4"
  ],
  "metrics": {
    "technique": "solution analyzer",
    "measurement_count": 4,
    "has_sample_document": true
  },
  "validator": "allotropy",
  "certification": {
    "status": "ALLOTROPE_CERTIFIED",
    "certificate_id": "CERT-20260114203000",
    "issued_at": "2026-01-14T20:30:00.000Z",
    "validator": "allotropy_v1.1.1"
  },
  "certification_report": {
    "available": true,
    "format": "pdf",
    "size_bytes": 45678,
    "data": "JVBERi0xLjQKJeLjz9MKMyAwIG9iago8PC9UeXBlIC9QYWdlCi9QYXJlbnQgMSAwIFIKL1Jlc291cmNlcyAyIDAgUgovQ29udGVudHMgNCAwIFI+PgplbmRvYmoKNCAwIG9iago8PC9GaWx0ZXIgL0ZsYXRlRGVjb2RlIC9MZW5ndGggNTU+PgpzdHJlYW0KeJwr5HIK4TI2U..."
  }
}
```

### Decoding the PDF

The PDF is returned as base64-encoded data. Decode and save it:

**Python:**
```python
import base64
import json

response = api_call_to_dvaas()
result = json.loads(response)

if result.get('certification_report', {}).get('available'):
    pdf_data = base64.b64decode(result['certification_report']['data'])
    
    with open('certification_report.pdf', 'wb') as f:
        f.write(pdf_data)
    
    print("Certification report saved!")
```

**JavaScript:**
```javascript
const response = await fetch(dvaasUrl, { method: 'POST', body: JSON.stringify(payload) });
const result = await response.json();

if (result.certification_report?.available) {
  const pdfData = atob(result.certification_report.data);
  const bytes = new Uint8Array(pdfData.length);
  for (let i = 0; i < pdfData.length; i++) {
    bytes[i] = pdfData.charCodeAt(i);
  }
  
  const blob = new Blob([bytes], { type: 'application/pdf' });
  const url = URL.createObjectURL(blob);
  
  // Download or display
  window.open(url);
}
```

**Bash/curl:**
```bash
curl -X POST https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate \
  -H "Content-Type: application/json" \
  -d @request.json | jq -r '.certification_report.data' | base64 -d > report.pdf
```

## Report Contents

### 1. Header
- Title: "ASM VALIDATION CERTIFICATION REPORT"
- Status indicator (CERTIFIED ✓ / VALID / FAILED ✗)

### 2. Certificate Information (if certified)
- Certificate ID (e.g., CERT-20260114203000)
- Issued timestamp
- Validator version
- Certification status

### 3. File Information
- File name
- Validation level
- Validation timestamp
- Validator used

### 4. Validation Metrics
- Technique detected
- Measurement count
- Document structure flags
- Identifier counts

### 5. Errors (if any)
- List of validation errors
- Critical issues that caused failure

### 6. Warnings (if any)
- Non-critical issues
- Recommendations for improvement

### 7. Validation Details
- Info messages
- Technique detection details
- Structure validation results

### 8. Summary
- Overall assessment
- Regulatory suitability statement

### 9. Footer
- Generation timestamp
- Support contact information

## Sample Reports

Two sample reports have been generated:

1. **certification_report_PASSED.pdf** - Example of successful certification
2. **certification_report_FAILED.pdf** - Example of failed validation

## Use Cases

### 1. Regulatory Submission
```python
# Validate and certify ASM file for FDA submission
result = validate_asm(asm_data, validation_level='certification', generate_report=True)

if result['valid'] and result['certification']:
    # Save certification report with submission package
    save_pdf(result['certification_report']['data'], 'FDA_submission_cert.pdf')
```

### 2. Batch Validation with Reports
```python
# Validate multiple files and generate reports for each
for asm_file in asm_files:
    result = validate_asm(
        asm_data=load_file(asm_file),
        validation_level='comprehensive',
        generate_report=True,
        file_name=asm_file
    )
    
    save_pdf(result['certification_report']['data'], f'{asm_file}_report.pdf')
```

### 3. Quality Assurance Workflow
```python
# Validate before archival
result = validate_asm(asm_data, validation_level='certification', generate_report=True)

if result['valid']:
    # Archive ASM file with certification report
    archive_with_certificate(asm_file, result['certification_report'])
else:
    # Send back for correction
    notify_errors(result['errors'])
```

## Deployment

### Update Lambda Function

1. Add `reportlab` to requirements.txt:
```
boto3>=1.26.0
jsonschema>=4.17.0
reportlab>=4.0.0
```

2. Include `generate_certification_report.py` in Lambda deployment package

3. Redeploy DVaaS service:
```bash
cd services
python deploy_services.py
```

### Lambda Layer (Recommended)

For faster deployments, create a Lambda layer with reportlab:

```bash
mkdir python
pip install reportlab -t python/
zip -r reportlab-layer.zip python/
aws lambda publish-layer-version --layer-name reportlab --zip-file fileb://reportlab-layer.zip
```

## Testing

Run the test script to generate sample reports:

```bash
python test_certification_report.py
```

This generates:
- `certification_report_PASSED.pdf` - Successful validation
- `certification_report_FAILED.pdf` - Failed validation

## Benefits

1. **Regulatory Compliance**: Professional reports suitable for FDA/EMA submission
2. **Audit Trail**: Certificate IDs and timestamps for traceability
3. **Documentation**: Complete validation details in single document
4. **Archival**: PDF format suitable for 30+ year retention
5. **Automation**: Programmatic generation eliminates manual report creation

## Support

For questions or issues with certification reports:
- Email: support@asm-transformation.com
- Documentation: See USER-GUIDE-OPEN-SOURCE.md
