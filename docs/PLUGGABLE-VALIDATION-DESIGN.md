# Pluggable Validation Framework — Design Document

**Date:** April 2, 2026
**Author:** AWS ASM Transformation Service Team
**Status:** Draft for internal alignment and customer review

---

## Problem Statement

The ASM Transformation Service is intended for open-source release and broad industry adoption. However, different organizations have different validation requirements beyond the Allotrope JSON schema standard:

- **Allotrope Foundation** defines the JSON schema (structure and types)
- **Individual organizations** add rules on top (required fields, unit ontologies, naming conventions, business rules)
- **Hardcoding any organization's rules into the core service makes it non-portable**

We need a validation architecture that is standards-based at the core but extensible for any organization's specific requirements.

---

## Design Principles

1. **Core is universal** — ships with Allotrope JSON schema validation that works for everyone
2. **Extensions are pluggable** — organizations add their own rules without modifying service code
3. **Rules are data, not code** — validation rules are JSON configuration files, not Python scripts
4. **Findings are labeled** — every validation finding identifies which rule set caught it
5. **Rule sets are shareable** — organizations can publish and share rule sets
6. **Backward compatible** — existing validation behavior unchanged; plugins are additive

---

## Architecture

```
ASM File
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                    DVaaS Validation Engine                │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  CORE (ships with service)                         │  │
│  │                                                    │  │
│  │  Layer 1: JSON Schema Validation                   │  │
│  │  • jsonschema-rs + official Allotrope schemas      │  │
│  │  • Structure, types, required fields               │  │
│  │  • Detector schema conformance                     │  │
│  │                                                    │  │
│  │  Layer 2: Data Integrity Verification              │  │
│  │  • field_mapping comparison (source vs ASM)        │  │
│  │  • Value-level accuracy proof                      │  │
│  │                                                    │  │
│  │  Layer 3: Built-in Supplementary Checks            │  │
│  │  • Calculated data traceability                    │  │
│  │  • Measurement identifier presence                 │  │
│  │  • Naming convention checks (spaces not hyphens)   │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  PLUGINS (customer-provided, loaded at runtime)    │  │
│  │                                                    │  │
│  │  Rule Set: "allotrope-asm-tags-v1"                 │  │
│  │  • $asm.pattern enforcement                        │  │
│  │  • $asm.type enforcement                           │  │
│  │  • Unit validation against QUDT ontology           │  │
│  │  • (Could become core if Allotrope standardizes)   │  │
│  │                                                    │  │
│  │  Rule Set: "merck-level-3-v1"                      │  │
│  │  • Required analyst field                          │  │
│  │  • Non-empty string validation                     │  │
│  │  • HarmonizingBaseTerms compliance                 │  │
│  │  • Custom field 1:1 transfer rules                 │  │
│  │                                                    │  │
│  │  Rule Set: "merck-level-4-v1"                      │  │
│  │  • Organization-specific naming conventions        │  │
│  │  • Site-specific metadata requirements             │  │
│  │  • Instrument-specific field requirements          │  │
│  │                                                    │  │
│  │  Rule Set: "<any-org>-<any-rules>-v<n>"            │  │
│  │  • Any organization can create and upload          │  │
│  │  • Shared across the organization's deployments    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  OUTPUT                                            │  │
│  │                                                    │  │
│  │  Each finding tagged with:                         │  │
│  │  • rule_set: which rule set caught it              │  │
│  │  • rule_id: specific rule within the set           │  │
│  │  • severity: error / warning / info                │  │
│  │  • level: L1 / L2 / L3 / L4 / custom              │  │
│  │  • message: human-readable description             │  │
│  │  • path: JSON path to the issue in the ASM         │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Rule Set Format

A rule set is a JSON file that defines a collection of validation checks. The rule engine evaluates each check against the ASM file.

### Rule Set Structure

```json
{
    "rule_set_id": "merck-level-3-v1",
    "name": "Merck ASM Building Principles (Level 3)",
    "version": "1.0",
    "description": "Allotrope-aligned building principles for ASM files",
    "author": "Merck Research Labs",
    "level": "L3",
    "rules": [ ... ]
}
```

### Supported Check Types

| Check Type | Description | Example Use |
|-----------|-------------|-------------|
| `field_required` | A field must exist at the specified path | `analyst` must be present |
| `field_not_empty` | A string field must not be empty | Custom field values must have content |
| `value_in_list` | A value must be in an allowed list | Unit must be a valid QUDT symbol |
| `value_not_in_list` | A value must NOT be in a blocked list | Reject known invalid terms |
| `value_matches_pattern` | A value must match a regex pattern | UUID format, ISO 8601 timestamps |
| `field_type` | A value must be a specific JSON type | Numeric fields must be numbers |
| `path_exists` | A JSON path must exist in the document | `$asm.manifest` must be present |
| `conditional_required` | A field is required IF another field exists | `data source aggregate document` required if `calculated data document` exists |
| `count_min` | An array must have at least N items | `measurement document` must have ≥ 1 item |
| `value_equals` | A field must have a specific value | `device type` must be "solution analyzer" |
| `custom_script` | Run a Python function for complex logic | Advanced validation beyond declarative rules |

### Rule Examples

**Required field:**
```json
{
    "rule_id": "required-analyst",
    "check": "field_required",
    "path": "**.solution analyzer document[*]",
    "field": "analyst",
    "severity": "error",
    "message": "The 'analyst' field is required in each solution analyzer document"
}
```

**Non-empty string:**
```json
{
    "rule_id": "non-empty-custom-strings",
    "check": "field_not_empty",
    "path": "**.custom information document[*].scalar string datum",
    "severity": "error",
    "message": "Custom field string values must not be empty"
}
```

**Unit validation:**
```json
{
    "rule_id": "valid-units",
    "check": "value_in_list",
    "path": "**.unit",
    "list_source": "qudt-unit-symbols.json",
    "severity": "error",
    "message": "Unit '{value}' is not a recognized QUDT unit symbol"
}
```

**Conditional requirement:**
```json
{
    "rule_id": "traceability-required",
    "check": "conditional_required",
    "if_path": "**.calculated data document",
    "then_path": "**.data source aggregate document",
    "severity": "error",
    "message": "Calculated data must include data source traceability"
}
```

**Regex pattern:**
```json
{
    "rule_id": "uuid-measurement-ids",
    "check": "value_matches_pattern",
    "path": "**.measurement identifier",
    "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    "severity": "warning",
    "message": "Measurement identifiers should be UUID v4 format"
}
```

**Custom script (for complex logic):**
```json
{
    "rule_id": "asm-pattern-enforcement",
    "check": "custom_script",
    "script": "validate_asm_patterns.py",
    "severity": "error",
    "message": "ASM pattern validation failed"
}
```

---

## Rule Set Management

### Storage

Rule sets are stored in S3 alongside custom converters:

```
s3://custom-converters-{account}-{region}/
├── converters/           # Custom converter code
│   ├── nova-flex2-v1.py
│   └── agilent-gen5-v1.py
├── rule-sets/            # Validation rule sets
│   ├── allotrope-asm-tags-v1.json
│   ├── merck-level-3-v1.json
│   ├── merck-level-4-v1.json
│   └── qudt-unit-symbols.json    # Reference data for value_in_list checks
└── reference-data/       # Shared reference data
    ├── qudt-unit-symbols.json
    └── allotrope-vocabulary.json
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rule-sets/register` | Upload a new rule set |
| GET | `/rule-sets/list` | List all registered rule sets |
| GET | `/rule-sets/{id}` | Get a specific rule set |
| DELETE | `/rule-sets/{id}` | Remove a rule set |

### Dashboard Integration

The **Converter Management** tab gets a new section: "Validation Rule Sets"
- Browse registered rule sets
- Upload new rule sets (JSON file)
- Enable/disable rule sets per validation request
- View rule set details and individual rules

The **Validate ASM File** tab gets a rule set selector:
- Multi-select dropdown: choose which rule sets to apply
- Default: Core only (JSON schema + supplementary)
- Optional: Add any registered plugin rule sets

### Validation Request (Updated)

```json
{
    "asm_data": { ... },
    "validation_level": "comprehensive",
    "rule_sets": ["allotrope-asm-tags-v1", "merck-level-3-v1"],
    "generate_report": true,
    "file_name": "my_asm_file.json"
}
```

If `rule_sets` is omitted, only core validation runs (backward compatible).

### Validation Response (Updated)

```json
{
    "valid": false,
    "errors": [
        {
            "rule_set": "core",
            "rule_id": "schema-validation",
            "level": "L1",
            "severity": "error",
            "path": "solution analyzer document/0/measurement document/0",
            "message": "pCO2 unit 'nmHg' is not valid"
        },
        {
            "rule_set": "merck-level-3-v1",
            "rule_id": "required-analyst",
            "level": "L3",
            "severity": "error",
            "path": "solution analyzer document/0",
            "message": "The 'analyst' field is required"
        }
    ],
    "warnings": [ ... ],
    "rule_sets_applied": ["core", "allotrope-asm-tags-v1", "merck-level-3-v1"],
    "metrics": { ... }
}
```

---

## Migration Path

### Phase 1: Framework (Estimated: 2 weeks)
- Build rule engine in DVaaS that evaluates JSON rule sets
- Support check types: `field_required`, `field_not_empty`, `value_in_list`, `value_matches_pattern`, `conditional_required`
- Add S3 storage for rule sets
- Add API endpoints for rule set management
- Update validation request/response format (backward compatible)

### Phase 2: Default Rule Sets (Estimated: 1 week)
- Create `allotrope-asm-tags-v1` rule set from `$asm` attribute analysis
- Create `qudt-unit-symbols.json` reference data from QUDT ontology
- Ship these as default rule sets (installed on deployment)

### Phase 3: Customer Rule Sets (Estimated: 1 week)
- Work with customer to create their Level 3 and Level 4 rule sets
- Translate their ASM Building Principles v33 into declarative rules
- Translate their HarmonizingBaseTerms into reference data
- Test against their MockData files

### Phase 4: Dashboard Integration (Estimated: 1 week)
- Add rule set management to Converter Management tab
- Add rule set selector to Validate ASM File tab
- Update validation results display to show rule set labels
- Update PDF report to include rule set information

### Phase 5: Advanced (Future)
- `custom_script` check type for complex validation logic
- Rule set versioning and deprecation
- Rule set marketplace (organizations share rule sets)
- AI-assisted rule generation from design principles documents

---

## How This Addresses the Customer's Needs

| Customer Need | How Pluggable Framework Addresses It |
|--------------|--------------------------------------|
| Level 1: JSON Schema + $asm tags | Core (schema) + Plugin (`allotrope-asm-tags-v1`) |
| Level 2: Field-to-field comparison | Core (Data Integrity Verification) |
| Level 3: Allotrope building principles | Plugin (`allotrope-principles-v1`) |
| Level 4: Merck-specific rules | Plugin (`merck-level-4-v1`) |
| Two layers of rules (Allotrope vs org-specific) | Separate rule sets, clearly labeled |
| AI learning principles | Future: AI generates rule sets from documents |
| Validation level labels on findings | Each finding tagged with rule_set and level |
| Configurable per organization | Each org uploads their own rule sets |

---

## Open Source Benefits

| Benefit | How |
|---------|-----|
| Universal core | JSON schema validation works for any ASM file |
| No vendor lock-in | Rule sets are JSON files, not proprietary code |
| Community contributions | Organizations can publish rule sets for others to use |
| Standards evolution | When Allotrope standardizes rules, they move from plugin to core |
| Adoption friendly | New users get value immediately; advanced users add plugins |

---

## Example: Customer Onboarding Flow

```
1. Customer deploys ASM Transformation Service
   └── Core validation works immediately (JSON schema)

2. Customer downloads Allotrope $asm tag rule set (published by us)
   └── Uploads via dashboard or API
   └── Now catches $asm.pattern, $asm.type, unit validation

3. Customer creates their own Level 3/4 rule sets
   └── Translates their building principles into JSON rules
   └── Uploads via dashboard or API
   └── Validation now matches their internal standards

4. Customer shares rule sets across their organization
   └── Same rule sets deployed to all their AWS accounts
   └── Consistent validation across all sites/labs
```

---

## Questions for Discussion

1. Should the `allotrope-asm-tags-v1` rule set ship as a default (always applied) or as an opt-in plugin?
2. Should `custom_script` check type be supported in Phase 1, or deferred to Phase 5?
3. Should rule sets have an approval workflow like custom converters?
4. Should we support rule set inheritance (e.g., Level 4 extends Level 3)?
5. How should rule set versioning work when Allotrope updates their schemas?
