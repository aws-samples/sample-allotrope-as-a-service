# Merck Customer Requirements Analysis

**Date**: January 14, 2026  
**Source**: merck/asm-infrastructure.md + sample files

## Customer Context

### Key Points from Communication

1. **Use Case**: Medium complexity - Solution Analyzer
2. **Lab Process**: Monthly data capture where each row = 1 sample = 1 ASM file
3. **Data Provided**:
   - Source instrument data (CSV)
   - ASM schema (JSON Schema)
   - Example ASM files (3 samples from monthly file)
4. **Primary Goal**: Service to **certify and validate** resulting ASMs
5. **Secondary Goal**: Convert native files to ASM format (PoC)
6. **Data Sensitivity**: Active laboratory data - NDA applies

### Files Provided

```
merck/
├── asm-infrastructure.md              # Customer requirements
├── solution-analyzer.schema.json      # Official ASM schema
├── SampleResults2025-November.csv     # Source instrument data (27 rows)
├── SampleResults2025-November-1.json  # ASM example (row 1)
├── SampleResults2025-November-2.json  # ASM example (row 2)
├── SampleResults2025-November-3.json  # ASM example (row 3)
├── SampleResultsT26B200180C2025-July(in).csv  # Additional source data
├── SampleResultsT26B200180C2025-July(in)-1.json
├── SampleResultsT26B200180C2025-July(in)-2.json
└── SampleResultsT26B200180C2025-July(in)-3.json
```

## Instrument Analysis

### Device Information
- **Instrument**: Nova Biomedical BioProfile FLEX2
- **Type**: Solution Analyzer (multi-parameter)
- **Software**: flex2
- **Converter**: zontal-nova-flex v1.0.0

### Measurement Capabilities

**Blood Gas Analysis**:
- pO2 (partial pressure oxygen) - mmHg
- pCO2 (partial pressure carbon dioxide) - mmHg
- O2 Saturation - %
- CO2 Saturation - %

**pH Measurement**:
- pH value
- Temperature corrected pH
- Temperature - °C

**Osmolality**:
- Osmolality - mosm/kg

**Metabolite Analysis** (8 analytes):
1. Glutamine (Gln) - mmol/L
2. Glutamate (Glu) - mmol/L
3. Glucose (Gluc) - g/L
4. Lactate (Lac) - g/L
5. Ammonium (NH4+) - mmol/L
6. Sodium (Na+) - mmol/L
7. Potassium (K+) - mmol/L
8. Calcium (Ca++) - mmol/L

**Calculated Data**:
- Temperature corrected pO2
- Temperature corrected pCO2
- Bicarbonate (HCO3) - mmol/L

### CSV Structure

**40 columns** including:
- Date & Time
- Sample ID (e.g., "XB21-720-0300")
- Sample Type (e.g., "Default", "PH ONLY")
- Raw measurements
- Temperature corrected values
- Operator information
- Cartridge lot numbers
- Dilution ratios

## ASM Schema Analysis

### Schema Details
- **Schema ID**: `http://purl.allotrope.org/json-schemas/adm/solution-analyzer/REC/2025/06/solution-analyzer.schema`
- **Version**: REC/2025/06 (June 2025 Recommendation)
- **Technique**: Solution Analyzer Aggregate Document

### Required Structure

```json
{
  "$asm.manifest": "solution-analyzer.manifest",
  "solution analyzer aggregate document": {
    "data system document": {...},
    "device system document": {...},
    "solution analyzer document": [
      {
        "analyst": "string",
        "measurement aggregate document": {
          "measurement document": [
            {
              "measurement identifier": "uuid",
              "measurement time": "ISO8601",
              "device control aggregate document": {...},
              "sample document": {...},
              // Measurement-specific fields
            }
          ],
          "calculated data aggregate document": {...},
          "custom information aggregate document": {...}
        }
      }
    ]
  }
}
```

### Supported Detector Types (anyOf)
1. Osmolality detector
2. Absorbance point detector
3. pH detector
4. Blood gas analyzer
5. Cell counting detector
6. Metabolite analyzer
7. Light obscuration detector

### Key Validation Requirements
- `measurement identifier` - REQUIRED
- `measurement time` - REQUIRED
- Proper device control document structure
- Valid units for all measurements
- Proper nesting of documents

## Merck's ASM Conversion Approach

### Converter Details
- **Name**: zontal-nova-flex
- **Version**: 1.0.0
- **Conversion Time**: Captured in ASM
- **File Identifier**: Original filename preserved

### Data Mapping Strategy

**1 CSV Row → 1 ASM File with Multiple Measurements**

