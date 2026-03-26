"""
SOPRA Utilities — Risk calculation, data aggregation, chart builders, and helpers.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import base64
import time

from sopra_controls import get_control_by_id
from sopra.theme import (
    CHART_BG, CHART_PLOT_BG, CHART_FONT_COLOR, CHART_GRID_COLOR, CHART_GRID_LIGHT,
    CHART_BORDER_COLOR, CHART_LEGEND, COLOR_PASSED, COLOR_FAILED, COLOR_NOT_ASSESSED,
    COLOR_CRITICAL, COLOR_HIGH, COLOR_MEDIUM, COLOR_LOW,
    PIE_COLORS_STATUS, BAR_COLORS_SEV, SEV_ORDER, SEV_COLORS,
    FAMILY_ABBREV, OPRA_CATEGORIES, chart_layout
)

@st.cache_data(ttl=300)
def load_demo_data():
    """Load all demo CSV files once and cache the result."""
    demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_csv_data")
    if not os.path.exists(demo_dir):
        return [], pd.DataFrame()
    
    demo_files = sorted([f for f in os.listdir(demo_dir) if f.endswith('.csv')])
    all_dfs = []
    file_paths = []
    for fname in demo_files:
        fpath = os.path.join(demo_dir, fname)
        file_paths.append(fpath)
        try:
            all_dfs.append(pd.read_csv(fpath))
        except Exception:
            pass
    
    combined = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    return file_paths, combined


def aggregate_findings(findings):
    """Single-pass aggregation over findings list. Returns a dict of all computed metrics."""
    total = len(findings)
    passed = 0
    failed = 0
    not_assessed = 0
    cat_passed = {}
    cat_failed = {}
    cat_total = {}
    sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    family_counts = {}
    heatmap_data = {}
    failed_findings = []
    passed_findings = []
    
    for f in findings:
        status = f.get("status", "Not Assessed")
        category = f.get("category", "Unknown")
        severity = f.get("severity")
        family = f.get("family", "Unknown")
        
        cat_total[category] = cat_total.get(category, 0) + 1
        
        if status == "Passed":
            passed += 1
            cat_passed[category] = cat_passed.get(category, 0) + 1
            passed_findings.append(f)
        elif status == "Failed":
            failed += 1
            cat_failed[category] = cat_failed.get(category, 0) + 1
            failed_findings.append(f)
            if severity and severity in sev_counts:
                sev_counts[severity] += 1
            # Heatmap
            if severity and category:
                if category not in heatmap_data:
                    heatmap_data[category] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
                if severity in heatmap_data[category]:
                    heatmap_data[category][severity] += 1
        else:
            not_assessed += 1
        
        # Family counts
        if family not in family_counts:
            family_counts[family] = {"Passed": 0, "Failed": 0}
        if status == "Passed":
            family_counts[family]["Passed"] += 1
        elif status == "Failed":
            family_counts[family]["Failed"] += 1
    
    return {
        "total": total, "passed": passed, "failed": failed, "not_assessed": not_assessed,
        "cat_passed": cat_passed, "cat_failed": cat_failed, "cat_total": cat_total,
        "sev_counts": sev_counts, "family_counts": family_counts,
        "heatmap_data": heatmap_data,
        "failed_findings": failed_findings, "passed_findings": passed_findings
    }


def create_status_donut(passed, failed, not_assessed, total, height=320, title="Control Status"):
    """Create a pass/fail/NA donut chart."""
    fig = go.Figure(data=[go.Pie(
        labels=["Passed", "Failed", "Not Assessed"],
        values=[passed, failed, not_assessed],
        hole=0.55,
        marker_colors=PIE_COLORS_STATUS,
        marker_line=dict(color=CHART_BORDER_COLOR, width=2),
        textinfo="label+percent",
        textfont=dict(size=14, color="#ffffff"),
        pull=[0.03, 0.07, 0.03]
    )])
    pct = int(passed / (total or 1) * 100)
    fig.update_layout(**chart_layout(
        height=height,
        title=dict(text=title, font=dict(color=COLOR_PASSED, size=16)) if title != "Control Status" else {},
        annotations=[dict(
            text=f"<b>{pct}%</b><br>Compliant",
            x=0.5, y=0.5, font_size=18, font_color=COLOR_PASSED, showarrow=False
        )]
    ))
    return fig


def create_category_bar(cat_passed, cat_failed, height=None, title="Findings by Category", barmode='stack'):
    """Create a horizontal stacked bar chart of findings by category."""
    all_cats = sorted(set(list(cat_passed.keys()) + list(cat_failed.keys())))
    if not all_cats:
        return None
    # Auto-scale height based on number of categories (min 320, ~28px per bar)
    if height is None:
        height = max(320, len(all_cats) * 28 + 80)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Passed", y=all_cats,
        x=[cat_passed.get(c, 0) for c in all_cats],
        marker_color=COLOR_PASSED, marker_line=dict(color="#00cc6a", width=1), opacity=0.95,
        orientation='h'
    ))
    fig.add_trace(go.Bar(
        name="Failed", y=all_cats,
        x=[cat_failed.get(c, 0) for c in all_cats],
        marker_color=COLOR_FAILED, marker_line=dict(color="#ff5a75", width=1), opacity=0.95,
        orientation='h'
    ))
    fig.update_layout(**chart_layout(
        height=height,
        title=dict(text=title, font=dict(color=COLOR_PASSED, size=16)),
        barmode=barmode,
        yaxis=dict(tickfont=dict(size=9, color=CHART_FONT_COLOR), gridcolor=CHART_GRID_LIGHT, zeroline=False, autorange="reversed"),
        xaxis=dict(tickfont=dict(color=CHART_FONT_COLOR), gridcolor=CHART_GRID_COLOR, title="Controls", zeroline=False),
        margin=dict(t=40, b=30, l=170, r=20)
    ))
    return fig


def create_severity_polar(sev_counts, height=320):
    """Create a polar/radar chart of severity distribution."""
    if sum(sev_counts.values()) == 0:
        return None
    fig = go.Figure(data=go.Barpolar(
        r=[sev_counts.get(s, 0) for s in SEV_ORDER],
        theta=SEV_ORDER,
        marker_color=BAR_COLORS_SEV,
        marker_line=dict(color="rgba(255,255,255,0.3)", width=1),
        opacity=0.92
    ))
    fig.update_layout(
        title=dict(text="Severity Radar", font=dict(color=COLOR_PASSED, size=16)),
        paper_bgcolor=CHART_BG,
        polar=dict(
            bgcolor='rgba(22, 36, 64, 0.4)',
            radialaxis=dict(visible=True, color="#8899bb", gridcolor='rgba(0, 217, 255, 0.15)'),
            angularaxis=dict(color=CHART_FONT_COLOR, gridcolor=CHART_GRID_COLOR, linecolor='rgba(0, 217, 255, 0.2)')
        ),
        font_color=CHART_FONT_COLOR, height=height,
        margin=dict(t=40, b=20, l=40, r=40)
    )
    return fig


def create_risk_gauge(score, height=320, title="Risk Score"):
    """Create a risk score gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(suffix="%", font=dict(color=COLOR_PASSED, size=36)),
        title=dict(text=title, font=dict(color=COLOR_PASSED, size=16)) if title else {},
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#8899bb", tickfont=dict(color=CHART_FONT_COLOR)),
            bar=dict(color=COLOR_PASSED),
            bgcolor="rgba(22, 36, 64, 0.5)",
            bordercolor="rgba(0, 217, 255, 0.2)", borderwidth=1,
            steps=[
                dict(range=[0, 40], color="rgba(233, 69, 96, 0.45)"),
                dict(range=[40, 60], color="rgba(255, 107, 107, 0.4)"),
                dict(range=[60, 80], color="rgba(255, 193, 7, 0.4)"),
                dict(range=[80, 100], color="rgba(0, 217, 255, 0.4)")
            ],
            threshold=dict(line=dict(color="#ffffff", width=3), thickness=0.8, value=score)
        )
    ))
    fig.update_layout(**chart_layout(height=height, margin=dict(t=40, b=20, l=40, r=40)))
    return fig


