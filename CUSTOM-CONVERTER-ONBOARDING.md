# Custom Converter Onboarding Process

## Current Process (Manual)

### Step 1: Customer Provides Files
- Sample instrument files (CSV, XML, JSON, etc.)
- Instrument details (manufacturer, model, type)
- Expected ASM output (if available)

### Step 2: Developer Creates Converter
```python
# Example: customer_instrument_converter.py
def convert_customer_format(file_content):
    # Parse customer format
    # Convert to ASM structure
    # Return ASM JSON
    pass
```

### Step 3: Add to Unified Converter
```python
# In services/unified-converter/lambda_function.py

def is_customer_instrument(file_content, file_name):
    # Add detection logic
    return 'customer_specific_header' in file_content

# In lambda_handler():
if is_customer_instrument(file_content, file_name):
    result = convert_customer_format(file_content)
    return success_response(result)
```

### Step 4: Deploy
```bash
cd services
cdk deploy
```

## Planned Process (Automated)

### Architecture Components Needed

1. **Custom Converter Registry (DynamoDB)**
```json
{
  "converter_id": "customer-instrument-v1",
  "vendor": "customer_vendor",
  "model": "customer_model", 
  "instrument_type": "solution_analyzer",
  "converter_location": "s3://converters/customer_converter.py",
  "status": "APPROVED",
  "approved_by": "scientist@company.com"
}
```

2. **Custom Converter Service (Lambda)**
- Loads converters from S3
- Executes in sandboxed environment
- Returns ASM output

3. **Approval Workflow**
- Code review interface
- DVaaS validation testing
- Electronic signature
- Deployment automation

### Implementation Steps

1. **Create Registry Table**
```python
# In services/deploy_services.py
converter_registry = dynamodb.Table(
    self, "CustomConverterRegistry",
    partition_key=dynamodb.Attribute(
        name="converter_id",
        type=dynamodb.AttributeType.STRING
    )
)
```

2. **Create Converter Service**
```python
# services/custom-converter/lambda_function.py
def lambda_handler(event, context):
    converter_id = event['converter_id']
    file_content = event['file_content']
    
    # Load converter from S3
    converter_code = load_converter(converter_id)
    
    # Execute converter
    result = execute_converter(converter_code, file_content)
    
    return result
```

3. **Update Unified Converter**
```python
# Check custom converter registry first
custom_converter = lookup_custom_converter(vendor, model)
if custom_converter and custom_converter['status'] == 'APPROVED':
    return execute_custom_converter(custom_converter, file_content)
```

## Quick Start for New Customer Converter

### 1. Create Converter Template
```bash
cp nova_flex2_converter.py customer_instrument_converter.py
# Edit to match customer format
```

### 2. Test Locally
```python
python test_customer_converter.py
```

### 3. Add to Unified Converter
```python
# Add detection function
def is_customer_instrument(file_content, file_name):
    # Customer-specific detection logic
    pass

# Add to lambda_handler routing
```

### 4. Deploy
```bash
cd services
cdk deploy
```

### 5. Test End-to-End
```python
python test_unified_converter.py
```

## Estimated Implementation Time

**Manual Process (Current)**: 2-4 hours per converter
**Automated Process (Planned)**: 
- Initial setup: 2-3 days
- Per converter: 30 minutes (after approval)

## Files to Modify

**For Manual Process:**
- `services/unified-converter/lambda_function.py`
- `services/deploy_services.py` (if new dependencies)

**For Automated Process:**
- `services/custom-converter/` (new service)
- `services/deploy_services.py` (add registry + service)
- `services/unified-converter/lambda_function.py` (registry lookup)
- Dashboard approval interface (optional)

## Security Considerations

1. **Code Review**: All converters must pass human review
2. **Sandboxing**: Execute in isolated environment  
3. **Input Validation**: Validate file content before processing
4. **Output Validation**: Validate ASM via DVaaS
5. **Access Control**: Only approved converters executable
6. **Audit Logging**: Log all converter executions

## Next Steps

1. **Immediate**: Use manual process for urgent customer needs
2. **Short-term**: Implement Custom Converter Registry
3. **Long-term**: Build approval workflow interface