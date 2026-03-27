"""
NIST 800-53 Rev 5 Dashboard Module
===================================
Contains all dependencies, configuration, CSS styling, and main dashboard components.
"""

# =============================================================================
# DEPENDENCIES
# =============================================================================
import streamlit as st

if not hasattr(st, "rerun") and hasattr(st, "experimental_rerun"):
    st.rerun = st.experimental_rerun  # type: ignore[attr-defined, assignment]

import pandas as pd
import json
import time
import os
import boto3
import platform
import subprocess
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from botocore.exceptions import ClientError

from nist_800_53_rev5_full import NIST80053Rev5Assessor, ControlResult, ControlStatus

# =============================================================================
# CONFIGURATION
# =============================================================================

# S3 bucket for storing assessment results
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "saelarallpurpose")
S3_PREFIX = "nist-assessments/"

# Certificate locations - use relative path or environment variable
# For containerization: mount certificates to /app/ssl_certs or set SAELAR_CERT_DIR
CERT_DIR = Path(os.environ.get('SAELAR_CERT_DIR', Path(__file__).parent / 'ssl_certs'))

# NIST 800-53 Rev 5 documentation links for all 20 control families
NIST_LINKS = {
    'AC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AC',
    'AT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AT',
    'AU': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AU',
    'CA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CA',
    'CM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM',
    'CP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CP',
    'IA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IA',
    'IR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IR',
    'MA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MA',
    'MP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MP',
    'PE': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PE',
    'PL': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PL',
    'PM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PM',
    'PS': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PS',
    'PT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PT',
    'RA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=RA',
    'SA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SA',
    'SC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SC',
    'SI': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SI',
    'SR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SR',
}

# System information persistence file
SYSTEM_INFO_FILE = Path(os.environ.get('SAELAR_CONFIG_DIR', Path(__file__).parent)) / '.saelar_system_info.json'

# NIST 800-53 Rev 5 documentation links for all 20 control families
NIST_LINKS = {
    'AC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AC',
    'AT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AT',
    'AU': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AU',
    'CA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CA',
    'CM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM',
    'CP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CP',
    'IA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IA',
    'IR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IR',
    'MA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MA',
    'MP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MP',
    'PE': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PE',
    'PL': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PL',
    'PM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PM',
    'PS': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PS',
    'PT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PT',
    'RA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=RA',
    'SA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SA',
    'SC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SC',
    'SI': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SI',
    'SR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SR',
}


def save_system_info():
    """Save system information to persistent storage."""
    system_info = {
        'system_info_name': st.session_state.get('system_info_name', ''),
        'system_info_acronym': st.session_state.get('system_info_acronym', ''),
        'system_info_owner': st.session_state.get('system_info_owner', ''),
        'system_info_owner_email': st.session_state.get('system_info_owner_email', ''),
        'system_info_ao': st.session_state.get('system_info_ao', ''),
        'system_info_ao_email': st.session_state.get('system_info_ao_email', ''),
        'system_info_isso': st.session_state.get('system_info_isso', ''),
        'system_info_isso_email': st.session_state.get('system_info_isso_email', ''),
        'system_info_categorization': st.session_state.get('system_info_categorization', 'Moderate'),
        'system_info_status': st.session_state.get('system_info_status', 'Operational'),
        'system_info_description': st.session_state.get('system_info_description', ''),
        'system_info_boundary': st.session_state.get('system_info_boundary', 'AWS Commercial Cloud'),
    }
    try:
        with open(SYSTEM_INFO_FILE, 'w', encoding='utf-8') as f:
            json.dump(system_info, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save system info: {e}")


def load_system_info():
    """Load system information from persistent storage into session state."""
    if SYSTEM_INFO_FILE.exists():
        try:
            with open(SYSTEM_INFO_FILE, 'r', encoding='utf-8') as f:
                system_info = json.load(f)
                for key, value in system_info.items():
                    if key not in st.session_state or not st.session_state.get(key):
                        st.session_state[key] = value
        except Exception as e:
            print(f"Warning: Could not load system info: {e}")
CERT_FILE = CERT_DIR / "streamlit.crt"
KEY_FILE = CERT_DIR / "streamlit.key"

# NIST 800-53 Rev 5 documentation links for all 20 control families
NIST_LINKS = {
    'AC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AC',
    'AT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AT',
    'AU': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AU',
    'CA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CA',
    'CM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM',
    'CP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CP',
    'IA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IA',
    'IR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IR',
    'MA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MA',
    'MP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MP',
    'PE': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PE',
    'PL': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PL',
    'PM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PM',
    'PS': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PS',
    'PT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PT',
    'RA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=RA',
    'SA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SA',
    'SC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SC',
    'SI': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SI',
    'SR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SR',
}

# Control family definitions with descriptions
# All 20 NIST 800-53 Rev 5 Control Families
# Format: family_code: (display_name, description)
CONTROL_FAMILY_INFO = {
    'AC': ('🔐 Access Control', 'Account management, access enforcement, least privilege'),
    'AT': ('📚 Awareness & Training', 'Security training, role-based training'),
    'AU': ('📝 Audit & Accountability', 'Audit events, logging, monitoring, retention'),
    'CA': ('📋 Assessment & Authorization', 'Security assessments, POA&M, continuous monitoring'),
    'CM': ('⚙️ Configuration Management', 'Baselines, change control, inventory'),
    'CP': ('💾 Contingency Planning', 'Backup, recovery, alternate sites'),
    'IA': ('🎫 Identification & Auth', 'MFA, password policies, PKI, authenticator management'),
    'IR': ('🚨 Incident Response', 'Incident handling, monitoring, reporting'),
    'MA': ('🔧 Maintenance', 'System maintenance, remote maintenance, tools'),
    'MP': ('💿 Media Protection', 'Media access, marking, storage, sanitization'),
    'PE': ('🏢 Physical & Environmental', 'Physical access, monitoring, environmental controls'),
    'PL': ('📋 Planning', 'Security plans, rules of behavior, architecture'),
    'PM': ('📊 Program Management', 'Security program, risk strategy, enterprise architecture'),
    'PS': ('👤 Personnel Security', 'Screening, termination, transfers, agreements'),
    'PT': ('🔏 PII Processing', 'Privacy notices, consent, data minimization'),
    'RA': ('📈 Risk Assessment', 'Categorization, vulnerability scanning, risk response'),
    'SA': ('🏗️ System Acquisition', 'SDLC, supply chain, developer security'),
    'SC': ('🔒 System & Comms Protection', 'Boundary protection, encryption, network security'),
    'SI': ('🛡️ System Integrity', 'Flaw remediation, malware protection, monitoring'),
    'SR': ('📦 Supply Chain', 'SCRM plan, supplier assessments, component authenticity'),
}

# Control counts by system classification level (FIPS 199 / NIST 800-53 Rev 5)
# Based on actual NIST 800-53 Rev 5 control baselines
# Low: Minimum baseline controls (approx 156 controls)
# Moderate: Standard controls for most systems (approx 325 controls)
# High: Comprehensive controls for critical systems (approx 421 controls)
CONTROL_COUNTS_BY_LEVEL = {
    'Low': {
        'AC': 12,   # Access Control baseline
        'AT': 4,    # Awareness & Training baseline
        'AU': 8,    # Audit & Accountability baseline
        'CA': 5,    # Assessment & Authorization baseline
        'CM': 8,    # Configuration Management baseline
        'CP': 7,    # Contingency Planning baseline
        'IA': 7,    # Identification & Authentication baseline
        'IR': 6,    # Incident Response baseline
        'MA': 4,    # Maintenance baseline
        'MP': 5,    # Media Protection baseline
        'PE': 12,   # Physical & Environmental baseline
        'PL': 6,    # Planning baseline
        'PM': 16,   # Program Management baseline
        'PS': 6,    # Personnel Security baseline
        'PT': 4,    # PII Processing baseline
        'RA': 5,    # Risk Assessment baseline
        'SA': 12,   # System Acquisition baseline
        'SC': 18,   # System & Comms Protection baseline
        'SI': 8,    # System Integrity baseline
        'SR': 3,    # Supply Chain baseline
    },
    'Moderate': {
        'AC': 18,   # Enhanced access control
        'AT': 5,    # Enhanced awareness & training
        'AU': 12,   # Enhanced audit & accountability
        'CA': 7,    # Standard assessment & authorization
        'CM': 11,   # Standard configuration management
        'CP': 10,   # Standard contingency planning
        'IA': 10,   # Standard identification & auth (MFA)
        'IR': 8,    # Standard incident response
        'MA': 6,    # Standard maintenance
        'MP': 7,    # Standard media protection
        'PE': 17,   # Standard physical & environmental
        'PL': 8,    # Standard planning
        'PM': 25,   # Standard program management
        'PS': 7,    # Standard personnel security
        'PT': 6,    # Standard PII processing
        'RA': 7,    # Standard risk assessment
        'SA': 18,   # Standard system acquisition
        'SC': 35,   # Standard system & comms protection
        'SI': 14,   # Standard system integrity
        'SR': 8,    # Standard supply chain
    },
    'High': {
        'AC': 25,   # Full access control suite
        'AT': 6,    # Full awareness & training
        'AU': 16,   # Comprehensive audit & accountability
        'CA': 9,    # Full assessment & authorization
        'CM': 14,   # Full configuration management
        'CP': 13,   # Full contingency planning
        'IA': 12,   # Full identification & authentication
        'IR': 10,   # Full incident response
        'MA': 7,    # Full maintenance
        'MP': 8,    # Full media protection
        'PE': 23,   # Full physical & environmental
        'PL': 11,   # Full planning
        'PM': 32,   # Full program management
        'PS': 9,    # Full personnel security
        'PT': 8,    # Full PII processing
        'RA': 10,   # Full risk assessment
        'SA': 23,   # Full system acquisition
        'SC': 51,   # Full system & comms protection
        'SI': 23,   # Full system integrity
        'SR': 12,   # Full supply chain risk management
    },
}

# Classification level descriptions
CLASSIFICATION_LEVELS = {
    'Low': {
        'description': 'Limited adverse effect on operations, assets, or individuals',
        'color': '#22c55e',
        'icon': '🟢'
    },
    'Moderate': {
        'description': 'Serious adverse effect on operations, assets, or individuals',
        'color': '#f59e0b',
        'icon': '🟡'
    },
    'High': {
        'description': 'Severe or catastrophic adverse effect on operations, assets, or individuals',
        'color': '#dc2626',
        'icon': '🔴'
    }
}

def get_control_families(classification_level: str = 'High') -> dict:
    """Get control families with counts based on classification level."""
    counts = CONTROL_COUNTS_BY_LEVEL.get(classification_level, CONTROL_COUNTS_BY_LEVEL['High'])
    return {
        family: (info[0], info[1], counts.get(family, 0))
        for family, info in CONTROL_FAMILY_INFO.items()
    }

# Default to High for backward compatibility
CONTROL_FAMILIES = get_control_families('High')

# AWS Regions
AWS_REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-central-1",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
]


