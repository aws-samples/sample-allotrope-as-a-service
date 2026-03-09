# Instrument Manifest Schema

## Overview

The manifest file provides metadata about the instrument that generated the data file. This ensures 100% accurate conversion to ASM format.

**Important**: One manifest file per instrument. Reuse the same manifest for all data files from that instrument.

---

## Manifest File Format

**File Name**: `manifest.json` or `{instrument_id}_manifest.json`

**Format**: JSON

---

## Required Fields

```json
{
  "vendor": "string",
  "instrument_type": "string",
  "manufacturer": "string",
  "model": "string",
  "file_format": "string"
}
```

### Field Descriptions

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `vendor` | string | **Yes** | Vendor identifier (see supported vendors) | `"NOVABIO_FLEX2"` |
| `instrument_type` | string | **Yes** | Type of instrument | `"solution_analyzer"` |
| `manufacturer` | string | **Yes** | Manufacturer name | `"Nova Biomedical"` |
| `model` | string | **Yes** | Instrument model | `"BioProfile FLEX2"` |
| `file_format` | string | **Yes** | Data file format | `"csv"`, `"xml"`, `"json"` |

---

## Optional Fields

```json
{
  "serial_number": "string",
  "software_version": "string",
  "location": "string",
  "contact": "string",
  "notes": "string"
}
```

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `serial_number` | string | Instrument serial number | `"SN123456789"` |
| `software_version` | string | Instrument software version | `"6.2.1"` |
| `location` | string | Lab location | `"Building 3, Lab 201"` |
| `contact` | string | Responsible person | `"john.doe@company.com"` |
| `notes` | string | Additional information | `"Primary QC instrument"` |

---

## Instrument Types

Supported values for `instrument_type`:

- `solution_analyzer` - Cell culture analyzers (pH, metabolites, gases)
- `cell_counter` - Cell viability and counting
- `plate_reader` - Microplate readers (absorbance, fluorescence, luminescence)
- `spectrophotometer` - UV-Vis, NanoDrop, etc.
- `qpcr` - Real-time PCR systems
- `dpcr` - Digital PCR systems
- `osmometer` - Osmolality measurement
- `endotoxin_analyzer` - LAL assay systems
- `hplc` - High-performance liquid chromatography
- `mass_spectrometer` - Mass spectrometry systems

---

## Supported Vendors (Allotropy Library)

### Solution Analyzers
- `NOVABIO_FLEX2` - Nova BioProfile FLEX2
- `ROCHE_CEDEX_BIOHT` - Roche CEDEX BioHT
- `ROCHE_CEDEX_HIRES` - Roche CEDEX HiRes

### Cell Counters
- `BECKMAN_VI_CELL_BLU` - Beckman Vi-CELL BLU
- `BECKMAN_VI_CELL_XR` - Beckman Vi-CELL XR
- `CHEMOMETEC_NC_VIEW` - ChemoMetec NC-View
- `CHEMOMETEC_NUCLEOVIEW` - ChemoMetec NucleoView

### Plate Readers
- `AGILENT_GEN5` - Agilent Gen5 (BioTek)
- `AGILENT_GEN5_IMAGE` - Agilent Gen5 Image
- `BMG_MARS` - BMG MARS
- `MOLDEV_SOFTMAX_PRO` - Molecular Devices SoftMax Pro
- `PERKIN_ELMER_ENVISION` - PerkinElmer EnVision
- `REVVITY_KALEIDO` - Revvity Kaleido

### Spectrophotometers
- `BECKMAN_PHARMSPEC` - Beckman PharmSpec
- `THERMO_FISHER_GENESYS30` - Thermo Fisher Genesys 30
- `THERMO_FISHER_NANODROP_EIGHT` - Thermo Fisher NanoDrop Eight
- `THERMO_FISHER_NANODROP_ONE` - Thermo Fisher NanoDrop ONE
- `THERMO_FISHER_QUBIT4` - Thermo Fisher Qubit 4
- `THERMO_FISHER_QUBIT_FLEX` - Thermo Fisher Qubit Flex
- `UNCHAINED_LABS_LUNATIC` - Unchained Labs Lunatic

### qPCR/dPCR
- `APPBIO_ABSOLUTE_Q` - Applied Biosystems Absolute Q
- `APPBIO_QUANTSTUDIO` - Applied Biosystems QuantStudio
- `APPBIO_QUANTSTUDIO_DESIGNANDANALYSIS` - Applied Biosystems QuantStudio Design & Analysis
- `BIORAD_BIOPLEX` - Bio-Rad BioPlex
- `QIACUITY_DPCR` - QIAcuity dPCR

