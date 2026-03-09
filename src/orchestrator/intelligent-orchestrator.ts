import { BaseAgent, AgentTask, AgentResult } from '../agents/base-agent';
import { SupervisorAgent, WorkflowPlan } from '../agents/supervisor-agent';
import { FileAnalysisAgent } from '../agents/file-analysis-agent';
import { ConverterGenerationAgent } from '../agents/converter-generation-agent';

export interface IntelligentConversionRequest {
  id: string;
  files: Array<{
    filename: string;
    content: Buffer;
    mimeType?: string;
  }>;
  targetSchema: string;
  requirements?: string[];
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  constraints?: {
    maxDuration?: number;
    qualityThreshold?: number;
  };
}

export class IntelligentOrchestrator {
  private agents: Map<string, BaseAgent> = new Map();
  private supervisor: SupervisorAgent;
  private activeWorkflows: Map<string, WorkflowExecution> = new Map();

  constructor() {
    this.supervisor = new SupervisorAgent();
    this.initializeAgents();
  }

  private initializeAgents(): void {
    const agents = [
      new FileAnalysisAgent(),
      new ConverterGenerationAgent()
    ];

    agents.forEach(agent => {
      this.agents.set(agent.id, agent);
    });
  }

  async processRequest(request: IntelligentConversionRequest): Promise<any> {
    // Step 1: Supervisor creates workflow plan
    const planTask = this.createTask('plan_workflow', {
      request,
      availableAgents: this.getAgentStatus(),
      constraints: request.constraints
    });

    const planResult = await this.supervisor.execute(planTask);
    if (!planResult.success) {
      throw new Error(`Workflow planning failed: ${planResult.error}`);
    }

    const { plan, reasoning } = planResult.output;
    console.log(`Supervisor reasoning: ${reasoning}`);

    // Step 2: Execute workflow with supervision
    const execution = new WorkflowExecution(request.id, plan, this.agents, this.supervisor);
    this.activeWorkflows.set(request.id, execution);

    try {
      const result = await execution.execute();
      return result;
    } finally {
      this.activeWorkflows.delete(request.id);
    }
  }

  private getAgentStatus() {
    return Array.from(this.agents.values()).map(agent => ({
      id: agent.id,
      name: agent.name,
      capabilities: agent.capabilities.map(c => c.name),
      currentLoad: this.calculateAgentLoad(agent.id)
    }));
  }

  private calculateAgentLoad(agentId: string): number {
    // Count active workflows using this agent
    let activeCount = 0;
    for (const workflow of this.activeWorkflows.values()) {
      if (workflow.isUsingAgent(agentId)) {
        activeCount++;
      }
    }
    return Math.min(activeCount * 25, 100); // 25% per active workflow, max 100%
  }

  private createTask(type: string, input: any): AgentTask {
    return {
      id: `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      input,
      priority: 'medium'
    };
  }

  // Management methods
  getActiveWorkflows() {
    return Array.from(this.activeWorkflows.keys());
  }

  async getWorkflowStatus(requestId: string) {
    const workflow = this.activeWorkflows.get(requestId);
    return workflow ? workflow.getStatus() : null;
  }
}

class WorkflowExecution {
  private currentStep = 0;
  private results: Map<string, AgentResult> = new Map();
  private startTime = new Date();

  constructor(
    private requestId: string,
    private plan: WorkflowPlan,
    private agents: Map<string, BaseAgent>,
    private supervisor: SupervisorAgent
  ) {}

  async execute(): Promise<any> {
    const executionSteps = [];

    for (let i = 0; i < this.plan.steps.length; i++) {
      const step = this.plan.steps[i];
      this.currentStep = i;

      try {
        // Check dependencies
        const dependenciesMet = this.checkDependencies(step.dependencies);
        if (!dependenciesMet) {
          throw new Error(`Dependencies not met for step ${i}`);
        }

        // Execute step
        const agent = this.agents.get(step.agentId);
        if (!agent) {
          throw new Error(`Agent ${step.agentId} not found`);
        }

        const task = this.createStepTask(step);
        const result = await agent.execute(task);
        
        this.results.set(step.agentId, result);
        executionSteps.push({
          step: i,
          agent: step.agentId,
          task: step.taskType,
          result,
          duration: Date.now() - task.context?.startTime || 0
        });

        // Monitor execution with supervisor
        if (i < this.plan.steps.length - 1) {
          await this.supervisorMonitoring(executionSteps);
        }

      } catch (error) {
        // Handle failure with supervisor
        const recovery = await this.handleStepFailure(step, error, executionSteps);
        if (recovery.shouldContinue) {
          // Apply recovery plan
          continue;
        } else {
          throw error;
        }
      }
    }

    return {
      requestId: this.requestId,
      success: true,
      results: Array.from(this.results.values()),
      executionSteps,
      totalDuration: Date.now() - this.startTime.getTime()
    };
  }

  private checkDependencies(dependencies: string[]): boolean {
    return dependencies.every(dep => this.results.has(dep));
  }

  private createStepTask(step: any): AgentTask {
    const previousResults = Array.from(this.results.values());
    
    return {
      id: `step-${this.currentStep}-${Date.now()}`,
      type: step.taskType,
      input: this.buildStepInput(step, previousResults),
      context: { startTime: Date.now() },
      priority: step.priority || 'medium'
    };
  }

  private buildStepInput(step: any, previousResults: AgentResult[]): any {
    // Build input based on step type and previous results
    if (step.taskType === 'analyze_file_format') {
      return {
        fileBuffer: Buffer.from(''), // Would come from request
        filename: 'sample.csv'
      };
    } else if (step.taskType === 'generate_converter') {
      const analysisResult = previousResults.find(r => r.agentId === 'file-analysis-agent');
      return {
        fileAnalysis: analysisResult?.output,
        targetSchema: 'asm-1.0.0'
      };
    }
    return {};
  }

  private async supervisorMonitoring(executionSteps: any[]): Promise<void> {
    const monitorTask = {
      id: `monitor-${Date.now()}`,
      type: 'monitor_execution',
      input: {
        currentStep: this.currentStep,
        executionSteps,
        plan: this.plan
      }
    };

    const monitorResult = await this.supervisor.execute(monitorTask);
    if (monitorResult.success && monitorResult.output.adjustments?.length > 0) {
      console.log('Supervisor adjustments:', monitorResult.output.adjustments);
      // Apply adjustments to remaining steps
    }
  }

  private async handleStepFailure(step: any, error: any, executionSteps: any[]): Promise<{ shouldContinue: boolean }> {
    const recoveryTask = {
      id: `recovery-${Date.now()}`,
      type: 'handle_failures',
      input: {
        failedStep: step,
        error: error.message,
        executionSteps,
        plan: this.plan
      }
    };

    const recoveryResult = await this.supervisor.execute(recoveryTask);
    
    if (recoveryResult.success && recoveryResult.output.recoveryPlan) {
      console.log('Applying recovery plan:', recoveryResult.output.recoveryPlan);
      return { shouldContinue: true };
    }

    return { shouldContinue: false };
  }

  isUsingAgent(agentId: string): boolean {
    return this.plan.steps.some(step => step.agentId === agentId);
  }

  getStatus() {
    return {
      requestId: this.requestId,
      currentStep: this.currentStep,
      totalSteps: this.plan.steps.length,
      progress: (this.currentStep / this.plan.steps.length) * 100,
      startTime: this.startTime,
      estimatedCompletion: new Date(this.startTime.getTime() + this.plan.totalEstimatedTime)
    };
  }
}