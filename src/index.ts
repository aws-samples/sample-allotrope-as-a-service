import { AgentOrchestrator, ConversionRequest } from './orchestrator/agent-orchestrator';
import { v4 as uuidv4 } from 'uuid';
import * as fs from 'fs';

export class ASMTransformationService {
  private orchestrator: AgentOrchestrator;

  constructor() {
    this.orchestrator = new AgentOrchestrator();
  }

  async convertFiles(
    filePaths: string[],
    targetSchema: string = 'asm-1.0.0',
    requirements?: string[]
  ): Promise<any> {
    // Load files
    const files = filePaths.map(filePath => ({
      filename: filePath.split(/[/\\]/).pop() || 'unknown',
      content: fs.readFileSync(filePath),
      mimeType: this.getMimeType(filePath)
    }));

    // Create conversion request
    const request: ConversionRequest = {
      id: uuidv4(),
      files,
      targetSchema,
      requirements,
      priority: 'medium'
    };

    // Process request
    const result = await this.orchestrator.processConversionRequest(request);
    
    return {
      success: result.success,
      converter: result.converter,
      error: result.error,
      processingSteps: result.steps.map(step => ({
        agent: step.agent,
        task: step.task,
        success: step.result.success,
        duration: step.result.metadata?.executionTime
      })),
      totalDuration: result.metadata.totalDuration
    };
  }

  async getServiceStatus(): Promise<{
    agents: Array<{ id: string; name: string; capabilities: string[] }>;
    activeRequests: number;
  }> {
    return {
      agents: this.orchestrator.getAvailableAgents(),
      activeRequests: this.orchestrator.getActiveRequests().length
    };
  }

  private getMimeType(filePath: string): string {
    const ext = filePath.split('.').pop()?.toLowerCase();
    const mimeTypes: Record<string, string> = {
      'csv': 'text/csv',
      'json': 'application/json',
      'xml': 'application/xml',
      'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'pdf': 'application/pdf',
      'txt': 'text/plain'
    };
    return mimeTypes[ext || ''] || 'application/octet-stream';
  }
}

// Example usage
async function main() {
  const service = new ASMTransformationService();
  
  console.log('ASM Transformation Service - Agent-based Version');
  console.log('Service Status:', await service.getServiceStatus());
  
  // Example: Convert a sample file
  // const result = await service.convertFiles(['./sample-data.csv']);
  // console.log('Conversion Result:', result);
}

if (require.main === module) {
  main().catch(console.error);
}

export { AgentOrchestrator, ConversionRequest } from './orchestrator/agent-orchestrator';
export { FileAnalysisAgent } from './agents/file-analysis-agent';
export { ConverterGenerationAgent } from './agents/converter-generation-agent';