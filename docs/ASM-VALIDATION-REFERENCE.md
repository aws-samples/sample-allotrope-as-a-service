# ASM Validation Service - Technical Reference

**Version:** 1.0  
**Date:** January 2026  
**Service:** DVaaS (Data Validation as a Service)  
**Validator:** validate_asm.py (Anthropic/Allotrope Foundation)

---

## Executive Summary

The ASM Validation Service provides **comprehensive, multi-level validation** of Allotrope Simple Model (ASM) JSON files against the official Allotrope specification. This is not basic JSON schema validation - it performs deep structural analysis, semantic validation, and regulatory compliance checks.

---

## Validation Levels

### 1. Basic Validation
- JSON syntax validation
- Manifest presence and format
- Top-level structure

### 2. Comprehensive Validation (Default)
- All basic checks PLUS:
- Nested document structure validation
- Calculated data traceability
- Measurement counting and identification
- Sample role validation
- Statistics document validation
- Unit validation
- Metadata completeness
- Unique identifier validation

### 3. Certification Validation (Strictest)
- All comprehensive checks PLUS:
- Equipment serial numbers required
- Software version required
- All warnings treated as errors
- Full regulatory compliance

---

## What Gets Validated

### 1. Manifest Validation
```python
✓ Presence of $asm.manifest
✓ Valid Allotrope URL format
✓ Technique-specific manifest matching
```

**Example:**
```json
{
  "$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/REC/2025/06/solution-analyzer.manifest"
}
```

### 2. Technique Detection & Validation
```python
✓ Automatic technique detection from aggregate document structure
✓ Validation against 60+ known Allotrope techniques
✓ Content-based technique verification
✓ Technique-specific validation rules
```

**Supported Techniques (60+):**
- solution-analyzer, plate-reader, cell-counting, chromatography
- spectrophotometry, flow-cytometry, mass-spectrometry, pcr
- liquid-handler, electrophoresis, fluorescence, luminescence
- And 48+ more...

### 3. Nested Document Structure Validation

**Critical Feature:** Validates that fields are properly nested, not flattened.

**Sample Document Fields:**
```python
✓ sample identifier
✓ written name
✓ batch identifier
✓ sample role type
✓ location identifier
✓ well location identifier
```

**Device Control Fields:**
```python
✓ device type
✓ detector wavelength setting
✓ compartment temperature
✓ sample volume setting
✓ flow rate
```

**Custom Information Fields:**
```python
✓ Vendor-specific fields
✓ Instrument-specific metadata
```

**Example Error Detected:**
```
ERROR: Fields that should be nested in 'sample document' are flattened on measurement:
['sample identifier', 'well location identifier', 'batch identifier']

Tip: Wrap sample fields in a 'sample document' object inside each measurement
```

### 4. Calculated Data Traceability

**Regulatory Requirement:** All calculated values must link back to source measurements.

```python
✓ Presence of calculated-data-document
✓ Presence of data-source-aggregate-document
✓ Each calculated value has source identifiers
✓ Source identifiers reference actual measurements
```

**Example Structure:**
```json
{
  "calculated data aggregate document": {
    "calculated data document": [{
      "calculated data identifier": "calc-1",
      "calculated data name": "temperature corrected pH",
      "calculated result": {"value": 7.189, "unit": "pH"},
      "data source aggregate document": {
        "data source document": [{
          "data source identifier": "measurement-1",
          "data source feature": "pH measurement"
        }]
      }
    }]
  }
}
```

**Example Error Detected:**
```
ERROR: Calculated data found without data-source-aggregate-document - 
traceability is required for audit/regulatory compliance
```

### 5. Measurement Validation

```python
✓ Counts all measurement documents
✓ Validates unique measurement identifiers
✓ Checks for proper measurement structure
✓ Validates measurement time formats
```

**Metrics Provided:**
- measurement_count: Total measurements found
- measurement_identifiers: Count of unique IDs
- calculated_data_identifiers: Count of calculated values
- data_source_identifiers: Count of traceability links

### 6. Sample Role Validation

```python
✓ Validates against known sample roles:
  - standard sample role
  - blank role
  - control sample role
  - unknown sample role
  - reference sample role
  - calibration sample role
```

### 7. Statistics Validation

```python
✓ Checks for statistics aggregate document
✓ Validates statistic datum roles:
  - median role
  - arithmetic mean role
  - coefficient of variation role
  - standard deviation role
  - standard error role
```

**Required for:** Multi-analyte profiling, bead-based assays

### 8. Unit Validation

```python
✓ Validates unit capitalization (RFU not rfu)
✓ Checks against known Allotrope units
✓ Detects non-standard units
```

**Known Units:**
- Fluorescence: RFU, MFI, (unitless)
- Volume: μL, mL, L
- Concentration: ng/μL, mg/mL, M, mM, μM, nM
- Temperature: degC
- Time: s, min, h
- Molecular weight: bp, Da, kDa

### 9. Metadata Validation

```python
✓ device system document → equipment serial number
✓ data system document → software name
✓ data system document → software version
```

**Example Warning:**
```
WARNING: Missing recommended metadata: 
['equipment serial number', 'software version']
```

