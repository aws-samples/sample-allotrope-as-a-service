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
├── docs/                 # Documentation
├── demo-samples/         # Sample files for testing
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

## 🔐 Security & Compliance

- **No Data Persistence**: Files processed in-memory only
- **Audit Trail**: Complete traceability for calculated values
- **Regulatory Ready**: FDA 21 CFR Part 11 and EMA Annex 11 compliant
- **Data Integrity**: Validation against Allotrope schemas

## 🧪 Testing

```bash
# Test with sample file
curl -X POST https://your-api-endpoint/prod/convert \
  -H "Content-Type: application/json" \
  -d @demo-samples/sample-request.json
```

## 📝 License

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

---

**Built with**: AWS Lambda, AWS Bedrock Claude, Allotropy Library, React, AWS CDK
