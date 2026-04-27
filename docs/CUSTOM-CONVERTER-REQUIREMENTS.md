# Custom Converter Requirements

## Purpose

This document defines the requirements for building custom converters that integrate with the ASM Transformation Service. Any converter submitted for registration must comply with these requirements to ensure data integrity verification, regulatory traceability, and system compatibility.

## 1. Function Signature

### Required

```python
def convert(file_content):
    """
    Convert instrument file content to Allotrope Simple Model (ASM) JSON.

    Args:
        file_content (str): Raw file content as a string.

    Returns:
        dict: {
            "success": True/False,
            "asm_output": { ... },          # ASM JSON (required on success)
            "field_mapping": [ ... ],        # Data integrity mappings (required)
            "error": "message"               # Error message (required on failure)
        }
    """
```

### Rules

- Function name must be `convert`
- Must accept a single `file_content` string parameter (not a file path)
- Must return a dict with `success`, `asm_output`, and `field_mapping` keys
- Must not read from or write to the filesystem
- Must not make network calls
- Must not use `eval()`, `exec()`, `os.system()`, `subprocess`, or `__import__`

### Do NOT use CLI-style signatures

```python
# ❌ WRONG — file path based
def convert(input_path, output_path):
    text = Path(input_path).read_text()
    Path(output_path).write_text(result)

# ✅ CORRECT — content based
def convert(file_content):
    return {"success": True, "asm_output": asm, "field_mapping": mappings}
```

## 2. Return Format

### On Success

```python
{
    "success": True,
    "asm_output": { ... },       # Complete ASM JSON document
    "field_mapping": [ ... ]     # Array of source-to-ASM field mappings
}
```

### On Failure

```python
{
    "success": False,
    "error": "Human-readable error message describing what went wrong"
}
```

## 3. Field Mapping (Required)

The `field_mapping` array is what powers the Data Integrity Verification report. It proves that every source value was preserved exactly in the ASM output. **Every value from the source file must have a corresponding entry.**

### Entry Format

```python
{
    "source_field": "pH",              # Column name or field name in source file
    "source_value": 7.183,             # Exact value from source file
    "asm_field": "pH",                 # Field name in ASM output
    "asm_value": 7.183,                # Exact value written to ASM
    "unit": "pH"                       # Unit of measurement (empty string if unitless)
}
```

### Rules

- `source_value` and `asm_value` must be identical — no rounding, no transformation
- Include entries for ALL values: measurements, metadata, calculated data, custom info
- String values are valid (e.g., lot numbers, operator names, sample IDs)
- Use empty string `""` for unit when not applicable
- Only omit fields that are used structurally (e.g., timestamp used as `measurement time`, sample ID used as `sample identifier`) — these are already visible in the ASM structure

### Numeric Example

```python
field_mapping.append({
    "source_field": "PO2",
    "source_value": 94.5,
    "asm_field": "pO2",
    "asm_value": 94.5,
    "unit": "mmHg"
})
```

### String Example

```python
field_mapping.append({
    "source_field": "Gas Cartridge Lot Number",
    "source_value": "25175029",
    "asm_field": "Gas Cartridge Lot Number (custom info)",
    "asm_value": "25175029",
    "unit": ""
})
```

### Calculated Value Example

```python
field_mapping.append({
    "source_field": "pH @ Temp",
    "source_value": 7.189,
    "asm_field": "temperature corrected pH (calculated)",
    "asm_value": 7.189,
    "unit": "pH"
})
```

## 4. ASM Output Structure

The `asm_output` must follow the Allotrope Simple Model schema for the relevant instrument type.

### Required Elements

| Element | Description |
|---------|-------------|
| `$asm.manifest` | Allotrope manifest URL for the instrument type |
| Aggregate document | Top-level document (e.g., `solution analyzer aggregate document`) |
| `data system document` | Converter name, version, timestamp, file identifier |
| `device system document` | Device identifier, manufacturer, device type |
| `measurement document` | Array of measurements with UUIDs and ISO 8601 timestamps |
| `sample document` | Sample identifier and description per measurement |

### Measurement Identifiers

Use UUID v4 for all identifiers:

```python
import uuid
measurement_id = str(uuid.uuid4())
```

### Timestamps

Use ISO 8601 with timezone:

```python
from datetime import datetime, timezone
iso_timestamp = dt.replace(tzinfo=timezone.utc).isoformat()
# Example: "2025-11-01T04:46:26+00:00"
```

### Calculated Data Traceability

If the source file contains calculated values (e.g., temperature-corrected pH), include a `calculated data aggregate document` that links each calculated value back to its source measurement by `measurement identifier`.