# =============================================================================
# CSS STYLING
# =============================================================================

def apply_custom_css():
    """Apply custom CSS styling - Light grey theme for better readability."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&family=Source+Code+Pro:wght@400;500&display=swap');
        
        /* Main content area - light grey background */
        .main .block-container {
            background-color: #f5f5f5;
            padding: 2rem;
            border-radius: 8px;
        }
        
        html, body, [class*="css"] {
            font-family: 'Source Sans Pro', sans-serif;
        }
        
        code, .stCode, pre {
            font-family: 'Source Code Pro', monospace !important;
        }
        
        .main-header {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #3d7ab5 100%);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            border-left: 5px solid #00d4aa;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }
        
        .main-header h1 {
            color: #ffffff;
            margin: 0;
            font-weight: 700;
            font-size: 1.8rem;
        }
        
        .main-header p {
            color: #b8d4e8;
            margin: 0.5rem 0 0 0;
            font-size: 1rem;
        }
        
        .rev-badge {
            background: #00d4aa;
            color: #1e3a5f;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            margin-left: 1rem;
        }
        
        .family-card {
            background: #ffffff;
            border-radius: 10px;
            padding: 1.25rem;
            margin: 0.5rem 0;
            border-left: 4px solid #3d7ab5;
            transition: transform 0.2s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .family-card:hover {
            transform: translateX(5px);
        }
        
        .family-card h4 {
            color: #1e3a5f;
            margin: 0 0 0.5rem 0;
            font-size: 1rem;
        }
        
        .family-card p {
            color: #4a5568;
            margin: 0;
            font-size: 0.85rem;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 1rem;
            margin: 1.5rem 0;
        }
        
        .metric-box {
            background: #ffffff;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            font-family: 'Source Code Pro', monospace;
        }
        
        .metric-label {
            color: #4a5568;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 0.5rem;
        }
        
        .pass { color: #059669; }
        .fail { color: #dc2626; }
        .warning { color: #d97706; }
        .error { color: #dc2626; }
        .info { color: #2563eb; }
        
        .control-item {
            background: #ffffff;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #cbd5e1;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }
        
        .control-item.pass-item { border-left-color: #059669; }
        .control-item.fail-item { border-left-color: #dc2626; }
        .control-item.warning-item { border-left-color: #d97706; }
        
        .control-id {
            font-family: 'Source Code Pro', monospace;
            font-weight: 600;
            color: #1e3a5f;
            font-size: 0.9rem;
        }
        
        .control-name {
            color: #1f2937;
            font-weight: 600;
            margin-left: 0.5rem;
        }
        
        .finding-box {
            background: #f8fafc;
            padding: 0.5rem 1rem;
            margin: 0.25rem 0;
            border-radius: 4px;
            font-size: 0.9rem;
            color: #374151;
            border: 1px solid #e5e7eb;
        }
        
        .recommendation-box {
            background: #ecfdf5;
            border-left: 3px solid #059669;
            padding: 0.5rem 1rem;
            margin: 0.25rem 0;
            border-radius: 0 4px 4px 0;
            font-size: 0.9rem;
            color: #065f46;
        }
        
        .family-section {
            background: linear-gradient(90deg, #1e3a5f, #3d7ab5);
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin: 2rem 0 1rem 0;
            border-left: 4px solid #059669;
        }
        
        .family-section h2 {
            margin: 0;
            font-size: 1.2rem;
            color: #ffffff;
        }
        
        .family-section span {
            color: #e2e8f0;
            font-size: 0.9rem;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #059669, #047857);
            color: #ffffff;
            border: none;
            padding: 0.75rem 2rem;
            font-weight: 700;
            border-radius: 8px;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #10b981, #059669);
            box-shadow: 0 4px 20px rgba(5, 150, 105, 0.4);
        }
        
        .progress-container {
            background: #ffffff;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid #e5e7eb;
        }
        
        .score-ring {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: conic-gradient(#059669 var(--score), #e5e7eb var(--score));
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
        }
        
        .score-inner {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }
        
        .score-value {
            font-size: 2rem;
            font-weight: 700;
            color: #059669;
        }
        
        .score-label {
            font-size: 0.8rem;
            color: #4a5568;
        }
        
        div[data-testid="stExpander"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
        }
        
        div[data-testid="stExpander"] summary {
            color: #1f2937;
        }
        
        .stats-row {
            display: flex;
            gap: 2rem;
            margin: 1rem 0;
            flex-wrap: wrap;
        }
        
        .stat-item {
            background: #ecfdf5;
            padding: 0.75rem 1.25rem;
            border-radius: 8px;
            border: 1px solid #d1fae5;
        }
        
        .stat-value {
            font-family: 'Source Code Pro', monospace;
            font-size: 1.25rem;
            font-weight: 600;
            color: #059669;
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: #4a5568;
            text-transform: uppercase;
        }
        
        .compliance-bar {
            background: #e5e7eb;
            border-radius: 10px;
            height: 24px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .compliance-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        
        .login-container {
            max-width: 400px;
            margin: 4rem auto;
            padding: 2rem;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        /* Sidebar Control Family toggles - high contrast, force dark checkmarks */
        div[data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stButton > button p {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #94a3b8 !important;
            font-weight: 500 !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
        }
        
        /* Control Family checkboxes - clear/transparent when unchecked, subtle checkmark when checked */
        [data-testid="stSidebar"] input[type="checkbox"] {
            appearance: none;
            -webkit-appearance: none;
            width: 18px !important;
            height: 18px !important;
            min-width: 18px !important;
            min-height: 18px !important;
            border: 2px solid #cbd5e1 !important;
            border-radius: 4px !important;
            background: transparent !important;
            background-color: transparent !important;
            cursor: pointer;
            vertical-align: middle;
        }
        [data-testid="stSidebar"] input[type="checkbox"]:checked {
            background: #dbeafe !important;
            background-color: #dbeafe !important;
            border-color: #3b82f6 !important;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231e3a5f' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='20 6 9 17 4 12'%3E%3C/polyline%3E%3C/svg%3E") !important;
            background-size: 14px 14px !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
        }
        
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_status_emoji(status: ControlStatus) -> str:
    """Get emoji representation for control status."""
    return {
        ControlStatus.PASS: "✅",
        ControlStatus.FAIL: "❌",
        ControlStatus.WARNING: "⚠️",
        ControlStatus.ERROR: "🔴",
        ControlStatus.NOT_APPLICABLE: "➖"
    }.get(status, "❓")


def get_status_class(status: ControlStatus) -> str:
    """Get CSS class for control status."""
    return {
        ControlStatus.PASS: "pass",
        ControlStatus.FAIL: "fail",
        ControlStatus.WARNING: "warning",
        ControlStatus.ERROR: "error",
    }.get(status, "")


def run_openssl_command(args: list) -> str:
    """Run an OpenSSL command and return the output."""
    try:
        result = subprocess.run(
            ["openssl"] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except FileNotFoundError:
        return "Error: OpenSSL not found"
    except Exception as e:
        return f"Error: {str(e)}"


# =============================================================================
# LOGO PATH
# =============================================================================

# Use relative path or environment variable for containerization
# For containers: mount logo to /app/assets or set SAELAR_LOGO_PATH
LOGO_PATH = Path(os.environ.get('SAELAR_LOGO_PATH', Path(__file__).parent / 'assets' / 'saelar_logo.png'))


# =============================================================================
# DASHBOARD COMPONENTS
# =============================================================================

def get_logo_base64() -> str:
    """Get the logo as base64 encoded string."""
    try:
        import base64
        with open(LOGO_PATH, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""


def render_header():
    """Render the main application header with logo."""
    # Scroll to top on page load
    st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"], .main {
            scroll-behavior: auto !important;
        }
    </style>
    <script>
        // Immediate scroll
        window.scrollTo({top: 0, left: 0, behavior: 'instant'});
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
        
        // Delayed scroll to catch after render
        setTimeout(function() {
            window.scrollTo({top: 0, left: 0, behavior: 'instant'});
            var mainContainer = document.querySelector('[data-testid="stAppViewContainer"]');
            if (mainContainer) mainContainer.scrollTop = 0;
        }, 100);
    </script>
    """, unsafe_allow_html=True)
    
    # Logo centered at the top by itself
    if LOGO_PATH.exists():
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image(str(LOGO_PATH), width=286)
    else:
        st.markdown("<h1 style='text-align: center;'>🛡️</h1>", unsafe_allow_html=True)
    
    # Text header below logo - full width for Quality Control-Ready on same line
    st.markdown("""
    <div class="main-header" style="text-align: center; margin-top: 0.5rem;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.2rem;">SAELAR-53</h1>
        <h2 style="font-size: 1.5rem; margin-top: 0; font-weight: 500;">NIST 800-53 Security Controls Assessment <span class="rev-badge">Rev 5</span></h2>
        <p style="white-space: nowrap;">Real-Time Risk Transparency & Remediation | ISSO-Friendly | Quality Control-Ready</p>
    </div>
    """, unsafe_allow_html=True)