def create_heatmap(heatmap_data, height=300):
    """Create a category vs severity risk heatmap."""
    if not heatmap_data:
        return None
    cats = list(heatmap_data.keys())
    sevs = SEV_ORDER
    z_data = [[heatmap_data[c].get(s, 0) for s in sevs] for c in cats]
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data, x=sevs, y=cats,
        colorscale=[
            [0, '#162440'], [0.2, 'rgba(0, 217, 255, 0.35)'],
            [0.4, 'rgba(255, 193, 7, 0.55)'], [0.65, 'rgba(255, 107, 107, 0.75)'],
            [0.85, 'rgba(233, 69, 96, 0.9)'], [1.0, '#e94560']
        ],
        text=z_data, texttemplate="%{text}",
        textfont=dict(size=15, color="#ffffff"),
        hoverinfo="x+y+z", xgap=3, ygap=3
    ))
    fig.update_layout(**chart_layout(
        height=height,
        xaxis=dict(tickfont=dict(color=CHART_FONT_COLOR, size=12)),
        yaxis=dict(tickfont=dict(color=CHART_FONT_COLOR, size=10)),
        margin=dict(t=20, b=40, l=150, r=20)
    ))
    return fig


FAMILY_ABBREV = {
    "Access Control": "AC",
    "Audit & Accountability": "AU",
    "Audit and Accountability": "AU",
    "Configuration Management": "CM",
    "Contingency Planning": "CP",
    "Identification & Authentication": "IA",
    "Identification and Authentication": "IA",
    "Incident Response": "IR",
    "Maintenance": "MA",
    "Media Protection": "MP",
    "Physical & Environmental Protection": "PE",
    "Physical & Environmental": "PE",
    "Physical and Environmental Protection": "PE",
    "Planning": "PL",
    "Personnel Security": "PS",
    "Risk Assessment": "RA",
    "System & Services Acquisition": "SA",
    "System and Services Acquisition": "SA",
    "System & Communications Protection": "SC",
    "System and Communications Protection": "SC",
    "System & Comm Protection": "SC",
    "System & Information Integrity": "SI",
    "System and Information Integrity": "SI",
    "System & Info Integrity": "SI",
    "Program Management": "PM",
    "Supply Chain Risk Management": "SR",
}


