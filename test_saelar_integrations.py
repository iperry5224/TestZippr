#!/usr/bin/env python3
"""
SAELAR Integration Tests
========================
Validates that core SAELAR modules import and key components work.
Run: python test_saelar_integrations.py
"""
import sys

def test_imports():
    """Test that all core SAELAR modules import without error."""
    errors = []
    
    modules = [
        ("streamlit", None),
        ("boto3", None),
        ("nist_800_53_rev5_full", ["NIST80053Rev5Assessor", "ControlResult", "ControlStatus"]),
        ("nist_dashboard", ["render_sidebar", "load_system_info", "save_system_info"]),
        ("ssp_generator", ["SSPGenerator", "SystemCategorization", "SystemInfo"]),
        ("risk_score_calculator", ["RiskScoreCalculator", "RiskAssessment", "Finding"]),
        ("nist_800_53_controls", None),
    ]
    
    for mod_name, attrs in modules:
        try:
            mod = __import__(mod_name)
            if attrs:
                for attr in attrs:
                    if not hasattr(mod, attr):
                        errors.append(f"  {mod_name}.{attr} missing")
            print(f"  OK {mod_name}")
        except Exception as e:
            errors.append(f"  {mod_name}: {e}")
            print(f"  FAIL {mod_name}: {e}")
    
    return errors

def test_nist_assessor_init():
    """Test NIST80053Rev5Assessor can be instantiated (no AWS needed for init)."""
    try:
        from nist_800_53_rev5_full import NIST80053Rev5Assessor
        # Init without credentials - will fail on first API call but init should work
        a = NIST80053Rev5Assessor(region="us-east-1")
        assert a is not None
        assert a.region == "us-east-1"
        print("  OK NIST80053Rev5Assessor init")
        return []
    except Exception as e:
        print(f"  FAIL NIST80053Rev5Assessor: {e}")
        return [str(e)]

def test_ssp_generator():
    """Test SSPGenerator creates valid structure."""
    try:
        from ssp_generator import SSPGenerator, SystemCategorization
        ssp = SSPGenerator(
            system_name="Test System",
            system_owner="Test Owner",
            categorization="Moderate"
        )
        data = ssp.to_dict()
        assert "system_name" in data or "controls" in data or "system_info" in str(data)
        print("  OK SSPGenerator")
        return []
    except Exception as e:
        print(f"  FAIL SSPGenerator: {e}")
        return [str(e)]

def test_control_families():
    """Test control family structure is intact (from nist_dashboard)."""
    try:
        from nist_dashboard import CONTROL_FAMILY_INFO, CONTROL_COUNTS_BY_LEVEL, get_control_families
        assert "Moderate" in CONTROL_COUNTS_BY_LEVEL
        assert "AC" in CONTROL_FAMILY_INFO or len(CONTROL_FAMILY_INFO) > 0
        families = get_control_families("Moderate")
        assert isinstance(families, dict) and len(families) > 0
        print("  OK Control families")
        return []
    except Exception as e:
        print(f"  FAIL Control families: {e}")
        return [str(e)]

def test_nist_setup_import():
    """Test nist_setup imports (main app - may have side effects)."""
    try:
        # Import just the controller class, not the full app run
        import nist_setup
        assert hasattr(nist_setup, "NISTApplicationController")
        print("  OK nist_setup")
        return []
    except Exception as e:
        print(f"  FAIL nist_setup: {e}")
        return [str(e)]

def main():
    print("=" * 60)
    print("SAELAR Integration Tests")
    print("=" * 60)
    
    all_errors = []
    
    print("\n1. Core module imports:")
    all_errors.extend(test_imports())
    
    print("\n2. NIST80053Rev5Assessor:")
    all_errors.extend(test_nist_assessor_init())
    
    print("\n3. SSPGenerator:")
    all_errors.extend(test_ssp_generator())
    
    print("\n4. Control families:")
    all_errors.extend(test_control_families())
    
    print("\n5. nist_setup (main app):")
    all_errors.extend(test_nist_setup_import())
    
    print("\n" + "=" * 60)
    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s)")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
