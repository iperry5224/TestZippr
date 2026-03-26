"""
SOPRA - SAE On-Premise Risk Assessment
A comprehensive security assessment tool for on-premise environments

Version: 2.0.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Import detailed control definitions
from sopra_controls import (
    ALL_CONTROLS, get_control_by_id, get_controls_by_category,
    get_remediation_script, ControlStatus, Severity, ControlFamily
)

# Page configuration
st.set_page_config(
    page_title="SOPRA - SAE On-Premise Risk Assessment",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for SOPRA branding - Industrial/Enterprise aesthetic
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Professional icon styling */
    .cat-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #00d9ff 0%, #0f3460 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .cat-icon-container {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
    }
    
    .cat-icon-box {
        width: 42px;
        height: 42px;
        border-radius: 10px;
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.2) 0%, rgba(15, 52, 96, 0.3) 100%);
        border: 1px solid rgba(0, 217, 255, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    
    .cat-icon-box i {
        font-size: 1.2rem;
        color: #00d9ff;
    }
    
    /* Metric card click overlay button - invisible but clickable */
    .metric-btn-wrapper {
        position: relative;
    }
    
    .metric-btn-wrapper button {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 10 !important;
    }
    
    .metric-card {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 217, 255, 0.4);
        border-color: #00d9ff;
    }
    
    :root {
        --sopra-primary: #1a1a2e;
        --sopra-secondary: #16213e;
        --sopra-accent: #e94560;
        --sopra-highlight: #0f3460;
        --sopra-success: #00d9ff;
        --sopra-warning: #ffc107;
        --sopra-danger: #e94560;
        --sopra-text: #f5f5f5;
    }
    
    /* Global text brightness for maximum readability */
    .main p, .main li, .main span, .main td, .main th, .main div {
        color: #f0f0f0 !important;
    }
    
    .main strong, .main b {
        color: #ffffff !important;
    }
    
    .stMarkdown p {
        color: #f0f0f0 !important;
    }
    
    .stMarkdown li {
        color: #f0f0f0 !important;
    }
    
    .stMarkdown code {
        color: #00d9ff !important;
        background: rgba(0, 217, 255, 0.1) !important;
    }
    
    /* Table styling for bright text */
    .stDataFrame, .stTable {
        color: #f0f0f0 !important;
    }
    
    /* Selectbox and multiselect text */
    .stSelectbox label, .stMultiSelect label, .stTextInput label, .stTextArea label {
        color: #f0f0f0 !important;
    }
    
    /* Caption and helper text */
    .stCaption, small, .caption {
        color: #c0c0c0 !important;
    }
    
    /* Expander headers */
    .streamlit-expanderHeader {
        color: #f0f0f0 !important;
    }
    
    /* Tab labels */
    .stTabs [data-baseweb="tab"] {
        color: #f0f0f0 !important;
    }
    
    /* Keep header colors cyan */
    .main h1, .main h2, .main h3, .main h4 {
        color: #00d9ff !important;
    }
    
    .main {
        background: linear-gradient(180deg, #000000 0%, #050510 20%, #0a0a1a 40%, #0d1525 60%, #0a1220 80%, #050a12 100%);
    }
    
    .stApp {
        background: linear-gradient(180deg, #000000 0%, #050510 20%, #0a0a1a 40%, #0d1525 60%, #0a1220 80%, #050a12 100%);
    }
    
    /* Animated grid background effect */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            linear-gradient(rgba(0, 217, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 217, 255, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
    }
    
    h1, h2, h3 {
        font-family: 'IBM Plex Sans', sans-serif !important;
        color: #00d9ff !important;
    }
    
    .opra-header {
        background: linear-gradient(180deg, #000000 0%, #0a0a14 30%, #0f1a2e 70%, #0a1628 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        border: 1px solid rgba(0, 217, 255, 0.3);
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 0 60px rgba(0, 0, 0, 0.8), inset 0 0 100px rgba(0, 217, 255, 0.05);
        position: relative;
        overflow: hidden;
    }
    
    .opra-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(ellipse at center, rgba(0, 217, 255, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    
    .opra-header h1 {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 3rem !important;
        color: #00d9ff !important;
        margin: 0;
        text-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
    }
    
    .opra-header p {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #f5f5f5;
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }
    
    .opra-card {
        background: linear-gradient(145deg, #16213e, #1a1a2e);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .opra-card:hover {
        border-color: #e94560;
        box-shadow: 0 0 20px rgba(233, 69, 96, 0.2);
        transform: translateY(-2px);
    }
    
    .metric-card {
        background: linear-gradient(145deg, #0f3460, #16213e);
        border: 1px solid #00d9ff;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
    }
    
    /* Make ALL buttons look like styled dark tiles */
    .stButton button,
    .stButton > button,
    div[data-testid="stButton"] > button,
    button[kind="secondary"],
    .stButton button[kind="secondary"] {
        background: linear-gradient(145deg, #0f3460, #16213e) !important;
        border: 1px solid rgba(0, 217, 255, 0.5) !important;
        border-radius: 12px !important;
        color: #00d9ff !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        min-height: 100px !important;
        white-space: pre-wrap !important;
        line-height: 1.4 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover,
    .stButton > button:hover,
    div[data-testid="stButton"] > button:hover {
        border-color: #00d9ff !important;
        box-shadow: 0 0 25px rgba(0, 217, 255, 0.4) !important;
        transform: translateY(-3px) !important;
        background: linear-gradient(145deg, #16213e, #1a1a2e) !important;
    }
    
    .stButton button:active,
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    .stButton button:focus,
    .stButton > button:focus {
        box-shadow: 0 0 25px rgba(0, 217, 255, 0.4) !important;
        outline: none !important;
    }
    
    /* Primary buttons keep their distinctive red style */
    .stButton button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #e94560, #c73e54) !important;
        border: none !important;
        color: white !important;
        min-height: auto !important;
    }
    
    .stButton button[kind="primary"]:hover,
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #ff5a75, #e94560) !important;
        box-shadow: 0 0 20px rgba(233, 69, 96, 0.4) !important;
    }
    
    /* Extra specificity for Streamlit button overrides */
    .element-container .stButton button,
    section[data-testid="stSidebar"] .stButton button,
    .main .stButton button {
        background: linear-gradient(145deg, #0f3460, #16213e) !important;
        border: 1px solid rgba(0, 217, 255, 0.5) !important;
        color: #00d9ff !important;
    }
    
    /* Ensure button text is visible */
    .stButton button p,
    .stButton button span,
    .stButton button div {
        color: #00d9ff !important;
    }
    
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        color: #00d9ff;
    }
    
    .metric-label {
        font-family: 'IBM Plex Sans', sans-serif;
        color: #f5f5f5;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .risk-critical { color: #e94560 !important; }
    .risk-high { color: #ff6b6b !important; }
    .risk-medium { color: #ffc107 !important; }
    .risk-low { color: #00d9ff !important; }
    
    .stButton > button {
        background: linear-gradient(90deg, #e94560, #0f3460) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #0f3460, #e94560) !important;
        box-shadow: 0 0 20px rgba(233, 69, 96, 0.4) !important;
        transform: scale(1.02) !important;
    }
    
    .assessment-category {
        background: #16213e;
        border-left: 4px solid #e94560;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .sidebar .stSelectbox, .sidebar .stMultiSelect {
        background: #1a1a2e;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #e94560;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00d9ff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'opra_assessment_results' not in st.session_state:
    st.session_state.opra_assessment_results = None
if 'opra_active_tab' not in st.session_state:
    st.session_state.opra_active_tab = "Dashboard"
if 'opra_chat_history' not in st.session_state:
    st.session_state.opra_chat_history = []
if 'opra_selected_category' not in st.session_state:
    st.session_state.opra_selected_category = None
if 'opra_selected_control' not in st.session_state:
    st.session_state.opra_selected_control = None
if 'opra_selected_metric' not in st.session_state:
    st.session_state.opra_selected_metric = None

# =============================================================================
# AWS BEDROCK INTEGRATION (Data stays within AWS)
# =============================================================================

# List of Bedrock models to try in order of preference
BEDROCK_MODELS = [
    "nvidia.nemotron-nano-12b-v2",                # NVIDIA Nemotron Nano 12B
    # Claude removed per policy
    "amazon.titan-text-express-v1",               # Titan Express
    "amazon.titan-text-lite-v1",                  # Titan Lite
    "meta.llama3-8b-instruct-v1:0",               # Llama 3
    "mistral.mistral-7b-instruct-v0:2",           # Mistral
]

def call_bedrock_ai(messages: list, system_prompt: str, max_tokens: int = 4096, region: str = "us-east-1") -> str:
    """
    Call AI via Amazon Bedrock (data stays within AWS).
    Tries multiple models until one works.
    """
    try:
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=region
        )
        
        # Format messages for Bedrock Converse API
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": [{"text": msg["content"]}]
            })
        
        # Try each model until one works
        last_error = None
        for model_id in BEDROCK_MODELS:
            try:
                response = bedrock.converse(
                    modelId=model_id,
                    messages=formatted_messages,
                    system=[{"text": system_prompt}],
                    inferenceConfig={
                        "maxTokens": min(max_tokens, 4096),
                        "temperature": 0.7,
                    }
                )
                return response['output']['message']['content'][0]['text']
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code in ['AccessDeniedException', 'ValidationException', 'ResourceNotFoundException']:
                    last_error = f"{model_id}: {error_code}"
                    continue
                else:
                    raise
        
        raise Exception(f"No Bedrock models available. Last error: {last_error}")
        
    except NoCredentialsError:
        raise Exception("AWS credentials not configured. Please configure AWS credentials first.")
    except Exception as e:
        error_msg = str(e)
        if "No Bedrock models available" in error_msg:
            raise Exception("""
⚠️ **Bedrock Not Configured**

    To use SOPRA AI, you need to enable a model in Amazon Bedrock:

1. Go to **AWS Console** → **Amazon Bedrock**
2. Look for **Model catalog** or **Foundation models**
3. Select a model (Titan, Llama, or Mistral)
4. Click **Request access** or **Enable**

