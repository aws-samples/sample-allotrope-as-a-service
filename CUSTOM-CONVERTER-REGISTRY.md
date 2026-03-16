# Custom Converter Registry - Implementation Complete

## Architecture

```
Customer Request with Manifest
    ↓
Unified Converter
    ↓
1. Check Custom Converter Registry (DynamoDB)
   - Query by vendor + model
   - Status = APPROVED
    ↓
2. If found → Custom Converter Service
   - Load converter from S3
   - Execute converter code
   - Return ASM
    ↓
3. If not found → Multi-Instrument (allotropy)
    ↓
4. If fails → ATaaS (AI)
```

## Components Deployed

### 1. DynamoDB Table: CustomConverterRegistry
- **Partition Key**: converter_id
- **Attributes**: vendor, model, instrument_type, s3_location, status, approved_by, created_at
- **Status Values**: PENDING, APPROVED, DEPRECATED

### 2. S3 Bucket: custom-converters-{account}-{region}
- Stores converter Python files
- Path: `converters/{converter_id}.py`

### 3. Lambda Functions
- **CustomConverterFunction**: Executes approved converters
- **RegisterConverterFunction**: Registers new converters (inline)
- **ApproveConverterFunction**: Approves pending converters (inline)

### 4. API Endpoints
- **POST /execute**: Execute converter
- **POST /register**: Register new converter
- **POST /approve**: Approve pending converter

## Usage

### Register a New Converter

```python
import requests

converter_code = """
def convert(file_content):
    # Your conversion logic
    return asm_output
"""

response = requests.post(
    "https://{api-id}.execute-api.us-east-1.amazonaws.com/prod/register",
    json={
        "converter_id": "nova-flex2-v1",
        "converter_code": converter_code,
        "vendor": "NOVABIO_FLEX2",
        "model": "BioProfile FLEX2",
        "instrument_type": "solution_analyzer"
    }
)
# Returns: {"converter_id": "nova-flex2-v1", "status": "PENDING"}
```

### Approve Converter

```python
response = requests.post(
    "https://{api-id}.execute-api.us-east-1.amazonaws.com/prod/approve",
    json={
        "converter_id": "nova-flex2-v1",
        "approved_by": "scientist@company.com"
    }
)
# Returns: {"converter_id": "nova-flex2-v1", "status": "APPROVED"}
```

### Use via Unified Converter

```python
response = requests.post(
    "https://{unified-api-id}.execute-api.us-east-1.amazonaws.com/prod/convert",
    json={
        "file_content": "...",
        "file_name": "data.csv",
        "manifest": {
            "vendor": "NOVABIO_FLEX2",
            "model": "BioProfile FLEX2",
            "instrument_type": "solution_analyzer"
        }
    }
)
# Automatically uses custom converter if approved
```

## Converter Code Requirements

Converters must define a `convert` function:

```python
def convert(file_content):
    """
    Args:
        file_content (str): Raw file content
    
    Returns:
        dict: ASM JSON structure
    """
    # Parse file_content
    # Convert to ASM
    return asm_output
```

## Security

- Converters execute in Lambda sandbox
- Only APPROVED converters can execute
- Code stored in private S3 bucket
- Registry access controlled by IAM

## Deployment

```bash
cd services
cdk deploy
```

## Testing

```bash
# Update endpoints in test file
python test_custom_converter_registry.py
```

## Next Steps

1. **Migrate Nova FLEX2**: Register embedded converter to registry
2. **Add Validation**: Validate converter code before registration
3. **Add Testing**: Test converters with sample files before approval
4. **Build UI**: Dashboard for converter management
5. **Add Versioning**: Support multiple versions of same converter