def _render_system_info_form():
    """Render the system information form in the sidebar."""
    with st.form("sidebar_system_info_form", clear_on_submit=False):
        system_name = st.text_input(
            "System Name *",
            value=st.session_state.get('system_info_name', ''),
            placeholder="e.g., AWS Cloud Infrastructure",
            key="sidebar_sys_name"
        )
        
        system_acronym = st.text_input(
            "Acronym",
            value=st.session_state.get('system_info_acronym', ''),
            placeholder="e.g., AWS-CI",
            key="sidebar_sys_acronym"
        )
        
        system_owner = st.text_input(
            "System Owner *",
            value=st.session_state.get('system_info_owner', ''),
            placeholder="e.g., IT Security Team",
            key="sidebar_sys_owner"
        )
        
        isso_name = st.text_input(
            "ISSO Name",
            value=st.session_state.get('system_info_isso', ''),
            placeholder="e.g., John Smith",
            key="sidebar_sys_isso"
        )
        
        categorization = st.selectbox(
            "Security Categorization *",
            ["Moderate", "Low", "High"],
            index=["Moderate", "Low", "High"].index(
                st.session_state.get('system_info_categorization', 'Moderate')
            ),
            key="sidebar_sys_cat"
        )
        
        system_description = st.text_area(
            "Description *",
            value=st.session_state.get('system_info_description', ''),
            placeholder="Brief system description...",
            height=80,
            key="sidebar_sys_desc"
        )
        
        submitted = st.form_submit_button("💾 Save System Info", use_container_width=True)
        
        if submitted:
            if system_name and system_owner and system_description:
                st.session_state.system_info_name = system_name
                st.session_state.system_info_acronym = system_acronym
                st.session_state.system_info_owner = system_owner
                st.session_state.system_info_isso = isso_name
                st.session_state.system_info_categorization = categorization
                st.session_state.system_info_description = system_description
                # Save to persistent storage
                save_system_info()
                st.success("✅ System info saved!")
                st.rerun()
            else:
                st.error("Please fill in required fields (*)")


