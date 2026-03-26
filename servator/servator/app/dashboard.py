"""
Servator Command Center - Store Security Control Center

Professional operational intelligence dashboard for loss prevention.
Phases 1-4: LLM actions, vision, predictive analytics, agentic workflows.
"""

import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Logo path (relative to servator package root)
ROOT = Path(__file__).resolve().parent.parent.parent
LOGO_PATH = ROOT / "assets" / "servator_logo.png"

st.set_page_config(
    page_title="Servator - Operational Intelligence",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Control center aesthetic - professional, subtle, non-confrontational
st.markdown("""
<style>
    /* Main container - dark, calm */
    .stApp { background: linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); }
    
    /* Header - premium, understated */
    .control-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.25rem;
        border-left: 3px solid #64748b;
        box-shadow: 0 4px 24px rgba(0,0,0,0.2);
    }
    .control-header h1 { color: #f8fafc; font-weight: 600; letter-spacing: -0.02em; margin: 0; }
    .control-header .tagline { color: #94a3b8; font-size: 0.9rem; margin: 0.25rem 0 0 0; }
    .control-header .privacy-note { color: #64748b; font-size: 0.75rem; margin-top: 0.5rem; }
    
    /* Insight cards - meaningful, not alarming */
    .insight-card {
        background: rgba(51, 65, 85, 0.5);
        border: 1px solid rgba(100, 116, 139, 0.3);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin: 0.5rem 0;
        transition: border-color 0.2s;
    }
    .insight-card:hover { border-color: rgba(100, 116, 139, 0.5); }
    .insight-card .title { color: #e2e8f0; font-weight: 600; font-size: 0.95rem; }
    .insight-card .value { color: #38bdf8; font-size: 1.5rem; font-weight: 700; margin: 0.25rem 0; }
    .insight-card .trend-up { color: #4ade80; }
    .insight-card .trend-down { color: #38bdf8; }
    .insight-card .subtext { color: #64748b; font-size: 0.8rem; }
    
    /* Recommended action - actionable, not punitive */
    .action-card {
        background: rgba(30, 58, 138, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.25);
        border-radius: 8px;
        padding: 0.9rem 1rem;
        margin: 0.4rem 0;
    }
    .action-card .action { color: #93c5fd; font-weight: 500; }
    .action-card .reason { color: #94a3b8; font-size: 0.85rem; margin-top: 0.2rem; }
    
    /* Event row - neutral language */
    .event-row {
        background: rgba(51, 65, 85, 0.35);
        border-radius: 6px;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        border-left: 3px solid #475569;
    }
    .event-row .type { color: #94a3b8; font-size: 0.8rem; }
    .event-row .desc { color: #e2e8f0; }
    .event-row .time { color: #64748b; font-size: 0.75rem; }
    
    /* Section headers */
    .section-title { color: #cbd5e1; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# Header - logo + branding
header_col1, header_col2 = st.columns([1, 4])
with header_col1:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
with header_col2:
    st.markdown("""
    <div class="control-header" style="padding-left: 0;">
        <h1>Servator</h1>
        <p class="tagline">Operational Intelligence · Loss Prevention Analytics</p>
        <p class="privacy-note">Supports store operations through pattern analysis. No customer identification. Back-office only.</p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
        st.markdown("---")
    st.markdown("### Location")
    store = st.selectbox(
        "Store",
        ["Store 1001 - Downtown", "Store 1002 - Mall", "Store 1003 - Highway"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("### Time Range")
    date_range = st.selectbox(
        "Range",
        ["Last 24 hours", "Last 7 days", "Last 30 days"],
        label_visibility="collapsed",
        key="range",
    )
    store_id = "1001" if "1001" in store else ("1002" if "1002" in store else "1003")
    st.markdown("---")
    st.markdown("### Modules")
    st.markdown("• SCO Vision")
    st.markdown("• Shelf Monitor")
    st.markdown("• Exit Verification")
    st.markdown("• Predictive Analytics")
    st.markdown("• Internal Patterns")

# --- Phase 3: Predictive metrics ---
try:
    from servator.analytics.predictive import get_executive_metrics, get_risk_by_category, get_activity_by_hour
    metrics = get_executive_metrics(store_id, date_range)
except Exception:
    metrics = {
        "operational_events": 14,
        "events_trend_pct": -12,
        "est_loss_prevented": 2340,
        "loss_trend_pct": 8,
        "process_exceptions": 6,
        "focus_areas": ["Aisle 12", "Lane 3"],
        "focus_count": 2,
        "risk_index": 68,
        "risk_trend": -5,
    }

# --- Executive Summary (Wow factor - at a glance) ---
st.markdown('<p class="section-title">Executive Summary</p>', unsafe_allow_html=True)
e1, e2, e3, e4, e5 = st.columns(5)
trend_down = f'<span class="trend-down">↓{abs(metrics["events_trend_pct"])}% vs prior day</span>' if metrics["events_trend_pct"] < 0 else f'<span class="trend-up">↑{metrics["events_trend_pct"]}%</span>'
with e1:
    st.markdown(f"""
    <div class="insight-card">
        <div class="title">Operational Events</div>
        <div class="value">{metrics["operational_events"]}</div>
        <div class="subtext">Last 24h · {trend_down}</div>
    </div>
    """, unsafe_allow_html=True)
with e2:
    st.markdown(f"""
    <div class="insight-card">
        <div class="title">Est. Loss Prevented</div>
        <div class="value">${metrics["est_loss_prevented"]:,}</div>
        <div class="subtext">This week · <span class="trend-up">↑{metrics["loss_trend_pct"]}%</span></div>
    </div>
    """, unsafe_allow_html=True)
with e3:
    st.markdown(f"""
    <div class="insight-card">
        <div class="title">Process Exceptions</div>
        <div class="value">{metrics["process_exceptions"]}</div>
        <div class="subtext">SCO · Exit · Inventory</div>
    </div>
    """, unsafe_allow_html=True)
with e4:
    focus_str = " · ".join(metrics["focus_areas"][:2]) if metrics["focus_areas"] else "—"
    st.markdown(f"""
    <div class="insight-card">
        <div class="title">Focus Areas</div>
        <div class="value">{metrics["focus_count"]}</div>
        <div class="subtext">{focus_str}</div>
    </div>
    """, unsafe_allow_html=True)
with e5:
    rt = metrics["risk_trend"]
    rt_str = f'<span class="trend-down">↓{abs(rt)} pts</span>' if rt < 0 else f'<span class="trend-up">↑{rt} pts</span>'
    st.markdown(f"""
    <div class="insight-card">
        <div class="title">Risk Index</div>
        <div class="value">{metrics["risk_index"]}</div>
        <div class="subtext">0–100 · {rt_str}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Phase 1: LLM Recommended Actions ---
st.markdown('<p class="section-title">Recommended Actions</p>', unsafe_allow_html=True)
events_data = [
    {"type": "SCO Process", "desc": "Lane 3 · Bagging sequence variance", "time": "2 min ago"},
    {"type": "Shelf Activity", "desc": "Aisle 12 (Beverages) · Unusual movement pattern", "time": "15 min ago"},
    {"type": "SCO Process", "desc": "Lane 1 · Rapid void sequence", "time": "32 min ago"},
    {"type": "Predictive", "desc": "Baby formula · Elevated risk window", "time": "1 hr ago"},
    {"type": "Shelf Activity", "desc": "Aisle 8 (Health) · Activity variance", "time": "2 hrs ago"},
    {"type": "Exit Verification", "desc": "Exit 2 · Receipt-cart variance (low confidence)", "time": "2 hrs ago"},
]
risk_data = {"high_risk_categories": metrics.get("focus_areas", ["Beverages", "Baby & Infant"]), "risk_index": metrics["risk_index"]}

if st.button("🤖 Generate AI Recommendations", key="ai_recommend"):
    try:
        from servator.ai_engine import ai_recommend_actions
        with st.spinner("AI is analyzing context..."):
            actions = ai_recommend_actions(events_data, risk_data, store, date_range)
            st.session_state["_servator_actions"] = actions
            st.rerun()
    except Exception as e:
        st.error(f"AI unavailable: {e}")

actions = st.session_state.get("_servator_actions")
if not actions:
    actions = [
        {"action": "Consider visibility at Aisle 12 (Beverages) during 6–8 PM", "reason": "Above-average activity variance in last 3 days. Peak hour pattern."},
        {"action": "Review SCO Lane 3 transaction logs", "reason": "2 process exceptions in past hour. May indicate training opportunity."},
        {"action": "Exit 2: Receipt variance flagged at 2:34 PM", "reason": "Cart-receipt mismatch. Low confidence—possible scanner error."},
        {"action": "Baby formula inventory check recommended", "reason": "High-risk category. Predictive score 88. No recent physical count."},
        {"action": "Staffing alignment: Thursday 4–6 PM", "reason": "Historical peak for operational events. Current schedule at baseline."},
    ]

col_left, col_right = st.columns([1, 1])
for i, a in enumerate(actions):
    col = col_left if i % 2 == 0 else col_right
    with col:
        st.markdown(f"""
        <div class="action-card">
            <div class="action">{a.get("action", a)}</div>
            <div class="reason">{a.get("reason", "")}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Operational Events", "Analytics", "SCO Vision", "Exit Verification", "Investigation Agent", "Configuration",
])

with tab1:
    st.markdown("### Recent Operational Events")
    st.caption("Pattern-based alerts. Neutral language. Back-office only.")

    # Phase 1: AI event summary
    if st.button("🤖 Generate AI Event Summary", key="ai_summary"):
        try:
            from servator.ai_engine import ai_summarize_events
            with st.spinner("Generating summary..."):
                summary = ai_summarize_events(events_data, store)
                if summary:
                    st.session_state["_servator_summary"] = summary
                    st.rerun()
        except Exception:
            pass
    if st.session_state.get("_servator_summary"):
        st.info(st.session_state["_servator_summary"])

    for e in events_data:
        st.markdown(f"""
        <div class="event-row">
            <span class="type">{e["type"]}</span>
            <div class="desc">{e["desc"]}</div>
            <span class="time">{e["time"]}</span>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("### Risk Analytics (Phase 3: Prophet + Anomaly Detection)")
    st.caption("Category-level and time-based patterns. Real predictive models.")

    try:
        risk_df = get_risk_by_category(store_id)
        activity_df = get_activity_by_hour(store_id)
    except Exception:
        risk_df = pd.DataFrame({
            "Category": ["Beverages", "Baby & Infant", "Health & OTC", "Meat & Dairy", "Personal Care"],
            "Risk Index": [92, 88, 85, 78, 72],
            "Events (7d)": [12, 8, 6, 4, 3],
            "Trend": ["↑", "→", "↓", "→", "↓"],
        })
        activity_df = pd.DataFrame({"Hour": [f"{h}:00" for h in range(6, 24)], "Activity Index": [50 + (h % 6) * 8 for h in range(6, 24)]})

    st.dataframe(risk_df, use_container_width=True, hide_index=True)
    st.markdown("**Activity by Hour**")
    st.bar_chart(activity_df.set_index("Hour"))

with tab3:
    st.markdown("### SCO Vision (Phase 2: AI Image Analysis)")
    st.caption("Upload a self-checkout camera image for AI anomaly detection.")

    uploaded = st.file_uploader("Upload SCO camera image (JPEG/PNG)", type=["jpg", "jpeg", "png"], key="sco_upload")
    if uploaded:
        img_bytes = uploaded.read()
        fmt = "jpeg" if uploaded.type in ("image/jpeg", "image/jpg") else "png"
        col_img, col_result = st.columns([1, 1])
        with col_img:
            st.image(img_bytes, caption="Uploaded image", use_container_width=True)
        if st.button("🔍 Analyze with AI Vision", key="sco_analyze"):
            try:
                from servator.ai_engine import ai_analyze_sco_image
                with st.spinner("AI is analyzing image..."):
                    result = ai_analyze_sco_image(img_bytes, fmt)
                    st.session_state["_sco_result"] = result
                    st.rerun()
            except Exception as e:
                st.error(str(e))
        if st.session_state.get("_sco_result"):
            r = st.session_state["_sco_result"]
            with col_result:
                st.markdown("**AI Analysis**")
                st.markdown(f"**Summary:** {r.get('summary', 'N/A')}")
                st.markdown(f"**Confidence:** {r.get('confidence', 'N/A')}")
                st.markdown(f"**Recommendation:** {r.get('recommendation', 'N/A')}")
                if r.get("anomalies"):
                    st.markdown("**Observed:**")
                    for a in r["anomalies"]:
                        st.markdown(f"- {a}")

with tab4:
    st.markdown("### Exit Verification")
    st.caption("Cart-receipt alignment. Supports accuracy without customer interaction.")

    ex1, ex2 = st.columns(2)
    with ex1:
        st.metric("Exits Monitored", 4, "All lanes")
        st.metric("Variances Today", 2, "Low confidence")
    with ex2:
        st.metric("Accuracy Rate", "99.2%", "+0.3%")
        st.metric("False Positive Rate", "0.8%", "↓")

    st.markdown("**Recent Exit Events**")
    st.markdown("""
    <div class="event-row">
        <span class="type">Exit 2</span>
        <div class="desc">Receipt-cart variance · 2:34 PM · Low confidence (possible scanner skip)</div>
    </div>
    <div class="event-row">
        <span class="type">Exit 1</span>
        <div class="desc">All clear · Last 4 hours</div>
    </div>
    """, unsafe_allow_html=True)

with tab5:
    st.markdown("### Investigation Agent (Phase 4)")
    st.caption("Agentic workflow: AI synthesizes context into investigation summary.")

    alert_type = st.selectbox("Alert Type", ["SCO Process", "Shelf Activity", "Exit Verification", "Predictive"], key="inv_type")
    alert_desc = st.text_area("Alert Description", value="Lane 3 · Bagging sequence variance · 2 process exceptions in past hour", key="inv_desc")
    if st.button("🔍 Run Investigation", key="inv_run"):
        try:
            from servator.ai_engine import ai_investigate_alert
            context = {
                "store": store,
                "recent_transactions": ["TXN-001: 3 items, 2 voids", "TXN-002: 5 items, 1 void"],
                "video_timestamp": "14:32:15",
                "inventory_check": "Baby formula: last count 2 days ago",
            }
            with st.spinner("Investigation agent analyzing..."):
                result = ai_investigate_alert(alert_type, alert_desc, context)
                st.session_state["_inv_result"] = result
                st.rerun()
        except Exception as e:
            st.error(str(e))
    if st.session_state.get("_inv_result"):
        r = st.session_state["_inv_result"]
        st.markdown("**Investigation Summary**")
        st.markdown(f"**Likely Cause:** {r.get('likely_cause', 'N/A')}")
        st.markdown("**Evidence to Review:**")
        for e in r.get("evidence_to_review", []):
            st.markdown(f"- {e}")
        st.markdown(f"**Recommended Action:** {r.get('recommended_action', 'N/A')}")
        st.markdown(f"**Priority:** {r.get('priority', 'N/A')}")

with tab6:
    st.markdown("### Configuration")
    st.info("Store and module settings. Contact administrator.")

st.markdown("---")
with st.container():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=60)
    st.markdown(
        "<p style='text-align: center; color: #475569; font-size: 0.75rem;'>Servator · Operational Intelligence · Loss Prevention · Back-Office Only</p>",
        unsafe_allow_html=True,
    )