### 10. Naming Convention Validation

```python
✓ Detects hyphenated field names (should be space-separated)
✓ Validates proper ASM field naming
```

**Example:**
```
WARNING: Found hyphenated field names (ASM uses spaces):
['sample-identifier', 'measurement-time', 'device-type']

Tip: Use 'sample identifier' not 'sample-identifier'
```

### 11. Liquid Handler Specific Validation

```python
✓ Source/destination pairing validation
✓ Aspiration volume + transfer volume structure
✓ Proper transfer semantics
✓ Labware name validation
```

---

## Validation Output

### Metrics Returned
```json
{
  "technique": "solution analyzer",
  "technique_confidence": 100.0,
  "measurement_count": 27,
  "measurement_identifiers": 27,
  "calculated_data_identifiers": 4,
  "data_source_identifiers": 8,
  "has_sample_document": true,
  "has_device_control_document": true,
  "has_custom_information_document": true,
  "has_calculated_data": true,
  "has_data_source_traceability": true,
  "has_statistics": false
}
```

### Error Categories

**ERRORS (Blocking):**
- Missing required fields
- Incorrect nested structure
- Missing traceability
- Invalid technique
- Measurement count mismatches

**WARNINGS (Non-blocking):**
- Unknown units (may be new Allotrope additions)
- Unknown techniques (may be new Allotrope additions)
- Missing recommended metadata
- Non-standard naming conventions

**INFO (Informational):**
- Detected technique
- Measurement counts
- Document structure presence

---

## Reference Comparison

When a reference ASM is provided, additional validation:

```python
✓ Technique matching
✓ Measurement count comparison
✓ Sample role comparison
✓ Nested document structure comparison
✓ Field presence comparison
```

**Example:**
```
ERROR: Missing 23 measurements: generated 4 vs reference 27
ERROR: Reference has 'sample document' but generated ASM does not - 
fields may be incorrectly flattened
```

---

## Validation Rules Source

**Based on:** Allotrope ASM Specification (December 2024)  
**Schema Source:** https://gitlab.com/allotrope-public/asm/-/tree/main/json-schemas/adm  
**Last Updated:** 2026-01-07

**Note:** Unknown techniques/units generate WARNINGS (not errors) to allow for new additions to the Allotrope specification after the validation rules were last updated.

---

## API Usage

### Endpoint
```
POST https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate
```

### Request
```json
{
  "asm_data": { /* ASM JSON */ },
  "validation_level": "comprehensive",
  "generate_report": true
}
```

### Response
```json
{
  "status": "VALID" | "INVALID",
  "errors": ["ERROR: ..."],
  "warnings": ["WARNING: ..."],
  "info": ["INFO: ..."],
  "metrics": { /* validation metrics */ },
  "certificate_id": "CERT-20260130123456",
  "pdf_report": "base64_encoded_pdf"
}
```

---

## Validation Levels Comparison

| Feature | Basic | Comprehensive | Certification |
|---------|-------|---------------|---------------|
| JSON syntax | ✓ | ✓ | ✓ |
| Manifest validation | ✓ | ✓ | ✓ |
| Technique detection | ✓ | ✓ | ✓ |
| Nested structure | - | ✓ | ✓ |
| Traceability | - | ✓ | ✓ |
| Metadata | - | ✓ | ✓ |
| Serial numbers | - | - | ✓ |
| Software version | - | - | ✓ |
| Warnings as errors | - | - | ✓ |

---

## Common Validation Failures

### 1. Missing Traceability
**Issue:** Calculated values without source links  
**Fix:** Add data-source-aggregate-document

### 2. Flattened Structure
**Issue:** Sample fields directly on measurement  
**Fix:** Wrap in sample document

### 3. Hyphenated Names
**Issue:** Using "sample-identifier"  
**Fix:** Use "sample identifier" (space-separated)

### 4. Missing Metadata
**Issue:** No equipment serial number  
**Fix:** Add to device system document

---

## Regulatory Compliance

**FDA 21 CFR Part 11:**
- ✓ Unique identifiers for audit trail
- ✓ Timestamp precision with timezone
- ✓ Data lineage (calculated from source)
- ✓ Complete metadata capture

**EMA Annex 11:**
- ✓ Data integrity controls
- ✓ Traceability requirements
- ✓ Audit trail completeness

---

## Contact & Support

**Service:** DVaaS (Data Validation as a Service)    
**API Endpoint:** https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/

---

## Appendix: Validation Script Details

**Script:** validate_asm.py  
**Source:** Anthropic/Allotrope Foundation collaboration  
**Lines of Code:** ~1,500  
**Validation Functions:** 15+  
**Supported Techniques:** 60+  
**Known Units:** 50+  
**Sample Roles:** 6  
**Statistic Roles:** 9

**Key Functions:**
- validate_manifest()
- detect_technique()
- validate_technique()
- validate_nested_document_structure()
- validate_calculated_data()
- validate_measurements()
- validate_sample_roles()
- validate_statistics()
- validate_units()
- validate_metadata()
- validate_unique_identifiers()
- validate_liquid_handler_structure()
- compare_to_reference()

---

**This is comprehensive validation, not basic JSON checking.**
