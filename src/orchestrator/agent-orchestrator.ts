import { BaseAgent, AgentTask, AgentResult } from '../agents/base-agent';
import { FileAnalysisAgent } from '../agents/file-analysis-agent';
import { ConverterGenerationAgent } from '../agents/converter-generation-agent';
import { spawn } from 'child_process';
import * as path from 'path';

export interface ConversionRequest {
  id: string;
  files: Array<{
    filename: string;
    content: Buffer;
    mimeType?: string;
  }>;
  targetSchema: string;
  requirements?: string[];
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  useStrandsAgents?: boolean;
}

export interface ConversionResult {
  requestId: string;
  success: boolean;
  converter?: any;
  error?: string;
  steps: Array<{
    agent: string;
    task: string;
    result: AgentResult;
  }>;
  metadata: {
    startTime: Date;
    endTime: Date;
    totalDuration: number;
  };
}

export class AgentOrchestrator {
  private agents: Map<string, BaseAgent> = new Map();
  private activeRequests: Map<string, ConversionRequest> = new Map();
  private strandsAgentsPath: string;

  constructor() {
    this.initializeAgents();
    this.strandsAgentsPath = path.join(__dirname, '..', 'agents');
  }

  private initializeAgents(): void {
    const fileAnalysisAgent = new FileAnalysisAgent();
    const converterGenerationAgent = new ConverterGenerationAgent();

    this.agents.set(fileAnalysisAgent.id, fileAnalysisAgent);
    this.agents.set(converterGenerationAgent.id, converterGenerationAgent);
  }

