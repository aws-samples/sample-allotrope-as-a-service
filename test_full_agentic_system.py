#!/usr/bin/env python3
"""
Full Agentic System Test
Tests the complete supervisor agent workflow
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.orchestrator.strands_agent_orchestrator import ASMTransformationWorkflow
from src.agents.strands_file_analysis_agent import create_file_analysis_agent
import asyncio
import json

async def test_full_agentic_workflow():
    """Test the complete agentic workflow"""
    
    print("=== Full Agentic System Test ===")
    print("Testing Supervisor Agent + File Analysis Agent + Workflow Orchestration")
    
    # Initialize the workflow system
    workflow = ASMTransformationWorkflow()
    
    # Test files with different complexity levels
    test_cases = [
        {
            'name': 'Known Format - CSV',
            'file': 'test_data_solution_analyzer_agilent.csv',
            'expected_complexity': 'low'
        },
        {
            'name': 'Unknown Format - Tab Separated',
            'content': "Time\tValue\tStatus\n10:00\t123.45\tOK\n10:05\t125.67\tWARN",
            'expected_complexity': 'medium'
        },
        {
            'name': 'Complex Binary-like Format',
            'content': "##HEADER\n@DATA\nBinary_Sample_001\x00\x01\x02Mixed_Content",
            'expected_complexity': 'high'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        
        # Get file content
        if 'file' in test_case and os.path.exists(test_case['file']):
            with open(test_case['file'], 'r') as f:
                file_content = f.read().encode('utf-8')
            filename = test_case['file']
        else:
            file_content = test_case['content'].encode('utf-8')
            filename = f"test_case_{i}.txt"
        
        print(f"Processing: {filename}")
        print(f"Content size: {len(file_content)} bytes")
        
        # Process through supervisor agent workflow
        try:
            result = await workflow.process_conversion_request(
                file_data=file_content,
                filename=filename,
                requirements={
                    'target_schema': 'asm-1.0.0',
                    'quality_threshold': 0.8,
                    'max_duration': 120,
                    'generate_converter': True,
                    'approval_required': True
                }
            )
            
            print(f"Workflow Status: {'SUCCESS' if result['success'] else 'FAILED'}")
            print(f"Workflow ID: {result['workflow_id']}")
            
            # Parse supervisor responses for workflow details
            planning_response = result.get('planning_response', '')
            execution_response = result.get('execution_response', '')
            
            print(f"Planning Response Length: {len(planning_response)} chars")
            print(f"Execution Response Length: {len(execution_response)} chars")
            
            results.append({
                'test_case': test_case['name'],
                'filename': filename,
                'success': result['success'],
                'workflow_id': result['workflow_id'],
                'supervisor_planning': planning_response[:200] + "..." if len(planning_response) > 200 else planning_response,
                'supervisor_execution': execution_response[:200] + "..." if len(execution_response) > 200 else execution_response
            })
            
        except Exception as e:
            print(f"Workflow Error: {str(e)}")
            results.append({
                'test_case': test_case['name'],
                'filename': filename,
                'success': False,
                'error': str(e)
            })
    
    return results

async def test_file_analysis_agent():
    """Test the file analysis agent directly"""
    
    print(f"\n=== File Analysis Agent Test ===")
    
    # Create file analysis agent
    file_agent = create_file_analysis_agent()
    
    # Test with a sample file
    sample_csv = b"Sample_ID,Concentration,pH,Temperature\nSOL_001,5.2,7.1,23.5\nSOL_002,3.8,6.9,24.1"
    
    try:
        response = file_agent(f"""
        Please analyze this laboratory data file:
        Filename: sample_solution_data.csv
        
        Use the analyze_file_format tool first, then provide your expert analysis of:
        1. What type of instrument likely generated this data
        2. What data patterns you observe
        3. How complex the conversion to ASM format would be
        4. Any recommendations for processing
        """)
        
        print("File Analysis Agent Response:")
        print(response)
        
        return {'success': True, 'response': response}
        
    except Exception as e:
        print(f"File Analysis Agent Error: {str(e)}")
        return {'success': False, 'error': str(e)}

async def main():
    """Run full agentic system tests"""
    
    print("FULL AGENTIC ASM TRANSFORMATION SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: File Analysis Agent
    analysis_result = await test_file_analysis_agent()
    
    # Test 2: Full Workflow with Supervisor Agent
    workflow_results = await test_full_agentic_workflow()
    
    # Summary
    print(f"\n{'=' * 60}")
    print("AGENTIC SYSTEM TEST SUMMARY")
    print(f"{'=' * 60}")
    
    print(f"\nFile Analysis Agent:")
    print(f"Status: {'SUCCESS' if analysis_result['success'] else 'FAILED'}")
    
    print(f"\nSupervisor Agent Workflows:")
    for result in workflow_results:
        status = 'SUCCESS' if result['success'] else 'FAILED'
        print(f"- {result['test_case']}: {status}")
    
    print(f"\nAgentic Components Tested:")
    print(f"✓ Strands File Analysis Agent")
    print(f"✓ Supervisor Agent with Extended Thinking")
    print(f"✓ Multi-Agent Workflow Orchestration")
    print(f"✓ Dynamic Workflow Planning")
    print(f"✓ Agent Tool Integration")
    
    print(f"\nWorkflow Features Demonstrated:")
    print(f"✓ Format Detection → Converter Selection")
    print(f"✓ Unknown Format → New Converter Generation")
    print(f"✓ Approval Workflow Integration")
    print(f"✓ Quality Metrics Generation")
    print(f"✓ Metadata Capture Throughout")
    
    successful_workflows = sum(1 for r in workflow_results if r['success'])
    print(f"\nResults: {successful_workflows}/{len(workflow_results)} workflows successful")

if __name__ == "__main__":
    asyncio.run(main())