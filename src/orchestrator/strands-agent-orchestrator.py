from strands import Agent, tool
from strands.models import BedrockModel
import json
import logging
from typing import Dict, List, Any
import uuid
from datetime import datetime

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)

@tool
def coordinate_agents(
    request_type: str,
    file_data: str,
    requirements: str = None
) -> str:
    """
    Coordinate multiple agents for ASM transformation workflow.
    
    Args:
        request_type (str): Type of request (analyze, convert, validate)
        file_data (str): File data or analysis results
        requirements (str): Additional requirements (optional)
    
    Returns:
        str: JSON string containing coordination results
    """
    try:
        workflow_id = str(uuid.uuid4())
        
        coordination_result = {
            "workflow_id": workflow_id,
            "request_type": request_type,
            "status": "initiated",
            "steps": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Define workflow steps based on request type
        if request_type == "full_conversion":
            coordination_result["steps"] = [
                {"agent": "file_analysis", "status": "pending", "order": 1},
                {"agent": "knowledge_base", "status": "pending", "order": 2},
                {"agent": "allotrope_standards", "status": "pending", "order": 3},
                {"agent": "converter_generation", "status": "pending", "order": 4},
                {"agent": "validation", "status": "pending", "order": 5}
            ]
        elif request_type == "analyze_only":
            coordination_result["steps"] = [
                {"agent": "file_analysis", "status": "pending", "order": 1}
            ]
        elif request_type == "generate_converter":
            coordination_result["steps"] = [
                {"agent": "converter_generation", "status": "pending", "order": 1},
                {"agent": "validation", "status": "pending", "order": 2}
            ]
        
        return json.dumps(coordination_result)
        
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})

@tool
def update_workflow_status(
    workflow_id: str,
    agent_name: str,
    status: str,
    result: str = None
) -> str:
    """
    Update workflow status for a specific agent step.
    
    Args:
        workflow_id (str): Workflow identifier
        agent_name (str): Name of the agent
        status (str): Status update (completed, failed, in_progress)
        result (str): Agent result data (optional)
    
    Returns:
        str: JSON string containing status update
    """
    try:
        status_update = {
            "workflow_id": workflow_id,
            "agent": agent_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        
        return json.dumps(status_update)
        
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})

@tool
def plan_workflow(
    file_analysis: str,
    available_agents: str,
    constraints: str = None
) -> str:
    """
    Plan optimal workflow based on file analysis and available agents.
    
    Args:
        file_analysis (str): JSON string with file analysis results
        available_agents (str): JSON string with available agents and their capabilities
        constraints (str): JSON string with constraints (time, quality, etc.)
    
    Returns:
        str: JSON string containing workflow plan
    """
    try:
        analysis = json.loads(file_analysis) if isinstance(file_analysis, str) else file_analysis
        agents = json.loads(available_agents) if isinstance(available_agents, str) else available_agents
        constraints_data = json.loads(constraints) if constraints else {}
        
        # Assess file complexity
        complexity = _assess_file_complexity(analysis)
        
        # Create workflow plan
        workflow_plan = {
            "plan_id": str(uuid.uuid4()),
            "complexity": complexity,
            "estimated_duration": _estimate_duration(complexity),
            "recommended_agents": _select_agents(complexity, agents),
            "parallel_steps": _identify_parallel_steps(complexity),
            "quality_threshold": constraints_data.get("quality_threshold", 0.8),
            "max_duration": constraints_data.get("max_duration", 300)  # 5 minutes default
        }
        
        return json.dumps(workflow_plan)
        
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})

def _assess_file_complexity(analysis: dict) -> str:
    """Assess file complexity for workflow planning"""
    score = 0
    
    if analysis.get("format") == "unknown":
        score += 3
    if analysis.get("structure", {}).get("type") == "binary":
        score += 2
    if analysis.get("metadata", {}).get("size", 0) > 1024 * 1024:  # > 1MB
        score += 1
    if analysis.get("confidence", 1.0) < 0.5:
        score += 2
    
    if score >= 5:
        return "high"
    elif score >= 2:
        return "medium"
    return "low"

def _estimate_duration(complexity: str) -> int:
    """Estimate workflow duration in seconds"""
    durations = {
        "low": 30,
        "medium": 90,
        "high": 180
    }
    return durations.get(complexity, 90)

def _select_agents(complexity: str, available_agents: list) -> list:
    """Select optimal agents based on complexity"""
    if complexity == "high":
        return [
            "file_analysis",
            "knowledge_base", 
            "allotrope_standards",
            "converter_generation",
            "quality_assurance",
            "validation"
        ]
    elif complexity == "medium":
        return [
            "file_analysis",
            "knowledge_base",
            "allotrope_standards", 
            "converter_generation",
            "validation"
        ]
    else:
        return [
            "file_analysis",
            "allotrope_standards",
            "converter_generation"
        ]

def _identify_parallel_steps(complexity: str) -> list:
    """Identify steps that can run in parallel"""
    if complexity == "low":
        return [["knowledge_base", "allotrope_standards"]]
    return []

