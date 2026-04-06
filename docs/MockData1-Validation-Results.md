# MockData1 Validation Test Results — Updated

**Date:** April 2, 2026
**Files Tested:** MockData1.csv, MockData1_1.json, MockData1_2.json
**Validator:** DVaaS (jsonschema-rs + Allotrope ASM schemas, 113 schemas loaded)
**Schema:** solution-analyzer.schema (REC/2025/12)

---

## Executive Summary

We ran both files through our validation pipeline. MockData1_2.json correctly failed with 3 schema errors. MockData1_1.json passed schema validation — which revealed an important finding about the scope of the official Allotrope JSON schemas.

The Allotrope JSON schemas are more permissive than expected. They define field types and structure but enforce very few required fields. Issues like missing `analyst`, value rounding, and empty strings are not caught by schema validation alone. This confirms that multiple validation layers are needed, which aligns with your 4-level validation approach.

---

## MockData1_2.json (Row 2) — INVALID

**3 schema errors detected.** Our Level 1 validation correctly flagged these:

| Error | Measurement | Root Cause |
|-------|-------------|------------|
| 1 | Blood gas (measurement[0]) | pCO2 unit is `"nmHg"` instead of `"mmHg"` — schema does not recognize this unit |
| 2 | Metabolite (measurement[3]) | glucose unit `"mg/L"` with value 4910 — schema expects `"g/L"` for mass concentration |
| 3 | Cell counter (measurement[4]) | `cell density dilution factor` missing `"unit"` field — has `{"value": 1.0}` without unit |

These are structural/type issues that the JSON schema correctly enforces.

---

## MockData1_1.json (Row 1) — VALID (Schema Passed)

**0 schema errors.** The file passes official Allotrope JSON schema validation.

### Why It Passed

We investigated the schema and found that the official Allotrope JSON schema (REC/2025/12) is permissive by design:

- `analyst` is defined as an **optional** property in the hierarchy schema — not in a `required` array
- Value precision (164.7 vs 165) is not enforced — the schema only checks that the value is a number
- Empty strings are valid strings in JSON Schema
- Extra characters in string values (e.g., "25099058--") pass string type validation

The schema validates **structure and types**, not **data quality or business rules**.

### Level 2 Issues We Identified (Manual Comparison)

By comparing MockData1.csv against MockData1_1.json field-by-field, we found 4 intentional data manipulations:

| # | Source Field | Source Value | ASM Value | Issue |
|---|-------------|-------------|-----------|-------|
| 1 | PO2 | 164.7 | 165 | Value rounded |
| 2 | O2 Saturation | 100 | 90 | Value changed |
| 3 | Chemistry Cartridge Lot Number | 25099058 | 25099058-- | Extra characters appended |
| 4 | Chemistry Card Lot Number | 25094029 | (empty string) | Value dropped entirely |

These would be caught by our Data Integrity Verification (field_mapping) when files go through our conversion pipeline.

---

## Validation Coverage Analysis

| Issue Type | Allotrope JSON Schema (Level 1) | Data Integrity Verification (Level 2) | Additional Rules Needed |
|-----------|--------------------------------|--------------------------------------|------------------------|
| Wrong unit string (nmHg) | ✅ Caught | ✅ Would catch | — |
| Invalid unit for field type (mg/L) | ✅ Caught | ✅ Would catch | — |
| Missing unit field | ✅ Caught | ✅ Would catch | — |
| Value rounding (164.7→165) | ❌ Not caught | ✅ Would catch | — |
| Value changed (100→90) | ❌ Not caught | ✅ Would catch | — |
| Extra characters in string | ❌ Not caught | ✅ Would catch | — |
| Value dropped to empty string | ❌ Not caught | ✅ Would catch | Could add non-empty string rule |
| Missing analyst field | ❌ Not caught (optional in schema) | N/A | Could add as required field rule |

---

## Gap Analysis: Schema vs Customer Expectations

Your email mentioned that MockData1_1.json includes intentional Level 1 schema issues. Our investigation found that the official Allotrope JSON schema does not enforce some of the rules your validation pipeline expects. This aligns with what you described in your review — your Level 1 validation includes both JSON schema validation AND ASM tag validation via your custom Python package.

### What the Allotrope JSON Schema Enforces
- Document structure (hierarchy, nesting)
- Required fields: `measurement identifier`, `measurement time` (within measurement documents)
- Field types (string, number, object, array)
- Detector schema conformance (which fields belong to which measurement type)
- `$asm.manifest` presence

