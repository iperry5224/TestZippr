"""SOPRA ISSO Toolkit — Pop-out Hub Page"""
import streamlit as st
from datetime import datetime

from sopra.persistence import load_results_from_file
from sopra.isso.poam import render_poam_tracker
from sopra.isso.risk_acceptance import render_risk_acceptance
from sopra.isso.evidence import render_evidence_collection
from sopra.isso.inheritance import render_control_inheritance
from sopra.isso.scheduling import render_assessment_scheduling
from sopra.isso.approvals import render_approval_workflow
from sopra.isso.stig_import import render_stig_import
from sopra.isso.incidents import render_incident_correlation
from sopra.isso.ai_remed_ui import render_ai_remediation_dashboard
from sopra.isso.crosswalk_ui import render_crosswalk_page

def render_isso_toolkit_page():
    """Standalone ISSO Toolkit pop-out page with sidebar navigation."""
    # Load assessment results from file if not in session (pop-out runs in separate tab)
    if not st.session_state.get("opra_assessment_results"):
        file_results = load_results_from_file()
        if file_results:
            st.session_state.opra_assessment_results = file_results

    # Initialize ISSO sub-tab state
    if "isso_active_tab" not in st.session_state:
        st.session_state.isso_active_tab = "Home"

    # Inject dark-ops styling (hide main sidebar)
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"], .stApp {
            background: linear-gradient(160deg, #0d1117 0%, #0f1923 40%, #131b2e 100%) !important;
        }
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] span,
        [data-testid="stAppViewContainer"] li,
        [data-testid="stAppViewContainer"] td,
        [data-testid="stAppViewContainer"] th,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] h4 { color: #c8d6e5 !important; }
        [data-testid="stMetricValue"] { color: #00d9ff !important; }
        @keyframes scan-sweep {
            0% { transform: translateX(-100%); opacity: 0; }
            10% { opacity: 1; } 90% { opacity: 1; }
            100% { transform: translateX(250%); opacity: 0; }
        }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: rgba(13,17,23,0.4); }
        ::-webkit-scrollbar-thumb { background: rgba(0,217,255,0.25); border-radius: 3px; }
        /* Sidebar styling for ISSO window */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0f1a 0%, #0d1420 100%) !important;
        }
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label { color: #c8d6e5 !important; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 0.8rem 0.5rem;">
            <div style="font-size: 0.5rem; letter-spacing: 3px; color: rgba(0,217,255,0.6); text-transform: uppercase;">SOPRA</div>
            <h3 style="color: #00d9ff; margin: 0.2rem 0; font-size: 1.1rem;">🛡️ ISSO Toolkit</h3>
            <p style="color: #4a6a8a; font-size: 0.65rem;">Information System Security Officer Tools</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        isso_nav = [
            ("Home", "🏠"), ("Control Crosswalk", "🔄"), ("AI Remediation", "🧠"),
            ("POA&M Tracker", "📋"), ("Risk Acceptance", "⚖️"),
            ("Evidence Collection", "📎"), ("Control Inheritance", "🏛️"),
            ("Assessment Schedule", "📅"), ("Approvals", "✍️"),
            ("STIG Import", "📥"), ("Incident Correlation", "🔗")
        ]

        for name, icon in isso_nav:
            if st.button(f"{icon} {name}", use_container_width=True,
                        type="primary" if st.session_state.isso_active_tab == name else "secondary",
                        key=f"isso_nav_{name}"):
                st.session_state.isso_active_tab = name
                st.rerun()

    # Route to the selected ISSO tool
    tab = st.session_state.isso_active_tab

    if tab == "Home":
        _render_isso_home()
    elif tab == "Control Crosswalk":
        render_crosswalk_page()
    elif tab == "AI Remediation":
        render_ai_remediation_dashboard()
    elif tab == "POA&M Tracker":
        render_poam_tracker()
    elif tab == "Risk Acceptance":
        render_risk_acceptance()
    elif tab == "Evidence Collection":
        render_evidence_collection()
    elif tab == "Control Inheritance":
        render_control_inheritance()
    elif tab == "Assessment Schedule":
        render_assessment_scheduling()
    elif tab == "Approvals":
        render_approval_workflow()
    elif tab == "STIG Import":
        render_stig_import()
    elif tab == "Incident Correlation":
        render_incident_correlation()


def _render_isso_home():
    """ISSO Toolkit landing page with tool cards."""
    # Animated header
    st.markdown(
        '<div style="position:relative;text-align:center;padding:1.2rem 1.5rem;margin-bottom:1.2rem;background:linear-gradient(145deg,rgba(0,217,255,0.05),rgba(0,255,136,0.03));border:1px solid rgba(0,217,255,0.2);border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.3);overflow:hidden;">'
        '<div style="position:absolute;top:0;left:0;width:40%;height:100%;background:linear-gradient(90deg,transparent,rgba(0,217,255,0.05),transparent);animation:scan-sweep 4s ease-in-out infinite;"></div>'
        '<div style="font-size:0.5rem;letter-spacing:4px;color:rgba(0,217,255,0.6);text-transform:uppercase;">&#9670; INFORMATION SYSTEM SECURITY OFFICER &#9670;</div>'
        '<h2 style="color:#fff;margin:0.3rem 0;font-size:1.4rem;font-weight:700;text-shadow:0 0 25px rgba(0,217,255,0.3);">ISSO Toolkit</h2>'
        '<p style="color:#4a6a8a;margin:0;font-size:0.75rem;letter-spacing:1.5px;">ATO Documentation &bull; Risk Management &bull; Continuous Monitoring &bull; Audit Readiness</p>'
        '</div>',
        unsafe_allow_html=True
    )

    tools = [
        ("🔄", "Control Crosswalk", "Bidirectional NIST 800-53 and CIS v8 mapping with coverage stats and CSV export.", "#00d9ff"),
        ("🧠", "AI Remediation", "AI-powered attack chain analysis, remediation plans, validation scripts, impact analysis, and ticket generation.", "#a855f7"),
        ("📋", "POA&M Tracker", "Track remediation milestones, due dates, responsible parties, and overdue alerts.", "#e94560"),
        ("⚖️", "Risk Acceptance", "Document accepted risks, operational justifications, and compensating controls.", "#ffc107"),
        ("📎", "Evidence Collection", "Attach audit evidence (screenshots, configs, logs) to findings.", "#00d9ff"),
        ("🏛️", "Control Inheritance", "Classify controls as inherited, common, or system-specific.", "#00ff88"),
        ("📅", "Assessment Schedule", "Define reassessment cadence with automated overdue detection.", "#a855f7"),
        ("✍️", "Approvals", "Record AO/ISSO sign-off on risk acceptances, POA&M closures, and ATOs.", "#f59e0b"),
        ("📥", "STIG Import", "Import DISA STIG Viewer or CIS Benchmark scan results.", "#06b6d4"),
        ("🔗", "Incident Correlation", "Link assessment findings to actual security incidents.", "#ef4444"),
    ]

    # Render tool cards in a 2-column grid
    for i in range(0, len(tools), 2):
        c1, c2 = st.columns(2)
        for col, idx in [(c1, i), (c2, i + 1)]:
            if idx < len(tools):
                icon, name, desc, color = tools[idx]
                with col:
                    st.markdown(
                        '<div style="background:rgba(13,17,23,0.7);backdrop-filter:blur(12px);border:1px solid ' + color + '30;border-radius:14px;padding:1rem;margin-bottom:0.5rem;min-height:120px;transition:border-color 0.3s,box-shadow 0.3s;cursor:default;">'
                        '<div style="font-size:1.6rem;margin-bottom:0.3rem;">' + icon + '</div>'
                        '<div style="color:' + color + ';font-weight:700;font-size:1rem;margin-bottom:0.3rem;">' + name + '</div>'
                        '<div style="color:#6b839e;font-size:0.8rem;line-height:1.4;">' + desc + '</div>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                    if st.button(f"Open {name}", use_container_width=True, key=f"isso_card_{name}"):
                        st.session_state.isso_active_tab = name
                        st.rerun()


