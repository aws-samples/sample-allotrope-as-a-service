# DVaaS Validation Update — Standards-Based ASM Schema Validation

## Summary

Based on your feedback, we have replaced our previous heuristic-based ASM validator with a standards-compliant implementation that uses the official Allotrope JSON schemas and a compliant JSON Schema validator. This update is live in production.

## What Changed

Our DVaaS validation service now implements a three-layer validation approach:

**Layer 1 — JSON Schema Validation (Allotrope Standard Schemas)**
- Uses [jsonschema-rs](https://pypi.org/project/jsonschema-rs/) (Rust-based, JSON Schema draft 2020-12 compliant) to validate ASM files against the official Allotrope JSON schemas published at https://gitlab.com/allotrope-public/asm
- The `$asm.manifest` URI in each ASM file is resolved to the correct technique-specific schema automatically
- 113 schemas loaded (latest REC version per technique), covering all published Allotrope technique types
- Full `$ref` resolution across schema files, including core hierarchy, technique-specific, and QUDT unit schemas

**Layer 2 — `$asm`-Prefixed Attribute Validation**
- Unit symbols are validated against the QUDT unit schema (772 unit definitions) via `$ref` resolution from each technique schema — enforced as `const` constraints per field
- Ontology terms (sample role types, container types, statistical features, regression features) are validated against the `enum` values defined in the Allotrope schemas
- Additional checks for ontology term values not covered by schema `enum` constraints

**Layer 3 — Supplementary Checks**
- Calculated data traceability: verifies `data source aggregate document` is present when `calculated data document` exists
- Naming convention checks: flags hyphenated field names (ASM standard uses space-separated names)
- Measurement identifier completeness

## Validation Examples

**Schema-enforced unit validation:**
A `plate well count` field with an incorrect unit returns:
```
ERROR: [plate reader aggregate document/.../plate well count/unit] "#" was expected
```

**Schema-enforced required fields:**
A measurement document missing required properties returns:
```
ERROR: [.../measurement aggregate document] "measurement time" is a required property
ERROR: [.../measurement aggregate document] "plate well count" is a required property
ERROR: [.../measurement document/0] "measurement identifier" is a required property
```

**Schema-enforced ontology terms:**
A `sample role type` with an invalid value is caught by the schema's `enum` constraint, which is sourced from the Allotrope role ontology.

## Technical Details

| Component | Detail |
|---|---|
| Schema validator | jsonschema-rs 0.45.0 (Rust-based) |
| JSON Schema draft | 2020-12 |
| Schema source | https://gitlab.com/allotrope-public/asm (public, CC BY-NC 4.0) |
| Schema version | Latest REC per technique (as of March 2026) |
| QUDT units | 772 unit definitions with `const` enforcement |
| Techniques covered | 60+ (all published Allotrope ADM technique schemas) |
| Runtime | AWS Lambda, Python 3.12 |

## API Response

The validation response now includes:

```json
{
  "valid": true,
  "validator": "allotrope-schema-jsonschema-rs",
  "metrics": {
    "schema_id": "http://purl.allotrope.org/json-schemas/adm/plate-reader/REC/2025/12/plate-reader.schema",
    "schema_errors": 0,
    "schemas_loaded": 113,
    "measurement_count": 1,
    "technique": "plate reader",
    "has_calculated_data": false,
    "has_data_source_traceability": false
  }
}
```

## Endpoint

No changes to the API contract. The existing endpoint continues to work as before:

```
POST https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate
```

The dashboard Validate ASM tab at https://d2630v5zyoh8t7.cloudfront.net has been updated to display schema validation details.

## Next Steps

We welcome your feedback on this implementation. Specific areas where your input would be valuable:

- Are there specific `$asm`-prefixed attribute validations beyond unit symbols and ontology terms that your team performs?
- Should we support validation against older schema versions (we currently validate against the latest REC)?
- Are there additional supplementary checks that would be useful for your workflows?
