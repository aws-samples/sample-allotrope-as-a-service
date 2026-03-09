import { BaseAgent, AgentTask, AgentResult, AgentCapability } from './base-agent';
import { S3Client, GetObjectCommand, ListObjectsV2Command } from '@aws-sdk/client-s3';

export interface InstrumentDocumentation {
  instrumentId: string;
  manufacturer: string;
  model: string;
  version?: string;
  documentation: {
    fileFormats: Array<{
      extension: string;
      description: string;
      structure: any;
      sampleData?: string;
    }>;
    dataTypes: Array<{
      name: string;
      unit: string;
      range?: { min: number; max: number };
      precision?: number;
      description: string;
    }>;
    calibration: {
      procedures: string[];
      standards: string[];
      factors: Record<string, number>;
    };
    metadata: {
      requiredFields: string[];
      optionalFields: string[];
      defaultValues: Record<string, any>;
    };
    validationRules: Array<{
      field: string;
      rule: string;
      message: string;
    }>;
  };
  lastUpdated: Date;
  source: string;
}

export interface KnowledgeQuery {
  instrumentType?: string;
  manufacturer?: string;
  model?: string;
  fileFormat?: string;
  dataTypes?: string[];
  query: string;
}

export class KnowledgeBaseAgent extends BaseAgent {
  private s3Client: S3Client;
  private knowledgeBaseBucket: string;

  constructor(knowledgeBaseBucket: string = 'asm-instrument-knowledge') {
    const capabilities: AgentCapability[] = [
      {
        name: 'query_instrument_docs',
        description: 'Query instrument documentation for converter generation',
        inputSchema: {
          type: 'object',
          properties: {
            instrumentType: { type: 'string' },
            manufacturer: { type: 'string' },
            model: { type: 'string' },
            fileFormat: { type: 'string' },
            query: { type: 'string' }
          },
          required: ['query']
        },
        outputSchema: {
          type: 'object',
          properties: {
            relevantDocs: { type: 'array' },
            recommendations: { type: 'object' },
            confidence: { type: 'number' }
          }
        }
      },
      {
        name: 'extract_converter_specs',
        description: 'Extract specific converter specifications from documentation',
        inputSchema: { type: 'object' },
        outputSchema: { type: 'object' }
      }
    ];

    super('knowledge-base-agent', 'Knowledge Base Agent', capabilities);
    this.s3Client = new S3Client({ region: 'us-east-1' });
    this.knowledgeBaseBucket = knowledgeBaseBucket;
  }

  async execute(task: AgentTask): Promise<AgentResult> {
    try {
      switch (task.type) {
        case 'query_instrument_docs':
          return await this.queryInstrumentDocs(task);
        case 'extract_converter_specs':
          return await this.extractConverterSpecs(task);
        default:
          return this.createResult(task, false, null, `Unknown task type: ${task.type}`);
      }
    } catch (error) {
      return this.createResult(task, false, null, error instanceof Error ? error.message : 'Unknown error');
    }
  }

  private async queryInstrumentDocs(task: AgentTask): Promise<AgentResult> {
    const query = task.input as KnowledgeQuery;
    
    // Find relevant documentation
    const relevantDocs = await this.findRelevantDocumentation(query);
    
    // Use Claude to analyze documentation and provide recommendations
    const analysisPrompt = this.buildAnalysisPrompt(query, relevantDocs);
    const claudeResponse = await this.invokeClaude(analysisPrompt, 6000);
    
    const recommendations = this.parseRecommendations(claudeResponse);
    
    return this.createResult(task, true, {
      relevantDocs,
      recommendations,
      confidence: this.calculateConfidence(relevantDocs, query)
    });
  }

  private async findRelevantDocumentation(query: KnowledgeQuery): Promise<InstrumentDocumentation[]> {
    try {
      // List all documentation files
      const listCommand = new ListObjectsV2Command({
        Bucket: this.knowledgeBaseBucket,
        Prefix: 'instruments/'
      });
      
      const response = await this.s3Client.send(listCommand);
      const docs: InstrumentDocumentation[] = [];
      
      // Load and filter relevant documentation
      for (const object of response.Contents || []) {
        if (object.Key?.endsWith('.json')) {
          try {
            const doc = await this.loadDocumentation(object.Key);
            if (doc && this.isRelevant(doc, query)) {
              docs.push(doc);
            }
          } catch (error) {
            console.warn(`Failed to load documentation ${object.Key}:`, error);
          }
        }
      }
      
      return docs.sort((a, b) => this.calculateRelevanceScore(b, query) - this.calculateRelevanceScore(a, query));
    } catch (error) {
      console.error('Failed to find relevant documentation:', error);
      return [];
    }
  }

  private async loadDocumentation(key: string): Promise<InstrumentDocumentation | null> {
    try {
      const command = new GetObjectCommand({
        Bucket: this.knowledgeBaseBucket,
        Key: key
      });
      
      const response = await this.s3Client.send(command);
      if (!response.Body) return null;
      
      const content = await response.Body.transformToString();
      return JSON.parse(content) as InstrumentDocumentation;
    } catch (error) {
      console.error(`Failed to load documentation ${key}:`, error);
      return null;
    }
  }

