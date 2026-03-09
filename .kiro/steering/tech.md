# Technology Stack

## Core Technologies

### Frontend/Client
- **TypeScript**: Primary language for agent implementations and orchestration
- **Node.js 18+**: Runtime environment
- **Strands Agent Framework**: Multi-agent orchestration and tool integration

### Backend/Services
- **Python 3.x**: Lambda functions and CDK infrastructure
- **AWS CDK**: Infrastructure as Code for deployment
- **AWS Lambda**: Serverless compute for services
- **AWS Bedrock**: Claude 3 Sonnet model access
- **AWS IoT Greengrass**: Edge computing for on-premises deployment

### Key Dependencies
- `@aws-sdk/client-bedrock-runtime`: Bedrock model invocation
- `@aws-sdk/client-s3`: File storage operations
- `@aws-sdk/client-dynamodb`: Data persistence
- `@strands/agent-framework`: Agent orchestration
- `aws-cdk-lib`: Infrastructure deployment
- `zod`: Schema validation
- `uuid`: Unique identifier generation
- `allotropy`: Instrument data parsing (v0.1.55) - 50+ instruments
- `pandas`: Data manipulation for allotropy
- `openpyxl`: Excel file support
- `pdfplumber`: PDF parsing support

## Build System

### TypeScript Build
```bash
# Install dependencies
npm install

# Build TypeScript to JavaScript
npm run build

# Development with hot reload
npm run dev

# Run tests
npm run test
```

### Python/CDK Deployment
```bash
# Deploy services stack
cd services
python deploy_services.py

# Deploy storage service
cd storage-service
python deploy_storage.py

# Deploy approval system
cd approval-system
python deploy_approval.py
```

### Greengrass Edge Deployment
```bash
cd greengrass
# Deploy to edge device
./deploy.sh
```

## Development Patterns

### Agent Implementation
- Extend `BaseAgent` class for TypeScript agents
- Use Strands framework for Python agents with `@tool` decorators
- Implement `execute()` method for task processing
- Use `invokeClaude()` for AI model interactions

### Error Handling
- Always wrap agent operations in try-catch blocks
- Return structured `AgentResult` objects with success/error states
- Include metadata for debugging and audit trails

### AWS Integration
- Use AWS SDK v3 with proper error handling
- Configure region as `us-east-1` by default
- Implement proper IAM roles and permissions for Lambda functions

## Environment Configuration

Required environment variables:
- `AWS_REGION`: AWS deployment region
- `AWS_ACCESS_KEY_ID`: AWS credentials
- `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `BEDROCK_MODEL_ID`: Claude model identifier (default: anthropic.claude-3-sonnet-20240229-v1:0)