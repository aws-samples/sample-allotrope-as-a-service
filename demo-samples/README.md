# Demo Sample Files

This directory contains sample files used in the ASM Transformation Service demo.

## Files

### 1. sample_plate_reader.csv
**Purpose**: Demonstrate Multi-Instrument service with allotropy library  
**Instrument Type**: Plate reader  
**Format**: CSV with well positions and absorbance readings  
**Expected Result**: Fast conversion (<1 second) using rule-based parser

**Contents**:
- 6 wells (A1-A6)
- 2 absorbance wavelengths (450nm, 650nm)
- Standards, samples, and control

**Demo Command**:
```bash
python demo_presentation.py --demo multi-instrument
```

---

### 2. unknown_instrument.csv
**Purpose**: Demonstrate AI-powered ATaaS with Bedrock Claude  
**Instrument Type**: Unknown (solution analyzer)  
**Format**: Simple CSV with pH, temperature, conductivity  
**Expected Result**: AI analysis and converter generation

**Contents**:
- 5 samples (S1-S5)
- pH measurements
- Temperature readings
- Conductivity values

**Demo Command**:
```bash
python demo_presentation.py --demo ataas
```

---

### 3. Customer Files (in ../merck/)
**Purpose**: Demonstrate customer converter validation  
**Files**:
- `SampleResults2025-November.csv` - Nova FLEX2 instrument data (27 samples)
- `SampleResults2025-November-1.json` - Customer's existing ASM output

**Demo Command**:
```bash
python demo_presentation.py --demo customer-validation
```

---

## Output Files

Demo outputs are saved to `demo-outputs/` directory:

- `multi_instrument_output.json` - ASM from Multi-Instrument service
- `ataas_output.json` - ASM from AI-powered ATaaS
- `ataas_converter.py` - Generated converter code from ATaaS
- `validation_report.json` - DVaaS validation results

---

## Usage

**Run individual demos**:
```bash
# Multi-Instrument demo
python demo_presentation.py --demo multi-instrument

# ATaaS demo  
python demo_presentation.py --demo ataas

# DVaaS demo
python demo_presentation.py --demo dvaas

# Customer validation
python demo_presentation.py --demo customer-validation
```

**Run full presentation**:
```bash
python demo_presentation.py --full
```

---

## For Customer Presentation

**Show source files**:
1. Open `demo-samples/sample_plate_reader.csv` - show simple plate reader data
2. Open `demo-samples/unknown_instrument.csv` - show unknown format
3. Open `merck/SampleResults2025-November.csv` - show real customer data

**Show outputs**:
1. Open `demo-outputs/multi_instrument_output.json` - show ASM structure
2. Open `demo-outputs/ataas_converter.py` - show AI-generated converter code
3. Open `demo-outputs/validation_report.json` - show validation results

**Key talking points**:
- Multi-Instrument: Fast, reliable, 31 instruments supported
- ATaaS: AI-powered, handles unknown formats, generates converter code
- DVaaS: Validates everything, catches compliance issues
- Customer validation: We found and fixed their compliance issue

---

**Last Updated**: January 27, 2026