Run this to check available models:
```
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[*].modelId'
```
""")
        raise Exception(f"Bedrock error: {error_msg}")

# ============================================================================
# ON-PREMISE ASSESSMENT CATEGORIES
# ============================================================================

OPRA_CATEGORIES = {
    "active_directory": {
        "name": "Active Directory Security",
        "icon": "fa-solid fa-sitemap",
        "icon_emoji": "🔐",  # Fallback
        "description": "Domain controllers, GPOs, privileged accounts, authentication",
        "controls": [
            {"id": "AD-001", "name": "Domain Admin Account Security", "family": "Access Control"},
            {"id": "AD-002", "name": "Service Account Management", "family": "Access Control"},
            {"id": "AD-003", "name": "Group Policy Security", "family": "Configuration Management"},
            {"id": "AD-004", "name": "Password Policy Enforcement", "family": "Identification & Auth"},
            {"id": "AD-005", "name": "Kerberos Configuration", "family": "Identification & Auth"},
            {"id": "AD-006", "name": "LDAP Signing & Binding", "family": "System & Comm Protection"},
            {"id": "AD-007", "name": "AdminSDHolder Protection", "family": "Access Control"},
            {"id": "AD-008", "name": "Trust Relationship Security", "family": "Access Control"},
            {"id": "AD-009", "name": "Replication Security", "family": "System & Comm Protection"},
            {"id": "AD-010", "name": "Audit Policy Configuration", "family": "Audit & Accountability"},
        ]
    },
    "network_infrastructure": {
        "name": "Network Infrastructure",
        "icon": "fa-solid fa-network-wired",
        "icon_emoji": "🌐",
        "description": "Firewalls, switches, routers, segmentation, IDS/IPS",
        "controls": [
            {"id": "NET-001", "name": "Network Segmentation", "family": "System & Comm Protection"},
            {"id": "NET-002", "name": "Firewall Rule Review", "family": "System & Comm Protection"},
            {"id": "NET-003", "name": "IDS/IPS Configuration", "family": "System & Info Integrity"},
            {"id": "NET-004", "name": "VPN Security", "family": "System & Comm Protection"},
            {"id": "NET-005", "name": "Switch Port Security", "family": "System & Comm Protection"},
            {"id": "NET-006", "name": "Router ACL Review", "family": "Access Control"},
            {"id": "NET-007", "name": "Network Device Hardening", "family": "Configuration Management"},
            {"id": "NET-008", "name": "Wireless Security", "family": "System & Comm Protection"},
            {"id": "NET-009", "name": "DNS Security", "family": "System & Comm Protection"},
            {"id": "NET-010", "name": "Network Monitoring", "family": "System & Info Integrity"},
        ]
    },
    "endpoint_security": {
        "name": "Endpoint Security",
        "icon": "fa-solid fa-laptop-code",
        "icon_emoji": "💻",
        "description": "Workstations, laptops, servers, EDR, patching",
        "controls": [
            {"id": "END-001", "name": "Endpoint Protection Platform", "family": "System & Info Integrity"},
            {"id": "END-002", "name": "Patch Management", "family": "System & Info Integrity"},
            {"id": "END-003", "name": "Host-based Firewall", "family": "System & Comm Protection"},
            {"id": "END-004", "name": "Application Whitelisting", "family": "Configuration Management"},
            {"id": "END-005", "name": "Local Admin Rights", "family": "Access Control"},
            {"id": "END-006", "name": "USB/Removable Media Control", "family": "Media Protection"},
            {"id": "END-007", "name": "Full Disk Encryption", "family": "System & Comm Protection"},
            {"id": "END-008", "name": "EDR/XDR Deployment", "family": "System & Info Integrity"},
            {"id": "END-009", "name": "Secure Boot Configuration", "family": "System & Info Integrity"},
            {"id": "END-010", "name": "Endpoint Logging", "family": "Audit & Accountability"},
        ]
    },
    "server_security": {
        "name": "Server Security",
        "icon": "fa-solid fa-server",
        "icon_emoji": "🖥️",
        "description": "Windows/Linux servers, hardening, services, databases",
        "controls": [
            {"id": "SRV-001", "name": "Server Hardening Baseline", "family": "Configuration Management"},
            {"id": "SRV-002", "name": "Unnecessary Services Disabled", "family": "Configuration Management"},
            {"id": "SRV-003", "name": "Database Security", "family": "System & Comm Protection"},
            {"id": "SRV-004", "name": "File Server Permissions", "family": "Access Control"},
            {"id": "SRV-005", "name": "Web Server Security", "family": "System & Comm Protection"},
            {"id": "SRV-006", "name": "Email Server Security", "family": "System & Comm Protection"},
            {"id": "SRV-007", "name": "Backup Server Protection", "family": "Contingency Planning"},
            {"id": "SRV-008", "name": "Virtualization Security", "family": "System & Comm Protection"},
            {"id": "SRV-009", "name": "Server Certificate Management", "family": "System & Comm Protection"},
            {"id": "SRV-010", "name": "Server Access Logging", "family": "Audit & Accountability"},
        ]
    },
    "physical_security": {
        "name": "Physical Security",
        "icon": "fa-solid fa-building-shield",
        "icon_emoji": "🏢",
        "description": "Data centers, server rooms, access controls, surveillance",
        "controls": [
            {"id": "PHY-001", "name": "Physical Access Control", "family": "Physical & Environmental"},
            {"id": "PHY-002", "name": "Visitor Management", "family": "Physical & Environmental"},
            {"id": "PHY-003", "name": "Surveillance Systems", "family": "Physical & Environmental"},
            {"id": "PHY-004", "name": "Server Room Access", "family": "Physical & Environmental"},
            {"id": "PHY-005", "name": "Environmental Controls", "family": "Physical & Environmental"},
            {"id": "PHY-006", "name": "Cable Management", "family": "Physical & Environmental"},
            {"id": "PHY-007", "name": "Equipment Disposal", "family": "Media Protection"},
            {"id": "PHY-008", "name": "Emergency Power", "family": "Physical & Environmental"},
            {"id": "PHY-009", "name": "Fire Suppression", "family": "Physical & Environmental"},
            {"id": "PHY-010", "name": "Physical Security Logging", "family": "Audit & Accountability"},
        ]
    },
    "data_protection": {
        "name": "Data Protection",
        "icon": "fa-solid fa-shield-halved",
        "icon_emoji": "🛡️",
        "description": "Encryption, DLP, backup, classification, retention",
        "controls": [
            {"id": "DAT-001", "name": "Data Classification", "family": "Risk Assessment"},
            {"id": "DAT-002", "name": "Data Loss Prevention", "family": "System & Info Integrity"},
            {"id": "DAT-003", "name": "Encryption at Rest", "family": "System & Comm Protection"},
            {"id": "DAT-004", "name": "Encryption in Transit", "family": "System & Comm Protection"},
            {"id": "DAT-005", "name": "Backup & Recovery", "family": "Contingency Planning"},
            {"id": "DAT-006", "name": "Data Retention Policy", "family": "System & Info Integrity"},
            {"id": "DAT-007", "name": "Sensitive Data Handling", "family": "Media Protection"},
            {"id": "DAT-008", "name": "Database Encryption", "family": "System & Comm Protection"},
            {"id": "DAT-009", "name": "Key Management", "family": "System & Comm Protection"},
            {"id": "DAT-010", "name": "Data Access Auditing", "family": "Audit & Accountability"},
        ]
    },
    "identity_access": {
        "name": "Identity & Access Management",
        "icon": "fa-solid fa-user-shield",
        "icon_emoji": "👤",
        "description": "Authentication, authorization, privileged access, MFA",
        "controls": [
            {"id": "IAM-001", "name": "Multi-Factor Authentication", "family": "Identification & Auth"},
            {"id": "IAM-002", "name": "Privileged Access Management", "family": "Access Control"},
            {"id": "IAM-003", "name": "Role-Based Access Control", "family": "Access Control"},
            {"id": "IAM-004", "name": "Account Lifecycle Management", "family": "Access Control"},
            {"id": "IAM-005", "name": "Password Vault/Management", "family": "Identification & Auth"},
            {"id": "IAM-006", "name": "Session Management", "family": "Access Control"},
            {"id": "IAM-007", "name": "Access Review Process", "family": "Access Control"},
            {"id": "IAM-008", "name": "Separation of Duties", "family": "Access Control"},
            {"id": "IAM-009", "name": "Remote Access Security", "family": "Access Control"},
            {"id": "IAM-010", "name": "Identity Federation", "family": "Identification & Auth"},
        ]
    },
    "monitoring_logging": {
        "name": "Monitoring & Logging",
        "icon": "fa-solid fa-chart-line",
        "icon_emoji": "📊",
        "description": "SIEM, log management, alerting, incident detection",
        "controls": [
            {"id": "MON-001", "name": "SIEM Implementation", "family": "Audit & Accountability"},
            {"id": "MON-002", "name": "Log Collection & Aggregation", "family": "Audit & Accountability"},
            {"id": "MON-003", "name": "Log Retention & Protection", "family": "Audit & Accountability"},
            {"id": "MON-004", "name": "Real-time Alerting", "family": "System & Info Integrity"},
            {"id": "MON-005", "name": "Security Event Correlation", "family": "System & Info Integrity"},
            {"id": "MON-006", "name": "Threat Detection Rules", "family": "System & Info Integrity"},
            {"id": "MON-007", "name": "Network Traffic Analysis", "family": "System & Info Integrity"},
            {"id": "MON-008", "name": "User Behavior Analytics", "family": "System & Info Integrity"},
            {"id": "MON-009", "name": "Incident Response Integration", "family": "Incident Response"},
            {"id": "MON-010", "name": "Compliance Reporting", "family": "Audit & Accountability"},
        ]
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def render_header():
    """Render the SOPRA header with logo"""
    import base64
    import os
    
    # Try to load the SOPRA logo (check both names)
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "SOPRA_logo_dark.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "OPRA_logo_dark.png")
    logo_html = ""
    
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        logo_html = f'<div style="display: block; margin: 0 auto; width: fit-content; padding: 2rem 3rem; background: radial-gradient(ellipse at center, rgba(10, 22, 40, 0.95) 0%, rgba(15, 26, 46, 0.8) 40%, rgba(10, 10, 20, 0.6) 70%, transparent 100%); border-radius: 30px; position: relative;"><img src="data:image/png;base64,{logo_data}" style="display: block; max-width: 455px; margin: 0 auto; position: relative; z-index: 1; filter: drop-shadow(0 0 40px rgba(0, 217, 255, 0.5));"></div>'
    else:
        logo_html = '<h1 style="font-family: JetBrains Mono, monospace; font-size: 4rem; color: #00d9ff; margin: 0; text-shadow: 0 0 30px rgba(0, 217, 255, 0.6);">🛡️ SOPRA</h1><p style="font-size: 1rem; color: #f0f0f0; letter-spacing: 4px; margin-top: 0.25rem;">SAE ON-PREMISE RISK ASSESSMENT</p>'
    
    st.markdown(f"""
    <div class="opra-header">
        {logo_html}
        <p style="font-size: 0.9rem; color: #00d9ff; letter-spacing: 2px; text-transform: uppercase;">SAE On-Premise Risk Assessment | Enterprise Infrastructure Security</p>
    </div>
    """, unsafe_allow_html=True)

def calculate_risk_score(findings):
    """Calculate overall risk score from findings"""
    if not findings:
        return 0
    
    total_weight = 0
    weighted_score = 0
    
    severity_weights = {
        "Critical": 10,
        "High": 7,
        "Medium": 4,
        "Low": 1
    }
    
    for finding in findings:
        weight = severity_weights.get(finding.get("severity", "Low"), 1)
        if finding.get("status") == "Failed":
            weighted_score += weight
        total_weight += weight
    
    if total_weight == 0:
        return 100
    
    # Return score out of 100 (higher is better)
    return max(0, 100 - int((weighted_score / total_weight) * 100))

def get_risk_color(score):
    """Get color based on risk score"""
    if score >= 80:
        return "#00d9ff"  # Good - cyan
    elif score >= 60:
        return "#ffc107"  # Medium - yellow
    elif score >= 40:
        return "#ff6b6b"  # High - orange-red
    else:
        return "#e94560"  # Critical - red

def render_metric_card(label, value, color=None):
    """Render a styled metric card"""
    color = color or "#00d9ff"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {color};">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# PAGE RENDERERS
# ============================================================================

def render_dashboard():
    """Render the main SOPRA dashboard with charts and visualizations"""
    render_header()
    
    # ── Quick stats row - CLICKABLE metric tiles ──
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("20\n\nASSESSMENT CATEGORIES", key="metric_categories", use_container_width=True, help="Click to view all 20 assessment categories"):
            st.session_state.opra_selected_metric = "categories"
            st.session_state.opra_active_tab = "Metric Details"
            st.rerun()
    
    with col2:
        if st.button("200\n\nTOTAL CONTROLS", key="metric_controls", use_container_width=True, help="Click to explore 200 security controls"):
            st.session_state.opra_selected_metric = "controls"
            st.session_state.opra_active_tab = "Metric Details"
            st.rerun()
    
    with col3:
        if st.session_state.opra_assessment_results:
            score = calculate_risk_score(st.session_state.opra_assessment_results.get("findings", []))
            score_display = f"{score}%"
        else:
            score_display = "N/A"
        
        if st.button(f"{score_display}\n\nRISK SCORE", key="metric_risk", use_container_width=True, help="Click to learn how Risk Score is calculated"):
            st.session_state.opra_selected_metric = "risk_score"
            st.session_state.opra_active_tab = "Metric Details"
            st.rerun()
    
    with col4:
        status = "Complete" if st.session_state.opra_assessment_results else "Pending"
        
        if st.button(f"{status}\n\nSTATUS", key="metric_status", use_container_width=True, help="Click to view assessment status"):
            st.session_state.opra_selected_metric = "status"
            st.session_state.opra_active_tab = "Metric Details"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── VISUAL ANALYTICS SECTION ──
    if st.session_state.opra_assessment_results:
        findings = st.session_state.opra_assessment_results.get("findings", [])
        passed = len([f for f in findings if f["status"] == "Passed"])
        failed = len([f for f in findings if f["status"] == "Failed"])
        not_assessed = len([f for f in findings if f["status"] == "Not Assessed"])
        total = len(findings)
        
        st.markdown("### 📈 Security Posture Overview")
        
        chart_col1, chart_col2, chart_col3 = st.columns(3)
        
        # ── Donut Chart: Overall Compliance ──
        with chart_col1:
            fig_donut = go.Figure(data=[go.Pie(
                labels=["Passed", "Failed", "Not Assessed"],
                values=[passed, failed, not_assessed],
                hole=0.55,
                marker_colors=["#00d9ff", "#e94560", "#3a3a5c"],
                textinfo="label+percent",
                textfont=dict(size=13, color="#f5f5f5"),
                hoverinfo="label+value+percent",
                pull=[0.02, 0.06, 0.02]
            )])
            fig_donut.update_layout(
                title=dict(text="Control Status", font=dict(color="#00d9ff", size=16)),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#f5f5f5',
                legend=dict(font=dict(color="#f5f5f5", size=12)),
                height=320,
                margin=dict(t=40, b=20, l=20, r=20),
                annotations=[dict(
                    text=f"<b>{int(passed/(total or 1)*100)}%</b><br>Compliant",
                    x=0.5, y=0.5, font_size=16, font_color="#00d9ff",
                    showarrow=False
                )]
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        
        # ── Bar Chart: Findings by Category ──
        with chart_col2:
            cat_passed = {}
            cat_failed = {}
            for f in findings:
                cat = f.get("category", "Unknown")
                if f["status"] == "Passed":
                    cat_passed[cat] = cat_passed.get(cat, 0) + 1
                elif f["status"] == "Failed":
                    cat_failed[cat] = cat_failed.get(cat, 0) + 1
            
            all_cats = sorted(set(list(cat_passed.keys()) + list(cat_failed.keys())))
            if all_cats:
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    name="Passed",
                    x=all_cats,
                    y=[cat_passed.get(c, 0) for c in all_cats],
                    marker_color="#00d9ff",
                    marker_line=dict(width=0),
                    opacity=0.9
                ))
                fig_bar.add_trace(go.Bar(
                    name="Failed",
                    x=all_cats,
                    y=[cat_failed.get(c, 0) for c in all_cats],
                    marker_color="#e94560",
                    marker_line=dict(width=0),
                    opacity=0.9
                ))
                fig_bar.update_layout(
                    title=dict(text="Findings by Category", font=dict(color="#00d9ff", size=16)),
                    barmode='stack',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#f5f5f5',
                    legend=dict(font=dict(color="#f5f5f5", size=12)),
                    xaxis=dict(tickangle=-30, tickfont=dict(size=10, color="#f5f5f5"), gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(tickfont=dict(color="#f5f5f5"), gridcolor='rgba(255,255,255,0.08)', title="Controls"),
                    height=320,
                    margin=dict(t=40, b=60, l=40, r=20)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No category data to display")
        
        # ── Severity Distribution Gauge / Polar Chart ──
        with chart_col3:
            sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
            for f in findings:
                if f["status"] == "Failed" and f.get("severity"):
                    sev = f["severity"]
                    if sev in sev_counts:
                        sev_counts[sev] += 1
            
            if sum(sev_counts.values()) > 0:
                fig_polar = go.Figure(data=go.Barpolar(
                    r=[sev_counts["Critical"], sev_counts["High"], sev_counts["Medium"], sev_counts["Low"]],
                    theta=["Critical", "High", "Medium", "Low"],
                    marker_color=["#e94560", "#ff6b6b", "#ffc107", "#00d9ff"],
                    marker_line=dict(color="#000", width=1),
                    opacity=0.85
                ))
                fig_polar.update_layout(
                    title=dict(text="Severity Radar", font=dict(color="#00d9ff", size=16)),
                    paper_bgcolor='rgba(0,0,0,0)',
                    polar=dict(
                        bgcolor='rgba(0,0,0,0)',
                        radialaxis=dict(visible=True, color="#666", gridcolor='rgba(255,255,255,0.1)'),
                        angularaxis=dict(color="#f5f5f5", gridcolor='rgba(255,255,255,0.1)')
                    ),
                    font_color='#f5f5f5',
                    height=320,
                    margin=dict(t=40, b=20, l=40, r=40)
                )
                st.plotly_chart(fig_polar, use_container_width=True)
            else:
                # Show a gauge-style risk score
                score = calculate_risk_score(findings)
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=score,
                    domain=dict(x=[0, 1], y=[0, 1]),
                    title=dict(text="Risk Score", font=dict(color="#00d9ff", size=16)),
                    number=dict(suffix="%", font=dict(color="#00d9ff", size=32)),
                    gauge=dict(
                        axis=dict(range=[0, 100], tickcolor="#f5f5f5", tickfont=dict(color="#f5f5f5")),
                        bar=dict(color="#00d9ff"),
                        bgcolor="rgba(0,0,0,0)",
                        steps=[
                            dict(range=[0, 40], color="rgba(233, 69, 96, 0.3)"),
                            dict(range=[40, 60], color="rgba(255, 107, 107, 0.3)"),
                            dict(range=[60, 80], color="rgba(255, 193, 7, 0.3)"),
                            dict(range=[80, 100], color="rgba(0, 217, 255, 0.3)")
                        ],
                        threshold=dict(line=dict(color="#ffffff", width=3), thickness=0.8, value=score)
                    )
                ))
                fig_gauge.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#f5f5f5',
                    height=320,
                    margin=dict(t=40, b=20, l=40, r=40)
                )
                st.plotly_chart(fig_gauge, use_container_width=True)
        
        # ── Second row of charts ──
        st.markdown("---")
        
        chart2_col1, chart2_col2 = st.columns(2)
        
        # ── Heatmap: Category vs Severity ──
        with chart2_col1:
            st.markdown("#### 🔥 Risk Heatmap")
            heatmap_data = {}
            for f in findings:
                if f["status"] == "Failed" and f.get("severity") and f.get("category"):
                    cat = f["category"]
                    sev = f["severity"]
                    if cat not in heatmap_data:
                        heatmap_data[cat] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
                    if sev in heatmap_data[cat]:
                        heatmap_data[cat][sev] += 1
            
            if heatmap_data:
                cats = list(heatmap_data.keys())
                sevs = ["Critical", "High", "Medium", "Low"]
                z_data = [[heatmap_data[c].get(s, 0) for s in sevs] for c in cats]
                
                fig_heat = go.Figure(data=go.Heatmap(
                    z=z_data,
                    x=sevs,
                    y=cats,
                    colorscale=[
                        [0, 'rgba(0, 217, 255, 0.1)'],
                        [0.25, 'rgba(255, 193, 7, 0.4)'],
                        [0.5, 'rgba(255, 107, 107, 0.6)'],
                        [0.75, 'rgba(233, 69, 96, 0.8)'],
                        [1.0, 'rgba(233, 69, 96, 1.0)']
                    ],
                    text=z_data,
                    texttemplate="%{text}",
                    textfont=dict(size=14, color="#ffffff"),
                    hoverinfo="x+y+z"
                ))
                fig_heat.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#f5f5f5',
                    xaxis=dict(tickfont=dict(color="#f5f5f5")),
                    yaxis=dict(tickfont=dict(color="#f5f5f5", size=10)),
                    height=300,
                    margin=dict(t=20, b=40, l=150, r=20)
                )
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.info("Complete an assessment to view the risk heatmap")
        
        # ── Timeline / Trend placeholder ──
        with chart2_col2:
            st.markdown("#### 📊 Control Family Breakdown")
            family_counts = {}
            for f in findings:
                fam = f.get("family", "Unknown")
                if fam not in family_counts:
                    family_counts[fam] = {"Passed": 0, "Failed": 0}
                if f["status"] == "Passed":
                    family_counts[fam]["Passed"] += 1
                elif f["status"] == "Failed":
                    family_counts[fam]["Failed"] += 1
            
            if family_counts:
                fam_names = list(family_counts.keys())
                fam_passed = [family_counts[f]["Passed"] for f in fam_names]
                fam_failed = [family_counts[f]["Failed"] for f in fam_names]
                
                fig_horiz = go.Figure()
                fig_horiz.add_trace(go.Bar(
                    y=fam_names, x=fam_passed, name="Passed",
                    orientation='h', marker_color="#00d9ff", opacity=0.85
                ))
                fig_horiz.add_trace(go.Bar(
                    y=fam_names, x=fam_failed, name="Failed",
                    orientation='h', marker_color="#e94560", opacity=0.85
                ))
                fig_horiz.update_layout(
                    barmode='stack',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#f5f5f5',
                    legend=dict(font=dict(color="#f5f5f5")),
                    xaxis=dict(title="Controls", tickfont=dict(color="#f5f5f5"), gridcolor='rgba(255,255,255,0.08)'),
                    yaxis=dict(tickfont=dict(color="#f5f5f5", size=10)),
                    height=300,
                    margin=dict(t=20, b=40, l=150, r=20)
                )
                st.plotly_chart(fig_horiz, use_container_width=True)
            else:
                st.info("Complete an assessment to view control family breakdown")
    
    else:
        # ── No assessment data yet - show preview gauges ──
        st.markdown("### 📈 Security Posture Overview")
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(145deg, rgba(15, 52, 96, 0.3), rgba(26, 26, 46, 0.5)); border: 1px solid rgba(0, 217, 255, 0.2); border-radius: 12px; margin-bottom: 1rem;">
            <p style="font-size: 1.3rem; color: #f5f5f5; margin-bottom: 0.5rem;">📊 Complete an assessment to unlock interactive visualizations</p>
            <p style="color: #c0c0c0; font-size: 0.95rem;">Upload CSV data or run a manual assessment to see pie charts, heatmaps, severity radars, and category breakdowns</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show placeholder gauge
        preview_col1, preview_col2, preview_col3 = st.columns(3)
        with preview_col1:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=0,
                domain=dict(x=[0, 1], y=[0, 1]),
                title=dict(text="Risk Score", font=dict(color="#00d9ff", size=14)),
                number=dict(suffix="%", font=dict(color="#3a3a5c", size=28)),
                gauge=dict(
                    axis=dict(range=[0, 100], tickcolor="#333", tickfont=dict(color="#666")),
                    bar=dict(color="#3a3a5c"),
                    bgcolor="rgba(0,0,0,0)",
                    steps=[
                        dict(range=[0, 40], color="rgba(233, 69, 96, 0.15)"),
                        dict(range=[40, 60], color="rgba(255, 107, 107, 0.15)"),
                        dict(range=[60, 80], color="rgba(255, 193, 7, 0.15)"),
                        dict(range=[80, 100], color="rgba(0, 217, 255, 0.15)")
                    ]
                )
            ))
            fig_gauge.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', font_color='#666',
                height=220, margin=dict(t=40, b=10, l=20, r=20)
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with preview_col2:
            fig_preview = go.Figure(data=[go.Pie(
                labels=["Awaiting", "Data"],
                values=[1, 0],
                hole=0.6,
                marker_colors=["#1a2a4a", "#0a0a1a"],
                textinfo="none",
                hoverinfo="none"
            )])
            fig_preview.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color='#666', showlegend=False,
                height=220, margin=dict(t=30, b=10, l=20, r=20),
                annotations=[dict(text="No Data", x=0.5, y=0.5, font_size=14, font_color="#666", showarrow=False)]
            )
            st.plotly_chart(fig_preview, use_container_width=True)
        
        with preview_col3:
            fig_bar_preview = go.Figure(data=[go.Bar(
                x=["AD", "NET", "END", "SRV", "PHY", "DAT", "IAM", "MON"],
                y=[0, 0, 0, 0, 0, 0, 0, 0],
                marker_color="rgba(0, 217, 255, 0.15)",
                marker_line=dict(color="rgba(0, 217, 255, 0.3)", width=1)
            )])
            fig_bar_preview.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color='#666',
                xaxis=dict(tickfont=dict(color="#666"), gridcolor='rgba(255,255,255,0.03)'),
                yaxis=dict(tickfont=dict(color="#666"), gridcolor='rgba(255,255,255,0.03)', range=[0, 10]),
                height=220, margin=dict(t=30, b=30, l=20, r=20)
            )
            st.plotly_chart(fig_bar_preview, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Assessment categories overview - CLICKABLE tiles ──
    st.markdown("### 📋 Assessment Categories")
    st.caption("Click any category tile to explore controls in detail")
    
    # First row of 4
    cols = st.columns(4)
    cat_keys = list(OPRA_CATEGORIES.keys())
    
    for idx in range(4):
        key = cat_keys[idx]
        category = OPRA_CATEGORIES[key]
        with cols[idx]:
            btn_label = f"🔹 {category['name']}\n\n{category['description']}\n\n🔴 {len(category['controls'])} Controls"
            if st.button(btn_label, key=f"cat_{key}", use_container_width=True, help=f"Click to explore {category['name']}"):
                st.session_state.opra_selected_category = key
                st.session_state.opra_active_tab = "Category Details"
                st.rerun()
    
    # Second row of 4
    cols2 = st.columns(4)
    for idx in range(4, 8):
        key = cat_keys[idx]
        category = OPRA_CATEGORIES[key]
        with cols2[idx - 4]:
            btn_label = f"🔹 {category['name']}\n\n{category['description']}\n\n🔴 {len(category['controls'])} Controls"
            if st.button(btn_label, key=f"cat_{key}", use_container_width=True, help=f"Click to explore {category['name']}"):
                st.session_state.opra_selected_category = key
                st.session_state.opra_active_tab = "Category Details"
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Quick actions ──
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Full Assessment", use_container_width=True):
            st.session_state.opra_active_tab = "Assessment"
            st.rerun()
    
    with col2:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state.opra_active_tab = "Reports"
            st.rerun()
    
    with col3:
        if st.button("💬 Ask SOPRA AI", use_container_width=True):
            st.session_state.opra_active_tab = "AI Assistant"
            st.rerun()


def render_category_details():
    """Render detailed view for a selected category with all controls and insights"""
    cat_key = st.session_state.opra_selected_category
    
    if not cat_key or cat_key not in OPRA_CATEGORIES:
        st.warning("No category selected. Returning to dashboard...")
        st.session_state.opra_active_tab = "Dashboard"
        st.rerun()
        return
    
    category = OPRA_CATEGORIES[cat_key]
    
    # Back button
    if st.button("← Back to Dashboard", key="back_to_dash"):
        st.session_state.opra_selected_category = None
        st.session_state.opra_selected_control = None
        st.session_state.opra_active_tab = "Dashboard"
        st.rerun()
    
    # Category header with professional icon
    st.markdown(f"""
    <div class="opra-header" style="padding: 2rem;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; margin-bottom: 0.5rem;">
            <div style="width: 60px; height: 60px; border-radius: 15px; background: linear-gradient(135deg, rgba(0, 217, 255, 0.2) 0%, rgba(15, 52, 96, 0.4) 100%); border: 2px solid rgba(0, 217, 255, 0.4); display: flex; align-items: center; justify-content: center;">
                <i class="{category['icon']}" style="font-size: 1.8rem; color: #00d9ff;"></i>
            </div>
            <h1 style="font-size: 2.5rem; margin: 0;">{category['name']}</h1>
        </div>
        <p style="color: #f0f0f0; font-size: 1.1rem; margin-top: 0.5rem;">{category['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Category overview metrics
    controls = category['controls']
    total_controls = len(controls)
    
    # Check how many have detailed definitions
    detailed_count = sum(1 for c in controls if get_control_by_id(c['id']))
    
    # Get assessment results for this category if available
    assessed_count = 0
    passed_count = 0
    failed_count = 0
    
    if st.session_state.opra_assessment_results:
        findings = st.session_state.opra_assessment_results.get("findings", [])
        cat_findings = [f for f in findings if f.get("category") == category['name']]
        assessed_count = len([f for f in cat_findings if f["status"] != "Not Assessed"])
        passed_count = len([f for f in cat_findings if f["status"] == "Passed"])
        failed_count = len([f for f in cat_findings if f["status"] == "Failed"])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Controls", str(total_controls), "#00d9ff")
    with col2:
        render_metric_card("Detailed Definitions", str(detailed_count), "#00d9ff")
    with col3:
        if st.session_state.opra_assessment_results:
            render_metric_card("Passed", str(passed_count), "#00d9ff")
        else:
            render_metric_card("Assessed", "0", "#666")
    with col4:
        if st.session_state.opra_assessment_results:
            color = "#e94560" if failed_count > 0 else "#00d9ff"
            render_metric_card("Failed", str(failed_count), color)
        else:
            render_metric_card("Failed", "0", "#666")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Category insights section
    st.markdown("### 📊 Category Insights")
    
    # Group controls by family
    families = {}
    for control in controls:
        family = control.get('family', 'Unknown')
        if family not in families:
            families[family] = []
        families[family].append(control)
    
    # Visual charts for this category
    insight_col1, insight_col2, insight_col3 = st.columns(3)
    
    with insight_col1:
        # Controls by Family pie chart
        fam_labels = list(families.keys())
        fam_values = [len(v) for v in families.values()]
        family_colors = ["#00d9ff", "#e94560", "#ffc107", "#00ff88", "#ff6b6b", "#a855f7"]
        fig_fam = go.Figure(data=[go.Pie(
            labels=fam_labels, values=fam_values, hole=0.45,
            marker_colors=family_colors[:len(fam_labels)],
            textinfo="label+value",
            textfont=dict(size=11, color="#f5f5f5")
        )])
        fig_fam.update_layout(
            title=dict(text="Controls by Family", font=dict(color="#00d9ff", size=14)),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f5f5f5', showlegend=False,
            height=260, margin=dict(t=35, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_fam, use_container_width=True)
    
    with insight_col2:
        # Assessment status for this category
        if st.session_state.opra_assessment_results:
            na_count = total_controls - passed_count - failed_count
            fig_cat_status = go.Figure(data=[go.Pie(
                labels=["Passed", "Failed", "Not Assessed"],
                values=[passed_count, failed_count, na_count],
                hole=0.5,
                marker_colors=["#00d9ff", "#e94560", "#3a3a5c"],
                textinfo="value+percent",
                textfont=dict(size=12, color="#f5f5f5")
            )])
            fig_cat_status.update_layout(
                title=dict(text="Assessment Status", font=dict(color="#00d9ff", size=14)),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font_color='#f5f5f5', showlegend=True,
                legend=dict(font=dict(color="#f5f5f5", size=10)),
                height=260, margin=dict(t=35, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_cat_status, use_container_width=True)
        else:
            fig_placeholder = go.Figure(go.Indicator(
                mode="gauge+number", value=0,
                number=dict(suffix="%", font=dict(color="#3a3a5c", size=24)),
                title=dict(text="Compliance", font=dict(color="#00d9ff", size=14)),
                gauge=dict(
                    axis=dict(range=[0, 100], tickcolor="#333", tickfont=dict(color="#666")),
                    bar=dict(color="#3a3a5c"), bgcolor="rgba(0,0,0,0)",
                    steps=[dict(range=[0, 100], color="rgba(0, 217, 255, 0.1)")]
                )
            ))
            fig_placeholder.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', font_color='#666',
                height=260, margin=dict(t=35, b=10, l=20, r=20)
            )
            st.plotly_chart(fig_placeholder, use_container_width=True)
    
    with insight_col3:
        # Key focus areas for this category
        focus_areas = get_category_focus_areas(cat_key)
        st.markdown("**🎯 Key Focus Areas:**")
        for area in focus_areas:
            st.markdown(f"- {area}")
    
    st.markdown("---")
    
    # Controls list with drill-down
    st.markdown("### 🔍 Controls in This Category")
    st.caption("Click any control to see detailed procedures and remediation guidance")
    
    # Control filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔎 Search controls", placeholder="Search by ID, name, or keyword...", key="ctrl_search")
    with col2:
        family_filter = st.selectbox("Filter by Family", ["All Families"] + list(families.keys()), key="fam_filter")
    
    # Filter controls
    filtered_controls = controls
    if search_term:
        search_lower = search_term.lower()
        filtered_controls = [c for c in filtered_controls if 
                           search_lower in c['id'].lower() or 
                           search_lower in c['name'].lower()]
    if family_filter != "All Families":
        filtered_controls = [c for c in filtered_controls if c.get('family') == family_filter]
    
    # Display controls
    for control_ref in filtered_controls:
        detailed_control = get_control_by_id(control_ref['id'])
        
        # Determine status color if assessed
        status_color = "#666"
        status_text = ""
        if st.session_state.opra_assessment_results:
            findings = st.session_state.opra_assessment_results.get("findings", [])
            ctrl_finding = next((f for f in findings if f["control_id"] == control_ref['id']), None)
            if ctrl_finding:
                if ctrl_finding["status"] == "Passed":
                    status_color = "#00d9ff"
                    status_text = " ✅"
                elif ctrl_finding["status"] == "Failed":
                    status_color = "#e94560"
                    status_text = f" ❌ ({ctrl_finding.get('severity', 'Unknown')})"
        
        with st.expander(f"**{control_ref['id']}**: {control_ref['name']}{status_text}", expanded=False):
            if detailed_control:
                # Overview tab
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Description:**")
                    st.markdown(detailed_control.description)
                    
                    st.markdown(f"**Default Severity:** `{detailed_control.default_severity.value}`")
                    st.markdown(f"**Family:** {control_ref['family']}")
                
                with col2:
                    st.markdown("**Mappings:**")
                    if detailed_control.nist_mapping:
                        st.markdown(f"🔖 **NIST 800-53:** {', '.join(detailed_control.nist_mapping)}")
                    if detailed_control.cis_mapping:
                        st.markdown(f"🔖 **CIS Controls:** {detailed_control.cis_mapping}")
                    if detailed_control.references:
                        st.markdown(f"📚 **References:** {', '.join(detailed_control.references[:2])}")
                
                st.markdown("---")
                
                # Check Procedure
                st.markdown("#### 📋 Check Procedure")
                st.code(detailed_control.check_procedure.strip(), language=None)
                
                st.markdown(f"**Expected Result:** {detailed_control.expected_result}")
                
                st.markdown("---")
                
                # Remediation Steps
                st.markdown("#### 🔧 Remediation Steps")
                
                if detailed_control.remediation_steps:
                    for step in detailed_control.remediation_steps:
                        downtime_badge = " ⚠️ **Requires Downtime**" if step.requires_downtime else ""
                        time_badge = f" `{step.estimated_time}`" if step.estimated_time else ""
                        
                        st.markdown(f"**Step {step.step_number}:** {step.description}{time_badge}{downtime_badge}")
                        
                        if step.command:
                            st.code(step.command, language=step.script_type or "powershell")
                    
                    # Download remediation script
                    ps_script = get_remediation_script(control_ref['id'], "powershell")
                    if ps_script and len(ps_script) > 100:
                        st.download_button(
                            label="📥 Download PowerShell Remediation Script",
                            data=ps_script,
                            file_name=f"remediate_{control_ref['id']}.ps1",
                            mime="text/plain",
                            key=f"dl_script_{control_ref['id']}"
                        )
                else:
                    st.info("Remediation steps not yet defined for this control.")
            else:
                st.warning(f"Detailed definition not yet available for {control_ref['id']}. Basic info:")
                st.markdown(f"- **Name:** {control_ref['name']}")
                st.markdown(f"- **Family:** {control_ref['family']}")
    
    # Action buttons at bottom
    st.markdown("---")
    st.markdown("### 🚀 Actions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"▶️ Assess {category['name']}", use_container_width=True):
            st.session_state.opra_active_tab = "Assessment"
            st.rerun()
    with col2:
        if st.button("💬 Ask SOPRA AI About This", use_container_width=True):
            # Pre-populate a question about this category
            st.session_state.opra_chat_history.append({
                "role": "user", 
                "content": f"What are the most important security considerations for {category['name']}?"
            })
            st.session_state.opra_active_tab = "AI Assistant"
            st.rerun()
    with col3:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state.opra_active_tab = "Reports"
            st.rerun()


def get_category_focus_areas(cat_key):
    """Get key focus areas for each category"""
    focus_areas = {
        "active_directory": [
            "🔐 Privileged account security and tiered admin model",
            "🔑 Kerberos security (AES encryption, pre-auth)",
            "📋 Group Policy hardening and auditing",
            "🔒 LDAP signing and channel binding",
            "👥 Service account management with gMSA"
        ],
        "network_infrastructure": [
            "🌐 Network segmentation and micro-segmentation",
            "🛡️ Firewall rule optimization and review",
            "📡 IDS/IPS deployment and tuning",
            "🔒 VPN security with MFA",
            "📊 Network traffic monitoring and analysis"
        ],
        "endpoint_security": [
            "🦠 Endpoint protection platform (EPP/AV) coverage",
            "📦 Patch management and vulnerability remediation",
            "🔐 Local admin rights removal (LAPS)",
            "💿 Full disk encryption (BitLocker)",
            "🕵️ EDR/XDR deployment for threat detection"
        ],
        "server_security": [
            "🔧 CIS/STIG hardening baselines",
            "🗄️ Database security (TDE, access controls)",
            "🌐 Web server security headers and TLS",
            "💾 Backup server protection from ransomware",
            "🖥️ Virtualization security and isolation"
        ],
        "physical_security": [
            "🚪 Physical access control systems",
            "📹 Video surveillance and monitoring",
            "🏢 Server room environmental controls",
            "⚡ Emergency power (UPS/generator)",
            "🔥 Fire detection and suppression"
        ],
        "data_protection": [
            "📊 Data classification and labeling",
            "🚫 Data loss prevention (DLP)",
            "🔐 Encryption at rest and in transit",
            "💾 Backup and recovery (3-2-1 rule)",
            "🔑 Key management and rotation"
        ],
        "identity_access": [
            "🔐 Multi-factor authentication (MFA)",
            "👤 Privileged access management (PAM)",
            "🎭 Role-based access control (RBAC)",
            "🔄 Account lifecycle management",
            "📋 Access review and certification"
        ],
        "monitoring_logging": [
            "📊 SIEM implementation and tuning",
            "📝 Centralized log collection",
            "🚨 Real-time alerting and escalation",
            "🔍 Threat detection and correlation",
            "📈 User behavior analytics (UBA)"
        ]
    }
    return focus_areas.get(cat_key, ["No specific focus areas defined"])


def render_metric_details():
    """Render detailed view for a selected metric"""
    metric = st.session_state.opra_selected_metric
    
    if not metric:
        st.session_state.opra_active_tab = "Dashboard"
        st.rerun()
        return
    
    # Back button
    if st.button("← Back to Dashboard", key="back_from_metric"):
        st.session_state.opra_selected_metric = None
        st.session_state.opra_active_tab = "Dashboard"
        st.rerun()
    
    if metric == "categories":
        render_categories_detail()
    elif metric == "controls":
        render_controls_detail()
    elif metric == "risk_score":
        render_risk_score_detail()
    elif metric == "status":
        render_status_detail()


def render_categories_detail():
    """Detailed view for Assessment Categories metric"""
    st.markdown("""
    <div class="opra-header" style="padding: 2rem;">
        <h1 style="font-size: 2.5rem; margin: 0;">📊 Assessment Categories</h1>
        <p style="color: #f0f0f0; font-size: 1.1rem; margin-top: 0.5rem;">20 comprehensive security domains for on-premise infrastructure</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    ### Overview
    
    SOPRA organizes security controls into **20 assessment categories** (200 controls total), each focusing on a critical aspect of on-premise infrastructure security. This structure aligns with industry frameworks including **NIST 800-53 Rev 5** and **CIS Controls v8**.
    
    ### Why 20 Categories?
    
    These categories provide complete coverage of enterprise security:
    """)
    
    # Display categories with details
    for key, category in OPRA_CATEGORIES.items():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem;">
                <div style="width: 60px; height: 60px; border-radius: 15px; background: linear-gradient(135deg, rgba(0, 217, 255, 0.2) 0%, rgba(15, 52, 96, 0.4) 100%); border: 2px solid rgba(0, 217, 255, 0.4); display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                    <i class="{category['icon']}" style="font-size: 1.5rem; color: #00d9ff;"></i>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"#### {category['name']}")
            st.markdown(f"{category['description']}")
            st.markdown(f"**{len(category['controls'])} controls** | Families: {', '.join(set(c['family'] for c in category['controls'][:3]))}")
        st.markdown("---")
    
    # Framework alignment
    st.markdown("""
    ### Framework Alignment
    
    | Framework | Alignment |
    |-----------|-----------|
    | **NIST 800-53 Rev 5** | Full mapping to control families (AC, AU, CM, CP, IA, IR, MA, MP, PE, PL, PS, RA, SA, SC, SI) |
    | **CIS Controls v8** | Mapped to applicable safeguards |
    | **ISO 27001** | Aligned with Annex A controls |
    | **CMMC 2.0** | Supports Level 2 and 3 practices |
    """)
    
    if st.button("▶️ Start Assessment", use_container_width=True, type="primary"):
        st.session_state.opra_active_tab = "Assessment"
        st.rerun()


def render_controls_detail():
    """Detailed view for Total Controls metric"""
    st.markdown("""
    <div class="opra-header" style="padding: 2rem;">
        <h1 style="font-size: 2.5rem; margin: 0;">🔧 80 Security Controls</h1>
        <p style="color: #f0f0f0; font-size: 1.1rem; margin-top: 0.5rem;">Comprehensive control library with procedures, remediation, and mappings</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Controls", "80", "#00d9ff")
    with col2:
        render_metric_card("Categories", "8", "#00d9ff")
    with col3:
        critical_count = sum(1 for c in ALL_CONTROLS.values() if c.default_severity.value == "Critical")
        render_metric_card("Critical", str(critical_count), "#e94560")
    with col4:
        high_count = sum(1 for c in ALL_CONTROLS.values() if c.default_severity.value == "High")
        render_metric_card("High", str(high_count), "#ff6b6b")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    ### What Each Control Includes
    
    Every control in SOPRA provides comprehensive guidance:
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### 📋 Assessment Components
        - **Control ID & Name** - Unique identifier (e.g., AD-001)
        - **Description** - What the control addresses
        - **Check Procedure** - Step-by-step verification process
        - **Expected Result** - What compliance looks like
        - **Default Severity** - Risk if control fails
        """)
    with col2:
        st.markdown("""
        #### 🔧 Remediation Components
        - **Remediation Steps** - Numbered action items
        - **Commands/Scripts** - PowerShell, GPO, CLI examples
        - **Time Estimates** - Implementation duration
        - **Downtime Indicators** - Change management flags
        - **References** - Documentation links
        """)
    
    st.markdown("""
    ### Controls by Severity
    """)
    
    # Severity breakdown
    severity_counts = {}
    for control in ALL_CONTROLS.values():
        sev = control.default_severity.value
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    import plotly.express as px
    fig = px.pie(
        values=list(severity_counts.values()),
        names=list(severity_counts.keys()),
        color_discrete_sequence=["#e94560", "#ff6b6b", "#ffc107", "#00d9ff"],
        hole=0.4
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#f5f5f5'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    ### Compliance Mappings
    
    | Control Family | NIST 800-53 | CIS Controls v8 | Count |
    |----------------|-------------|-----------------|-------|
    | Access Control | AC-2, AC-3, AC-6 | 5, 6 | Multiple |
    | Audit & Accountability | AU-2, AU-3, AU-6 | 8 | Multiple |
    | Configuration Management | CM-6, CM-7 | 4 | Multiple |
    | System & Communications | SC-7, SC-8, SC-28 | 3, 12 | Multiple |
    | System & Info Integrity | SI-2, SI-3, SI-4 | 7, 10, 13 | Multiple |
    """)
    
    if st.button("📖 Browse All Controls", use_container_width=True, type="primary"):
        st.session_state.opra_active_tab = "Assessment"
        st.rerun()


def render_risk_score_detail():
    """Detailed view for Risk Score metric"""
    st.markdown("""
    <div class="opra-header" style="padding: 2rem;">
        <h1 style="font-size: 2.5rem; margin: 0;">📈 Risk Score Methodology</h1>
        <p style="color: #f0f0f0; font-size: 1.1rem; margin-top: 0.5rem;">Understanding how SOPRA calculates your security posture</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Current score if available
    if st.session_state.opra_assessment_results:
        score = calculate_risk_score(st.session_state.opra_assessment_results.get("findings", []))
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 4rem; font-weight: bold; color: {get_risk_color(score)};">{score}%</div>
            <div style="color: #f0f0f0; font-size: 1.2rem;">Your Current Risk Score</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("⏳ Complete an assessment to see your Risk Score")
    
    st.markdown("""
    ### Calculation Formula
    
    The Risk Score is calculated using a **severity-weighted formula**:
    
    ```
    Risk Score = 100 - (Weighted Failed Controls / Total Weighted Controls × 100)
    ```
    
    ### Severity Weights
    
    | Severity | Weight | Rationale |
    |----------|--------|-----------|
    | **Critical** | 10 | Immediate exploitation risk, data breach potential |
    | **High** | 7 | Significant security gap, priority remediation |
    | **Medium** | 4 | Moderate risk, should be addressed |
    | **Low** | 1 | Minor issue, address when possible |
    
    ### Score Interpretation
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="padding: 1rem; background: rgba(0, 217, 255, 0.1); border-left: 4px solid #00d9ff; border-radius: 8px; margin: 0.5rem 0;">
            <strong style="color: #00d9ff;">🟢 80-100%: Strong</strong><br>
            <span style="color: #f0f0f0;">Excellent security posture. Continue monitoring and maintaining controls.</span>
        </div>
        <div style="padding: 1rem; background: rgba(255, 193, 7, 0.1); border-left: 4px solid #ffc107; border-radius: 8px; margin: 0.5rem 0;">
            <strong style="color: #ffc107;">🟡 60-79%: Moderate</strong><br>
            <span style="color: #f0f0f0;">Some gaps exist. Prioritize High/Critical findings for remediation.</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="padding: 1rem; background: rgba(255, 107, 107, 0.1); border-left: 4px solid #ff6b6b; border-radius: 8px; margin: 0.5rem 0;">
            <strong style="color: #ff6b6b;">🟠 40-59%: Elevated</strong><br>
            <span style="color: #f0f0f0;">Significant risk. Implement remediation plan immediately.</span>
        </div>
        <div style="padding: 1rem; background: rgba(233, 69, 96, 0.1); border-left: 4px solid #e94560; border-radius: 8px; margin: 0.5rem 0;">
            <strong style="color: #e94560;">🔴 0-39%: Critical</strong><br>
            <span style="color: #f0f0f0;">Severe risk exposure. Emergency remediation required.</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    ### Improving Your Score
    
    1. **Focus on Critical/High first** - These have the highest weight
    2. **Use remediation scripts** - SOPRA provides PowerShell automation
    3. **Track progress** - Re-assess after remediation
    4. **Generate POA&M** - Document your remediation plan
    """)
    
    if not st.session_state.opra_assessment_results:
        if st.button("▶️ Start Assessment", use_container_width=True, type="primary"):
            st.session_state.opra_active_tab = "Assessment"
            st.rerun()


def render_status_detail():
    """Detailed view for Status metric"""
    st.markdown("""
    <div class="opra-header" style="padding: 2rem;">
        <h1 style="font-size: 2.5rem; margin: 0;">📋 Assessment Status</h1>
        <p style="color: #f0f0f0; font-size: 1.1rem; margin-top: 0.5rem;">Current assessment state and next steps</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.session_state.opra_assessment_results:
        results = st.session_state.opra_assessment_results
        findings = results.get("findings", [])
        timestamp = results.get("timestamp", "Unknown")
        
        st.success("✅ Assessment Complete")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card("Total Assessed", str(len(findings)), "#00d9ff")
        with col2:
            passed = len([f for f in findings if f["status"] == "Passed"])
            render_metric_card("Passed", str(passed), "#00d9ff")
        with col3:
            failed = len([f for f in findings if f["status"] == "Failed"])
            render_metric_card("Failed", str(failed), "#e94560")
        with col4:
            score = calculate_risk_score(findings)
            render_metric_card("Risk Score", f"{score}%", get_risk_color(score))
        
        st.markdown(f"""
        <br>
        
        ### Assessment Details
        
        | Property | Value |
        |----------|-------|
        | **Completed** | {timestamp[:19] if len(timestamp) > 19 else timestamp} |
        | **Categories Assessed** | {len(results.get('categories_assessed', []))} |
        | **Include Remediation** | {'Yes' if results.get('include_remediation') else 'No'} |
        """, unsafe_allow_html=True)
        
        st.markdown("### Next Steps")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 View Reports", use_container_width=True):
                st.session_state.opra_active_tab = "Reports"
                st.rerun()
        with col2:
            if st.button("🔄 Run New Assessment", use_container_width=True):
                st.session_state.opra_active_tab = "Assessment"
                st.rerun()
        with col3:
            if st.button("💬 Discuss with AI", use_container_width=True):
                st.session_state.opra_active_tab = "AI Assistant"
                st.rerun()
    
    else:
        st.warning("⏳ Assessment Pending")
        
        st.markdown("""
        ### No assessment has been completed yet.
        
        A SOPRA assessment evaluates your on-premise infrastructure against 80 security controls across 8 categories.
        
        ### How to Start
        
        1. **Click "Start Assessment"** below or navigate to the Assessment tab
        2. **Select categories** to assess (or assess all)
        3. **Answer questionnaire** for each control
        4. **Review results** and generate reports
        
        ### Time Required
        
        | Scope | Estimated Time |
        |-------|---------------|
        | Single Category | 5-10 minutes |
        | Half Assessment | 20-30 minutes |
        | Full Assessment | 45-60 minutes |
        
        ### What You'll Get
        
        - ✅ Risk Score and security posture rating
        - 📊 Detailed findings by severity
        - 🔧 Remediation guidance with scripts
        - 📋 Exportable reports (Executive Summary, Full Report, POA&M)
        """)
        
        if st.button("▶️ Start Assessment Now", use_container_width=True, type="primary"):
            st.session_state.opra_active_tab = "Assessment"
            st.rerun()


def render_assessment_page():
    """Render the assessment configuration and execution page"""
    st.markdown("## 🔍 On-Premise Assessment")
    
    # =========================================================================
    # ZERO-TOUCH ARCHITECTURE BANNER - Prominent emphasis on CSV-based approach
    # =========================================================================
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(0, 217, 255, 0.15) 0%, rgba(15, 52, 96, 0.3) 100%); 
                border: 2px solid rgba(0, 217, 255, 0.5); 
                border-radius: 15px; 
                padding: 1.5rem 2rem; 
                margin-bottom: 2rem;
                position: relative;
                overflow: hidden;">
        <div style="display: flex; align-items: center; gap: 1.5rem;">
            <div style="flex-shrink: 0;">
                <i class="fa-solid fa-shield-halved" style="font-size: 3rem; color: #00d9ff;"></i>
            </div>
            <div>
                <h3 style="color: #00d9ff; margin: 0 0 0.5rem 0; font-size: 1.4rem;">
                    🔒 Zero-Touch Architecture
                </h3>
                <p style="color: #e8e8e8; margin: 0; font-size: 1.05rem; line-height: 1.6;">
                    <strong>SOPRA never connects to or touches your environment.</strong> 
                    You export your system data using your own tools, then upload CSV files for analysis. 
                    Your security data stays under your complete control at all times.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # PRIMARY: CSV FILE UPLOAD SECTION
    # =========================================================================
    st.markdown("### 📁 CSV Data Ingestion")
    st.markdown("**Primary Method:** Upload CSV exports from your environment for security assessment")
    
    # Category selection for CSV upload
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_categories = st.multiselect(
            "Select Categories to Assess",
            options=list(OPRA_CATEGORIES.keys()),
            default=list(OPRA_CATEGORIES.keys()),
            format_func=lambda x: f"{OPRA_CATEGORIES[x]['name']}",
            help="Choose which security domains to include in your assessment"
        )
    with col2:
        include_remediation = st.checkbox("Include remediation guidance", value=True, key="csv_remediation")
    
    # CSV Upload Interface - Main Focus
    st.markdown("---")
    
    # Three-step process visualization
    st.markdown("""
    <div style="display: flex; justify-content: space-between; gap: 1rem; margin-bottom: 2rem;">
        <div style="flex: 1; text-align: center; padding: 1.5rem; background: rgba(15, 52, 96, 0.4); border-radius: 12px; border: 1px solid rgba(0, 217, 255, 0.3);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">1️⃣</div>
            <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0;">Download Templates</h4>
            <p style="color: #f0f0f0; font-size: 0.9rem; margin: 0;">Get CSV templates with the required data fields</p>
        </div>
        <div style="flex: 1; text-align: center; padding: 1.5rem; background: rgba(15, 52, 96, 0.4); border-radius: 12px; border: 1px solid rgba(0, 217, 255, 0.3);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">2️⃣</div>
            <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0;">Export Your Data</h4>
            <p style="color: #f0f0f0; font-size: 0.9rem; margin: 0;">Run provided scripts in YOUR environment</p>
        </div>
        <div style="flex: 1; text-align: center; padding: 1.5rem; background: rgba(15, 52, 96, 0.4); border-radius: 12px; border: 1px solid rgba(0, 217, 255, 0.3);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">3️⃣</div>
            <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0;">Upload & Analyze</h4>
            <p style="color: #f0f0f0; font-size: 0.9rem; margin: 0;">Upload CSVs for automated assessment</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Templates and Upload tabs
    csv_tab1, csv_tab2, csv_tab3 = st.tabs(["📥 Download Templates", "📤 Upload CSV Files", "🔧 Export Scripts"])
    
    with csv_tab1:
        st.markdown("#### CSV Templates by Category")
        st.markdown("Download these templates, then populate them with your environment data.")
        
        template_col1, template_col2 = st.columns(2)
        
        with template_col1:
            # Generate template CSVs for each category
            for cat_key in ["active_directory", "network_infrastructure", "endpoint_security", "server_security"]:
                if cat_key in OPRA_CATEGORIES:
                    cat = OPRA_CATEGORIES[cat_key]
                    template_csv = generate_csv_template(cat_key)
                    st.download_button(
                        label=f"📄 {cat['name']} Template",
                        data=template_csv,
                        file_name=f"sopra_{cat_key}_template.csv",
                        mime="text/csv",
                        key=f"template_{cat_key}",
                        use_container_width=True
                    )
        
        with template_col2:
            for cat_key in ["physical_security", "data_protection", "identity_access_management", "monitoring_logging"]:
                if cat_key in OPRA_CATEGORIES:
                    cat = OPRA_CATEGORIES[cat_key]
                    template_csv = generate_csv_template(cat_key)
                    st.download_button(
                        label=f"📄 {cat['name']} Template",
                        data=template_csv,
                        file_name=f"sopra_{cat_key}_template.csv",
                        mime="text/csv",
                        key=f"template_{cat_key}",
                        use_container_width=True
                    )
        
        # Download all templates as one
        st.markdown("---")
        all_templates = generate_master_csv_template()
        st.download_button(
            label="📦 Download All Templates (Combined)",
            data=all_templates,
            file_name="sopra_all_templates.csv",
            mime="text/csv",
            key="template_all",
            type="primary",
            use_container_width=True
        )
    
    with csv_tab2:
        st.markdown("#### Upload Your CSV Files")
        st.markdown("Upload one or more CSV files containing your exported environment data.")
        
        uploaded_files = st.file_uploader(
            "Drop CSV files here or click to browse",
            type=["csv"],
            accept_multiple_files=True,
            key="csv_upload",
            help="You can upload multiple CSV files at once"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
            
            # Show uploaded files summary
            for f in uploaded_files:
                with st.expander(f"📄 {f.name}", expanded=False):
                    try:
                        import pandas as pd
                        df = pd.read_csv(f)
                        st.dataframe(df.head(10), use_container_width=True)
                        st.caption(f"Showing first 10 of {len(df)} rows")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")
            
            st.markdown("---")
            if st.button("🚀 Process CSV Data & Run Assessment", type="primary", use_container_width=True):
                process_csv_assessment(uploaded_files, selected_categories, include_remediation)
        else:
            st.info("📁 Upload your CSV exports to begin the assessment. Use the templates from the 'Download Templates' tab.")
    
    with csv_tab3:
        st.markdown("#### SOPRA Data Export Tool")
        st.markdown("Download and run this **single unified script** in your environment. It provides an interactive menu to export all the data SOPRA needs.")
        
        # Generate the unified script
        unified_script = generate_unified_export_script()
        
        st.markdown("""
        <div style="background: rgba(0, 217, 255, 0.1); border: 1px solid rgba(0, 217, 255, 0.3); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0;">📜 SOPRA-Export.ps1</h4>
            <p style="color: #f0f0f0; margin: 0 0 1rem 0;">
                One script with an interactive menu. Run it on any Windows system to export security configuration data.
            </p>
            <ul style="color: #f0f0f0; margin: 0; padding-left: 1.5rem;">
                <li>Interactive menu - select what to export</li>
                <li>Exports data to CSV format</li>
                <li>No external dependencies required</li>
                <li>Safe, read-only operations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Download button for unified script
        st.download_button(
            label="📥 Download SOPRA-Export.ps1",
            data=unified_script,
            file_name="SOPRA-Export.ps1",
            mime="text/plain",
            key="unified_export_script",
            type="primary",
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Show script preview
        with st.expander("👁️ Preview Script", expanded=False):
            st.code(unified_script, language="powershell")
    
    # =========================================================================
    # SECONDARY: Manual Assessment Option
    # =========================================================================
    st.markdown("---")
    with st.expander("📝 Alternative: Manual Assessment Questionnaire", expanded=False):
        st.markdown("""
        <div style="background: rgba(255, 193, 7, 0.1); border-left: 4px solid #ffc107; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <strong style="color: #ffc107;">ℹ️ When to Use Manual Assessment</strong><br>
            <span style="color: #f0f0f0;">Use this option when you cannot export CSV data, or for quick initial assessments. 
            CSV-based assessment is recommended for accuracy and audit trails.</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Manual Assessment", type="secondary", use_container_width=True, key="manual_assess_btn"):
            run_manual_assessment(selected_categories, include_remediation)


def generate_csv_template(category_key):
    """Generate a CSV template for a specific category"""
    import io
    
    category = OPRA_CATEGORIES.get(category_key, {})
    controls = category.get('controls', [])
    
    # Create template with headers and example data
    lines = ["control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date"]
    
    for ctrl in controls:
        detailed = get_control_by_id(ctrl['id'])
        default_sev = detailed.default_severity.value if detailed else "Medium"
        lines.append(f'{ctrl["id"]},"{ctrl["name"]}",Not Assessed,{default_sev},"","",""," "')
    
    return "\n".join(lines)


def generate_master_csv_template():
    """Generate a combined CSV template with all categories"""
    import io
    
    lines = ["category,control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date"]
    
    for cat_key, category in OPRA_CATEGORIES.items():
        for ctrl in category.get('controls', []):
            detailed = get_control_by_id(ctrl['id'])
            default_sev = detailed.default_severity.value if detailed else "Medium"
            lines.append(f'"{category["name"]}",{ctrl["id"]},"{ctrl["name"]}",Not Assessed,{default_sev},"","",""," "')
    
    return "\n".join(lines)


def generate_unified_export_script():
    """Generate a single unified PowerShell export script with interactive menu"""
    
    script = '''#Requires -Version 5.1
<#
.SYNOPSIS
    SOPRA Data Export Tool - Unified Export Script
    
.DESCRIPTION
    This script exports security configuration data from your Windows environment
    for analysis by SOPRA (SAE On-Premise Risk Assessment). All operations are READ-ONLY
    and do not modify your system.
    
.NOTES
    Version: 1.0
    Author: SOPRA Security Tool
    
.EXAMPLE
    .\\SOPRA-Export.ps1
    Runs the interactive menu to select what data to export.
    
.EXAMPLE
    .\\SOPRA-Export.ps1 -ExportAll
    Exports all available data without prompting.
#>

param(
    [switch]$ExportAll,
    [string]$OutputPath = "C:\\SOPRA_Exports"
)

# ============================================================================
# CONFIGURATION
# ============================================================================
$Script:ExportPath = $OutputPath
$Script:ExportedFiles = @()

# Create output directory
function Initialize-ExportDirectory {
    if (-not (Test-Path $Script:ExportPath)) {
        New-Item -ItemType Directory -Force -Path $Script:ExportPath | Out-Null
    }
    Write-Host ""
    Write-Host "  Export Directory: $Script:ExportPath" -ForegroundColor Cyan
    Write-Host ""
}

# ============================================================================
# BANNER
# ============================================================================
function Show-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║                                                               ║" -ForegroundColor Cyan
    Write-Host "  ║   ██████╗ ██████╗ ██████╗  █████╗                            ║" -ForegroundColor Cyan
    Write-Host "  ║  ██╔═══██╗██╔══██╗██╔══██╗██╔══██╗                           ║" -ForegroundColor Cyan
    Write-Host "  ║  ██║   ██║██████╔╝██████╔╝███████║                           ║" -ForegroundColor Cyan
    Write-Host "  ║  ██║   ██║██╔═══╝ ██╔══██╗██╔══██║                           ║" -ForegroundColor Cyan
    Write-Host "  ║  ╚██████╔╝██║     ██║  ██║██║  ██║                           ║" -ForegroundColor Cyan
    Write-Host "  ║   ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝                           ║" -ForegroundColor Cyan
    Write-Host "  ║                                                               ║" -ForegroundColor Cyan
    Write-Host "  ║          On-Premise Risk Assessment - Data Export            ║" -ForegroundColor White
    Write-Host "  ║                                                               ║" -ForegroundColor Cyan
    Write-Host "  ╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  This tool exports security data for SOPRA analysis." -ForegroundColor Gray
    Write-Host "  All operations are READ-ONLY and safe to run." -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# MAIN MENU
# ============================================================================
function Show-MainMenu {
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │                      MAIN MENU                              │" -ForegroundColor DarkCyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │                                                             │" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Active Directory Security                           │" -ForegroundColor White
    Write-Host "  │   [2]  Network Infrastructure                              │" -ForegroundColor White
    Write-Host "  │   [3]  Endpoint Security                                   │" -ForegroundColor White
    Write-Host "  │   [4]  Server Security                                     │" -ForegroundColor White
    Write-Host "  │   [5]  Data Protection                                     │" -ForegroundColor White
    Write-Host "  │   [6]  Identity & Access Management                        │" -ForegroundColor White
    Write-Host "  │   [7]  Monitoring & Logging                                │" -ForegroundColor White
    Write-Host "  │                                                             │" -ForegroundColor DarkCyan
    Write-Host "  │   [A]  Export ALL Categories                               │" -ForegroundColor Green
    Write-Host "  │   [V]  View Exported Files                                 │" -ForegroundColor Yellow
    Write-Host "  │   [Q]  Quit                                                │" -ForegroundColor Red
    Write-Host "  │                                                             │" -ForegroundColor DarkCyan
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

# ============================================================================
# CATEGORY SUBMENUS
# ============================================================================
function Show-ADMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            ACTIVE DIRECTORY SECURITY                        │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Domain Admins                                       │" -ForegroundColor White
    Write-Host "  │   [2]  Service Accounts                                    │" -ForegroundColor White
    Write-Host "  │   [3]  Group Policy Objects (GPOs)                         │" -ForegroundColor White
    Write-Host "  │   [4]  Privileged Groups                                   │" -ForegroundColor White
    Write-Host "  │   [5]  Stale/Inactive Accounts                             │" -ForegroundColor White
    Write-Host "  │   [A]  Export All AD Data                                  │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-NetworkMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            NETWORK INFRASTRUCTURE                           │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Firewall Rules                                      │" -ForegroundColor White
    Write-Host "  │   [2]  Network Configuration                               │" -ForegroundColor White
    Write-Host "  │   [3]  DNS Configuration                                   │" -ForegroundColor White
    Write-Host "  │   [4]  Open Ports & Listeners                              │" -ForegroundColor White
    Write-Host "  │   [A]  Export All Network Data                             │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-EndpointMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            ENDPOINT SECURITY                                │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Windows Defender Status                             │" -ForegroundColor White
    Write-Host "  │   [2]  Installed Software                                  │" -ForegroundColor White
    Write-Host "  │   [3]  Running Services                                    │" -ForegroundColor White
    Write-Host "  │   [4]  Scheduled Tasks                                     │" -ForegroundColor White
    Write-Host "  │   [A]  Export All Endpoint Data                            │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-ServerMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            SERVER SECURITY                                  │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Installed Roles & Features                          │" -ForegroundColor White
    Write-Host "  │   [2]  Windows Updates                                     │" -ForegroundColor White
    Write-Host "  │   [3]  IIS Configuration (if installed)                    │" -ForegroundColor White
    Write-Host "  │   [A]  Export All Server Data                              │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-DataProtectionMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            DATA PROTECTION                                  │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  BitLocker Status                                    │" -ForegroundColor White
    Write-Host "  │   [2]  Shared Folders & Permissions                        │" -ForegroundColor White
    Write-Host "  │   [A]  Export All Data Protection Info                     │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-IAMMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            IDENTITY & ACCESS MANAGEMENT                     │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Local Administrators                                │" -ForegroundColor White
    Write-Host "  │   [2]  Local Users & Groups                                │" -ForegroundColor White
    Write-Host "  │   [3]  Password Policy                                     │" -ForegroundColor White
    Write-Host "  │   [A]  Export All IAM Data                                 │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-MonitoringMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            MONITORING & LOGGING                             │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Audit Policy                                        │" -ForegroundColor White
    Write-Host "  │   [2]  Event Log Configuration                             │" -ForegroundColor White
    Write-Host "  │   [3]  Recent Security Events                              │" -ForegroundColor White
    Write-Host "  │   [A]  Export All Monitoring Data                          │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

function Write-ExportStatus {
    param([string]$Message, [string]$Status = "INFO")
    
    switch ($Status) {
        "OK"      { Write-Host "  [OK] " -ForegroundColor Green -NoNewline; Write-Host $Message }
        "FAIL"    { Write-Host "  [FAIL] " -ForegroundColor Red -NoNewline; Write-Host $Message }
        "SKIP"    { Write-Host "  [SKIP] " -ForegroundColor Yellow -NoNewline; Write-Host $Message }
        "INFO"    { Write-Host "  [INFO] " -ForegroundColor Cyan -NoNewline; Write-Host $Message }
        default   { Write-Host "  $Message" }
    }
}

# --- ACTIVE DIRECTORY ---
function Export-DomainAdmins {
    try {
        $data = Get-ADGroupMember -Identity "Domain Admins" -ErrorAction Stop | 
            Get-ADUser -Properties LastLogonDate, Enabled, PasswordLastSet, Description |
            Select-Object SamAccountName, Name, Enabled, LastLogonDate, PasswordLastSet, Description
        $file = "$Script:ExportPath\\ad_domain_admins.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Domain Admins -> $file" "OK"
    } catch {
        Write-ExportStatus "Domain Admins - AD module not available or not on domain" "SKIP"
    }
}

function Export-ServiceAccounts {
    try {
        $data = Get-ADUser -Filter {ServicePrincipalName -like "*"} -Properties ServicePrincipalName, PasswordLastSet, Enabled, Description -ErrorAction Stop |
            Select-Object SamAccountName, Name, Enabled, PasswordLastSet, Description, @{N='SPNs';E={$_.ServicePrincipalName -join "; "}}
        $file = "$Script:ExportPath\\ad_service_accounts.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Service Accounts -> $file" "OK"
    } catch {
        Write-ExportStatus "Service Accounts - AD module not available" "SKIP"
    }
}

function Export-GPOs {
    try {
        $data = Get-GPO -All -ErrorAction Stop | 
            Select-Object DisplayName, Id, GpoStatus, CreationTime, ModificationTime
        $file = "$Script:ExportPath\\ad_gpos.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Group Policy Objects -> $file" "OK"
    } catch {
        Write-ExportStatus "GPOs - GroupPolicy module not available" "SKIP"
    }
}

function Export-PrivilegedGroups {
    try {
        $groups = @("Domain Admins", "Enterprise Admins", "Schema Admins", "Administrators", "Account Operators", "Backup Operators")
        $allMembers = @()
        foreach ($group in $groups) {
            try {
                $members = Get-ADGroupMember -Identity $group -ErrorAction SilentlyContinue
                foreach ($member in $members) {
                    $allMembers += [PSCustomObject]@{
                        GroupName = $group
                        MemberName = $member.Name
                        MemberType = $member.objectClass
                        SamAccountName = $member.SamAccountName
                    }
                }
            } catch { }
        }
        $file = "$Script:ExportPath\\ad_privileged_groups.csv"
        $allMembers | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Privileged Groups -> $file" "OK"
    } catch {
        Write-ExportStatus "Privileged Groups - AD module not available" "SKIP"
    }
}

function Export-StaleAccounts {
    try {
        $staleDate = (Get-Date).AddDays(-90)
        $data = Get-ADUser -Filter {LastLogonDate -lt $staleDate -and Enabled -eq $true} -Properties LastLogonDate, PasswordLastSet -ErrorAction Stop |
            Select-Object SamAccountName, Name, LastLogonDate, PasswordLastSet
        $file = "$Script:ExportPath\\ad_stale_accounts.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Stale Accounts (90+ days) -> $file" "OK"
    } catch {
        Write-ExportStatus "Stale Accounts - AD module not available" "SKIP"
    }
}

# --- NETWORK ---
function Export-FirewallRules {
    try {
        $data = Get-NetFirewallRule -ErrorAction Stop | 
            Select-Object Name, DisplayName, Enabled, Direction, Action, Profile
        $file = "$Script:ExportPath\\network_firewall_rules.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Firewall Rules -> $file" "OK"
    } catch {
        Write-ExportStatus "Firewall Rules - NetSecurity module not available" "SKIP"
    }
}

function Export-NetworkConfig {
    try {
        $data = Get-NetIPConfiguration -ErrorAction Stop | 
            Select-Object InterfaceAlias, @{N='IPv4Address';E={$_.IPv4Address.IPAddress}}, 
                          @{N='Gateway';E={$_.IPv4DefaultGateway.NextHop}},
                          @{N='DNS';E={$_.DNSServer.ServerAddresses -join "; "}}
        $file = "$Script:ExportPath\\network_config.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Network Configuration -> $file" "OK"
    } catch {
        Write-ExportStatus "Network Configuration failed" "FAIL"
    }
}

function Export-DNSConfig {
    try {
        $data = Get-DnsClientServerAddress -ErrorAction Stop | 
            Where-Object { $_.ServerAddresses } |
            Select-Object InterfaceAlias, @{N='DNSServers';E={$_.ServerAddresses -join "; "}}
        $file = "$Script:ExportPath\\network_dns.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "DNS Configuration -> $file" "OK"
    } catch {
        Write-ExportStatus "DNS Configuration failed" "FAIL"
    }
}

function Export-OpenPorts {
    try {
        $data = Get-NetTCPConnection -State Listen -ErrorAction Stop | 
            Select-Object LocalAddress, LocalPort, OwningProcess, 
                          @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}}
        $file = "$Script:ExportPath\\network_open_ports.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Open Ports -> $file" "OK"
    } catch {
        Write-ExportStatus "Open Ports failed" "FAIL"
    }
}

# --- ENDPOINT ---
function Export-DefenderStatus {
    try {
        $data = Get-MpComputerStatus -ErrorAction Stop | 
            Select-Object AMServiceEnabled, AntispywareEnabled, AntivirusEnabled, 
                          RealTimeProtectionEnabled, AntivirusSignatureLastUpdated, NISEnabled
        $file = "$Script:ExportPath\\endpoint_defender.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Windows Defender Status -> $file" "OK"
    } catch {
        Write-ExportStatus "Windows Defender - Defender module not available" "SKIP"
    }
}

function Export-InstalledSoftware {
    try {
        $data = Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* -ErrorAction Stop |
            Where-Object { $_.DisplayName } |
            Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
        $file = "$Script:ExportPath\\endpoint_software.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Installed Software -> $file" "OK"
    } catch {
        Write-ExportStatus "Installed Software failed" "FAIL"
    }
}

function Export-RunningServices {
    try {
        $data = Get-Service | 
            Select-Object Name, DisplayName, Status, StartType
        $file = "$Script:ExportPath\\endpoint_services.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Running Services -> $file" "OK"
    } catch {
        Write-ExportStatus "Running Services failed" "FAIL"
    }
}

function Export-ScheduledTasks {
    try {
        $data = Get-ScheduledTask -ErrorAction Stop | 
            Where-Object { $_.State -ne "Disabled" } |
            Select-Object TaskName, TaskPath, State, @{N='Author';E={$_.Principal.UserId}}
        $file = "$Script:ExportPath\\endpoint_scheduled_tasks.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Scheduled Tasks -> $file" "OK"
    } catch {
        Write-ExportStatus "Scheduled Tasks failed" "FAIL"
    }
}

# --- SERVER ---
function Export-ServerFeatures {
    try {
        $data = Get-WindowsFeature -ErrorAction Stop | 
            Where-Object { $_.Installed } |
            Select-Object Name, DisplayName, FeatureType
        $file = "$Script:ExportPath\\server_features.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Server Features -> $file" "OK"
    } catch {
        Write-ExportStatus "Server Features - Not a Windows Server or feature not available" "SKIP"
    }
}

function Export-WindowsUpdates {
    try {
        $Session = New-Object -ComObject Microsoft.Update.Session
        $Searcher = $Session.CreateUpdateSearcher()
        $History = $Searcher.QueryHistory(0, 50)
        $data = $History | Select-Object Title, @{N='Date';E={$_.Date}}, 
                                         @{N='Status';E={switch($_.ResultCode){1{"InProgress"};2{"Succeeded"};3{"SucceededWithErrors"};4{"Failed"};5{"Aborted"}}}}
        $file = "$Script:ExportPath\\server_updates.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Windows Updates (last 50) -> $file" "OK"
    } catch {
        Write-ExportStatus "Windows Updates failed" "FAIL"
    }
}

function Export-IISConfig {
    try {
        Import-Module WebAdministration -ErrorAction Stop
        $data = Get-Website -ErrorAction Stop | 
            Select-Object Name, State, PhysicalPath, @{N='Bindings';E={$_.Bindings.Collection.bindingInformation -join "; "}}
        $file = "$Script:ExportPath\\server_iis.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "IIS Configuration -> $file" "OK"
    } catch {
        Write-ExportStatus "IIS - Not installed or WebAdministration module not available" "SKIP"
    }
}

# --- DATA PROTECTION ---
function Export-BitLocker {
    try {
        $data = Get-BitLockerVolume -ErrorAction Stop | 
            Select-Object MountPoint, VolumeStatus, EncryptionMethod, ProtectionStatus, LockStatus
        $file = "$Script:ExportPath\\data_bitlocker.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "BitLocker Status -> $file" "OK"
    } catch {
        Write-ExportStatus "BitLocker - Module not available or requires elevation" "SKIP"
    }
}

function Export-SharedFolders {
    try {
        $data = Get-SmbShare -ErrorAction Stop | 
            Where-Object { $_.Name -notlike "*$" } |
            Select-Object Name, Path, Description, CurrentUsers
        $file = "$Script:ExportPath\\data_shares.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Shared Folders -> $file" "OK"
    } catch {
        Write-ExportStatus "Shared Folders failed" "FAIL"
    }
}

# --- IAM ---
function Export-LocalAdmins {
    try {
        $data = Get-LocalGroupMember -Group "Administrators" -ErrorAction Stop |
            Select-Object Name, ObjectClass, PrincipalSource
        $file = "$Script:ExportPath\\iam_local_admins.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Local Administrators -> $file" "OK"
    } catch {
        Write-ExportStatus "Local Administrators - LocalAccounts module not available" "SKIP"
    }
}

function Export-LocalUsers {
    try {
        $data = Get-LocalUser -ErrorAction Stop |
            Select-Object Name, Enabled, PasswordRequired, PasswordLastSet, LastLogon
        $file = "$Script:ExportPath\\iam_local_users.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Local Users -> $file" "OK"
    } catch {
        Write-ExportStatus "Local Users failed" "FAIL"
    }
}

function Export-PasswordPolicy {
    try {
        $policy = net accounts 2>&1
        $file = "$Script:ExportPath\\iam_password_policy.txt"
        $policy | Out-File $file
        $Script:ExportedFiles += $file
        Write-ExportStatus "Password Policy -> $file" "OK"
    } catch {
        Write-ExportStatus "Password Policy failed" "FAIL"
    }
}

# --- MONITORING ---
function Export-AuditPolicy {
    try {
        $file = "$Script:ExportPath\\monitoring_audit_policy.csv"
        $auditData = auditpol /get /category:* /r 2>&1 | ConvertFrom-Csv
        $auditData | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Audit Policy -> $file" "OK"
    } catch {
        Write-ExportStatus "Audit Policy failed" "FAIL"
    }
}

function Export-EventLogConfig {
    try {
        $data = Get-WinEvent -ListLog Security, System, Application -ErrorAction Stop |
            Select-Object LogName, MaximumSizeInBytes, RecordCount, IsEnabled, LogMode
        $file = "$Script:ExportPath\\monitoring_eventlog_config.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Event Log Configuration -> $file" "OK"
    } catch {
        Write-ExportStatus "Event Log Configuration failed" "FAIL"
    }
}

function Export-RecentSecurityEvents {
    try {
        $data = Get-WinEvent -LogName Security -MaxEvents 100 -ErrorAction Stop |
            Select-Object TimeCreated, Id, LevelDisplayName, Message
        $file = "$Script:ExportPath\\monitoring_security_events.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Recent Security Events (100) -> $file" "OK"
    } catch {
        Write-ExportStatus "Security Events - Access denied or log not available" "SKIP"
    }
}

# ============================================================================
# BULK EXPORT FUNCTIONS
# ============================================================================
function Export-AllAD {
    Write-Host ""
    Write-Host "  Exporting Active Directory data..." -ForegroundColor Cyan
    Export-DomainAdmins
    Export-ServiceAccounts
    Export-GPOs
    Export-PrivilegedGroups
    Export-StaleAccounts
}

function Export-AllNetwork {
    Write-Host ""
    Write-Host "  Exporting Network data..." -ForegroundColor Cyan
    Export-FirewallRules
    Export-NetworkConfig
    Export-DNSConfig
    Export-OpenPorts
}

function Export-AllEndpoint {
    Write-Host ""
    Write-Host "  Exporting Endpoint data..." -ForegroundColor Cyan
    Export-DefenderStatus
    Export-InstalledSoftware
    Export-RunningServices
    Export-ScheduledTasks
}

function Export-AllServer {
    Write-Host ""
    Write-Host "  Exporting Server data..." -ForegroundColor Cyan
    Export-ServerFeatures
    Export-WindowsUpdates
    Export-IISConfig
}

function Export-AllDataProtection {
    Write-Host ""
    Write-Host "  Exporting Data Protection info..." -ForegroundColor Cyan
    Export-BitLocker
    Export-SharedFolders
}

function Export-AllIAM {
    Write-Host ""
    Write-Host "  Exporting IAM data..." -ForegroundColor Cyan
    Export-LocalAdmins
    Export-LocalUsers
    Export-PasswordPolicy
}

function Export-AllMonitoring {
    Write-Host ""
    Write-Host "  Exporting Monitoring data..." -ForegroundColor Cyan
    Export-AuditPolicy
    Export-EventLogConfig
    Export-RecentSecurityEvents
}

function Export-Everything {
    Write-Host ""
    Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  EXPORTING ALL CATEGORIES" -ForegroundColor Cyan
    Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Export-AllAD
    Export-AllNetwork
    Export-AllEndpoint
    Export-AllServer
    Export-AllDataProtection
    Export-AllIAM
    Export-AllMonitoring
    Show-ExportSummary
}

function Show-ExportSummary {
    Write-Host ""
    Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  EXPORT COMPLETE" -ForegroundColor Green
    Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Files exported: $($Script:ExportedFiles.Count)" -ForegroundColor White
    Write-Host "  Location: $Script:ExportPath" -ForegroundColor White
    Write-Host ""
    Write-Host "  Upload these CSV files to SOPRA for security assessment." -ForegroundColor Cyan
    Write-Host ""
}

function Show-ExportedFiles {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            EXPORTED FILES                                   │" -ForegroundColor Cyan
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
    
    if ($Script:ExportedFiles.Count -eq 0) {
        Write-Host "  No files exported yet." -ForegroundColor Yellow
    } else {
        foreach ($file in $Script:ExportedFiles) {
            $fileName = Split-Path $file -Leaf
            Write-Host "  - $fileName" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "  Location: $Script:ExportPath" -ForegroundColor Cyan
    }
    Write-Host ""
}

# ============================================================================
# MENU HANDLERS
# ============================================================================
function Handle-ADMenu {
    do {
        Show-ADMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-DomainAdmins }
            "2" { Export-ServiceAccounts }
            "3" { Export-GPOs }
            "4" { Export-PrivilegedGroups }
            "5" { Export-StaleAccounts }
            "A" { Export-AllAD }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-NetworkMenu {
    do {
        Show-NetworkMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-FirewallRules }
            "2" { Export-NetworkConfig }
            "3" { Export-DNSConfig }
            "4" { Export-OpenPorts }
            "A" { Export-AllNetwork }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-EndpointMenu {
    do {
        Show-EndpointMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-DefenderStatus }
            "2" { Export-InstalledSoftware }
            "3" { Export-RunningServices }
            "4" { Export-ScheduledTasks }
            "A" { Export-AllEndpoint }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-ServerMenu {
    do {
        Show-ServerMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-ServerFeatures }
            "2" { Export-WindowsUpdates }
            "3" { Export-IISConfig }
            "A" { Export-AllServer }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-DataProtectionMenu {
    do {
        Show-DataProtectionMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-BitLocker }
            "2" { Export-SharedFolders }
            "A" { Export-AllDataProtection }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-IAMMenu {
    do {
        Show-IAMMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-LocalAdmins }
            "2" { Export-LocalUsers }
            "3" { Export-PasswordPolicy }
            "A" { Export-AllIAM }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-MonitoringMenu {
    do {
        Show-MonitoringMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-AuditPolicy }
            "2" { Export-EventLogConfig }
            "3" { Export-RecentSecurityEvents }
            "A" { Export-AllMonitoring }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

# ============================================================================
# MAIN
# ============================================================================
Initialize-ExportDirectory

if ($ExportAll) {
    Show-Banner
    Export-Everything
    exit
}

do {
    Show-Banner
    Show-MainMenu
    $choice = Read-Host "  Select option"
    
    switch ($choice.ToUpper()) {
        "1" { Handle-ADMenu }
        "2" { Handle-NetworkMenu }
        "3" { Handle-EndpointMenu }
        "4" { Handle-ServerMenu }
        "5" { Handle-DataProtectionMenu }
        "6" { Handle-IAMMenu }
        "7" { Handle-MonitoringMenu }
        "A" { Export-Everything; Read-Host "  Press Enter to continue" }
        "V" { Show-ExportedFiles; Read-Host "  Press Enter to continue" }
        "Q" { 
            Write-Host ""
            Write-Host "  Thank you for using SOPRA Export Tool!" -ForegroundColor Cyan
            Write-Host ""
            exit 
        }
    }
} while ($true)
'''
    
    return script


def process_csv_assessment(uploaded_files, selected_categories, include_remediation):
    """Process uploaded CSV files and run assessment"""
    import pandas as pd
    
    all_findings = []
    
    with st.spinner("Processing CSV files..."):
        for uploaded_file in uploaded_files:
            try:
                # Reset file position to beginning (important after preview)
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file)
                
                # Process each row as a finding
                for _, row in df.iterrows():
                    finding = {
                        "control_id": row.get('control_id', 'UNKNOWN'),
                        "control_name": row.get('control_name', 'Unknown Control'),
                        "category": row.get('category', 'Uncategorized'),
                        "family": row.get('family', 'Unknown'),
                        "status": row.get('status', 'Not Assessed'),
                        "severity": row.get('severity', None) if row.get('status') == 'Failed' else None,
                        "evidence": row.get('evidence', ''),
                        "notes": row.get('notes', ''),
                        "assessed_by": row.get('assessed_by', 'CSV Import'),
                        "assessment_date": row.get('assessment_date', datetime.now().isoformat())
                    }
                    all_findings.append(finding)
                    
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
    
    if all_findings:
        # Store results
        st.session_state.opra_assessment_results = {
            "timestamp": datetime.now().isoformat(),
            "findings": all_findings,
            "categories_assessed": selected_categories,
            "include_remediation": include_remediation,
            "source": "CSV Import"
        }
        
        st.success(f"✅ Assessment complete! Processed {len(all_findings)} controls from {len(uploaded_files)} file(s).")
        st.balloons()
        
        # Show quick summary
        passed = len([f for f in all_findings if f['status'] == 'Passed'])
        failed = len([f for f in all_findings if f['status'] == 'Failed'])
        not_assessed = len([f for f in all_findings if f['status'] == 'Not Assessed'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Passed", passed, delta=None)
        with col2:
            st.metric("Failed", failed, delta=None, delta_color="inverse")
        with col3:
            st.metric("Not Assessed", not_assessed)
        
        if st.button("📊 View Full Report", type="primary", use_container_width=True):
            st.session_state.opra_active_tab = "Reports"
            st.rerun()
    else:
        st.warning("⚠️ No valid assessment data found in the uploaded files.")

def run_manual_assessment(categories, include_remediation):
    """Run a manual assessment questionnaire with detailed control information"""
    findings = []
    
    st.markdown("---")
    st.markdown("### 📝 Assessment Questionnaire")
    
    for cat_key in categories:
        category = OPRA_CATEGORIES[cat_key]
        
        with st.expander(f"{category['icon']} {category['name']}", expanded=False):
            for control_ref in category['controls']:
                # Get detailed control from sopra_controls.py
                detailed_control = get_control_by_id(control_ref['id'])
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{control_ref['id']}**: {control_ref['name']}")
                    st.caption(f"Family: {control_ref['family']}")
                    
                    # Show detailed info if available
                    if detailed_control:
                        with st.popover("ℹ️ Details"):
                            st.markdown(f"**Description:** {detailed_control.description}")
                            st.markdown("**Check Procedure:**")
                            st.code(detailed_control.check_procedure.strip(), language=None)
                            st.markdown(f"**Expected Result:** {detailed_control.expected_result}")
                            if detailed_control.nist_mapping:
                                st.markdown(f"**NIST Mapping:** {', '.join(detailed_control.nist_mapping)}")
                            if detailed_control.cis_mapping:
                                st.markdown(f"**CIS Mapping:** {detailed_control.cis_mapping}")
                
                with col2:
                    # Default severity from detailed control
                    default_sev = detailed_control.default_severity.value if detailed_control else "Medium"
                    
                    status = st.selectbox(
                        "Status",
                        ["Not Assessed", "Passed", "Failed", "N/A"],
                        key=f"status_{control_ref['id']}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    if status == "Failed":
                        severity_options = ["Low", "Medium", "High", "Critical"]
                        default_idx = severity_options.index(default_sev) if default_sev in severity_options else 1
                        severity = st.selectbox(
                            "Severity",
                            severity_options,
                            index=default_idx,
                            key=f"severity_{control_ref['id']}",
                            label_visibility="collapsed"
                        )
                    else:
                        severity = "N/A"
                        st.text("N/A")
                
                findings.append({
                    "control_id": control['id'],
                    "control_name": control['name'],
                    "category": category['name'],
                    "family": control['family'],
                    "status": status,
                    "severity": severity if status == "Failed" else None
                })
    
    if st.button("✅ Complete Assessment", type="primary", use_container_width=True):
        st.session_state.opra_assessment_results = {
            "timestamp": datetime.now().isoformat(),
            "findings": findings,
            "categories_assessed": categories,
            "include_remediation": include_remediation
        }
        st.success("🎉 Assessment completed! View results in the Reports tab.")
        st.balloons()

def render_reports_page():
    """Render the reports page with enhanced visualizations"""
    st.markdown("## 📊 Assessment Reports")
    
    if not st.session_state.opra_assessment_results:
        st.warning("⚠️ No assessment data available. Please run an assessment first.")
        if st.button("▶️ Go to Assessment"):
            st.session_state.opra_active_tab = "Assessment"
            st.rerun()
        return
    
    results = st.session_state.opra_assessment_results
    findings = results.get("findings", [])
    
    # Summary metrics
    total = len(findings)
    passed = len([f for f in findings if f["status"] == "Passed"])
    failed = len([f for f in findings if f["status"] == "Failed"])
    not_assessed = len([f for f in findings if f["status"] == "Not Assessed"])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Controls", str(total), "#00d9ff")
    with col2:
        render_metric_card("Passed", str(passed), "#00d9ff")
    with col3:
        render_metric_card("Failed", str(failed), "#e94560")
    with col4:
        score = calculate_risk_score(findings)
        render_metric_card("Risk Score", f"{score}%", get_risk_color(score))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Enhanced Charts Row 1 ──
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Control Status Distribution")
        fig_donut = go.Figure(data=[go.Pie(
            labels=["Passed", "Failed", "Not Assessed"],
            values=[passed, failed, not_assessed],
            hole=0.55,
            marker_colors=["#00d9ff", "#e94560", "#3a3a5c"],
            textinfo="label+percent",
            textfont=dict(size=13, color="#f5f5f5"),
            pull=[0.02, 0.06, 0.02]
        )])
        fig_donut.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f5f5f5',
            legend=dict(font=dict(color="#f5f5f5", size=12)),
            height=350,
            margin=dict(t=20, b=20, l=20, r=20),
            annotations=[dict(
                text=f"<b>{int(passed/(total or 1)*100)}%</b><br>Pass Rate",
                x=0.5, y=0.5, font_size=16, font_color="#00d9ff", showarrow=False
            )]
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with col2:
        st.markdown("### Findings by Category")
        cat_passed = {}
        cat_failed = {}
        for f in findings:
            cat = f.get("category", "Unknown")
            if f["status"] == "Passed":
                cat_passed[cat] = cat_passed.get(cat, 0) + 1
            elif f["status"] == "Failed":
                cat_failed[cat] = cat_failed.get(cat, 0) + 1
        
        all_cats = sorted(set(list(cat_passed.keys()) + list(cat_failed.keys())))
        if all_cats:
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(name="Passed", x=all_cats, y=[cat_passed.get(c, 0) for c in all_cats], marker_color="#00d9ff", opacity=0.85))
            fig_bar.add_trace(go.Bar(name="Failed", x=all_cats, y=[cat_failed.get(c, 0) for c in all_cats], marker_color="#e94560", opacity=0.85))
            fig_bar.update_layout(
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#f5f5f5',
                legend=dict(font=dict(color="#f5f5f5")),
                xaxis=dict(tickangle=-25, tickfont=dict(color="#f5f5f5", size=10), gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(title="Controls", tickfont=dict(color="#f5f5f5"), gridcolor='rgba(255,255,255,0.08)'),
                height=350,
                margin=dict(t=20, b=60, l=40, r=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No category data to display")
    
    # ── Enhanced Charts Row 2 ──
    chart2_col1, chart2_col2 = st.columns(2)
    
    with chart2_col1:
        st.markdown("### 🎯 Severity Distribution")
        sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for f in findings:
            if f["status"] == "Failed" and f.get("severity"):
                sev = f["severity"]
                if sev in sev_counts:
                    sev_counts[sev] += 1
        
        if sum(sev_counts.values()) > 0:
            colors = ["#e94560", "#ff6b6b", "#ffc107", "#00d9ff"]
            fig_sev = go.Figure(data=[go.Bar(
                x=list(sev_counts.keys()),
                y=list(sev_counts.values()),
                marker_color=colors,
                text=list(sev_counts.values()),
                textposition='auto',
                textfont=dict(color="#ffffff", size=14)
            )])
            fig_sev.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#f5f5f5',
                xaxis=dict(tickfont=dict(color="#f5f5f5", size=12)),
                yaxis=dict(tickfont=dict(color="#f5f5f5"), gridcolor='rgba(255,255,255,0.08)', title="Count"),
                height=300,
                margin=dict(t=20, b=40, l=40, r=20)
            )
            st.plotly_chart(fig_sev, use_container_width=True)
        else:
            st.success("🎉 No failed controls to display!")
    
    with chart2_col2:
        st.markdown("### 🔒 Risk Score Gauge")
        score = calculate_risk_score(findings)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number=dict(suffix="%", font=dict(color="#00d9ff", size=36)),
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor="#f5f5f5", tickfont=dict(color="#f5f5f5")),
                bar=dict(color="#00d9ff"),
                bgcolor="rgba(0,0,0,0)",
                steps=[
                    dict(range=[0, 40], color="rgba(233, 69, 96, 0.3)"),
                    dict(range=[40, 60], color="rgba(255, 107, 107, 0.3)"),
                    dict(range=[60, 80], color="rgba(255, 193, 7, 0.3)"),
                    dict(range=[80, 100], color="rgba(0, 217, 255, 0.3)")
                ],
                threshold=dict(line=dict(color="#ffffff", width=3), thickness=0.8, value=score)
            )
        ))
        fig_gauge.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f5f5f5',
            height=300,
            margin=dict(t=30, b=20, l=40, r=40)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed findings table
    st.markdown("### 📋 Detailed Findings")
    
    failed_findings = [f for f in findings if f["status"] == "Failed"]
    if failed_findings:
        df = pd.DataFrame(failed_findings)
        df = df[["control_id", "control_name", "category", "severity", "family"]]
        df.columns = ["Control ID", "Control Name", "Category", "Severity", "Family"]
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Remediation guidance section
        if results.get("include_remediation", True):
            st.markdown("### 🔧 Remediation Guidance")
            
            # Group by severity for prioritization
            severity_order = ["Critical", "High", "Medium", "Low"]
            for sev in severity_order:
                sev_findings = [f for f in failed_findings if f.get("severity") == sev]
                if sev_findings:
                    sev_color = {"Critical": "#e94560", "High": "#ff6b6b", "Medium": "#ffc107", "Low": "#00d9ff"}.get(sev, "#c0c0c0")
                    st.markdown(f"#### <span style='color: {sev_color};'>🔴 {sev} Severity ({len(sev_findings)} findings)</span>", unsafe_allow_html=True)
                    
                    for finding in sev_findings:
                        control = get_control_by_id(finding["control_id"])
                        if control:
                            with st.expander(f"**{finding['control_id']}**: {finding['control_name']}"):
                                st.markdown(f"**Category:** {finding['category']}")
                                st.markdown(f"**Expected Result:** {control.expected_result}")
                                
                                if control.remediation_steps:
                                    st.markdown("**Remediation Steps:**")
                                    for step in control.remediation_steps:
                                        downtime_badge = " ⚠️ *Requires Downtime*" if step.requires_downtime else ""
                                        time_est = f" ({step.estimated_time})" if step.estimated_time else ""
                                        st.markdown(f"{step.step_number}. {step.description}{time_est}{downtime_badge}")
                                        if step.command:
                                            st.code(step.command, language=step.script_type or "powershell")
                                
                                # Generate PowerShell script button
                                ps_script = get_remediation_script(finding["control_id"], "powershell")
                                if ps_script and len(ps_script) > 100:
                                    st.download_button(
                                        label="📥 Download PowerShell Script",
                                        data=ps_script,
                                        file_name=f"remediate_{finding['control_id']}.ps1",
                                        mime="text/plain",
                                        key=f"dl_{finding['control_id']}"
                                    )
                                
                                if control.references:
                                    st.markdown(f"**References:** {', '.join(control.references)}")
    else:
        st.success("🎉 No failed controls found!")
    
    # Export options
    st.markdown("### 📥 Export Reports")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export Executive Summary", use_container_width=True):
            export_executive_summary(results, findings)
    
    with col2:
        if st.button("📊 Export Full Report", use_container_width=True):
            export_full_report(results, findings)
    
    with col3:
        if st.button("📋 Export POA&M", use_container_width=True):
            export_poam(results, findings)


def export_executive_summary(results, findings):
    """Generate and download executive summary"""
    total = len(findings)
    passed = len([f for f in findings if f["status"] == "Passed"])
    failed = len([f for f in findings if f["status"] == "Failed"])
    score = calculate_risk_score(findings)
    
    summary = f"""# SOPRA Executive Summary
## On-Premise Risk Assessment Report

**Assessment Date:** {results.get('timestamp', datetime.now().isoformat())[:10]}
**Generated By:** SOPRA v2.0.0

---

## Assessment Overview

| Metric | Value |
|--------|-------|
| Total Controls Assessed | {total} |
| Controls Passed | {passed} |
| Controls Failed | {failed} |
| Overall Risk Score | {score}% |

---

## Risk Summary

"""
    # Count by severity
    severity_counts = {}
    for f in findings:
        if f["status"] == "Failed":
            sev = f.get("severity", "Unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    for sev in ["Critical", "High", "Medium", "Low"]:
        count = severity_counts.get(sev, 0)
        if count > 0:
            summary += f"- **{sev}:** {count} finding(s)\n"
    
    summary += """
---

## Key Recommendations

"""
    # Top 5 critical/high findings
    critical_high = [f for f in findings if f["status"] == "Failed" and f.get("severity") in ["Critical", "High"]][:5]
    for i, f in enumerate(critical_high, 1):
        summary += f"{i}. **{f['control_id']}**: {f['control_name']} ({f['category']})\n"
    
    summary += """
---

*This report was generated by SOPRA - SAE On-Premise Risk Assessment Tool*
"""
    
    st.download_button(
        label="📥 Download Executive Summary",
        data=summary,
        file_name=f"SOPRA_Executive_Summary_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )
    st.success("✅ Executive summary generated!")


def export_full_report(results, findings):
    """Generate and download full assessment report"""
    report = f"""# SOPRA Full Assessment Report
## On-Premise Risk Assessment

**Assessment Date:** {results.get('timestamp', datetime.now().isoformat())[:10]}
**Generated By:** SOPRA v2.0.0

---

## All Findings

"""
    # Group by category
    categories = {}
    for f in findings:
        cat = f.get("category", "Unknown")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f)
    
    for cat, cat_findings in categories.items():
        report += f"### {cat}\n\n"
        for f in cat_findings:
            status_emoji = {"Passed": "✅", "Failed": "❌", "N/A": "⏭️"}.get(f["status"], "❓")
            report += f"- {status_emoji} **{f['control_id']}**: {f['control_name']}"
            if f["status"] == "Failed":
                report += f" - *{f.get('severity', 'Unknown')} Severity*"
            report += "\n"
        report += "\n"
    
    # Add remediation section for failed controls
    failed = [f for f in findings if f["status"] == "Failed"]
    if failed:
        report += "---\n\n## Remediation Guidance\n\n"
        for f in failed:
            control = get_control_by_id(f["control_id"])
            if control:
                report += f"### {f['control_id']}: {f['control_name']}\n\n"
                report += f"**Severity:** {f.get('severity', 'Unknown')}\n\n"
                report += f"**Expected Result:** {control.expected_result}\n\n"
                
                if control.remediation_steps:
                    report += "**Remediation Steps:**\n\n"
                    for step in control.remediation_steps:
                        report += f"{step.step_number}. {step.description}"
                        if step.estimated_time:
                            report += f" ({step.estimated_time})"
                        if step.requires_downtime:
                            report += " ⚠️ Requires Downtime"
                        report += "\n"
                        if step.command:
                            report += f"\n```{step.script_type or 'powershell'}\n{step.command}\n```\n\n"
                
                report += "\n---\n\n"
    
    report += """
*This report was generated by SOPRA - SAE On-Premise Risk Assessment Tool*
"""
    
    st.download_button(
        label="📥 Download Full Report",
        data=report,
        file_name=f"SOPRA_Full_Report_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )
    st.success("✅ Full report generated!")


def export_poam(results, findings):
    """Generate and download POA&M (Plan of Action & Milestones)"""
    failed = [f for f in findings if f["status"] == "Failed"]
    
    if not failed:
        st.info("No failed controls to include in POA&M")
        return
    
    # Create POA&M in CSV format for easy import
    poam_data = []
    for i, f in enumerate(failed, 1):
        control = get_control_by_id(f["control_id"])
        
        # Calculate estimated completion based on remediation steps
        total_time = ""
        if control and control.remediation_steps:
            total_time = " + ".join([s.estimated_time for s in control.remediation_steps if s.estimated_time])
        
        poam_data.append({
            "POA&M ID": f"SOPRA-{i:03d}",
            "Control ID": f["control_id"],
            "Weakness Name": f["control_name"],
            "Category": f["category"],
            "Severity": f.get("severity", "Unknown"),
            "Status": "Open",
            "Expected Completion": total_time or "TBD",
            "Responsible Party": "TBD",
            "NIST Mapping": ", ".join(control.nist_mapping) if control and control.nist_mapping else "",
            "Notes": control.expected_result if control else ""
        })
    
    df = pd.DataFrame(poam_data)
    csv = df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download POA&M (CSV)",
        data=csv,
        file_name=f"SOPRA_POAM_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    st.success("✅ POA&M generated!")

def render_ai_assistant():
    """Render the AI assistant page powered by AWS Bedrock"""
    st.markdown("## 💬 SOPRA AI Assistant")
    st.markdown("Your on-premise security expert powered by AWS Bedrock 🔒")
    
    # Chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.opra_chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div style="background: #0f3460; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 3px solid #00d9ff;">
                    <strong style="color: #00d9ff;">You:</strong>
                    <p style="color: #f5f5f5; margin: 0.5rem 0 0 0;">{message["content"]}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #16213e; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 3px solid #e94560;">
                    <strong style="color: #e94560;">🤖 SOPRA AI:</strong>
                    <p style="color: #f5f5f5; margin: 0.5rem 0 0 0;">{message["content"]}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Quick action buttons
    st.markdown("### ⚡ Quick Questions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔐 AD Security Best Practices", use_container_width=True):
            add_ai_response("What are the best practices for Active Directory security?")
    
    with col2:
        if st.button("🌐 Network Segmentation Tips", use_container_width=True):
            add_ai_response("How should I implement network segmentation?")
    
    with col3:
        if st.button("💻 Endpoint Hardening Guide", use_container_width=True):
            add_ai_response("What are the key endpoint hardening measures?")
    
    # User input
    user_input = st.chat_input("Ask SOPRA AI about on-premise security...")
    
    if user_input:
        add_ai_response(user_input)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.opra_chat_history = []
        st.rerun()

def add_ai_response(question):
    """Add user question and AI response to chat via AWS Bedrock"""
    st.session_state.opra_chat_history.append({
        "role": "user",
        "content": question
    })
    
    # Build context from assessment data if available
    context = build_assessment_context()
    
    # Build the system prompt for SOPRA AI
    system_prompt = f"""You are SOPRA AI, an expert on-premise security analyst specializing in enterprise infrastructure security.
You help security professionals with:
- Active Directory security and hardening
- Network infrastructure security (firewalls, segmentation, IDS/IPS)
- Endpoint security and hardening (Windows, Linux)
- Server security (databases, web servers, virtualization)
- Physical security controls
- Data protection and encryption
- Identity and access management
- Security monitoring and SIEM

You provide practical, actionable advice with specific commands (PowerShell, Cisco IOS, etc.) when appropriate.
Use markdown formatting for clarity. Be concise but thorough.

{context}"""
    
    # Build messages for Bedrock
    messages = []
    for msg in st.session_state.opra_chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    try:
        with st.spinner("🤔 SOPRA AI is thinking..."):
            response = call_bedrock_ai(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=4096
            )
    except Exception as e:
        # Fallback to local responses if Bedrock fails
        response = generate_fallback_response(question, str(e))
    
    st.session_state.opra_chat_history.append({
        "role": "assistant",
        "content": response
    })
    
    st.rerun()


def build_assessment_context():
    """Build context from current assessment data"""
    if not st.session_state.opra_assessment_results:
        return "No assessment data available yet."
    
    results = st.session_state.opra_assessment_results
    findings = results.get("findings", [])
    
    total = len(findings)
    passed = len([f for f in findings if f["status"] == "Passed"])
    failed = len([f for f in findings if f["status"] == "Failed"])
    score = calculate_risk_score(findings)
    
    context = f"""Current Assessment Context:
- Total Controls: {total}
- Passed: {passed}
- Failed: {failed}
- Risk Score: {score}%

Failed Controls (top issues):
"""
    failed_findings = [f for f in findings if f["status"] == "Failed"][:10]
    for f in failed_findings:
        context += f"- {f['control_id']}: {f['control_name']} ({f.get('severity', 'Unknown')} severity)\n"
    
    return context


def generate_fallback_response(question, error_msg=""):
    """Generate fallback response when Bedrock is unavailable"""
    # Check if it's a Bedrock configuration issue
    if "Bedrock" in error_msg or "credentials" in error_msg.lower():
        bedrock_help = f"""
⚠️ **AWS Bedrock Not Available**

{error_msg}

In the meantime, here's some general guidance:

"""
    else:
        bedrock_help = ""
    
    # Keyword-based fallback responses
    fallback_responses = {
        "active directory": """**Active Directory Security Best Practices:**

1. **Privileged Access Management**: Implement a tiered admin model (Tier 0/1/2) to protect domain admin credentials
2. **Password Policy**: Enforce 14+ character passwords with complexity requirements
3. **Service Accounts**: Use Group Managed Service Accounts (gMSA) where possible
4. **AdminSDHolder**: Monitor and protect this critical container
5. **LDAP Signing**: Require LDAP signing and channel binding
6. **Kerberos**: Enable AES encryption, disable RC4
7. **Audit Policies**: Enable advanced audit policies for logon events and directory service access
8. **Protected Users Group**: Add sensitive accounts to this security group
9. **LAPS**: Deploy Local Administrator Password Solution
10. **Regular Reviews**: Conduct quarterly access reviews for privileged groups""",
        
        "network segmentation": """**Network Segmentation Implementation Guide:**

1. **Identify Critical Assets**: Map your crown jewels and their data flows
2. **Define Security Zones**: Create zones based on trust levels (DMZ, Internal, Restricted, PCI, etc.)
3. **Implement VLANs**: Use 802.1Q VLANs to logically separate traffic
4. **Deploy Firewalls**: Place next-gen firewalls between zones with explicit allow rules
5. **Microsegmentation**: Consider software-defined segmentation for east-west traffic
6. **Zero Trust**: Implement "never trust, always verify" between segments
7. **Jump Servers**: Use bastion hosts for administrative access to secure zones
8. **Network Access Control**: Deploy 802.1X for port-based authentication
9. **Monitor Traffic**: Implement IDS/IPS at segment boundaries
10. **Regular Testing**: Conduct periodic penetration tests to validate segmentation""",
        
        "endpoint hardening": """**Endpoint Hardening Checklist:**

1. **OS Hardening**: Apply CIS benchmarks or DISA STIGs
2. **Patch Management**: Automated patching within 14 days for critical vulnerabilities
3. **EDR/XDR**: Deploy endpoint detection and response on all endpoints
4. **Application Control**: Implement allowlisting (AppLocker, WDAC)
5. **Local Admin Rights**: Remove local admin rights, use PAM for elevation
6. **Disk Encryption**: Enable BitLocker with TPM + PIN
7. **USB Controls**: Restrict removable media via GPO
8. **Host Firewall**: Enable Windows Defender Firewall with strict rules
9. **PowerShell**: Enable constrained language mode and script block logging
10. **Credential Guard**: Enable Credential Guard on Windows 10/11 Enterprise"""
    }
    
    question_lower = question.lower()
    
    if "active directory" in question_lower or "ad " in question_lower:
        return bedrock_help + fallback_responses["active directory"]
    elif "network" in question_lower or "segment" in question_lower:
        return bedrock_help + fallback_responses["network segmentation"]
    elif "endpoint" in question_lower or "hardening" in question_lower:
        return bedrock_help + fallback_responses["endpoint hardening"]
    else:
        return bedrock_help + f"""I can help you with on-premise security topics including:

- **Active Directory Security**: Domain controller hardening, GPO security, privileged access
- **Network Infrastructure**: Segmentation, firewall rules, IDS/IPS configuration
- **Endpoint Security**: Hardening, patching, EDR deployment
- **Server Security**: Windows/Linux hardening, database security
- **Physical Security**: Access controls, surveillance, environmental
- **Data Protection**: Encryption, DLP, backup strategies
- **Identity Management**: MFA, PAM, access reviews
- **Monitoring**: SIEM, logging, threat detection

Please ask a more specific question about any of these areas!"""

def render_settings_page():
    """Render the settings page"""
    st.markdown("## ⚙️ SOPRA Settings")
    
    with st.expander("🎨 Appearance", expanded=True):
        st.selectbox("Theme", ["Dark (Default)", "Light", "High Contrast"])
        st.checkbox("Show control families in reports", value=True)
        st.checkbox("Enable animations", value=True)
    
    with st.expander("🔗 Integrations", expanded=False):
        st.markdown("**Vulnerability Scanners**")
        st.text_input("Nessus API URL")
        st.text_input("Nessus API Key", type="password")
        
        st.markdown("**SIEM Integration**")
        st.text_input("Splunk URL")
        st.text_input("Splunk Token", type="password")
    
    with st.expander("🤖 AI Configuration", expanded=False):
        st.markdown("**AWS Bedrock Settings**")
        st.text_input("AWS Region", value="us-east-1")
        st.selectbox("AI Model", ["NVIDIA Nemotron Nano 12B", "Amazon Titan", "Llama 3", "Mistral"])
        st.slider("Response Temperature", 0.0, 1.0, 0.7)
    
    with st.expander("📊 Report Settings", expanded=False):
        st.text_input("Organization Name", value="Your Organization")
        st.text_area("Report Header Text")
        st.file_uploader("Organization Logo")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    import os
    import base64
    
    # Sidebar navigation
    with st.sidebar:
        # Try to show logo in sidebar
        import base64
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "SOPRA_logo_dark.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "OPRA_logo_dark.png")
        
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_data = base64.b64encode(f.read()).decode()
            st.markdown(f"""
            <div style="text-align: center; padding: 1.5rem; background: radial-gradient(ellipse at center, rgba(10, 22, 40, 0.95) 0%, rgba(15, 26, 46, 0.7) 50%, rgba(0, 0, 0, 0.9) 100%); border-radius: 20px; margin-bottom: 1rem; border: 1px solid rgba(0, 217, 255, 0.15);">
                <img src="data:image/png;base64,{logo_data}" style="display: block; max-width: 180px; margin: 0 auto; filter: drop-shadow(0 0 20px rgba(0, 217, 255, 0.4));">
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <h2 style="color: #00d9ff; margin: 0;">🛡️ SOPRA</h2>
                <p style="color: #f0f0f0; font-size: 0.8rem;">SAE On-Premise Risk Assessment</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation buttons
        nav_options = ["Dashboard", "Assessment", "Reports", "AI Assistant", "Settings"]
        
        for option in nav_options:
            icon = {"Dashboard": "📊", "Assessment": "🔍", "Reports": "📋", 
                   "AI Assistant": "💬", "Settings": "⚙️"}.get(option, "📌")
            
            if st.button(f"{icon} {option}", use_container_width=True, 
                        type="primary" if st.session_state.opra_active_tab == option else "secondary"):
                st.session_state.opra_active_tab = option
                st.rerun()
        
        st.markdown("---")
        
        # Version info
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <p style="color: #888; font-size: 0.75rem;">SOPRA v2.0.0</p>
            <p style="color: #666; font-size: 0.65rem;">SAE On-Premise Risk Assessment</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content area
    if st.session_state.opra_active_tab == "Dashboard":
        render_dashboard()
    elif st.session_state.opra_active_tab == "Category Details":
        render_category_details()
    elif st.session_state.opra_active_tab == "Metric Details":
        render_metric_details()
    elif st.session_state.opra_active_tab == "Assessment":
        render_assessment_page()
    elif st.session_state.opra_active_tab == "Reports":
        render_reports_page()
    elif st.session_state.opra_active_tab == "AI Assistant":
        render_ai_assistant()
    elif st.session_state.opra_active_tab == "Settings":
        render_settings_page()

if __name__ == "__main__":
    main()
