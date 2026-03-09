#!/usr/bin/env python3
"""
Test client to simulate laboratory instrument file generation
Creates sample files in watch directory to test Greengrass edge client
"""

import os
import json
import csv
import time
import random
from datetime import datetime

class InstrumentSimulator:
    def __init__(self, output_dir="/tmp/instruments/output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_csv_file(self):
        """Generate sample CSV file like solution analyzer"""
        filename = f"solution_analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        data = [
            ["Sample ID", "Concentration", "pH", "Temperature", "Timestamp"],
            ["SAMPLE_001", f"{random.uniform(0.1, 10.0):.2f}", f"{random.uniform(6.0, 8.0):.1f}", f"{random.uniform(20.0, 25.0):.1f}", datetime.now().isoformat()],
            ["SAMPLE_002", f"{random.uniform(0.1, 10.0):.2f}", f"{random.uniform(6.0, 8.0):.1f}", f"{random.uniform(20.0, 25.0):.1f}", datetime.now().isoformat()],
            ["SAMPLE_003", f"{random.uniform(0.1, 10.0):.2f}", f"{random.uniform(6.0, 8.0):.1f}", f"{random.uniform(20.0, 25.0):.1f}", datetime.now().isoformat()]
        ]
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        print(f"Generated: {filepath}")
        return filepath
    
    def generate_json_file(self):
        """Generate sample JSON file like plate reader"""
        filename = f"plate_reader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        data = {
            "instrument": "PlateReader_XYZ",
            "run_id": f"RUN_{random.randint(1000, 9999)}",
            "timestamp": datetime.now().isoformat(),
            "wells": [
                {"well": "A1", "absorbance": random.uniform(0.1, 2.0), "wavelength": 450},
                {"well": "A2", "absorbance": random.uniform(0.1, 2.0), "wavelength": 450},
                {"well": "B1", "absorbance": random.uniform(0.1, 2.0), "wavelength": 450}
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Generated: {filepath}")
        return filepath

def main():
    """Simulate instrument file generation"""
    simulator = InstrumentSimulator()
    
    print("Starting instrument simulation...")
    print(f"Output directory: {simulator.output_dir}")
    
    try:
        while True:
            # Generate random file type
            if random.choice([True, False]):
                simulator.generate_csv_file()
            else:
                simulator.generate_json_file()
            
            # Wait 10-30 seconds between files
            wait_time = random.randint(10, 30)
            print(f"Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped")

if __name__ == "__main__":
    main()