### Custom Information

Instrument metadata that doesn't fit standard ASM fields (lot numbers, flow times, dilution ratios, etc.) goes in `custom information aggregate document`.

## 5. Complete Example

```python
import csv
import io
import uuid
from datetime import datetime, timezone


def convert(file_content):
    try:
        reader = csv.DictReader(io.StringIO(file_content))
        rows = list(reader)

        if not rows:
            return {"success": False, "error": "No data rows found"}

        row = rows[0]
        field_mapping = []
        measurements = []

        # Parse a measurement value
        absorbance = float(row.get("Absorbance", "0"))
        well = row.get("Well", "A1")

        m_id = str(uuid.uuid4())
        measurements.append({
            "measurement identifier": m_id,
            "measurement time": datetime.now(timezone.utc).isoformat(),
            "absorbance": {"value": absorbance, "unit": "mAU"},
            "sample document": {
                "sample identifier": well,
                "location identifier": well
            }
        })

        field_mapping.append({
            "source_field": "Absorbance",
            "source_value": absorbance,
            "asm_field": "absorbance",
            "asm_value": absorbance,
            "unit": "mAU"
        })

        # Parse a metadata value
        lot = row.get("Cartridge Lot", "").strip()
        custom_info = []
        if lot:
            custom_info.append({"datum label": "Cartridge Lot", "scalar string datum": lot})
            field_mapping.append({
                "source_field": "Cartridge Lot",
                "source_value": lot,
                "asm_field": "Cartridge Lot (custom info)",
                "asm_value": lot,
                "unit": ""
            })

        asm = {
            "$asm.manifest": "http://purl.allotrope.org/manifests/plate-reader/REC/2025/12/plate-reader.manifest",
            "plate reader aggregate document": {
                "plate reader document": [{
                    "device system document": {
                        "device identifier": "READER-001",
                        "product manufacturer": "Agilent",
                        "device document": [{"device type": "plate reader"}]
                    },
                    "measurement aggregate document": {
                        "measurement document": measurements
                    }
                }]
            }
        }

        if custom_info:
            asm["plate reader aggregate document"]["plate reader document"][0][
                "measurement aggregate document"
            ]["custom information aggregate document"] = {
                "custom information document": custom_info
            }

        return {"success": True, "asm_output": asm, "field_mapping": field_mapping}

    except Exception as e:
        return {"success": False, "error": str(e)}
```

## 6. How the Service Executes Your Converter

Understanding how the service runs your code helps you write converters correctly.

### Execution Model

Your converter file is **not imported as a Python module** and **not run as a standalone script**. Instead, the Custom Converter Service Lambda:

1. Downloads your `.py` file from S3
2. Executes the entire file using `exec()` into an isolated namespace
3. Looks for a function named `convert` in that namespace
4. Calls `convert(file_content)` with the raw instrument file content
5. Returns whatever your function returns

This means:

- **Your `convert` function is the only entry point** — the service calls it directly
- **Top-level code runs during `exec()`** — imports, constants, helper functions are all fine
- **`if __name__ == '__main__'` blocks do NOT run** — `exec()` does not set `__name__` to `'__main__'`, so these blocks are safely skipped

### Can I Include a `__main__` Block?

**Yes.** Including a `__main__` block for local testing is perfectly fine and encouraged:

```python
import csv
import io
import uuid
from datetime import datetime, timezone

def convert(file_content):
    # ... your converter logic ...
    return {"success": True, "asm_output": asm, "field_mapping": mappings}

# This block runs ONLY when you execute the file locally for testing.
# The service ignores it completely.
if __name__ == '__main__':
    import json
    with open('sample_data.csv', 'r') as f:
        result = convert(f.read())
    print(json.dumps(result, indent=2))
    with open('output.json', 'w') as f:
        json.dump(result['asm_output'], f, indent=2)
```

The `__main__` block lets you test locally with file I/O, but the service never executes it. The security checks (no `open()`, no `Path()`) apply to the `convert` function and top-level code — not to the `__main__` block.

### What Runs vs What Doesn't

| Code | Runs in Service? | Runs Locally? |
|------|-----------------|---------------|
| `import csv, uuid, ...` | Yes (during exec) | Yes |
| Helper functions | Yes (during exec) | Yes |
| Top-level constants | Yes (during exec) | Yes |
| `def convert(file_content)` | Yes (called by service) | Yes (called by main) |
| `if __name__ == '__main__'` | **No** (skipped) | Yes |

## 7. Registration