### Other
- `CTL_IMMUNOSPOT` - CTL ImmunoSpot
- `LUMINEX_XPONENT` - Luminex xPONENT
- `MABTECH_APEX` - Mabtech APEX
- `AGILENT_TAPESTATION_ANALYSIS` - Agilent TapeStation

**Full list**: See [SUPPORTED-INSTRUMENTS.md](SUPPORTED-INSTRUMENTS.md)

---

## File Format Values

- `csv` - Comma-separated values
- `tsv` - Tab-separated values
- `xml` - XML format
- `json` - JSON format
- `xlsx` - Excel format
- `txt` - Plain text

---

## Complete Examples

### Example 1: Nova FLEX2 Solution Analyzer

```json
{
  "vendor": "NOVABIO_FLEX2",
  "instrument_type": "solution_analyzer",
  "manufacturer": "Nova Biomedical",
  "model": "BioProfile FLEX2",
  "file_format": "csv",
  "serial_number": "FLEX2-2023-001",
  "software_version": "6.2.1",
  "location": "QC Lab, Building 3",
  "contact": "lab.manager@company.com",
  "notes": "Primary cell culture analyzer"
}
```

### Example 2: Beckman Vi-CELL BLU

```json
{
  "vendor": "BECKMAN_VI_CELL_BLU",
  "instrument_type": "cell_counter",
  "manufacturer": "Beckman Coulter",
  "model": "Vi-CELL BLU",
  "file_format": "csv",
  "serial_number": "VICELL-BLU-456",
  "software_version": "7.1"
}
```

### Example 3: Thermo NanoDrop

```json
{
  "vendor": "THERMO_FISHER_NANODROP_EIGHT",
  "instrument_type": "spectrophotometer",
  "manufacturer": "Thermo Fisher Scientific",
  "model": "NanoDrop Eight",
  "file_format": "xlsx"
}
```

### Example 4: Unknown Instrument (Custom)

If your instrument is not in the supported list, use:

```json
{
  "vendor": "CUSTOM",
  "instrument_type": "solution_analyzer",
  "manufacturer": "Acme Instruments",
  "model": "CustomAnalyzer 3000",
  "file_format": "csv",
  "notes": "Custom instrument - AI will generate converter"
}
```

---

## Usage

### Single File Conversion

Upload both files together:
- `data.csv` - Your instrument data
- `manifest.json` - Instrument metadata

### Batch Conversion

One manifest for multiple data files:
- `manifest.json` - Instrument metadata
- `sample_001.csv` - Data file 1
- `sample_002.csv` - Data file 2
- `sample_003.csv` - Data file 3

All data files will use the same manifest.

---

## Validation

The system will validate your manifest:

✓ All required fields present  
✓ Vendor is recognized or marked as CUSTOM  
✓ Instrument type is valid  
✓ File format matches actual data file  

If validation fails, you'll receive a clear error message.

---

## Manifest Generator Tool

Don't want to create JSON manually? Use our manifest generator:

**Web Interface**: [URL to be added]

**Command Line**:
```bash
asm-manifest-generator \
  --vendor NOVABIO_FLEX2 \
  --type solution_analyzer \
  --manufacturer "Nova Biomedical" \
  --model "BioProfile FLEX2" \
  --format csv \
  --output manifest.json
```

**Python**:
```python
from asm_tools import ManifestGenerator

manifest = ManifestGenerator()
manifest.vendor = "NOVABIO_FLEX2"
manifest.instrument_type = "solution_analyzer"
manifest.manufacturer = "Nova Biomedical"
manifest.model = "BioProfile FLEX2"
manifest.file_format = "csv"
manifest.save("manifest.json")
```

---

## FAQ

**Q: Do I need a new manifest for each data file?**  
A: No! One manifest per instrument. Reuse it for all files from that instrument.

**Q: What if my instrument isn't in the supported list?**  
A: Use `vendor: "CUSTOM"`. Our AI will analyze your file and generate a converter.

**Q: Can I have multiple instruments?**  
A: Yes! Create one manifest per instrument. Name them: `flex2_manifest.json`, `vicell_manifest.json`, etc.

**Q: What if I make a mistake in the manifest?**  
A: The system will validate and tell you exactly what's wrong.

**Q: Is the manifest required?**  
A: Yes, for production use. It ensures 100% accuracy and compliance.

**Q: Can the manifest be auto-generated?**  
A: Yes! After first successful conversion, the system can generate the manifest for you.

---

## Support

Questions? Contact: asm-service@aws.amazon.com

See also:
- [User Guide](USER-GUIDE.md)
- [Supported Instruments](SUPPORTED-INSTRUMENTS.md)
- [API Documentation](API-REFERENCE.md)

---

**Version**: 1.0  
**Last Updated**: January 21, 2026
