# Nova FLEX2 Validation Results

**Date**: January 21, 2026  
**File**: merck/SampleResults2025-November-1.json  
**Validator**: Allotropy (comprehensive)  
**Status**: ❌ FAILED (1 error, 2 warnings)

## Issues Found

### ERROR (1)
**Traceability Missing**:
- Calculated data found without data-source-aggregate-document
- Required for audit/regulatory compliance
- **Fix**: Add data source references for all calculated values

### WARNINGS (2)

**1. Unknown Units**:
- Units: mmol/L, psi, sec, mmHg, pH, mosm/kg, g/L
- May be valid Allotrope units added after spec version 2024-12
- **Fix**: Verify units against latest Allotrope spec or use standard alternatives

**2. Missing Metadata**:
- equipment serial number
- software version
- **Fix**: Add device metadata to ASM output

## Validation Metrics

✅ **Structure**: All correct
- technique: solution analyzer (100% confidence)
- measurement_count: 4
- has_sample_document: True
- has_device_control_document: True
- has_custom_information_document: True

❌ **Traceability**: Missing
- has_calculated_data: True
- has_data_source_traceability: False
- calculated_data_identifiers: 0
- data_source_identifiers: 0

## Next Steps

1. **Add Data Source Traceability** (Critical - blocks certification)
   - Add data-source-aggregate-document
   - Link calculated values to source measurements
   
2. **Verify Units** (Warning - may not be blocking)
   - Check if units are valid in latest Allotrope spec
   - Use standard unit format if needed
   
3. **Add Metadata** (Warning - recommended)
   - Add equipment serial number
   - Add software version

## Priority

**HIGH**: Fix traceability (error blocks certification)  
**MEDIUM**: Add metadata (recommended for compliance)  
**LOW**: Verify units (may already be valid)

---

**Conclusion**: Nova FLEX2 converter generates proper ASM structure but needs traceability for regulatory compliance.