# Create the Supervisor Agent
def create_supervisor_agent():
    """Create a Strands supervisor agent for workflow orchestration"""
    
    # Create Bedrock model with extended thinking
    model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        temperature=0.2,  # Lower temperature for more deterministic planning
        additional_request_fields={
            "thinking": {
                "type": "enabled",
                "budget_tokens": 3000,
            }
        }
    )
    
    # System prompt for supervisor agent
    system_prompt = """You are the Supervisor Agent for the ASM Transformation Service.
    
    Your role is to intelligently orchestrate multiple specialized agents to convert 
    laboratory instrument data to ASM (Allotrope Simple Model) format.
    
    Available specialized agents:
    - File Analysis Agent: Analyzes file formats and structures
    - Knowledge Base Agent: Queries instrument documentation
    - Allotrope Standards Agent: Ensures ASM compliance
    - Converter Generation Agent: Creates conversion code
    - Quality Assurance Agent: Validates output quality
    - Validation Agent: Performs final ASM validation
    
    Your capabilities:
    - coordinate_agents: Orchestrate multi-agent workflows
    - update_workflow_status: Track workflow progress
    - plan_workflow: Create optimal execution plans
    
    Decision-making process:
    1. ANALYZE the request and file characteristics
    2. PLAN the optimal workflow considering:
       - File complexity and format
       - Available agent capabilities
       - Quality vs speed tradeoffs
       - Resource constraints
    3. COORDINATE agent execution with proper sequencing
    4. MONITOR progress and handle failures
    5. OPTIMIZE workflow based on intermediate results
    
    Always think through your decisions step-by-step:
    - What type of file are we processing?
    - What's the optimal agent sequence?
    - Can any steps run in parallel?
    - What are the quality requirements?
    - How should we handle potential failures?
    
    Focus on:
    - Scientific accuracy and regulatory compliance
    - Efficient resource utilization
    - Robust error handling and recovery
    - Clear progress tracking and reporting"""
    
    # Create supervisor agent
    supervisor = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[coordinate_agents, update_workflow_status, plan_workflow]
    )
    
    return supervisor

# Workflow execution class
class ASMTransformationWorkflow:
    """Manages ASM transformation workflows using Strands agents"""
    
    def __init__(self):
        self.supervisor = create_supervisor_agent()
        self.active_workflows: Dict[str, Dict] = {}
    
    async def process_conversion_request(
        self,
        file_data: bytes,
        filename: str,
        requirements: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process a complete conversion request"""
        
        # Create initial request
        request_data = {
            "filename": filename,
            "size": len(file_data),
            "requirements": requirements or {}
        }
        
        # Ask supervisor to plan the workflow
        planning_response = self.supervisor(f"""
        Plan an optimal workflow for converting this laboratory data file:
        
        File: {filename}
        Size: {len(file_data)} bytes
        Requirements: {json.dumps(requirements or {}, indent=2)}
        
        Please:
        1. Analyze the file characteristics
        2. Plan the optimal agent workflow
        3. Consider quality vs speed tradeoffs
        4. Identify any parallel processing opportunities
        5. Estimate total processing time
        
        Use the plan_workflow tool to create a detailed execution plan.
        """)
        
        print(f"Supervisor Planning Response: {planning_response}")
        
        # Execute the planned workflow
        execution_response = self.supervisor(f"""
        Now execute the planned workflow for file: {filename}
        
        Coordinate the following agents in the optimal sequence:
        1. Start with file analysis
        2. Proceed based on the analysis results
        3. Ensure ASM compliance throughout
        4. Validate final output
        
        Use the coordinate_agents tool to manage the workflow execution.
        """)
        
        print(f"Supervisor Execution Response: {execution_response}")
        
        return {
            "success": True,
            "planning_response": planning_response,
            "execution_response": execution_response,
            "workflow_id": str(uuid.uuid4())
        }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow status"""
        return self.active_workflows.get(workflow_id, {"status": "not_found"})

# CLI Interface for TypeScript integration
if __name__ == "__main__":
    import sys
    import asyncio
    from datetime import datetime
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing input data", "success": False}))
        sys.exit(1)
    
    try:
        # Parse CLI input
        input_data = json.loads(sys.argv[1])
        
        # Extract workflow data
        workflow_type = input_data.get('workflow_type', 'full_conversion')
        file_data = input_data.get('file_data', {})
        requirements = input_data.get('requirements', {})
        
        async def run_workflow():
            # Create workflow manager
            workflow = ASMTransformationWorkflow()
            
            # Process conversion request
            result = await workflow.process_conversion_request(
                file_data=file_data.get('content', b'').encode() if isinstance(file_data.get('content'), str) else b'',
                filename=file_data.get('filename', 'unknown'),
                requirements=requirements
            )
            
            return result
        
        # Run workflow
        workflow_result = asyncio.run(run_workflow())
        
        # Return structured result
        result = {
            "success": True,
            "agent": "supervisor_orchestrator",
            "workflow_type": workflow_type,
            "workflow_result": workflow_result,
            "timestamp": datetime.now().isoformat()
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "agent": "supervisor_orchestrator",
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_result))
        sys.exit(1)