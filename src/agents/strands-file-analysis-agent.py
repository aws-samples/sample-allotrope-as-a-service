from strands import Agent, tool
from strands.models import BedrockModel
import json
import logging

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)

@tool
def analyze_file_format(file_buffer: bytes, filename: str, mime_type: str = None) -> str:
    """
    Analyze file format and structure for laboratory instrument data.
    
    Args:
        file_buffer (bytes): The file content as bytes
        filename (str): Name of the file
        mime_type (str): MIME type of the file (optional)
    
    Returns:
        str: JSON string containing file analysis results
    """
    try:
        # Basic file signature analysis
        file_signature = _analyze_file_signature(file_buffer)
        
        # Content analysis for text-based files
        content_sample = _extract_content_sample(file_buffer)
        
        # Determine structure type
        structure_type = _determine_structure_type(file_buffer)
        
        # Check allotropy support
        allotropy_support = _check_allotropy_support(filename, content_sample)
        
        analysis_result = {
            "format": file_signature["format"],
            "confidence": file_signature["confidence"],
            "structure": {
                "type": structure_type,
                "encoding": "utf-8" if _is_valid_text(content_sample) else "binary",
                "sample": content_sample[:500] if content_sample else None
            },
            "metadata": {
                "size": len(file_buffer),
                "filename": filename,
                "mime_type": mime_type
            },
            "allotropy": allotropy_support
        }
        
        return json.dumps(analysis_result)
        
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})

@tool
def detect_allotropy_support(filename: str, file_content: str) -> str:
    """
    Check if allotropy library supports this instrument type.
    
    Args:
        filename (str): Name of the file
        file_content (str): Sample of file content
    
    Returns:
        str: JSON string with allotropy support information
    """
    try:
        support_info = _check_allotropy_support(filename, file_content)
        return json.dumps(support_info)
    except Exception as e:
        return json.dumps({"supported": False, "error": str(e)})

def _analyze_file_signature(buffer: bytes) -> dict:
    """Analyze file signature/magic numbers"""
    signatures = [
        {"format": "pdf", "signature": [0x25, 0x50, 0x44, 0x46], "confidence": 0.95},
        {"format": "xlsx", "signature": [0x50, 0x4B, 0x03, 0x04], "confidence": 0.8},
        {"format": "png", "signature": [0x89, 0x50, 0x4E, 0x47], "confidence": 0.95},
        {"format": "jpeg", "signature": [0xFF, 0xD8, 0xFF], "confidence": 0.95}
    ]
    
    for sig in signatures:
        if len(buffer) >= len(sig["signature"]):
            matches = all(buffer[i] == byte for i, byte in enumerate(sig["signature"]))
            if matches:
                return {"format": sig["format"], "confidence": sig["confidence"]}
    
    # Check for text-based formats
    text_sample = buffer.decode('utf-8', errors='ignore')[:1000]
    if _is_valid_text(text_sample):
        if ',' in text_sample and '\n' in text_sample:
            return {"format": "csv", "confidence": 0.7}
        if '<' in text_sample and '>' in text_sample:
            return {"format": "xml", "confidence": 0.7}
        if '{' in text_sample and '}' in text_sample:
            return {"format": "json", "confidence": 0.7}
    
    return {"format": "unknown", "confidence": 0.1}

def _extract_content_sample(buffer: bytes) -> str:
    """Extract content sample for analysis"""
    try:
        return buffer.decode('utf-8', errors='ignore')[:2000]
    except:
        return ""

def _determine_structure_type(buffer: bytes) -> str:
    """Determine if file is binary, text, or structured"""
    sample = buffer.decode('utf-8', errors='ignore')[:1000]
    if not _is_valid_text(sample):
        return 'binary'
    
    if any(char in sample for char in [',', '\t', '<', '{', ';']):
        return 'structured'
    return 'text'

def _is_valid_text(text: str) -> bool:
    """Check if text is valid UTF-8"""
    control_chars = sum(1 for char in text if ord(char) < 32 and char not in '\n\r\t')
    return control_chars < len(text) * 0.1

