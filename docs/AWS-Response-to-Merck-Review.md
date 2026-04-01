# AWS Response to Merck ASM Conversion Review

**Date:** March 2026
**In response to:** 2026-03-17 AWS ASM Conversion Review & Merck ASM Basic Design Principles v33

---

## Responses to Questions

### Question 1: How can the AI converter platform capture instrument-specific metadata such as mount path, geography, and server identifiers?

The instrument config file (JSON) is the right vehicle for this. We will extend the instrument config schema to include metadata fields that capture the information currently derived from the mount path:

```json
{
    "vendor": "NOVABIO_FLEX2",
    "model": "BioProfile FLEX2",
    "manufacturer": "Nova Biomedical",
    "instrument_type": "solution_analyzer",
    "file_format": "csv",
    "serial_number": "FLEX2-2024-001",
    "software_version": "6.2.1",
    "location": {
        "geography": "America",
        "site": "New_York",
        "unc_path": "\\\\MERCKSERVER\\ExportDEV\\Results\\",
        "timezone": "America/New_York"
    }
}
```

The instrument config is created once per instrument and reused for every file. The `timezone` field solves the [META] issue where the July file (European) was interpreted with US date format. The `unc_path` field provides the traceability back to the source file server.

For the future Greengrass edge client deployment, the mount path metadata would be captured automatically since the edge client knows which instrument folder it is watching.

### Question 2: Can the AI agent provide a confidence level for each mapping?

Yes, but with an important distinction between conversion routes:

**Custom converters (Route A):** Confidence is 100% by design. Every field mapping is deterministic — the converter author explicitly defines which source field maps to which ASM field. There is no inference or guessing. The Data Integrity Verification report proves this field-by-field.

**Allotropy library (Route B):** Confidence is 100% for supported instruments. Allotropy uses rule-based parsers written specifically for each instrument format. No AI inference involved.

**ATaaS / AI-powered (Route C):** This is where per-mapping confidence levels are valuable. We can enhance the ATaaS service to have Claude provide a confidence score for each field mapping, categorized as:
- **High confidence:** Direct column-to-field match with clear semantic alignment
- **Medium confidence:** Reasonable mapping but multiple valid interpretations exist
- **Low confidence:** Best guess, human review recommended

We recommend that for production use, customers use custom converters (Route A) or allotropy (Route B) where confidence is deterministic. ATaaS (Route C) is best suited for initial analysis of unknown formats, with human-in-the-loop review before the mapping is finalized into a custom converter.

### Question 3: Which validation levels are we using today?

| Merck Level | Description | Our Equivalent | Status |
|-------------|-------------|----------------|--------|
| **Level 1** | ASM schema validation (JSON + ASM tags) | DVaaS with allotropy validation script | ✅ Implemented — checks schema compliance, required fields, structure |
| **Level 2** | Data quality assessment (ASM vs raw data) | Data Integrity Verification (field_mapping) | ⚠️ Work in progress — implemented for Nova FLEX2, rolling out to all converters |
| **Level 3** | Allotrope ASM building principles | Not yet implemented | 🔲 Planned — can be added as DVaaS validation rules |
| **Level 4** | Merck-specific principles | Not yet implemented | 🔲 Planned — configurable per-customer rules |

**Our Data Integrity Verification directly addresses your Level 2 pain point.** You noted that Level 2 requires "significant instrument-specific coding" for each instrument. Our approach solves this: the converter itself emits the field_mapping during conversion, so the verification is automatic. No separate TOSCA database, no SQL queries, no instrument-specific comparison scripts. The converter is the single source of truth.

For Levels 3 and 4, we propose adding the Merck ASM Basic Design Principles as configurable validation rules in DVaaS. This would allow the validation service to check not just schema compliance but also adherence to your design principles (custom field placement, calculated data linkage, term formatting, etc.).

**Regarding labeling errors and warnings by validation level:** We will update DVaaS to tag each finding with the corresponding validation level (L1/L2/L3/L4) so the human-in-the-loop reviewer can prioritize accordingly.

