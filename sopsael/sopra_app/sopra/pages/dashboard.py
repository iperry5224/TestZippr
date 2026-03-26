"""SOPRA Dashboard Page"""
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px
import os
import base64
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
import zipfile
import io

from sopra_controls import get_control_by_id, get_controls_by_category, get_remediation_script, ALL_CONTROLS, ControlFamily
from sopra.theme import (
    CHART_BG, CHART_FONT_COLOR, CHART_BORDER_COLOR, COLOR_PASSED, COLOR_FAILED, COLOR_CRITICAL,
    COLOR_HIGH, COLOR_MEDIUM, COLOR_LOW, SEV_COLORS, SEV_ICONS,
    FAMILY_ABBREV, OPRA_CATEGORIES, chart_layout
)
from sopra.persistence import save_results_to_file
from sopra.pages.remediation import binary_rain
from sopra.utils import (
    aggregate_findings, create_status_donut, create_category_bar,
    create_severity_polar, create_risk_gauge, create_heatmap, create_family_bar,
    render_header, calculate_risk_score, get_risk_color, render_metric_card,
    load_demo_data, lookup_family
)
from sopra.fips199 import get_controls_for_level, get_control_count_by_level, FIPS_DESCRIPTIONS

def render_dashboard():
    """Render the main SOPRA dashboard with charts and visualizations"""
    # Consistent vertical spacing across the dashboard
    st.markdown("""<style>
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stVerticalBlock"] > div[style] {
        margin-bottom: 0 !important;
    }
    div.stButton, div.stLinkButton { margin-bottom:0 !important; }
    h3 { margin-top:0.6rem !important; margin-bottom:0.4rem !important; }
    </style>""", unsafe_allow_html=True)

    render_header()
    
    # ── Quick stats row - CLICKABLE metric tiles ──
    _results = st.session_state.opra_assessment_results
    if _results:
        score = calculate_risk_score(_results.get("findings", []))
        score_display = f"{score}%"
        _finding_count = len(_results.get("findings", []))
        _cat_count = len(_results.get("categories_assessed", []))
        _fips_lvl = _results.get("fips199_level", "")
        _fips_tag = f" ({_fips_lvl})" if _fips_lvl else ""
    else:
        score_display = "N/A"
        _finding_count = len(OPRA_CATEGORIES) * 10  # 200 controls (20 categories x 10)
        _cat_count = len(OPRA_CATEGORIES)            # 20 categories
        _fips_tag = ""
    status = "Complete" if _results else "Pending"

    _tiles = [
        ("metric_categories", str(_cat_count), "ASSESSMENT CATEGORIES", "categories"),
        ("metric_controls", str(_finding_count) + _fips_tag, "CONTROLS ASSESSED", "controls"),
        ("metric_risk", score_display, "RISK SCORE", "risk_score"),
        ("metric_status", status, "STATUS", "status"),
    ]

    _tile_style = "display:flex;flex-direction:column;align-items:center;justify-content:center;height:68px;border:1px solid rgba(0,217,255,0.25);border-radius:8px;background:rgba(14,25,45,0.7);cursor:pointer;transition:all 0.2s;text-decoration:none;"
    _val_style = "font-size:1.1rem;font-weight:700;color:#00d9ff;margin:0;"
    _lbl_style = "font-size:0.65rem;letter-spacing:1.5px;color:#6b839e;text-transform:uppercase;margin:0.15rem 0 0 0;"

    tile_cols = st.columns(4)
    for i, (key, val, label, metric) in enumerate(_tiles):
        with tile_cols[i]:
            if st.button(f"{val}\n{label}", key=key, use_container_width=True):
                st.session_state.opra_selected_metric = metric
                st.session_state.opra_active_tab = "Metric Details"
                st.rerun()

    # Force uniform height on metric tiles (first row of buttons)
    st.markdown("""<style>
    div[data-testid="stHorizontalBlock"]:first-of-type .stButton button {
        min-height:68px !important; max-height:68px !important; height:68px !important;
        display:inline-flex !important; align-items:center !important; justify-content:center !important;
        padding:0.2rem 0.5rem !important; box-sizing:border-box !important;
        overflow:hidden !important;
    }
    div[data-testid="stHorizontalBlock"]:first-of-type .stButton button p {
        margin:0 !important; padding:0 !important; line-height:1.3 !important;
    }
    </style>""", unsafe_allow_html=True)
    
    # Consistent section spacing
    st.markdown('<div style="margin-top:0.8rem;"></div>', unsafe_allow_html=True)
    
    # ── VISUAL ANALYTICS SECTION ──
    if st.session_state.opra_assessment_results:
        findings = st.session_state.opra_assessment_results.get("findings", [])
        agg = aggregate_findings(findings)
        
        # Show FIPS 199 badge if a categorization was selected
        _fips = st.session_state.opra_assessment_results.get("fips199_level", "")
        if _fips:
            _finfo = FIPS_DESCRIPTIONS.get(_fips, {})
            _fcolor = _finfo.get("color", "#00d9ff")
            st.markdown(
                '<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.3rem;">'
                '<h3 style="margin:0 !important;">📈 Security Posture Overview</h3>'
                '<span style="display:inline-flex;align-items:center;gap:4px;padding:3px 12px;'
                'border-radius:20px;background:rgba(' + ','.join(str(int(_fcolor.lstrip("#")[i:i+2], 16)) for i in (0,2,4)) + ',0.12);'
                'border:1px solid ' + _fcolor + '40;font-size:0.7rem;font-weight:600;color:' + _fcolor + ';">'
                + _finfo.get("icon", "") + ' FIPS 199 ' + _fips + ' — ' + str(len(findings)) + ' controls</span>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown("### 📈 Security Posture Overview")
        
        chart_col1, chart_col2, chart_col3 = st.columns(3)
        
        # ── Donut Chart: Overall Compliance ──
        with chart_col1:
            st.plotly_chart(create_status_donut(agg["passed"], agg["failed"], agg["not_assessed"], agg["total"], title="Compliance Overview"), use_container_width=True)
            st.caption("Overall pass/fail compliance rate. Center % = controls meeting requirements.")
        
        # ── Bar Chart: Findings by Category ──
        with chart_col2:
            fig_bar = create_category_bar(agg["cat_passed"], agg["cat_failed"])
            if fig_bar:
                st.plotly_chart(fig_bar, use_container_width=True)
                st.caption("Passed (blue) vs failed (red) by category. Taller red bars need more attention.")
            else:
                st.info("No category data to display")
        
        # ── Severity Distribution Gauge / Polar Chart ──
        with chart_col3:
            fig_polar = create_severity_polar(agg["sev_counts"])
            if fig_polar:
                st.plotly_chart(fig_polar, use_container_width=True)
                st.caption("Severity distribution of failed findings. Larger wedges = more findings at that level.")
            else:
                # Show a gauge-style risk score
                score = calculate_risk_score(findings)
                st.plotly_chart(create_risk_gauge(score), use_container_width=True)
                st.caption("Overall risk score. Higher % = better security posture.")
        
        # ── Second row of charts ──
        st.markdown("---")
        
        chart2_col1, chart2_col2 = st.columns(2)
        
        # ── Heatmap: Category vs Severity ──
        with chart2_col1:
            st.markdown("#### 🔥 Risk Heatmap")
            fig_heat = create_heatmap(agg["heatmap_data"])
            if fig_heat:
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.info("Complete an assessment to view the risk heatmap")
        
        # ── Control Family Breakdown ──
        with chart2_col2:
            st.markdown("#### 📊 Control Family Breakdown")
            fig_fam = create_family_bar(agg["family_counts"])
            if fig_fam:
                st.plotly_chart(fig_fam, use_container_width=True)
            else:
                st.info("Complete an assessment to view control family breakdown")
    
    else:
        # ── No assessment data yet - show preview gauges ──
        st.markdown("### 📈 Security Posture Overview")
        st.markdown(
            '<div style="text-align:center;padding:0.8rem 1rem;background:linear-gradient(145deg,rgba(22,36,64,0.8),rgba(26,45,80,0.7));border:1px solid rgba(0,217,255,0.25);border-radius:10px;margin-bottom:0.8rem;">'
            '<p style="font-size:0.95rem;color:#f5f5f5;margin:0 0 0.25rem 0;">📊 Complete an assessment to unlock interactive visualizations</p>'
            '<p style="color:#c0c0c0;font-size:0.78rem;margin:0;">Upload CSV data or run a manual assessment to see pie charts, heatmaps, severity radars, and category breakdowns</p>'
            '</div>',
            unsafe_allow_html=True
        )
        
        # ── FIPS 199 Security Categorization + Execute Simulation ──
        _pad_l, _center_col, _pad_r = st.columns([1.5, 5, 1.5])
        with _center_col:
            # FIPS 199 selector card
            _counts = get_control_count_by_level()
            st.markdown(
                '<div style="text-align:center;padding:0.6rem 1rem;margin-bottom:0.6rem;'
                'background:linear-gradient(145deg,rgba(22,36,64,0.8),rgba(26,45,80,0.6));'
                'border:1px solid rgba(0,217,255,0.2);border-radius:10px;">'
                '<div style="font-size:0.55rem;letter-spacing:3px;color:rgba(0,217,255,0.6);'
                'text-transform:uppercase;margin-bottom:0.3rem;">FIPS 199 Security Categorization</div>'
                '<p style="color:#8899aa;font-size:0.72rem;margin:0;">Select the system impact level to determine the control baseline for assessment</p>'
                '</div>',
                unsafe_allow_html=True
            )

            # Initialize FIPS session state
            if "fips199_level" not in st.session_state:
                st.session_state.fips199_level = "High"

            _fips_cols = st.columns(3)
            for idx, level in enumerate(["Low", "Moderate", "High"]):
                info = FIPS_DESCRIPTIONS[level]
                count = _counts[level]
                with _fips_cols[idx]:
                    is_selected = st.session_state.fips199_level == level
                    border_color = info["color"] if is_selected else "rgba(255,255,255,0.08)"
                    bg = f"rgba({','.join(str(int(info['color'].lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.12)" if is_selected else "rgba(13,17,23,0.6)"
                    st.markdown(
                        '<div style="text-align:center;padding:0.5rem;border-radius:8px;'
                        'border:1px solid ' + border_color + ';background:' + bg + ';'
                        'margin-bottom:0.3rem;min-height:60px;display:flex;flex-direction:column;justify-content:center;">'
                        '<div style="font-size:1rem;">' + info["icon"] + '</div>'
                        '<div style="color:' + info["color"] + ';font-weight:700;font-size:0.85rem;">' + info["label"] + '</div>'
                        '<div style="color:#6b839e;font-size:0.7rem;">' + str(count) + ' controls</div>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                    if st.button(
                        f"{'● ' if is_selected else ''}{level}",
                        use_container_width=True,
                        type="primary" if is_selected else "secondary",
                        key=f"fips_btn_{level}"
                    ):
                        st.session_state.fips199_level = level
                        st.rerun()

            # Selected level description
            _sel = st.session_state.fips199_level
            _sel_info = FIPS_DESCRIPTIONS[_sel]
            st.markdown(
                '<div style="text-align:center;padding:0.35rem;margin:0.3rem 0 0.6rem 0;'
                'border-left:3px solid ' + _sel_info["color"] + ';background:rgba(0,0,0,0.2);border-radius:0 6px 6px 0;">'
                '<span style="color:' + _sel_info["color"] + ';font-weight:600;font-size:0.78rem;">' + _sel_info["label"] + ':</span> '
                '<span style="color:#8899aa;font-size:0.72rem;">' + _sel_info["description"] + '</span>'
                '</div>',
                unsafe_allow_html=True
            )

            # Execute button
            st.markdown("""
            <style>
            #exec-sim-container + div button {
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
                min-height: 4.5rem !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
            }
            #exec-sim-container + div button p {
                font-size: 1.1rem !important;
                font-weight: 600 !important;
            }
            #exec-sim-container + div button::after {
                content: "SOPRA will assess """ + str(_counts[_sel]) + """ controls at the """ + _sel + """ baseline";
                display: block;
                font-size: 0.7rem;
                color: #6b839e;
                font-weight: 400;
                margin-top: 0.3rem;
            }
            </style>
            <div id="exec-sim-container"></div>
            """, unsafe_allow_html=True)
            _load_clicked = st.button("⚡ Run Security Controls Assessment", use_container_width=True, key="dashboard_run_test_btn")

        if _load_clicked:
            demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "demo_csv_data")
            
            if os.path.exists(demo_dir):
                # Get the controls that apply to the selected FIPS 199 level
                fips_level = st.session_state.get("fips199_level", "High")
                allowed_controls = get_controls_for_level(fips_level)

                demo_files = sorted([f for f in os.listdir(demo_dir) if f.endswith('.csv')])
                
                all_findings = []
                progress = st.progress(0)
                status_text = st.empty()
                
                for idx, fname in enumerate(demo_files):
                    fpath = os.path.join(demo_dir, fname)
                    try:
                        df = pd.read_csv(fpath)
                        cat_name = df['category'].iloc[0] if 'category' in df.columns and len(df) > 0 else "Unknown"
                        status_text.markdown(f"<span style='color: #00d9ff;'>Loading: <strong>{cat_name}</strong>...</span>", unsafe_allow_html=True)
                        
                        for _, row in df.iterrows():
                            ctrl_id = row.get('control_id', 'UNKNOWN')
                            # Skip controls not in the selected FIPS 199 baseline
                            if ctrl_id not in allowed_controls:
                                continue
                            all_findings.append({
                                "control_id": ctrl_id,
                                "control_name": row.get('control_name', 'Unknown Control'),
                                "category": row.get('category', 'Uncategorized'),
                                "family": row.get('family', '') or lookup_family(ctrl_id),
                                "status": row.get('status', 'Not Assessed'),
                                "severity": row.get('severity', None) if row.get('status') == 'Failed' else None,
                                "evidence": row.get('evidence', ''),
                                "notes": row.get('notes', ''),
                                "assessed_by": row.get('assessed_by', 'Demo Data'),
                                "assessment_date": row.get('assessment_date', datetime.now().isoformat())
                            })
                        
                        progress.progress((idx + 1) / len(demo_files))
                        time.sleep(0.25)
                    except Exception as e:
                        st.error(f"Error loading {fname}: {e}")
                
                status_text.empty()
                progress.empty()
                
                if all_findings:
                    # Determine which categories were actually assessed
                    assessed_cats = list(set(f["category"] for f in all_findings))
                    st.session_state.opra_assessment_results = {
                        "timestamp": datetime.now().isoformat(),
                        "findings": all_findings,
                        "categories_assessed": assessed_cats,
                        "include_remediation": True,
                        "source": f"Test Data (Demo) — FIPS 199 {fips_level}",
                        "fips199_level": fips_level,
                    }
                    save_results_to_file(st.session_state.opra_assessment_results)
                    st.success(f"✅ {fips_level} baseline loaded! {len(all_findings)} controls across {len(assessed_cats)} categories. Refreshing dashboard...")
                    binary_rain()
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Demo data directory not found.")
        
        # Show placeholder gauge
        st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)
        preview_col1, preview_col2, preview_col3 = st.columns(3)
        with preview_col1:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=0,
                domain=dict(x=[0, 1], y=[0, 1]),
                title=dict(text="Risk Score", font=dict(color="#4a6fa5", size=14)),
                number=dict(suffix="%", font=dict(color="#4a6fa5", size=28)),
                gauge=dict(
                    axis=dict(range=[0, 100], tickcolor="#2a4a70", tickfont=dict(color="#4a6fa5")),
                    bar=dict(color="#2a4a70"),
                    bgcolor="rgba(22, 36, 64, 0.4)",
                    bordercolor="rgba(0, 217, 255, 0.1)",
                    steps=[
                        dict(range=[0, 40], color="rgba(233, 69, 96, 0.2)"),
                        dict(range=[40, 60], color="rgba(255, 107, 107, 0.2)"),
                        dict(range=[60, 80], color="rgba(255, 193, 7, 0.2)"),
                        dict(range=[80, 100], color="rgba(0, 217, 255, 0.2)")
                    ]
                )
            ))
            fig_gauge.update_layout(**chart_layout(height=220, font_color='#4a6fa5', margin=dict(t=40, b=10, l=20, r=20)))
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with preview_col2:
            fig_preview = go.Figure(data=[go.Pie(
                labels=["Awaiting", "Data"],
                values=[1, 0],
                hole=0.6,
                marker_colors=["#2a4a70", "#162440"],
                marker_line=dict(color="rgba(0, 217, 255, 0.15)", width=1),
                textinfo="none",
                hoverinfo="none"
            )])
            fig_preview.update_layout(**chart_layout(
                height=220, font_color='#4a6fa5', showlegend=False,
                margin=dict(t=30, b=10, l=20, r=20),
                annotations=[dict(text="No Data", x=0.5, y=0.5, font_size=14, font_color="#4a6fa5", showarrow=False)]
            ))
            st.plotly_chart(fig_preview, use_container_width=True)
        
        with preview_col3:
            fig_bar_preview = go.Figure(data=[go.Bar(
                x=["AD", "NET", "END", "SRV", "PHY", "DAT", "IAM", "MON"],
                y=[0, 0, 0, 0, 0, 0, 0, 0],
                marker_color="rgba(0, 217, 255, 0.2)",
                marker_line=dict(color="rgba(0, 217, 255, 0.35)", width=1)
            )])
            fig_bar_preview.update_layout(**chart_layout(
                height=220, font_color='#4a6fa5',
                xaxis=dict(tickfont=dict(color="#4a6fa5"), gridcolor='rgba(0, 217, 255, 0.06)'),
                yaxis=dict(tickfont=dict(color="#4a6fa5"), gridcolor='rgba(0, 217, 255, 0.06)', range=[0, 10]),
                margin=dict(t=30, b=30, l=20, r=20)
            ))
            st.plotly_chart(fig_bar_preview, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Assessment workflow: what to download and when ──
    st.markdown("### 📋 What to Download & When")
    st.markdown("""
    <div style="background: rgba(0, 217, 255, 0.06); border: 1px solid rgba(0, 217, 255, 0.25); border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.8rem; font-size: 0.9rem;">
    <strong>Step 1:</strong> Assessment Scripts — run on <em>your</em> systems → produces CSV<br>
    <strong>Step 2:</strong> Upload that CSV in Data Collection & Ingestion<br>
    <strong>Step 3:</strong> Run Assessment (click the button)<br>
    <strong>Step 4 (after):</strong> Remediation Scripts — fix scripts for failed controls
    </div>
    """, unsafe_allow_html=True)
    
    scripts_col, upload_col, run_col, rem_col = st.columns(4)
    with scripts_col:
        if st.button("1️⃣ Assessment Scripts — Run on Your Systems", key="tile_assessment_scripts", use_container_width=True,
                     help="Download PowerShell scripts. Run them on your Windows/AD environment. They produce a CSV file you'll upload to SOPRA."):
            st.session_state.opra_active_tab = "Assessment Scripts"
            st.rerun()
        st.caption("PowerShell → CSV output")
    with upload_col:
        if st.button("2️⃣ Upload CSV Files", key="tile_upload_csv", use_container_width=True,
                     help="Upload the CSV produced by Assessment Scripts. SOPRA will analyze it and produce results."):
            st.session_state.opra_active_tab = "Data Collection & Ingestion"
            st.rerun()
        st.caption("Upload your CSV here")
    with run_col:
        if st.button("3️⃣ Run Assessment", key="tile_run_assessment", use_container_width=True,
                     help="Run the security assessment on your uploaded data. Click after uploading your CSV."):
            st.session_state.opra_active_tab = "Run Security Assessment"
            st.rerun()
        st.caption("Execute assessment on uploaded data")
    with rem_col:
        if st.button("4️⃣ Remediation Scripts — After Assessment", key="tile_remediation", use_container_width=True,
                     help="Browse controls and download fix-it scripts for failed findings. Use these AFTER you've run an assessment."):
            st.session_state.opra_active_tab = "Remediation Templates"
            st.rerun()
        st.caption("Fix scripts for failed controls")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Quick Actions — ordered by workflow ──
    st.markdown("### 🔒 Quick Actions")
    st.caption("Start with Data Collection & Ingestion to upload your CSV and run assessment")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.link_button("📥 Data Collection & Ingestion — Run Assessment",
                       "?view=assessment", use_container_width=True,
                       help="Upload your CSV here and run the assessment")
    with col2:
        st.link_button("📊 View Reports",
                       "?view=reports", use_container_width=True)
    with col3:
        st.link_button("💬 Ask SOPRA AI",
                       "?view=ai", use_container_width=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.link_button("🔧 Remediation Center",
                       "?view=remediation", use_container_width=True,
                       help="Get fix scripts and guidance for failed controls")
    with col5:
        st.link_button("📜 Generate SSP",
                       "?view=ssp_poam", use_container_width=True)
    with col6:
        st.link_button("📡 Continuous Monitoring",
                       "?view=conmon", use_container_width=True)


def render_remediation_templates_picker():
    """Category picker for Remediation Scripts — click any category to explore controls"""
    st.markdown("### 🔧 Remediation Scripts — Step 3 (After Assessment)")
    st.caption("Browse controls and download fix-it scripts for failed findings")
    
    if st.button("← Back to Dashboard", key="back_remediation_picker"):
        st.session_state.opra_active_tab = "Dashboard"
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    cat_keys = list(OPRA_CATEGORIES.keys())
    num_cats = len(cat_keys)
    cols_per_row = 4
    for row_start in range(0, num_cats, cols_per_row):
        row_cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            cat_idx = row_start + col_idx
            if cat_idx < num_cats:
                key = cat_keys[cat_idx]
                with row_cols[col_idx]:
                    if st.button(OPRA_CATEGORIES[key]['name'], key=f"rem_cat_{key}", use_container_width=True):
                        st.session_state.opra_selected_category = key
                        st.session_state.opra_return_tab = "Remediation Templates"
                        st.session_state.opra_active_tab = "Category Details"
                        st.rerun()


def render_assessment_scripts_page():
    """Assessment scripts — PowerShell scripts run on target; output CSV for SOPRA import"""
    st.markdown("### 🔧 Assessment Scripts")
    st.caption("PowerShell scripts to run on target systems. Output: sopra_assessment_results.csv → import into SOPRA")
    
    if st.button("← Back to Dashboard", key="back_assessment_scripts"):
        st.session_state.opra_active_tab = "Dashboard"
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Resolve script directory (project root / sopra_assessment_scripts)
    project_root = Path(__file__).resolve().parent.parent.parent
    scripts_dir = project_root / "sopra_assessment_scripts"
    # Also check /opt/apps for EC2 deployment
    if not scripts_dir.exists() and Path("/opt/apps/sopra_assessment_scripts").exists():
        scripts_dir = Path("/opt/apps/sopra_assessment_scripts")
    
    if not scripts_dir.exists():
        st.warning(f"Assessment scripts directory not found at `{scripts_dir}`. Run `python export_sopra_assessment_scripts.py` to generate.")
        return
    
    ps1_files = sorted([f for f in scripts_dir.glob("*.ps1")])
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(0, 217, 255, 0.1) 0%, rgba(15, 52, 96, 0.3) 100%); 
                border: 1px solid rgba(0, 217, 255, 0.35); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem;">
        <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0;">Step 1: Run These on YOUR Systems</h4>
        <p style="color: #e8e8e8; margin: 0; font-size: 0.95rem;">
            Download & run these PowerShell scripts on your Windows/AD environment. 
            They produce <code>sopra_assessment_results.csv</code>. 
            <strong>Then upload that CSV</strong> in Data Collection & Ingestion.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        run_all = scripts_dir / "Run-All-Assessments.ps1"
        if run_all.exists():
            with open(run_all, "r", encoding="utf-8") as f:
                run_all_content = f.read()
            st.download_button(
                label="📥 Download Run-All-Assessments.ps1",
                data=run_all_content,
                file_name="Run-All-Assessments.ps1",
                mime="text/plain",
                key="dl_run_all",
                use_container_width=True
            )
        st.caption("Single script — run one command to execute all checks. Quick start.")
    
    with dl_col2:
        # Build zip of all *_assessment.ps1 scripts
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in ps1_files:
                zf.write(f, f.name)
        zip_buffer.seek(0)
        st.download_button(
            label=f"📦 Download All Scripts ({len(ps1_files)} .ps1 files)",
            data=zip_buffer.read(),
            file_name="sopra_assessment_scripts.zip",
            mime="application/zip",
            key="dl_all_scripts",
            use_container_width=True
        )
        st.caption("All 201 per-control scripts — run subsets, inspect, or integrate into your automation.")
    
    st.markdown("---")
    st.markdown("#### Scripts by control")
    
    # Group by prefix (AD_, NET_, etc.) using OPRA_CATEGORIES mapping
    prefix_to_cat = {}
    for key, cat in OPRA_CATEGORIES.items():
        # Map category to common prefix (e.g. active_directory -> AD)
        for ctrl in cat.get("controls", [])[:1]:
            ctrl_id = ctrl.get("id", "")
            prefix = ctrl_id.split("-")[0] if "-" in ctrl_id else ""
            if prefix and prefix not in prefix_to_cat:
                prefix_to_cat[prefix] = cat["name"]
    
    by_prefix = {}
    for f in ps1_files:
        if f.name == "Run-All-Assessments.ps1":
            continue
        prefix = f.name.split("_")[0] if "_" in f.name else "Other"
        if prefix not in by_prefix:
            by_prefix[prefix] = []
        by_prefix[prefix].append(f)
    
    for prefix in sorted(by_prefix.keys()):
        cat_name = prefix_to_cat.get(prefix, prefix)
        files = by_prefix[prefix]
        with st.expander(f"{cat_name} ({len(files)} scripts)", expanded=False):
            for i in range(0, len(files), 4):
                cols = st.columns(4)
                for col_idx, f in enumerate(files[i : i + 4]):
                    with cols[col_idx]:
                        with open(f, "r", encoding="utf-8") as fp:
                            content = fp.read()
                        st.download_button(
                            label=f.name,
                            data=content,
                            file_name=f.name,
                            mime="text/plain",
                            key=f"dl_{f.stem}",
                            use_container_width=True
                        )


def render_category_details():
    """Render detailed view for a selected category with all controls and insights"""
    cat_key = st.session_state.opra_selected_category
    
    if not cat_key or cat_key not in OPRA_CATEGORIES:
        st.warning("No category selected. Returning to dashboard...")
        st.session_state.opra_active_tab = "Dashboard"
        st.rerun()
        return
    
    category = OPRA_CATEGORIES[cat_key]
    
    # Back button — return to Remediation Templates picker or Dashboard
    return_tab = st.session_state.get("opra_return_tab", "Dashboard")
    back_label = f"← Back to {return_tab}" if return_tab != "Dashboard" else "← Back to Dashboard"
    if st.button(back_label, key="back_to_dash"):
        st.session_state.opra_selected_category = None
        st.session_state.opra_selected_control = None
        st.session_state.opra_active_tab = return_tab
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
            marker_line=dict(color=CHART_BORDER_COLOR, width=2),
            textinfo="label+value",
            textfont=dict(size=12, color="#ffffff")
        )])
        fig_fam.update_layout(**chart_layout(
            height=260,
            title=dict(text="Controls by Family", font=dict(color=COLOR_PASSED, size=14)),
            showlegend=False,
            margin=dict(t=35, b=10, l=10, r=10)
        ))
        st.plotly_chart(fig_fam, use_container_width=True)
    
    with insight_col2:
        # Assessment status for this category
        if st.session_state.opra_assessment_results:
            na_count = total_controls - passed_count - failed_count
            st.plotly_chart(create_status_donut(passed_count, failed_count, na_count, total_controls, height=260, title="Assessment Status"), use_container_width=True)
        else:
            st.plotly_chart(create_risk_gauge(0, height=260, title="Compliance"), use_container_width=True)
    
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
            st.session_state.opra_active_tab = "Run Security Assessment"
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
        st.session_state.opra_active_tab = "Run Security Assessment"
        st.rerun()