### Via Dashboard (Recommended)

Go to the **Converter Management** tab → **Register New Converter** → fill in vendor, model, instrument type → upload your `.py` file. The converter ID is auto-generated from vendor + model (e.g., `novabio-flex2-v1`). If a converter already exists for that vendor+model, the version auto-increments (`v2`, `v3`, etc.).

### Via API

```
POST /register (Custom Converter API)
```

```json
{
    "converter_id": "agilent-gen5-v1",
    "converter_code": "def convert(file_content): ...",
    "vendor": "AGILENT_GEN5",
    "model": "Gen5 Plate Reader",
    "instrument_type": "plate_reader",
    "description": "Converts Agilent Gen5 TXT export to ASM plate reader format"
}
```

Endpoint URL is in `dashboard/src/config.js` after deployment.

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `converter_id` | Yes | Auto-generated by dashboard, or provide manually via API |
| `converter_code` | Yes | Full Python source code as a string |
| `vendor` | Yes | Vendor identifier (UPPERCASE_WITH_UNDERSCORES) |
| `model` | Yes | Instrument model name |
| `instrument_type` | Yes | One of: `solution_analyzer`, `cell_counter`, `plate_reader`, `spectrophotometer`, `qpcr`, `dpcr`, `chromatography`, `endotoxin_testing`, `electrophoresis`, `light_obscuration` |
| `description` | No | Human-readable description of what the converter does |

### Converter ID Convention

Auto-generated: `{vendor}-{model}-v{version}` (lowercased, special chars replaced with hyphens)

```
Examples:
  novabio-flex2-v1          (first converter for Nova FLEX2)
  novabio-flex2-v2          (second converter — different output format)
  agilent-gen5-v1
  beckman-vicell-blu-v1
```

## 8. Approval

Converters must be approved before they can be used in production.

### Via Dashboard (Recommended)

Go to **Converter Management** tab → click **Review** on a PENDING converter → enter your email → **Approve** or **Reject** with comments.

### Via API

```
POST /approve (Custom Converter API)
```

```json
{
    "converter_id": "agilent-gen5-v1",
    "status": "APPROVED",
    "approved_by": "reviewer@company.com",
    "comments": "Code reviewed, ASM output validated, field_mapping complete"
}
```

To reject, set `"status": "REJECTED"` with comments explaining why.

## 9. Conversion

Once approved, converters are automatically used by the Unified Converter when the instrument config matches.

### Via Dashboard

Go to **Convert Instrument File** tab → upload instrument file + instrument config JSON → click **Convert to ASM & Validate**.

### Via API

```
POST /convert (Unified Converter API)
```

```json
{
    "file_content": "<raw instrument file content>",
    "file_name": "experiment_data.txt",
    "manifest": {
        "vendor": "AGILENT_GEN5",
        "model": "Gen5 Plate Reader",
        "instrument_type": "plate_reader",
        "file_format": "txt",
        "serial_number": "GEN5-2024-001",
        "software_version": "3.12"
    }
}
```

Endpoint URL is in `dashboard/src/config.js` after deployment.

### Routing Priority

The Unified Converter routes requests in this order:

1. **Explicit converter_id** — if specified in the instrument config
2. **Custom Converter Registry** — if an approved converter matches the vendor + model
3. **Embedded Custom Converters** — built-in converters (e.g., Nova FLEX2)
4. **Multi-Instrument Service** — 31 instruments via allotropy library
5. **ATaaS (AI)** — Bedrock Claude fallback for unknown formats

## 10. Validation Checklist

Before submitting a converter for registration, verify:

- [ ] Function is named `convert` and accepts `file_content` string
- [ ] Returns `{"success": True, "asm_output": ..., "field_mapping": ...}` on success
- [ ] Returns `{"success": False, "error": "..."}` on failure
- [ ] `field_mapping` covers every value from the source file
- [ ] `source_value` equals `asm_value` for every mapping entry (no rounding)
- [ ] ASM output includes `$asm.manifest` with correct instrument type URL
- [ ] Measurement identifiers are UUID v4
- [ ] Timestamps are ISO 8601 with timezone
- [ ] No filesystem access (`open()`, `Path()`, `os.path`)
- [ ] No network calls (`requests`, `urllib`, `socket`)
- [ ] No dangerous functions (`eval`, `exec`, `os.system`, `subprocess`, `__import__`)
- [ ] Handles empty or malformed input gracefully (returns error, does not crash)
- [ ] Tested with at least one real instrument file

## 11. Support

For questions about converter development or the registration process, contact the ASM Transformation Service team.
