#!/usr/bin/env python3
"""
Simple Allotropy Integration Test (No Unicode)
"""

import sys

def test_allotropy():
    print("Testing allotropy import...")
    try:
        from allotropy.parser_factory import Vendor
        print("[OK] Allotropy imported successfully")
        print(f"[INFO] Found {len([v for v in Vendor])} supported vendors")
        return True
    except ImportError as e:
        print(f"[FAIL] Could not import allotropy: {e}")
        return False

def test_detection():
    print("\nTesting instrument detection...")
    try:
        sys.path.insert(0, 'src/agents')
        from strands_file_analysis_agent import _check_allotropy_support
        
        result = _check_allotropy_support("test.csv", "Sample ID,Viable cells,Viability")
        print(f"[OK] Detection works: supported={result['supported']}")
        return True
    except Exception as e:
        print(f"[FAIL] Detection failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ALLOTROPY INTEGRATION TEST")
    print("=" * 60)
    
    test1 = test_allotropy()
    test2 = test_detection()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("[PASS] All tests passed")
        sys.exit(0)
    else:
        print("[FAIL] Some tests failed")
        sys.exit(1)
