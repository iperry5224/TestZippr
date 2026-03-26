"""
NIST 800-53 Rev 5 Comprehensive Assessment - Streamlit UI
==========================================================
Full cloud security controls assessment dashboard covering
all 13 control families from NIST 800-53 Revision 5.
"""

import streamlit as st
import pandas as pd
import json
import time
import os
import boto3
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pathlib import Path
from botocore.exceptions import ClientError

from nist_800_53_rev5_full import NIST80053Rev5Assessor, ControlResult, ControlStatus

# S3 bucket for storing assessment results
S3_BUCKET_NAME = "saegrctest1"
S3_PREFIX = "nist-assessments/"

# Local folder for storing assessment reports (on Desktop)
LOCAL_REPORTS_DIR = Path("C:/Users/iperr/OneDrive/Desktop/NIST_Assessment_Reports")

# Certificate locations - detect if running in WSL or Windows
import platform
import subprocess
if 'microsoft' in platform.uname().release.lower() or os.path.exists('/mnt/c'):
    CERT_DIR = Path("/mnt/c/Users/iperr/TestZippr/ssl_certs")
else:
    CERT_DIR = Path("C:/Users/iperr/TestZippr/ssl_certs")
CERT_FILE = CERT_DIR / "streamlit.crt"
KEY_FILE = CERT_DIR / "streamlit.key"

