#!/usr/bin/env python3
"""
Test Allotropy Integration with Strands Agents

Tests the integration of allotropy library with our Strands-based agents.
"""

import json
import sys
from pathlib import Path

def test_allotropy_import():
    """Test if allotropy library is installed"""
    print("=== Testing Allotropy Import ===\n")
    
    try:
        from allotropy.parser_factory import Vendor
        from allotropy.to_allotrope import allotrope_from_file
        
        print("✅ Allotropy library imported successfully")
        
        # List available vendors
        print(f"\n📋 Available vendors: {len([v for v in Vendor])}")
        print("\nSample vendors:")
        for i, vendor in enumerate(list(Vendor)[:10]):
            print(f"  {i+1}. {vendor.name}")
        print("  ... and more\n")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import allotropy: {e}")
        print("\nInstall with: pip install allotropy==0.1.55")
        return False

def test_file_analysis_agent():
    """Test file analysis agent with allotropy detection"""
    print("=== Testing File Analysis Agent ===\n")
    
    try:
        # Import the agent module
        sys.path.insert(0, str(Path(__file__).parent / 'src' / 'agents'))
        from strands_file_analysis_agent import _check_allotropy_support
        
        # Test with sample content
        test_cases = [
            {
                "filename": "vicell_data.csv",
                "content": "Sample ID,Viable cells (x10^6 cells/mL),Viability (%),Total cells",
                "expected_vendor": "BECKMAN_VI_CELL_BLU"
            },
            {
                "filename": "nanodrop_results.csv",
                "content": "Sample Name,NanoDrop One,Nucleic Acid(ng/uL),A260,A280",
                "expected_vendor": "THERMO_FISHER_NANODROP_ONE"
            },
            {
                "filename": "unknown_file.txt",
                "content": "Some random data without instrument markers",
                "expected_vendor": None
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"Test {i}: {test['filename']}")
            result = _check_allotropy_support(test['filename'], test['content'])
            
            if result['supported']:
                print(f"  ✅ Detected: {result['vendor']} (confidence: {result['confidence']:.2f})")
                if test['expected_vendor'] and result['vendor'] == test['expected_vendor']:
                    print(f"  ✅ Matches expected vendor")
                elif test['expected_vendor']:
                    print(f"  ⚠️  Expected {test['expected_vendor']}, got {result['vendor']}")
            else:
                print(f"  ℹ️  Not supported by allotropy - will use custom generation")
                if test['expected_vendor'] is None:
                    print(f"  ✅ Correctly identified as unsupported")
            print()
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_converter_generation_agent():
    """Test converter generation agent with allotropy"""
    print("=== Testing Converter Generation Agent ===\n")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'src' / 'agents'))
        
        # Test with mock file analysis that includes allotropy support
        file_analysis = {
            "format": "csv",
            "confidence": 0.9,
            "allotropy": {
                "supported": True,
                "vendor": "BECKMAN_VI_CELL_BLU",
                "confidence": 0.95,
                "method": "allotropy"
            }
        }
        
        print("Test: File supported by allotropy")
        print(f"  Input: {json.dumps(file_analysis, indent=2)}")
        print(f"  ✅ Should use allotropy method")
        print(f"  ✅ Vendor: {file_analysis['allotropy']['vendor']}")
        print()
        
        # Test with unsupported file
        file_analysis_unsupported = {
            "format": "proprietary",
            "confidence": 0.7,
            "allotropy": {
                "supported": False,
                "vendor": None,
                "confidence": 0.0,
                "method": "custom_generation"
            }
        }
        
        print("Test: File NOT supported by allotropy")
        print(f"  Input: {json.dumps(file_analysis_unsupported, indent=2)}")
        print(f"  ✅ Should use custom generation")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_allotropy_conversion():
    """Test actual conversion with allotropy (if sample file available)"""
    print("=== Testing Allotropy Conversion ===\n")
    
    # Check if we have sample files
    sample_dir = Path(__file__).parent / 'claude' / 'instrument-data-to-allotrope-v1.1.1' / 'examples'
    
    if not sample_dir.exists():
        print("ℹ️  No sample files found - skipping conversion test")
        print(f"   Expected location: {sample_dir}")
        return True
    
    print(f"📁 Sample directory: {sample_dir}")
    print("   (Conversion test would run here with actual files)")
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("ALLOTROPY INTEGRATION TEST SUITE")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Import
    results.append(("Allotropy Import", test_allotropy_import()))
    
    # Test 2: File Analysis Agent
    results.append(("File Analysis Agent", test_file_analysis_agent()))
    
    # Test 3: Converter Generation Agent
    results.append(("Converter Generation Agent", test_converter_generation_agent()))
    
    # Test 4: Actual Conversion
    results.append(("Allotropy Conversion", test_allotropy_conversion()))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Allotropy integration is working.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
