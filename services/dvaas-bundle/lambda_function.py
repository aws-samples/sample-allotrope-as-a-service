"""
DVaaS - Data Validation as a Service (Enhanced with Allotropy)
Standalone ASM validation service with certification report generation
"""

import json
from datetime import datetime
import sys
import os
import base64

# Import certification report generator
try:
    from generate_certification_report import generate_certification_report
    REPORT_GENERATION_AVAILABLE = True
    print("PDF report generation enabled")  # Debug log
except ImportError as e:
    REPORT_GENERATION_AVAILABLE = False
    print(f"PDF report generation disabled: {e}")  # Debug log

def lambda_handler(event, context):
    """DVaaS entry point - validates ASM files"""
    
    try:
        # Handle both direct invocation and API Gateway
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        asm_data = body.get('asm_data')
        validation_level = body.get('validation_level', 'basic')
        use_allotropy = body.get('use_allotropy_validator', True)
        generate_report = body.get('generate_report', False)
        asm_file_name = body.get('file_name', 'unknown.json')
        
        if not asm_data:
            return error_response(400, "Missing asm_data in request")
        
        # Perform validation
        if use_allotropy and validation_level in ['comprehensive', 'certification']:
            result = validate_with_allotropy(asm_data, validation_level)
        else:
            result = validate_asm_basic(asm_data, validation_level)
        
        # Generate certification report if requested
        if generate_report and REPORT_GENERATION_AVAILABLE:
            try:
                pdf_bytes = generate_certification_report(result, asm_file_name)
                result['certification_report'] = {
                    'available': True,
                    'format': 'pdf',
                    'size_bytes': len(pdf_bytes),
                    'data': base64.b64encode(pdf_bytes).decode('utf-8')
                }
            except Exception as e:
                result['certification_report'] = {
                    'available': False,
                    'error': f'Report generation failed: {str(e)}'
                }
        elif generate_report and not REPORT_GENERATION_AVAILABLE:
            result['certification_report'] = {
                'available': False,
                'error': 'Report generation not available (missing dependencies)'
            }
        
        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return error_response(500, f"Validation failed: {str(e)}")

def validate_with_allotropy(asm_data, validation_level):
    """Use Anthropic's allotropy validation script"""
    
    try:
        # Import validation script
        from validate_asm import validate_asm, ValidationResult
        import tempfile
        
        # Write ASM to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(asm_data, f, indent=2)
            temp_path = f.name
        
        try:
            # Run validation
            strict = validation_level == 'certification'
            validation_result = validate_asm(temp_path, strict=strict)
            
            # Build response
            result = {
                'valid': validation_result.is_valid(),
                'validation_level': validation_level,
                'timestamp': datetime.utcnow().isoformat(),
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'info': validation_result.info,
                'metrics': validation_result.metrics,
                'validator': 'allotropy',
                'certification': None
            }
            
            # Add certification for valid ASM
            if validation_level == 'certification' and validation_result.is_valid():
                result['certification'] = {
                    'status': 'ALLOTROPE_CERTIFIED',
                    'certificate_id': f"CERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    'issued_at': datetime.utcnow().isoformat(),
                    'validator': 'allotropy_v1.1.1'
                }
            
            return result
            
        finally:
            # Clean up temp file
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except ImportError:
        # Fallback to basic validation if allotropy not available
        return validate_asm_basic(asm_data, validation_level)
    except Exception as e:
        return {
            'valid': False,
            'validation_level': validation_level,
            'timestamp': datetime.utcnow().isoformat(),
            'errors': [f'Allotropy validation failed: {str(e)}'],
            'warnings': [],
            'validator': 'allotropy_fallback'
        }

def validate_asm_basic(asm_data, validation_level):
    """Validate ASM data against basic schema"""
    
    validation_result = {
        'valid': True,
        'validation_level': validation_level,
        'timestamp': datetime.utcnow().isoformat(),
        'errors': [],
        'warnings': [],
        'certification': None
    }
    
    try:
        # Basic validation checks
        if not isinstance(asm_data, dict):
            validation_result['valid'] = False
            validation_result['errors'].append({
                'field': 'root',
                'message': 'ASM data must be a JSON object'
            })
            return validation_result
        
        # Check manifest
        manifest = asm_data.get('$asm.manifest', '')
        if not manifest:
            validation_result['errors'].append({
                'field': '$asm.manifest',
                'message': 'Missing ASM manifest'
            })
            validation_result['valid'] = False
        elif not manifest.startswith('http://purl.allotrope.org/manifests/'):
            validation_result['warnings'].append({
                'field': '$asm.manifest',
                'message': 'Non-standard manifest URL format'
            })
        
        # Check measurement document
        measurements = asm_data.get('measurement document', [])
        if not measurements:
            validation_result['errors'].append({
                'field': 'measurement document',
                'message': 'No measurements found'
            })
            validation_result['valid'] = False
        elif not isinstance(measurements, list):
            validation_result['errors'].append({
                'field': 'measurement document',
                'message': 'Measurement document must be an array'
            })
            validation_result['valid'] = False
        
        # Certification for valid ASM
        if validation_level == 'certification' and validation_result['valid']:
            validation_result['certification'] = {
                'status': 'ALLOTROPE_CERTIFIED',
                'certificate_id': f"CERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                'issued_at': datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'].append({
            'field': 'general',
            'message': f'Validation error: {str(e)}'
        })
    
    return validation_result

def error_response(status_code, message):
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }