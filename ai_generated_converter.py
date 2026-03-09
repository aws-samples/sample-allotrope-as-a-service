import csv
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class CSVtoASMConverter:
    def __init__(self):
        self.manifest_url = "https://raw.githubusercontent.com/adap/asm/main/manifests/basic_measurements.json"
        self.metadata = {
            "measurement_type": "solution_analysis",
            "instrument_type": "solution_analyzer",
            "creation_date": datetime.now().isoformat()
        }

    def read_csv(self, filepath: str) -> List[Dict]:
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            raise Exception(f"Error reading CSV file: {str(e)}")

    def convert_row(self, row: Dict) -> Dict[str, Any]:
        measurements = {}
        
        try:
            for key, value in row.items():
                if key == 'Sample ID':
                    continue
                    
                measurements[key.lower()] = {
                    "value": float(value),
                    "unit": self._get_unit(key)
                }
                
            return {
                "sample_id": row['Sample ID'],
                "measurements": measurements
            }
            
        except ValueError as e:
            raise Exception(f"Error converting values for sample {row.get('Sample ID', 'unknown')}: {str(e)}")

    def _get_unit(self, measurement: str) -> str:
        units = {
            'pH': 'pH',
            'Osmolality': 'mOsm/kg',
            'Glucose': 'mmol/L',
            'Lactate': 'mmol/L'
        }
        return units.get(measurement, 'unknown')

    def generate_asm(self, samples: List[Dict]) -> Dict:
        return {
            "manifest_url": self.manifest_url,
            "metadata": self.metadata,
            "samples": [self.convert_row(row) for row in samples]
        }

    def convert_file(self, input_path: str, output_path: str = None) -> None:
        try:
            if not output_path:
                output_path = Path(input_path).with_suffix('.asm.json')

            samples = self.read_csv(input_path)
            asm_data = self.generate_asm(samples)

            with open(output_path, 'w') as f:
                json.dump(asm_data, f, indent=2)

        except Exception as e:
            raise Exception(f"Conversion failed: {str(e)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python converter.py <input_csv> [output_json]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        converter = CSVtoASMConverter()
        converter.convert_file(input_file, output_file)
        print(f"Successfully converted {input_file} to ASM format")
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()