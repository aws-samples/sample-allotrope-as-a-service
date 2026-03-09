#!/usr/bin/env python3
"""
Synthetic Data Generator for Instrument Testing
"""

import json
import random
from datetime import datetime, timedelta

def generate_plate_reader_data():
    """Generate synthetic plate reader data"""
    
    data = "Well,Absorbance,OD600,Sample_ID\n"
    
    # 96-well plate (A1-H12)
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    for row in rows[:4]:  # First 4 rows
        for col in range(1, 13):  # 12 columns
            well = f"{row}{col}"
            absorbance = round(random.uniform(0.1, 2.5), 3)
            od600 = round(random.uniform(0.05, 1.8), 3)
            sample_id = f"SAMPLE_{row}{col:02d}"
            data += f"{well},{absorbance},{od600},{sample_id}\n"
    
    return data

def generate_cell_counter_data():
    """Generate synthetic cell counter data"""
    
    data = "Sample_ID,Total_Cells,Live_Cells,Viability_Percent,Average_Diameter\n"
    
    for i in range(1, 21):  # 20 samples
        sample_id = f"CELL_{i:03d}"
        total_cells = random.randint(500000, 2000000)
        viability = round(random.uniform(85.0, 98.5), 1)
        live_cells = int(total_cells * viability / 100)
        diameter = round(random.uniform(12.5, 18.2), 1)
        data += f"{sample_id},{total_cells},{live_cells},{viability},{diameter}\n"
    
    return data

def generate_solution_analyzer_data():
    """Generate synthetic solution analyzer data"""
    
    data = "Sample_ID,Concentration_mgL,pH,Temperature_C,Conductivity,Turbidity\n"
    
    for i in range(1, 16):  # 15 samples
        sample_id = f"SOL_{i:03d}"
        concentration = round(random.uniform(0.5, 50.0), 2)
        ph = round(random.uniform(6.0, 8.5), 2)
        temperature = round(random.uniform(20.0, 30.0), 1)
        conductivity = round(random.uniform(100, 2000), 0)
        turbidity = round(random.uniform(0.1, 5.0), 2)
        data += f"{sample_id},{concentration},{ph},{temperature},{conductivity},{turbidity}\n"
    
    return data

def generate_hplc_data():
    """Generate synthetic HPLC data"""
    
    data = "Time_min,Peak_Area,Peak_Height,Retention_Time,Compound_ID\n"
    
    compounds = ['Caffeine', 'Aspirin', 'Ibuprofen', 'Acetaminophen', 'Unknown_1']
    
    for i, compound in enumerate(compounds):
        for rep in range(3):  # 3 replicates each
            time = round(random.uniform(0.5, 15.0), 2)
            area = random.randint(10000, 500000)
            height = random.randint(1000, 50000)
            retention = round(random.uniform(2.1, 12.8), 2)
            data += f"{time},{area},{height},{retention},{compound}_R{rep+1}\n"
    
    return data

def generate_mass_spec_data():
    """Generate synthetic mass spectrometry data"""
    
    data = "Mass_mz,Intensity,Charge,Formula,Compound_Name\n"
    
    compounds = [
        (180.063, 'C6H12O6', 'Glucose'),
        (342.117, 'C12H22O11', 'Sucrose'),
        (194.079, 'C7H14O6', 'Gluconic_acid'),
        (146.058, 'C6H10O4', 'Adipic_acid'),
        (162.053, 'C6H10O5', 'Unknown_sugar')
    ]
    
    for mass, formula, name in compounds:
        for i in range(random.randint(2, 5)):  # Multiple peaks per compound
            mz = round(mass + random.uniform(-0.5, 0.5), 3)
            intensity = random.randint(1000, 1000000)
            charge = random.choice([1, 2])
            data += f"{mz},{intensity},{charge},{formula},{name}_{i+1}\n"
    
    return data

# Test data sets
TEST_DATA = {
    'plate_reader_tecan': generate_plate_reader_data(),
    'cell_counter_beckman': generate_cell_counter_data(),
    'solution_analyzer_agilent': generate_solution_analyzer_data(),
    'hplc_waters': generate_hplc_data(),
    'mass_spec_thermo': generate_mass_spec_data()
}

if __name__ == "__main__":
    # Save test files
    for instrument, data in TEST_DATA.items():
        filename = f"test_data_{instrument}.csv"
        with open(filename, 'w') as f:
            f.write(data)
        print(f"Generated: {filename}")