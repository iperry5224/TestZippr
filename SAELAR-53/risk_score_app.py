#!/usr/bin/env python3
"""
Security Risk Score Calculator - Streamlit UI
==============================================
Interactive web interface for calculating and visualizing
security risk scores from assessment reports.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import plotly.express as px
import plotly.graph_objects as go

from risk_score_calculator import (
    RiskScoreCalculator, RiskAssessment, Finding,
    Likelihood, Impact, RiskLevel
)

# Page configuration
st.set_page_config(
    page_title="Risk Score Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Light theme matching the NIST app
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&family=Source+Code+Pro:wght@400;500&display=swap');
    
    .main .block-container {
        background-color: #f5f5f5;
        padding: 2rem;
        border-radius: 8px;
    }
    
    html, body, [class*="css"] {
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #3d7ab5 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border-left: 5px solid #f59e0b;
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
    
    .risk-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #e5e7eb;
    }
    
    .risk-card.critical { border-left-color: #dc2626; }
    .risk-card.high { border-left-color: #f59e0b; }
    .risk-card.medium { border-left-color: #eab308; }
    .risk-card.low { border-left-color: #22c55e; }
    
    .metric-box {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #e5e7eb;
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
    
    .critical { color: #dc2626; }
    .high { color: #f59e0b; }
    .medium { color: #eab308; }
    .low { color: #22c55e; }
    
    .finding-item {
        background: #ffffff;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #e5e7eb;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: #ffffff;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 700;
        border-radius: 8px;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #fbbf24, #f59e0b);
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.4);
    }
    
    .risk-matrix-cell {
        text-align: center;
        padding: 8px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def render_header():
    st.markdown("""
    <div class="main-header">
        <h1>📊 Security Architecture and Evaluation's Risk Score Calculator</h1>
        <p>Calculate, visualize, and prioritize security risks from assessment findings</p>
    </div>
    """, unsafe_allow_html=True)


def get_risk_color(level: RiskLevel) -> str:
    """Get color for risk level."""
    return {
        RiskLevel.CRITICAL: "#dc2626",
        RiskLevel.HIGH: "#f59e0b",
        RiskLevel.MEDIUM: "#eab308",
        RiskLevel.LOW: "#22c55e"
    }.get(level, "#6b7280")


def get_risk_class(level: RiskLevel) -> str:
    """Get CSS class for risk level."""
    return level.value.lower()


def render_risk_gauge(score: float, max_score: float = 25):
    """Render a risk gauge chart."""
    percentage = (score / max_score) * 100
    
    if percentage >= 68:
        color = "#dc2626"
        level = "CRITICAL"
    elif percentage >= 40:
        color = "#f59e0b"
        level = "HIGH"
    elif percentage >= 20:
        color = "#eab308"
        level = "MEDIUM"
    else:
        color = "#22c55e"
        level = "LOW"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Risk Score<br><span style='font-size:0.8em;color:{color}'>{level}</span>"},
        gauge={
            'axis': {'range': [0, 25], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 4], 'color': "#dcfce7"},
                {'range': [4, 9], 'color': "#fef9c3"},
                {'range': [9, 16], 'color': "#fed7aa"},
                {'range': [16, 25], 'color': "#fecaca"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Source Sans Pro'}
    )
    
    return fig


def render_risk_distribution(findings: List[Finding]):
    """Render risk distribution pie chart."""
    risk_counts = {
        'CRITICAL': len([f for f in findings if f.risk_level == RiskLevel.CRITICAL]),
        'HIGH': len([f for f in findings if f.risk_level == RiskLevel.HIGH]),
        'MEDIUM': len([f for f in findings if f.risk_level == RiskLevel.MEDIUM]),
        'LOW': len([f for f in findings if f.risk_level == RiskLevel.LOW])
    }
    
    colors = ['#dc2626', '#f59e0b', '#eab308', '#22c55e']
    
    fig = px.pie(
        values=list(risk_counts.values()),
        names=list(risk_counts.keys()),
        color_discrete_sequence=colors,
        hole=0.4
    )
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Source Sans Pro'},
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig


def render_risk_by_family(findings: List[Finding]):
    """Render risk by control family bar chart."""
    family_data = {}
    for f in findings:
        if f.control_family not in family_data:
            family_data[f.control_family] = {'count': 0, 'total_risk': 0}
        family_data[f.control_family]['count'] += 1
        family_data[f.control_family]['total_risk'] += f.risk_score
    
    families = list(family_data.keys())
    avg_risks = [family_data[f]['total_risk'] / family_data[f]['count'] for f in families]
    counts = [family_data[f]['count'] for f in families]
    
    # Sort by average risk
    sorted_data = sorted(zip(families, avg_risks, counts), key=lambda x: x[1], reverse=True)
    families, avg_risks, counts = zip(*sorted_data) if sorted_data else ([], [], [])
    
    colors = ['#dc2626' if r > 16 else '#f59e0b' if r > 9 else '#eab308' if r > 4 else '#22c55e' for r in avg_risks]
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(families),
            y=list(avg_risks),
            marker_color=colors,
            text=[f"{r:.1f}" for r in avg_risks],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="Average Risk by Control Family",
        xaxis_title="Control Family",
        yaxis_title="Average Risk Score",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Source Sans Pro'},
        yaxis=dict(range=[0, 25])
    )
    
    return fig


def render_risk_matrix():
    """Render interactive risk matrix."""
    st.markdown("### 📐 Risk Matrix")
    
    # Create matrix data
    matrix_data = []
    impacts = ['Negligible', 'Minor', 'Moderate', 'Significant', 'Severe']
    likelihoods = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
    
    for i, likelihood in enumerate(likelihoods, 1):
        row = {'Likelihood': likelihood}
        for j, impact in enumerate(impacts, 1):
            score = i * j
            row[impact] = score
        matrix_data.append(row)
    
    df = pd.DataFrame(matrix_data)
    df = df.set_index('Likelihood')
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=impacts,
        y=likelihoods,
        colorscale=[
            [0, '#22c55e'],
            [0.16, '#22c55e'],
            [0.16, '#eab308'],
            [0.36, '#eab308'],
            [0.36, '#f59e0b'],
            [0.64, '#f59e0b'],
            [0.64, '#dc2626'],
            [1, '#dc2626']
        ],
        showscale=True,
        text=df.values,
        texttemplate="%{text}",
        textfont={"size": 14, "color": "white"},
        hovertemplate="Likelihood: %{y}<br>Impact: %{x}<br>Score: %{z}<extra></extra>"
    ))
    
    fig.update_layout(
        xaxis_title="Impact",
        yaxis_title="Likelihood",
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Source Sans Pro'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Legend
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🟢 **LOW** (1-4)")
    with col2:
        st.markdown("🟡 **MEDIUM** (5-9)")
    with col3:
        st.markdown("🟠 **HIGH** (10-16)")
    with col4:
        st.markdown("🔴 **CRITICAL** (17-25)")


def render_finding_card(finding: Finding, index: int):
    """Render a finding card."""
    risk_class = get_risk_class(finding.risk_level)
    risk_emoji = "🔴" if finding.risk_level == RiskLevel.CRITICAL else \
                 "🟠" if finding.risk_level == RiskLevel.HIGH else \
                 "🟡" if finding.risk_level == RiskLevel.MEDIUM else "🟢"
    
    with st.expander(f"{risk_emoji} **{finding.control_id}**: {finding.title} (Score: {finding.risk_score:.0f})", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Risk Score", f"{finding.risk_score:.0f}/25")
        with col2:
            st.metric("Likelihood", finding.likelihood.name)
        with col3:
            st.metric("Impact", finding.impact.name)
        
        st.markdown("**Description:**")
        st.info(finding.description)
        
        if finding.remediation:
            st.markdown("**Remediation:**")
            st.success(finding.remediation)
        
        st.markdown(f"**Status:** `{finding.status}`")


def create_sample_assessment() -> RiskAssessment:
    """Create a sample assessment for demonstration."""
    assessment = RiskAssessment(
        assessment_id=f"RA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        assessment_name="AWS Security Assessment",
        organization="Security Architecture and Evaluation",
        assessor="SAE Security Team",
        date=datetime.now()
    )
    
    sample_findings = [
        Finding(
            finding_id="FIND-001",
            title="Missing MFA on Root Account",
            description="Root account does not have MFA enabled, exposing critical access to potential compromise.",
            control_family="AC",
            control_id="AC-2",
            likelihood=Likelihood.HIGH,
            impact=Impact.SEVERE,
            remediation="Enable MFA on root account immediately using hardware token or virtual MFA."
        ),
        Finding(
            finding_id="FIND-002",
            title="CloudTrail Not Enabled in All Regions",
            description="CloudTrail logging is not enabled in all AWS regions, creating blind spots for security monitoring.",
            control_family="AU",
            control_id="AU-2",
            likelihood=Likelihood.MEDIUM,
            impact=Impact.SIGNIFICANT,
            remediation="Enable CloudTrail in all regions with multi-region trail."
        ),
        Finding(
            finding_id="FIND-003",
            title="Unencrypted S3 Buckets",
            description="Several S3 buckets do not have default encryption enabled, risking data exposure.",
            control_family="SC",
            control_id="SC-8",
            likelihood=Likelihood.MEDIUM,
            impact=Impact.MODERATE,
            remediation="Enable default encryption on all S3 buckets using SSE-S3 or SSE-KMS."
        ),
        Finding(
            finding_id="FIND-004",
            title="Weak Password Policy",
            description="IAM password policy does not meet complexity requirements.",
            control_family="IA",
            control_id="IA-5",
            likelihood=Likelihood.HIGH,
            impact=Impact.SIGNIFICANT,
            remediation="Update IAM password policy to require minimum 14 characters with complexity."
        ),
        Finding(
            finding_id="FIND-005",
            title="No Baseline Configuration",
            description="EC2 instances lack documented baseline configurations.",
            control_family="CM",
            control_id="CM-2",
            likelihood=Likelihood.LOW,
            impact=Impact.MODERATE,
            remediation="Implement AWS Systems Manager State Manager for configuration baselines."
        ),
    ]
    
    for finding in sample_findings:
        assessment.add_finding(finding)
    
    return assessment


def render_sidebar():
    """Render sidebar with options."""
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        
        st.markdown("---")
        st.markdown("### 📂 Load Assessment")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload NIST Assessment JSON",
            type=['json'],
            help="Upload a JSON file from your NIST assessment"
        )
        
        st.markdown("---")
        
        # Or use demo data
        use_demo = st.checkbox("Use Demo Data", value=True)
        
        st.markdown("---")
        st.markdown("### ➕ Add Custom Finding")
        
        with st.expander("Add New Finding"):
            finding_title = st.text_input("Title")
            finding_desc = st.text_area("Description", height=100)
            
            col1, col2 = st.columns(2)
            with col1:
                control_family = st.selectbox(
                    "Control Family",
                    ['AC', 'AU', 'CA', 'CM', 'CP', 'IA', 'IR', 'MP', 'RA', 'SA', 'SC', 'SI', 'SR']
                )
                likelihood = st.selectbox(
                    "Likelihood",
                    [l.name for l in Likelihood]
                )
            with col2:
                control_id = st.text_input("Control ID", placeholder="e.g., AC-2")
                impact = st.selectbox(
                    "Impact",
                    [i.name for i in Impact]
                )
            
            remediation = st.text_area("Remediation", height=100)
            
            add_finding = st.button("➕ Add Finding", use_container_width=True)
        
        return uploaded_file, use_demo, {
            'add': add_finding,
            'title': finding_title,
            'desc': finding_desc,
            'family': control_family,
            'control_id': control_id,
            'likelihood': likelihood,
            'impact': impact,
            'remediation': remediation
        }


def main():
    render_header()
    
    # Initialize session state
    if 'assessment' not in st.session_state:
        st.session_state.assessment = None
    if 'custom_findings' not in st.session_state:
        st.session_state.custom_findings = []
    
    uploaded_file, use_demo, new_finding = render_sidebar()
    
    # Handle new finding
    if new_finding['add'] and new_finding['title']:
        finding = Finding(
            finding_id=f"FIND-CUSTOM-{len(st.session_state.custom_findings)+1}",
            title=new_finding['title'],
            description=new_finding['desc'],
            control_family=new_finding['family'],
            control_id=new_finding['control_id'],
            likelihood=Likelihood[new_finding['likelihood']],
            impact=Impact[new_finding['impact']],
            remediation=new_finding['remediation']
        )
        st.session_state.custom_findings.append(finding)
        st.success(f"✅ Added finding: {new_finding['title']}")
    
    # Load assessment
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            calculator = RiskScoreCalculator()
            # Process uploaded file
            st.session_state.assessment = calculator.load_nist_assessment(Path(uploaded_file.name))
            st.success("✅ Assessment loaded successfully!")
        except Exception as e:
            st.error(f"Error loading file: {e}")
            use_demo = True
    
    if use_demo or st.session_state.assessment is None:
        assessment = create_sample_assessment()
    else:
        assessment = st.session_state.assessment
    
    # Add custom findings
    for finding in st.session_state.custom_findings:
        assessment.add_finding(finding)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 Findings", "📐 Risk Matrix", "📄 Report"])
    
    with tab1:
        # Summary metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        risk_color = get_risk_color(assessment.overall_risk_level)
        
        with col1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value" style="color: {risk_color};">{assessment.overall_risk_level.value}</div>
                <div class="metric-label">Overall Risk</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{assessment.average_risk_score:.1f}</div>
                <div class="metric-label">Avg Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{assessment.total_findings}</div>
                <div class="metric-label">Total Findings</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{assessment.compliance_score:.0f}%</div>
                <div class="metric-label">Compliance</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value critical">{assessment.open_findings}</div>
                <div class="metric-label">Open Issues</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Risk Gauge")
            fig = render_risk_gauge(assessment.average_risk_score)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Risk Distribution")
            fig = render_risk_distribution(assessment.findings)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Risk by family
        fig = render_risk_by_family(assessment.findings)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### 📋 Detailed Findings")
        st.markdown(f"*Showing {len(assessment.findings)} findings, sorted by risk score*")
        
        # Sort findings by risk
        sorted_findings = sorted(assessment.findings, key=lambda f: f.risk_score, reverse=True)
        
        for i, finding in enumerate(sorted_findings, 1):
            render_finding_card(finding, i)
    
    with tab3:
        render_risk_matrix()
    
    with tab4:
        st.markdown("### 📄 Risk Assessment Report")
        
        calculator = RiskScoreCalculator()
        report = calculator.generate_risk_report(assessment)
        
        st.code(report, language="text")
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Download Report (TXT)",
                data=report,
                file_name=f"risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            # Create JSON export
            export_data = {
                'assessment_id': assessment.assessment_id,
                'date': assessment.date.isoformat(),
                'summary': {
                    'overall_risk': assessment.overall_risk_level.value,
                    'avg_score': assessment.average_risk_score,
                    'compliance': assessment.compliance_score
                },
                'findings': [
                    {
                        'id': f.finding_id,
                        'title': f.title,
                        'risk_score': f.risk_score,
                        'risk_level': f.risk_level.value
                    }
                    for f in assessment.findings
                ]
            }
            
            st.download_button(
                label="📥 Download Report (JSON)",
                data=json.dumps(export_data, indent=2),
                file_name=f"risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )


if __name__ == "__main__":
    main()