def _check_allotropy_support(filename: str, content_sample: str) -> dict:
    """
    Check if allotropy library supports this instrument.
    Uses detection patterns from Anthropic skill.
    """
    try:
        # Try to import allotropy
        from allotropy.parser_factory import Vendor
        
        # Detection patterns (subset from Anthropic skill)
        patterns = {
            "BECKMAN_VI_CELL_BLU": ["Sample ID", "Viable cells", "Viability"],
            "BECKMAN_VI_CELL_XR": ["Total cells/ml", "Viable cells/ml"],
            "THERMO_FISHER_NANODROP_EIGHT": ["NanoDrop Eight", "A260", "A280"],
            "THERMO_FISHER_NANODROP_ONE": ["NanoDrop One", "Nucleic Acid"],
            "MOLDEV_SOFTMAX_PRO": ["SoftMax Pro", "SpectraMax"],
            "BMG_MARS": ["BMG LABTECH", "CLARIOstar"],
            "APPBIO_QUANTSTUDIO": ["QuantStudio", "qPCR"],
        }
        
        content_lower = content_sample.lower()
        best_match = None
        best_score = 0
        
        for vendor, keywords in patterns.items():
            score = sum(1 for kw in keywords if kw.lower() in content_lower)
            if score > best_score:
                best_score = score
                best_match = vendor
        
        if best_match and best_score >= 2:
            return {
                "supported": True,
                "vendor": best_match,
                "confidence": min(0.95, best_score * 0.3),
                "method": "allotropy"
            }
        
        return {
            "supported": False,
            "vendor": None,
            "confidence": 0.0,
            "method": "custom_generation"
        }
        
    except ImportError:
        return {
            "supported": False,
            "vendor": None,
            "confidence": 0.0,
            "error": "allotropy not installed",
            "method": "custom_generation"
        }

# Create the File Analysis Agent
def create_file_analysis_agent():
    """Create a Strands agent for file analysis"""
    
    # Create Bedrock model
    model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        temperature=0.3,
    )
    
    # System prompt for file analysis
    system_prompt = """You are a specialized file analysis agent for laboratory instrument data.
    
    Your role is to:
    1. Analyze file formats and structures
    2. Identify data patterns and instrument types
    3. Assess file complexity and processing requirements
    4. Provide recommendations for data conversion
    
    Use the analyze_file_format tool to examine files, then provide intelligent analysis
    of the results including:
    - Instrument type identification
    - Data pattern recognition
    - Complexity assessment
    - Processing recommendations
    
    Always provide detailed, scientific analysis suitable for pharmaceutical data processing."""
    
    # Create agent with tools
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[analyze_file_format]
    )
    
    return agent

# CLI Interface for TypeScript integration
if __name__ == "__main__":
    import sys
    import base64
    from datetime import datetime
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing input data", "success": False}))
        sys.exit(1)
    
    try:
        # Parse CLI input
        input_data = json.loads(sys.argv[1])
        
        # Extract file data
        file_content = input_data.get('file_content', '')
        filename = input_data.get('filename', 'unknown')
        
        # Decode base64 file content if provided
        if input_data.get('file_content_base64'):
            file_content = base64.b64decode(input_data['file_content_base64'])
        else:
            file_content = file_content.encode('utf-8')
        
        # Create agent and analyze
        agent = create_file_analysis_agent()
        
        prompt = f"""
Analyze this laboratory data file:
Filename: {filename}

Use the analyze_file_format tool first, then provide analysis of:
1. File format and structure
2. Instrument type identification  
3. Data patterns and complexity
4. Processing recommendations

Return results in structured format.
"""
        
        response = agent(prompt)
        
        # Return structured result
        result = {
            "success": True,
            "agent": "file_analysis",
            "filename": filename,
            "analysis": response,
            "timestamp": datetime.now().isoformat()
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "agent": "file_analysis",
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_result))
        sys.exit(1)