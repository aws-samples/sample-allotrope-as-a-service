# ASM Transformation Service - Project Structure

## Overview

This is an **open-source, vendor-neutral** ASM transformation platform that any pharmaceutical or life sciences company can use.

## Core Services (Vendor-Neutral)

These services work with ANY instrument:

```
services/
├── ataas/                    # ASM Transformation as a Service (GENERIC)
├── dvaas/                    # Data Validation as a Service (GENERIC)
└── multi-instrument/         # Multi-Instrument Service (50+ instruments via allotropy)
```

**Key Point**: The core platform supports 50+ instruments out-of-the-box via the allotropy library and can be extended for any instrument.

## Example Converters (Reference Implementations)

These are **example implementations** showing how to add custom converters:

```
nova_flex2_converter.py       # Example: Nova BioProfile FLEX2 (solution analyzer)
merck_batch_processor.py      # Example: Batch processing workflow
asm_comparison_tool.py        # Generic: ASM comparison (vendor-neutral)
```

**Key Point**: The Nova FLEX2 converter is ONE example. You can create similar converters for YOUR instruments using the same pattern.

## Documentation

- **USER-GUIDE-OPEN-SOURCE.md** - Vendor-neutral guide for any company
- **USER-GUIDE.md** - Includes Merck examples (for reference)
- **ARCHITECTURE.md** - Technical architecture (vendor-neutral)
- **MEMORY.md** - Project history and decisions

## How to Use This for Your Company

### Option 1: Use Existing Support (50+ Instruments)

If your instrument is supported by allotropy:

```python
import requests

response = requests.post(
    'https://6uogqq4zb5.execute-api.us-east-1.amazonaws.com/prod/convert',
    json={
        'file_content': your_data,
        'vendor': 'YOUR_VENDOR',  # e.g., 'BECKMAN_VI_CELL_BLU'
        'instrument_type': 'auto'
    }
)
```

### Option 2: Create Custom Converter

If your instrument is NOT supported:

1. Copy `nova_flex2_converter.py` as a template
2. Modify for your instrument's CSV/JSON/XML format
3. Follow ASM schema for your technique
4. Test and validate
5. Deploy to your environment

**Example**:
```python
# your_company_converter.py
def convert_your_format_to_asm(file_content):
    # Parse your format
    # Map to ASM structure
    # Return ASM JSON
    pass
```

## Vendor-Specific Files (Examples Only)

```
merck/                        # Example customer data (DO NOT include in open source)
├── SampleResults*.csv        # Example input files
├── SampleResults*.json       # Example reference ASMs
└── solution-analyzer.schema.json  # ASM schema (generic, not Merck-specific)
```

**Important**: When publishing open source:
- ✅ Include: Core services, generic tools, documentation
- ✅ Include: Example converters (as templates)
- ❌ Exclude: Customer-specific data files
- ❌ Exclude: Customer names in code (use as examples in docs only)

## Architecture: Vendor-Neutral by Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Laboratory                          │
│  (Any Instrument, Any Vendor, Any Format)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Multi-Instrument Service                        │
│  • 50+ instruments via allotropy (vendor-neutral)           │
│  • Custom converters (your instruments)                     │
│  • AI-powered fallback (unknown formats)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   ATaaS + DVaaS                             │
│  • Conversion (vendor-neutral)                              │
│  • Validation (Allotrope standard)                          │
│  • Certification (industry standard)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Certified ASM Output                            │
│  • Standard format (Allotrope Foundation)                   │
│  • Vendor-neutral                                           │
│  • Regulatory compliant                                     │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles

1. **Vendor-Neutral Core**: All core services work with any instrument
2. **Extensible**: Easy to add converters for new instruments
3. **Standards-Based**: Uses Allotrope Foundation standards
4. **Open Source**: Community-driven development
5. **Examples Included**: Reference implementations for guidance

## For Open Source Release

### Include:
- ✅ All service code (ataas, dvaas, multi-instrument)
- ✅ Generic tools (comparison, validation)
- ✅ Example converters (as templates)
- ✅ Vendor-neutral documentation
- ✅ Architecture diagrams
- ✅ Deployment scripts (CDK)

### Exclude:
- ❌ Customer-specific data files
- ❌ Customer names in code
- ❌ Proprietary instrument formats (unless open)
- ❌ Internal credentials/keys

### Rename for Open Source:
- `nova_flex2_converter.py` → `examples/solution_analyzer_converter_example.py`
- `merck_batch_processor.py` → `examples/batch_processor_template.py`
- `merck/` → `examples/sample_data/` (with generic data)

## Summary

**This is a vendor-neutral, open-source platform.**

The Merck files are **examples** showing how one customer uses the system. Any pharmaceutical company can:
1. Use the platform as-is for 50+ supported instruments
2. Create custom converters for their specific instruments
3. Contribute back to the open-source community

The core architecture is designed to be universal and extensible.
