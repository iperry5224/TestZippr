#!/usr/bin/env python3
"""Test imports for the Streamlit app."""
print("Testing imports...")

try:
    import streamlit as st
    print("✅ streamlit imported")
except Exception as e:
    print(f"❌ streamlit: {e}")

try:
    import pandas as pd
    print("✅ pandas imported")
except Exception as e:
    print(f"❌ pandas: {e}")

try:
    import boto3
    print("✅ boto3 imported")
except Exception as e:
    print(f"❌ boto3: {e}")

try:
    from nist_800_53_rev5_full import NIST80053Rev5Assessor, ControlResult, ControlStatus
    print("✅ nist_800_53_rev5_full imported")
except Exception as e:
    print(f"❌ nist_800_53_rev5_full: {e}")

try:
    from botocore.exceptions import ClientError
    print("✅ botocore imported")
except Exception as e:
    print(f"❌ botocore: {e}")

print("\nAll imports tested!")

