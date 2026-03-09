#!/usr/bin/env python3
"""
Continuous Greengrass Client Test
Simulates ongoing laboratory instrument file generation
"""

import time
import random
import json
from datetime import datetime
from pathlib import Path
from test_greengrass_final import TestASMEdgeClient

def generate_random_csv():
    """Generate random CSV data like solution analyzer"""
    samples = []
    for i in range(random.randint(2, 5)):
        sample = {
            'Sample ID': f'SAMPLE_{i+1:03d}',
            'Concentration': round(random.uniform(0.1, 10.0), 2),
            'pH': round(random.uniform(6.0, 8.0), 1),
            'Temperature': round(random.uniform(20.0, 25.0), 1)
        }
        samples.append(sample)
    
    # Create CSV content
    headers = list(samples[0].keys())
    csv_lines = [','.join(headers)]
    
    for sample in samples:
        csv_lines.append(','.join(str(sample[h]) for h in headers))
    
    return '\n'.join(csv_lines)

def generate_random_json():
    """Generate random JSON data like plate reader"""
    wells = []
    for row in ['A', 'B', 'C']:
        for col in range(1, random.randint(3, 6)):
            wells.append({
                'well': f'{row}{col}',
                'absorbance': round(random.uniform(0.1, 2.0), 3),
                'wavelength': random.choice([450, 540, 630])
            })
    
    return {
        'instrument': f'PlateReader_{random.randint(100, 999)}',
        'run_id': f'RUN_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'timestamp': datetime.now().isoformat(),
        'wells': wells
    }

def continuous_test(duration_minutes=5):
    """Run continuous test for specified duration"""
    
    print(f"=== Continuous Greengrass Test ({duration_minutes} minutes) ===")
    
    # Setup
    test_dir = Path("continuous_test")
    instrument_dir = test_dir / "instruments" / "output"
    instrument_dir.mkdir(parents=True, exist_ok=True)
    
    config = {
        "apiGatewayUrl": "https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod",
        "watchDirectory": str(instrument_dir),
        "logLevel": "INFO",
        "auditEnabled": True
    }
    
    config_file = test_dir / "config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Initialize client
    client = TestASMEdgeClient(str(config_file))
    
    print(f"Client initialized - Running for {duration_minutes} minutes")
    print(f"Generating files every 10-30 seconds...")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    file_count = 0
    success_count = 0
    
    try:
        while time.time() < end_time:
            # Generate random file type
            if random.choice([True, False]):
                # CSV file
                content = generate_random_csv()
                filename = f"solution_analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                file_path = instrument_dir / filename
                
                with open(file_path, 'w') as f:
                    f.write(content)
            else:
                # JSON file
                content = generate_random_json()
                filename = f"plate_reader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                file_path = instrument_dir / filename
                
                with open(file_path, 'w') as f:
                    json.dump(content, f, indent=2)
            
            file_count += 1
            print(f"\n[{file_count}] Generated: {filename}")
            
            # Process file
            result = client.process_file(str(file_path))
            if result and result.get('status') == 'success':
                success_count += 1
                print(f"    SUCCESS - Conversion: {result.get('conversion_id')}")
                print(f"    ASM measurements: {len(result.get('asm_output', {}).get('measurement document', []))}")
            else:
                print(f"    FAILED - {result.get('error') if result else 'Unknown error'}")
            
            # Wait random interval
            wait_time = random.randint(10, 30)
            print(f"    Waiting {wait_time} seconds...")
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    # Summary
    elapsed = time.time() - start_time
    print(f"\n=== Test Summary ===")
    print(f"Duration: {elapsed/60:.1f} minutes")
    print(f"Files generated: {file_count}")
    print(f"Successful conversions: {success_count}")
    print(f"Success rate: {success_count/file_count*100:.1f}%" if file_count > 0 else "N/A")
    print(f"Average processing time: {elapsed/file_count:.1f} seconds per file" if file_count > 0 else "N/A")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    print("Test environment cleaned up")

if __name__ == "__main__":
    # Run 2-minute test
    continuous_test(2)