def render_controls_detail():
    """Detailed view for Total Controls metric"""
    st.markdown("""
    <div class="opra-header" style="padding: 2rem;">
        <h1 style="font-size: 2.5rem; margin: 0;">🔧 200 Security Controls</h1>
        <p style="color: #f0f0f0; font-size: 1.1rem; margin-top: 0.5rem;">Comprehensive control library across 20 categories with procedures, remediation, NIST/CIS mappings, and FIPS 199 baselines</p>
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
    
    fig = px.pie(
        values=list(severity_counts.values()),
        names=list(severity_counts.keys()),
        color_discrete_sequence=["#e94560", "#ff6b6b", "#ffc107", "#00d9ff"],
        hole=0.4
    )
    fig.update_traces(
        marker_line=dict(color="#0f1b2d", width=2),
        textfont=dict(color="#ffffff", size=13)
    )
    fig.update_layout(**chart_layout(legend=dict(bgcolor='rgba(0,0,0,0)')))
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
        st.session_state.opra_active_tab = "Run Security Assessment"
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
            st.session_state.opra_active_tab = "Run Security Assessment"
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
                st.session_state.opra_active_tab = "Run Security Assessment"
                st.rerun()
        with col3:
            if st.button("💬 Discuss with AI", use_container_width=True):
                st.session_state.opra_active_tab = "AI Assistant"
                st.rerun()
    
    else:
        st.warning("⏳ Assessment Pending")
        
        st.markdown("""
        ### No assessment has been completed yet.
        
        A SOPRA assessment evaluates your on-premise infrastructure against 200 security controls across 20 categories, aligned to NIST 800-53 Rev 5 and CIS Controls v8.
        
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
            st.session_state.opra_active_tab = "Run Security Assessment"
            st.rerun()