  // New method to call Python Strands agents
  private async callStrandsAgent(agentScript: string, input: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const agentPath = path.join(this.strandsAgentsPath, agentScript);
      const python = spawn('python', [agentPath, JSON.stringify(input)], {
        shell: true // Enable shell on Windows
      });
      
      let stdout = '';
      let stderr = '';
      
      python.stdout.on('data', (data) => {
        stdout += data.toString();
      });
      
      python.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      python.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout);
            resolve(result);
          } catch (error) {
            reject(new Error(`Failed to parse agent response: ${error.message}`));
          }
        } else {
          reject(new Error(`Agent failed with code ${code}: ${stderr}`));
        }
      });
      
      python.on('error', (error) => {
        reject(new Error(`Failed to spawn Python agent: ${error.message}`));
      });
    });
  }

  async processConversionRequest(request: ConversionRequest): Promise<ConversionResult> {
    const startTime = new Date();
    const steps: Array<{ agent: string; task: string; result: AgentResult }> = [];
    
    this.activeRequests.set(request.id, request);

    try {
      // Choose between Strands agents or TypeScript agents
      if (request.useStrandsAgents) {
        return await this.processWithStrandsAgents(request, startTime, steps);
      } else {
        return await this.processWithTypeScriptAgents(request, startTime, steps);
      }
    } catch (error) {
      return this.createFailureResult(
        request.id, 
        error instanceof Error ? error.message : 'Unknown error',
        steps,
        startTime
      );
    } finally {
      this.activeRequests.delete(request.id);
    }
  }

  private async processWithStrandsAgents(request: ConversionRequest, startTime: Date, steps: any[]): Promise<ConversionResult> {
    // Step 1: Analyze files with Strands File Analysis Agent
    for (const file of request.files) {
      const analysisInput = {
        filename: file.filename,
        file_content_base64: file.content.toString('base64')
      };
      
      const analysisResult = await this.callStrandsAgent('strands-file-analysis-agent.py', analysisInput);
      
      steps.push({
        agent: 'strands-file-analysis',
        task: 'analyze_file_format',
        result: {
          taskId: `analyze-${Date.now()}`,
          agentId: 'strands-file-analysis',
          success: analysisResult.success,
          output: analysisResult.analysis,
          metadata: { timestamp: analysisResult.timestamp }
        }
      });
      
      if (!analysisResult.success) {
        throw new Error(`File analysis failed: ${analysisResult.error}`);
      }
    }
    
    // Step 2: Generate converter with Strands Converter Generation Agent
    const lastAnalysis = steps[steps.length - 1].result.output;
    const converterInput = {
      file_analysis: lastAnalysis,
      target_schema: request.targetSchema,
      language: 'python'
    };
    
    const converterResult = await this.callStrandsAgent('strands-converter-generation-agent.py', converterInput);
    
    steps.push({
      agent: 'strands-converter-generation',
      task: 'generate_converter',
      result: {
        taskId: `generate-${Date.now()}`,
        agentId: 'strands-converter-generation',
        success: converterResult.success,
        output: converterResult.converter_response,
        metadata: { timestamp: converterResult.timestamp }
      }
    });
    
    if (!converterResult.success) {
      throw new Error(`Converter generation failed: ${converterResult.error}`);
    }
    
    const endTime = new Date();
    return {
      requestId: request.id,
      success: true,
      converter: converterResult.converter_response,
      steps,
      metadata: {
        startTime,
        endTime,
        totalDuration: endTime.getTime() - startTime.getTime()
      }
    };
  }

  private async processWithTypeScriptAgents(request: ConversionRequest, startTime: Date, steps: any[]): Promise<ConversionResult> {
    // Original TypeScript agent implementation
    const analysisResults = await this.analyzeFiles(request.files);
    steps.push(...analysisResults.steps);

    if (!analysisResults.success) {
      return this.createFailureResult(request.id, 'File analysis failed', steps, startTime);
    }

    const generationResult = await this.generateConverter(
      analysisResults.analysis,
      request.files,
      request.targetSchema,
      request.requirements
    );
    steps.push(generationResult.step);

    if (!generationResult.success) {
      return this.createFailureResult(request.id, 'Converter generation failed', steps, startTime);
    }

    const endTime = new Date();
    return {
      requestId: request.id,
      success: true,
      converter: generationResult.converter,
      steps,
      metadata: {
        startTime,
        endTime,
        totalDuration: endTime.getTime() - startTime.getTime()
      }
    };
  }

  private async analyzeFiles(files: ConversionRequest['files']): Promise<{
    success: boolean;
    analysis?: any;
    steps: Array<{ agent: string; task: string; result: AgentResult }>;
  }> {
    const fileAnalysisAgent = this.agents.get('file-analysis-agent');
    if (!fileAnalysisAgent) {
      throw new Error('File analysis agent not found');
    }

    const steps: Array<{ agent: string; task: string; result: AgentResult }> = [];
    const analyses: any[] = [];

    for (const file of files) {
      const task: AgentTask = {
        id: `analyze-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: 'analyze_file_format',
        input: {
          fileBuffer: file.content,
          filename: file.filename,
          mimeType: file.mimeType
        }
      };

      const result = await fileAnalysisAgent.execute(task);
      steps.push({
        agent: fileAnalysisAgent.name,
        task: 'analyze_file_format',
        result
      });

      if (result.success) {
        analyses.push(result.output);
      } else {
        return { success: false, steps };
      }
    }

    const combinedAnalysis = this.combineAnalyses(analyses);
    
    return {
      success: true,
      analysis: combinedAnalysis,
      steps
    };
  }

  private async generateConverter(
    analysis: any,
    sampleFiles: ConversionRequest['files'],
    targetSchema: string,
    requirements?: string[]
  ): Promise<{
    success: boolean;
    converter?: any;
    step: { agent: string; task: string; result: AgentResult };
  }> {
    const converterAgent = this.agents.get('converter-generation-agent');
    if (!converterAgent) {
      throw new Error('Converter generation agent not found');
    }

    const task: AgentTask = {
      id: `generate-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: 'generate_converter',
      input: {
        fileAnalysis: analysis,
        sampleFiles: sampleFiles.map(f => ({
          filename: f.filename,
          content: f.content
        })),
        targetSchema,
        requirements
      }
    };

    const result = await converterAgent.execute(task);
    const step = {
      agent: converterAgent.name,
      task: 'generate_converter',
      result
    };

    return {
      success: result.success,
      converter: result.output,
      step
    };
  }

  private combineAnalyses(analyses: any[]): any {
    if (analyses.length === 1) {
      return analyses[0];
    }

    const formats = [...new Set(analyses.map(a => a.format))];
    const allPatterns = analyses.flatMap(a => a.patterns || []);
    const allDataTypes = [...new Set(analyses.flatMap(a => a.metadata.dataTypes || []))];

    return {
      format: formats.length === 1 ? formats[0] : 'mixed',
      confidence: analyses.reduce((sum, a) => sum + a.confidence, 0) / analyses.length,
      structure: analyses[0].structure,
      patterns: allPatterns,
      metadata: {
        size: analyses.reduce((sum, a) => sum + a.metadata.size, 0),
        complexity: this.determineOverallComplexity(analyses),
        instrumentType: analyses.find(a => a.metadata.instrumentType)?.metadata.instrumentType,
        dataTypes: allDataTypes
      }
    };
  }

  private determineOverallComplexity(analyses: any[]): 'low' | 'medium' | 'high' {
    const complexities = analyses.map(a => a.metadata.complexity);
    if (complexities.includes('high')) return 'high';
    if (complexities.includes('medium')) return 'medium';
    return 'low';
  }

  private createFailureResult(
    requestId: string,
    error: string,
    steps: Array<{ agent: string; task: string; result: AgentResult }>,
    startTime: Date
  ): ConversionResult {
    const endTime = new Date();
    return {
      requestId,
      success: false,
      error,
      steps,
      metadata: {
        startTime,
        endTime,
        totalDuration: endTime.getTime() - startTime.getTime()
      }
    };
  }

  getActiveRequests(): ConversionRequest[] {
    return Array.from(this.activeRequests.values());
  }

  getAvailableAgents(): Array<{ id: string; name: string; capabilities: string[] }> {
    return Array.from(this.agents.values()).map(agent => ({
      id: agent.id,
      name: agent.name,
      capabilities: agent.capabilities.map(c => c.name)
    }));
  }
}