Each ASM contains 4 measurement documents:
1. **Blood Gas Measurement** (pO2, pCO2, saturations)
2. **pH Measurement** (pH, temperature)
3. **Osmolality Measurement** (osmolality)
4. **Metabolite Measurement** (8 analytes)

### Custom Information Handling

Merck captures additional metadata:
- Pre-Dilution Multiplier
- Vessel Pressure
- Sparging O2%
- Flow times
- Dilution ratios
- Cartridge lot numbers

All stored in `custom information aggregate document`

## Gap Analysis

### What We Have
✅ Multi-Instrument Service deployed
✅ DVaaS validation service with allotropy
✅ Storage infrastructure (S3 + DynamoDB)
✅ Basic ASM validation

### What We Need

#### 1. Solution Analyzer Specific Support
- [ ] Nova BioProfile FLEX2 parser
- [ ] CSV → ASM conversion for this specific format
- [ ] 1 row → 1 ASM file logic
- [ ] Multiple measurement documents per sample

#### 2. Schema Validation Enhancement
- [ ] Validate against official solution-analyzer.schema.json
- [ ] Support for REC/2025/06 schema version
- [ ] Validate nested document structure
- [ ] Validate required fields (measurement identifier, time)

#### 3. Certification Service
- [ ] Compare generated ASM vs Merck reference ASMs
- [ ] Field-by-field validation
- [ ] Unit validation
- [ ] Structure validation
- [ ] Generate certification report

#### 4. Batch Processing
- [ ] Process monthly CSV files (27+ rows)
- [ ] Generate individual ASM files per row
- [ ] Maintain sample ID mapping
- [ ] Batch validation reporting

## Recommendations

### Immediate Actions (Phase 4)

**1. Create Nova FLEX2 Converter** (3-4 hours)
- Parse 40-column CSV format
- Map to 4 measurement document types
- Handle missing values (empty strings)
- Generate proper UUIDs for measurements
- Preserve custom information

**2. Enhance DVaaS for Schema Validation** (2-3 hours)
- Load solution-analyzer.schema.json
- Validate against official schema
- Report schema violations
- Support REC/2025/06 version

**3. Build Reference Comparison Tool** (3-4 hours)
- Compare generated ASM vs Merck reference
- Field-by-field diff
- Tolerance for floating point values
- Generate comparison report

**4. Batch Processing Pipeline** (2-3 hours)
- CSV → Multiple ASM files
- Parallel processing
- Progress tracking
- Consolidated validation report

### Medium-Term Enhancements

**5. Certification Dashboard**
- Visual comparison of ASMs
- Pass/fail indicators
- Detailed error reporting
- Export certification reports

**6. Performance Metrics**
- Conversion time tracking
- Validation success rates
- Compare vs manual process

## Technical Considerations

### Data Quality Issues in CSV

**Missing Values**: Some rows have empty strings for metabolites
```csv
"11/5/2025  7:57:22 AM",,,"","","","","","","",""
```

**Sample Types**: Different types affect measurements
- "Default" - Full analysis
- "PH ONLY" - Limited measurements

### ASM Complexity

**Nested Structure**: 5 levels deep
```
aggregate document
  → solution analyzer document
    → measurement aggregate document
      → measurement document
        → device control aggregate document
```

**Multiple Measurement Types**: Each sample has 4 different measurement documents with different schemas

### Validation Challenges

1. **Schema Complexity**: anyOf with 7 detector types
2. **Required Fields**: Different per detector type
3. **Unit Validation**: Must match ontology
4. **UUID Generation**: Must be unique per measurement
5. **Timestamp Format**: ISO8601 with timezone

## Success Criteria

### Phase 4 Completion
- [ ] Convert Merck CSV to ASM files
- [ ] Validate against official schema
- [ ] Match Merck reference ASMs
- [ ] Generate certification report
- [ ] Process full monthly file (27 samples)

### Customer Satisfaction
- [ ] >95% match with reference ASMs
- [ ] <1 minute per sample conversion
- [ ] Clear certification status
- [ ] Detailed error reporting
- [ ] Batch processing capability

## Next Steps

1. **Analyze Merck reference ASMs** - Understand exact format
2. **Build Nova FLEX2 converter** - CSV → ASM
3. **Test against reference files** - Validate accuracy
4. **Deploy certification service** - DVaaS enhancement
5. **Demo to customer** - Show working solution

---

**Priority**: HIGH - Customer waiting for PoC demonstration
**Estimated Effort**: 10-14 hours for complete solution
**Dependencies**: Existing DVaaS and Multi-Instrument services
