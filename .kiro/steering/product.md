# Product Overview

ASM Transformation Service is an AI agent-powered system for converting laboratory instrument data into Allotrope Simple Model (ASM) format. The system uses AWS Bedrock Claude models with multi-agent orchestration to intelligently analyze file formats and generate converters dynamically.

## Core Capabilities

- **AI-Powered File Analysis**: Automatically detects and analyzes unknown file formats from laboratory instruments
- **50+ Supported Instruments**: Native support via allotropy library (Vi-CELL, NanoDrop, SoftMax Pro, QuantStudio, and more)
- **Dynamic Converter Generation**: Generates TypeScript and Python converters on-demand using Claude 3 Sonnet for unsupported formats
- **Hybrid Approach**: Uses proven allotropy parsers for supported instruments, falls back to AI generation for proprietary formats
- **Multi-Agent Orchestration**: Coordinates specialized agents (File Analysis, Converter Generation, Knowledge Base) to handle complex transformation workflows
- **Autonomous Services**: ATaaS (Allotrope Transformation as a Service), DVaaS (Data Validation as a Service), and Multi-Instrument support
- **Edge Computing**: AWS IoT Greengrass integration for on-premises instrument data processing
- **Approval Workflows**: Human-in-the-loop approval system for generated converters

## Target Users

Scientific data engineers, laboratory automation teams, and organizations needing to standardize instrument data into ASM format for regulatory compliance and data interoperability.

## Key Differentiators

Unlike traditional static converters, this system uses AI agents to understand context, make intelligent decisions, and generate converters for previously unseen formats. The multi-agent architecture enables extensibility and self-improvement over time.
