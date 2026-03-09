# Allotropy Library Integration Plan

**Date**: January 2026  
**Status**: IN PROGRESS  
**Priority**: HIGH  
**Estimated Effort**: 7-10 hours

## Overview

Integrating Anthropic's `allotropy` library (v0.1.55) into the ASM Transformation Service to leverage 50+ pre-built instrument parsers while maintaining our custom agent architecture.

## Discovery

**Source**: Anthropic Claude announcement - Instrument Data to Allotrope Skill v1.1.1  
**Location**: `C:\app\asm2agent\claude\instrument-data-to-allotrope-v1.1.1\`  
**Key Files**:
- `SKILL.md` - Complete skill documentation
- `scripts/convert_to_asm.py` - Main conversion script
- `scripts/validate_asm.py` - ASM validation
- `references/supported_instruments.md` - 50+ supported instruments

## Integration Strategy: HYBRID APPROACH

### Architecture Decision
**Keep our Strands agent architecture** + **Add allotropy as a tool**

```
Strands Agents (Our Architecture)
├── File Analysis Agent
│   └── NEW: Detect if allotropy supports instrument
├── Converter Generation Agent
│   ├── NEW: Try allotropy first (50+ instruments)
│   └── FALLBACK: Custom code generation (proprietary formats)
└── Supervisor Agent
    └── Orchestrate workflow as before
```

### Benefits
- ✅ Instant support for 50+ instruments
- ✅ Keep custom generation for proprietary formats
- ✅ Maintain approval workflow
- ✅ Keep Lambda deployment automation
- ✅ Proven, vendor-validated parsers

## Implementation Phases

### Phase 1: Core Integration (2-3 hours)

**1.1 Install Dependencies**
```bash
cd C:\app\asm2agent\src\agents
pip install allotropy==0.1.55 pandas==2.0.3 openpyxl==3.1.2 pdfplumber==0.9.0
```

**1.2 Add Allotropy Tool to File Analysis Agent**
- File: `src/agents/strands-file-analysis-agent.py`
- Add: `detect_allotropy_support()` tool
- Purpose: Check if instrument is supported by allotropy

**1.3 Add Allotropy Tool to Converter Generation Agent**
- File: `src/agents/strands-converter-generation-agent.py`
- Add: `convert_with_allotropy()` tool
- Purpose: Use allotropy for supported instruments
- Fallback: Custom generation for unsupported formats

**1.4 Update Requirements**
- File: `src/agents/requirements.txt`
- Add allotropy and dependencies

### Phase 2: Validation Enhancement (3-4 hours)

**2.1 Integrate Validation Script**
- Copy: `claude/instrument-data-to-allotrope-v1.1.1/scripts/validate_asm.py`
- To: `src/agents/validate_asm.py`
- Update DVaaS to use validation script

**2.2 Update DVaaS Service**
- File: `services/dvaas/lambda_function.py`
- Add: Allotropy validation logic
- Enhance: Error reporting with detailed validation results

**2.3 Update Multi-Instrument Service**
- File: `services/multi-instrument/lambda_function.py`
- Add: Allotropy support for plate readers, cell counters
- Test: End-to-end workflow

### Phase 3: Testing & Documentation (2-3 hours)

**3.1 Create Test Suite**
- File: `test_allotropy_integration.py`
- Test: All 50+ supported instruments
- Validate: Fallback to custom generation works

**3.2 Update Documentation**
- Update: `ARCHITECTURE.md`
- Update: `MEMORY.md`
- Update: `README.md`
- Create: This file (`ALLOTROPY-INTEGRATION.md`)

**3.3 Update Steering Documents**
- Update: `.kiro/steering/tech.md`
- Update: `.kiro/steering/product.md`

## Supported Instruments (via Allotropy)

### Cell Counting (5 instruments)
- Beckman Coulter Vi-CELL BLU/XR
- ChemoMetec NucleoView NC-200
- ChemoMetec NC-View
- Revvity Matrix

### Spectrophotometry (5 instruments)
- Thermo Fisher NanoDrop One/Eight/8000
- Unchained Labs Lunatic
- Thermo Fisher Genesys 30

### Plate Readers (9 instruments)
- Molecular Devices SoftMax Pro
- PerkinElmer EnVision
- Agilent Gen5 (BioTek)
- BMG MARS (CLARIOstar)
- BMG LabTech Smart Control
- Thermo SkanIt
- Revvity Kaleido
- Tecan Magellan

### ELISA (4 instruments)
- Molecular Devices SoftMax Pro
- MSD Discovery Workbench
- MSD Methodical Mind
- BMG MARS

### qPCR (4 instruments)
- Applied Biosystems QuantStudio
- Bio-Rad CFX Maestro
- Roche LightCycler

### Chromatography (3 instruments)
- Waters Empower
- Thermo Fisher Chromeleon
- Agilent ChemStation

### Electrophoresis (2 instruments)
- Agilent TapeStation
- PerkinElmer LabChip

### Flow Cytometry (2 instruments)
- BD Biosciences FACSDiva
- FlowJo

### Solution Analysis (2 instruments)
- Roche Cedex BioHT
- Beckman Coulter Biomek

**Total: 50+ instruments supported out-of-the-box**

## Code Changes Required

### File: `src/agents/strands-file-analysis-agent.py`
```python
# ADD: New tool for allotropy detection
@tool
def detect_allotropy_support(filename: str, file_content: str) -> str:
    """Check if allotropy library supports this instrument"""
    from allotropy.parser_factory import Vendor
    
    # Detection logic from Anthropic skill
    # Returns: {"supported": true/false, "vendor": "VENDOR_NAME", "confidence": 0.95}
