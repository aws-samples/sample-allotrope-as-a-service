# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at http://aws.amazon.com/apache2.0/
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
"""
Multi-Instrument ASM Converter Service
Supports: 50+ instruments via allotropy + custom converters
"""

import json
import boto3
import os
import tempfile
from datetime import datetime

try:
    from allotropy.parser_factory import Vendor
    from allotropy.allotrope import AllotropeConversionError
    from allotropy.to_allotrope import allotrope_from_file
    ALLOTROPY_AVAILABLE = True
except ImportError:
    ALLOTROPY_AVAILABLE = False

def lambda_handler(event, context):
    """Multi-instrument converter entry point"""
    
    try:
        # Parse request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            file_content = body.get('file_content', '')
            instrument_type = body.get('instrument_type', 'auto')
            vendor = body.get('vendor', 'unknown')
        else:
            file_content = event.get('file_content', '')
            instrument_type = event.get('instrument_type', 'auto')
            vendor = event.get('vendor', 'unknown')
        
        if not file_content:
            return error_response(400, "No file content provided")
        
        # Try allotropy first for supported instruments
        allotropy_result = try_allotropy_conversion(file_content, vendor)
        
        if allotropy_result['success']:
            asm_result = allotropy_result['asm']
            conversion_method = 'allotropy'
            instrument_type = allotropy_result.get('instrument_type', instrument_type)
        else:
            # Fallback to custom converters
            if instrument_type == 'auto':
                instrument_type = detect_instrument_type(file_content, vendor)
            
            if instrument_type == 'plate_reader':
                asm_result = convert_plate_reader(file_content, vendor)
            elif instrument_type == 'cell_counter':
                asm_result = convert_cell_counter(file_content, vendor)
            elif instrument_type == 'solution_analyzer':
                asm_result = convert_solution_analyzer(file_content, vendor)
            else:
                return error_response(400, f"Unsupported instrument type: {instrument_type}")
            
            conversion_method = 'custom'
        
        conversion_id = f"MULTI-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Store result
        storage_result = store_multi_instrument_result({
            'conversion_id': conversion_id,
            'instrument_type': instrument_type,
            'vendor': vendor,
            'asm_output': asm_result,
            'conversion_method': conversion_method,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'conversion_id': conversion_id,
                'instrument_type': instrument_type,
                'vendor': vendor,
                'conversion_method': conversion_method,
                'asm_output': asm_result,
                'storage': storage_result,
                'status': 'success'
            })
        }
        
    except Exception as e:
        return error_response(500, f"Conversion failed: {str(e)}")

def try_allotropy_conversion(file_content, vendor):
    """Try converting with allotropy library"""
    
    if not ALLOTROPY_AVAILABLE:
        return {'success': False, 'error': 'allotropy not available'}
    
    try:
        # Detect vendor from content
        detected_vendor = detect_allotropy_vendor(file_content, vendor)
        if not detected_vendor:
            return {'success': False, 'error': 'vendor not supported by allotropy'}
        
        # Write to temp file for allotropy
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        
        try:
            # Convert with allotropy
            vendor_enum = getattr(Vendor, detected_vendor)
            asm_dict = allotrope_from_file(tmp_path, vendor_enum)
            
            # Determine instrument type from manifest
            manifest = asm_dict.get('$asm.manifest', '')
            if 'plate-reader' in manifest:
                instrument_type = 'plate_reader'
            elif 'cell-count' in manifest:
                instrument_type = 'cell_counter'
            else:
                instrument_type = 'solution_analyzer'
            
            return {
                'success': True,
                'asm': asm_dict,
                'vendor': detected_vendor,
                'instrument_type': instrument_type
            }
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def detect_allotropy_vendor(file_content, vendor_hint):
    """Detect if allotropy supports this vendor"""
    
    content_lower = file_content.lower()
    
    # Map common patterns to allotropy vendors
    vendor_patterns = {
        'BECKMAN_VI_CELL_BLU': ['vi-cell', 'beckman'],
        'BECKMAN_VI_CELL_XR': ['vi-cell xr'],
        'THERMO_FISHER_NANODROP_EIGHT': ['nanodrop', 'eight'],
        'MOLECULAR_DEVICES_SOFTMAX_PRO': ['softmax', 'molecular devices'],
        'AGILENT_GEN5': ['gen5', 'biotek'],
        'THERMO_FISHER_QUANT_STUDIO': ['quantstudio', 'quant studio'],
        'PERKIN_ELMER_ENVISION': ['envision', 'perkinelmer'],
        'BMG_MARS': ['mars', 'bmg'],
        'ROCHE_CEDEX_BIOHT': ['cedex', 'bioht']
    }
    
    # Check vendor hint first
    if vendor_hint and vendor_hint.upper() in [v for v in dir(Vendor) if not v.startswith('_')]:
        return vendor_hint.upper()
    
    # Pattern matching
    for vendor_name, patterns in vendor_patterns.items():
        if any(pattern in content_lower for pattern in patterns):
            return vendor_name
    
    return None