# Page configuration
st.set_page_config(
    page_title="NIST 800-53 Rev 5 Assessment",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Light grey theme for better readability
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
</style>
""", unsafe_allow_html=True)


def get_status_emoji(status: ControlStatus) -> str:
    return {
        ControlStatus.PASS: "✅",
        ControlStatus.FAIL: "❌",
        ControlStatus.WARNING: "⚠️",
        ControlStatus.ERROR: "🔴",
        ControlStatus.NOT_APPLICABLE: "➖"
    }.get(status, "❓")


def get_status_class(status: ControlStatus) -> str:
    return {
        ControlStatus.PASS: "pass",
        ControlStatus.FAIL: "fail",
        ControlStatus.WARNING: "warning",
        ControlStatus.ERROR: "error",
    }.get(status, "")


def render_header():
    st.markdown("""
    <div class="main-header">
        <h1>🛡️ Security Architecture and Evaluation's NIST 800-53 Security Controls Assessment <span class="rev-badge">Rev 5</span></h1>
        <p>Comprehensive cloud security assessment covering 13 control families and 40+ automated checks</p>
    </div>
    """, unsafe_allow_html=True)


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


def render_certificate_viewer():
    """Render the certificate details section."""
    st.markdown("## 🔐 SSL/TLS Certificate Details")
    
    if not CERT_FILE.exists():
        st.warning("⚠️ No certificate found. Run `bash generate_ssl_certs.sh` to create certificates.")
        return
    
    # Get certificate info
    try:
        cert_stat = CERT_FILE.stat()
        key_stat = KEY_FILE.stat() if KEY_FILE.exists() else None
        
        # Basic info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value info">📜</div>
                <div class="metric-label">Certificate</div>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"{CERT_FILE.name} ({cert_stat.st_size} bytes)")
        
        with col2:
            st.markdown("""
            <div class="metric-box">
                <div class="metric-value info">🔑</div>
                <div class="metric-label">Private Key</div>
            </div>
            """, unsafe_allow_html=True)
            if key_stat:
                st.caption(f"{KEY_FILE.name} ({key_stat.st_size} bytes)")
            else:
                st.caption("Not found")
        
        with col3:
            # Check validity
            end_date = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-enddate"])
            if "notAfter=" in end_date:
                date_str = end_date.split("=")[1].strip()
                try:
                    expiry = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
                    days_remaining = (expiry - datetime.now()).days
                    if days_remaining < 0:
                        status_color = "fail"
                        status_text = f"EXPIRED"
                    elif days_remaining < 30:
                        status_color = "warning"
                        status_text = f"{days_remaining} days"
                    else:
                        status_color = "pass"
                        status_text = f"{days_remaining} days"
                except:
                    status_color = "info"
                    status_text = "Unknown"
            else:
                status_color = "info"
                status_text = "Unknown"
            
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value {status_color}">{status_text}</div>
                <div class="metric-label">Validity</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Certificate details in expanders
        with st.expander("📋 Subject & Issuer", expanded=True):
            subject = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-subject"])
            issuer = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-issuer"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Subject:**")
                st.code(subject.strip().replace("subject=", ""))
            with col2:
                st.markdown("**Issuer:**")
                st.code(issuer.strip().replace("issuer=", ""))
        
        with st.expander("📅 Validity Period"):
            dates = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-dates"])
            for line in dates.strip().split('\n'):
                if "notBefore" in line:
                    st.success(f"**Valid From:** {line.split('=')[1]}")
                elif "notAfter" in line:
                    st.info(f"**Valid Until:** {line.split('=')[1]}")
        
        with st.expander("🔏 Fingerprints"):
            sha256 = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-fingerprint", "-sha256"])
            sha1 = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-fingerprint", "-sha1"])
            
            st.markdown("**SHA-256:**")
            st.code(sha256.strip().split("=")[-1] if "=" in sha256 else sha256)
            
            st.markdown("**SHA-1:**")
            st.code(sha1.strip().split("=")[-1] if "=" in sha1 else sha1)
        
        with st.expander("🔐 Key Information"):
            serial = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-serial"])
            st.markdown(f"**Serial Number:** `{serial.strip().split('=')[-1] if '=' in serial else serial}`")
            
            # Signature algorithm
            text_output = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-text"])
            for line in text_output.split('\n'):
                if "Signature Algorithm:" in line:
                    st.markdown(f"**Signature Algorithm:** `{line.strip().split(':')[-1].strip()}`")
                    break
                if "Public-Key:" in line:
                    st.markdown(f"**Public Key:** `{line.strip()}`")
            
            # Key verification
            if KEY_FILE.exists():
                cert_modulus = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-modulus"])
                key_modulus = run_openssl_command(["rsa", "-in", str(KEY_FILE), "-noout", "-modulus"])
                
                if cert_modulus.strip() == key_modulus.strip():
                    st.success("✅ Certificate and private key MATCH")
                else:
                    st.error("❌ Certificate and private key DO NOT MATCH")
        
        with st.expander("📜 Certificate Purpose"):
            purpose = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-purpose"])
            purposes = []
            for line in purpose.strip().split('\n'):
                if ": Yes" in line:
                    purposes.append(f"✅ {line.split(':')[0].strip()}")
                elif ": No" in line:
                    purposes.append(f"❌ {line.split(':')[0].strip()}")
            
            col1, col2 = st.columns(2)
            mid = len(purposes) // 2
            with col1:
                for p in purposes[:mid]:
                    st.markdown(p)
            with col2:
                for p in purposes[mid:]:
                    st.markdown(p)
        
        with st.expander("📄 Raw Certificate (PEM)"):
            with open(CERT_FILE, 'r') as f:
                cert_content = f.read()
            st.code(cert_content, language="text")
        
        st.markdown("---")
        st.markdown(f"📁 **Certificate Location:** `{CERT_DIR}`")
        
    except Exception as e:
        st.error(f"Error reading certificate: {e}")


def render_sidebar() -> tuple:
    with st.sidebar:
        st.markdown("### ⚙️ Assessment Configuration")
        
        # Region selection
        regions = [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1",
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
        ]
        region = st.selectbox("🌍 AWS Region", options=["Default"] + regions)
        
        st.markdown("---")
        st.markdown("### 📋 Control Families")
        st.markdown("*Select one or more families to assess*")
        
        # Control family descriptions with control counts
        families = {
            'AC': ('🔐 Access Control', 'Account management, least privilege', 7),
            'AU': ('📝 Audit & Accountability', 'Logging, monitoring, retention', 6),
            'CA': ('✅ Assessment & Authorization', 'Security Hub, Config rules', 2),
            'CM': ('⚙️ Configuration Management', 'Baselines, inventory', 3),
            'CP': ('💾 Contingency Planning', 'Backup, disaster recovery', 2),
            'IA': ('🎫 Identification & Auth', 'MFA, password policies', 2),
            'IR': ('🚨 Incident Response', 'GuardDuty, alerting', 2),
            'MP': ('💿 Media Protection', 'Encryption at rest', 1),
            'RA': ('📊 Risk Assessment', 'Vulnerability scanning', 1),
            'SA': ('🏗️ System Acquisition', 'SDLC, CI/CD', 2),
            'SC': ('🔒 System & Comms Protection', 'Network, encryption', 4),
            'SI': ('🛡️ System Integrity', 'Patching, malware protection', 3),
            'SR': ('📦 Supply Chain', 'Third-party dependencies', 1),
        }
        
        # Quick select options
        col1, col2 = st.columns(2)
        with col1:
            select_all = st.button("✅ Select All", use_container_width=True)
        with col2:
            clear_all = st.button("🔄 Clear All", use_container_width=True)
        
        # Initialize session state for selections
        if 'selected_families' not in st.session_state:
            st.session_state.selected_families = []  # Default: none selected
        
        # Handle select/clear all
        if select_all:
            st.session_state.selected_families = list(families.keys())
        if clear_all:
            st.session_state.selected_families = []
        
        st.markdown("---")
        
        # Multi-select checkboxes for each family
        selected_families = []
        for family_code, (display_name, description, count) in families.items():
            # Check if family should be selected
            is_selected = family_code in st.session_state.selected_families
            
            checked = st.checkbox(
                f"{display_name} ({count})",
                value=is_selected,
                key=f"family_{family_code}",
                help=description
            )
            if checked:
                selected_families.append(family_code)
        
        # Update session state
        st.session_state.selected_families = selected_families
        
        # Show selection summary
        total_controls = sum(families[f][2] for f in selected_families) if selected_families else 0
        
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
        run_assessment = st.button(
            f"🚀 Run Assessment ({total_controls} controls)", 
            use_container_width=True,
            disabled=len(selected_families) == 0
        )
        
        st.markdown("---")
        st.markdown("### 📊 Control Counts Reference")
        st.markdown("""
        | Family | Controls |
        |--------|----------|
        | AC | 7 |
        | AU | 6 |
        | CA | 2 |
        | CM | 3 |
        | CP | 2 |
        | IA | 2 |
        | IR | 2 |
        | MP | 1 |
        | RA | 1 |
        | SA | 2 |
        | SC | 4 |
        | SI | 3 |
        | SR | 1 |
        | **Total** | **36** |
        """)
        
        return region, selected_families, run_assessment


def render_metrics(summary: dict):
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
        <div class="metric-box">
            <div class="metric-value pass">{passed}</div>
            <div class="metric-label">Passed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value fail">{failed}</div>
            <div class="metric-label">Failed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value warning">{warnings}</div>
            <div class="metric-label">Warnings</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value info">{total}</div>
            <div class="metric-label">Total</div>
        </div>
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
    st.markdown("### 📋 Results by Control Family")
    
    cols = st.columns(4)
    idx = 0
    
    for family, counts in summary.get('by_family', {}).items():
        with cols[idx % 4]:
            total = sum(counts.values())
            passed = counts.get('pass', 0)
            pct = (passed / total * 100) if total > 0 else 0
            
            color = "#00d4aa" if pct >= 80 else "#ffc107" if pct >= 50 else "#ff6b6b"
            
            st.markdown(f"""
            <div class="family-card">
                <h4>{family}</h4>
                <p>{family_names.get(family, family)}</p>
                <div style="margin-top: 0.5rem;">
                    <span style="color: {color}; font-weight: 700;">{passed}/{total}</span>
                    <span style="color: #8ba3bc;"> passed ({pct:.0f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        idx += 1


def render_control_result(result: ControlResult):
    status_class = get_status_class(result.status)
    status_emoji = get_status_emoji(result.status)
    
    with st.expander(f"{status_emoji} **{result.control_id}**: {result.control_name}", expanded=False):
        if result.findings:
            st.markdown("**📋 Findings:**")
            for finding in result.findings:
                st.markdown(f'<div class="finding-box">{finding}</div>', unsafe_allow_html=True)
        
        if result.recommendations:
            st.markdown("**💡 Recommendations:**")
            for rec in result.recommendations:
                st.markdown(f'<div class="recommendation-box">{rec}</div>', unsafe_allow_html=True)


def render_results(results: List[ControlResult], family_names: dict):
    # Group by family
    by_family = {}
    for result in results:
        if result.family not in by_family:
            by_family[result.family] = []
        by_family[result.family].append(result)
    
    for family, family_results in by_family.items():
        passed = len([r for r in family_results if r.status == ControlStatus.PASS])
        total = len(family_results)
        
        st.markdown(f"""
        <div class="family-section">
            <h2>{family} - {family_names.get(family, family)}</h2>
            <span>{passed}/{total} controls passed</span>
        </div>
        """, unsafe_allow_html=True)
        
        for result in family_results:
            render_control_result(result)


def create_export_data(results: List[ControlResult], assessor) -> dict:
    summary = assessor.generate_summary(results)
    
    return {
        'assessment_info': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'account_id': assessor.account_id,
            'framework': 'NIST 800-53 Revision 5',
            'scope': 'Comprehensive Cloud Assessment'
        },
        'summary': summary,
        'results': [
            {
                'control_id': r.control_id,
                'control_name': r.control_name,
                'family': r.family,
                'status': r.status.name,
                'findings': r.findings,
                'recommendations': r.recommendations
            }
            for r in results
        ]
    }


def save_results_locally(results: List[ControlResult], assessor, family: str, export_data: dict) -> Optional[str]:
    """
    Save assessment results to local NIST_Assessment_Reports folder.
    Returns the local folder path if successful, None otherwise.
    """
    try:
        # Ensure local directory exists
        LOCAL_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create timestamp for unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        account_id = assessor.account_id
        
        # Generate base filename
        base_name = f"nist_rev5_{family}_{account_id}_{timestamp}"
        
        # Create subdirectories
        json_dir = LOCAL_REPORTS_DIR / "json"
        csv_dir = LOCAL_REPORTS_DIR / "csv"
        reports_dir = LOCAL_REPORTS_DIR / "reports"
        
        json_dir.mkdir(exist_ok=True)
        csv_dir.mkdir(exist_ok=True)
        reports_dir.mkdir(exist_ok=True)
        
        # Save JSON
        json_path = json_dir / f"{base_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        # Save CSV
        csv_path = csv_dir / f"{base_name}.csv"
        rows = []
        for r in results:
            rows.append({
                'Family': r.family,
                'Control ID': r.control_id,
                'Control Name': r.control_name,
                'Status': r.status.name,
                'Findings': ' | '.join(r.findings),
                'Recommendations': ' | '.join(r.recommendations)
            })
        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False)
        
        # Save summary report (Markdown)
        summary = export_data['summary']
        report = f"""# NIST 800-53 Rev 5 Assessment Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Account:** {assessor.account_id}  
**Framework:** NIST 800-53 Revision 5  
**Family Assessed:** {family}

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Controls | {summary['total_controls']} |
| ✅ Passed | {summary['passed']} |
| ❌ Failed | {summary['failed']} |
| ⚠️ Warnings | {summary['warnings']} |
| **Compliance Score** | **{(summary['passed']/summary['total_controls']*100):.1f}%** |

## Results by Family

"""
        for fam, counts in summary.get('by_family', {}).items():
            total = sum(counts.values())
            report += f"### {fam}\n"
            report += f"- Passed: {counts.get('pass', 0)}/{total}\n\n"
        
        report += "## Detailed Findings\n\n"
        
        for r in results:
            report += f"### {r.control_id}: {r.control_name}\n"
            report += f"**Status:** {r.status.name}\n\n"
            
            if r.findings:
                report += "**Findings:**\n"
                for f in r.findings:
                    report += f"- {f}\n"
            
            if r.recommendations:
                report += "\n**Recommendations:**\n"
                for rec in r.recommendations:
                    report += f"- {rec}\n"
            
            report += "\n---\n\n"
        
        report_path = reports_dir / f"{base_name}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(LOCAL_REPORTS_DIR)
        
    except Exception as e:
        st.error(f"Error saving results locally: {e}")
        return None


def save_results_to_s3(results: List[ControlResult], assessor, family: str) -> Optional[str]:
    """
    Automatically save assessment results to S3 bucket AND local folder.
    Returns the S3 key if successful, None otherwise.
    """
    try:
        s3 = boto3.client('s3')
        
        # Create timestamp for unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        account_id = assessor.account_id
        
        # Create export data
        export_data = create_export_data(results, assessor)
        
        # Generate filenames
        base_name = f"nist_rev5_{family}_{account_id}_{timestamp}"
        
        # Save JSON
        json_key = f"{S3_PREFIX}json/{base_name}.json"
        json_data = json.dumps(export_data, indent=2)
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=json_key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json',
            Metadata={
                'assessment-type': 'NIST-800-53-Rev5',
                'account-id': account_id,
                'family': family,
                'timestamp': timestamp
            }
        )
        
        # Save CSV
        csv_key = f"{S3_PREFIX}csv/{base_name}.csv"
        rows = []
        for r in results:
            rows.append({
                'Family': r.family,
                'Control ID': r.control_id,
                'Control Name': r.control_name,
                'Status': r.status.name,
                'Findings': ' | '.join(r.findings),
                'Recommendations': ' | '.join(r.recommendations)
            })
        df = pd.DataFrame(rows)
        csv_data = df.to_csv(index=False)
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=csv_key,
            Body=csv_data.encode('utf-8'),
            ContentType='text/csv'
        )
        
        # Save summary report (Markdown)
        summary = export_data['summary']
        report = f"""# NIST 800-53 Rev 5 Assessment Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Account:** {assessor.account_id}  
**Framework:** NIST 800-53 Revision 5  
**Family Assessed:** {family}

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Controls | {summary['total_controls']} |
| ✅ Passed | {summary['passed']} |
| ❌ Failed | {summary['failed']} |
| ⚠️ Warnings | {summary['warnings']} |
| **Compliance Score** | **{(summary['passed']/summary['total_controls']*100):.1f}%** |

## Results by Family

"""
        for fam, counts in summary.get('by_family', {}).items():
            total = sum(counts.values())
            report += f"### {fam}\n"
            report += f"- Passed: {counts.get('pass', 0)}/{total}\n\n"
        
        report += "## Detailed Findings\n\n"
        
        for r in results:
            report += f"### {r.control_id}: {r.control_name}\n"
            report += f"**Status:** {r.status.name}\n\n"
            
            if r.findings:
                report += "**Findings:**\n"
                for f in r.findings:
                    report += f"- {f}\n"
            
            if r.recommendations:
                report += "\n**Recommendations:**\n"
                for rec in r.recommendations:
                    report += f"- {rec}\n"
            
            report += "\n---\n\n"
        
        report_key = f"{S3_PREFIX}reports/{base_name}.md"
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=report_key,
            Body=report.encode('utf-8'),
            ContentType='text/markdown'
        )
        
        # Also save locally
        local_path = save_results_locally(results, assessor, family, export_data)
        if local_path:
            st.success(f"📁 Local copy saved to: `{local_path}`")
        
        return json_key
        
    except ClientError as e:
        st.error(f"Failed to save to S3: {e}")
        # Still try to save locally even if S3 fails
        export_data = create_export_data(results, assessor)
        local_path = save_results_locally(results, assessor, family, export_data)
        if local_path:
            st.info(f"📁 Local copy saved to: `{local_path}`")
        return None
    except Exception as e:
        st.error(f"Error saving results: {e}")
        return None


