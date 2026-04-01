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

## 6. Registration API

### Endpoint

```
POST https://tfv79s08rl.execute-api.us-east-1.amazonaws.com/prod/register
```

### Request Body

```json
{
    "converter_id": "agilent-gen5-v1",
    "converter_code": "def convert(file_content): ...",
    "vendor": "AGILENT_GEN5",
    "model": "Gen5 Plate Reader",
    "instrument_type": "plate_reader",
    "description": "Converts Agilent Gen5 TXT export to ASM plate reader format",
    "filename": "convert_agilent_gen5.py"
}
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `converter_id` | Yes | Unique identifier (lowercase, hyphens, with version suffix) |
| `converter_code` | Yes | Full Python source code as a string |
| `vendor` | Yes | Vendor identifier (UPPERCASE_WITH_UNDERSCORES) |
| `model` | Yes | Instrument model name |
| `instrument_type` | Yes | One of: `solution_analyzer`, `cell_counter`, `plate_reader`, `spectrophotometer`, `qpcr`, `dpcr`, `chromatography`, `endotoxin_testing` |
| `description` | No | Human-readable description of what the converter does |
| `filename` | No | Original filename for reference |

### Response

```json
{
    "converter_id": "agilent-gen5-v1",
    "status": "PENDING",
    "s3_location": "converters/agilent-gen5-v1.py"
}
```

### Converter ID Convention

```
{vendor}-{model}-v{version}

Examples:
  nova-flex2-v1
  agilent-gen5-v1
  beckman-vicell-blu-v1
  charlesriver-endoscan-v1
```

## 7. Approval API

Converters must be approved before they can be used in production.

### Approve

```
POST https://tfv79s08rl.execute-api.us-east-1.amazonaws.com/prod/approve
```

```json
{
    "converter_id": "agilent-gen5-v1",
    "status": "APPROVED",
    "approved_by": "reviewer@company.com",
    "comments": "Code reviewed, ASM output validated, field_mapping complete"
}
```

### Reject

```
POST https://tfv79s08rl.execute-api.us-east-1.amazonaws.com/prod/approve
```

```json
{
    "converter_id": "agilent-gen5-v1",
    "status": "REJECTED",
    "approved_by": "reviewer@company.com",
    "comments": "Missing field_mapping for lot number columns"
}
```

## 8. Conversion API

Once approved, converters are automatically used by the Unified Converter when the manifest matches.

### Endpoint

```
POST https://tqzatn5bse.execute-api.us-east-1.amazonaws.com/prod/convert
```

### Request Body

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

### Response

```json
{
    "conversion_id": "UNIFIED-20260316120000",
    "timestamp": "2026-03-16T12:00:00",
    "method": "custom-converter",
    "converter_used": "agilent-gen5-v1",
    "asm_output": { ... },
    "field_mapping": [ ... ],
    "status": "success",
    "message": "Converted using custom converter"
}
```

### Routing Priority

The Unified Converter routes requests in this order:

1. **Custom Converter Registry** — if an approved converter matches the manifest vendor + model
2. **Embedded Custom Converters** — built-in converters (e.g., Nova FLEX2)
3. **Multi-Instrument Service** — 31 instruments via allotropy library
4. **ATaaS (AI)** — Bedrock Claude fallback for simple unknown formats

## 9. Validation Checklist

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

## 10. Support

For questions about converter development or the registration process, contact the ASM Transformation Service team.