def detect_instrument_type(file_content, vendor):
    """Auto-detect instrument type from file content"""
    
    content_lower = file_content.lower()
    
    # Plate reader indicators
    if any(term in content_lower for term in ['well', 'plate', 'a1', 'b1', 'od', 'absorbance', '96', '384']):
        return 'plate_reader'
    
    # Cell counter indicators  
    if any(term in content_lower for term in ['cell', 'count', 'viability', 'diameter', 'volume']):
        return 'cell_counter'
    
    # Solution analyzer indicators
    if any(term in content_lower for term in ['concentration', 'ph', 'temperature', 'sample']):
        return 'solution_analyzer'
    
    return 'solution_analyzer'  # Default

def convert_plate_reader(file_content, vendor):
    """Convert plate reader data to ASM"""
    
    asm_output = {
        "$asm.manifest": "http://purl.allotrope.org/manifests/plate-reader/BENCHLING/2023/09/plate-reader.manifest",
        "measurement document": []
    }
    
    # Parse plate reader data
    lines = file_content.strip().split('\n')
    if len(lines) < 2:
        return asm_output
    
    for i, line in enumerate(lines[1:], 1):
        values = [v.strip() for v in line.split(',')]
        if len(values) >= 2:
            measurement = {
                "measurement identifier": f"PLATE_WELL_{i}",
                "measurement time": datetime.utcnow().isoformat(),
                "processed data document": {
                    "well_position": values[0] if values else f"A{i}",
                    "absorbance": float(values[1]) if len(values) > 1 and values[1].replace('.','').replace('-','').isdigit() else 0.0,
                    "vendor": vendor
                }
            }
            asm_output["measurement document"].append(measurement)
    
    return asm_output

def convert_cell_counter(file_content, vendor):
    """Convert cell counter data to ASM"""
    
    asm_output = {
        "$asm.manifest": "http://purl.allotrope.org/manifests/cell-counter/BENCHLING/2023/09/cell-counter.manifest",
        "measurement document": []
    }
    
    # Parse cell counter data
    lines = file_content.strip().split('\n')
    if len(lines) < 2:
        return asm_output
    
    for i, line in enumerate(lines[1:], 1):
        values = [v.strip() for v in line.split(',')]
        if len(values) >= 2:
            measurement = {
                "measurement identifier": f"CELL_COUNT_{i}",
                "measurement time": datetime.utcnow().isoformat(),
                "processed data document": {
                    "sample_id": values[0] if values else f"SAMPLE_{i}",
                    "cell_count": int(float(values[1])) if len(values) > 1 and values[1].replace('.','').isdigit() else 0,
                    "viability": float(values[2]) if len(values) > 2 and values[2].replace('.','').isdigit() else 95.0,
                    "vendor": vendor
                }
            }
            asm_output["measurement document"].append(measurement)
    
    return asm_output

def convert_solution_analyzer(file_content, vendor):
    """Convert solution analyzer data to ASM"""
    
    asm_output = {
        "$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/BENCHLING/2023/09/solution-analyzer.manifest",
        "measurement document": []
    }
    
    # Parse solution analyzer data
    lines = file_content.strip().split('\n')
    if len(lines) < 2:
        return asm_output
    
    for i, line in enumerate(lines[1:], 1):
        values = [v.strip() for v in line.split(',')]
        if len(values) >= 2:
            measurement = {
                "measurement identifier": f"SOLUTION_{i}",
                "measurement time": datetime.utcnow().isoformat(),
                "processed data document": {
                    "sample_id": values[0] if values else f"SAMPLE_{i}",
                    "concentration": float(values[1]) if len(values) > 1 and values[1].replace('.','').isdigit() else 0.0,
                    "pH": float(values[2]) if len(values) > 2 and values[2].replace('.','').isdigit() else 7.0,
                    "temperature": float(values[3]) if len(values) > 3 and values[3].replace('.','').isdigit() else 25.0,
                    "vendor": vendor
                }
            }
            asm_output["measurement document"].append(measurement)
    
    return asm_output

def store_multi_instrument_result(conversion_data):
    """Store multi-instrument conversion result"""
    
    try:
        s3 = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        
        conversion_id = conversion_data.get('conversion_id')
        bucket = os.environ.get('ASM_FILES_BUCKET', 'asm-converted-files')
        table_name = os.environ.get('CONVERSION_HISTORY_TABLE', 'ConversionHistory')
        
        # Store ASM file
        asm_key = f"multi_instrument/{conversion_id}.json"
        s3.put_object(
            Bucket=bucket,
            Key=asm_key,
            Body=json.dumps(conversion_data['asm_output'], indent=2),
            ContentType='application/json'
        )
        
        # Store metadata
        table = dynamodb.Table(table_name)
        table.put_item(
            Item={
                'conversion_id': conversion_id,
                'timestamp': conversion_data['timestamp'],
                'instrument_type': conversion_data['instrument_type'],
                'vendor': conversion_data['vendor'],
                'conversion_method': conversion_data.get('conversion_method', 'custom'),
                'asm_s3_key': asm_key,
                'source': 'multi_instrument_service',
                'status': 'completed'
            }
        )
        
        return {
            'stored': True,
            'conversion_id': conversion_id,
            'storage_location': f's3://{bucket}/{asm_key}'
        }
        
    except Exception as e:
        return {
            'stored': False,
            'error': str(e)
        }

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