def render_local_files():
    """Show files saved locally."""
    try:
        if LOCAL_REPORTS_DIR.exists():
            json_dir = LOCAL_REPORTS_DIR / "json"
            csv_dir = LOCAL_REPORTS_DIR / "csv"
            reports_dir = LOCAL_REPORTS_DIR / "reports"
            
            json_files = sorted(json_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5] if json_dir.exists() else []
            csv_files = sorted(csv_dir.glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True)[:5] if csv_dir.exists() else []
            report_files = sorted(reports_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:5] if reports_dir.exists() else []
            
            if json_files or csv_files or report_files:
                st.markdown("### 💻 Local Assessment Reports")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**📄 JSON Files**")
                    for f in json_files:
                        size = f.stat().st_size / 1024
                        st.markdown(f"• `{f.name}` ({size:.1f} KB)")
                
                with col2:
                    st.markdown("**📊 CSV Files**")
                    for f in csv_files:
                        size = f.stat().st_size / 1024
                        st.markdown(f"• `{f.name}` ({size:.1f} KB)")
                
                with col3:
                    st.markdown("**📝 Reports**")
                    for f in report_files:
                        size = f.stat().st_size / 1024
                        st.markdown(f"• `{f.name}` ({size:.1f} KB)")
                
                st.markdown(f"*Local folder:* `{LOCAL_REPORTS_DIR}`")
    except Exception as e:
        st.info(f"Could not list local files: {e}")


