"""
EndoScan-V Endotoxin Testing Converter
Converts Charles River EndoScan-V XML files to ASM format

Instrument: EndoScan-V (Charles River)
Method: Kinetic Turbidimetric LAL Assay
Output: Endotoxin concentration (EU/mL) and reaction time
"""

import xml.etree.ElementTree as ET
import json
import uuid
from datetime import datetime


def parse_endoscan_xml(xml_content):
    """Parse EndoScan-V XML file"""
    root = ET.fromstring(xml_content)
    
    # Extract plate metadata
    export_plate = root.find('ExportPlate')
    
    metadata = {
        'operator': export_plate.findtext('OperatorName', 'Unknown'),
        'assay_datetime': export_plate.findtext('AssayDateTime', ''),
        'serial_number': export_plate.findtext('SerialNumber', 'Unknown'),
        'file_name': export_plate.findtext('FileName', 'Unknown'),
        'collection_type': export_plate.findtext('CollectionType', 'Unknown'),
        'wavelength': export_plate.findtext('FilterWaveLength', '340'),
        'onset_od': export_plate.findtext('OnsetOD', '0.1'),
        'plate_temp_begin': export_plate.findtext('PlateTemperatureBeginColl', ''),
        'plate_temp_end': export_plate.findtext('PlateTemperatureEndColl', '')
    }
    
    # Extract standard curve
    std_curve = export_plate.find('.//StandardCurve')
    if std_curve is not None:
        metadata['std_curve'] = {
            'name': std_curve.findtext('STDSetName', ''),
            'concentrations': std_curve.findtext('STDSetConcentrations', ''),
            'coefficient0': std_curve.findtext('STDSetCoefficient0', ''),
            'coefficient1': std_curve.findtext('STDSetCoefficient1', ''),
            'r_value': std_curve.findtext('STDSet.r', '')
        }
    
    # Extract groups (samples, standards, spikes, controls)
    groups = []
    for group in export_plate.findall('.//Group'):
        group_data = {
            'name': group.findtext('Name', ''),
            'type': group.findtext('GType', ''),
            'number': group.findtext('Number', ''),
            'product_name': group.findtext('ProductName', ''),
            'product_id': group.findtext('ProductID', ''),
            'lot_number': group.findtext('ProductLotNumber', ''),
            'sponsor': group.findtext('Sponsor', ''),
            'concentration': group.findtext('Concentration', ''),
            'reaction_time': group.findtext('ReactionTime', ''),
            'reaction_time_prefix': group.findtext('RTPrefix', ''),
            'std_dev_rt': group.findtext('StandardDeviationRT', ''),
            'cv_rt': group.findtext('CVRT', ''),
            'eu_number': group.findtext('EUNumber', ''),
            'eu_prefix': group.findtext('EUPrefix', ''),
            'theoretical_eu': group.findtext('TheoreticalEU', ''),
            'spike_recovery': group.findtext('SpikeRecovery', ''),
            'std_set_name': group.findtext('STDSetName', ''),
            'wells': []
        }
        
        # Extract wells
        for well in group.findall('.//Well'):
            well_data = {
                'tag': well.findtext('Tag', ''),
                'masked': well.findtext('Masked', '0'),
                'reaction_time': well.findtext('ReactionTime', ''),
                'reaction_time_prefix': well.findtext('ReactionTimePrefix', ''),
                'eu_number': well.findtext('EUNumber', ''),
                'eu_prefix': well.findtext('EUPrefix', '')
            }
            group_data['wells'].append(well_data)
        
        groups.append(group_data)
    
    # Extract accessories (reagents)
    accessories = []
    for accessory in export_plate.findall('.//Accessory'):
        acc_data = {
            'type': accessory.findtext('Type', ''),
            'product_code': accessory.findtext('ProductCode', ''),
            'lot_number': accessory.findtext('LotNumber', ''),
            'expiration_date': accessory.findtext('ExpirationDate', '')
        }
        accessories.append(acc_data)
    
    metadata['accessories'] = accessories
    
    return metadata, groups


