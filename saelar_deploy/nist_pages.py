"""
NIST 800-53 Rev 5 Pages Module
==============================
Contains all secondary pages: certificate viewer, results display,
export sections, S3/local file management.
"""

import streamlit as st
import pandas as pd
import json
import time
import boto3
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pathlib import Path
from botocore.exceptions import ClientError

from nist_800_53_rev5_full import ControlResult, ControlStatus

# Import configuration from dashboard module
from nist_dashboard import (
    S3_BUCKET_NAME, S3_PREFIX,
    CERT_DIR, CERT_FILE, KEY_FILE,
    get_status_emoji, get_status_class, run_openssl_command
)


# =============================================================================
# CERTIFICATE VIEWER PAGE
# =============================================================================

def render_certificate_viewer():
    """Render the SSL/TLS certificate details section."""
    st.markdown("## 🔐 SSL/TLS Certificate Details")
    
    if not CERT_FILE.exists():
        st.warning("⚠️ No certificate found. Run `bash generate_ssl_certs.sh` to create certificates.")
        return
    
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


# =============================================================================
# RESULTS DISPLAY
# =============================================================================

def render_control_result(result: ControlResult):
    """Render a single control result in an expandable section."""
    status_class = get_status_class(result.status)
    status_emoji = get_status_emoji(result.status)
    
    with st.expander(f"{status_emoji} **{result.control_id}**: {result.control_name}", expanded=False):
        if result.findings:
            # For passed controls, show "Compliant"; for failed/warning, show "Findings"
            finding_label = "**📋 Compliant**" if result.status == ControlStatus.PASS else "**📋 Findings:**"
            st.markdown(finding_label)
            for finding in result.findings:
                st.markdown(f'<div class="finding-box">{finding}</div>', unsafe_allow_html=True)
        
        if result.recommendations:
            st.markdown("**💡 Recommendations:**")
            for rec in result.recommendations:
                st.markdown(f'<div class="recommendation-box">{rec}</div>', unsafe_allow_html=True)