---

## Remediation Plan

### Issue Tracker

| # | Category | Issue | Severity | Status | Action |
|---|----------|-------|----------|--------|--------|
| 1 | [META] | Measurement time missing timezone/geography context | Medium | 🔲 Open | Add `timezone` field to instrument config schema |
| 2 | [ERROR] | Sample type uses invalid ASM term | High | 🔲 Open | Map to valid ASM term from schema |
| 3 | [ERROR] | Skipped processed data: total cell count, viable cell count, cell density dilution factor | High | 🔲 Open | Add processed data aggregate document to converter |
| 4 | [ERROR] | Cell density dilution factor not nested under data processing document | Medium | 🔲 Open | Fix nesting per schema |
| 5 | [ERROR][RULE] | Calculated fields were ignored | High | ✅ Fixed | Calculated data aggregate document with pH @ Temp, PO2 @ Temp, PCO2 @ Temp, HCO3 now included |
| 6 | [ERROR][RULE] | Custom fields were ignored | High | ✅ Fixed | Custom information aggregate document now includes all custom fields (lot numbers, flow times, vessel pressure, dilution ratio, metadata) |
| 7 | [CONFIG] | Missing Data System Document | High | ✅ Partially fixed | Data system document exists with converter name, version, timestamp, file identifier. Needs UNC path and enhanced traceability fields |
| 8 | [CONFIG] | Missing Device Document with device type = "solution analyzer" | High | ✅ Fixed | Device system document includes device type = "solution analyzer" |
| 9 | [META] | No traceability to original source file (UNC path, filename) | Medium | 🔲 Open | Add UNC path from instrument config to data system document |
| 10 | [RULE] | Custom fields have manually added units not in source | Medium | 🔲 Open | Remove units from custom fields where source doesn't provide them |
| 11 | [RULE] | Missing @index for array ordering | Low | 🔲 Open | Add @index to measurement document arrays |
| 12 | [RULE] | Calculated data missing per-calculation data source linkage | Medium | 🔲 Open | Move data source aggregate document inside each calculated data document (known issue documented in MEMORY.md) |
| 13 | [RULE] | No processed data aggregate document layer | Medium | 🔲 Open | Add processed data section for instrument-produced transformations |

### Already Fixed (Since Review)

These issues were identified in the review but have been resolved in subsequent updates:

**Issue 5 — Calculated fields:** Our converter now includes a `calculated data aggregate document` with temperature-corrected pH, PO2, PCO2, and bicarbonate (HCO3). Each includes the calculated value and unit.

**Issue 6 — Custom fields:** Our converter now maps all custom fields to `custom information aggregate document` including: Pre-Dilution Multiplier, Vessel Pressure, Sparging O2%, flow times, Chemistry Dilution Ratio, all lot numbers, Vessel ID, Batch ID, Cell Type, Comment, Tray Location, Time In Tray, and Sample Time.

**Issue 8 — Device Document:** Our converter includes `device system document` with `device identifier: "bioprofile flex2"`, `product manufacturer: "nova biomedical"`, and `device document` with `device type: "solution analyzer"`.

### Remediation Priority

**Phase 1 — High Priority (address before next review)**

| # | Issue | Effort | Change |
|---|-------|--------|--------|
| 1 | Timezone in instrument config | 1 hour | Add `location.timezone` to config schema, use in timestamp parsing |
| 2 | Invalid sample type term | 30 min | Map to valid ASM term per schema |
| 9 | UNC path traceability | 1 hour | Read from instrument config, write to data system document |
| 10 | Remove manually added units from custom fields | 1 hour | Only include units when present in source data |
| 12 | Per-calculation data source linkage | 1 hour | Nest data source aggregate inside each calculated data document |

**Phase 2 — Medium Priority**

| # | Issue | Effort | Change |
|---|-------|--------|--------|
| 3 | Processed data (cell counts, dilution factor) | 2 hours | Add processed data aggregate document, map applicable fields |
| 4 | Dilution factor nesting | 30 min | Nest under data processing document |
| 11 | @index for array ordering | 1 hour | Add @index based on source data order or chronological timestamp |
| 13 | Processed data layer | 2 hours | Distinguish raw measurement vs instrument-produced transformation |