### What the Allotrope JSON Schema Does NOT Enforce
- `analyst` as a required field (it's optional)
- Value precision or accuracy
- Non-empty string constraints
- Specific unit values beyond what detector schemas define
- Business rules (e.g., "all source values must be preserved")

### Our Plan to Close the Gap

Based on the validation workflow, mapping rules, traceability example, and building principles you shared, we are adding supplementary validation rules to DVaaS:

| Rule | Source | Priority | Status |
|------|--------|----------|--------|
| `$asm.type` attribute enforcement (e.g., dateTime, string) | Your validation workflow / sdc-asm-to-rdf | High | Planned |
| `$asm.pattern` attribute enforcement (e.g., "value datum" requires value + unit) | Your validation workflow / sdc-asm-to-rdf | High | Planned |
| Required `analyst` field | Building Principles | High | Planned |
| Non-empty string validation for custom fields | MockData1 test findings | High | Planned |
| Calculated data traceability nesting (per-calculation, not aggregate) | Traceability example | High | In progress |
| Every source term must be mapped (no silent drops) | Mapping rules | High | Implemented (field_mapping) |
| Unit validation against Allotrope ontology | Building Principles | Medium | Planned |
| HarmonizingBaseTerms integration | Reference Excel | Medium | Planned |
| Configurable Allotrope rules (Level 3) vs org-specific rules (Level 4) | Mapping email | Medium | Planned |
| Validation level labels (L1/L2/L3/L4) on findings | Your validation workflow | Medium | Planned |

These rules will be tagged with validation levels (L1/L2/L3/L4) in the output so reviewers can prioritize findings by level.

---

## Timezone Verification

Source CSV: `2/7/2025 10:35` (MST, UTC-7)
ASM files: `2025-02-07T17:35:00+00:00` (UTC)
Offset: 10:35 + 7 hours = 17:35 ✅ Correct

Your converter (zontal-nova-flex v1.2.dev0) handles the MST→UTC conversion correctly. Our instrument config supports `"timezone": "America/Denver"` for this purpose.

---

## Timestamp and Date Format Analysis

The customer noted that Flex2 timestamps are in MST (UTC-7). We identified several date-related observations:

| Aspect | Row 1 | Row 2 | Notes |
|--------|-------|-------|-------|
| Source timestamp | `2/7/2025 10:35` | `2/7/2025 10:35:00.123` | Row 1 missing seconds; Row 2 has milliseconds |
| ASM timestamp | `2025-02-07T17:35:00+00:00` | `2025-02-07T17:35:00.123+00:00` | Both correctly offset by +7 hours (MST to UTC) |
| Seconds handling | Assumed `:00` | Preserved `.123` | Converter fills missing seconds with zero |
| Date interpretation | February 7 (US format) | February 7 (US format) | Ambiguous without timezone context — could be July 2 in European format |

**Key observations:**

1. **Timezone conversion is correct** — 10:35 MST + 7 hours = 17:35 UTC. The customer's converter (zontal-nova-flex v1.2.dev0) handles this correctly.

2. **Date format ambiguity** — `2/7/2025` is M/D/YYYY (US) or D/M/YYYY (European). Without timezone or locale context, this is ambiguous. This is the [META] issue from your review — the mount path provides geographic context that resolves this ambiguity. Our instrument config supports `"timezone": "America/Denver"` for this purpose.

3. **Millisecond precision in Row 2** — The source has `10:35:00.123` which is unusual for this instrument. The ASM correctly preserves the milliseconds. This may be an intentional test of precision handling.

4. **Missing seconds in Row 1** — The source has `10:35` without seconds. The converter assumes `:00`. A Level 2 comparison should note this inference rather than treating it as an exact match.

---

## Recommendations

1. **We are reviewing the materials you shared** — Thank you for providing the validation workflow, mapping rules, traceability example (`tracebility-data-source-example.json`), HarmonizingBaseTerms Excel, and the ASM Building Principles document. We are also reviewing your `$asm` tag validation approach referenced in your validation workflow (`sdc-asm-to-rdf`). We will use these to add supplementary validation rules to DVaaS that go beyond the base JSON schema — specifically the `$asm.type`, `$asm.pattern`, and `$asm.property-class` attribute enforcement that your Python package performs.

2. **Calculated data traceability** — Your traceability example confirms the pattern we should follow: `data source aggregate document` nested inside each `calculated data document`, not at the aggregate level. We are updating our converter to match this pattern.

3. **Two-layer validation rules** — We agree with your approach of separating Allotrope-approved rules (Level 3) from organization-specific rules (Level 4). We will implement both as configurable rule sets in DVaaS, so the validation output clearly labels which level each finding belongs to.

4. **Every source term must be mapped** — Per your mapping guidance, our converters already follow this principle for the Nova FLEX2 (all 40 CSV columns mapped). Our Custom Converter Requirements document mandates this for all customer-built converters as well.

5. **Test Level 2 via conversion pipeline** — Upload MockData1.csv through our "Convert Instrument File" tab to see the Data Integrity Verification in action. The field_mapping will flag every value-level discrepancy that schema validation cannot catch.

6. **HarmonizingBaseTerms integration** — We will review the Excel file you provided and incorporate the standardized terms as converter configuration input. This ensures consistent terminology across all instrument converters.
