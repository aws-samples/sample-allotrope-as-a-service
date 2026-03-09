import { BaseAgent, AgentTask, AgentResult, AgentCapability } from './base-agent';
import { FileAnalysisOutput } from './file-analysis-agent';
import { GeneratedConverter } from './converter-generation-agent';

export interface EnhancedConverterGenerationInput {
  fileAnalysis: FileAnalysisOutput;
  instrumentKnowledge?: {
    bestMatch: {
      instrumentId: string;
      confidence: number;
      reasoning: string;
    };
    fileFormatSpecs: {
      structure: string;
      parsingInstructions: string;
      sampleCode: string;
    };
    dataTypeMappings: Array<{
      sourceField: string;
      asmField: string;
      unit: string;
      conversion: string;
    }>;
    validationRules: any[];
    calibrationFactors: Record<string, number>;
    commonIssues: string[];
  };
  sampleFiles: Array<{
    filename: string;
    content: Buffer;
  }>;
  targetSchema: string;
  requirements?: string[];
}

export class EnhancedConverterGenerationAgent extends BaseAgent {
  constructor() {
    const capabilities: AgentCapability[] = [
      {
        name: 'generate_knowledge_based_converter',
        description: 'Generate converter using instrument documentation knowledge',
        inputSchema: {
          type: 'object',
          properties: {
            fileAnalysis: { type: 'object' },
            instrumentKnowledge: { type: 'object' },
            sampleFiles: { type: 'array' },
            targetSchema: { type: 'string' }
          },
          required: ['fileAnalysis', 'targetSchema']
        },
        outputSchema: {
          type: 'object',
          properties: {
            converter: { type: 'object' },
            knowledgeUsed: { type: 'object' },
            confidence: { type: 'number' }
          }
        }
      }
    ];

    super('enhanced-converter-generation-agent', 'Enhanced Converter Generation Agent', capabilities);
  }

  async execute(task: AgentTask): Promise<AgentResult> {
    try {
      switch (task.type) {
        case 'generate_knowledge_based_converter':
          return await this.generateKnowledgeBasedConverter(task);
        default:
          return this.createResult(task, false, null, `Unknown task type: ${task.type}`);
      }
    } catch (error) {
      return this.createResult(task, false, null, error instanceof Error ? error.message : 'Unknown error');
    }
  }