  private isRelevant(doc: InstrumentDocumentation, query: KnowledgeQuery): boolean {
    // Check manufacturer match
    if (query.manufacturer && doc.manufacturer.toLowerCase().includes(query.manufacturer.toLowerCase())) {
      return true;
    }
    
    // Check model match
    if (query.model && doc.model.toLowerCase().includes(query.model.toLowerCase())) {
      return true;
    }
    
    // Check file format match
    if (query.fileFormat) {
      const hasFormat = doc.documentation.fileFormats.some(format => 
        format.extension.toLowerCase() === query.fileFormat?.toLowerCase()
      );
      if (hasFormat) return true;
    }
    
    // Check data types match
    if (query.dataTypes && query.dataTypes.length > 0) {
      const hasDataTypes = query.dataTypes.some(queryType =>
        doc.documentation.dataTypes.some(docType =>
          docType.name.toLowerCase().includes(queryType.toLowerCase())
        )
      );
      if (hasDataTypes) return true;
    }
    
    return false;
  }

  private calculateRelevanceScore(doc: InstrumentDocumentation, query: KnowledgeQuery): number {
    let score = 0;
    
    // Manufacturer match
    if (query.manufacturer && doc.manufacturer.toLowerCase().includes(query.manufacturer.toLowerCase())) {
      score += 10;
    }
    
    // Model match
    if (query.model && doc.model.toLowerCase().includes(query.model.toLowerCase())) {
      score += 15;
    }
    
    // File format match
    if (query.fileFormat) {
      const formatMatch = doc.documentation.fileFormats.some(format => 
        format.extension.toLowerCase() === query.fileFormat?.toLowerCase()
      );
      if (formatMatch) score += 20;
    }
    
    // Data types overlap
    if (query.dataTypes) {
      const overlap = query.dataTypes.filter(queryType =>
        doc.documentation.dataTypes.some(docType =>
          docType.name.toLowerCase().includes(queryType.toLowerCase())
        )
      ).length;
      score += overlap * 5;
    }
    
    return score;
  }

  private buildAnalysisPrompt(query: KnowledgeQuery, docs: InstrumentDocumentation[]): string {
    return `Analyze instrument documentation to provide converter generation recommendations:

Query: ${JSON.stringify(query, null, 2)}

Available Documentation:
${docs.map(doc => `
Instrument: ${doc.manufacturer} ${doc.model}
File Formats: ${doc.documentation.fileFormats.map(f => f.extension).join(', ')}
Data Types: ${doc.documentation.dataTypes.map(d => `${d.name} (${d.unit})`).join(', ')}
Required Fields: ${doc.documentation.metadata.requiredFields.join(', ')}
Validation Rules: ${doc.documentation.validationRules.length} rules
`).join('\n')}

Provide recommendations for converter generation:
1. Best matching instrument documentation
2. Specific file format handling instructions
3. Data type mappings and unit conversions
4. Required metadata fields and validation rules
5. Calibration factors and corrections
6. Sample code snippets for data extraction
7. Common pitfalls and error handling

Return JSON format:
{
  "bestMatch": {
    "instrumentId": "...",
    "confidence": 0.95,
    "reasoning": "..."
  },
  "fileFormatSpecs": {
    "structure": "...",
    "parsingInstructions": "...",
    "sampleCode": "..."
  },
  "dataTypeMappings": [
    {
      "sourceField": "...",
      "asmField": "...",
      "unit": "...",
      "conversion": "..."
    }
  ],
  "validationRules": [...],
  "calibrationFactors": {...},
  "commonIssues": [...]
}`;
  }

  private parseRecommendations(response: string): any {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (error) {
      console.warn('Failed to parse recommendations:', error);
    }
    
    return {
      bestMatch: null,
      fileFormatSpecs: {},
      dataTypeMappings: [],
      validationRules: [],
      calibrationFactors: {},
      commonIssues: []
    };
  }

  private async extractConverterSpecs(task: AgentTask): Promise<AgentResult> {
    const { documentationId, requirements } = task.input;
    
    const doc = await this.loadDocumentation(`instruments/${documentationId}.json`);
    if (!doc) {
      return this.createResult(task, false, null, 'Documentation not found');
    }
    
    const extractionPrompt = `Extract specific converter specifications from this instrument documentation:

${JSON.stringify(doc, null, 2)}

Requirements: ${JSON.stringify(requirements, null, 2)}

Generate detailed converter specifications including:
1. Exact parsing logic for each data field
2. Unit conversion formulas
3. Validation rules implementation
4. Error handling strategies
5. Metadata extraction procedures

Return as detailed JSON specification.`;

    const response = await this.invokeClaude(extractionPrompt, 8000);
    const specs = this.parseConverterSpecs(response);
    
    return this.createResult(task, true, specs);
  }

  private parseConverterSpecs(response: string): any {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (error) {
      console.warn('Failed to parse converter specs:', error);
    }
    return {};
  }

  private calculateConfidence(docs: InstrumentDocumentation[], query: KnowledgeQuery): number {
    if (docs.length === 0) return 0.1;
    
    const bestDoc = docs[0];
    const relevanceScore = this.calculateRelevanceScore(bestDoc, query);
    
    // Convert relevance score to confidence (0-1)
    const maxPossibleScore = 50; // Theoretical maximum
    return Math.min(relevanceScore / maxPossibleScore, 0.95);
  }
}