# ASM Transformation Service - Agentic Architecture

## System Overview

The ASM Transformation Service uses a **hybrid architecture** where AI agents generate code at build-time, and lightweight Lambda services execute at runtime.

## Architecture Principles

1. **Agents = Code Generators** (Build-time intelligence)
2. **Services = Runtime Execution** (Fast, lightweight)
3. **APIs = External Interface** (Internal/external access)

## Component Architecture

### 1. Agent System (Code Generation Layer)
**Location**: `C:\app\asm2agent\src\agents\`
**Purpose**: Intelligent code generation using Strands framework

```
Strands Agents (Build-time)
├── File Analysis Agent
│   └── Analyzes instrument files → Generates analysis metadata
├── Converter Generation Agent  
│   └── Creates Python converter code → Deployable Lambda functions
└── Supervisor Agent
    └── Orchestrates workflow → Manages agent coordination
```

**Key Files**:
- `strands-file-analysis-agent.py` - File format detection and analysis
- `strands-converter-generation-agent.py` - Python code generation
- `strands-agent-orchestrator.py` - Workflow supervision

### 2. Service Layer (Runtime Execution)
**Location**: `C:\app\asm2agent\services\`
**Purpose**: Autonomous microservices for production workloads

```
Runtime Services
├── ATaaS (ASM Transformation as a Service)
│   ├── API Gateway → Lambda Function → S3/DynamoDB
│   ├── Converts files to ASM format
│   ├── Generates Python converter code
│   └── Stores results and metadata
├── DVaaS (Data Validation as a Service)
│   ├── API Gateway → Lambda Function → Results
│   ├── Validates ASM files against schemas
│   ├── Issues ALLOTROPE_CERTIFIED status
│   └── Standalone validation service
└── Multi-Instrument Service
    ├── API Gateway → Lambda Function → S3/DynamoDB
    ├── Handles multiple instrument types
    └── Aggregated result visualization
```

**Key Files**:
- `services/ataas/lambda_function.py` - ATaaS runtime service
- `services/dvaas/lambda_function.py` - DVaaS runtime service
- `services/multi-instrument/lambda_function.py` - Multi-instrument service
- `services/deploy_services.py` - CDK deployment stack

### 3. Integration Layer (TypeScript Frontend)
**Location**: `C:\app\asm2agent\src\orchestrator\`
**Purpose**: Frontend orchestration and Python agent integration

```
Frontend Integration
├── TypeScript Orchestrators
│   ├── Call Python Strands agents via subprocess
│   ├── Handle web API requests
│   └── Coordinate agent workflows
└── Service Integration
    ├── Deploy generated code as Lambda functions
    └── Update service configurations
```

## Execution Workflow

### Build-time (Code Generation)
```
1. File Upload → TypeScript Orchestrator
2. Orchestrator → Calls Strands File Analysis Agent (Python)
3. Analysis Results → Strands Converter Generation Agent (Python)
4. Generated Code → Deploy as new Lambda function
5. Lambda Endpoint → Register with ATaaS service
```

### Runtime (Service Execution)
```
1. API Request → API Gateway
2. API Gateway → Lambda Function (Generated Code)
3. Lambda → Process file → Generate ASM
4. Optional: Lambda → Call DVaaS for validation
5. Results → Store in S3/DynamoDB → Return to client
```

## Service Autonomy Requirements

### ATaaS Service (✅ AUTONOMOUS)
- **Independent Operation**: Runs without external dependencies
- **API Interface**: REST endpoints for external/internal calls
- **Storage Integration**: S3 + DynamoDB persistence
- **Code Generation**: Creates deployable Python converters
- **Health Monitoring**: Service status endpoints
- **Error Handling**: Graceful failure recovery

### DVaaS Service (✅ AUTONOMOUS)
- **Independent Operation**: Standalone validation service
- **API Interface**: REST endpoints for validation requests
- **Schema Validation**: ASM compliance checking
- **Certification**: ALLOTROPE_CERTIFIED status issuance
- **Health Monitoring**: Service status endpoints
- **Error Handling**: Validation error reporting

## Integration Points

### Internal Service Communication
```
ATaaS → DVaaS (validation)
Multi-Instrument → ATaaS (conversion)
Multi-Instrument → DVaaS (validation)
```

### External API Access
```
Client → ATaaS API (file conversion)
Client → DVaaS API (validation)
Client → Multi-Instrument API (multi-device processing)
```

### Agent Integration
```
TypeScript Orchestrator → Python Strands Agents (subprocess calls)
Generated Code → Deploy as Lambda functions
Service Updates → Configuration management
```

## Deployment Architecture

### Container Strategy (ECS)
```
Single Container:
├── Node.js (TypeScript orchestration)
├── Python (Strands agents)
├── AWS SDK (service deployment)
└── Generated Lambda code
```

### AWS Services
```
Compute:
├── ECS Fargate (orchestration container)
├── Lambda Functions (generated converters)
└── API Gateway (service interfaces)

Storage:
├── S3 (ASM files, converter code)
├── DynamoDB (metadata, history)
└── CloudWatch (monitoring, logs)
```

## Implementation Status

### ✅ COMPLETED
- Strands agents (file analysis, converter generation, orchestrator)
- Autonomous ATaaS and DVaaS services
- Multi-instrument support with visualization
- S3/DynamoDB storage integration
- API Gateway endpoints with CORS
- Health monitoring and error handling

### ❌ MISSING INTEGRATION
- TypeScript → Python agent subprocess calls
- Generated code → Lambda deployment automation
- Agent-driven service updates
- End-to-end workflow testing

## Next Steps for Full Integration

1. **Add Python Agent CLI Interface** (1-2 hours)
   ```python
   if __name__ == "__main__":
       input_data = json.loads(sys.argv[1])
       agent = create_file_analysis_agent()
       result = agent(input_data["prompt"])
       print(json.dumps(result))
   ```

2. **Add TypeScript → Python Bridge** (2-3 hours)
   ```typescript
   private async callStrandsAgent(agentPath: string, input: any): Promise<any> {
       const python = spawn('python', [agentPath, JSON.stringify(input)]);
       // Handle response
   }
   ```

3. **Add Lambda Deployment Automation** (2-4 hours)
   - Generated code → CDK deployment
   - Service configuration updates
   - Endpoint registration

4. **End-to-End Testing** (1-2 hours)
   - Agent workflow validation
   - Service integration testing
   - Error scenario handling

**Total Integration Effort**: 6-11 hours for complete agent-service integration.