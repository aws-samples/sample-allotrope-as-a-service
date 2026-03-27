"""
Unified ASM Conversion Service
Tries Multi-Instrument (allotropy) first, falls back to ATaaS (AI) if needed
"""

import json
import boto3
import os
import requests
import csv
import io
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

def try_custom_converter(vendor, model, file_content):
    """Try custom converter from registry"""
    
    try:
        # Query registry for matching converter
        registry_table = dynamodb.Table(os.environ.get('CONVERTER_REGISTRY_TABLE'))
        
        # Scan for matching vendor and model (simple implementation)
        response = registry_table.scan(
            FilterExpression='vendor = :vendor AND model = :model AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':vendor': vendor,
                ':model': model,
                ':status': 'APPROVED'
            }
        )
        
        if not response.get('Items'):
            return {'success': False, 'error': 'No approved converter found'}
        
        converter = response['Items'][0]
        converter_id = converter['converter_id']
        
        # Call Custom Converter Service
        custom_endpoint = os.environ.get('CUSTOM_CONVERTER_ENDPOINT')
        
        result = requests.post(
            custom_endpoint,
            json={'converter_id': converter_id, 'file_content': file_content},
            timeout=60
        )
        
        if result.status_code == 200:
            data = result.json()
            return {
                'success': True,
                'converter_id': converter_id,
                'asm_output': data.get('asm_output')
            }
        
        return {'success': False, 'error': f"Custom converter failed: {result.text[:200]}"}
        
    except Exception as e:
        return {'success': False, 'error': f"Custom converter error: {str(e)}"}

def lambda_handler(event, context):
    """Unified conversion with intelligent fallback"""
    
    try:
        # Parse request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        file_content = body.get('file_content', '')
        file_name = body.get('file_name', 'unknown.txt')
        manifest = body.get('manifest', {})
        store_results = body.get('store_results', False)
        
        if not file_content:
            return error_response(400, "No file content provided")
        
        conversion_id = f"UNIFIED-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Step 1: Check Custom Converter Registry (if manifest provided)
        if manifest:
            vendor = manifest.get('vendor', '')
            model = manifest.get('model', '')
            
            custom_result = try_custom_converter(vendor, model, file_content)
            if custom_result['success']:
                response = {
                    'conversion_id': conversion_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'custom-converter',
                    'converter_used': custom_result.get('converter_id'),
                    'asm_output': custom_result['asm_output'],
                    'status': 'success',
                    'message': 'Converted using custom converter'
                }
                
                if store_results:
                    storage_result = store_conversion(response)
                    response['storage'] = storage_result
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(response)
                }
        
        # Check if it's Nova FLEX2 - use embedded custom converter
        if is_nova_flex2(file_content, file_name):
            nova_result = convert_nova_flex2(file_content)
            if nova_result['success']:
                response = {
                    'conversion_id': conversion_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'custom-nova-flex2',
                    'converter_used': 'nova_flex2',
                    'asm_output': nova_result['asm_output'],
                    'field_mapping': nova_result.get('field_mapping', []),
                    'status': 'success',
                    'message': 'Converted using custom Nova FLEX2 converter'
                }
                
                if store_results:
                    storage_result = store_conversion(response)
                    response['storage'] = storage_result
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(response)
                }
        
        # Step 2: Try Multi-Instrument Service (fast, rule-based)
        multi_instrument_result = try_multi_instrument(file_content, file_name)
        
        if multi_instrument_result['success']:
            response = {
                'conversion_id': conversion_id,
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'multi-instrument',
                'converter_used': multi_instrument_result.get('vendor', 'allotropy'),
                'asm_output': multi_instrument_result['asm_output'],
                'field_mapping': multi_instrument_result.get('field_mapping', []),
                'integrity_summary': multi_instrument_result.get('integrity_summary', {}),
                'status': 'success',
                'message': 'Converted using allotropy library with data integrity verification'
            }
        else:
            # Step 2: Fallback to ATaaS (AI-powered)
            ataas_result = try_ataas(file_content)
            
            if ataas_result['success']:
                response = {
                    'conversion_id': conversion_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'ataas-ai',
                    'file_analysis': ataas_result.get('file_analysis', {}),
                    'asm_output': ataas_result['asm_output'],
                    'converter_code': ataas_result.get('converter_code', {}),
                    'status': 'success',
                    'message': 'Converted using AI (Bedrock Claude)'
                }
            else:
                return error_response(500, f"Both conversion methods failed. Multi-Instrument: {multi_instrument_result.get('error')}. ATaaS: {ataas_result.get('error')}")
        
        # Store results if requested
        if store_results:
            storage_result = store_conversion(response)
            response['storage'] = storage_result
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        return error_response(500, f"Error: {str(e)}")

