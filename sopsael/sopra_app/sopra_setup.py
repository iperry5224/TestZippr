"""
SOPRA - SAE On-Premise Risk Assessment
A comprehensive security assessment tool for on-premise environments

Version: 2.1.0
"""

import streamlit as st
from datetime import datetime
import os

# Page configuration — MUST be first Streamlit command
st.set_page_config(
    page_title="SOPRA - SAE On-Premise Risk Assessment",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import theme and inject global CSS
from sopra.theme import GLOBAL_CSS

st.markdown(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">'
    "<style>"
    "@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');"
    + GLOBAL_CSS
    + "</style>",
    unsafe_allow_html=True
)

# Inject floating "Back to Dashboard" button (top-right, next to Deploy)
_current_view = st.query_params.get("view", "")
_on_dashboard = (not _current_view and st.session_state.get("opra_active_tab") == "Dashboard")
if not _on_dashboard:
    _back_url = "/" if _current_view else "javascript:void(0)"
    _onclick = "" if _current_view else "onclick=\"window.parent.postMessage({type:'streamlit:setComponentValue'},'*'); return false;\""
    st.markdown(
        '<a id="sopra-back-btn" href="/" target="_self" '
        'style="position:fixed;top:12px;right:140px;z-index:999999;'
        'display:inline-flex;align-items:center;gap:6px;'
        'padding:6px 16px;border-radius:8px;'
        'background:rgba(0,217,255,0.08);border:1px solid rgba(0,217,255,0.25);'
        'color:#00d9ff;font-size:0.78rem;font-weight:600;font-family:inherit;'
        'text-decoration:none;backdrop-filter:blur(8px);'
        'transition:all 0.2s ease;cursor:pointer;" '
        'onmouseover="this.style.background=\'rgba(0,217,255,0.18)\';this.style.borderColor=\'rgba(0,217,255,0.5)\';this.style.boxShadow=\'0 0 12px rgba(0,217,255,0.15)\';" '
        'onmouseout="this.style.background=\'rgba(0,217,255,0.08)\';this.style.borderColor=\'rgba(0,217,255,0.25)\';this.style.boxShadow=\'none\';">'
        '&#x2190; Dashboard</a>',
        unsafe_allow_html=True
    )

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

# Import all page renderers
from sopra.pages.dashboard import (
    render_dashboard, render_category_details, render_metric_details,
    render_remediation_templates_picker, render_assessment_scripts_page
)
from sopra.pages.assessment import render_assessment_page
from sopra.pages.reports import render_reports_page
from sopra.pages.ssp_generator import render_ssp_generator
from sopra.pages.ai_assistant import render_ai_assistant
from sopra.pages.remediation import render_remediation_page
from sopra.pages.conmon import render_conmon_page
from sopra.pages.settings import render_settings_page
from sopra.isso.toolkit import render_isso_toolkit_page
from sopra.isso.poam import render_poam_tracker
from sopra.isso.risk_acceptance import render_risk_acceptance


def main():
    """Main application entry point"""
    # If opened as the pop-out remediation window, render only that page
    if st.query_params.get("view") == "remediation":
        render_remediation_page()
        return

    # If opened as the ConMon pop-out dashboard, render only that page
    if st.query_params.get("view") == "conmon":
        render_conmon_page()
        return

    # If opened as the SSP Generator (standalone)
    if st.query_params.get("view") == "ssp":
        render_ssp_generator()
        return

    # SSP & POA&M tabbed view: Generate SSP | POA&Ms | Risk Acceptance
    if st.query_params.get("view") == "ssp_poam":
        st.markdown("## 📋 Plan of Action & Milestones (POA&M)")
        tab_gen_ssp, tab_poams, tab_risk_acceptance = st.tabs(["📜 Generate SSP", "📋 POA&Ms", "⚖️ Risk Acceptance"])
        with tab_gen_ssp:
            render_ssp_generator()
        with tab_poams:
            render_poam_tracker()
        with tab_risk_acceptance:
            render_risk_acceptance()
        return

    # Risk Acceptance standalone (e.g. from POA&M tile)
    if st.query_params.get("view") == "risk_acceptance":
        render_risk_acceptance()
        return

    # If opened as the ISSO Toolkit pop-out, render that hub
    if st.query_params.get("view") == "isso":
        render_isso_toolkit_page()
        return

    # If opened as the AI Remediation Center directly
    if st.query_params.get("view") == "ai_remed":
        from sopra.isso.ai_remed_ui import render_ai_remediation_dashboard
        render_ai_remediation_dashboard()
        return

    # Quick Action links that open full pages in a new tab
    _view = st.query_params.get("view")
    if _view == "assessment":
        render_assessment_page()
        return
    if _view == "reports":
        render_reports_page()
        return
    if _view == "ai":
        render_ai_assistant()
        return

    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h2 style="color: #00d9ff; margin: 0;">🛡️ SOPRA</h2>
            <p style="color: #f0f0f0; font-size: 0.8rem;">SAE On-Premise Risk Assessment</p>
        </div>
        """, unsafe_allow_html=True)
    
        st.markdown("---")
    
        # Navigation buttons
        nav_options = ["Dashboard", "Data Collection & Ingestion", "Run Security Assessment", "Reports", "Vulnerability Management", "SSP Generator", "AI Assistant"]
    
        for option in nav_options:
            icon = {"Dashboard": "📊", "Data Collection & Ingestion": "📥", "Run Security Assessment": "🔒", "Reports": "📋",
                   "Vulnerability Management": "🧠", "SSP Generator": "📜", "AI Assistant": "💬"}.get(option, "📌")
        
            if st.button(f"{icon} {option}", use_container_width=True, 
                        type="primary" if st.session_state.opra_active_tab == option else "secondary"):
                st.session_state.opra_active_tab = option
                st.rerun()
    
        st.markdown("---")

        st.link_button("🛡️ ISSO Toolkit", "?view=isso", use_container_width=True)

        st.markdown("---")

        if st.button("⚙️ Settings", use_container_width=True,
                    type="primary" if st.session_state.opra_active_tab == "Settings" else "secondary",
                    key="nav_settings"):
            st.session_state.opra_active_tab = "Settings"
            st.rerun()
    
        # Version info
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem;">
            <p style="color: #888; font-size: 0.75rem;">SOPRA v2.1.0</p>
            <p style="color: #666; font-size: 0.65rem;">SAE On-Premise Risk Assessment</p>
        </div>
        """, unsafe_allow_html=True)

    # Main content area
    if st.session_state.opra_active_tab == "Dashboard":
        render_dashboard()
    elif st.session_state.opra_active_tab == "Remediation Templates":
        render_remediation_templates_picker()
    elif st.session_state.opra_active_tab == "Assessment Scripts":
        render_assessment_scripts_page()
    elif st.session_state.opra_active_tab == "Category Details":
        render_category_details()
    elif st.session_state.opra_active_tab == "Metric Details":
        render_metric_details()
    elif st.session_state.opra_active_tab in ("Data Collection & Ingestion", "Run Security Assessment"):
        render_assessment_page()
    elif st.session_state.opra_active_tab == "Reports":
        render_reports_page()
    elif st.session_state.opra_active_tab == "Vulnerability Management":
        from sopra.isso.ai_remed_ui import render_ai_remediation_dashboard
        render_ai_remediation_dashboard()
    elif st.session_state.opra_active_tab == "SSP Generator":
        # SSP & POA&M tabbed view: Generate SSP | POA&Ms | Risk Acceptance
        st.markdown("## 📋 SSP & POA&M")
        tab_gen_ssp, tab_poams, tab_risk_acceptance = st.tabs(["📜 Generate SSP", "📋 POA&Ms", "⚖️ Risk Acceptance"])
        with tab_gen_ssp:
            render_ssp_generator()
        with tab_poams:
            render_poam_tracker()
        with tab_risk_acceptance:
            render_risk_acceptance()
    elif st.session_state.opra_active_tab == "AI Assistant":
        render_ai_assistant()
    elif st.session_state.opra_active_tab == "Settings":
        render_settings_page()

if __name__ == "__main__":
    main()