def create_family_bar(family_counts, height=300):
    """Create a horizontal stacked bar chart by control family."""
    if not family_counts:
        return None
    fam_names_raw = list(family_counts.keys())
    fam_names = [f"{FAMILY_ABBREV.get(f, '??')}- {f}" for f in fam_names_raw]
    fam_passed = [family_counts[f]["Passed"] for f in fam_names_raw]
    fam_failed = [family_counts[f]["Failed"] for f in fam_names_raw]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=fam_names, x=fam_passed, name="Passed",
        orientation='h', marker_color=COLOR_PASSED, marker_line=dict(color="#00cc6a", width=1), opacity=0.95
    ))
    fig.add_trace(go.Bar(
        y=fam_names, x=fam_failed, name="Failed",
        orientation='h', marker_color=COLOR_FAILED, marker_line=dict(color="#ff5a75", width=1), opacity=0.95
    ))
    fig.update_layout(**chart_layout(
        height=height, barmode='stack',
        xaxis=dict(title="Controls", tickfont=dict(color=CHART_FONT_COLOR), gridcolor=CHART_GRID_COLOR, zeroline=False),
        yaxis=dict(tickfont=dict(color=CHART_FONT_COLOR, size=10)),
        margin=dict(t=20, b=40, l=150, r=20)
    ))
    return fig


def render_header():
    """Render the SOPRA header with logo"""
    # Try to load the SOPRA logo (check both names)
    _project_root = os.path.dirname(os.path.dirname(__file__))
    logo_path = os.path.join(_project_root, "assets", "SOPRA_logo_dark.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(_project_root, "assets", "OPRA_logo_dark.png")
    logo_html = ""
    
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        logo_html = f'<div style="display: block; margin: 0 auto; width: fit-content; padding: 2rem 3rem; background: radial-gradient(ellipse at center, rgba(60, 60, 75, 0.95) 0%, rgba(65, 65, 80, 0.8) 40%, rgba(55, 55, 68, 0.6) 70%, transparent 100%); border-radius: 30px; position: relative;"><img src="data:image/png;base64,{logo_data}" style="display: block; max-width: 455px; margin: 0 auto; position: relative; z-index: 1; filter: drop-shadow(0 0 40px rgba(0, 217, 255, 0.5));"></div>'
    else:
        logo_html = '<h1 style="font-family: JetBrains Mono, monospace; font-size: 4rem; color: #00d9ff; margin: 0; text-shadow: 0 0 30px rgba(0, 217, 255, 0.6);">🛡️ SOPRA</h1><p style="font-size: 1rem; color: #f0f0f0; letter-spacing: 4px; margin-top: 0.25rem;">SAE ON-PREMISE RISK ASSESSMENT</p>'
    
    st.markdown(f"""
    <div class="opra-header">
        {logo_html}
        <p style="font-size: 0.9rem; color: #00d9ff; letter-spacing: 2px; text-transform: uppercase;">Enterprise Infrastructure Security</p>
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


# Build a control_id -> family lookup from OPRA_CATEGORIES
CONTROL_FAMILY_MAP = {}
for _cat_key, _cat_data in OPRA_CATEGORIES.items():
    for _ctrl in _cat_data.get('controls', []):
        CONTROL_FAMILY_MAP[_ctrl['id']] = _ctrl.get('family', 'Unknown')

def lookup_family(control_id):
    """Look up the control family from the OPRA_CATEGORIES definitions"""
    return CONTROL_FAMILY_MAP.get(control_id, 'Unknown')
