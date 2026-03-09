"""
Wyatt ASTRA SEC-MALS Converter
Converts Wyatt ASTRA experiment XML files to ASM (Allotrope Simple Model) format
"""
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from typing import Dict, List, Any

def parse_scalar(scalar_elem) -> Dict[str, Any]:
    """Parse scalar element with value and optional units"""
    if scalar_elem is None:
        return None
    
    text = scalar_elem.text
    if not text or text.lower() in ['n/a', 'unknown', '']:
        return None
    
    try:
        value = float(text)
    except ValueError:
        return None
    
    units = scalar_elem.get('units', '')
    
    return {
        'value': value,
        'unit': units
    }

def convert_wyatt_astra_to_asm(xml_content: str) -> Dict[str, Any]:
    """
    Convert Wyatt ASTRA XML to ASM format
    """
    root = ET.fromstring(xml_content)
    ns = {'exp': 'http://www.wyatt.com/schemas/ExperimentReport'}
    
    # Extract experiment name
    experiment_name = root.find('exp:name', ns)
    exp_name = experiment_name.text if experiment_name is not None else "Unknown"
    
    # Extract sample info
    sample = root.find('exp:sample', ns)
    sample_name = sample.find('exp:name', ns).text if sample is not None else "Unknown"
    
    # Extract collection info
    procedures = root.find('exp:procedures', ns)
    collection_time = None
    collection_operator = None
    
    if procedures is not None:
        settings = procedures.find('exp:settings', ns)
        if settings is not None:
            for setting in settings.findall('exp:setting', ns):
                name = setting.find('exp:name', ns)
                value = setting.find('exp:value', ns)
                if name is not None and value is not None:
                    if name.text == 'Collection Time':
                        collection_time = value.text
                    elif name.text == 'Collection Operator':
                        collection_operator = value.text
    
    # Extract results
    results_section = root.find('exp:results', ns)
    measurements = []
    
    if results_section is not None:
        for result in results_section.findall('exp:result', ns):
            result_type = result.get('type', '')
            name_elem = result.find('exp:name', ns)
            scalar_elem = result.find('exp:scalar', ns)
            
            if name_elem is not None and scalar_elem is not None:
                measurement_name = name_elem.text
                scalar_data = parse_scalar(scalar_elem)
                
                if scalar_data:
                    measurements.append({
                        'type': result_type,
                        'name': measurement_name,
                        'value': scalar_data['value'],
                        'unit': scalar_data['unit']
                    })
    
    # Extract instrument configuration
    config = root.find('exp:configuration', ns)
    instruments_info = []
    
    if config is not None:
        instruments = config.find('exp:instruments', ns)
        if instruments is not None:
            for instrument in instruments.findall('exp:instrument', ns):
                inst_type = instrument.get('type', '')
                inst_name = instrument.find('exp:name', ns)
                
                if inst_name is not None:
                    instruments_info.append({
                        'type': inst_type,
                        'name': inst_name.text
                    })
    
    # Build ASM structure
    asm_output = {
        "$asm.manifest": "http://purl.allotrope.org/manifests/chromatography/REC/2024/09/chromatography.manifest",
        "chromatography aggregate document": {
            "device system document": {
                "device identifier": "Wyatt ASTRA SEC-MALS System",
                "equipment serial number": "Unknown",
                "model number": "ASTRA",
                "product manufacturer": "Wyatt Technology"
            },
            "data system document": {
                "file name": exp_name,
                "software name": "ASTRA",
                "software version": "7.1.3.25",
                "ASM converter name": "wyatt_astra_converter",
                "ASM converter version": "1.0.0"
            },
            "chromatography document": [
                {
                    "measurement identifier": exp_name,
                    "sample document": {
                        "sample identifier": sample_name,
                        "description": f"SEC-MALS analysis: {sample_name}"
                    },
                    "measurement time": collection_time or datetime.now().isoformat(),
                    "analyst": collection_operator or "Unknown",
                    "detector configuration": [
                        {
                            "detector identifier": inst['name'],
                            "detector type": inst['type']
                        }
                        for inst in instruments_info
                    ],
                    "chromatography results": {
                        "peak list": [
                            {
                                "peak identifier": "Peak 1",
                                "peak start": measurements[0]['value'] if measurements else 0,
                                "peak end": measurements[-1]['value'] if measurements else 0,
                                "chromatography peak measurements": [
                                    {
                                        "measurement name": m['name'],
                                        "measurement type": m['type'],
                                        "value": m['value'],
                                        "unit": m['unit']
                                    }
                                    for m in measurements[:20]  # Limit to first 20 measurements
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    }
    
    return asm_output

def convert_wyatt_astra_to_asm_batch(xml_file_path: str) -> List[Dict[str, Any]]:
    """
    Convert Wyatt ASTRA XML file to ASM format
    Returns list with single ASM document (one experiment per file)
    """
    with open(xml_file_path, 'rb') as f:
        file_bytes = f.read()
        try:
            xml_content = file_bytes.decode('utf-8')
        except:
            xml_content = file_bytes.decode('latin-1')
    
    asm_output = convert_wyatt_astra_to_asm(xml_content)
    
    return [{
        'sample_id': asm_output['chromatography aggregate document']['chromatography document'][0]['sample document']['sample identifier'],
        'asm_output': asm_output,
        'status': 'success'
    }]

if __name__ == "__main__":
    # Test conversion
    xml_file = r"C:\app\asm2agent\merck\ASTRA Report BSA - Result Over 2 Lines - EDITED.xml"
    
    print("Converting Wyatt ASTRA XML to ASM...")
    results = convert_wyatt_astra_to_asm_batch(xml_file)
    
    for result in results:
        print(f"\nSample: {result['sample_id']}")
        print(f"Status: {result['status']}")
        
        # Save to file
        output_file = f"output/wyatt_astra_{result['sample_id']}.json"
        with open(output_file, 'w') as f:
            json.dump(result['asm_output'], f, indent=2)
        
        print(f"Saved to: {output_file}")
        print(f"Size: {len(json.dumps(result['asm_output']))} bytes")