**Phase 3 — Validation Enhancement**

| Item | Effort | Change |
|------|--------|--------|
| DVaaS Level 3 rules (Allotrope principles) | 4 hours | Add design principle checks to validation |
| DVaaS Level 4 rules (Merck-specific) | 4 hours | Add configurable customer-specific rules |
| Validation level labels on findings | 2 hours | Tag each error/warning with L1/L2/L3/L4 |
| ATaaS confidence scores per mapping | 4 hours | Add per-field confidence to AI-generated mappings |

---

## Alignment with Merck Design Principles

### What We Align On Today

| Principle | Our Implementation | Status |
|-----------|-------------------|--------|
| Instrument hardcoded terms | Instrument config JSON file | ✅ Aligned — needs UNC path and timezone additions |
| Data hierarchical structure | Follow solution-analyzer schema | ✅ Aligned |
| ASM terms lowercase with spaces | Terms match schema (pO2, pCO2, pH, osmolality) | ✅ Aligned |
| Custom fields 1:1 transfer | Custom information aggregate document | ✅ Aligned — need to remove manually added units |
| Calculated fields with traceability | Calculated data aggregate document with data sources | ✅ Aligned — need to fix nesting (per-calculation) |
| Manufacturer in lowercase | "nova biomedical" | ✅ Aligned |
| Source file traceability | Data system document with file name, converter info | ⚠️ Partial — need UNC path |

### What We Need to Add

| Principle | Gap | Plan |
|-----------|-----|------|
| Processed data aggregate document | Not implemented | Phase 2 — distinguish raw vs transformed values |
| @index for array ordering | Not implemented | Phase 2 — add explicit ordering |
| HarmonizingBaseTerms integration | Not formalized | Accept customer's base terms spreadsheet as input alongside instrument config |
| Custom field units only from source | We add units manually | Phase 1 — remove manually added units |
| Statistic datum role | Not implemented | Future — add when statistical fields are present |
| Complex file pre-processing | Not implemented | Future — ATaaS can handle some complex formats |

---

## Data Integrity Verification — Addressing Level 2

Your Level 2 validation (TOSCA-based source-to-ASM comparison) requires significant per-instrument coding. Our Data Integrity Verification provides the same assurance with a fundamentally different approach:

| Aspect | Merck Level 2 (TOSCA) | AWS Data Integrity Verification |
|--------|----------------------|--------------------------------|
| Approach | Post-conversion comparison via SQL | Converter emits field_mapping during conversion |
| Per-instrument effort | Significant — load to SQLite, build SQL queries, define tolerances | Zero — field_mapping is built into the converter |
| Tolerance handling | SQL-based rounding and TOSCA parameters | Exact match — no rounding, no tolerance needed |
| Coverage | Depends on SQL queries written | Every field the converter touches |
| Output | TOSCA report | Dashboard table + API response |
| Maintenance | Update SQL when converter changes | Automatic — field_mapping updates with converter |

**Key advantage:** Because the converter emits the mapping at conversion time, there is no separate comparison step, no database, and no instrument-specific SQL. The integrity proof is a byproduct of the conversion itself.

**Current status:** Implemented for Nova FLEX2 (all 40 CSV columns). Required for all custom converters per our requirements spec. Planned for allotropy-based conversions.

---

## Next Steps

1. **Immediate:** Share this response with Merck for review
2. **Phase 1:** Implement high-priority fixes (timezone, sample type, UNC path, custom field units, data source nesting) — estimated 5 hours
3. **Phase 2:** Implement medium-priority fixes (processed data, @index, dilution factor nesting) — estimated 6 hours
4. **Phase 3:** Validation enhancement (L3/L4 rules, level labels, confidence scores) — estimated 14 hours
5. **Ongoing:** Accept and integrate HarmonizingBaseTerms spreadsheet as converter configuration input
