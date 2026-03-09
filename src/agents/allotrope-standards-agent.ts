import { BaseAgent, AgentTask, AgentResult, AgentCapability } from './base-agent';
import { S3Client, GetObjectCommand, ListObjectsV2Command } from '@aws-sdk/client-s3';

export interface ASMTemplate {
  id: string;
  name: string;
  version: string;
  schemaVersion: string;
  content: string;
  checksum: string;
  lastUpdated: Date;
  source: 'allotrope' | 'custom';
}

export interface SchemaValidationRule {
  id: string;
  schemaVersion: string;
  ruleName: string;
  ruleType: 'structure' | 'format' | 'content' | 'metadata';
  constraint: any;
  severity: 'error' | 'warning' | 'info';
  message: string;
}

export interface StandardsQuery {
  schemaVersion?: string;
  templateType?: string;
  instrumentType?: string;
  dataTypes?: string[];
}

export class AllotropeStandardsAgent extends BaseAgent {
  private s3Client: S3Client;
  private allotropeBucket: string;

  constructor(allotropeBucket: string = 'asm-allotrope-standards') {
    const capabilities: AgentCapability[] = [
      {
        name: 'get_asm_template',
        description: 'Get official ASM template from Allotrope Foundation',
        inputSchema: {
          type: 'object',
          properties: {
            schemaVersion: { type: 'string' },
            templateType: { type: 'string' },
            instrumentType: { type: 'string' }
          }
        },
        outputSchema: {
          type: 'object',
          properties: {
            template: { type: 'object' },
            validationRules: { type: 'array' }
          }
        }
      },
      {
        name: 'validate_asm_compliance',
        description: 'Validate generated ASM against official standards',
        inputSchema: {
          type: 'object',
          properties: {
            asmData: { type: 'object' },
            schemaVersion: { type: 'string' }
          }
        },
        outputSchema: {
          type: 'object',
          properties: {
            isCompliant: { type: 'boolean' },
            violations: { type: 'array' },
            warnings: { type: 'array' }
          }
        }
      }
    ];

    super('allotrope-standards-agent', 'Allotrope Standards Agent', capabilities);
    this.s3Client = new S3Client({ region: 'us-east-1' });
    this.allotropeBucket = allotropeBucket;
  }

  async execute(task: AgentTask): Promise<AgentResult> {
    try {
      switch (task.type) {
        case 'get_asm_template':
          return await this.getASMTemplate(task);
        case 'validate_asm_compliance':
          return await this.validateASMCompliance(task);
        default:
          return this.createResult(task, false, null, `Unknown task type: ${task.type}`);
      }
    } catch (error) {
      return this.createResult(task, false, null, error instanceof Error ? error.message : 'Unknown error');
    }
  }

  private async getASMTemplate(task: AgentTask): Promise<AgentResult> {
    const query = task.input as StandardsQuery;
    
    // Find best matching template
    const template = await this.findBestTemplate(query);
    if (!template) {
      return this.createResult(task, false, null, 'No matching ASM template found');
    }

    // Get validation rules for the schema version
    const validationRules = await this.getValidationRules(template.schemaVersion);

    // Use Claude to provide template guidance
    const guidancePrompt = this.buildTemplateGuidancePrompt(template, query);
    const guidance = await this.invokeClaude(guidancePrompt);

    return this.createResult(task, true, {
      template,
      validationRules,
      guidance: this.parseGuidance(guidance),
      schemaVersion: template.schemaVersion
    });
  }

  private async validateASMCompliance(task: AgentTask): Promise<AgentResult> {
    const { asmData, schemaVersion } = task.input;
    
    // Get validation rules for schema version
    const validationRules = await this.getValidationRules(schemaVersion);
    
    // Use Claude to validate compliance
    const validationPrompt = this.buildValidationPrompt(asmData, validationRules, schemaVersion);
    const validationResponse = await this.invokeClaude(validationPrompt, 6000);
    
    const validation = this.parseValidationResponse(validationResponse);
    
    return this.createResult(task, true, {
      isCompliant: validation.isCompliant,
      violations: validation.violations || [],
      warnings: validation.warnings || [],
      score: validation.score || 0,
      recommendations: validation.recommendations || []
    });
  }

  private async findBestTemplate(query: StandardsQuery): Promise<ASMTemplate | null> {
    try {
      const templates = await this.getAllTemplates();
      
      // Score templates based on query match
      const scoredTemplates = templates.map(template => ({
        template,
        score: this.scoreTemplateMatch(template, query)
      }));
      
      // Sort by score and return best match
      scoredTemplates.sort((a, b) => b.score - a.score);
      
      return scoredTemplates.length > 0 ? scoredTemplates[0].template : null;
    } catch (error) {
      console.error('Failed to find best template:', error);
      return null;
    }
  }

