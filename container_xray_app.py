"""
BeeKeeper — Automated Container Security Platform
==================================================
AI-powered container vulnerability scanning. JFrog Xray–style capabilities
for enterprises without managed container tooling.

Run: streamlit run container_xray_app.py
"""
import base64
import re
import streamlit as st
from pathlib import Path
import time

from container_xray.scanner import scan_image, ScanResult, VulnFinding, scanner_available
from container_xray.ai_engine import (
    ai_scan_summary,
    ai_remediation_for_finding,
    ai_remediation_for_cve,
    ai_prioritization,
    ai_policy_recommendations,
    ai_sbom_narrative,
)
st.set_page_config(
    page_title="BeeKeeper",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Logo path
LOGO_PATH = Path(__file__).resolve().parent / "container_xray" / "assets" / "beekeeper_logo.png"

# ═══════════════════════════════════════════════════════════════════════════════
# WOW FACTOR: Dark cyberpunk theme
# ═══════════════════════════════════════════════════════════════════════════════
BEEKEEPER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Base dark theme */
:root {
  --bk-bg: #0a0e17;
  --bk-surface: #111827;
  --bk-surface-elevated: #1a2332;
  --bk-border: #2d3a4f;
  --bk-teal: #00d4aa;
  --bk-teal-dim: #00a884;
  --bk-gold: #f0b429;
  --bk-blue: #3b82f6;
  --bk-critical: #ef4444;
  --bk-high: #f97316;
  --bk-medium: #eab308;
  --bk-low: #22c55e;
  --bk-text: #e2e8f0;
  --bk-text-dim: #94a3b8;
}

/* Override Streamlit — force dark background, ensure text contrast */
.stApp, .stApp > div, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > div,
.main, .main .block-container {
  background: var(--bk-bg) !important;
  background-color: var(--bk-bg) !important;
}
.main .block-container { padding: 2rem 3rem; max-width: 1400px; }
/* Main content text — light on dark (Dashboard, Scan) */
.main p, .main span, .main label, .main .stMarkdown, .main [data-testid="stMarkdown"] { color: var(--bk-text) !important; }
.main input, .main textarea { background: var(--bk-surface) !important; color: var(--bk-text) !important; border-color: var(--bk-border) !important; }

/* Hide default elements */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* Sidebar: dark theme for visibility (match main content) */
section[data-testid="stSidebar"],
[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div {
  background: var(--bk-surface) !important;
  background-color: #111827 !important;
}
[data-testid="stSidebar"] {
  border-right: 1px solid var(--bk-border) !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
  color: var(--bk-text) !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  color: var(--bk-teal) !important;
  font-weight: 700 !important;
}
[data-testid="stSidebar"] hr {
  border-color: var(--bk-border) !important;
  opacity: 0.8 !important;
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stRadio span,
[data-testid="stSidebar"] .stRadio p {
  color: var(--bk-text) !important;
  font-weight: 600 !important;
}
[data-testid="stSidebar"] .stRadio div[data-baseweb="radio"] {
  color: var(--bk-teal) !important;
}
[data-testid="stSidebar"] [role="radio"] {
  border-color: var(--bk-teal-dim) !important;
  background: var(--bk-surface-elevated) !important;
}
[data-testid="stSidebar"] [role="radio"][aria-checked="true"] {
  background: var(--bk-teal) !important;
  border-color: var(--bk-teal) !important;
}

/* Splash */
.splash-wrap {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center;
  padding: 1rem;
  background: #e5e7eb;
  z-index: 9999;
}
.splash-inner {
  display: flex; flex-direction: column; align-items: center;
  gap: 1.5rem; padding: 2rem;
}
.splash-inner .splash-enter-btn {
  text-decoration: none; display: inline-block;
  font-family: 'Orbitron', sans-serif; font-size: 1.1rem; font-weight: 700;
  padding: 1rem 3rem; background: linear-gradient(135deg, var(--bk-teal) 0%, var(--bk-teal-dim) 100%);
  color: var(--bk-bg); border: none; border-radius: 8px;
  cursor: pointer; transition: all 0.3s ease;
  box-shadow: 0 0 25px rgba(0,212,170,0.4);
}
.splash-inner .splash-enter-btn:hover {
  transform: scale(1.05); box-shadow: 0 0 40px rgba(0,212,170,0.6);
}
.splash-logo { max-width: 520px; margin-bottom: 1.5rem; filter: drop-shadow(0 0 30px rgba(0,212,170,0.3)); }
.splash-enter-btn {
  font-family: 'Orbitron', sans-serif; font-size: 1.1rem; font-weight: 700;
  padding: 1rem 3rem; margin-top: 2rem;
  background: linear-gradient(135deg, var(--bk-teal) 0%, var(--bk-teal-dim) 100%);
  color: var(--bk-bg); border: none; border-radius: 8px;
  cursor: pointer; transition: all 0.3s ease;
  box-shadow: 0 0 25px rgba(0,212,170,0.4);
}
.splash-enter-btn:hover {
  transform: scale(1.05); box-shadow: 0 0 40px rgba(0,212,170,0.6);
}
/* Target form submit in splash */
.splash-wrap .stForm button {
  font-family: 'Orbitron', sans-serif !important; font-size: 1.1rem !important; font-weight: 700 !important;
  padding: 1rem 3rem !important; margin-top: 1rem !important;
  background: linear-gradient(135deg, var(--bk-teal) 0%, var(--bk-teal-dim) 100%) !important;
  color: var(--bk-bg) !important; border: none !important; border-radius: 8px !important;
  box-shadow: 0 0 25px rgba(0,212,170,0.4) !important;
  transition: all 0.3s ease !important;
}
.splash-wrap .stForm button:hover {
  transform: scale(1.05) !important; box-shadow: 0 0 40px rgba(0,212,170,0.6) !important;
}

/* Glow pulse for splash logo */
@keyframes logo-glow {
  0%, 100% { filter: drop-shadow(0 0 25px rgba(0,212,170,0.3)); }
  50% { filter: drop-shadow(0 0 45px rgba(0,212,170,0.5)); }
}
.splash-wrap img { animation: logo-glow 3s ease-in-out infinite; }
/* Bring splash content (logo, form) above the overlay - they are sibling blocks */
[data-testid="stVerticalBlock"] > div:has(.splash-wrap) ~ div,
[data-testid="block-container"] > div:has(.splash-wrap) ~ div {
  position: relative; z-index: 10000 !important;
}

/* Hero */
.hero {
  background: linear-gradient(135deg, rgba(0,212,170,0.06) 0%, rgba(59,130,246,0.04) 100%);
  border: 1px solid var(--bk-border); border-radius: 12px;
  padding: 2rem; margin-bottom: 2rem;
  position: relative; overflow: hidden;
}
.hero::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0;
  height: 2px; background: linear-gradient(90deg, transparent, var(--bk-teal), transparent);
  opacity: 0.6;
}
.hero-title { font-family: 'Orbitron', sans-serif; font-size: 1.8rem; font-weight: 700;
  color: var(--bk-teal); margin-bottom: 0.5rem;
  text-shadow: 0 0 20px rgba(0,212,170,0.3); }
.hero-sub { font-family: 'JetBrains Mono', monospace; color: var(--bk-text-dim);
  font-size: 0.9rem; letter-spacing: 0.05em; }

/* Terminal input */
.terminal-box {
  background: var(--bk-surface); border: 1px solid var(--bk-border);
  border-radius: 8px; padding: 1rem 1.25rem;
  font-family: 'JetBrains Mono', monospace; margin-bottom: 1rem;
}
.terminal-prompt { color: var(--bk-teal); font-size: 0.9rem; margin-bottom: 0.5rem; }
.terminal-prompt::before { content: '>$ '; opacity: 0.8; }

/* Metric cards */
.bk-metric {
  background: var(--bk-surface); border: 1px solid var(--bk-border);
  border-radius: 10px; padding: 1.25rem; text-align: center;
  transition: all 0.3s ease;
}
.bk-metric:hover { border-color: var(--bk-teal-dim); transform: translateY(-2px); }
.bk-metric-critical { border-left: 4px solid var(--bk-critical); }
.bk-metric-high { border-left: 4px solid var(--bk-high); }
.bk-metric-medium { border-left: 4px solid var(--bk-medium); }
.bk-metric-low { border-left: 4px solid var(--bk-low); }
.bk-metric-num { font-family: 'Orbitron', sans-serif; font-size: 2.2rem; font-weight: 700; }
.bk-metric-label { font-size: 0.8rem; color: var(--bk-text-dim); text-transform: uppercase;
  letter-spacing: 0.1em; margin-top: 0.25rem; }

/* Clean scan celebration */
.clean-scan {
  background: linear-gradient(135deg, rgba(34,197,94,0.15) 0%, rgba(0,212,170,0.08) 100%);
  border: 1px solid var(--bk-low); border-radius: 12px;
  padding: 3rem; text-align: center; margin: 2rem 0;
}
.clean-scan-icon { font-size: 4rem; margin-bottom: 1rem; }
.clean-scan-title { font-family: 'Orbitron', sans-serif; font-size: 1.8rem;
  color: var(--bk-teal); font-weight: 700; }
.clean-scan-sub { color: var(--bk-text-dim); margin-top: 0.5rem; }

/* Finding cards */
.bk-finding {
  background: var(--bk-surface); border-radius: 8px;
  border-left: 4px solid var(--bk-border); padding: 1rem 1.25rem;
  margin: 0.75rem 0; transition: all 0.2s ease;
}
.bk-finding:hover { background: var(--bk-surface-elevated); }
.bk-finding-critical { border-left-color: var(--bk-critical); }
.bk-finding-high { border-left-color: var(--bk-high); }
.bk-finding-medium { border-left-color: var(--bk-medium); }
.bk-finding-low { border-left-color: var(--bk-low); }
.bk-finding-id { font-family: 'JetBrains Mono', monospace; color: var(--bk-teal);
  font-size: 0.85rem; }
.bk-finding-pkg { font-weight: 600; color: var(--bk-text); }

/* AI intel panel */
.ai-intel {
  background: linear-gradient(180deg, rgba(0,212,170,0.05) 0%, transparent 100%);
  border: 1px solid var(--bk-border); border-radius: 10px;
  padding: 1.5rem; margin: 1rem 0;
}
.ai-intel-header { font-family: 'Orbitron', sans-serif; font-size: 1rem;
  color: var(--bk-gold); text-transform: uppercase; letter-spacing: 0.15em;
  margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
.ai-intel-header::before { content: '◆'; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bk-surface) !important;
  border-radius: 8px !important;
  padding: 0.25rem !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'Orbitron', sans-serif !important;
  color: var(--bk-text-dim) !important;
}
.stTabs [aria-selected="true"] {
  background: var(--bk-teal) !important;
  color: var(--bk-bg) !important;
  border-radius: 6px !important;
}

/* Buttons */
.stButton > button {
  font-family: 'Orbitron', sans-serif !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--bk-teal) 0%, var(--bk-teal-dim) 100%) !important;
  color: var(--bk-bg) !important;
  border: none !important;
  box-shadow: 0 0 20px rgba(0,212,170,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 0 30px rgba(0,212,170,0.5) !important;
  transform: translateY(-1px) !important;
}

/* Scanning animation */
@keyframes pulse-scan {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.scanning { animation: pulse-scan 1.5s ease-in-out infinite; }

/* Text */
p, span, label { color: var(--bk-text) !important; }
h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: var(--bk-text) !important; }

/* Xray-style dashboard */
.xray-header-bar {
  background: linear-gradient(90deg, var(--bk-teal) 0%, var(--bk-teal-dim) 100%);
  color: var(--bk-bg); padding: 1rem 1.5rem; border-radius: 8px 8px 0 0;
  font-family: 'Orbitron', sans-serif; font-size: 1.4rem; font-weight: 700;
}
.xray-section {
  background: var(--bk-surface); border: 1px solid var(--bk-border);
  border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1.5rem;
}
.xray-section-title { font-family: 'Orbitron', sans-serif; font-size: 0.85rem;
  color: var(--bk-teal); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.75rem; }
.xray-alert { padding: 0.75rem; margin: 0.5rem 0; background: var(--bk-surface-elevated);
  border-radius: 6px; border-left: 3px solid var(--bk-border); }
.xray-alert-critical { border-left-color: var(--bk-critical); }
.xray-alert-major { border-left-color: var(--bk-high); }
.xray-alert-minor { border-left-color: var(--bk-medium); }
.xray-metric-card { text-align: center; padding: 1rem; background: var(--bk-surface-elevated);
  border-radius: 8px; border: 1px solid var(--bk-border); }
.xray-metric-num { font-family: 'Orbitron', sans-serif; font-size: 2rem; font-weight: 700;
  color: var(--bk-teal); }
.xray-metric-label { font-size: 0.75rem; color: var(--bk-text-dim); text-transform: uppercase;
  margin-top: 0.25rem; }
.xray-vuln { padding: 0.75rem; margin: 0.5rem 0; background: var(--bk-surface-elevated);
  border-radius: 6px; }
.xray-vuln-id { font-family: 'JetBrains Mono', monospace; color: var(--bk-teal);
  font-weight: 600; font-size: 0.9rem; }
.xray-sev-tag { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 4px;
  font-weight: 600; display: inline-block; margin-left: 0.5rem; }
.xray-sev-critical { background: var(--bk-critical); color: white; }
.xray-sev-high { background: var(--bk-high); color: white; }
.xray-sev-minor { background: var(--bk-medium); color: var(--bk-bg); }
.xray-pkg { padding: 0.4rem 0; font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem; }
.xray-pkg-ok { color: var(--bk-low); }
.xray-pkg-vuln { color: var(--bk-critical); }
.xray-tech-chip { display: inline-block; padding: 0.35rem 0.75rem; margin: 0.25rem;
  background: var(--bk-surface-elevated); border: 1px solid var(--bk-border);
  border-radius: 6px; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace; }

/* Enterprise Simulation — 3-pane command center */
.ent-hero {
  background: linear-gradient(135deg, rgba(239,68,68,0.12) 0%, rgba(0,212,170,0.08) 50%, rgba(59,130,246,0.1) 100%);
  border: 1px solid var(--bk-border); border-radius: 12px;
  padding: 2rem; margin-bottom: 2rem;
  text-align: center;
  box-shadow: 0 0 60px rgba(239,68,68,0.15);
}
.ent-hero-num { font-family: 'Orbitron', sans-serif; font-size: 3.5rem; font-weight: 900;
  background: linear-gradient(135deg, #ef4444, #f97316); -webkit-background-clip: text;
  -webkit-text-fill-color: transparent; background-clip: text;
  text-shadow: 0 0 40px rgba(239,68,68,0.4);
  letter-spacing: 0.02em;
  animation: ent-pulse 3s ease-in-out infinite; }
@keyframes ent-pulse {
  0%, 100% { filter: drop-shadow(0 0 20px rgba(239,68,68,0.5)); opacity: 1; }
  50% { filter: drop-shadow(0 0 35px rgba(239,68,68,0.8)); opacity: 0.95; }
}
.ent-hero-label { font-family: 'JetBrains Mono', monospace; color: var(--bk-text-dim);
  font-size: 1rem; text-transform: uppercase; letter-spacing: 0.2em; margin-top: 0.5rem; }
.ent-pane {
  background: var(--bk-surface); border: 1px solid var(--bk-border);
  border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem;
  min-height: 280px; transition: all 0.3s ease;
}
.ent-pane:hover { border-color: var(--bk-teal-dim); box-shadow: 0 0 25px rgba(0,212,170,0.1); }
.ent-pane-title { font-family: 'Orbitron', sans-serif; font-size: 0.9rem;
  color: var(--bk-teal); text-transform: uppercase; letter-spacing: 0.15em;
  margin-bottom: 1rem; border-bottom: 1px solid var(--bk-border); padding-bottom: 0.5rem; }
.ent-mkt-card {
  background: var(--bk-surface-elevated); border: 1px solid var(--bk-border);
  border-radius: 8px; padding: 0.9rem; margin: 0.5rem 0;
  cursor: pointer; transition: all 0.2s ease;
}
.ent-mkt-card:hover { border-color: var(--bk-teal); transform: translateX(4px);
  box-shadow: 0 0 15px rgba(0,212,170,0.2); }
.ent-mkt-card.in-cart { border-color: var(--bk-teal); background: rgba(0,212,170,0.08); }
.ent-sev-bar { height: 8px; border-radius: 4px; margin: 0.25rem 0; }
.ent-impact { font-family: 'Orbitron', sans-serif; color: var(--bk-teal); font-weight: 700; }
</style>
"""

st.markdown(BEEKEEPER_CSS, unsafe_allow_html=True)


def _extract_cve(text: str) -> str | None:
    """Extract first CVE-ID from text (e.g. CVE-2022-41741)."""
    m = re.search(r"CVE-\d{4}-\d{4,7}", text)
    return m.group(0) if m else None


def render_xray_dashboard():
    """JFrog Xray–style dashboard with simulation data."""
    from container_xray.test_data import (
        get_recent_alerts,
        get_recent_vulnerabilities,
        get_recent_packages,
        get_metrics,
        get_sync_status,
        SUPPORTED_TECHNOLOGIES,
    )
    st.session_state.setdefault("remediation_cache", {})
    alerts = get_recent_alerts()
    vulns = get_recent_vulnerabilities()
    packages = get_recent_packages()
    scanned, indexed, total_alerts = get_metrics()
    sync = get_sync_status()

    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, rgba(0,212,170,0.15) 0%, transparent 100%);
                border-bottom: 1px solid var(--bk-border); padding: 1rem 0; margin: -1rem 0 1.5rem 0;">
      <p style="font-family: Orbitron; font-size: 1.6rem; font-weight: 700; color: var(--bk-teal); margin: 0;">Welcome to BeeKeeper</p>
      <p style="font-family: JetBrains Mono; font-size: 0.85rem; color: var(--bk-text-dim); margin: 0.25rem 0 0;">BeeKeeper Version: 1.0 (Simulation Mode)</p>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        # My Recent Alerts (expandable → auto-remediation)
        st.markdown('<p style="font-family: Orbitron; font-size: 1rem; color: var(--bk-text); margin-bottom: 0.75rem;">📋 MY RECENT ALERTS</p>', unsafe_allow_html=True)
        cache = st.session_state.setdefault("remediation_cache", {})
        for i, a in enumerate(alerts):
            sev_color = {"Critical": "#ef4444", "Major": "#f97316", "Minor": "#eab308"}.get(a.severity, "#94a3b8")
            cve_match = re.search(r"CVE-\d{4}-\d{4,7}", a.message)
            cve_id = cve_match.group(0) if cve_match else f"Alert-{i}"
            desc = a.message[:300] if not cve_match else a.message
            cache_key = f"alert_{i}_{a.message[:50]}"
            label = f"[{a.severity}] {a.message[:80]}{'...' if len(a.message) > 80 else ''}"
            with st.expander(label, expanded=False):
                st.markdown(f"**{a.timestamp}** · {a.issue_count} issue(s)  \n\n{a.message}")
                st.markdown("---\n**🤖 Auto-Remediation**")
                if cache_key not in cache:
                    with st.spinner("Generating remediation..."):
                        cache[cache_key] = ai_remediation_for_cve(cve_id, desc, a.severity, context=a.message[:200])
                st.markdown(cache[cache_key])

        # Metrics
        st.markdown('<p style="font-family: Orbitron; font-size: 1rem; color: var(--bk-text); margin: 1.5rem 0 0.75rem;">📊 METRICS</p>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        for col, (val, label) in zip([m1, m2, m3], [(scanned, "Scanned Images"), (indexed, "Indexed Packages"), (total_alerts, "My Alerts")]):
            with col:
                st.markdown(f"""
                <div class="bk-metric">
                  <p class="bk-metric-num" style="color: var(--bk-teal);">{val}</p>
                  <p class="bk-metric-label">{label}</p>
                </div>
                """, unsafe_allow_html=True)

        # Sync Status
        st.markdown('<p style="font-family: Orbitron; font-size: 1rem; color: var(--bk-text); margin: 1.5rem 0 0.75rem;">🔄 SYNC STATUS</p>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: var(--bk-surface); border: 1px solid var(--bk-border); border-radius: 8px; padding: 1rem;">
          <p style="color: var(--bk-text-dim); font-size: 0.85rem; margin: 0 0 0.5rem;">Syncing data from global database · {100 - sync['percent']}% remaining</p>
          <div style="background: var(--bk-bg); border-radius: 4px; height: 8px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, var(--bk-teal), var(--bk-teal-dim)); height: 100%; width: {sync['percent']}%;"></div>
          </div>
          <p style="color: var(--bk-text-dim); font-size: 0.75rem; margin: 0.5rem 0 0;">{sync['percent']}% ({sync['current']}/{sync['total']})</p>
        </div>
        """, unsafe_allow_html=True)

        # Supported Technologies
        st.markdown('<p style="font-family: Orbitron; font-size: 1rem; color: var(--bk-text); margin: 1.5rem 0 0.75rem;">🔧 SUPPORTED TECHNOLOGIES</p>', unsafe_allow_html=True)
        techs = "  ".join([f'<span style="background: var(--bk-surface); padding: 0.35rem 0.6rem; border-radius: 4px; font-size: 0.8rem; color: var(--bk-teal);">{t[0]}</span>' for t in SUPPORTED_TECHNOLOGIES])
        st.markdown(f'<div style="margin-bottom: 1rem;">{techs}</div>', unsafe_allow_html=True)

    with col_right:
        # Recent Vulnerabilities (expandable → auto-remediation)
        st.markdown('<p style="font-family: Orbitron; font-size: 1rem; color: var(--bk-text); margin-bottom: 0.75rem;">⚠️ RECENT VULNERABILITIES</p>', unsafe_allow_html=True)
        cache = st.session_state.setdefault("remediation_cache", {})
        for v in vulns:
            cache_key = f"vuln_{v.cve_id}"
            label = f"[{v.severity}] {v.cve_id} — {v.description[:70]}{'...' if len(v.description) > 70 else ''}"
            with st.expander(label, expanded=False):
                st.markdown(f"**{v.cve_id}** ({v.severity})  \n\n{v.description}")
                st.markdown("---\n**🤖 Auto-Remediation**")
                if cache_key not in cache:
                    with st.spinner("Generating remediation..."):
                        cache[cache_key] = ai_remediation_for_cve(v.cve_id, v.description, v.severity)
                st.markdown(cache[cache_key])

        # Recent Packages
        st.markdown('<p style="font-family: Orbitron; font-size: 1rem; color: var(--bk-text); margin: 1.5rem 0 0.75rem;">📦 RECENT PACKAGES</p>', unsafe_allow_html=True)
        pkg_search = st.text_input("Search packages", placeholder="Search query...", key="pkg_search", label_visibility="collapsed")
        pkg_list = [p for p in packages if not pkg_search or pkg_search.lower() in p.name.lower()]
        for p in pkg_list[:12]:
            status_color = "#22c55e" if p.status == "Normal" else "#ef4444"
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0; border-bottom: 1px solid var(--bk-border);">
              <span style="font-family: JetBrains Mono; font-size: 0.85rem; color: var(--bk-text);">{p.name}</span>
              <span style="background: {status_color}; color: white; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.7rem;">{p.status}</span>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SPLASH
# ═══════════════════════════════════════════════════════════════════════════════
if "splash_passed" not in st.session_state:
    st.session_state.splash_passed = False
st.session_state.setdefault("current_page", "dashboard")
st.session_state.setdefault("current_page", "dashboard")

if not st.session_state.splash_passed:
    # Handle Enter via query param (link click in single HTML block)
    qp = st.query_params
    if qp.get("enter") == "1":
        st.session_state.splash_passed = True
        st.session_state.current_page = "enterprise"
        if "enter" in qp:
            del qp["enter"]
        st.rerun()
    # Single HTML block — logo and Enter link inside overlay (no separate Streamlit blocks hidden behind it)
    img_html = ""
    if LOGO_PATH.exists():
        try:
            b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
            img_html = f'<img src="data:image/png;base64,{b64}" class="splash-logo" alt="BeeKeeper" style="max-width:520px;margin:0 auto 1.5rem;display:block;" />'
        except Exception:
            img_html = '<p class="hero-title">BeeKeeper</p><p class="hero-sub">Automated Container Security Platform</p>'
    else:
        img_html = '<p class="hero-title">BeeKeeper</p><p class="hero-sub">Automated Container Security Platform</p>'
    enter_url = "?enter=1"
    st.markdown(f"""
    <div class="splash-wrap">
      <div class="splash-inner">
        {img_html}
        <a href="{enter_url}" class="splash-enter-btn">ENTER PLATFORM</a>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR: Navigation (Xray-style)
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    sidebar_logo_html = ""
    if LOGO_PATH.exists():
        try:
            b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
            sidebar_logo_html = f'<div style="display: flex; align-items: center; gap: 0.5rem; font-size: 1.25rem; font-weight: 700; color: var(--bk-teal); margin-bottom: 0;"><img src="data:image/png;base64,{b64}" alt="" style="height: 1em; width: auto; flex-shrink: 0; object-fit: contain;" /><span>BeeKeeper</span></div>'
        except Exception:
            pass
    if not sidebar_logo_html:
        sidebar_logo_html = '<div style="font-size: 1.25rem; font-weight: 700; color: var(--bk-teal);">🛡️ BeeKeeper</div>'
    st.markdown(sidebar_logo_html, unsafe_allow_html=True)
    st.markdown("---")
    nav_options = ["📊 Dashboard", "🏢 Enterprise Simulation", "🔍 Scan Image"]
    nav_default = 1 if st.session_state.get("current_page") == "enterprise" else (2 if st.session_state.get("current_page") == "scan" else 0)
    page = st.radio(
        "Navigate",
        nav_options,
        index=min(nav_default, len(nav_options) - 1),
        label_visibility="collapsed",
        key="nav_page",
    )
    if "Dashboard" in page:
        st.session_state.current_page = "dashboard"
    elif "Enterprise" in page:
        st.session_state.current_page = "enterprise"
    else:
        st.session_state.current_page = "scan"
    st.markdown("---")
    if "simulation_run" not in st.session_state:
        st.session_state.simulation_run = False

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD: Xray-style layout with simulation data
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.current_page == "dashboard":
    if st.button("🔄 Run Simulation", type="primary", key="run_sim"):
        st.session_state.simulation_run = True
        st.rerun()
    render_xray_dashboard()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# ENTERPRISE SIMULATION: Inventory | 857K Vulnerabilities | Remediation Marketplace
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.current_page == "enterprise":
    # Light background for Enterprise page — force light theme, dark text
    st.markdown("""
    <style>
    /* Enterprise: force light background — body/html ensures it wins */
    body, html, .stApp, .stApp > div, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > div,
    .main, .main .block-container, section[data-testid="stMain"] > div {
      background: #f8fafc !important; background-color: #f8fafc !important;
    }
    section[data-testid="stSidebar"], [data-testid="stSidebar"] > div { background: #f1f5f9 !important; }
    .ent-hero { background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(241,245,249,0.95) 100%) !important; border-color: #cbd5e1 !important; }
    .ent-pane, .ent-pane-title { color: #1e293b !important; }
    .ent-pane { background: #ffffff !important; border-color: #e2e8f0 !important; }
    .ent-sev-card .ent-sev-num { color: var(--sev-color) !important; }
    /* Main content — dark text for contrast on light bg */
    .main p, .main span, .main label, .main div, .main a { color: #1e293b !important; }
    .main .stMarkdown, .main [data-testid="stMarkdown"] { color: #1e293b !important; }
    .main .bk-metric-label { color: #64748b !important; }
    .main .bk-metric-num { color: #0d9488 !important; }
    /* Streamlit inputs — visible borders and dark text */
    .main input, .main textarea { background: #ffffff !important; color: #1e293b !important; border: 1px solid #94a3b8 !important; }
    .main [data-testid="stTextInput"] input, .main [data-testid="stTextInput"] input::placeholder { background: #ffffff !important; color: #1e293b !important; border: 1px solid #94a3b8 !important; }
    .main [data-testid="stSelectbox"] div, .main [data-testid="stSelectbox"] span { color: #1e293b !important; background: #ffffff !important; border: 1px solid #94a3b8 !important; }
    .main .stExpander label, .main [data-testid="stExpander"] label { color: #1e293b !important; }
    .main button { color: #1e293b !important; border: 1px solid #94a3b8 !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div { color: #1e293b !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #0d9488 !important; }
    [data-testid="stSidebar"] [role="radio"] { border-color: #94a3b8 !important; background: #ffffff !important; }
    [data-testid="stSidebar"] [role="radio"][aria-checked="true"] { background: #00d4aa !important; border-color: #00d4aa !important; }
    </style>
    """, unsafe_allow_html=True)
    st.session_state.setdefault("remediation_cart", set())
    from container_xray.test_data import (
        TOTAL_ENTERPRISE_VULNS,
        get_all_inventory_components,
        get_enterprise_vuln_breakdown,
        get_enterprise_top_vulns,
        get_enterprise_remediation_options,
        get_enterprise_kpis,
        get_enterprise_risk_heatmap,
        get_enterprise_action_breakdown,
    )
    breakdown = get_enterprise_vuln_breakdown()
    all_components = get_all_inventory_components()
    top_vulns = get_enterprise_top_vulns()
    remediation_options = get_enterprise_remediation_options()
    kpis = get_enterprise_kpis()
    heatmap_data = get_enterprise_risk_heatmap()
    action_breakdown = get_enterprise_action_breakdown()
    cart = st.session_state.remediation_cart

    # 4 KPI cards (top row) — light theme, strong contrast
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 1.25rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
          <p style="font-size: 0.75rem; color: #1e293b; text-transform: uppercase; letter-spacing: 0.1em; margin: 0; font-weight: 600;">% Risks</p>
          <p style="font-family: Orbitron; font-size: 2rem; font-weight: 700; color: #047857; margin: 0.25rem 0;">{kpis['pct_risks']}%</p>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 1.25rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
          <p style="font-size: 0.75rem; color: #1e293b; text-transform: uppercase; letter-spacing: 0.1em; margin: 0; font-weight: 600;">Total of Risks</p>
          <p style="font-family: Orbitron; font-size: 2rem; font-weight: 700; color: #047857; margin: 0.25rem 0;">{kpis['total_risks']:,}</p>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 1.25rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
          <p style="font-size: 0.75rem; color: #1e293b; text-transform: uppercase; letter-spacing: 0.1em; margin: 0; font-weight: 600;">Risk Analysis Progress</p>
          <p style="font-family: Orbitron; font-size: 2rem; font-weight: 700; color: #047857; margin: 0.25rem 0;">{kpis['risk_analysis_progress']}%</p>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 1.25rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
          <p style="font-size: 0.75rem; color: #1e293b; text-transform: uppercase; letter-spacing: 0.1em; margin: 0; font-weight: 600;">Response Progress for Risks</p>
          <p style="font-family: Orbitron; font-size: 2rem; font-weight: 700; color: #047857; margin: 0.25rem 0;">{kpis['response_progress']}%</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # 3 chart panels: Risk Rating donut | Heat map | Action Plan donut
    import plotly.graph_objects as go
    c1, c2, c3 = st.columns(3)

    with c1:
        total_sev = sum(breakdown.values())
        donut_labels = ["Critical", "High", "Medium", "Low", "Info"]
        donut_values = [
            breakdown["critical"], breakdown["high"], breakdown["medium"],
            breakdown["low"], breakdown["info"],
        ]
        donut_colors = ["#dc2626", "#ea580c", "#eab308", "#16a34a", "#64748b"]
        fig1 = go.Figure(data=[go.Pie(
            labels=donut_labels, values=donut_values, hole=0.55,
            marker={"colors": donut_colors},
            textinfo="label+percent", textposition="outside",
        )])
        fig1.update_layout(
            title={"text": "RISK RATING BREAKDOWN", "font": {"size": 12, "family": "Orbitron", "color": "#059669"}},
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font={"color": "#1e293b", "size": 11}, showlegend=True, legend={"orientation": "h", "yanchor": "top"},
            height=300, margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig1, use_container_width=True, key="ent_risk_donut")

    with c2:
        rows, cols = heatmap_data["rows"], heatmap_data["cols"]
        matrix = heatmap_data["matrix"]
        max_val = max(max(r) for r in matrix)
        fig2 = go.Figure(data=go.Heatmap(
            z=matrix, x=cols, y=rows,
            colorscale=[[0, "#22c55e"], [0.4, "#eab308"], [0.7, "#f97316"], [1, "#ef4444"]],
            text=[[str(v) for v in row] for row in matrix], texttemplate="%{text}", textfont={"size": 11},
        ))
        fig2.update_layout(
            title={"text": "RISK HEAT MAP", "font": {"size": 12, "family": "Orbitron", "color": "#059669"}},
            xaxis={"title": "Likelihood", "tickangle": -30, "tickfont": {"color": "#1e293b"}},
            yaxis={"title": "Severity", "autorange": "reversed", "tickfont": {"color": "#1e293b"}},
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font={"color": "#1e293b", "size": 11}, height=300, margin=dict(l=10, r=10, t=40, b=60),
        )
        st.plotly_chart(fig2, use_container_width=True, key="ent_heatmap")

    with c3:
        act_labels = list(action_breakdown.keys())
        act_values = list(action_breakdown.values())
        act_colors = ["#0f766e", "#0d9488", "#14b8a6", "#2dd4bf"]
        fig3 = go.Figure(data=[go.Pie(
            labels=act_labels, values=act_values, hole=0.55,
            marker={"colors": act_colors},
            textinfo="label+percent", textposition="outside",
        )])
        fig3.update_layout(
            title={"text": "ACTION PLAN BREAKDOWN", "font": {"size": 12, "family": "Orbitron", "color": "#059669"}},
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font={"color": "#1e293b", "size": 11}, showlegend=True, legend={"orientation": "h", "yanchor": "top"},
            height=300, margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig3, use_container_width=True, key="ent_action_donut")

    # Hero: 857,284 vulnerabilities (compact) — light theme
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(239,68,68,0.08) 0%, rgba(0,212,170,0.06) 50%, rgba(59,130,246,0.06) 100%); border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
      <p style="font-family: Orbitron; font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #dc2626, #ea580c); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">{TOTAL_ENTERPRISE_VULNS:,}</p>
      <p style="font-family: JetBrains Mono; color: #64748b; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.15em; margin-top: 0.5rem;">Vulnerabilities across unpatched clusters • images • repos • YAML</p>
      <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.5rem;">Inventory & patch • or decommission</p>
    </div>
    """, unsafe_allow_html=True)

    # 3-pane layout
    pane1, pane2, pane3 = st.tabs(["📋 INVENTORY", "⚠️ VULNERABILITIES", "🛒 REMEDIATION MARKETPLACE"])

    with pane1:
        st.markdown('<p class="ent-pane-title">~1,500 Components — Clusters • Docker Images • Repos • YAML</p>', unsafe_allow_html=True)
        inv_f1, inv_f2 = st.columns([3, 1])
        with inv_f1:
            inv_search = st.text_input("Search components", placeholder="Filter by name, type...", key="inv_search", label_visibility="collapsed")
        with inv_f2:
            inv_type = st.selectbox("Filter", ["All", "Clusters", "Docker Images", "Repos", "YAML"], key="inv_type")
        type_map = {"All": None, "Clusters": "cluster", "Docker Images": "image", "Repos": "repo", "YAML": "yaml"}
        filter_type = type_map.get(inv_type, None)
        filtered = [
            c for c in all_components
            if (not inv_search or inv_search.lower() in c.get("name", "").lower() or inv_search.lower() in c.get("summary", "").lower())
            and (filter_type is None or c.get("type") == filter_type)
        ]
        st.caption(f"Showing {len(filtered):,} of {len(all_components):,} components • Click to view details")
        for comp in filtered:
            t = comp.get("type", "")
            name = comp.get("name", "")
            summary = comp.get("summary", "")
            status = comp.get("status", "unpatched")
            vuln_count = comp.get("vuln_count", 0)
            details = comp.get("details", "")
            if isinstance(details, dict):
                details = "\n".join(f"{k}: {v}" for k, v in details.items())
            sev_color = "#ef4444" if status == "unpatched" else "#eab308"
            type_icon = {"cluster": "🖥️", "image": "🐳", "repo": "📦", "yaml": "⚙️"}.get(t, "•")
            label = f"{type_icon} {name} — {summary}"
            with st.expander(label, expanded=False):
                st.markdown(f"**{name}** ({t})  \n{summary}\n\n---\n**Details**\n```\n{details}\n```")

    with pane2:
        st.markdown('<p class="ent-pane-title">857,284 Vulnerabilities — Severity & Top CVEs</p>', unsafe_allow_html=True)
        sev_cols = st.columns(5)
        sev_data = [
            ("Critical", breakdown["critical"], "#ef4444"),
            ("High", breakdown["high"], "#f97316"),
            ("Medium", breakdown["medium"], "#eab308"),
            ("Low", breakdown["low"], "#22c55e"),
            ("Info", breakdown["info"], "#94a3b8"),
        ]
        for col, (label, count, color) in zip(sev_cols, sev_data):
            with col:
                pct = 100 * count / TOTAL_ENTERPRISE_VULNS
                st.markdown(f"""
                <div class="ent-sev-card" style="--sev-color: {color}; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; text-align: center; border-left: 4px solid {color}; box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
                  <p class="ent-sev-num" style="font-family: Orbitron; font-size: 1.5rem; font-weight: 700; margin: 0;">{count:,}</p>
                  <p style="font-size: 0.75rem; color: #334155; font-weight: 600; margin: 0.25rem 0;">{label}</p>
                  <div style="background: #f1f5f9; height: 6px; border-radius: 3px; margin-top: 0.5rem;">
                    <div style="background: {color}; height: 100%; width: {min(100, pct)}%; border-radius: 3px;"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("**Top CVEs by affected assets**")
        for v in top_vulns[:8]:
            sev_c = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308"}.get(v.severity, "#94a3b8")
            st.markdown(f"""
            <div class="ent-pane ent-cve-card" style="padding: 0.75rem; margin: 0.4rem 0;">
              <span style="font-family: JetBrains Mono; color: #0d9488; font-weight: 600;">{v.cve_id}</span>
              <span style="background: {sev_c}; color: white; font-size: 0.65rem; padding: 0.1rem 0.4rem; border-radius: 4px; margin-left: 0.5rem;">{v.severity}</span>
              <p style="color: #1e293b; font-size: 0.85rem; margin: 0.35rem 0; font-weight: 500;">{v.description}</p>
              <p style="color: #334155; font-size: 0.75rem; margin: 0.15rem 0 0;">{v.affected_count:,} affected • Exploitability: {v.exploitability}</p>
            </div>
            """, unsafe_allow_html=True)

    with pane3:
        st.markdown('<p class="ent-pane-title">Remediation Marketplace — Pick systems to patch or decommission</p>', unsafe_allow_html=True)
        for opt in remediation_options:
            in_cart = opt["id"] in cart
            action_color = {"patch": "#00d4aa", "upgrade": "#3b82f6", "decommission": "#eab308"}[opt["action"]]
            btn_key = f"mkt_{opt['id']}"
            if st.button(
                f"{'✓ ' if in_cart else ''}{opt['name']} — **{opt['vulns_removed']:,}** vulns removed",
                key=btn_key,
                use_container_width=True,
                type="primary" if in_cart else "secondary",
            ):
                if in_cart:
                    cart.discard(opt["id"])
                else:
                    cart.add(opt["id"])
                st.rerun()
            with st.container():
                st.caption(f"Action: {opt['action'].upper()} • Effort: {opt['effort']}")

        cart_total = sum(o["vulns_removed"] for o in remediation_options if o["id"] in cart)
        if cart:
            st.markdown("---")
            st.success(f"**Cart:** {len(cart)} items → **{cart_total:,}** vulnerabilities would be remediated")
            if st.button("🚀 Execute Remediation Plan", type="primary", key="exec_remediate"):
                st.balloons()
                st.success("Remediation plan queued. Patches and decommissions scheduled.")
                cart.clear()
                st.rerun()
        st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# SCAN PAGE: Live container scan
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <p class="hero-title">🔍 Scan Image</p>
  <p class="hero-sub">Enter a container image to run a live vulnerability scan with Trivy/Grype</p>
</div>
""", unsafe_allow_html=True)

available, scanner_name = scanner_available()
if not available:
    st.warning("⚠️ **No scanner detected.** Install [Trivy](https://trivy.dev) or [Grype](https://github.com/anchore/grype). Windows: `scoop install trivy`")
else:
    st.markdown(f'<p style="color: var(--bk-teal); font-family: JetBrains Mono;">✓ Scanner: <strong>{scanner_name}</strong></p>', unsafe_allow_html=True)

st.markdown('<p class="terminal-prompt">Container image to scan</p>', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])
with col1:
    image_ref = st.text_input(
        "image",
        placeholder="nginx:latest | alpine:3.18 | myregistry.io/app:v1",
        label_visibility="collapsed",
        key="img_ref",
    )
with col2:
    run_scan = st.button("🔍 SCAN", type="primary", use_container_width=True)

# Session state
for k in ["scan_result", "ai_summary", "ai_priorities", "ai_policy", "ai_sbom"]:
    if k not in st.session_state:
        st.session_state[k] = None

if run_scan and image_ref.strip():
    scan_placeholder = st.empty()
    with scan_placeholder.container():
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
          <p style="font-family: Orbitron; font-size: 1.2rem; color: var(--bk-teal);" class="scanning">▸ SCANNING IMAGE...</p>
          <p style="color: var(--bk-text-dim); font-size: 0.9rem;">Pulling layers • Analyzing packages • CVE lookup</p>
        </div>
        """, unsafe_allow_html=True)
    result = scan_image(image_ref.strip())
    scan_placeholder.empty()
    st.session_state.scan_result = result

    if not result.success:
        st.error(result.error_message)
        st.session_state.scan_result = None
    else:
        st.balloons()
        st.success(f"**Scan complete:** `{result.image}`")

result: ScanResult | None = st.session_state.scan_result
if result is None:
    st.markdown("""
    <div class="ai-intel" style="text-align: center; padding: 3rem;">
      <p class="hero-sub">Enter a container image above and click <strong style="color: var(--bk-teal);">SCAN</strong></p>
      <p style="color: var(--bk-text-dim); font-size: 0.85rem; margin-top: 1rem;">e.g. nginx:latest • alpine:3.18 • ubuntu:22.04</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ═══════════════════════════════════════════════════════════════════════════════
if not result.findings:
    st.markdown("""
    <div class="clean-scan">
      <p class="clean-scan-icon">✓</p>
      <p class="clean-scan-title">IMAGE CLEAN</p>
      <p class="clean-scan-sub">No vulnerabilities detected — {image}</p>
    </div>
    """.replace("{image}", result.image), unsafe_allow_html=True)
    st.balloons()
    st.stop()

# Risk gauge with threat level
import plotly.graph_objects as go
total = len(result.findings)
critical = result.total_critical
high = result.total_high
risk_score = min(100, (critical * 25 + high * 15 + result.total_medium * 5) / max(1, total) * 2)
if risk_score < 40:
    threat_level, threat_color = "LOW", "#00d4aa"
elif risk_score < 70:
    threat_level, threat_color = "ELEVATED", "#eab308"
else:
    threat_level, threat_color = "CRITICAL", "#ef4444"

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=round(risk_score),
    domain={"x": [0, 1], "y": [0, 1]},
    number={"suffix": "", "font": {"size": 42, "family": "Orbitron"}},
    gauge={
        "axis": {"range": [0, 100], "tickwidth": 1},
        "bar": {"color": threat_color},
        "bgcolor": "#111827",
        "borderwidth": 2,
        "bordercolor": "#2d3a4f",
        "steps": [
            {"range": [0, 40], "color": "rgba(0,212,170,0.2)"},
            {"range": [40, 70], "color": "rgba(234,179,8,0.2)"},
            {"range": [70, 100], "color": "rgba(239,68,68,0.2)"},
        ],
        "threshold": {"line": {"color": threat_color, "width": 4}, "value": risk_score},
    },
    title={"text": f"RISK SCORE · {threat_level}", "font": {"size": 14, "family": "Orbitron", "color": threat_color}},
))
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    font={"color": "#94a3b8"},
    height=240,
    margin=dict(l=20, r=20, t=60, b=20),
)
st.plotly_chart(fig, use_container_width=True)
threat_label = "LOW" if risk_score < 40 else "ELEVATED" if risk_score < 70 else "CRITICAL"
threat_color = "#00d4aa" if risk_score < 40 else "#eab308" if risk_score < 70 else "#ef4444"
st.markdown(f'<p style="font-family: Orbitron; font-size: 1rem; color: {threat_color}; margin: -0.75rem 0 0.5rem; text-align: center;">◉ THREAT LEVEL: {threat_label}</p>', unsafe_allow_html=True)

# Scanned image badge
st.markdown(f'<p style="font-family: JetBrains Mono; font-size: 0.85rem; color: var(--bk-text-dim); margin: -0.5rem 0 1rem;">▸ {result.image}</p>', unsafe_allow_html=True)

# Metric row
st.markdown('<p style="font-family: Orbitron; font-size: 1rem; margin: 1.5rem 0 0.75rem;">FINDINGS BREAKDOWN</p>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
metrics_data = [
    (result.total_critical, "CRITICAL", "bk-metric-critical", "#ef4444"),
    (result.total_high, "HIGH", "bk-metric-high", "#f97316"),
    (result.total_medium, "MEDIUM", "bk-metric-medium", "#eab308"),
    (result.total_low, "LOW", "bk-metric-low", "#22c55e"),
    (total, "TOTAL", "bk-metric", "#94a3b8"),
]
for col, (val, label, cls, color) in zip([c1, c2, c3, c4, c5], metrics_data):
    with col:
        st.markdown(f"""
        <div class="bk-metric {cls}">
          <p class="bk-metric-num" style="color: {color};">{val}</p>
          <p class="bk-metric-label">{label}</p>
        </div>
        """, unsafe_allow_html=True)

# Tabs
st.markdown("<br>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["📋 FINDINGS", "🤖 AI INTELLIGENCE", "📜 POLICY", "🔗 SUPPLY CHAIN"])

with tab1:
    severity_filter = st.multiselect(
        "Filter",
        ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "UNKNOWN"],
        default=["CRITICAL", "HIGH", "MEDIUM"],
        key="sev_filter",
    )
    filtered = [f for f in result.findings if f.severity in severity_filter] if severity_filter else result.findings

    for f in filtered[:50]:
        cls = f"bk-finding-{f.severity.lower()}" if f.severity in ("CRITICAL","HIGH","MEDIUM","LOW") else "bk-finding"
        with st.expander(f"**{f.vuln_id}** — {f.package} {f.installed_version}  `[{f.severity}]`"):
            st.markdown(f"**Fixed in:** `{f.fixed_version or 'N/A'}`")
            if f.title:
                st.markdown(f"*{f.title}*")
            if f.description:
                st.caption((f.description or "")[:400] + ("..." if len(f.description or "") > 400 else ""))
            if f.primary_url:
                st.markdown(f"[Reference]({f.primary_url})")
            if st.button(f"AI Remediation", key=f"rem_{f.vuln_id}_{f.package}".replace(".", "_")[:100]):
                with st.spinner("Analyzing..."):
                    rem = ai_remediation_for_finding(f)
                st.markdown("---")
                st.markdown("**🤖 AI Remediation**")
                st.markdown(rem)

with tab2:
    if st.button("Generate AI analysis", type="primary", key="ai_btn"):
        with st.spinner("AI analyzing..."):
            st.session_state.ai_summary = ai_scan_summary(result)
            st.session_state.ai_priorities = ai_prioritization(result)
            st.rerun()

    if st.session_state.ai_summary:
        st.markdown("""
        <div class="ai-intel">
          <p class="ai-intel-header">Executive Summary</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.ai_summary)
        if st.session_state.ai_priorities:
            st.markdown("---")
            st.markdown("**AI Prioritization**")
            for p in st.session_state.ai_priorities[:10]:
                ex = "🔴 Exploitable" if p.get("exploitable_likely") else "🟢 Lower risk"
                st.markdown(f"- **{p.get('vuln_id')}** — {p.get('priority_score')}/10 — {p.get('reason')} {ex}")

with tab3:
    if st.button("Policy recommendations", key="policy_btn"):
        with st.spinner("Generating..."):
            st.session_state.ai_policy = ai_policy_recommendations(result)
    if st.session_state.ai_policy:
        st.markdown(st.session_state.ai_policy)

with tab4:
    if st.button("Supply chain narrative", key="sbom_btn"):
        with st.spinner("Generating..."):
            st.session_state.ai_sbom = ai_sbom_narrative(result)
    if st.session_state.ai_sbom:
        st.markdown(st.session_state.ai_sbom)

st.markdown("---")
st.caption("BeeKeeper — Trivy/Grype • Bedrock/Ollama • CONTAINER_XRAY_AIRGAPPED for air-gapped")