def render_results(results: List[ControlResult], family_names: dict):
    """Render all assessment results grouped by status, then by family."""
    
    # Group by status
    failed_results = [r for r in results if r.status == ControlStatus.FAIL]
    warning_results = [r for r in results if r.status == ControlStatus.WARNING]
    passed_results = [r for r in results if r.status == ControlStatus.PASS]
    other_results = [r for r in results if r.status not in [ControlStatus.FAIL, ControlStatus.WARNING, ControlStatus.PASS]]
    
    # Group all results by family for anchor links
    results_by_family = {}
    for r in results:
        if r.family not in results_by_family:
            results_by_family[r.family] = []
        results_by_family[r.family].append(r)
    
    # All findings anchor
    st.markdown('<div id="all-findings"></div>', unsafe_allow_html=True)
    
    # Failed findings section
    if failed_results:
        st.markdown('<div id="failed-findings"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #dc2626, #ef4444); padding: 1rem 1.5rem; border-radius: 8px; margin: 1.5rem 0 1rem 0;">
            <h2 style="margin: 0; color: #ffffff; font-size: 1.3rem;">❌ Failed Controls ({len(failed_results)})</h2>
        </div>
        """, unsafe_allow_html=True)
        for result in failed_results:
            render_control_result(result)
    
    # Warning findings section
    if warning_results:
        st.markdown('<div id="warning-findings"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #d97706, #f59e0b); padding: 1rem 1.5rem; border-radius: 8px; margin: 1.5rem 0 1rem 0;">
            <h2 style="margin: 0; color: #ffffff; font-size: 1.3rem;">⚠️ Warnings ({len(warning_results)})</h2>
        </div>
        """, unsafe_allow_html=True)
        for result in warning_results:
            render_control_result(result)
    
    # Passed findings section
    if passed_results:
        st.markdown('<div id="passed-findings"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #059669, #10b981); padding: 1rem 1.5rem; border-radius: 8px; margin: 1.5rem 0 1rem 0;">
            <h2 style="margin: 0; color: #ffffff; font-size: 1.3rem;">✅ Passed Controls ({len(passed_results)})</h2>
        </div>
        """, unsafe_allow_html=True)
        for result in passed_results:
            render_control_result(result)
    
    # Other results (errors, not applicable)
    if other_results:
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #6b7280, #9ca3af); padding: 1rem 1.5rem; border-radius: 8px; margin: 1.5rem 0 1rem 0;">
            <h2 style="margin: 0; color: #ffffff; font-size: 1.3rem;">➖ Other ({len(other_results)})</h2>
        </div>
        """, unsafe_allow_html=True)
        for result in other_results:
            render_control_result(result)
    
    # Detailed Results by Family section with anchors
    st.markdown("---")
    st.markdown('<div id="detailed-family-results"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1e3a5f, #2d5a87); padding: 1rem 1.5rem; border-radius: 8px; margin: 1.5rem 0 1rem 0;">
        <h2 style="margin: 0; color: #ffffff; font-size: 1.3rem;">📊 Detailed Results by Control Family</h2>
    </div>
    """, unsafe_allow_html=True)
    
    for family in sorted(results_by_family.keys()):
        family_results = results_by_family[family]
        family_name = family_names.get(family, family)
        
        # Count statuses for this family
        family_passed = len([r for r in family_results if r.status == ControlStatus.PASS])
        family_failed = len([r for r in family_results if r.status == ControlStatus.FAIL])
        family_warnings = len([r for r in family_results if r.status == ControlStatus.WARNING])
        family_total = len(family_results)
        family_pct = (family_passed / family_total * 100) if family_total > 0 else 0
        
        # Determine status color
        if family_failed > 0:
            status_color = "#dc2626"
            status_bg = "linear-gradient(135deg, #fecaca 0%, #fca5a5 100%)"
        elif family_warnings > 0:
            status_color = "#d97706"
            status_bg = "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)"
        else:
            status_color = "#059669"
            status_bg = "linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)"
        
        # Family anchor and header with back link
        st.markdown(f'<div id="family-{family}"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: {status_bg}; border: 2px solid {status_color}; border-radius: 10px; 
                    padding: 1rem 1.5rem; margin: 1rem 0;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                <h3 style="margin: 0; color: #1e3a5f;">
                    {family} - {family_name}
                </h3>
                <a href="#family-summary" style="
                    background: #1e3a5f; 
                    color: white; 
                    padding: 0.4rem 0.8rem; 
                    border-radius: 5px; 
                    text-decoration: none; 
                    font-size: 0.85rem;
                    font-weight: 500;
                    transition: all 0.2s ease;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.3rem;
                " onmouseover="this.style.background='#2d5a87'" onmouseout="this.style.background='#1e3a5f'">
                    ↑ Back to Summary
                </a>
            </div>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <span style="color: #059669; font-weight: 600;">✅ Passed: {family_passed}</span>
                <span style="color: #dc2626; font-weight: 600;">❌ Failed: {family_failed}</span>
                <span style="color: #d97706; font-weight: 600;">⚠️ Warnings: {family_warnings}</span>
                <span style="color: #64748b;">Score: {family_pct:.0f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show all results for this family in an expander
        with st.expander(f"View {family_total} control(s) in {family}", expanded=False):
            for result in family_results:
                render_control_result(result)


# =============================================================================
# EXPORT DATA FUNCTIONS
# =============================================================================

def create_export_data(results: List[ControlResult], assessor) -> dict:
    """Create exportable data structure from assessment results."""
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


def save_results_to_s3(results: List[ControlResult], assessor, family: str) -> Optional[str]:
    """
    Save assessment results to S3 bucket.
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
        report = _generate_markdown_report(results, assessor, family, summary)
        
        report_key = f"{S3_PREFIX}reports/{base_name}.md"
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=report_key,
            Body=report.encode('utf-8'),
            ContentType='text/markdown'
        )
        
        return json_key
        
    except ClientError as e:
        st.error(f"Failed to save to S3: {e}")
        return None
    except Exception as e:
        st.error(f"Error saving results: {e}")
        return None


def _generate_markdown_report(results: List[ControlResult], assessor, family: str, summary: dict) -> str:
    """Generate a markdown format report."""
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
            report += ("**Compliant**\n" if r.status == ControlStatus.PASS else "**Findings:**\n")
            for f in r.findings:
                report += f"- {f}\n"
        
        if r.recommendations:
            report += "\n**Recommendations:**\n"
            for rec in r.recommendations:
                report += f"- {rec}\n"
        
        report += "\n---\n\n"
    
    return report


# =============================================================================
# FILE LISTING SECTIONS
# =============================================================================

# Local file storage removed - all reports now saved to S3 only


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
    """Render the export/download section."""
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
                report += ("**Compliant**\n" if r.status == ControlStatus.PASS else "**Findings:**\n")
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


# =============================================================================
# ASSESSMENT RUNNER
# =============================================================================

def run_assessment_with_progress(assessor, families: List[str]) -> List[ControlResult]:
    """
    Run assessment for selected control families with progress indication.
    
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