  private async generateKnowledgeBasedConverter(task: AgentTask): Promise<AgentResult> {
    const input = task.input as EnhancedConverterGenerationInput;
    
    // Determine language based on complexity and knowledge
    const language = this.selectLanguageWithKnowledge(input);
    
    // Build enhanced prompt with instrument knowledge
    const prompt = this.buildKnowledgeEnhancedPrompt(input, language);
    
    // Generate converter with more context
    const generatedCode = await this.invokeClaude(prompt, 8000);
    const code = this.extractCode(generatedCode, language);
    
    // Generate tests with knowledge-based validation
    const tests = await this.generateKnowledgeBasedTests(input, code, language);
    
    const converter: GeneratedConverter = {
      id: `enhanced-conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      code,
      language,
      metadata: {
        name: this.generateConverterName(input),
        description: this.generateConverterDescription(input),
        supportedFormats: [input.fileAnalysis.format],
        confidence: this.calculateEnhancedConfidence(input),
        complexity: input.fileAnalysis.metadata.complexity
      },
      tests
    };

    return this.createResult(task, true, {
      converter,
      knowledgeUsed: input.instrumentKnowledge || {},
      confidence: converter.metadata.confidence
    });
  }

  private selectLanguageWithKnowledge(input: EnhancedConverterGenerationInput): 'typescript' | 'python' {
    const { fileAnalysis, instrumentKnowledge } = input;
    
    // If we have specific instrument knowledge, use it to make better decisions
    if (instrumentKnowledge?.fileFormatSpecs?.sampleCode) {
      const sampleCode = instrumentKnowledge.fileFormatSpecs.sampleCode.toLowerCase();
      if (sampleCode.includes('import pandas') || sampleCode.includes('numpy')) {
        return 'python';
      }
    }
    
    // Check for scientific data types that benefit from Python
    const scientificDataTypes = ['spectroscopy', 'chromatography', 'mass_spec', 'nmr', 'ftir'];
    if (fileAnalysis.metadata.dataTypes.some(type => scientificDataTypes.includes(type))) {
      return 'python';
    }
    
    // Default logic
    if (fileAnalysis.metadata.complexity === 'high') return 'python';
    if (fileAnalysis.format === 'binary') return 'python';
    
    return 'typescript';
  }

  private buildKnowledgeEnhancedPrompt(input: EnhancedConverterGenerationInput, language: 'typescript' | 'python'): string {
    const { fileAnalysis, instrumentKnowledge, targetSchema } = input;
    
    let prompt = `Generate a ${language} converter for laboratory instrument data with SPECIFIC INSTRUMENT KNOWLEDGE.

File Analysis:
${JSON.stringify(fileAnalysis, null, 2)}

Target Schema: ${targetSchema}`;

    // Add instrument-specific knowledge if available
    if (instrumentKnowledge) {
      prompt += `

INSTRUMENT DOCUMENTATION KNOWLEDGE:
Best Match: ${instrumentKnowledge.bestMatch?.instrumentId} (confidence: ${instrumentKnowledge.bestMatch?.confidence})
Reasoning: ${instrumentKnowledge.bestMatch?.reasoning}

File Format Specifications:
${instrumentKnowledge.fileFormatSpecs?.structure}

Parsing Instructions:
${instrumentKnowledge.fileFormatSpecs?.parsingInstructions}

Data Type Mappings:
${instrumentKnowledge.dataTypeMappings?.map(mapping => 
  `- ${mapping.sourceField} → ${mapping.asmField} (${mapping.unit}) [${mapping.conversion}]`
).join('\n')}

Calibration Factors:
${JSON.stringify(instrumentKnowledge.calibrationFactors, null, 2)}

Validation Rules:
${instrumentKnowledge.validationRules?.map(rule => `- ${JSON.stringify(rule)}`).join('\n')}

Common Issues to Handle:
${instrumentKnowledge.commonIssues?.map(issue => `- ${issue}`).join('\n')}

Sample Code Reference:
${instrumentKnowledge.fileFormatSpecs?.sampleCode}`;
    }

    prompt += `

REQUIREMENTS:
1. Use the instrument documentation knowledge for PRECISE data extraction
2. Implement the specified data type mappings EXACTLY
3. Apply calibration factors where indicated
4. Include all validation rules from the documentation
5. Handle the common issues mentioned in the knowledge base
6. Preserve instrument-specific metadata and provenance
7. Generate ASM-compliant output with proper units and measurements

Generate a complete, production-ready converter that leverages this instrument knowledge.`;

    if (language === 'typescript') {
      prompt += `

Generate TypeScript class extending BaseConverter with:
- Precise parsing based on instrument documentation
- Exact data type mappings from knowledge base
- Calibration factor applications
- Comprehensive validation using documented rules
- Error handling for known common issues`;
    } else {
      prompt += `

Generate Python class with:
- Scientific libraries (pandas, numpy) for data processing
- Instrument-specific parsing logic
- Unit conversion using documented factors
- Validation based on instrument specifications
- Error handling for documented edge cases`;
    }

    return prompt;
  }

  private generateConverterName(input: EnhancedConverterGenerationInput): string {
    const { fileAnalysis, instrumentKnowledge } = input;
    
    if (instrumentKnowledge?.bestMatch?.instrumentId) {
      return `${instrumentKnowledge.bestMatch.instrumentId} to ASM Converter`;
    }
    
    return `${fileAnalysis.format.toUpperCase()} to ASM Converter (${fileAnalysis.metadata.instrumentType || 'Generic'})`;
  }

  private generateConverterDescription(input: EnhancedConverterGenerationInput): string {
    const { fileAnalysis, instrumentKnowledge } = input;
    
    let description = `Converts ${fileAnalysis.format} files to ASM format`;
    
    if (instrumentKnowledge?.bestMatch?.instrumentId) {
      description += ` using ${instrumentKnowledge.bestMatch.instrumentId} instrument documentation`;
    }
    
    if (fileAnalysis.metadata.instrumentType) {
      description += ` for ${fileAnalysis.metadata.instrumentType} instruments`;
    }
    
    return description;
  }

  private calculateEnhancedConfidence(input: EnhancedConverterGenerationInput): number {
    let confidence = input.fileAnalysis.confidence;
    
    // Boost confidence if we have good instrument knowledge
    if (input.instrumentKnowledge?.bestMatch?.confidence) {
      const knowledgeConfidence = input.instrumentKnowledge.bestMatch.confidence;
      confidence = (confidence + knowledgeConfidence) / 2;
      
      // Additional boost for having specific mappings and validation rules
      if (input.instrumentKnowledge.dataTypeMappings?.length > 0) {
        confidence += 0.1;
      }
      
      if (input.instrumentKnowledge.validationRules?.length > 0) {
        confidence += 0.1;
      }
      
      if (input.instrumentKnowledge.fileFormatSpecs?.sampleCode) {
        confidence += 0.15;
      }
    } else {
      // Reduce confidence if no instrument knowledge available
      confidence *= 0.8;
    }
    
    return Math.min(Math.max(confidence, 0.1), 0.98);
  }

  private async generateKnowledgeBasedTests(
    input: EnhancedConverterGenerationInput,
    code: string,
    language: 'typescript' | 'python'
  ): Promise<Array<{ name: string; input: any; expectedOutput: any }>> {
    const testPrompt = `Generate comprehensive test cases for this ${language} converter that uses instrument documentation:

Generated Code:
${code}

Instrument Knowledge:
${JSON.stringify(input.instrumentKnowledge, null, 2)}

Generate test cases that validate:
1. Correct data type mappings from instrument documentation
2. Proper calibration factor applications
3. Validation rule enforcement
4. Error handling for documented common issues
5. Metadata preservation and provenance

Return as JSON array with realistic test data based on the instrument specifications.`;

    const testResponse = await this.invokeClaude(testPrompt, 4000);
    
    try {
      const jsonMatch = testResponse.match(/\[[\s\S]*\]/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (error) {
      console.warn('Failed to parse knowledge-based test cases:', error);
    }
    
    // Fallback with enhanced test structure
    return [
      {
        name: 'test_instrument_specific_conversion',
        input: 'instrument-specific sample data',
        expectedOutput: {
          version: '1.0',
          schema: input.targetSchema,
          data: {
            measurements: [],
            samples: [],
            instruments: [{
              id: input.instrumentKnowledge?.bestMatch?.instrumentId || 'unknown',
              calibrationFactors: input.instrumentKnowledge?.calibrationFactors || {}
            }]
          }
        }
      }
    ];
  }

  private extractCode(response: string, language: 'typescript' | 'python'): string {
    const codeBlockRegex = language === 'typescript' 
      ? /```typescript\n([\s\S]*?)\n```/
      : /```python\n([\s\S]*?)\n```/;
    
    const match = response.match(codeBlockRegex);
    if (match) {
      return match[1].trim();
    }
    
    const genericMatch = response.match(/```[\w]*\n([\s\S]*?)\n```/);
    return genericMatch ? genericMatch[1].trim() : response;
  }
}