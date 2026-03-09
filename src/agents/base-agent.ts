import { BedrockRuntimeClient, InvokeModelCommand } from '@aws-sdk/client-bedrock-runtime';
import { v4 as uuidv4 } from 'uuid';

export interface AgentTask {
  id: string;
  type: string;
  input: any;
  context?: Record<string, any>;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

export interface AgentResult {
  taskId: string;
  agentId: string;
  success: boolean;
  output?: any;
  error?: string;
  metadata?: Record<string, any>;
  nextActions?: AgentTask[];
}

export interface AgentCapability {
  name: string;
  description: string;
  inputSchema: any;
  outputSchema: any;
}

export abstract class BaseAgent {
  protected bedrock: BedrockRuntimeClient;
  protected modelId: string = 'anthropic.claude-3-sonnet-20240229-v1:0';
  
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly capabilities: AgentCapability[]
  ) {
    this.bedrock = new BedrockRuntimeClient({ region: 'us-east-1' });
  }

  abstract execute(task: AgentTask): Promise<AgentResult>;

  protected async invokeClaude(prompt: string, maxTokens: number = 4000): Promise<string> {
    const requestBody = {
      anthropic_version: "bedrock-2023-05-31",
      max_tokens: maxTokens,
      temperature: 0.3,
      messages: [{ role: "user", content: prompt }]
    };

    const command = new InvokeModelCommand({
      modelId: this.modelId,
      contentType: "application/json",
      accept: "application/json",
      body: JSON.stringify(requestBody)
    });

    const response = await this.bedrock.send(command);
    const responseBody = JSON.parse(new TextDecoder().decode(response.body));
    return responseBody.content[0].text;
  }

  protected createTask(type: string, input: any, priority: AgentTask['priority'] = 'medium'): AgentTask {
    return {
      id: uuidv4(),
      type,
      input,
      priority
    };
  }

  protected createResult(task: AgentTask, success: boolean, output?: any, error?: string): AgentResult {
    return {
      taskId: task.id,
      agentId: this.id,
      success,
      output,
      error,
      metadata: {
        timestamp: new Date().toISOString(),
        executionTime: Date.now()
      }
    };
  }
}