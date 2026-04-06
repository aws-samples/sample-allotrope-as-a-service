"""
DVaaS - Data Validation as a Service
ASM validation using official Allotrope JSON schemas (jsonschema-rs)
with supplementary $asm attribute validation and certification reports.
"""

import json
from datetime import datetime
import base64
import tempfile
import os


def lambda_handler(event, context):
    """DVaaS entry point - validates ASM files against Allotrope schemas."""
    try:
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        asm_data = body.get('asm_data')
        validation_level = body.get('validation_level', 'basic')
        generate_report = body.get('generate_report', False)
        asm_file_name = body.get('file_name', 'unknown.json')
        rule_sets_input = body.get('rule_sets', [])

        if not asm_data:
            return error_response(400, "Missing asm_data in request")

        # Always use schema-based validation
        result = run_validation(asm_data, validation_level)

        # Run plugin rule sets if provided
        if rule_sets_input:
            try:
                from rule_engine import evaluate_rule_sets
                plugin_findings = evaluate_rule_sets(asm_data, rule_sets_input)
                
                # Separate into errors and warnings
                plugin_errors = [f for f in plugin_findings if f['severity'] == 'error']
                plugin_warnings = [f for f in plugin_findings if f['severity'] in ('warning', 'info')]
                
                # Format as strings for backward compatibility + keep structured data
                for f in plugin_errors:
                    result['errors'].append(f"[{f['rule_set']}:{f['rule_id']}] {f['message']}")
                for f in plugin_warnings:
                    result['warnings'].append(f"[{f['rule_set']}:{f['rule_id']}] {f['message']}")
                
                # Add structured findings
                result['plugin_findings'] = plugin_findings
                result['rule_sets_applied'] = list(set(rs.get('rule_set_id', 'unknown') for rs in rule_sets_input))
                
                # Recalculate validity — plugin errors make it invalid
                if plugin_errors:
                    result['valid'] = False
            except Exception as e:
                result['warnings'].append(f"WARNING: Plugin rule evaluation failed: {str(e)}")

        # Store validation job in history
        store_validation_job(result, asm_file_name)

        # Generate certification report if requested
        if generate_report:
            try:
                from generate_certification_report import generate_certification_report
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


def run_validation(asm_data, validation_level):
    """Run schema-based validation using official Allotrope schemas."""
    from validate_asm import validate_asm, ValidationResult

    # Write ASM to temp file for validator
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(asm_data, f, indent=2)
        temp_path = f.name

    try:
        strict = validation_level == 'certification'
        validation_result = validate_asm(temp_path, strict=strict)

        result = {
            'valid': validation_result.is_valid(),
            'schema_compliant': validation_result.is_valid(),
            'validation_level': validation_level,
            'timestamp': datetime.utcnow().isoformat(),
            'errors': validation_result.errors,
            'warnings': validation_result.warnings,
            'info': validation_result.info,
            'metrics': validation_result.metrics,
            'validator': 'allotrope-schema-jsonschema-rs',
            'certification': None
        }

        if validation_level == 'certification' and validation_result.is_valid():
            result['certification'] = {
                'status': 'ALLOTROPE_CERTIFIED',
                'certificate_id': f"CERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                'issued_at': datetime.utcnow().isoformat(),
                'validator': 'allotrope-schema-jsonschema-rs',
                'schema_version': validation_result.metrics.get('schema_id', 'unknown')
            }

        return result

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def store_validation_job(result, file_name):
    """Store validation job in ConversionHistory for Control Tower."""
    try:
        import boto3
        table_name = os.environ.get('CONVERSION_HISTORY_TABLE')
        if not table_name:
            return
        table = boto3.resource('dynamodb').Table(table_name)
        table.put_item(Item={
            'conversion_id': f"VALIDATE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'type': 'validation',
            'timestamp': result.get('timestamp', datetime.utcnow().isoformat()),
            'status': 'pass' if result.get('valid') else 'fail',
            'file_name': file_name,
            'validation_level': result.get('validation_level', 'basic'),
            'validator': result.get('validator', 'unknown'),
            'error_count': len(result.get('errors', [])),
            'warning_count': len(result.get('warnings', [])),
            'technique': result.get('metrics', {}).get('technique', '-'),
            'schema_id': result.get('metrics', {}).get('schema_id', '-'),
            'source': 'dvaas',
        })
    except Exception:
        pass  # Don't fail validation if storage fails


def error_response(status_code, message):
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