  private async getAllTemplates(): Promise<ASMTemplate[]> {
    const response = await this.s3Client.send(new ListObjectsV2Command({
      Bucket: this.allotropeBucket,
      Prefix: 'allotrope/templates/'
    }));

    const templates: ASMTemplate[] = [];
    
    for (const object of response.Contents || []) {
      if (object.Key?.endsWith('.json')) {
        try {
          const template = await this.loadTemplate(object.Key);
          if (template) {
            templates.push(template);
          }
        } catch (error) {
          console.warn(`Failed to load template ${object.Key}:`, error);
        }
      }
    }
    
    return templates;
  }

  private async loadTemplate(key: string): Promise<ASMTemplate | null> {
    try {
      const response = await this.s3Client.send(new GetObjectCommand({
        Bucket: this.allotropeBucket,
        Key: key
      }));
      
      if (!response.Body) return null;
      
      const content = await response.Body.transformToString();
      return JSON.parse(content) as ASMTemplate;
    } catch (error) {
      console.error(`Failed to load template ${key}:`, error);
      return null;
    }
  }

  private async getValidationRules(schemaVersion: string): Promise<SchemaValidationRule[]> {
    try {
      const response = await this.s3Client.send(new ListObjectsV2Command({
        Bucket: this.allotropeBucket,
        Prefix: `allotrope/schemas/${schemaVersion}/`
      }));

      const rules: SchemaValidationRule[] = [];
      
      for (const object of response.Contents || []) {
        if (object.Key?.endsWith('.json')) {
          try {
            const ruleSet = await this.loadValidationRules(object.Key);
            if (ruleSet) {
              rules.push(...ruleSet);
            }
          } catch (error) {
            console.warn(`Failed to load validation rules ${object.Key}:`, error);
          }
        }
      }
      
      return rules;
    } catch (error) {
      console.error('Failed to get validation rules:', error);
      return [];
    }
  }

  private async loadValidationRules(key: string): Promise<SchemaValidationRule[] | null> {
    try {
      const response = await this.s3Client.send(new GetObjectCommand({
        Bucket: this.allotropeBucket,
        Key: key
      }));
      
      if (!response.Body) return null;
      
      const content = await response.Body.transformToString();
      const data = JSON.parse(content);
      
      return Array.isArray(data) ? data : [data];
    } catch (error) {
      console.error(`Failed to load validation rules ${key}:`, error);
      return null;
    }
  }

  private scoreTemplateMatch(template: ASMTemplate, query: StandardsQuery): number {
    let score = 0;
    
    // Schema version match (highest priority)
    if (query.schemaVersion && template.schemaVersion === query.schemaVersion) {
      score += 50;
    }
    
    // Template type match
    if (query.templateType && template.name.toLowerCase().includes(query.templateType.toLowerCase())) {
      score += 30;
    }
    
    // Instrument type match
    if (query.instrumentType && template.content.toLowerCase().includes(query.instrumentType.toLowerCase())) {
      score += 20;
    }
    
    // Data types match
    if (query.dataTypes && query.dataTypes.length > 0) {
      const matchingTypes = query.dataTypes.filter(type =>
        template.content.toLowerCase().includes(type.toLowerCase())
      );
      score += matchingTypes.length * 5;
    }
    
    return score;
  }

  private buildTemplateGuidancePrompt(template: ASMTemplate, query: StandardsQuery): string {
    return `Provide guidance for using this official Allotrope ASM template:

Template: ${template.name} (${template.schemaVersion})
Content: ${template.content}

Query Context:
${JSON.stringify(query, null, 2)}

Provide specific guidance on:
1. How to properly structure data according to this template
2. Required fields and their formats
3. Best practices for metadata and provenance
4. Common mistakes to avoid
5. Instrument-specific considerations

Return as JSON:
{
  "structureGuidance": "...",
  "requiredFields": [...],
  "bestPractices": [...],
  "commonMistakes": [...],
  "instrumentSpecific": "..."
}`;
  }

  private buildValidationPrompt(asmData: any, rules: SchemaValidationRule[], schemaVersion: string): string {
    return `Validate this ASM data against official Allotrope standards:

ASM Data:
${JSON.stringify(asmData, null, 2)}

Schema Version: ${schemaVersion}

Validation Rules:
${rules.map(rule => `- ${rule.ruleName}: ${rule.message} (${rule.severity})`).join('\n')}

Perform comprehensive validation checking:
1. Required field presence and format
2. Data type compliance
3. Metadata completeness
4. Provenance and traceability
5. Scientific unit consistency
6. Schema version compatibility

Return validation results as JSON:
{
  "isCompliant": true/false,
  "score": 0-100,
  "violations": [
    {
      "rule": "rule-id",
      "severity": "error",
      "message": "description",
      "field": "field.path",
      "value": "actual value"
    }
  ],
  "warnings": [...],
  "recommendations": [...]
}`;
  }

  private parseGuidance(response: string): any {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (error) {
      console.warn('Failed to parse template guidance:', error);
    }
    return {};
  }

  private parseValidationResponse(response: string): any {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (error) {
      console.warn('Failed to parse validation response:', error);
    }
    return {
      isCompliant: false,
      violations: [],
      warnings: [],
      score: 0,
      recommendations: []
    };
  }
}