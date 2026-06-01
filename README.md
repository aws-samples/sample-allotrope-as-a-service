# ASM Transformation Service - Allotrope as a Service

AI-powered ASM (Allotrope Simple Model) transformation service for pharmaceutical laboratory data. Converts instrument output files to regulatory-compliant ASM format using AWS Bedrock Claude and the allotropy library.

## 🎯 Project Overview

This service provides automated conversion of laboratory instrument data to Allotrope Simple Model (ASM) format, with built-in validation and certification capabilities.

### Key Features

- **Multi-Instrument Support**: 31+ instruments via allotropy library
- **AI-Powered Conversion**: AWS Bedrock Claude for unknown formats
- **Validation & Certification**: DVaaS service with PDF attestation
- **Regulatory Compliance**: FDA 21 CFR Part 11 and EMA Annex 11 ready
- **Data Traceability**: Links calculated values to source measurements

## 📁 Repository Structure

```bash
asm-converter/
├── services/              # Backend Lambda services
│   ├── ataas/            # AI-powered transformation service
│   ├── dvaas/            # Data validation service
│   ├── multi-instrument/ # Allotropy-based converter (31+ instruments)
│   ├── unified-converter/# Intelligent routing service
│   └── deploy_services.py
├── dashboard/            # React dashboard (optional)
│   ├── src/
│   └── deploy-stack.py
├── README.md            # This file
└── MEMORY.md            # Project history and decisions
```

## 🚀 Deployment

Please refer to [DEPLOYMENT](./DEPLOYMENT.md) for detailed deployment instructions.

## 🔧 Services

### 1. ATaaS (ASM Transformation as a Service)

- **Endpoint**: `/prod/convert`
- **Purpose**: AI-powered file analysis and ASM conversion
- **Model**: AWS Bedrock Claude 4.6 Sonnet

### 2. DVaaS (Data Validation as a Service)

- **Endpoint**: `/prod/validate`
- **Purpose**: ASM validation and certification
- **Features**: PDF attestation, comprehensive validation

### 3. Multi-Instrument Service

- **Endpoint**: `/prod/convert`
- **Purpose**: 31+ instruments via allotropy library
- **Supported**: Plate readers, cell counters, solution analyzers, etc.

### 4. Unified Converter

- **Endpoint**: `/prod/convert`
- **Purpose**: Intelligent routing (allotropy → custom → AI)
- **Recommended**: Use this endpoint for all conversions

## 📊 Supported Instruments

See [SUPPORTED-INSTRUMENTS.md](docs/SUPPORTED-INSTRUMENTS.md) for complete list.

**Via Allotropy Library**: 31 instruments including:

- Beckman Vi-CELL (BLU, XR)
- Molecular Devices SoftMax Pro
- PerkinElmer EnVision
- Roche CEDEX BioHT
- And 27 more...

**Custom Converters**:

- Nova BioProfile FLEX2 (solution analyzer)
- Charles River EndoScan-V (endotoxin testing)

> **Example implementation**: See [sample-laboratory-data-transformation-mcp](https://github.com/aws-samples/sample-laboratory-data-transformation-mcp) for a reference implementation showing how to use AI to generate instrument data-to-ASM converter scripts.

## 🔐 Security & Compliance

- **No Data Persistence**: Files processed in-memory only
- **Audit Trail**: Complete traceability for calculated values
- **Regulatory Ready**: FDA 21 CFR Part 11 and EMA Annex 11 compliant
- **Data Integrity**: Validation against Allotrope schemas

## 🧪 Testing

Unit tests cover the Python backend services and require no deployed infrastructure or AWS credentials.

### Prerequisites

```bash
cd services
uv sync --group dev    # installs pytest, boto3, moto, pytest-mock
```

### Running tests

```bash
cd services

# Run all unit tests
uv run pytest

# Run with coverage report
uv run pytest --cov=. --cov-report=term-missing

# Run a single test file
uv run pytest tests/test_rule_engine.py -v

# Run a single test
uv run pytest tests/test_rule_engine.py::TestResolvePath::test_simple_nested
```

### Test structure

```bash
services/tests/
  conftest.py                   # shared fixtures and module loader
  fixtures/
    nova_flex2_sample.csv       # sample Nova FLEX2 instrument data
    sample_asm_valid.json       # minimal valid ASM document
    sample_rule_set.json        # sample validation rule set
  test_custom_converter.py      # sandbox import allowlist and exec() isolation
  test_multi_instrument.py      # instrument type detection and CSV converters
  test_rule_engine.py           # DVaaS rule engine (path resolution, all check types)
  test_unified_converter.py     # Nova FLEX2 detection and conversion, error responses
  test_validate_asm.py          # ASM attribute validation, technique detection
```

AWS SDK calls (boto3) are mocked via [moto](https://github.com/getmoto/moto); allotropy is stubbed since it is a Lambda layer dependency not required for unit tests.

## 📝 License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

---

**Built with**: AWS Lambda, AWS Bedrock Claude, Allotropy Library, React, AWS CDK
