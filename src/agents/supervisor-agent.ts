import { BaseAgent, AgentTask, AgentResult, AgentCapability } from './base-agent';

export interface WorkflowPlan {
  id: string;
  steps: Array<{
    agentId: string;
    taskType: string;
    dependencies: string[];
    priority: number;
    estimatedDuration: number;
  }>;
  totalEstimatedTime: number;
  confidence: number;
}

export interface SupervisorInput {
  request: any;
  availableAgents: Array<{
    id: string;
    name: string;
    capabilities: string[];
    currentLoad: number;
  }>;
  constraints?: {
    maxDuration?: number;
    qualityThreshold?: number;
    budget?: number;
  };
}

export class SupervisorAgent extends BaseAgent {
  constructor() {
    const capabilities: AgentCapability[] = [
      {
        name: 'plan_workflow',
        description: 'Create intelligent workflow plans for conversion requests',
        inputSchema: {
          type: 'object',
          properties: {
            request: { type: 'object' },
            availableAgents: { type: 'array' },
            constraints: { type: 'object' }
          }
        },
        outputSchema: {
          type: 'object',
          properties: {
            plan: { type: 'object' },
            reasoning: { type: 'string' }
          }
        }
      },
      {
        name: 'monitor_execution',
        description: 'Monitor workflow execution and make adjustments',
        inputSchema: { type: 'object' },
        outputSchema: { type: 'object' }
      },
      {
        name: 'handle_failures',
        description: 'Handle agent failures and re-route workflows',
        inputSchema: { type: 'object' },
        outputSchema: { type: 'object' }
      }
    ];

    super('supervisor-agent', 'Supervisor Agent', capabilities);
  }

  async execute(task: AgentTask): Promise<AgentResult> {
    try {
      switch (task.type) {
        case 'plan_workflow':
          return await this.planWorkflow(task);
        case 'monitor_execution':
          return await this.monitorExecution(task);
        case 'handle_failures':
          return await this.handleFailures(task);
        default:
          return this.createResult(task, false, null, `Unknown task type: ${task.type}`);
      }
    } catch (error) {
      return this.createResult(task, false, null, error instanceof Error ? error.message : 'Unknown error');
    }
  }

  private async planWorkflow(task: AgentTask): Promise<AgentResult> {
    const input = task.input as SupervisorInput;
    
    const planningPrompt = this.buildPlanningPrompt(input);
    const claudeResponse = await this.invokeClaude(planningPrompt);
    const plan = this.parsePlan(claudeResponse);
    
    return this.createResult(task, true, {
      plan,
      reasoning: this.extractReasoning(claudeResponse)
    });
  }

  private buildPlanningPrompt(input: SupervisorInput): string {
    return `As a supervisor agent, create an optimal workflow plan for this conversion request:

Request: ${JSON.stringify(input.request, null, 2)}

Available Agents:
${input.availableAgents.map(agent => 
  `- ${agent.name} (${agent.id}): ${agent.capabilities.join(', ')} [Load: ${agent.currentLoad}%]`
).join('\n')}

Constraints: ${JSON.stringify(input.constraints || {}, null, 2)}

Create a workflow plan considering:
1. Agent capabilities and current load
2. Task dependencies and parallelization opportunities
3. Error handling and fallback strategies
4. Quality vs speed tradeoffs

Return JSON format:
{
  "plan": {
    "id": "workflow-123",
    "steps": [
      {
        "agentId": "file-analysis-agent",
        "taskType": "analyze_file_format",
        "dependencies": [],
        "priority": 1,
        "estimatedDuration": 30000,
        "parallelizable": false
      }
    ],
    "totalEstimatedTime": 60000,
    "confidence": 0.85
  },
  "reasoning": "Selected file analysis first because...",
  "alternatives": ["Alternative approach if primary fails"],
  "riskFactors": ["Complex binary format", "Large file size"]
}`;
  }

  private parsePlan(response: string): WorkflowPlan {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return parsed.plan;
      }
    } catch (error) {
      console.warn('Failed to parse workflow plan:', error);
    }
    
    // Fallback: basic sequential plan
    return {
      id: `fallback-${Date.now()}`,
      steps: [
        {
          agentId: 'file-analysis-agent',
          taskType: 'analyze_file_format',
          dependencies: [],
          priority: 1,
          estimatedDuration: 30000
        },
        {
          agentId: 'converter-generation-agent',
          taskType: 'generate_converter',
          dependencies: ['file-analysis-agent'],
          priority: 2,
          estimatedDuration: 60000
        }
      ],
      totalEstimatedTime: 90000,
      confidence: 0.5
    };
  }

  private async monitorExecution(task: AgentTask): Promise<AgentResult> {
    const executionData = task.input;
    
    const monitoringPrompt = `Monitor this workflow execution and suggest adjustments:

Current Status: ${JSON.stringify(executionData, null, 2)}

Analyze:
1. Are agents performing as expected?
2. Should we adjust priorities or add parallel tasks?
3. Any quality concerns that need intervention?
4. Should we switch to alternative agents?

Provide recommendations in JSON format.`;

    const response = await this.invokeClaude(monitoringPrompt);
    
    return this.createResult(task, true, {
      recommendations: this.parseRecommendations(response),
      adjustments: this.parseAdjustments(response)
    });
  }

  private async handleFailures(task: AgentTask): Promise<AgentResult> {
    const failureData = task.input;
    
    const recoveryPrompt = `Handle this workflow failure and create recovery plan:

Failure Details: ${JSON.stringify(failureData, null, 2)}

Create recovery strategy:
1. Root cause analysis
2. Alternative agent selection
3. Modified workflow plan
4. Risk mitigation

Return recovery plan in JSON format.`;

    const response = await this.invokeClaude(recoveryPrompt);
    
    return this.createResult(task, true, {
      recoveryPlan: this.parseRecoveryPlan(response),
      rootCause: this.extractRootCause(response)
    });
  }

  private extractReasoning(response: string): string {
    const reasoningMatch = response.match(/"reasoning":\s*"([^"]+)"/);
    return reasoningMatch ? reasoningMatch[1] : 'No reasoning provided';
  }

  private parseRecommendations(response: string): any[] {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return parsed.recommendations || [];
      }
    } catch (error) {
      console.warn('Failed to parse recommendations:', error);
    }
    return [];
  }

  private parseAdjustments(response: string): any[] {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return parsed.adjustments || [];
      }
    } catch (error) {
      console.warn('Failed to parse adjustments:', error);
    }
    return [];
  }

  private parseRecoveryPlan(response: string): any {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return parsed.recoveryPlan || {};
      }
    } catch (error) {
      console.warn('Failed to parse recovery plan:', error);
    }
    return {};
  }

  private extractRootCause(response: string): string {
    const causeMatch = response.match(/"rootCause":\s*"([^"]+)"/);
    return causeMatch ? causeMatch[1] : 'Unknown cause';
  }
}