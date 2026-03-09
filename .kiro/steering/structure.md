# Project Structure

## Directory Organization

### Root Level
```
asm-transformation-service/
├── src/                          # TypeScript source code
├── services/                     # AWS Lambda services (Python)
├── approval-system/              # Human approval workflow
├── storage-service/              # S3/DynamoDB storage layer
├── greengrass/                   # Edge computing deployment
├── dashboard/                    # Web dashboard for monitoring
├── docs/                         # Documentation
├── logs/                         # Application logs
├── generated_converters/         # AI-generated converter code
├── strands-tutorial/             # Strands framework examples
└── test files                    # Various test and validation files
```

### Source Code Structure (`src/`)
```
src/
├── agents/                       # TypeScript agent implementations
│   ├── base-agent.ts            # Base agent class
│   ├── file-analysis-agent.ts   # File analysis logic
│   └── converter-generation-agent.ts # Code generation logic
├── orchestrator/                 # Agent coordination
│   ├── agent-orchestrator.ts    # Main orchestrator
│   └── strands-agent-orchestrator.py # Python Strands orchestrator
└── index.ts                     # Main service entry point
```

### Services Structure (`services/`)
```
services/
├── ataas/                       # ASM Transformation as a Service
│   ├── lambda_function.py      # Main Lambda handler
│   └── requirements.txt        # Python dependencies
├── dvaas/                       # Data Validation as a Service
│   ├── lambda_function.py      # Validation Lambda handler
│   └── requirements.txt        # Python dependencies
├── multi-instrument/            # Multi-instrument support
│   ├── lambda_function.py      # Multi-instrument handler
│   └── requirements.txt        # Python dependencies
├── deploy_services.py           # CDK deployment script
└── cdk.json                     # CDK configuration
```

### Strands Agents Structure
```
src/agents/
├── strands-file-analysis-agent.py      # File format analysis
├── strands-converter-generation-agent.py # Code generation
└── strands-agent-orchestrator.py       # Workflow coordination

src/orchestrator/
└── strands_agent_orchestrator.py       # Workflow management class
```

## File Naming Conventions

### TypeScript Files
- **Classes**: PascalCase (e.g., `AgentOrchestrator.ts`)
- **Interfaces**: PascalCase with 'I' prefix (e.g., `IAgentTask.ts`)
- **Utilities**: camelCase (e.g., `fileUtils.ts`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_ENDPOINTS.ts`)

### Python Files
- **Modules**: snake_case (e.g., `lambda_function.py`)
- **Classes**: PascalCase (e.g., `class FileAnalyzer`)
- **Functions**: snake_case (e.g., `def analyze_file()`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `BEDROCK_MODEL_ID`)

### Strands Agents
- **Pattern**: `strands-{purpose}-agent.py`
- **Examples**: 
  - `strands-file-analysis-agent.py`
  - `strands-converter-generation-agent.py`
  - `strands-agent-orchestrator.py`

## Configuration Files

### Package Management
- `package.json` - Node.js dependencies and scripts
- `requirements.txt` - Python dependencies (per service)
- `tsconfig.json` - TypeScript compiler configuration

### AWS Configuration
- `cdk.json` - CDK application settings
- `deploy_services.py` - Infrastructure deployment
- Environment variables in Lambda functions

### Development
- `.gitignore` - Version control exclusions
- `README.md` - Project documentation
- `ARCHITECTURE.md` - System architecture
- `ARCHITECTURE-STATUS.md` - Implementation status

## Data Flow Structure

### Input Processing
```
File Upload → TypeScript Orchestrator → Strands Agents → Generated Code → Lambda Deployment
```

### Service Execution
```
API Request → API Gateway → Lambda Function → S3/DynamoDB → Response
```

### Agent Workflow
```
File Analysis Agent → Converter Generation Agent → Supervisor Agent → Deployment
```

## Testing Structure

### Test Files Pattern
- `test_*.py` - Python test files
- `*.test.ts` - TypeScript test files
- Test data files: `test_data_*.csv`, `asm_test_data_*.json`

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service-to-service communication
- **End-to-End Tests**: Complete workflow validation
- **System Tests**: Full deployment testing

## Deployment Structure

### AWS Resources
```
Production:
├── Lambda Functions (ataas, dvaas, multi-instrument)
├── API Gateway (REST endpoints)
├── S3 Buckets (file storage)
├── DynamoDB Tables (metadata)
└── CloudWatch (monitoring)
```

### Edge Deployment
```
Greengrass:
├── Core device configuration
├── Lambda function deployment
├── Local data processing
└── Cloud synchronization
```

## Development Workflow

### Code Organization
1. **Agents** - AI-powered code generation (Python Strands)
2. **Services** - Runtime execution (Python Lambda)
3. **Orchestration** - Workflow coordination (TypeScript)
4. **Infrastructure** - AWS resource management (CDK)

### Build Process
1. TypeScript compilation (`npm run build`)
2. Python packaging (per service)
3. CDK synthesis and deployment
4. Agent testing and validation

## Integration Points

### Agent-Service Bridge
- TypeScript orchestrator calls Python Strands agents
- Generated code deployed as Lambda functions
- Service configuration updated automatically

### External Interfaces
- REST APIs for client integration
- S3 for file storage and retrieval
- DynamoDB for metadata and history
- CloudWatch for monitoring and logging

This structure supports the hybrid architecture where AI agents generate code at build-time and lightweight services execute at runtime.