```

### File: `src/agents/strands-converter-generation-agent.py`
```python
# ADD: New tool for allotropy conversion
@tool
def convert_with_allotropy(file_path: str, vendor: str) -> str:
    """Convert using allotropy library for supported instruments"""
    from allotropy.parser_factory import Vendor
    from allotropy.to_allotrope import allotrope_from_file
    
    try:
        vendor_enum = getattr(Vendor, vendor)
        asm = allotrope_from_file(file_path, vendor_enum)
        return json.dumps({"success": True, "asm": asm, "method": "allotropy"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

### File: `services/dvaas/lambda_function.py`
```python
# ADD: Allotropy validation
def validate_with_allotropy(asm_data):
    """Use Anthropic's validation script"""
    from validate_asm import validate_asm
    
    result = validate_asm(asm_data)
    return {
        'valid': result.is_valid(),
        'errors': result.errors,
        'warnings': result.warnings,
        'method': 'allotropy_validator'
    }
```

## Testing Strategy

### Unit Tests
- Test allotropy detection for each instrument type
- Test conversion for sample files
- Test fallback to custom generation

### Integration Tests
- Test end-to-end workflow with allotropy
- Test TypeScript → Python agent calls
- Test Lambda deployment

### Validation Tests
- Test DVaaS with allotropy validation
- Compare results with existing validation
- Test edge cases and error handling

## Rollout Plan

### Development Environment
1. Install allotropy locally
2. Test with sample files
3. Validate integration

### Staging Environment
1. Deploy updated agents
2. Test with real instrument files
3. Performance testing

### Production Environment
1. Deploy to Lambda functions
2. Monitor performance
3. Gradual rollout by instrument type

## Success Metrics

- ✅ 50+ instruments supported via allotropy
- ✅ Fallback to custom generation works
- ✅ Validation enhanced with allotropy
- ✅ No regression in existing functionality
- ✅ Performance maintained or improved
- ✅ Documentation updated

## Risks & Mitigation

### Risk 1: Allotropy Library Updates
**Mitigation**: Pin version to 0.1.55, test before upgrading

### Risk 2: Unsupported Instruments
**Mitigation**: Maintain custom generation fallback

### Risk 3: Performance Impact
**Mitigation**: Cache parsers, optimize imports

### Risk 4: Breaking Changes
**Mitigation**: Comprehensive test suite, gradual rollout

## Dependencies

### Python Packages
- `allotropy==0.1.55` - Core parsing library
- `pandas==2.0.3` - Data manipulation
- `openpyxl==3.1.2` - Excel support
- `pdfplumber==0.9.0` - PDF parsing

### Existing Dependencies
- `strands` - Agent framework
- `boto3` - AWS SDK
- `aws-cdk-lib` - Infrastructure

## Timeline

**Week 1**: Phase 1 - Core Integration (2-3 hours)  
**Week 1**: Phase 2 - Validation Enhancement (3-4 hours)  
**Week 2**: Phase 3 - Testing & Documentation (2-3 hours)  
**Week 2**: Deployment to staging  
**Week 3**: Production rollout

**Total Duration**: 2-3 weeks including testing and validation

## References

- Anthropic Skill: `C:\app\asm2agent\claude\instrument-data-to-allotrope-v1.1.1\`
- Allotropy Library: https://pypi.org/project/allotropy/
- Allotrope Foundation: https://gitlab.com/allotrope-public/asm
- Project Architecture: `C:\app\asm2agent\ARCHITECTURE.md`

## Status Updates

**2026-01-10**: Integration plan created  
**2026-01-10**: Starting Phase 1 implementation

---

**Next Action**: Implement Phase 1 - Core Integration