def render_s3_files():
    """Show files saved to S3."""
    try:
        s3 = boto3.client('s3')
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=S3_PREFIX,
            MaxKeys=20
        )
        
        files = response.get('Contents', [])
        if files:
            st.markdown("### ☁️ S3 Cloud Assessments")
            
            # Group by type
            json_files = [f for f in files if '/json/' in f['Key']]
            csv_files = [f for f in files if '/csv/' in f['Key']]
            report_files = [f for f in files if '/reports/' in f['Key']]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📄 JSON Files**")
                for f in sorted(json_files, key=lambda x: x['LastModified'], reverse=True)[:5]:
                    name = f['Key'].split('/')[-1]
                    size = f['Size'] / 1024
                    st.markdown(f"• `{name}` ({size:.1f} KB)")
            
            with col2:
                st.markdown("**📊 CSV Files**")
                for f in sorted(csv_files, key=lambda x: x['LastModified'], reverse=True)[:5]:
                    name = f['Key'].split('/')[-1]
                    size = f['Size'] / 1024
                    st.markdown(f"• `{name}` ({size:.1f} KB)")
            
            with col3:
                st.markdown("**📝 Reports**")
                for f in sorted(report_files, key=lambda x: x['LastModified'], reverse=True)[:5]:
                    name = f['Key'].split('/')[-1]
                    size = f['Size'] / 1024
                    st.markdown(f"• `{name}` ({size:.1f} KB)")
            
            st.markdown(f"*Files stored in:* `s3://{S3_BUCKET_NAME}/{S3_PREFIX}`")
    except Exception as e:
        st.info(f"Could not list S3 files: {e}")