def try_multi_instrument(file_content, file_name):
    """Try allotropy conversion locally with data integrity traceability."""
    try:
        from allotropy_wrapper import convert_with_traceability
        result = convert_with_traceability(file_content, file_name)
        if result['success']:
            return {
                'success': True,
                'asm_output': result['asm_output'],
                'field_mapping': result.get('field_mapping', []),
                'integrity_summary': result.get('integrity_summary', {}),
                'vendor': result.get('vendor', 'unknown'),
            }
        return {'success': False, 'error': result.get('error', 'Unknown error')}
    except ImportError:
        pass

    # Fallback: call multi-instrument service remotely
    try:
        multi_endpoint = os.environ.get('MULTI_INSTRUMENT_ENDPOINT',
                                       'https://6uogqq4zb5.execute-api.us-east-1.amazonaws.com/prod/convert')
        response = requests.post(
            multi_endpoint,
            json={'file_content': file_content, 'file_name': file_name},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get('asm_output'):
                return {
                    'success': True,
                    'asm_output': result['asm_output'],
                    'vendor': result.get('vendor', 'unknown'),
                }
        return {'success': False, 'error': f"Multi-Instrument failed: {response.text[:200]}"}
    except Exception as e:
        return {'success': False, 'error': f"Multi-Instrument error: {str(e)}"}

def try_ataas(file_content):
    """Fallback to ATaaS AI-powered conversion"""
    
    try:
        ataas_endpoint = os.environ.get('ATAAS_ENDPOINT',
                                       'https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod/convert')
        
        response = requests.post(
            ataas_endpoint,
            json={'file_content': file_content},
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'file_analysis': result.get('file_analysis', {}),
                'asm_output': result.get('asm_output', {}),
                'converter_code': result.get('converter_code', {})
            }
        
        return {
            'success': False,
            'error': f"ATaaS failed: {response.text[:200]}"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"ATaaS error: {str(e)}"
        }

def store_conversion(conversion_data):
    """Store conversion results in S3 and DynamoDB"""
    
    try:
        s3 = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        
        conversion_id = conversion_data.get('conversion_id')
        bucket = os.environ.get('ASM_FILES_BUCKET', 'asm-converted-files')
        table_name = os.environ.get('CONVERSION_HISTORY_TABLE', 'ConversionHistory')
        
        # Store ASM file
        asm_key = f"asm_files/{conversion_id}.json"
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
                'method': conversion_data['method'],
                'asm_s3_key': asm_key,
                'status': 'completed'
            }
        )
        
        return {
            'stored': True,
            'location': f's3://{bucket}/{asm_key}'
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

def is_nova_flex2(file_content, file_name):
    """Detect if file is Nova FLEX2 format"""
    if not file_name.lower().endswith('.csv'):
        return False
    
    lines = file_content.strip().split('\n')
    if len(lines) < 2:
        return False
    
    header = lines[0].lower()
    # Check for Nova FLEX2 specific columns
    return 'sample id' in header and 'ph' in header and ('gluc' in header or 'lac' in header or 'gln' in header)

def convert_nova_flex2(file_content):
    """Convert Nova FLEX2 CSV to proper Allotrope ASM - Returns FIRST file only"""
    try:
        reader = csv.DictReader(io.StringIO(file_content))
        rows = list(reader)
        
        if not rows:
            return {'success': False, 'error': 'No data rows found in CSV'}
        
        # Process FIRST row only for dashboard
        row = rows[0]
        idx = 1
        
        # Parse timestamp
        timestamp_str = row.get('Date & Time', '').strip()
        try:
            dt = datetime.strptime(timestamp_str, '%m/%d/%Y  %I:%M:%S %p')
            iso_timestamp = dt.strftime('%Y-%m-%dT%H:%M:%S.000+00:00')
        except:
            iso_timestamp = datetime.utcnow().isoformat() + '+00:00'
        
        # Helper to safely get float
        def get_float(key):
            val = row.get(key, '').strip()
            try:
                return float(val) if val else None
            except:
                return None
        
        # Build 4 separate measurements per sample
        measurements = []
        measurement_ids = {}
        field_mapping = []
        
        # 1. Blood Gas
        po2 = get_float('PO2')
        pco2 = get_float('PCO2')
        if po2 and pco2:
            gas_id = str(uuid.uuid4())
            measurement_ids['gas'] = gas_id
            o2_sat = get_float('O2 Saturation')
            co2_sat = get_float('CO2 Saturation')
            measurements.append({
                "measurement identifier": gas_id,
                "measurement time": iso_timestamp,
                "device control aggregate document": {
                    "device control document": [{"device type": "blood gas analyzer", "detection type": "sensor"}]
                },
                "pO2": {"value": po2, "unit": "mmHg"},
                "pCO2": {"value": pco2, "unit": "mmHg"},
                "oxygen saturation": {"value": o2_sat, "unit": "%"},
                "carbon dioxide saturation": {"value": co2_sat, "unit": "%"},
                "sample document": {
                    "sample identifier": row.get('Sample ID', ''),
                    "description": row.get('Sample Type', '')
                }
            })
            field_mapping.append({"source_field": "PO2", "source_value": po2, "asm_field": "pO2", "asm_value": po2, "unit": "mmHg"})
            field_mapping.append({"source_field": "PCO2", "source_value": pco2, "asm_field": "pCO2", "asm_value": pco2, "unit": "mmHg"})
            if o2_sat is not None:
                field_mapping.append({"source_field": "O2 Saturation", "source_value": o2_sat, "asm_field": "oxygen saturation", "asm_value": o2_sat, "unit": "%"})
            if co2_sat is not None:
                field_mapping.append({"source_field": "CO2 Saturation", "source_value": co2_sat, "asm_field": "carbon dioxide saturation", "asm_value": co2_sat, "unit": "%"})
        
        # 2. pH
        ph = get_float('pH')
        if ph:
            ph_id = str(uuid.uuid4())
            measurement_ids['ph'] = ph_id
            temp = get_float('Vessel Temperature (°C)')
            ph_measurement = {
                "measurement identifier": ph_id,
                "measurement time": iso_timestamp,
                "device control aggregate document": {
                    "device control document": [{"device type": "pH", "detection type": "sensor"}]
                },
                "pH": {"value": ph, "unit": "pH"},
                "sample document": {
                    "sample identifier": row.get('Sample ID', ''),
                    "description": row.get('Sample Type', '')
                }
            }
            if temp is not None:
                ph_measurement["temperature"] = {"value": temp, "unit": "degC"}
                field_mapping.append({"source_field": "Vessel Temperature (°C)", "source_value": temp, "asm_field": "temperature", "asm_value": temp, "unit": "degC"})
            measurements.append(ph_measurement)
            field_mapping.append({"source_field": "pH", "source_value": ph, "asm_field": "pH", "asm_value": ph, "unit": "pH"})
        
        # 3. Osmolality
        osm = get_float('Osm')
        if osm:
            measurements.append({
                "measurement identifier": str(uuid.uuid4()),
                "measurement time": iso_timestamp,
                "device control aggregate document": {
                    "device control document": [{"device type": "osmolality", "detection type": "sensor"}]
                },
                "osmolality": {"value": osm, "unit": "mosm/kg"},
                "sample document": {
                    "sample identifier": row.get('Sample ID', ''),
                    "description": row.get('Sample Type', '')
                }
            })
            field_mapping.append({"source_field": "Osm", "source_value": osm, "asm_field": "osmolality", "asm_value": osm, "unit": "mOsm/kg"})
        
        # 4. Metabolites
        analyte_map = [
            ('Gln', 'glutamine', 'molar concentration', 'mmol/L'),
            ('Glu', 'glutamate', 'molar concentration', 'mmol/L'),
            ('Gluc', 'glucose', 'mass concentration', 'g/L'),
            ('Lac', 'lactate', 'mass concentration', 'g/L'),
            ('NH4+', 'ammonium', 'molar concentration', 'mmol/L'),
            ('Na+', 'sodium', 'molar concentration', 'mmol/L'),
            ('K+', 'potassium', 'molar concentration', 'mmol/L'),
            ('Ca++', 'calcium', 'molar concentration', 'mmol/L'),
        ]
        analytes = []
        for csv_col, name, conc_type, unit in analyte_map:
            val = get_float(csv_col)
            if val:
                analytes.append({"analyte name": name, conc_type: {"value": val, "unit": unit}})
                field_mapping.append({"source_field": csv_col, "source_value": val, "asm_field": f"{name} ({conc_type})", "asm_value": val, "unit": unit})
        
        if analytes:
            measurements.append({
                "measurement identifier": str(uuid.uuid4()),
                "measurement time": iso_timestamp,
                "device control aggregate document": {
                    "device control document": [{"device type": "metabolite analyzer", "detection type": "sensor"}]
                },
                "analyte aggregate document": {"analyte document": analytes},
                "sample document": {
                    "sample identifier": row.get('Sample ID', ''),
                    "description": row.get('Sample Type', '')
                }
            })
        
        # Calculated data
        calc_map = [
            ('pH @ Temp', 'temperature corrected pH', 'pH'),
            ('PO2 @ Temp', 'temperature corrected pO2', 'mmHg'),
            ('PCO2 @ Temp', 'temperature corrected pCO2', 'mmHg'),
            ('HCO3', 'bicarbonate', 'mmol/L'),
        ]
        calculated_data = []
        for csv_col, calc_name, unit in calc_map:
            val = get_float(csv_col)
            if val:
                calculated_data.append({"calculated data name": calc_name, "calculated result": {"value": val, "unit": unit}})
                field_mapping.append({"source_field": csv_col, "source_value": val, "asm_field": f"{calc_name} (calculated)", "asm_value": val, "unit": unit})
        
        # Custom information
        custom_info = []
        custom_num_fields = [
            ('Pre-Dilution Multiplier', '(unitless)'),
            ('Vessel Pressure (psi)', 'psi'),
            ('Sparging O2%', '%'),
            ('pH / Gas Flow Time', 'sec'),
            ('Chemistry Flow Time', 'sec'),
        ]
        for csv_col, unit in custom_num_fields:
            val = get_float(csv_col)
            if val is not None:
                custom_info.append({"datum label": csv_col, "scalar double datum": val, "unit": unit})
                field_mapping.append({"source_field": csv_col, "source_value": val, "asm_field": f"{csv_col} (custom info)", "asm_value": val, "unit": unit})
        
        ratio = row.get('Chemistry Dilution Ratio', '').strip()
        if ratio and ':' in ratio:
            try:
                ratio_val = float(ratio.split(':')[1])
                custom_info.append({"datum label": "Chemistry Dilution Ratio", "scalar double datum": 1.0/ratio_val, "unit": "(unitless)"})
                field_mapping.append({"source_field": "Chemistry Dilution Ratio", "source_value": ratio, "asm_field": "Chemistry Dilution Ratio (custom info)", "asm_value": ratio, "unit": "(unitless)"})
            except:
                pass
        
        # String metadata fields
        string_meta_fields = [
            ('Vessel ID', 'Vessel ID'),
            ('Batch ID', 'Batch ID'),
            ('Cell Type', 'Cell Type'),
            ('Comment', 'Comment'),
            ('Tray Location', 'Tray Location'),
            ('Time In Tray', 'Time In Tray'),
            ('Sample Time', 'Sample Time'),
            ('Chemistry Cartridge Lot Number', 'Chemistry Cartridge Lot Number'),
            ('Chemistry Card Lot Number', 'Chemistry Card Lot Number'),
            ('Gas Cartridge Lot Number', 'Gas Cartridge Lot Number'),
            ('Gas Card Lot Number', 'Gas Card Lot Number'),
        ]
        for label, key in string_meta_fields:
            val = row.get(key, '').strip()
            if val:
                custom_info.append({"datum label": label, "scalar string datum": val})
                field_mapping.append({"source_field": key, "source_value": val, "asm_field": f"{label} (custom info)", "asm_value": val, "unit": ""})
        
        # Build ASM
        asm = {
            "$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/REC/2025/06/solution-analyzer.manifest",
            "solution analyzer aggregate document": {
                "data system document": {
                    "ASM conversion time": datetime.utcnow().isoformat() + '+00:00',
                    "ASM converter name": "aws-asm-service",
                    "ASM converter version": "1.0.0",
                    "ASM file identifier": f"SampleResults-{idx}.json",
                    "data system instance identifier": "SampleResults.csv",
                    "UNC path": "SampleResults.csv",
                    "file name": "SampleResults.csv",
                    "software name": "flex2"
                },
                "device system document": {
                    "device identifier": "bioprofile flex2",
                    "product manufacturer": "nova biomedical",
                    "device document": [{"device type": "solution analyzer"}]
                },
                "solution analyzer document": [{
                    "analyst": row.get('Operator', ''),
                    "measurement aggregate document": {
                        "measurement document": measurements
                    }
                }]
            }
        }
        
        # Add optional sections
        if calculated_data:
            # Add data source traceability
            data_sources = []
            if measurement_ids.get('ph'):
                data_sources.append({"data source identifier": measurement_ids['ph'], "data source feature": "pH measurement"})
            if measurement_ids.get('gas'):
                data_sources.append({"data source identifier": measurement_ids['gas'], "data source feature": "gas measurement"})
            
            asm["solution analyzer aggregate document"]["solution analyzer document"][0]["measurement aggregate document"]["calculated data aggregate document"] = {
                "calculated data document": calculated_data,
                "data source aggregate document": {
                    "data source document": data_sources
                }
            }
        
        if custom_info:
            asm["solution analyzer aggregate document"]["solution analyzer document"][0]["measurement aggregate document"]["custom information aggregate document"] = {
                "custom information document": custom_info
            }
        
        return {'success': True, 'asm_output': asm, 'field_mapping': field_mapping}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
