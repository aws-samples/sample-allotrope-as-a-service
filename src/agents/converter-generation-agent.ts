import { BaseAgent, AgentTask, AgentResult, AgentCapability } from './base-agent';
import { FileAnalysisOutput } from './file-analysis-agent';

export interface ConverterGenerationInput {
  fileAnalysis: FileAnalysisOutput;
  sampleFiles: Array<{
    filename: string;
    content: Buffer;
  }>;
  targetSchema: string;
  requirements?: string[];
}

export interface GeneratedConverter {
  id: string;
  code: string;
  language: 'typescript' | 'python';
  metadata: {
    name: string;
    description: string;
    supportedFormats: string[];
    confidence: number;
    complexity: 'low' | 'medium' | 'high';
  };
  tests: Array<{
    name: string;
    input: any;
    expectedOutput: any;
  }>;
}

export class ConverterGenerationAgent extends BaseAgent {
  constructor() {
    const capabilities: AgentCapability[] = [
      {
        name: 'generate_converter',
        description: 'Generate converter code based on file analysis',
        inputSchema: {
          type: 'object',
          properties: {
            fileAnalysis: { type: 'object' },
            sampleFiles: { type: 'array' },
            targetSchema: { type: 'string' },
            requirements: { type: 'array' }
          },
          required: ['fileAnalysis', 'targetSchema']
        },
        outputSchema: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            code: { type: 'string' },
            language: { type: 'string' },
            metadata: { type: 'object' },
            tests: { type: 'array' }
          }
        }
      }
    ];

    super('converter-generation-agent', 'Converter Generation Agent', capabilities);
  }

  async execute(task: AgentTask): Promise<AgentResult> {
    try {
      switch (task.type) {
        case 'generate_converter':
          return await this.generateConverter(task);
        default:
          return this.createResult(task, false, null, `Unknown task type: ${task.type}`);
      }
    } catch (error) {
      return this.createResult(task, false, null, error instanceof Error ? error.message : 'Unknown error');
    }
  }

  private async generateConverter(task: AgentTask): Promise<AgentResult> {
    const input = task.input as ConverterGenerationInput;
    
    // Determine best language for the converter
    const language = this.selectLanguage(input.fileAnalysis);
    
    // Generate converter code
    const prompt = this.buildGenerationPrompt(input, language);
    const generatedCode = await this.invokeClaude(prompt, 6000);
    
    // Extract code from response
    const code = this.extractCode(generatedCode, language);
    
    // Generate tests
    const tests = await this.generateTests(input, code, language);
    
    const converter: GeneratedConverter = {
      id: `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      code,
      language,
      metadata: {
        name: `${input.fileAnalysis.format.toUpperCase()} to ASM Converter`,
        description: `Converts ${input.fileAnalysis.format} files to ASM format`,
        supportedFormats: [input.fileAnalysis.format],
        confidence: this.calculateConfidence(input.fileAnalysis),
        complexity: input.fileAnalysis.metadata.complexity
      },
      tests
    };

    return this.createResult(task, true, converter);
  }

  private selectLanguage(analysis: FileAnalysisOutput): 'typescript' | 'python' {
    // Use Python for complex scientific data processing
    if (analysis.metadata.complexity === 'high') return 'python';
    if (analysis.format === 'binary') return 'python';
    if (analysis.metadata.dataTypes.some(type => 
      ['spectroscopy', 'chromatography', 'mass_spec'].includes(type)
    )) return 'python';
    
    // Use TypeScript for simpler formats and web integration
    return 'typescript';
  }

  private buildGenerationPrompt(input: ConverterGenerationInput, language: 'typescript' | 'python'): string {
    const { fileAnalysis, targetSchema } = input;
    
    const basePrompt = `Generate a ${language} converter for laboratory data files.

File Analysis:
- Format: ${fileAnalysis.format}
- Structure: ${JSON.stringify(fileAnalysis.structure, null, 2)}
- Patterns: ${JSON.stringify(fileAnalysis.patterns, null, 2)}
- Data Types: ${fileAnalysis.metadata.dataTypes.join(', ')}
- Instrument: ${fileAnalysis.metadata.instrumentType || 'Unknown'}

Target Schema: ${targetSchema}

Requirements:
- Convert to ASM (Allotrope Simple Model) format
- Preserve all scientific data with proper units
- Handle errors gracefully
- Include comprehensive validation
- Generate proper metadata and provenance`;

    if (language === 'typescript') {
      return `${basePrompt}

Generate a TypeScript class that extends this base:

\`\`\`typescript
export abstract class BaseConverter {
  abstract convert(input: Buffer, options?: any): Promise<ASMOutput>;
  abstract validate(input: Buffer): ValidationResult;
}

interface ASMOutput {
  version: string;
  schema: string;
  data: {
    measurements: Measurement[];
    samples: Sample[];
    methods: Method[];
    instruments: Instrument[];
  };
  metadata: {
    generatedAt: string;
    sourceFile: string;
    converter: string;
  };
}
\`\`\`

Provide complete TypeScript code with proper types and error handling.`;
    } else {
      return `${basePrompt}

Generate a Python class with these methods:

\`\`\`python
class BaseConverter:
    def convert(self, input_data: bytes, options: dict = None) -> dict:
        pass
    
    def validate(self, input_data: bytes) -> dict:
        pass
\`\`\`

Use pandas, numpy, and other scientific libraries as needed. Return ASM-compliant dictionary structure.`;
    }
  }

  private extractCode(response: string, language: 'typescript' | 'python'): string {
    const codeBlockRegex = language === 'typescript' 
      ? /```typescript\n([\s\S]*?)\n```/
      : /```python\n([\s\S]*?)\n```/;
    
    const match = response.match(codeBlockRegex);
    if (match) {
      return match[1].trim();
    }
    
    // Fallback: try to extract any code block
    const genericMatch = response.match(/```[\w]*\n([\s\S]*?)\n```/);
    return genericMatch ? genericMatch[1].trim() : response;
  }

  private async generateTests(
    input: ConverterGenerationInput, 
    code: string, 
    language: 'typescript' | 'python'
  ): Promise<Array<{ name: string; input: any; expectedOutput: any }>> {
    const testPrompt = `Generate test cases for this ${language} converter:

${code}

File format: ${input.fileAnalysis.format}
Sample patterns: ${JSON.stringify(input.fileAnalysis.patterns)}

Generate 3-5 test cases with:
1. Valid input data
2. Expected ASM output structure
3. Edge cases (empty data, malformed data)

Return as JSON array:
[
  {
    "name": "test_valid_data",
    "input": "sample input data",
    "expectedOutput": { "version": "1.0", "data": {...} }
  }
]`;

    const testResponse = await this.invokeClaude(testPrompt, 3000);
    
    try {
      const jsonMatch = testResponse.match(/\[[\s\S]*\]/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (error) {
      console.warn('Failed to parse test cases:', error);
    }
    
    // Fallback: basic test structure
    return [
      {
        name: 'test_basic_conversion',
        input: 'sample data',
        expectedOutput: {
          version: '1.0',
          schema: input.targetSchema,
          data: { measurements: [], samples: [] }
        }
      }
    ];
  }

  private calculateConfidence(analysis: FileAnalysisOutput): number {
    let confidence = analysis.confidence;
    
    // Adjust based on complexity
    if (analysis.metadata.complexity === 'high') confidence *= 0.8;
    if (analysis.metadata.complexity === 'low') confidence *= 1.1;
    
    // Adjust based on format recognition
    if (analysis.format === 'unknown') confidence *= 0.5;
    
    // Adjust based on patterns
    if (analysis.patterns.length > 0) {
      const avgPatternConfidence = analysis.patterns.reduce((sum, p) => sum + p.confidence, 0) / analysis.patterns.length;
      confidence = (confidence + avgPatternConfidence) / 2;
    }
    
    return Math.min(Math.max(confidence, 0.1), 0.95);
  }
}