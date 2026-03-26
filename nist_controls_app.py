"""
NIST 800-53 Security Controls Assessment - Streamlit UI
Control Families: AU (Audit and Accountability) & SA (System and Services Acquisition)
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timezone
from io import StringIO
import time

# Import the assessor from our main script
from nist_800_53_controls import NIST80053Assessor, ControlStatus, ControlResult

# Page configuration
st.set_page_config(
    page_title="NIST 800-53 Controls Assessment",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    
    code, .stCode {
        font-family: 'IBM Plex Mono', monospace;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border-left: 4px solid #e94560;
    }
    
    .main-header h1 {
        color: #ffffff;
        margin: 0;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        color: #a0a0a0;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    .metric-card {
        background: linear-gradient(145deg, #1e1e2f, #252540);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #333355;
        text-align: center;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .metric-label {
        color: #888;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }
    
    .pass { color: #00d26a; }
    .fail { color: #ff4757; }
    .warning { color: #ffa502; }
    .error { color: #ff6b6b; }
    
    .control-card {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #333;
    }
    
    .control-card.pass-card { border-left-color: #00d26a; }
    .control-card.fail-card { border-left-color: #ff4757; }
    .control-card.warning-card { border-left-color: #ffa502; }
    .control-card.error-card { border-left-color: #ff6b6b; }
    
    .control-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .control-id {
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        font-size: 1.1rem;
        color: #e94560;
    }
    
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .status-pass { background: rgba(0, 210, 106, 0.2); color: #00d26a; }
    .status-fail { background: rgba(255, 71, 87, 0.2); color: #ff4757; }
    .status-warning { background: rgba(255, 165, 2, 0.2); color: #ffa502; }
    .status-error { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
    
    .finding-item {
        background: rgba(255, 255, 255, 0.03);
        padding: 0.5rem 1rem;
        margin: 0.3rem 0;
        border-radius: 6px;
        font-size: 0.9rem;
        color: #ccc;
    }
    
    .recommendation-item {
        background: rgba(233, 69, 96, 0.1);
        padding: 0.5rem 1rem;
        margin: 0.3rem 0;
        border-radius: 6px;
        font-size: 0.9rem;
        color: #e94560;
        border-left: 2px solid #e94560;
    }
    
    .sidebar-section {
        background: rgba(255, 255, 255, 0.02);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #e94560, #c73e54);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 8px;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #ff5a75, #e94560);
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.4);
    }
    
    .score-ring {
        background: conic-gradient(
            #00d26a var(--score-percent),
            #333 var(--score-percent)
        );
        border-radius: 50%;
        width: 150px;
        height: 150px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
    }
    
    .score-inner {
        background: #1a1a2e;
        border-radius: 50%;
        width: 120px;
        height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    }
    
    .stExpander {
        background: #1a1a2e;
        border: 1px solid #333355;
        border-radius: 10px;
    }
    
    div[data-testid="stExpander"] details {
        background: #1a1a2e;
        border: 1px solid #333355;
    }
    
    .family-header {
        background: linear-gradient(90deg, #16213e, transparent);
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 2rem 0 1rem 0;
        border-left: 3px solid #e94560;
    }
    
    .family-header h2 {
        margin: 0;
        font-size: 1.3rem;
        color: #fff;
    }
    
    .family-header p {
        margin: 0.3rem 0 0 0;
        color: #888;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


def get_status_emoji(status: ControlStatus) -> str:
    """Get emoji for control status."""
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
        ControlStatus.NOT_APPLICABLE: "na"
    }.get(status, "")


def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🛡️ NIST 800-53 Security Controls Assessment</h1>
        <p>Automated compliance checking for AU (Audit & Accountability) and SA (System & Services Acquisition) control families</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with controls."""
    with st.sidebar:
        st.markdown("### ⚙️ Assessment Configuration")
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        
        # Region selection
        regions = [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1",
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
        ]
        region = st.selectbox(
            "🌍 AWS Region",
            options=["Default"] + regions,
            help="Select the AWS region to assess"
        )
        
        # Control family selection
        family = st.radio(
            "📋 Control Family",
            options=["All Controls", "AU - Audit & Accountability", "SA - System & Services Acquisition"],
            help="Select which control family to assess"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Run assessment button
        st.markdown("---")
        run_assessment = st.button("🚀 Run Assessment", use_container_width=True)
        
        # Info section
        st.markdown("---")
        st.markdown("### 📚 About")
        st.markdown("""
        This tool assesses AWS infrastructure against 
        **NIST 800-53** security controls.
        
        **AU Controls** focus on logging, audit trails, 
        and accountability mechanisms.
        
        **SA Controls** focus on system acquisition, 
        development practices, and vendor management.
        """)
        
        return region, family, run_assessment


def render_metrics(results: list):
    """Render the metrics cards."""
    passed = len([r for r in results if r.status == ControlStatus.PASS])
    failed = len([r for r in results if r.status == ControlStatus.FAIL])
    warnings = len([r for r in results if r.status == ControlStatus.WARNING])
    errors = len([r for r in results if r.status == ControlStatus.ERROR])
    total = len(results)
    
    # Calculate compliance score
    applicable = total - errors
    score = (passed / applicable * 100) if applicable > 0 else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: #00d26a;">{passed}</p>
            <p class="metric-label">Passed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: #ff4757;">{failed}</p>
            <p class="metric-label">Failed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: #ffa502;">{warnings}</p>
            <p class="metric-label">Warnings</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: #ff6b6b;">{errors}</p>
            <p class="metric-label">Errors</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        score_color = "#00d26a" if score >= 70 else "#ffa502" if score >= 50 else "#ff4757"
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value" style="color: {score_color};">{score:.0f}%</p>
            <p class="metric-label">Score</p>
        </div>
        """, unsafe_allow_html=True)


def render_control_result(result: ControlResult):
    """Render a single control result."""
    status_class = get_status_class(result.status)
    status_emoji = get_status_emoji(result.status)
    
    with st.expander(f"{status_emoji} **{result.control_id}**: {result.control_name}", expanded=False):
        # Findings
        if result.findings:
            st.markdown("**📋 Findings:**")
            for finding in result.findings:
                st.markdown(f"""
                <div class="finding-item">{finding}</div>
                """, unsafe_allow_html=True)
        
        # Recommendations
        if result.recommendations:
            st.markdown("**💡 Recommendations:**")
            for rec in result.recommendations:
                st.markdown(f"""
                <div class="recommendation-item">{rec}</div>
                """, unsafe_allow_html=True)


def render_results(results: list):
    """Render all assessment results."""
    # Separate AU and SA controls
    au_results = [r for r in results if r.control_id.startswith('AU')]
    sa_results = [r for r in results if r.control_id.startswith('SA')]
    
    if au_results:
        st.markdown("""
        <div class="family-header">
            <h2>🔍 AU - Audit and Accountability</h2>
            <p>Controls ensuring audit trails, logging, and accountability mechanisms</p>
        </div>
        """, unsafe_allow_html=True)
        
        for result in au_results:
            render_control_result(result)
    
    if sa_results:
        st.markdown("""
        <div class="family-header">
            <h2>🏗️ SA - System and Services Acquisition</h2>
            <p>Controls for system development, acquisition, and vendor management</p>
        </div>
        """, unsafe_allow_html=True)
        
        for result in sa_results:
            render_control_result(result)


def create_export_data(results: list, account_id: str) -> dict:
    """Create export data structure."""
    passed = len([r for r in results if r.status == ControlStatus.PASS])
    failed = len([r for r in results if r.status == ControlStatus.FAIL])
    warnings = len([r for r in results if r.status == ControlStatus.WARNING])
    errors = len([r for r in results if r.status == ControlStatus.ERROR])
    
    return {
        'assessment_info': {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'account_id': account_id,
            'framework': 'NIST 800-53',
            'control_families': ['AU', 'SA']
        },
        'summary': {
            'total_controls': len(results),
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'errors': errors,
            'compliance_score': round(passed / (len(results) - errors) * 100, 1) if (len(results) - errors) > 0 else 0
        },
        'results': [
            {
                'control_id': r.control_id,
                'control_name': r.control_name,
                'status': r.status.name,
                'findings': r.findings,
                'recommendations': r.recommendations
            }
            for r in results
        ]
    }


def create_csv_export(results: list) -> str:
    """Create CSV export string."""
    rows = []
    for r in results:
        rows.append({
            'Control ID': r.control_id,
            'Control Name': r.control_name,
            'Status': r.status.name,
            'Findings': ' | '.join(r.findings),
            'Recommendations': ' | '.join(r.recommendations)
        })
    
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def render_export_section(results: list, account_id: str):
    """Render the export section."""
    st.markdown("---")
    st.markdown("### 📥 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    export_data = create_export_data(results, account_id)
    
    with col1:
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_str,
            file_name=f"nist_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        csv_str = create_csv_export(results)
        st.download_button(
            label="📊 Download CSV",
            data=csv_str,
            file_name=f"nist_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        # Create a summary report
        report = f"""NIST 800-53 Security Controls Assessment Report
================================================

Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
AWS Account: {account_id}
Framework: NIST 800-53
Control Families: AU (Audit & Accountability), SA (System & Services Acquisition)

SUMMARY
-------
Total Controls Assessed: {export_data['summary']['total_controls']}
Passed: {export_data['summary']['passed']}
Failed: {export_data['summary']['failed']}
Warnings: {export_data['summary']['warnings']}
Errors: {export_data['summary']['errors']}
Compliance Score: {export_data['summary']['compliance_score']}%

DETAILED RESULTS
----------------
"""
        for r in results:
            report += f"\n{r.control_id}: {r.control_name}\n"
            report += f"Status: {r.status.name}\n"
            report += "Findings:\n"
            for f in r.findings:
                report += f"  - {f}\n"
            if r.recommendations:
                report += "Recommendations:\n"
                for rec in r.recommendations:
                    report += f"  - {rec}\n"
            report += "-" * 50 + "\n"
        
        st.download_button(
            label="📝 Download Report",
            data=report,
            file_name=f"nist_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )


def run_assessment_with_progress(assessor: NIST80053Assessor, family: str) -> list:
    """Run assessment with progress indication."""
    results = []
    
    # Define checks based on family
    au_checks = [
        ("AU-2", "Audit Events", assessor.check_au_2_audit_events),
        ("AU-3", "Content of Audit Records", assessor.check_au_3_content_of_audit_records),
        ("AU-4", "Audit Log Storage", assessor.check_au_4_audit_log_storage),
        ("AU-6", "Audit Review & Analysis", assessor.check_au_6_audit_review_analysis),
        ("AU-8", "Time Stamps", assessor.check_au_8_time_stamps),
        ("AU-9", "Protection of Audit Info", assessor.check_au_9_protection_of_audit_info),
        ("AU-11", "Audit Record Retention", assessor.check_au_11_audit_record_retention),
        ("AU-12", "Audit Generation", assessor.check_au_12_audit_generation),
    ]
    
    sa_checks = [
        ("SA-3", "System Development Lifecycle", assessor.check_sa_3_system_development_lifecycle),
        ("SA-4", "Acquisition Process", assessor.check_sa_4_acquisition_process),
        ("SA-8", "Security Engineering Principles", assessor.check_sa_8_security_engineering_principles),
        ("SA-9", "External System Services", assessor.check_sa_9_external_system_services),
        ("SA-10", "Developer Config Management", assessor.check_sa_10_developer_configuration_management),
        ("SA-11", "Developer Testing", assessor.check_sa_11_developer_testing),
        ("SA-15", "Development Process & Tools", assessor.check_sa_15_development_process),
    ]
    
    if family == "AU - Audit & Accountability":
        checks = au_checks
    elif family == "SA - System & Services Acquisition":
        checks = sa_checks
    else:
        checks = au_checks + sa_checks
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (control_id, control_name, check_func) in enumerate(checks):
        status_text.text(f"🔍 Checking {control_id}: {control_name}...")
        result = check_func()
        results.append(result)
        progress_bar.progress((i + 1) / len(checks))
        time.sleep(0.1)  # Small delay for visual feedback
    
    status_text.text("✅ Assessment complete!")
    time.sleep(0.5)
    status_text.empty()
    progress_bar.empty()
    
    return results


def main():
    """Main application entry point."""
    render_header()
    region, family, run_assessment = render_sidebar()
    
    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'account_id' not in st.session_state:
        st.session_state.account_id = None
    
    # Run assessment when button is clicked
    if run_assessment:
        try:
            with st.spinner("🔐 Connecting to AWS..."):
                selected_region = None if region == "Default" else region
                assessor = NIST80053Assessor(region=selected_region)
                st.session_state.account_id = assessor.account_id
            
            st.success(f"✅ Connected to AWS Account: {assessor.account_id}")
            
            # Run the assessment
            st.session_state.results = run_assessment_with_progress(assessor, family)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Make sure your AWS credentials are configured correctly.")
            return
    
    # Display results if available
    if st.session_state.results:
        st.markdown("---")
        render_metrics(st.session_state.results)
        st.markdown("---")
        render_results(st.session_state.results)
        render_export_section(st.session_state.results, st.session_state.account_id)
    else:
        # Show welcome message
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: linear-gradient(145deg, #1e1e2f, #252540); border-radius: 12px; margin: 2rem 0;">
            <h2 style="color: #fff; margin-bottom: 1rem;">👋 Welcome to the NIST 800-53 Controls Assessment</h2>
            <p style="color: #888; font-size: 1.1rem; max-width: 600px; margin: 0 auto;">
                Configure your assessment options in the sidebar and click 
                <strong style="color: #e94560;">Run Assessment</strong> to evaluate your AWS infrastructure 
                against NIST 800-53 security controls.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Control family info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: #1a1a2e; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #00d26a;">
                <h3 style="color: #00d26a; margin-top: 0;">🔍 AU Controls</h3>
                <p style="color: #ccc;">Audit and Accountability controls ensure proper logging, monitoring, and audit trail capabilities.</p>
                <ul style="color: #888;">
                    <li>AU-2: Audit Events</li>
                    <li>AU-3: Content of Audit Records</li>
                    <li>AU-4: Audit Log Storage</li>
                    <li>AU-6: Audit Review & Analysis</li>
                    <li>AU-8: Time Stamps</li>
                    <li>AU-9: Protection of Audit Info</li>
                    <li>AU-11: Audit Record Retention</li>
                    <li>AU-12: Audit Generation</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: #1a1a2e; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #e94560;">
                <h3 style="color: #e94560; margin-top: 0;">🏗️ SA Controls</h3>
                <p style="color: #ccc;">System and Services Acquisition controls govern development, procurement, and vendor management.</p>
                <ul style="color: #888;">
                    <li>SA-3: System Development Lifecycle</li>
                    <li>SA-4: Acquisition Process</li>
                    <li>SA-8: Security Engineering Principles</li>
                    <li>SA-9: External System Services</li>
                    <li>SA-10: Developer Config Management</li>
                    <li>SA-11: Developer Testing</li>
                    <li>SA-15: Development Process & Tools</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