def render_export_section(results: List[ControlResult], assessor):
    st.markdown("---")
    
    # Show local saved files
    render_local_files()
    
    st.markdown("---")
    
    # Show S3 saved files
    render_s3_files()
    
    st.markdown("---")
    st.markdown("### 📥 Download Results Locally")
    
    export_data = create_export_data(results, assessor)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_str,
            file_name=f"nist_rev5_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # Create CSV
        rows = []
        for r in results:
            rows.append({
                'Family': r.family,
                'Control ID': r.control_id,
                'Control Name': r.control_name,
                'Status': r.status.name,
                'Findings': ' | '.join(r.findings),
                'Recommendations': ' | '.join(r.recommendations)
            })
        df = pd.DataFrame(rows)
        csv_str = df.to_csv(index=False)
        
        st.download_button(
            label="📊 Download CSV",
            data=csv_str,
            file_name=f"nist_rev5_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        # Markdown report
        summary = export_data['summary']
        report = f"""# NIST 800-53 Rev 5 Assessment Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Account:** {assessor.account_id}  
**Framework:** NIST 800-53 Revision 5

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Controls | {summary['total_controls']} |
| ✅ Passed | {summary['passed']} |
| ❌ Failed | {summary['failed']} |
| ⚠️ Warnings | {summary['warnings']} |
| **Compliance Score** | **{(summary['passed']/summary['total_controls']*100):.1f}%** |

## Results by Family

"""
        for family, counts in summary.get('by_family', {}).items():
            total = sum(counts.values())
            report += f"### {family}\n"
            report += f"- Passed: {counts.get('pass', 0)}/{total}\n\n"
        
        report += "## Detailed Findings\n\n"
        
        for r in results:
            report += f"### {r.control_id}: {r.control_name}\n"
            report += f"**Status:** {r.status.name}\n\n"
            
            if r.findings:
                report += "**Findings:**\n"
                for f in r.findings:
                    report += f"- {f}\n"
            
            if r.recommendations:
                report += "\n**Recommendations:**\n"
                for rec in r.recommendations:
                    report += f"- {rec}\n"
            
            report += "\n---\n\n"
        
        st.download_button(
            label="📝 Download Report",
            data=report,
            file_name=f"nist_rev5_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )


def run_assessment_with_progress(assessor, families: List[str]) -> List[ControlResult]:
    """
    Run assessment for selected control families.
    
    Args:
        assessor: The NIST 800-53 Rev 5 assessor instance
        families: List of family codes to assess (e.g., ['AC', 'AU', 'SC'])
    
    Returns:
        List of ControlResult objects
    """
    all_checks = assessor.get_all_checks()
    
    # Build list of checks to run based on selected families
    checks_to_run = []
    for fam in families:
        if fam in all_checks:
            for check in all_checks[fam]:
                checks_to_run.append((fam, check))
    
    if not checks_to_run:
        st.warning("No checks found for the selected families.")
        return []
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    family_status = st.empty()
    
    current_family = None
    
    for i, (fam, check_func) in enumerate(checks_to_run):
        # Show current family being assessed
        if fam != current_family:
            current_family = fam
            family_status.markdown(f"**📂 Assessing: {assessor.CONTROL_FAMILIES.get(fam, fam)}**")
        
        status_text.text(f"🔍 [{fam}] {check_func.__name__.replace('check_', '').replace('_', ' ').title()}...")
        
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            results.append(ControlResult(
                control_id="ERR",
                control_name=check_func.__name__,
                family=fam,
                status=ControlStatus.ERROR,
                findings=[str(e)]
            ))
        
        progress_bar.progress((i + 1) / len(checks_to_run))
        time.sleep(0.05)
    
    family_status.empty()
    status_text.text(f"✅ Assessment complete! ({len(results)} controls assessed)")
    time.sleep(0.5)
    progress_bar.empty()
    status_text.empty()
    
    return results


def main():
    render_header()
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["🛡️ NIST Assessment", "🔐 SSL Certificates"])
    
    with tab2:
        render_certificate_viewer()
    
    with tab1:
        region, selected_families, run_assessment = render_sidebar()
        
        # Session state
        if 'results' not in st.session_state:
            st.session_state.results = None
        if 'assessor' not in st.session_state:
            st.session_state.assessor = None
        
        family_names = NIST80053Rev5Assessor.CONTROL_FAMILIES
        
        if run_assessment and selected_families:
            try:
                with st.spinner("🔐 Connecting to AWS..."):
                    selected_region = None if region == "Default" else region
                    assessor = NIST80053Rev5Assessor(region=selected_region)
                    st.session_state.assessor = assessor
                
                st.success(f"✅ Connected to AWS Account: **{assessor.account_id}**")
                
                # Show which families will be assessed
                families_str = ", ".join(selected_families)
                st.info(f"📋 Assessing families: **{families_str}**")
                
                st.session_state.results = run_assessment_with_progress(assessor, selected_families)
                st.session_state.families_assessed = selected_families
                
                # Auto-save results to S3
                family_label = "-".join(selected_families) if len(selected_families) <= 4 else f"{len(selected_families)}_families"
                with st.spinner("💾 Saving results to S3..."):
                    s3_key = save_results_to_s3(st.session_state.results, assessor, family_label)
                    if s3_key:
                        st.success(f"📦 Results saved to S3: `s3://{S3_BUCKET_NAME}/{S3_PREFIX}`")
                        st.session_state.s3_saved = True
                    else:
                        st.warning("⚠️ Could not save to S3 - results available for manual download")
                        st.session_state.s3_saved = False
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Ensure your AWS credentials are configured correctly.")
                return
        
        if st.session_state.results and st.session_state.assessor:
            results = st.session_state.results
            assessor = st.session_state.assessor
            summary = assessor.generate_summary(results)
            
            st.markdown("---")
            render_metrics(summary)
            
            # Risk level indicator
            score = (summary['passed'] / summary['total_controls'] * 100) if summary['total_controls'] > 0 else 0
            
            if summary['failed'] > 0:
                st.error(f"🚨 **{summary['failed']} control(s) FAILED** - Immediate attention required!")
            elif summary['warnings'] > 5:
                st.warning(f"⚠️ **{summary['warnings']} warning(s)** - Review recommended")
            elif score >= 80:
                st.success(f"✅ **Strong compliance posture** - {score:.0f}% score")
            
            st.markdown("---")
            render_family_summary(summary, family_names)
            
            st.markdown("---")
            render_results(results, family_names)
            
            render_export_section(results, assessor)
        
        else:
            # Welcome screen
            st.markdown("""
            <div style="text-align: center; padding: 3rem; background: #ffffff; border-radius: 12px; margin: 2rem 0; border: 1px solid #e5e7eb; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
                <h2 style="color: #1e3a5f; margin-bottom: 1rem;">🎯 Ready to Assess</h2>
                <p style="color: #4a5568; font-size: 1.1rem; max-width: 600px; margin: 0 auto;">
                    Select one or more control families from the sidebar using the checkboxes, 
                    then click <strong style="color: #059669;">Run Assessment</strong>.<br/><br/>
                    Use <strong style="color: #059669;">Select All</strong> for a comprehensive assessment 
                    or pick specific families to focus your evaluation.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Family overview cards
            st.markdown("### 📚 Control Family Overview")
            
            col1, col2, col3 = st.columns(3)
            
            families_info = [
                ("🔐 Access Control (AC)", "7 controls", "Account management, access enforcement, least privilege, remote access"),
                ("📝 Audit & Accountability (AU)", "6 controls", "Event logging, audit records, protection, retention"),
                ("✅ Assessment & Authorization (CA)", "2 controls", "Security Hub, continuous monitoring"),
                ("⚙️ Configuration Management (CM)", "3 controls", "Baseline configuration, inventory, settings"),
                ("💾 Contingency Planning (CP)", "2 controls", "System backup, recovery and reconstitution"),
                ("🎫 Identification & Auth (IA)", "2 controls", "MFA, password policy, authenticator management"),
                ("🚨 Incident Response (IR)", "2 controls", "Incident handling, reporting, GuardDuty"),
                ("💿 Media Protection (MP)", "1 control", "Encryption at rest for storage"),
                ("📊 Risk Assessment (RA)", "1 control", "Vulnerability scanning with Inspector"),
                ("🏗️ System Acquisition (SA)", "2 controls", "SDLC, external services review"),
                ("🔒 System & Comms Protection (SC)", "4 controls", "Network boundaries, encryption, TLS"),
                ("🛡️ System Integrity (SI)", "3 controls", "Patching, malware protection, monitoring"),
            ]
            
            for i, (name, count, desc) in enumerate(families_info):
                with [col1, col2, col3][i % 3]:
                    st.markdown(f"""
                    <div class="family-card">
                        <h4>{name}</h4>
                        <p><strong>{count}</strong> - {desc}</p>
                    </div>
                    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

