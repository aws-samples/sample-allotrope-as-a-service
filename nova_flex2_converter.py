"""
Nova BioProfile FLEX2 Converter
Converts Merck CSV format to ASM (Allotrope Simple Model)
"""

import json
import csv
from datetime import datetime
from uuid import uuid4

def parse_flex2_csv(csv_content):
    """Parse Nova FLEX2 CSV format"""
    lines = csv_content.strip().split('\n')
    reader = csv.DictReader(lines)
    return list(reader)

def convert_row_to_asm(row, row_index):
    """Convert single CSV row to complete ASM document"""
    
    sample_id = row.get('Sample ID', '').strip()
    sample_type = row.get('Sample Type', '').strip()
    timestamp = row.get('Date & Time', '').strip()
    operator = row.get('Operator', '').strip()
    
    # Parse timestamp
    try:
        dt = datetime.strptime(timestamp, '%m/%d/%Y  %I:%M:%S %p')
        iso_timestamp = dt.strftime('%Y-%m-%dT%H:%M:%S.000+00:00')
    except:
        iso_timestamp = datetime.utcnow().isoformat() + '+00:00'
    
    # Helper to safely get float
    def get_float(key):
        val = row.get(key, '').strip()
        return float(val) if val else None
    
    # Build measurement documents with IDs for traceability
    measurements = []
    measurement_ids = {}  # Track IDs for data source references
    
    # 1. Blood Gas Measurement
    po2 = get_float('PO2')
    pco2 = get_float('PCO2')
    if po2 and pco2:
        gas_id = str(uuid4())
        measurement_ids['gas'] = gas_id
        measurements.append({
            "measurement identifier": gas_id,
            "measurement time": iso_timestamp,
            "device control aggregate document": {
                "device control document": [{
                    "device type": "blood gas analyzer",
                    "detection type": "sensor"
                }]
            },
            "pO2": {"value": po2, "unit": "mmHg"},
            "pCO2": {"value": pco2, "unit": "mmHg"},
            "oxygen saturation": {"value": get_float('O2 Saturation'), "unit": "%"},
            "carbon dioxide saturation": {"value": get_float('CO2 Saturation'), "unit": "%"},
            "sample document": {
                "sample identifier": sample_id,
                "description": sample_type
            }
        })
    
    # 2. pH Measurement
    ph = get_float('pH')
    if ph:
        ph_id = str(uuid4())
        measurement_ids['ph'] = ph_id
        measurements.append({
            "measurement identifier": ph_id,
            "measurement time": iso_timestamp,
            "device control aggregate document": {
                "device control document": [{
                    "device type": "pH",
                    "detection type": "sensor"
                }]
            },
            "pH": {"value": ph, "unit": "pH"},
            "temperature": {"value": get_float('Vessel Temperature (°C)'), "unit": "degC"},
            "sample document": {
                "sample identifier": sample_id,
                "description": sample_type
            }
        })
    
    # 3. Osmolality Measurement
    osm = get_float('Osm')
    if osm:
        measurements.append({
            "measurement identifier": str(uuid4()),
            "measurement time": iso_timestamp,
            "device control aggregate document": {
                "device control document": [{
                    "device type": "osmolality",
                    "detection type": "sensor"
                }]
            },
            "osmolality": {"value": osm, "unit": "mosm/kg"},
            "sample document": {
                "sample identifier": sample_id,
                "description": sample_type
            }
        })
    
    # 4. Metabolite Measurement
    analytes = []
    if get_float('Gln'): analytes.append({"analyte name": "glutamine", "molar concentration": {"value": get_float('Gln'), "unit": "mmol/L"}})
    if get_float('Glu'): analytes.append({"analyte name": "glutamate", "molar concentration": {"value": get_float('Glu'), "unit": "mmol/L"}})
    if get_float('Gluc'): analytes.append({"analyte name": "glucose", "mass concentration": {"value": get_float('Gluc'), "unit": "g/L"}})
    if get_float('Lac'): analytes.append({"analyte name": "lactate", "mass concentration": {"value": get_float('Lac'), "unit": "g/L"}})
    if get_float('NH4+'): analytes.append({"analyte name": "ammonium", "molar concentration": {"value": get_float('NH4+'), "unit": "mmol/L"}})
    if get_float('Na+'): analytes.append({"analyte name": "sodium", "molar concentration": {"value": get_float('Na+'), "unit": "mmol/L"}})
    if get_float('K+'): analytes.append({"analyte name": "potassium", "molar concentration": {"value": get_float('K+'), "unit": "mmol/L"}})
    if get_float('Ca++'): analytes.append({"analyte name": "calcium", "molar concentration": {"value": get_float('Ca++'), "unit": "mmol/L"}})
    
    if analytes:
        measurements.append({
            "measurement identifier": str(uuid4()),
            "measurement time": iso_timestamp,
            "device control aggregate document": {
                "device control document": [{
                    "device type": "metabolite analyzer",
                    "detection type": "sensor"
                }]
            },
            "analyte aggregate document": {"analyte document": analytes},
            "sample document": {
                "sample identifier": sample_id,
                "description": sample_type
            }
        })
    
    # Calculated data with traceability
    calculated_data = []
    data_sources = []
    
    if get_float('pH @ Temp'):
        calc_id = str(uuid4())
        calculated_data.append({
            "calculated data identifier": calc_id,
            "calculated data name": "temperature corrected pH",
            "calculated result": {"value": get_float('pH @ Temp'), "unit": "pH"}
        })
        if 'ph' in measurement_ids:
            data_sources.append({
                "data source identifier": measurement_ids['ph'],
                "data source feature": "pH measurement"
            })
    
    if get_float('PO2 @ Temp'):
        calc_id = str(uuid4())
        calculated_data.append({
            "calculated data identifier": calc_id,
            "calculated data name": "temperature corrected pO2",
            "calculated result": {"value": get_float('PO2 @ Temp'), "unit": "mmHg"}
        })
        if 'gas' in measurement_ids:
            data_sources.append({
                "data source identifier": measurement_ids['gas'],
                "data source feature": "pO2 measurement"
            })
    
    if get_float('PCO2 @ Temp'):
        calc_id = str(uuid4())
        calculated_data.append({
            "calculated data identifier": calc_id,
            "calculated data name": "temperature corrected pCO2",
            "calculated result": {"value": get_float('PCO2 @ Temp'), "unit": "mmHg"}
        })
        if 'gas' in measurement_ids:
            data_sources.append({
                "data source identifier": measurement_ids['gas'],
                "data source feature": "pCO2 measurement"
            })
    
    if get_float('HCO3'):
        calc_id = str(uuid4())
        calculated_data.append({
            "calculated data identifier": calc_id,
            "calculated data name": "bicarbonate",
            "calculated result": {"value": get_float('HCO3'), "unit": "mmol/L"}
        })
        if 'gas' in measurement_ids and 'ph' in measurement_ids:
            data_sources.append({
                "data source identifier": measurement_ids['gas'],
                "data source feature": "pCO2 measurement"
            })
            data_sources.append({
                "data source identifier": measurement_ids['ph'],
                "data source feature": "pH measurement"
            })
    
    # Custom information - Match Merck order
    custom_info = []
    if get_float('Pre-Dilution Multiplier') is not None: 
        custom_info.append({"datum label": "Pre-Dilution Multiplier", "scalar double datum": get_float('Pre-Dilution Multiplier'), "unit": "(unitless)"})
    if get_float('Vessel Pressure (psi)') is not None: 
        custom_info.append({"datum label": "Vessel Pressure (psi)", "scalar double datum": get_float('Vessel Pressure (psi)'), "unit": "psi"})
    if get_float('Sparging O2%') is not None: 
        custom_info.append({"datum label": "Sparging O2%", "scalar double datum": get_float('Sparging O2%'), "unit": "%"})
    if get_float('pH / Gas Flow Time') is not None: 
        custom_info.append({"datum label": "pH / Gas Flow Time", "scalar double datum": get_float('pH / Gas Flow Time'), "unit": "sec"})
    if get_float('Chemistry Flow Time') is not None: 
        custom_info.append({"datum label": "Chemistry Flow Time", "scalar double datum": get_float('Chemistry Flow Time'), "unit": "sec"})
    
    ratio = row.get('Chemistry Dilution Ratio', '').strip()
    if ratio and ':' in ratio:
        ratio_val = ratio.split(':')[1]
        custom_info.append({"datum label": "Chemistry Dilution Ratio", "scalar double datum": 1.0/float(ratio_val), "unit": "(unitless)"})
    
    chem_cart = row.get('Chemistry Cartridge Lot Number', '').strip()
    if chem_cart: 
        custom_info.append({"datum label": "Chemistry Cartridge Lot Number", "scalar string datum": chem_cart})
    
    chem_card = row.get('Chemistry Card Lot Number', '').strip()
    if chem_card: 
        custom_info.append({"datum label": "Chemistry Card Lot Number", "scalar string datum": chem_card})
    
    gas_cart = row.get('Gas Cartridge Lot Number', '').strip()
    if gas_cart: 
        custom_info.append({"datum label": "Gas Cartridge Lot Number", "scalar string datum": gas_cart})
    
    gas_card = row.get('Gas Card Lot Number', '').strip()
    if gas_card: 
        custom_info.append({"datum label": "Gas Card Lot Number", "scalar string datum": gas_card})
    
    # Build complete ASM
    asm = {
        "$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/REC/2025/06/solution-analyzer.manifest",
        "solution analyzer aggregate document": {
            "data system document": {
                "ASM conversion time": datetime.utcnow().isoformat() + '+00:00',
                "ASM converter name": "aws-asm-service",
                "ASM converter version": "1.0.0",
                "ASM file identifier": f"SampleResults-{row_index}.json",
                "data system instance identifier": "SampleResults.csv",
                "file name": "SampleResults.csv",
                "software name": "flex2"
            },
            "device system document": {
                "device identifier": "bioprofile flex2",
                "product manufacturer": "nova biomedical",
                "device document": [{"device type": "solution analyzer"}]
            },
            "solution analyzer document": [{
                "analyst": operator,
                "measurement aggregate document": {
                    "measurement document": measurements
                }
            }]
        }
    }
    
    # Add optional sections
    if calculated_data:
        calc_agg = {"calculated data document": calculated_data}
        if data_sources:
            calc_agg["data source aggregate document"] = {
                "data source document": data_sources
            }
        asm["solution analyzer aggregate document"]["solution analyzer document"][0]["measurement aggregate document"]["calculated data aggregate document"] = calc_agg
    
    if custom_info:
        asm["solution analyzer aggregate document"]["solution analyzer document"][0]["measurement aggregate document"]["custom information aggregate document"] = {
            "custom information document": custom_info
        }
    
    return asm

def convert_csv_to_asm_batch(csv_content):
    """Convert entire CSV to multiple ASM files"""
    rows = parse_flex2_csv(csv_content)
    results = []
    
    for idx, row in enumerate(rows, 1):
        try:
            asm = convert_row_to_asm(row, idx)
            results.append({
                'success': True,
                'row': idx,
                'sample_id': row.get('Sample ID', ''),
                'asm': asm,
                'filename': f"SampleResults-{idx}.json"
            })
        except Exception as e:
            results.append({
                'success': False,
                'row': idx,
                'sample_id': row.get('Sample ID', ''),
                'error': str(e)
            })
    
    return results

if __name__ == "__main__":
    # Test with Merck sample
    with open('merck/SampleResults2025-November.csv', 'r') as f:
        csv_content = f.read()
    
    results = convert_csv_to_asm_batch(csv_content)
    
    print(f"Converted {len(results)} rows")
    print(f"Success: {sum(1 for r in results if r['success'])}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}")
    
    # Save first ASM
    if results[0]['success']:
        with open('test_nova_flex2_output.json', 'w') as f:
            json.dump(results[0]['asm'], f, indent=2)
        print("\nSaved test_nova_flex2_output.json")
