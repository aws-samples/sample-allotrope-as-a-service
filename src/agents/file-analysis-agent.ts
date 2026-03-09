import { BaseAgent, AgentTask, AgentResult, AgentCapability } from './base-agent';

export interface FileAnalysisInput {
  fileBuffer: Buffer;
  filename: string;
  mimeType?: string;
}

export interface FileAnalysisOutput {
  format: string;
  confidence: number;
  structure: {
    type: 'binary' | 'text' | 'structured';
    encoding?: string;
    headers?: string[];
    delimiter?: string;
  };
  patterns: Array<{
    type: string;
    description: string;
    examples: string[];
    confidence: number;
  }>;
  metadata: {
    size: number;
    complexity: 'low' | 'medium' | 'high';
    instrumentType?: string;
    dataTypes: string[];
  };
}

export class FileAnalysisAgent extends BaseAgent {
  constructor() {
    const capabilities: AgentCapability[] = [
      {
        name: 'analyze_file_format',
        description: 'Analyze file format and structure',
        inputSchema: {
          type: 'object',
          properties: {
            fileBuffer: { type: 'buffer' },
            filename: { type: 'string' },
            mimeType: { type: 'string' }
          },
          required: ['fileBuffer', 'filename']
        },
        outputSchema: {
          type: 'object',
          properties: {
            format: { type: 'string' },
            confidence: { type: 'number' },
            structure: { type: 'object' },
            patterns: { type: 'array' },
            metadata: { type: 'object' }
          }
        }
      }
    ];

    super('file-analysis-agent', 'File Analysis Agent', capabilities);
  }

  async execute(task: AgentTask): Promise<AgentResult> {
    try {
      switch (task.type) {
        case 'analyze_file_format':
          return await this.analyzeFileFormat(task);
        default:
          return this.createResult(task, false, null, `Unknown task type: ${task.type}`);
      }
    } catch (error) {
      return this.createResult(task, false, null, error instanceof Error ? error.message : 'Unknown error');
    }
  }

  private async analyzeFileFormat(task: AgentTask): Promise<AgentResult> {
    const input = task.input as FileAnalysisInput;
    
    // Basic file signature analysis
    const fileSignature = this.analyzeFileSignature(input.fileBuffer);
    
    // Content analysis using Claude
    const contentSample = this.extractContentSample(input.fileBuffer);
    const analysisPrompt = this.buildAnalysisPrompt(input.filename, fileSignature, contentSample);
    
    const claudeResponse = await this.invokeClaude(analysisPrompt);
    const analysis = this.parseClaudeResponse(claudeResponse);
    
    // Combine signature analysis with Claude insights
    const result: FileAnalysisOutput = {
      format: analysis.format || fileSignature.format,
      confidence: Math.min(fileSignature.confidence, analysis.confidence || 0.5),
      structure: {
        type: this.determineStructureType(input.fileBuffer),
        encoding: analysis.encoding || 'utf-8',
        headers: analysis.headers,
        delimiter: analysis.delimiter
      },
      patterns: analysis.patterns || [],
      metadata: {
        size: input.fileBuffer.length,
        complexity: this.assessComplexity(input.fileBuffer, analysis),
        instrumentType: analysis.instrumentType,
        dataTypes: analysis.dataTypes || []
      }
    };

    return this.createResult(task, true, result);
  }

  private analyzeFileSignature(buffer: Buffer): { format: string; confidence: number } {
    const signatures = [
      { format: 'pdf', signature: [0x25, 0x50, 0x44, 0x46], confidence: 0.95 },
      { format: 'xlsx', signature: [0x50, 0x4B, 0x03, 0x04], confidence: 0.8 },
      { format: 'zip', signature: [0x50, 0x4B, 0x03, 0x04], confidence: 0.7 },
      { format: 'png', signature: [0x89, 0x50, 0x4E, 0x47], confidence: 0.95 },
      { format: 'jpeg', signature: [0xFF, 0xD8, 0xFF], confidence: 0.95 }
    ];

    for (const sig of signatures) {
      if (buffer.length >= sig.signature.length) {
        const matches = sig.signature.every((byte, index) => buffer[index] === byte);
        if (matches) {
          return { format: sig.format, confidence: sig.confidence };
        }
      }
    }

    // Check for text-based formats
    const textSample = buffer.toString('utf-8', 0, Math.min(1000, buffer.length));
    if (this.isValidText(textSample)) {
      if (textSample.includes(',') && textSample.includes('\n')) {
        return { format: 'csv', confidence: 0.7 };
      }
      if (textSample.includes('<') && textSample.includes('>')) {
        return { format: 'xml', confidence: 0.7 };
      }
      if (textSample.includes('{') && textSample.includes('}')) {
        return { format: 'json', confidence: 0.7 };
      }
    }

    return { format: 'unknown', confidence: 0.1 };
  }

  private extractContentSample(buffer: Buffer): string {
    const maxSampleSize = 2000;
    const sample = buffer.toString('utf-8', 0, Math.min(maxSampleSize, buffer.length));
    return sample.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]/g, ''); // Remove control characters
  }

  private buildAnalysisPrompt(filename: string, signature: any, contentSample: string): string {
    return `Analyze this laboratory data file:

Filename: ${filename}
Detected format: ${signature.format}
Content sample:
${contentSample}

Provide analysis in JSON format:
{
  "format": "detected_format",
  "confidence": 0.8,
  "encoding": "utf-8",
  "headers": ["column1", "column2"],
  "delimiter": ",",
  "patterns": [
    {
      "type": "measurement_data",
      "description": "Numeric measurements with units",
      "examples": ["123.45 mg/mL", "0.234 AU"],
      "confidence": 0.9
    }
  ],
  "instrumentType": "HPLC",
  "dataTypes": ["concentration", "absorbance", "time"]
}`;
  }

  private parseClaudeResponse(response: string): any {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (error) {
      console.warn('Failed to parse Claude response as JSON:', error);
    }
    return {};
  }

  private determineStructureType(buffer: Buffer): 'binary' | 'text' | 'structured' {
    const sample = buffer.toString('utf-8', 0, Math.min(1000, buffer.length));
    if (!this.isValidText(sample)) return 'binary';
    
    if (sample.includes(',') || sample.includes('\t') || sample.includes('<') || sample.includes('{')) {
      return 'structured';
    }
    return 'text';
  }

  private assessComplexity(buffer: Buffer, analysis: any): 'low' | 'medium' | 'high' {
    let score = 0;
    
    if (buffer.length > 1024 * 1024) score += 2; // Large file
    if (analysis.patterns?.length > 5) score += 2; // Many patterns
    if (analysis.dataTypes?.length > 10) score += 1; // Many data types
    if (analysis.format === 'unknown') score += 3; // Unknown format
    
    if (score >= 5) return 'high';
    if (score >= 2) return 'medium';
    return 'low';
  }

  private isValidText(text: string): boolean {
    const controlChars = text.match(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]/g);
    return !controlChars || controlChars.length < text.length * 0.1;
  }
}