def convert_to_asm(xml_content, file_name='endoscan.xml'):
    """Convert EndoScan-V XML to ASM format"""
    
    metadata, groups = parse_endoscan_xml(xml_content)
    
    # Parse timestamp
    assay_time = metadata['assay_datetime']
    if assay_time:
        try:
            dt = datetime.fromisoformat(assay_time.replace('Z', '+00:00'))
            iso_time = dt.isoformat()
        except:
            iso_time = datetime.utcnow().isoformat() + '+00:00'
    else:
        iso_time = datetime.utcnow().isoformat() + '+00:00'
    
    # Build ASM structure
    asm = {
        "$asm.manifest": "http://purl.allotrope.org/manifests/plate-reader/REC/2024/09/plate-reader.manifest",
        "plate reader aggregate document": {
            "data system document": {
                "ASM conversion time": datetime.utcnow().isoformat() + '+00:00',
                "ASM converter name": "endoscan-v-converter",
                "ASM converter version": "1.0.0",
                "ASM file identifier": file_name.replace('.xml', '.json'),
                "data system instance identifier": file_name,
                "file name": file_name,
                "software name": "EndoScan-V",
                "software version": "6.0.2"
            },
            "device system document": {
                "device identifier": f"endoscan-v-{metadata['serial_number']}",
                "equipment serial number": metadata['serial_number'],
                "product manufacturer": "Charles River",
                "device document": [
                    {
                        "device type": "endotoxin analyzer"
                    }
                ]
            },
            "plate reader document": []
        }
    }
    
    # Process each group as a separate plate reader document
    for group in groups:
        group_type = group['type']
        
        # Create measurement documents for each well
        measurement_docs = []
        
        for well in group['wells']:
            if well['masked'] == '1':
                continue  # Skip masked wells
            
            measurement = {
                "measurement identifier": str(uuid.uuid4()),
                "measurement time": iso_time,
                "device control aggregate document": {
                    "device control document": [
                        {
                            "device type": "endotoxin analyzer",
                            "detection type": "kinetic turbidimetric",
                            "detector wavelength setting": {
                                "value": float(metadata['wavelength']),
                                "unit": "nm"
                            }
                        }
                    ]
                },
                "sample document": {
                    "sample identifier": group['name'],
                    "well location identifier": well['tag'],
                    "batch identifier": group['lot_number'] if group['lot_number'] else None,
                    "sample role type": {
                        'SPL': 'unknown sample role',
                        'STD': 'standard sample role',
                        'SPK': 'control sample role',
                        'CTRL': 'control sample role'
                    }.get(group_type, 'unknown sample role')
                }
            }
            
            # Add absorbance (using reaction time as primary measurement)
            rt = well['reaction_time']
            rt_prefix = well['reaction_time_prefix']
            if rt:
                measurement["absorbance"] = float(rt)
            
            # Add endotoxin concentration as calculated data
            eu = well['eu_number']
            eu_prefix = well['eu_prefix']
            if eu:
                measurement["calculated data aggregate document"] = {
                    "calculated data document": [{
                        "calculated data name": "endotoxin concentration",
                        "calculated result": {
                            "value": float(eu),
                            "unit": "EU/mL"
                        }
                    }]
                }
            
            measurement_docs.append(measurement)
        
        # Create plate reader document for this group
        plate_doc = {
            "analyst": metadata['operator'],
            "measurement aggregate document": {
                "measurement document": measurement_docs
            }
        }
        
        # Add calculated data for group statistics
        if group['reaction_time'] and group['eu_number']:
            plate_doc["measurement aggregate document"]["calculated data aggregate document"] = {
                "calculated data document": [
                    {
                        "calculated data name": "mean reaction time",
                        "calculated result": {
                            "value": float(group['reaction_time']),
                            "unit": "s"
                        }
                    },
                    {
                        "calculated data name": "standard deviation reaction time",
                        "calculated result": {
                            "value": float(group['std_dev_rt']) if group['std_dev_rt'] else 0.0,
                            "unit": "s"
                        }
                    },
                    {
                        "calculated data name": "coefficient of variation reaction time",
                        "calculated result": {
                            "value": float(group['cv_rt']) if group['cv_rt'] else 0.0,
                            "unit": "%"
                        }
                    },
                    {
                        "calculated data name": "mean endotoxin concentration",
                        "calculated result": {
                            "value": float(group['eu_number']),
                            "unit": "EU/mL"
                        }
                    }
                ]
            }
        
        # Add spike recovery for SPK samples
        if group_type == 'SPK' and group['spike_recovery']:
            if "calculated data aggregate document" not in plate_doc["measurement aggregate document"]:
                plate_doc["measurement aggregate document"]["calculated data aggregate document"] = {
                    "calculated data document": []
                }
            
            plate_doc["measurement aggregate document"]["calculated data aggregate document"]["calculated data document"].append({
                "calculated data name": "spike recovery",
                "calculated result": {
                    "value": float(group['spike_recovery']),
                    "unit": "%"
                }
            })
        
        # Add theoretical EU for standards
        if group['theoretical_eu']:
            plate_doc["measurement aggregate document"]["calculated data aggregate document"] = plate_doc["measurement aggregate document"].get("calculated data aggregate document", {"calculated data document": []})
            plate_doc["measurement aggregate document"]["calculated data aggregate document"]["calculated data document"].append({
                "calculated data name": "theoretical endotoxin concentration",
                "calculated result": {
                    "value": float(group['theoretical_eu']),
                    "unit": "EU/mL"
                }
            })
        
        # Add custom information
        custom_info = []
        
        if group['product_name']:
            custom_info.append({
                "datum label": "Product Name",
                "scalar string datum": group['product_name']
            })
        
        if group['product_id']:
            custom_info.append({
                "datum label": "Product ID",
                "scalar string datum": group['product_id']
            })
        
        if group['concentration']:
            custom_info.append({
                "datum label": "Sample Concentration",
                "scalar string datum": group['concentration']
            })
        
        if group['sponsor']:
            custom_info.append({
                "datum label": "Sponsor",
                "scalar string datum": group['sponsor']
            })
        
        if group['std_set_name']:
            custom_info.append({
                "datum label": "Standard Set Name",
                "scalar string datum": group['std_set_name']
            })
        
        if metadata.get('std_curve'):
            std_curve = metadata['std_curve']
            custom_info.extend([
                {
                    "datum label": "Standard Curve Coefficient 0",
                    "scalar double datum": float(std_curve['coefficient0']) if std_curve['coefficient0'] else 0.0,
                    "unit": "(unitless)"
                },
                {
                    "datum label": "Standard Curve Coefficient 1",
                    "scalar double datum": float(std_curve['coefficient1']) if std_curve['coefficient1'] else 0.0,
                    "unit": "(unitless)"
                },
                {
                    "datum label": "Standard Curve R Value",
                    "scalar double datum": float(std_curve['r_value']) if std_curve['r_value'] else 0.0,
                    "unit": "(unitless)"
                }
            ])
        
        if metadata['onset_od']:
            custom_info.append({
                "datum label": "Onset OD",
                "scalar double datum": float(metadata['onset_od']),
                "unit": "OD"
            })
        
        if metadata['plate_temp_begin']:
            custom_info.append({
                "datum label": "Plate Temperature Begin",
                "scalar double datum": float(metadata['plate_temp_begin']),
                "unit": "degC"
            })
        
        if custom_info:
            plate_doc["measurement aggregate document"]["custom information aggregate document"] = {
                "custom information document": custom_info
            }
        
        asm["plate reader aggregate document"]["plate reader document"].append(plate_doc)
    
    return asm


def convert_file(input_path, output_path=None):
    """Convert EndoScan-V XML file to ASM JSON"""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    asm_data = convert_to_asm(xml_content, input_path.split('\\')[-1])
    
    if output_path is None:
        output_path = input_path.replace('.xml', '_ASM.json')
    
    with open(output_path, 'w') as f:
        json.dump(asm_data, f, indent=2)
    
    return output_path, asm_data


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python endoscan_v_converter.py <input.xml> [output.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    output_path, asm_data = convert_file(input_file, output_file)
    
    print(f"Converted: {input_file}")
    print(f"Output: {output_path}")
    print(f"Groups: {len(asm_data['plate reader aggregate document']['plate reader document'])}")