def render_sidebar() -> Tuple[str, List[str], bool]:
    """Render the sidebar with assessment configuration options."""
    # Load system info from persistent storage on first run
    if 'system_info_loaded' not in st.session_state:
        load_system_info()
        st.session_state.system_info_loaded = True
    
    with st.sidebar:
        # System section at very top of sidebar
        st.markdown("### 🏢 System")
        
        has_system_info = bool(st.session_state.get('system_info_name'))
        
        if has_system_info:
            # Show system summary
            st.markdown(f"**{st.session_state.get('system_info_name', 'N/A')}**")
            if st.session_state.get('system_info_acronym'):
                st.markdown(f"*({st.session_state.get('system_info_acronym')})*")
            st.markdown(f"📊 {st.session_state.get('system_info_categorization', 'Moderate')} Impact")
            
            with st.expander("📝 Edit System Info", expanded=False):
                _render_system_info_form()
        else:
            # Show prompt to enter system details
            st.info("⚠️ No system configured")
            with st.expander("📝 Enter System Details", expanded=True):
                _render_system_info_form()
        
        st.markdown("---")
        
        # AWS Account info at top of sidebar
        if st.session_state.get('aws_configured', False):
            st.markdown("### ☁️ AWS Account")
            st.markdown(f"**Account:** `{st.session_state.get('aws_account_id', 'N/A')}`")
            if st.session_state.get('aws_iam_username'):
                st.markdown(f"**User:** `{st.session_state.aws_iam_username}`")
            st.markdown(f"**Region:** `{st.session_state.get('aws_region', 'us-east-1')}`")
            
            if st.button("🔄 Change Account", use_container_width=True, key="change_aws_btn"):
                st.session_state.aws_configured = False
                st.session_state.aws_validated = False
                st.rerun()
            
            st.markdown("---")
        
        st.markdown("### ⚙️ Assessment Configuration")
        
        # Region selection - use AWS region from session state as default
        default_region = st.session_state.get('aws_region', 'us-east-1')
        region_options = ["Default"] + AWS_REGIONS
        default_idx = region_options.index(default_region) if default_region in region_options else 0
        region = st.selectbox("🌍 AWS Region", options=region_options, index=default_idx)
        
        st.markdown("---")
        
        # System Classification Level (FIPS 199)
        st.markdown("### 🏛️ System Classification")
        st.markdown("*FIPS 199 Security Categorization*")
        
        # Initialize classification level in session state
        if 'classification_level' not in st.session_state:
            st.session_state.classification_level = 'Moderate'
        
        # Classification selector
        classification_options = list(CLASSIFICATION_LEVELS.keys())
        current_idx = classification_options.index(st.session_state.classification_level)
        
        selected_classification = st.selectbox(
            "Impact Level",
            options=classification_options,
            index=current_idx,
            key="classification_selector",
            help="Select the security impact level based on FIPS 199"
        )
        
        # Update session state if changed
        if selected_classification != st.session_state.classification_level:
            st.session_state.classification_level = selected_classification
            # Clear checkbox states to reset with new counts
            for family_code in CONTROL_FAMILY_INFO.keys():
                if f"sidebar_family_{family_code}" in st.session_state:
                    del st.session_state[f"sidebar_family_{family_code}"]
            st.session_state.selected_families = []
            if "cf_multiselect" in st.session_state:
                del st.session_state["cf_multiselect"]
            st.rerun()
        
        # Show classification info
        level_info = CLASSIFICATION_LEVELS[selected_classification]
        total_controls = sum(CONTROL_COUNTS_BY_LEVEL[selected_classification].values())
        
        st.markdown(f"""
        <div style="background: {level_info['color']}15; border-left: 4px solid {level_info['color']}; 
                    padding: 0.75rem; border-radius: 4px; margin: 0.5rem 0;">
            <div style="font-weight: 600; color: {level_info['color']};">
                {level_info['icon']} {selected_classification} Impact
            </div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem;">
                {level_info['description']}
            </div>
            <div style="font-size: 0.85rem; color: #1e3a5f; margin-top: 0.5rem; font-weight: 500;">
                📊 {total_controls} controls available
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div id="saelar-cf-section" style="margin-bottom: 0.75rem;">
            <h3 style="color: #1e3a5f; font-size: 1.1rem; margin: 0 0 0.25rem 0; font-weight: 700;">📋 Control Families</h3>
            <p style="color: #64748b; font-size: 0.85rem; margin: 0;">Select one or more families to assess</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick select - solid colors for Select All/Clear All (identical size, readable text)
        # Only target blocks where BOTH columns have buttons (excludes Security Hub row)
        st.markdown("""
        <style>
            /* Parent row: flex with equal flex-basis for guaranteed identical column widths */
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:not(:has([data-testid="stCheckbox"])):has(> :nth-of-type(1) .stButton):has(> :nth-of-type(2) .stButton) {
                display: flex !important;
                gap: 0.5rem !important;
                width: 100% !important;
            }
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:not(:has([data-testid="stCheckbox"])):has(> :nth-of-type(1) .stButton):has(> :nth-of-type(2) .stButton) > * {
                flex: 0 0 calc(50% - 0.25rem) !important;
                min-width: 0 !important;
                max-width: calc(50% - 0.25rem) !important;
            }
            /* stButton wrapper - fill column */
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:not(:has([data-testid="stCheckbox"])):has(> :nth-of-type(1) .stButton):has(> :nth-of-type(2) .stButton) .stButton {
                width: 100% !important;
                min-width: 0 !important;
            }
            /* Both Select All and Clear All - identical fixed size */
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:not(:has([data-testid="stCheckbox"])):has(> :nth-of-type(1) .stButton):has(> :nth-of-type(2) .stButton) .stButton > button {
                width: 100% !important;
                min-width: 0 !important;
                height: 52px !important;
                min-height: 52px !important;
                max-height: 52px !important;
                padding: 0.5rem 0.5rem !important;
                border-radius: 10px !important;
                font-weight: 600 !important;
                font-size: 0.9rem !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                box-sizing: border-box !important;
                white-space: nowrap !important;
            }
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:not(:has([data-testid="stCheckbox"])):has(> :nth-of-type(1) .stButton):has(> :nth-of-type(2) .stButton) .stButton > button p {
                white-space: nowrap !important;
            }
            /* Select All - solid green */
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:not(:has([data-testid="stCheckbox"])):has(> :nth-of-type(1) .stButton):has(> :nth-of-type(2) .stButton) > :nth-of-type(1) .stButton > button {
                background: #059669 !important;
                background-color: #059669 !important;
                color: white !important;
                border: none !important;
            }
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:not(:has([data-testid="stCheckbox"])):has(> :nth-of-type(1) .stButton):has(> :nth-of-type(2) .stButton) > :nth-of-type(1) .stButton > button p {
                color: white !important;
                background: transparent !important;
            }
            /* Clear All - solid teal, same size as Select All */
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:not(:has([data-testid="stCheckbox"])):has(> :nth-of-type(1) .stButton):has(> :nth-of-type(2) .stButton) > :nth-of-type(2) .stButton > button {
                background: #0d9488 !important;
                background-color: #0d9488 !important;
                color: white !important;
                border: none !important;
            }
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:not(:has([data-testid="stCheckbox"])):has(> :nth-of-type(1) .stButton):has(> :nth-of-type(2) .stButton) > :nth-of-type(2) .stButton > button p {
                color: white !important;
                background: transparent !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            select_all = st.button("✅ Select All", use_container_width=True, key="select_all_btn")
        with col2:
            clear_all = st.button("↻ Clear All", use_container_width=True, key="clear_all_btn")
        
        # Get control families based on current classification level
        current_classification = st.session_state.get('classification_level', 'Moderate')
        current_control_families = get_control_families(current_classification)
        
        # Initialize session state for selections
        if 'selected_families' not in st.session_state:
            st.session_state.selected_families = []
        
        # Handle select/clear all - update checkbox widget states
        if select_all:
            st.session_state.selected_families = list(current_control_families.keys())
            for family_code in current_control_families.keys():
                st.session_state[f"sidebar_family_{family_code}"] = True
            st.rerun()
        if clear_all:
            st.session_state.selected_families = []
            for family_code in current_control_families.keys():
                st.session_state[f"sidebar_family_{family_code}"] = False
            st.rerun()
        
        st.markdown("---")
        
        # NIST 800-53 documentation links for each control family
        NIST_LINKS = {
            'AC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AC',
            'AT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AT',
            'AU': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AU',
            'CA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CA',
            'CM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM',
            'CP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CP',
            'IA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IA',
            'IR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IR',
            'MA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MA',
            'MP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MP',
            'PE': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PE',
            'PL': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PL',
            'PM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PM',
            'PS': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PS',
            'PT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PT',
            'RA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=RA',
            'SA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SA',
            'SC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SC',
            'SI': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SI',
            'SR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SR',
        }
        
        # Control family list - card-style rows with checkboxes
        st.markdown("""
        <style>
        /* Control family checkbox rows - card styling */
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) {
            background: rgba(30, 58, 95, 0.04) !important;
            border-radius: 8px !important;
            padding: 0.5rem 0.75rem !important;
            margin: 0.2rem 0 !important;
            border-left: 3px solid #3d7ab5 !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]):hover {
            background: rgba(30, 58, 95, 0.08) !important;
            border-left-color: #00d4aa !important;
        }
        /* Security Hub - solid light blue tile, dark text for readability */
        [data-testid="stSidebar"] .stButton > button {
            background: #dbeafe !important;
            background-color: #dbeafe !important;
            color: #1e3a5f !important;
            border: 1px solid #93c5fd !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #bfdbfe !important;
            background-color: #bfdbfe !important;
            color: #0f172a !important;
        }
        [data-testid="stSidebar"] .stButton > button p {
            color: #1e3a5f !important;
            background: transparent !important;
            background-color: transparent !important;
        }
        /* Run Assessment - solid green tile, white text (primary CTA) - last full-width button before Control Counts */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"]:has(> div:only-child) .stButton > button {
            background: #059669 !important;
            background-color: #059669 !important;
            color: white !important;
            border: none !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"]:has(> div:only-child) .stButton > button p {
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Individual checkboxes for each family with NIST links (visible list)
        selected_families = []
        for family_code, (display_name, description, count) in current_control_families.items():
            checkbox_key = f"sidebar_family_{family_code}"

            # Initialize checkbox state if not already set
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = family_code in st.session_state.selected_families

            nist_url = NIST_LINKS.get(family_code, '#')

            # Create a container with checkbox and info link
            col_check, col_link = st.columns([6, 1])

            with col_check:
                checked = st.checkbox(
                    f"{display_name} ({count})",
                    key=checkbox_key,
                    help=f"{description} - Click 🔗 for NIST documentation"
                )
                if checked:
                    selected_families.append(family_code)

            with col_link:
                st.markdown(f"""
                <a href="{nist_url}" target="_blank" title="View {family_code} in NIST 800-53"
                   style="text-decoration: none; font-size: 1.1rem; opacity: 0.7; transition: opacity 0.2s;"
                   onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.7'">
                    🔗
                </a>
                """, unsafe_allow_html=True)

        st.session_state.selected_families = selected_families

        # NIST docs link (compact)
        st.markdown("[📖 NIST 800-53 Rev 5 Control Catalog](https://csrc.nist.gov/projects/cprt/catalog)", unsafe_allow_html=True)
        
        # Show selection summary
        total_controls = sum(current_control_families[f][2] for f in selected_families) if selected_families else 0
        
        if selected_families:
            st.markdown(f"""
            <div class='family-card'>
                <h4>📊 Selection Summary</h4>
                <p><strong>{len(selected_families)}</strong> families selected<br/>
                <strong>{total_controls}</strong> controls to assess</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Please select at least one family")
        
        st.markdown("---")
        
        # Security Hub Integration Option
        # Make the header a clickable button to view Security Hub findings (full-width for solid gray tile)
        view_security_hub = st.button(
            "🔗 Security Hub Findings",
            use_container_width=True,
            help="Click to view ONLY Security Hub findings"
        )
        
        # Store in session state for the main content area to handle
        if view_security_hub:
            st.session_state.show_security_hub_only = True
        
        include_security_hub = st.checkbox(
            "Include in Assessment",
            value=False,
            help="Import findings from AWS Security Hub to supplement SAELAR assessments. "
                 "This aggregates findings from GuardDuty, Inspector, Macie, and other AWS security services."
        )
        
        if include_security_hub:
            st.info("📥 Security Hub findings will be imported and mapped to NIST 800-53 control families.")
        
        st.markdown("---")
        
        run_assessment = st.button(
            f"🚀 Run Assessment ({total_controls} controls)", 
            use_container_width=True,
            disabled=len(selected_families) == 0
        )
        
        st.markdown("---")
        # Build dynamic Control Counts Reference table based on classification level
        level_info = CLASSIFICATION_LEVELS[current_classification]
        table_total = sum(current_control_families[f][2] for f in current_control_families)
        
        st.markdown(f"### 📊 Control Counts ({current_classification})")
        
        # Build table rows dynamically
        NIST_LINKS = {
            'AC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AC',
            'AT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AT',
            'AU': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AU',
            'CA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CA',
            'CM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM',
            'CP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CP',
            'IA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IA',
            'IR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IR',
            'MA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MA',
            'MP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MP',
            'PE': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PE',
            'PL': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PL',
            'PM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PM',
            'PS': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PS',
            'PT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PT',
            'RA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=RA',
            'SA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SA',
            'SC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SC',
            'SI': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SI',
            'SR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SR',
        }
        table_rows = ""
        family_names = {
            'AC': 'Access Control', 'AT': 'Awareness & Training', 'AU': 'Audit & Accountability',
            'CA': 'Assessment & Authorization', 'CM': 'Configuration Management', 'CP': 'Contingency Planning',
            'IA': 'Identification & Auth', 'IR': 'Incident Response', 'MA': 'Maintenance',
            'MP': 'Media Protection', 'PE': 'Physical & Environmental', 'PL': 'Planning',
            'PM': 'Program Management', 'PS': 'Personnel Security', 'PT': 'PII Processing',
            'RA': 'Risk Assessment', 'SA': 'System Acquisition', 'SC': 'System & Comms Protection',
            'SI': 'System Integrity', 'SR': 'Supply Chain'
        }
        NIST_LINKS = {
            'AC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AC',
            'AT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AT',
            'AU': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=AU',
            'CA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CA',
            'CM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM',
            'CP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CP',
            'IA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IA',
            'IR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IR',
            'MA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MA',
            'MP': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=MP',
            'PE': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PE',
            'PL': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PL',
            'PM': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PM',
            'PS': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PS',
            'PT': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=PT',
            'RA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=RA',
            'SA': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SA',
            'SC': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SC',
            'SI': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SI',
            'SR': 'https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SR',
        }
        for family_code, (display_name, description, count) in current_control_families.items():
            nist_url = NIST_LINKS.get(family_code, '#')
            short_name = family_names.get(family_code, display_name)
            table_rows += f'<tr><td><a href="{nist_url}" target="_blank">{family_code} - {short_name}</a></td><td><a class="count-link" href="{nist_url}" target="_blank">{count}</a></td></tr>'
        
        st.markdown(f"""
        <style>
            .control-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
            .control-table th {{ background: #dbeafe; color: #1e3a5f; padding: 0.5rem; text-align: left; }}
            .control-table td {{ padding: 0.4rem 0.5rem; border-bottom: 1px solid #e5e7eb; }}
            .control-table tr:hover {{ background: #f0f9ff; }}
            .control-table a {{ color: #2563eb; text-decoration: none; font-weight: 600; }}
            .control-table a:hover {{ text-decoration: underline; color: #1d4ed8; }}
            .control-table .count-link {{ color: #059669; font-weight: bold; }}
            .control-table .count-link:hover {{ color: #047857; }}
            .control-table .total-row {{ font-weight: bold; background: #f1f5f9; }}
        </style>
        <table class="control-table">
            <tr><th>Family</th><th>Controls</th></tr>
            {table_rows}
            <tr class="total-row"><td><strong>Total</strong></td><td><strong>{table_total}</strong></td></tr>
        </table>
        """, unsafe_allow_html=True)
        
        return region, selected_families, run_assessment, include_security_hub


def render_metrics(summary: dict):
    """Render the metrics dashboard showing assessment results with clickable links."""
    total = summary['total_controls']
    passed = summary['passed']
    failed = summary['failed']
    warnings = summary['warnings']
    
    applicable = total - summary.get('errors', 0)
    score = (passed / applicable * 100) if applicable > 0 else 0
    
    # Determine score color
    if score >= 80:
        score_color = "#059669"  # Green
    elif score >= 60:
        score_color = "#d97706"  # Amber
    else:
        score_color = "#dc2626"  # Red
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <a href="#passed-findings" style="text-decoration: none;">
            <div class="metric-box" style="cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                <div class="metric-value pass">{passed}</div>
                <div class="metric-label">Passed</div>
            </div>
        </a>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <a href="#failed-findings" style="text-decoration: none;">
            <div class="metric-box" style="cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                <div class="metric-value fail">{failed}</div>
                <div class="metric-label">Failed</div>
            </div>
        </a>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <a href="#warning-findings" style="text-decoration: none;">
            <div class="metric-box" style="cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                <div class="metric-value warning">{warnings}</div>
                <div class="metric-label">Warnings</div>
            </div>
        </a>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <a href="#all-findings" style="text-decoration: none;">
            <div class="metric-box" style="cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                <div class="metric-value info">{total}</div>
                <div class="metric-label">Total</div>
            </div>
        </a>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value" style="color: {score_color};">{score:.0f}%</div>
            <div class="metric-label">Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Compliance bar
    st.markdown(f"""
    <div class="compliance-bar">
        <div class="compliance-fill" style="width: {score}%; background: linear-gradient(90deg, #059669, #10b981);"></div>
    </div>
    """, unsafe_allow_html=True)


def render_family_summary(summary: dict, family_names: dict):
    """Render summary cards for each control family as clickable links."""
    st.markdown('<div id="family-summary"></div>', unsafe_allow_html=True)
    st.markdown("### 📋 Results by Control Family")
    st.markdown("*Click any family card to see detailed findings*")
    
    cols = st.columns(4)
    idx = 0
    
    for family, counts in summary.get('by_family', {}).items():
        with cols[idx % 4]:
            total = sum(counts.values())
            passed = counts.get('pass', 0)
            failed = counts.get('fail', 0)
            pct = (passed / total * 100) if total > 0 else 0
            
            # Determine color based on status
            if failed > 0:
                color = "#dc2626"
                bg_color = "linear-gradient(135deg, #fef2f2 0%, #fecaca 100%)"
                border_color = "#fca5a5"
            elif pct >= 80:
                color = "#059669"
                bg_color = "linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)"
                border_color = "#86efac"
            else:
                color = "#d97706"
                bg_color = "linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)"
                border_color = "#fcd34d"
            
            st.markdown(f"""
            <a href="#family-{family}" style="text-decoration: none;">
                <div style="background: {bg_color}; border: 2px solid {border_color}; border-radius: 10px;
                            padding: 1rem; margin: 0.25rem 0; cursor: pointer; transition: all 0.2s ease;"
                     onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(0,0,0,0.15)';"
                     onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                    <h4 style="margin: 0; color: #1e3a5f; font-size: 1.1rem;">{family}</h4>
                    <p style="margin: 0.25rem 0; color: #64748b; font-size: 0.85rem;">{family_names.get(family, family)}</p>
                    <div style="margin-top: 0.5rem;">
                        <span style="color: {color}; font-weight: 700; font-size: 1.1rem;">{passed}/{total}</span>
                        <span style="color: #64748b; font-size: 0.85rem;"> passed ({pct:.0f}%)</span>
                    </div>
                    <div style="text-align: right; margin-top: 0.25rem;">
                        <span style="color: #94a3b8; font-size: 0.75rem;">↓ View details</span>
                    </div>
                </div>
            </a>
            """, unsafe_allow_html=True)
        idx += 1


def render_welcome_screen():
    """Render the welcome screen when no assessment has been run."""
    
    # Get current classification level and control families
    current_classification = st.session_state.get('classification_level', 'Moderate')
    current_control_families = get_control_families(current_classification)
    level_info = CLASSIFICATION_LEVELS[current_classification]
    total_controls = sum(current_control_families[f][2] for f in current_control_families)
    
    # Two-column layout: compact control list on left, info on right
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown(f"""
        <div style="background: #ffffff; border-radius: 10px; padding: 1rem; border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h4 style="color: #1e3a5f; margin: 0 0 0.5rem 0; font-size: 0.95rem;">📋 Control Families</h4>
            <div style="font-size: 0.75rem; color: {level_info['color']}; font-weight: 600;">
                {level_info['icon']} {current_classification} Impact ({total_controls} controls)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Compact vertical listing of all control families
        for family_code, (display_name, description, count) in current_control_families.items():
            st.markdown(f"""
            <div style="
                background: #f8fafc;
                border-left: 3px solid #3d7ab5;
                padding: 0.5rem 0.75rem;
                margin: 0.25rem 0;
                border-radius: 0 4px 4px 0;
                font-size: 0.85rem;
            ">
                <span style="font-weight: 600; color: #1e3a5f;">{display_name}</span>
                <span style="color: #64748b; font-size: 0.75rem;"> ({count})</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col_right:
        # Chad (AI)'s avatar and Ready to Assess section
        from pathlib import Path
        import base64
        
        chad_avatar_path = Path(__file__).parent / 'assets' / 'chad_avatar.png'
        
        # Build Chad (AI) avatar HTML (156px = 120 * 1.3 = 30% larger)
        if chad_avatar_path.exists():
            with open(chad_avatar_path, "rb") as img_file:
                chad_img_data = base64.b64encode(img_file.read()).decode()
            chad_avatar_html = f'<img src="data:image/png;base64,{chad_img_data}" style="width: 156px; height: 156px; border-radius: 12px; object-fit: cover; border: 3px solid #3b82f6; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);" alt="Chad (AI)">'
        else:
            chad_avatar_html = '<div style="width: 156px; height: 156px; background: linear-gradient(135deg, #3b82f6 0%, #1e3a5f 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 4rem; border: 3px solid #3b82f6; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);">🛡️</div>'
        
        st.markdown(f"""
        <div style="display: flex; align-items: flex-start; gap: 1.5rem; padding: 2rem; background: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <div style="flex-shrink: 0;">
                {chad_avatar_html}
                <div style="text-align: center; margin-top: 0.5rem;">
                    <span style="font-weight: 700; color: #1e3a5f; font-size: 1.1rem;">Chad (AI)</span><br/>
                    <span style="color: #3b82f6; font-size: 0.85rem;">Security Analyst</span>
                </div>
            </div>
            <div style="flex: 1;">
                <h2 style="color: #1e3a5f; margin: 0 0 0.75rem 0;">🎯 Ready to Assess</h2>
                <p style="color: #4a5568; font-size: 0.95rem; margin: 0 0 1rem 0;">
                    Select one or more control families from the <strong style="color: #059669;">sidebar</strong> using the checkboxes, 
                    then click <strong style="color: #059669;">Run Assessment</strong>.
                </p>
                <p style="color: #4a5568; font-size: 0.95rem; margin: 0 0 1rem 0;">
                    Use <strong style="color: #059669;">Select All</strong> for a comprehensive assessment 
                    or pick specific families to focus your evaluation.
                </p>
                <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 0.75rem; margin-top: 0.5rem;">
                    <p style="color: #0369a1; margin: 0; font-size: 0.9rem;">
                        💬 <strong>Ask me anything!</strong> After your assessment, I can help analyze findings, generate reports, and provide remediation guidance.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # Quick stats - dynamic based on classification level
        st.markdown("### 📊 Assessment Overview")
        
        num_families = len(current_control_families)
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.metric("Control Families", str(num_families))
        with stat_col2:
            st.metric("Total Controls", str(total_controls))
        with stat_col3:
            st.metric("Classification", current_classification)
        
        # Threat Modeling Section
        st.markdown("<br/>", unsafe_allow_html=True)
        render_threat_modeling_section()


def render_threat_modeling_section(assessment_data=None, findings=None):
    """
    Render the Threat Modeling section.
    Maps relationships between security controls, gaps, assets, threats,
    and frameworks like MITRE ATT&CK with actuarial data integration.
    
    Args:
        assessment_data: Optional NIST assessment results from session state
        findings: Optional Risk Calculator findings for integration
    """
    # Try to get assessment data from session state if not provided
    if assessment_data is None:
        assessment_data = st.session_state.get('results', None)
    
    # Check if we have real assessment data
    has_real_data = assessment_data is not None and len(assessment_data) > 0
    
    st.markdown("### 🥷 Threat Modeling")
    
    # Show data source indicator
    if has_real_data:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #059669 0%, #047857 100%); 
                    padding: 0.5rem 1rem; border-radius: 6px; margin-bottom: 0.5rem; display: inline-block;">
            <span style="color: #ffffff; font-size: 0.85rem;">✅ <strong>LIVE DATA</strong> — Integrated with NIST Assessment Results</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: #f1f5f9; border: 1px solid #cbd5e1; 
                    padding: 0.5rem 1rem; border-radius: 6px; margin-bottom: 0.5rem; display: inline-block;">
            <span style="color: #64748b; font-size: 0.85rem;">📊 Showing baseline data — Run NIST Assessment for live integration</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Header with explanation
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #3d7ab5 100%); 
                padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #f59e0b;">
        <p style="color: #ffffff; margin: 0; font-size: 0.95rem;">
            <strong>Continuous Threat Intelligence</strong> — Mapping security controls to threats, assets, 
            and analytical frameworks to transform unknowns into actionable intelligence.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Threat modeling tabs
    tm_tab1, tm_tab2, tm_tab3, tm_tab4 = st.tabs([
        "🔗 Control-Threat Mapping", 
        "🏢 Asset-Threat Matrix", 
        "⚔️ MITRE ATT&CK Coverage",
        "📊 Actuarial Risk Data"
    ])
    
    with tm_tab1:
        _render_control_threat_mapping(assessment_data)
    
    with tm_tab2:
        _render_asset_threat_matrix(assessment_data)
    
    with tm_tab3:
        _render_mitre_attack_coverage(assessment_data)
    
    with tm_tab4:
        _render_actuarial_risk_data(assessment_data)


def _render_control_threat_mapping(assessment_data=None):
    """Render the Control-to-Threat mapping visualization."""
    st.markdown("#### Security Control Gap Analysis")
    
    # Calculate real coverage from assessment data if available
    family_stats = {}
    if assessment_data:
        for result in assessment_data:
            family = result.control_id.split('-')[0] if hasattr(result, 'control_id') else 'Unknown'
            if family not in family_stats:
                family_stats[family] = {'passed': 0, 'failed': 0, 'warning': 0, 'total': 0, 'findings': []}
            family_stats[family]['total'] += 1
            if hasattr(result, 'status'):
                status_name = result.status.name if hasattr(result.status, 'name') else str(result.status)
                if status_name == 'PASS':
                    family_stats[family]['passed'] += 1
                elif status_name == 'FAIL':
                    family_stats[family]['failed'] += 1
                    family_stats[family]['findings'].append(result)
                elif status_name == 'WARNING':
                    family_stats[family]['warning'] += 1
                    family_stats[family]['findings'].append(result)
    
    # Base threat mapping data with dynamic coverage
    control_threat_mappings = {
        "AC (Access Control)": {
            "family_code": "AC",
            "threats": ["Unauthorized Access", "Privilege Escalation", "Credential Theft"],
            "mitre_tactics": ["Initial Access", "Privilege Escalation", "Credential Access"],
            "gap_indicators": ["MFA not enforced", "Excessive permissions", "Stale accounts"],
            "coverage": 78
        },
        "AU (Audit & Accountability)": {
            "family_code": "AU",
            "threats": ["Log Tampering", "Forensic Evasion", "Insider Threats"],
            "mitre_tactics": ["Defense Evasion", "Collection"],
            "gap_indicators": ["Incomplete logging", "No log integrity verification", "Short retention"],
            "coverage": 65
        },
        "CA (Assessment & Authorization)": {
            "family_code": "CA",
            "threats": ["Compliance Gaps", "Unassessed Risks", "Shadow IT"],
            "mitre_tactics": ["Discovery", "Lateral Movement"],
            "gap_indicators": ["Outdated assessments", "Missing ATO documentation"],
            "coverage": 82
        },
        "CM (Configuration Management)": {
            "family_code": "CM",
            "threats": ["Misconfigurations", "Drift", "Vulnerable Defaults"],
            "mitre_tactics": ["Execution", "Persistence", "Defense Evasion"],
            "gap_indicators": ["No baseline enforcement", "Manual config changes"],
            "coverage": 71
        },
        "CP (Contingency Planning)": {
            "family_code": "CP",
            "threats": ["Service Disruption", "Data Loss", "Ransomware"],
            "mitre_tactics": ["Impact"],
            "gap_indicators": ["Untested backups", "No DR plan", "Single point of failure"],
            "coverage": 58
        },
        "IA (Identification & Authentication)": {
            "family_code": "IA",
            "threats": ["Identity Spoofing", "Brute Force", "Pass-the-Hash"],
            "mitre_tactics": ["Initial Access", "Credential Access"],
            "gap_indicators": ["Weak password policy", "No MFA", "Shared accounts"],
            "coverage": 85
        },
        "IR (Incident Response)": {
            "family_code": "IR",
            "threats": ["Delayed Detection", "Inadequate Response", "Evidence Loss"],
            "mitre_tactics": ["Command and Control", "Exfiltration"],
            "gap_indicators": ["No IR playbooks", "Untrained staff", "No forensic capability"],
            "coverage": 62
        },
        "SC (System & Communications Protection)": {
            "family_code": "SC",
            "threats": ["Data Interception", "MITM Attacks", "Data Exfiltration"],
            "mitre_tactics": ["Exfiltration", "Command and Control"],
            "gap_indicators": ["Unencrypted data", "Open ports", "No network segmentation"],
            "coverage": 74
        }
    }
    
    # Update coverage with real data if available
    for family_name, data in control_threat_mappings.items():
        family_code = data.get("family_code", "")
        if family_code in family_stats and family_stats[family_code]['total'] > 0:
            stats = family_stats[family_code]
            # Calculate coverage as percentage of passed controls
            data['coverage'] = int((stats['passed'] / stats['total']) * 100)
            data['assessed'] = True
            data['stats'] = stats
        else:
            data['assessed'] = False
    
    # Display as expandable cards
    for family, data in control_threat_mappings.items():
        coverage = data["coverage"]
        is_assessed = data.get('assessed', False)
        
        if coverage >= 80:
            color = "#22c55e"
            status = "Strong"
            emoji = "🟢"
        elif coverage >= 65:
            color = "#f59e0b"
            status = "Moderate"
            emoji = "🟡"
        else:
            color = "#ef4444"
            status = "Weak"
            emoji = "🔴"
        
        # Show live data indicator if assessed
        data_badge = " 📡" if is_assessed else ""
        
        with st.expander(f"{emoji} **{family}** — Coverage: {coverage}% ({status}){data_badge}", expanded=False):
            # Show live data stats if available
            if is_assessed and 'stats' in data:
                stats = data['stats']
                st.markdown(f"""
                <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 6px; padding: 0.5rem; margin-bottom: 1rem;">
                    <strong>📊 Live Assessment Data:</strong> {stats['passed']} passed, {stats['failed']} failed, {stats['warning']} warnings out of {stats['total']} controls
                </div>
                """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Mapped Threats:**")
                for threat in data["threats"]:
                    st.markdown(f"- 🎯 {threat}")
                
                st.markdown("**MITRE Tactics:**")
                for tactic in data["mitre_tactics"]:
                    st.markdown(f"- ⚔️ {tactic}")
            
            with col2:
                st.markdown("**Gap Indicators:**")
                for gap in data["gap_indicators"]:
                    st.markdown(f"- ⚠️ {gap}")
                
                # Coverage bar
                st.markdown("**Control Coverage:**")
                st.progress(coverage / 100)
                
                # Show actual findings if available
                if is_assessed and 'stats' in data and data['stats']['findings']:
                    st.markdown("**🔍 Actual Findings from Assessment:**")
                    for finding in data['stats']['findings'][:5]:
                        control_id = finding.control_id if hasattr(finding, 'control_id') else 'Unknown'
                        title = finding.title if hasattr(finding, 'title') else str(finding)
                        status_name = finding.status.name if hasattr(finding, 'status') and hasattr(finding.status, 'name') else 'Unknown'
                        st.markdown(f"- `{control_id}` ({status_name}): {title[:50]}...")


def _render_asset_threat_matrix(assessment_data=None):
    """Render the Asset-Threat relationship matrix."""
    st.markdown("#### Asset-Threat Relationship Matrix")
    
    st.markdown("""
    <p style="color: #64748b; margin-bottom: 1rem;">
        Map critical assets to potential threats and attack vectors for prioritized protection.
    </p>
    """, unsafe_allow_html=True)
    
    # Asset categories with threat exposure
    asset_threat_data = {
        "Asset Category": [
            "Identity & Access (IAM)",
            "Compute (EC2/Lambda)",
            "Storage (S3/EBS)",
            "Database (RDS/DynamoDB)",
            "Network (VPC/CloudFront)",
            "Secrets (KMS/Secrets Manager)",
            "Logging (CloudTrail/CloudWatch)"
        ],
        "Primary Threats": [
            "Credential Theft, Privilege Escalation",
            "Cryptomining, RCE, Lateral Movement",
            "Data Exfiltration, Ransomware",
            "SQL Injection, Data Breach",
            "DDoS, MITM, Reconnaissance",
            "Key Compromise, Unauthorized Decryption",
            "Log Tampering, Evidence Destruction"
        ],
        "Attack Likelihood": ["High", "Critical", "Critical", "High", "Medium", "High", "Medium"],
        "Business Impact": ["Critical", "High", "Critical", "Critical", "High", "Critical", "High"],
        "Risk Score": [9.2, 8.8, 9.5, 9.1, 7.4, 8.9, 7.8]
    }
    
    df = pd.DataFrame(asset_threat_data)
    
    # Style the dataframe
    def color_risk(val):
        if val >= 9.0:
            return 'background-color: #fecaca; color: #991b1b'
        elif val >= 8.0:
            return 'background-color: #fed7aa; color: #9a3412'
        elif val >= 7.0:
            return 'background-color: #fef08a; color: #854d0e'
        else:
            return 'background-color: #bbf7d0; color: #166534'
    
    styled_df = df.style.applymap(color_risk, subset=['Risk Score'])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Risk distribution chart
    st.markdown("#### Risk Distribution by Asset Category")
    st.markdown("<p style='color: #64748b; font-size: 0.9rem;'>Click any asset below for detailed threat analysis</p>", unsafe_allow_html=True)
    
    chart_data = pd.DataFrame({
        'Asset': asset_threat_data["Asset Category"],
        'Risk Score': asset_threat_data["Risk Score"]
    })
    st.bar_chart(chart_data.set_index('Asset'))
    
    # Detailed expandable sections for each asset
    asset_details = {
        "Identity & Access (IAM)": {
            "description": "AWS Identity and Access Management controls who can access what resources.",
            "key_resources": ["IAM Users", "IAM Roles", "IAM Policies", "Identity Providers", "Access Keys"],
            "attack_vectors": [
                "Credential stuffing attacks using leaked password databases",
                "Phishing campaigns targeting admin users",
                "Access key exposure in code repositories",
                "Privilege escalation through policy misconfiguration",
                "Cross-account role assumption abuse"
            ],
            "mitre_techniques": ["T1078 - Valid Accounts", "T1098 - Account Manipulation", "T1136 - Create Account"],
            "controls": ["AC-2", "AC-3", "AC-6", "IA-2", "IA-5"],
            "mitigations": [
                "Enforce MFA on all human users",
                "Implement least privilege access",
                "Rotate access keys every 90 days",
                "Use IAM Access Analyzer regularly",
                "Enable CloudTrail for all IAM events"
            ]
        },
        "Compute (EC2/Lambda)": {
            "description": "Compute resources including virtual servers and serverless functions.",
            "key_resources": ["EC2 Instances", "Lambda Functions", "ECS Containers", "EKS Clusters", "AMIs"],
            "attack_vectors": [
                "Cryptomining malware via exposed instances",
                "Remote code execution through vulnerable applications",
                "Container escape attacks",
                "Malicious Lambda layer injection",
                "SSRF attacks against instance metadata"
            ],
            "mitre_techniques": ["T1496 - Resource Hijacking", "T1059 - Command and Scripting", "T1610 - Deploy Container"],
            "controls": ["CM-7", "SI-3", "SI-4", "SC-7"],
            "mitigations": [
                "Use IMDSv2 for instance metadata",
                "Implement security groups with least privilege",
                "Enable GuardDuty for runtime threat detection",
                "Use Inspector for vulnerability scanning",
                "Restrict Lambda execution roles"
            ]
        },
        "Storage (S3/EBS)": {
            "description": "Object storage and block storage containing sensitive data.",
            "key_resources": ["S3 Buckets", "EBS Volumes", "EFS File Systems", "Glacier Vaults", "S3 Access Points"],
            "attack_vectors": [
                "Publicly exposed S3 buckets",
                "Ransomware encryption of EBS volumes",
                "Data exfiltration via misconfigured bucket policies",
                "Snapshot exposure across accounts",
                "Unencrypted data at rest"
            ],
            "mitre_techniques": ["T1530 - Data from Cloud Storage", "T1537 - Transfer Data to Cloud Account", "T1486 - Data Encrypted for Impact"],
            "controls": ["SC-28", "MP-2", "AC-3", "AU-9"],
            "mitigations": [
                "Enable S3 Block Public Access at account level",
                "Use S3 Object Lock for ransomware protection",
                "Enable default encryption (SSE-S3/SSE-KMS)",
                "Implement S3 access logging",
                "Use Macie for sensitive data discovery"
            ]
        },
        "Database (RDS/DynamoDB)": {
            "description": "Managed database services storing structured business data.",
            "key_resources": ["RDS Instances", "DynamoDB Tables", "Aurora Clusters", "ElastiCache", "DocumentDB"],
            "attack_vectors": [
                "SQL injection through vulnerable applications",
                "Publicly accessible database endpoints",
                "Weak database credentials",
                "Unencrypted database backups",
                "Cross-account snapshot sharing"
            ],
            "mitre_techniques": ["T1190 - Exploit Public-Facing Application", "T1213 - Data from Information Repositories"],
            "controls": ["SC-28", "AC-3", "AU-12", "SC-8"],
            "mitigations": [
                "Place databases in private subnets only",
                "Enable encryption at rest and in transit",
                "Use IAM database authentication",
                "Enable Performance Insights for anomaly detection",
                "Implement automated backup retention"
            ]
        },
        "Network (VPC/CloudFront)": {
            "description": "Virtual network infrastructure and content delivery.",
            "key_resources": ["VPCs", "Subnets", "Security Groups", "NACLs", "CloudFront Distributions", "Route 53"],
            "attack_vectors": [
                "DDoS attacks against public endpoints",
                "Man-in-the-middle attacks on unencrypted traffic",
                "Network reconnaissance and port scanning",
                "DNS hijacking or cache poisoning",
                "Overly permissive security group rules"
            ],
            "mitre_techniques": ["T1498 - Network Denial of Service", "T1046 - Network Service Scanning", "T1557 - Man-in-the-Middle"],
            "controls": ["SC-7", "SC-8", "AC-4", "SI-4"],
            "mitigations": [
                "Enable AWS Shield Advanced for DDoS protection",
                "Use VPC Flow Logs for network monitoring",
                "Implement WAF rules on CloudFront/ALB",
                "Use private subnets for internal resources",
                "Enable DNSSEC on Route 53 hosted zones"
            ]
        },
        "Secrets (KMS/Secrets Manager)": {
            "description": "Cryptographic keys and secret management services.",
            "key_resources": ["KMS Keys", "Secrets Manager Secrets", "Parameter Store SecureStrings", "CloudHSM"],
            "attack_vectors": [
                "Unauthorized key access through policy misconfig",
                "Secrets exposure in application logs",
                "Key deletion causing data loss",
                "Cross-account key sharing abuse",
                "Hardcoded credentials in code"
            ],
            "mitre_techniques": ["T1552 - Unsecured Credentials", "T1555 - Credentials from Password Stores"],
            "controls": ["SC-12", "SC-28", "IA-5", "AC-6"],
            "mitigations": [
                "Enable automatic secret rotation",
                "Use key policies with least privilege",
                "Enable CloudTrail logging for KMS",
                "Implement key deletion protection",
                "Use separate keys per environment"
            ]
        },
        "Logging (CloudTrail/CloudWatch)": {
            "description": "Audit logging and monitoring infrastructure.",
            "key_resources": ["CloudTrail Trails", "CloudWatch Log Groups", "Config Rules", "EventBridge Rules"],
            "attack_vectors": [
                "CloudTrail log tampering or deletion",
                "Log injection attacks",
                "Disabling logging to hide activity",
                "Overwhelming logs with noise",
                "Evading detection through API throttling"
            ],
            "mitre_techniques": ["T1070 - Indicator Removal", "T1562 - Impair Defenses", "T1036 - Masquerading"],
            "controls": ["AU-2", "AU-6", "AU-9", "AU-12", "SI-4"],
            "mitigations": [
                "Enable CloudTrail log file validation",
                "Send logs to a separate security account",
                "Enable S3 Object Lock on log buckets",
                "Set up alerts for trail modifications",
                "Use CloudWatch Logs Insights for analysis"
            ]
        }
    }
    
    st.markdown("---")
    st.markdown("##### 📋 Asset Threat Details (Click to Expand)")
    
    for asset_name, details in asset_details.items():
        # Find risk score for this asset
        idx = asset_threat_data["Asset Category"].index(asset_name)
        risk_score = asset_threat_data["Risk Score"][idx]
        likelihood = asset_threat_data["Attack Likelihood"][idx]
        impact = asset_threat_data["Business Impact"][idx]
        
        # Color based on risk
        if risk_score >= 9.0:
            risk_emoji = "🔴"
        elif risk_score >= 8.0:
            risk_emoji = "🟠"
        else:
            risk_emoji = "🟡"
        
        with st.expander(f"{risk_emoji} **{asset_name}** — Risk Score: {risk_score} | Likelihood: {likelihood} | Impact: {impact}"):
            st.markdown(f"*{details['description']}*")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎯 Key Resources:**")
                for resource in details["key_resources"]:
                    st.markdown(f"- {resource}")
                
                st.markdown("**⚔️ MITRE ATT&CK Techniques:**")
                for technique in details["mitre_techniques"]:
                    st.markdown(f"- `{technique}`")
                
                st.markdown("**📋 NIST Controls:**")
                st.markdown(f"`{', '.join(details['controls'])}`")
            
            with col2:
                st.markdown("**🚨 Attack Vectors:**")
                for vector in details["attack_vectors"][:3]:
                    st.markdown(f"- {vector}")
                
                st.markdown("**🛡️ Recommended Mitigations:**")
                for mitigation in details["mitigations"][:3]:
                    st.markdown(f"- {mitigation}")


def _render_mitre_attack_coverage(assessment_data=None):
    """Render MITRE ATT&CK framework coverage analysis."""
    st.markdown("#### MITRE ATT&CK Framework Coverage")
    
    st.markdown("""
    <div style="background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <strong>🔍 ATT&CK Integration:</strong> Mapping NIST 800-53 controls to MITRE ATT&CK tactics 
        and techniques to identify defensive coverage gaps.
    </div>
    """, unsafe_allow_html=True)
    
    # MITRE ATT&CK Tactics with NIST mapping
    mitre_tactics = {
        "Reconnaissance": {"nist_controls": ["RA-5", "SI-4"], "coverage": 45, "techniques_covered": 3, "techniques_total": 10},
        "Resource Development": {"nist_controls": ["SA-3", "SA-4"], "coverage": 35, "techniques_covered": 2, "techniques_total": 7},
        "Initial Access": {"nist_controls": ["AC-2", "AC-3", "IA-2", "IA-5"], "coverage": 78, "techniques_covered": 7, "techniques_total": 9},
        "Execution": {"nist_controls": ["CM-7", "SI-3", "SI-4"], "coverage": 65, "techniques_covered": 8, "techniques_total": 12},
        "Persistence": {"nist_controls": ["AC-2", "CM-3", "CM-5"], "coverage": 72, "techniques_covered": 12, "techniques_total": 19},
        "Privilege Escalation": {"nist_controls": ["AC-6", "CM-5", "CM-7"], "coverage": 81, "techniques_covered": 10, "techniques_total": 13},
        "Defense Evasion": {"nist_controls": ["AU-2", "AU-6", "SI-4"], "coverage": 58, "techniques_covered": 15, "techniques_total": 42},
        "Credential Access": {"nist_controls": ["IA-2", "IA-5", "SC-28"], "coverage": 85, "techniques_covered": 12, "techniques_total": 15},
        "Discovery": {"nist_controls": ["AC-4", "AU-12", "SI-4"], "coverage": 52, "techniques_covered": 14, "techniques_total": 30},
        "Lateral Movement": {"nist_controls": ["AC-4", "SC-7", "SI-4"], "coverage": 68, "techniques_covered": 6, "techniques_total": 9},
        "Collection": {"nist_controls": ["AU-9", "SC-28", "MP-2"], "coverage": 61, "techniques_covered": 10, "techniques_total": 17},
        "Command and Control": {"nist_controls": ["SC-7", "SI-4", "AC-4"], "coverage": 74, "techniques_covered": 11, "techniques_total": 16},
        "Exfiltration": {"nist_controls": ["SC-7", "SC-8", "AU-6"], "coverage": 79, "techniques_covered": 7, "techniques_total": 9},
        "Impact": {"nist_controls": ["CP-9", "CP-10", "SI-17"], "coverage": 67, "techniques_covered": 9, "techniques_total": 13}
    }
    
    # Summary metrics
    total_techniques = sum(t["techniques_total"] for t in mitre_tactics.values())
    covered_techniques = sum(t["techniques_covered"] for t in mitre_tactics.values())
    avg_coverage = sum(t["coverage"] for t in mitre_tactics.values()) / len(mitre_tactics)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tactics Analyzed", len(mitre_tactics))
    with col2:
        st.metric("Techniques Covered", f"{covered_techniques}/{total_techniques}")
    with col3:
        st.metric("Average Coverage", f"{avg_coverage:.0f}%")
    
    st.markdown("---")
    
    # Tactic coverage details
    for tactic, data in mitre_tactics.items():
        coverage = data["coverage"]
        if coverage >= 75:
            emoji = "🟢"
        elif coverage >= 50:
            emoji = "🟡"
        else:
            emoji = "🔴"
        
        with st.expander(f"{emoji} **{tactic}** — {coverage}% coverage ({data['techniques_covered']}/{data['techniques_total']} techniques)"):
            st.markdown(f"**Mapped NIST Controls:** `{', '.join(data['nist_controls'])}`")
            st.progress(coverage / 100)
            
            if coverage < 60:
                st.warning(f"⚠️ Gap identified: {tactic} has weak control coverage. Consider enhancing detection and prevention capabilities.")


def _render_actuarial_risk_data(assessment_data=None):
    """Render actuarial risk data and probability analysis."""
    st.markdown("#### Actuarial Risk Intelligence")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                border: 1px solid #f59e0b; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <strong>📈 Data-Driven Risk Quantification:</strong> Using industry breach data, threat intelligence, 
        and actuarial models to quantify unknown risks and predict potential losses.
    </div>
    """, unsafe_allow_html=True)
    
    # Actuarial risk data (based on industry statistics)
    st.markdown("##### Annualized Loss Expectancy (ALE) by Threat Category")
    
    ale_data = {
        "Threat Category": [
            "Ransomware Attack",
            "Data Breach (PII)",
            "Cloud Misconfiguration",
            "Insider Threat",
            "DDoS Attack",
            "Supply Chain Compromise",
            "Credential Stuffing",
            "Zero-Day Exploit"
        ],
        "Annual Rate of Occurrence": [0.25, 0.15, 0.45, 0.10, 0.35, 0.08, 0.55, 0.05],
        "Single Loss Expectancy": ["$2.5M", "$4.2M", "$890K", "$1.8M", "$450K", "$3.1M", "$320K", "$5.5M"],
        "Annualized Loss Expectancy": ["$625K", "$630K", "$400K", "$180K", "$157K", "$248K", "$176K", "$275K"],
        "Control Effectiveness": ["72%", "65%", "58%", "45%", "82%", "38%", "78%", "25%"]
    }
    
    df = pd.DataFrame(ale_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Risk probability chart
    st.markdown("##### Probability vs Impact Matrix")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create probability-impact data for visualization
        prob_impact_data = pd.DataFrame({
            'Threat': ale_data["Threat Category"],
            'Probability': ale_data["Annual Rate of Occurrence"],
        })
        st.bar_chart(prob_impact_data.set_index('Threat'))
    
    with col2:
        st.markdown("""
        **Risk Tolerance Thresholds:**
        
        🔴 **Critical:** >$500K ALE  
        🟠 **High:** $250K-$500K ALE  
        🟡 **Medium:** $100K-$250K ALE  
        🟢 **Low:** <$100K ALE
        
        ---
        
        **Data Sources:**
        - Verizon DBIR 2025
        - IBM Cost of a Data Breach
        - CISA Threat Reports
        - Industry actuarial tables
        """)
    
    # Unknown to Known transformation
    st.markdown("---")
    st.markdown("##### 🔮 Transforming Unknowns to Known Risks")
    
    unknown_known_data = {
        "Unknown Risk Factor": [
            "Unpatched vulnerabilities in shadow IT",
            "Third-party vendor security posture",
            "Insider threat probability",
            "Zero-day exposure window",
            "Cloud permission sprawl impact"
        ],
        "Intelligence Source": [
            "CISA KEV + Asset Discovery",
            "SecurityScorecard + Questionnaires",
            "UEBA + HR Data Correlation",
            "Threat Intel Feeds + Patch Cadence",
            "IAM Analyzer + Permission Boundaries"
        ],
        "Confidence Level": ["High (85%)", "Medium (62%)", "Medium (58%)", "Low (35%)", "High (78%)"],
        "Estimated Annual Risk": ["$340K", "$520K", "$180K", "$890K", "$245K"]
    }
    
    df_unknown = pd.DataFrame(unknown_known_data)
    st.dataframe(df_unknown, use_container_width=True, hide_index=True)


def render_controls_selection():
    """Render controls selection - now uses sidebar."""
    # This function is kept for backward compatibility
    # but the sidebar handles control selection
    render_welcome_screen()


def render_security_hub_findings_only():
    """
    Render a dedicated view showing ONLY Security Hub findings.
    This is triggered when the user clicks the Security Hub link in the sidebar.
    """
    import boto3
    from botocore.exceptions import ClientError
    
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%); 
                border-radius: 10px; margin-bottom: 1.5rem;">
        <h1 style="color: white; margin: 0;">🔗 AWS Security Hub Findings</h1>
        <p style="color: #e0e7ff; margin: 0.5rem 0 0 0;">Real-time security findings from your AWS environment</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Assessment", use_container_width=False):
        st.session_state.show_security_hub_only = False
        st.rerun()
    
    st.markdown("---")
    
    # Check for AWS credentials
    import os
    if not os.environ.get('AWS_ACCESS_KEY_ID') or not os.environ.get('AWS_SECRET_ACCESS_KEY'):
        st.warning("⚠️ AWS credentials not configured. Please authenticate first on the NIST Assessment tab.")
        return
    
    try:
        with st.spinner("🔍 Fetching Security Hub findings..."):
            # Initialize Security Hub client
            region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
            securityhub = boto3.client('securityhub', region_name=region)
            
            # Check if Security Hub is enabled
            try:
                hub = securityhub.describe_hub()
                st.success(f"✅ Connected to Security Hub: {hub.get('HubArn', 'Unknown')}")
            except ClientError as e:
                st.error("❌ Security Hub is not enabled in this account/region.")
                st.info("💡 Enable Security Hub in the AWS Console to use this feature.")
                return
            
            # Get enabled standards
            try:
                standards = securityhub.get_enabled_standards()['StandardsSubscriptions']
                if standards:
                    std_names = [s.get('StandardsArn', '').split('/')[-1] for s in standards]
                    st.info(f"📋 Enabled Standards: {', '.join(std_names)}")
            except ClientError:
                pass
            
            # Fetch findings with filters
            filters = {
                'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}],
                'WorkflowStatus': [
                    {'Value': 'NEW', 'Comparison': 'EQUALS'},
                    {'Value': 'NOTIFIED', 'Comparison': 'EQUALS'},
                ],
            }
            
            all_findings = []
            paginator = securityhub.get_paginator('get_findings')
            
            for page in paginator.paginate(Filters=filters, MaxResults=100):
                all_findings.extend(page.get('Findings', []))
                if len(all_findings) >= 200:  # Limit to 200 findings
                    break
            
            if not all_findings:
                st.success("🎉 No active security findings! Your environment looks secure.")
                return
            
            # Summary metrics
            severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFORMATIONAL': 0}
            for finding in all_findings:
                sev = finding.get('Severity', {}).get('Label', 'INFORMATIONAL')
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            # Display metrics
            st.markdown("### 📊 Findings Summary")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("🔴 CRITICAL", severity_counts['CRITICAL'])
            with col2:
                st.metric("🟠 HIGH", severity_counts['HIGH'])
            with col3:
                st.metric("🟡 MEDIUM", severity_counts['MEDIUM'])
            with col4:
                st.metric("🟢 LOW", severity_counts['LOW'])
            with col5:
                st.metric("⚪ INFO", severity_counts['INFORMATIONAL'])
            
            st.markdown(f"**Total Active Findings: {len(all_findings)}**")
            st.markdown("---")
            
            # Filter options
            st.markdown("### 🔍 Filter Findings")
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                severity_filter = st.multiselect(
                    "Severity",
                    options=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFORMATIONAL'],
                    default=['CRITICAL', 'HIGH']
                )
            
            with filter_col2:
                # Get unique product names
                products = list(set([f.get('ProductName', 'Unknown') for f in all_findings]))
                product_filter = st.multiselect(
                    "Source Service",
                    options=products,
                    default=products[:5] if len(products) > 5 else products
                )
            
            # Filter findings
            filtered_findings = [
                f for f in all_findings
                if f.get('Severity', {}).get('Label', 'INFORMATIONAL') in severity_filter
                and f.get('ProductName', 'Unknown') in product_filter
            ]
            
            st.markdown(f"**Showing {len(filtered_findings)} of {len(all_findings)} findings**")
            st.markdown("---")
            
            # Display findings
            st.markdown("### 📋 Security Findings")
            
            for i, finding in enumerate(filtered_findings[:50]):  # Limit display to 50
                severity = finding.get('Severity', {}).get('Label', 'UNKNOWN')
                title = finding.get('Title', 'Unknown Finding')
                description = finding.get('Description', 'No description available')
                product = finding.get('ProductName', 'Unknown')
                created = finding.get('CreatedAt', 'Unknown')[:10] if finding.get('CreatedAt') else 'Unknown'
                
                # Get resources
                resources = finding.get('Resources', [])
                resource_ids = [r.get('Id', 'Unknown')[:50] for r in resources[:3]]
                
                # Get remediation
                remediation = finding.get('Remediation', {}).get('Recommendation', {})
                rec_text = remediation.get('Text', '')
                rec_url = remediation.get('Url', '')
                
                # Severity colors
                sev_colors = {
                    'CRITICAL': '#dc2626',
                    'HIGH': '#ea580c', 
                    'MEDIUM': '#ca8a04',
                    'LOW': '#16a34a',
                    'INFORMATIONAL': '#6b7280'
                }
                sev_color = sev_colors.get(severity, '#6b7280')
                
                with st.expander(f"**{severity}** | {title[:80]}{'...' if len(title) > 80 else ''}", expanded=(severity in ['CRITICAL', 'HIGH'] and i < 5)):
                    st.markdown(f"""
                    <div style="border-left: 4px solid {sev_color}; padding-left: 1rem;">
                        <p><strong>Severity:</strong> <span style="color: {sev_color}; font-weight: bold;">{severity}</span></p>
                        <p><strong>Source:</strong> {product}</p>
                        <p><strong>Created:</strong> {created}</p>
                        <p><strong>Description:</strong> {description[:500]}{'...' if len(description) > 500 else ''}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if resource_ids:
                        st.markdown(f"**Affected Resources:** {', '.join(resource_ids)}")
                    
                    if rec_text:
                        st.markdown(f"**Recommendation:** {rec_text[:300]}{'...' if len(rec_text) > 300 else ''}")
                    
                    if rec_url:
                        st.markdown(f"[📖 View Remediation Guide]({rec_url})")
            
            if len(filtered_findings) > 50:
                st.info(f"ℹ️ Showing first 50 of {len(filtered_findings)} findings. Apply filters to narrow results.")
                
    except Exception as e:
        st.error(f"❌ Error fetching Security Hub findings: {str(e)}")
        st.info("💡 Ensure your AWS credentials have permission to access Security Hub.")
