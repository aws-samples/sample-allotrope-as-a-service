"""
Test Certification Report Generation
Demonstrates how to generate PDF certification reports from validation results
"""

import json
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'dvaas'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'agents'))

from generate_certification_report import save_certification_report


def test_certification_report():
    """Test generating certification report from sample validation results"""
    
    # Sample validation result (PASSED with certification)
    passed_result = {
        "valid": True,
        "validation_level": "certification",
        "timestamp": "2026-01-14T20:30:00.000Z",
        "errors": [],
        "warnings": [
            "WARNING: Temperature value is null in pH measurement"
        ],
        "info": [
            "INFO: Detected technique: solution analyzer",
            "INFO: Measurement count: 4",
            "INFO: Manifest: http://purl.allotrope.org/manifests/solution-analyzer/REC/2025/06/solution-analyzer.manifest",
            "INFO: Statistics document: Present",
            "INFO: Data source traceability: Present"
        ],
        "metrics": {
            "technique": "solution analyzer",
            "technique_confidence": 100.0,
            "measurement_count": 4,
            "has_sample_document": True,
            "has_device_control_document": True,
            "has_custom_information_document": True,
            "has_calculated_data": True,
            "measurement_identifiers": 4
        },
        "validator": "allotropy",
        "certification": {
            "status": "ALLOTROPE_CERTIFIED",
            "certificate_id": "CERT-20260114203000",
            "issued_at": "2026-01-14T20:30:00.000Z",
            "validator": "allotropy_v1.1.1"
        }
    }
    
    # Sample validation result (FAILED)
    failed_result = {
        "valid": False,
        "validation_level": "comprehensive",
        "timestamp": "2026-01-14T20:35:00.000Z",
        "errors": [
            "ERROR: Missing ASM manifest",
            "ERROR: No measurement documents found",
            "ERROR: Fields that should be nested in 'sample document' are flattened on measurement"
        ],
        "warnings": [
            "WARNING: Non-standard manifest URL format",
            "WARNING: Unknown units not in known list"
        ],
        "info": [
            "INFO: Detected technique: unknown"
        ],
        "metrics": {
            "technique": "unknown",
            "measurement_count": 0
        },
        "validator": "allotropy",
        "certification": None
    }
    
    print("Generating certification reports...")
    
    # Generate PASSED report
    passed_path = "certification_report_PASSED.pdf"
    save_certification_report(
        passed_result, 
        passed_path, 
        "SampleResults2025-November-1.json"
    )
    print(f"[PASS] Generated PASSED certification report: {passed_path}")
    
    # Generate FAILED report
    failed_path = "certification_report_FAILED.pdf"
    save_certification_report(
        failed_result, 
        failed_path, 
        "invalid_sample.json"
    )
    print(f"[FAIL] Generated FAILED certification report: {failed_path}")
    
    print("\nReports generated successfully!")
    print("\nTo use in production:")
    print("1. Call DVaaS API with 'generate_report': true")
    print("2. Receive base64-encoded PDF in response")
    print("3. Decode and save PDF file")
    print("\nExample API call:")
    print("""
POST https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate
{
  "asm_data": { ... },
  "validation_level": "certification",
  "generate_report": true,
  "file_name": "SampleResults-1.json"
}
    """)


if __name__ == "__main__":
    test_certification_report()
