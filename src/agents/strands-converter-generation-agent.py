from strands import Agent, tool
from strands.models import BedrockModel
import json
import logging

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)

@tool
def generate_converter_code(
    file_analysis: str, 
    instrument_knowledge: str = None, 
    target_schema: str = "asm-1.0.0",
    language: str = "typescript"
) -> str:
    """
    Generate converter code based on file analysis and instrument knowledge.
    
    Args:
        file_analysis (str): JSON string containing file analysis results
        instrument_knowledge (str): JSON string with instrument documentation (optional)
        target_schema (str): Target ASM schema version
        language (str): Programming language (typescript or python)
    
    Returns:
        str: JSON string containing generated converter code and metadata
    """
    try:
        analysis = json.loads(file_analysis) if isinstance(file_analysis, str) else file_analysis
        knowledge = json.loads(instrument_knowledge) if instrument_knowledge else {}
        
        # Check if allotropy supports this instrument
        allotropy_info = analysis.get('allotropy', {})
        
        if allotropy_info.get('supported'):
            # Use allotropy for supported instruments
            return json.dumps({
                "success": True,
                "method": "allotropy",
                "vendor": allotropy_info.get('vendor'),
                "confidence": allotropy_info.get('confidence'),
                "message": "Use allotropy library for conversion"
            })
        
        # Fall back to custom generation for unsupported instruments
        complexity = _assess_complexity(analysis, knowledge)
        converter_metadata = {
            "id": f"conv-{analysis.get('format', 'unknown')}-{hash(str(analysis)) % 10000}",
            "name": f"{analysis.get('format', 'Unknown').upper()} to ASM Converter",
            "language": language,
            "target_schema": target_schema,
            "complexity": complexity,
            "confidence": _calculate_confidence(analysis, knowledge),
            "supported_formats": [analysis.get('format', 'unknown')],
            "method": "custom_generation"
        }
        
        result = {
            "success": True,
            "converter": {
                "metadata": converter_metadata,
                "code_template": _get_code_template(language, analysis, knowledge),
                "requirements": _get_requirements(language, complexity),
                "test_cases": _generate_test_cases(analysis)
            }
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def convert_with_allotropy(file_path: str, vendor: str) -> str:
    """
    Convert file using allotropy library for supported instruments.
    
    Args:
        file_path (str): Path to the instrument file
        vendor (str): Allotropy vendor enum name (e.g., BECKMAN_VI_CELL_BLU)
    
    Returns:
        str: JSON string containing ASM output or error
    """
    try:
        from allotropy.parser_factory import Vendor
        from allotropy.to_allotrope import allotrope_from_file
        
        # Get vendor enum
        vendor_enum = getattr(Vendor, vendor, None)
        if vendor_enum is None:
            return json.dumps({
                "success": False,
                "error": f"Vendor {vendor} not found in allotropy"
            })
        
        # Convert file
        asm = allotrope_from_file(file_path, vendor_enum)
        
        return json.dumps({
            "success": True,
            "method": "allotropy",
            "vendor": vendor,
            "asm": asm
        })
        
    except ImportError:
        return json.dumps({
            "success": False,
            "error": "allotropy library not installed"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "fallback": "Use custom generation"
        })

@tool
def validate_asm_output(asm_data: str, schema_version: str = "asm-1.0.0") -> str:
    """
    Validate generated ASM data against schema requirements.
    
    Args:
        asm_data (str): JSON string containing ASM data
        schema_version (str): ASM schema version to validate against
    
    Returns:
        str: JSON string containing validation results
    """
    try:
        data = json.loads(asm_data) if isinstance(asm_data, str) else asm_data
        
        validation_result = {
            "is_valid": True,
            "schema_version": schema_version,
            "violations": [],
            "warnings": [],
            "score": 100
        }
        
        # Basic ASM structure validation
        required_fields = ["version", "schema", "data", "metadata"]
        for field in required_fields:
            if field not in data:
                validation_result["violations"].append({
                    "field": field,
                    "message": f"Required field '{field}' is missing",
                    "severity": "error"
                })
                validation_result["is_valid"] = False
        
        # Data structure validation
        if "data" in data:
            data_section = data["data"]
            expected_sections = ["measurements", "samples", "methods", "instruments"]
            for section in expected_sections:
                if section not in data_section:
                    validation_result["warnings"].append({
                        "field": f"data.{section}",
                        "message": f"Recommended section '{section}' is missing",
                        "severity": "warning"
                    })
        
        # Calculate score
        total_checks = len(required_fields) + len(expected_sections)
        violations_count = len(validation_result["violations"])
        warnings_count = len(validation_result["warnings"])
        
        validation_result["score"] = max(0, 100 - (violations_count * 25) - (warnings_count * 5))
        
        return json.dumps(validation_result)
        
    except Exception as e:
        return json.dumps({"is_valid": False, "error": str(e)})

def _assess_complexity(analysis: dict, knowledge: dict) -> str:
    """Assess converter complexity"""
    score = 0
    
    if analysis.get("structure", {}).get("type") == "binary":
        score += 3
    if analysis.get("format") == "unknown":
        score += 3
    if analysis.get("metadata", {}).get("size", 0) > 1024 * 1024:  # > 1MB
        score += 2
    if not knowledge:
        score += 2
    
    if score >= 6:
        return "high"
    elif score >= 3:
        return "medium"
    return "low"

def _calculate_confidence(analysis: dict, knowledge: dict) -> float:
    """Calculate converter generation confidence"""
    base_confidence = analysis.get("confidence", 0.5)
    
    if knowledge:
        base_confidence += 0.2
    if analysis.get("format") != "unknown":
        base_confidence += 0.1
    if analysis.get("structure", {}).get("type") == "structured":
        base_confidence += 0.1
    
    return min(base_confidence, 0.95)

def _get_code_template(language: str, analysis: dict, knowledge: dict) -> str:
    """Get code template based on language and analysis"""
    if language == "python":
        return """
import pandas as pd
import numpy as np
from datetime import datetime

class GeneratedConverter:
    def __init__(self):
        self.format = "{format}"
        self.target_schema = "asm-1.0.0"
    
    def convert(self, file_data: bytes) -> dict:
        # Parse input data
        parsed_data = self._parse_data(file_data)
        
        # Transform to ASM format
        asm_data = self._transform_to_asm(parsed_data)
        
        return asm_data
    
    def _parse_data(self, file_data: bytes):
        # Implementation based on file format
        pass
    
    def _transform_to_asm(self, data):
        return {{
            "version": "1.0.0",
            "schema": "asm-1.0.0",
            "data": {{
                "measurements": [],
                "samples": [],
                "methods": [],
                "instruments": []
            }},
            "metadata": {{
                "generated_at": datetime.now().isoformat(),
                "source_format": self.format
            }}
        }}
""".format(format=analysis.get("format", "unknown"))
    else:  # TypeScript
        return """
export class GeneratedConverter {{
    private format = "{format}";
    private targetSchema = "asm-1.0.0";
    
    async convert(fileData: Buffer): Promise<ASMOutput> {{
        // Parse input data
        const parsedData = this.parseData(fileData);
        
        // Transform to ASM format
        const asmData = this.transformToASM(parsedData);
        
        return asmData;
    }}
    
    private parseData(fileData: Buffer): any {{
        // Implementation based on file format
        return {{}};
    }}
    
    private transformToASM(data: any): ASMOutput {{
        return {{
            version: "1.0.0",
            schema: "asm-1.0.0",
            data: {{
                measurements: [],
                samples: [],
                methods: [],
                instruments: []
            }},
            metadata: {{
                generatedAt: new Date().toISOString(),
                sourceFormat: this.format
            }}
        }};
    }}
}}

interface ASMOutput {{
    version: string;
    schema: string;
    data: {{
        measurements: any[];
        samples: any[];
        methods: any[];
        instruments: any[];
    }};
    metadata: {{
        generatedAt: string;
        sourceFormat: string;
    }};
}}
""".format(format=analysis.get("format", "unknown"))

def _get_requirements(language: str, complexity: str) -> list:
    """Get requirements based on language and complexity"""
    if language == "python":
        base_reqs = ["pandas", "numpy"]
        if complexity == "high":
            base_reqs.extend(["scipy", "h5py"])
        return base_reqs
    else:  # TypeScript
        return ["@types/node", "uuid"]

def _generate_test_cases(analysis: dict) -> list:
    """Generate basic test cases"""
    return [
        {
            "name": "test_basic_conversion",
            "description": f"Test basic {analysis.get('format', 'unknown')} conversion",
            "input": "sample_data",
            "expected_output": {
                "version": "1.0.0",
                "schema": "asm-1.0.0"
            }
        }
    ]

# Create the Converter Generation Agent
def create_converter_generation_agent():
    """Create a Strands agent for converter generation"""
    
    # Create Bedrock model with extended thinking
    model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        temperature=0.3,
        additional_request_fields={
            "thinking": {
                "type": "enabled",
                "budget_tokens": 2048,
            }
        }
    )
    
    # System prompt for converter generation
    system_prompt = """You are an expert converter generation agent for laboratory instrument data.
    
    Your role is to:
    1. Generate high-quality converter code based on file analysis
    2. Use instrument documentation knowledge when available
    3. Create ASM-compliant output structures
    4. Validate generated ASM data against schemas
    5. Provide comprehensive test cases and documentation
    
    You have access to tools for:
    - generate_converter_code: Create converter implementations
    - validate_asm_output: Validate ASM compliance
    
    Always think through the problem step-by-step:
    1. Analyze the file format and structure
    2. Consider instrument-specific knowledge
    3. Choose appropriate programming language
    4. Generate robust, well-documented code
    5. Create comprehensive test cases
    6. Validate ASM compliance
    
    Focus on scientific accuracy, regulatory compliance, and code quality."""
    
    # Create agent with tools
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[generate_converter_code, validate_asm_output]
    )
    
    return agent

# CLI Interface for TypeScript integration
if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing input data", "success": False}))
        sys.exit(1)
    
    try:
        # Parse CLI input
        input_data = json.loads(sys.argv[1])
        
        # Extract required data
        file_analysis = input_data.get('file_analysis', {})
        target_schema = input_data.get('target_schema', 'asm-1.0.0')
        language = input_data.get('language', 'python')
        instrument_knowledge = input_data.get('instrument_knowledge')
        
        # Create agent
        agent = create_converter_generation_agent()
        
        prompt = f"""
Generate a converter for this laboratory data file analysis:
{json.dumps(file_analysis, indent=2)}

Requirements:
1. Use {language} for the implementation
2. Target ASM schema version {target_schema}
3. Include proper error handling
4. Generate comprehensive test cases
5. Validate the ASM output structure

Think through the approach step-by-step and create a production-ready converter.
"""
        
        response = agent(prompt)
        
        # Return structured result
        result = {
            "success": True,
            "agent": "converter_generation",
            "target_schema": target_schema,
            "language": language,
            "converter_response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "agent": "converter_generation",
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_result))
        sys.exit(1)