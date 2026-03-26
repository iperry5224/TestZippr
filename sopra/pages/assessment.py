"""SOPRA Assessment Page"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import io
import os
import time

from sopra_controls import (
    ALL_CONTROLS, get_control_by_id, get_controls_by_category,
    get_remediation_script, ControlStatus, Severity, ControlFamily
)
from sopra.theme import (
    CHART_BG, CHART_FONT_COLOR, CHART_GRID_COLOR, CHART_GRID_LIGHT,
    COLOR_PASSED, COLOR_FAILED, COLOR_CRITICAL, COLOR_HIGH, COLOR_MEDIUM, COLOR_LOW,
    SEV_COLORS, FAMILY_ABBREV, OPRA_CATEGORIES, chart_layout
)
from sopra.persistence import save_results_to_file
from sopra.utils import (
    aggregate_findings, calculate_risk_score, render_metric_card,
    load_demo_data, lookup_family, create_risk_gauge
)
from sopra.pages.remediation import binary_rain

def render_assessment_page():
    """Render the assessment configuration and execution page"""
    st.markdown("## 🔍 On-Premise Assessment")
    
    # =========================================================================
    # ZERO-TOUCH ARCHITECTURE BANNER - Prominent emphasis on CSV-based approach
    # =========================================================================
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(0, 217, 255, 0.15) 0%, rgba(15, 52, 96, 0.3) 100%); 
                border: 2px solid rgba(0, 217, 255, 0.5); 
                border-radius: 15px; 
                padding: 1.5rem 2rem; 
                margin-bottom: 2rem;
                position: relative;
                overflow: hidden;">
        <div style="display: flex; align-items: center; gap: 1.5rem;">
            <div style="flex-shrink: 0;">
                <i class="fa-solid fa-shield-halved" style="font-size: 3rem; color: #00d9ff;"></i>
            </div>
            <div>
                <h3 style="color: #00d9ff; margin: 0 0 0.5rem 0; font-size: 1.4rem;">
                    🔒 Zero-Touch Architecture
                </h3>
                <p style="color: #e8e8e8; margin: 0; font-size: 1.05rem; line-height: 1.6;">
                    <strong>SOPRA never connects to or touches your environment.</strong> 
                    You export your system data using your own tools, then upload CSV files for analysis. 
                    Your security data stays under your complete control at all times.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # =========================================================================
    # PRIMARY: CSV FILE UPLOAD SECTION
    # =========================================================================
    st.markdown("### 📁 CSV Data Collection & Ingestion")
    st.markdown("**Primary Method:** Upload CSV exports from your environment for security assessment")
    
    # Category selection for CSV upload
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_categories = st.multiselect(
            "Select Categories to Assess",
            options=list(OPRA_CATEGORIES.keys()),
            default=list(OPRA_CATEGORIES.keys()),
            format_func=lambda x: f"{OPRA_CATEGORIES[x]['name']}",
            help="Choose which security domains to include in your assessment"
        )
    with col2:
        include_remediation = st.checkbox("Include remediation guidance", value=True, key="csv_remediation")
    
    # CSV Upload Interface - Main Focus
    st.markdown("---")
    
    # Four-step process visualization
    st.markdown("""
    <div style="display: flex; justify-content: space-between; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 180px; text-align: center; padding: 1.25rem; background: rgba(15, 52, 96, 0.4); border-radius: 12px; border: 1px solid rgba(0, 217, 255, 0.3);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">1️⃣</div>
            <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0; font-size: 1rem;">Download & Run on YOUR Systems</h4>
            <p style="color: #f0f0f0; font-size: 0.8rem; margin: 0;">Assessment Scripts or Export Script. Run on Windows/AD → produces CSV</p>
        </div>
        <div style="flex: 1; min-width: 180px; text-align: center; padding: 1.25rem; background: rgba(15, 52, 96, 0.4); border-radius: 12px; border: 1px solid rgba(0, 217, 255, 0.3);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">2️⃣</div>
            <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0; font-size: 1rem;">Upload CSV Here</h4>
            <p style="color: #f0f0f0; font-size: 0.8rem; margin: 0;">Drag and drop files below</p>
        </div>
        <div style="flex: 1; min-width: 180px; text-align: center; padding: 1.25rem; background: rgba(15, 52, 96, 0.4); border-radius: 12px; border: 1px solid rgba(0, 217, 255, 0.3);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">3️⃣</div>
            <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0; font-size: 1rem;">Run Security Controls Assessment</h4>
            <p style="color: #f0f0f0; font-size: 0.8rem; margin: 0;">Click "Process CSV Data & Run Assessment" button</p>
        </div>
        <div style="flex: 1; min-width: 180px; text-align: center; padding: 1.25rem; background: rgba(15, 52, 96, 0.4); border-radius: 12px; border: 1px solid rgba(0, 217, 255, 0.3);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">4️⃣</div>
            <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0; font-size: 1rem;">Get Fix Scripts (After)</h4>
            <p style="color: #f0f0f0; font-size: 0.8rem; margin: 0;">Remediation Scripts from Dashboard for failed controls</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Templates and Upload tabs
    csv_tab1, csv_tab2, csv_tab3, csv_tab4 = st.tabs(["📤 Upload CSV", "📥 CSV Format (optional)", "🔧 Export Script (alt to Assessment Scripts)", "🧪 Use Test Data"])
    
    with csv_tab1:
        st.markdown("#### Upload Your CSV Files")
        st.markdown("**Most users:** Run Assessment Scripts (Dashboard → 1️⃣ Assessment Scripts) on your systems, then upload the CSV here.")
        
        uploaded_files = st.file_uploader(
            "Drop CSV files here or click to browse",
            type=["csv"],
            accept_multiple_files=True,
            key="csv_upload",
            help="You can upload multiple CSV files at once"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
            
            # Show uploaded files summary
            for f in uploaded_files:
                with st.expander(f"📄 {f.name}", expanded=False):
                    try:
                        df = pd.read_csv(f)
                        st.dataframe(df.head(10), use_container_width=True)
                        st.caption(f"Showing first 10 of {len(df)} rows")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")
            
            st.markdown("---")
            if st.button("🚀 Process CSV Data & Run Assessment", type="primary", use_container_width=True):
                process_csv_assessment(uploaded_files, selected_categories, include_remediation)
        else:
            st.info("📁 Run Assessment Scripts on your systems first (Dashboard), then upload the CSV they produce.")
    
    with csv_tab2:
        st.markdown("#### CSV Format — Optional")
        st.markdown("Empty CSV templates if you prefer to manually collect data or need the column format. **Most users** use Assessment Scripts instead.")
        
        template_col1, template_col2 = st.columns(2)
        
        with template_col1:
            for cat_key in ["active_directory", "network_infrastructure", "endpoint_security", "server_security"]:
                if cat_key in OPRA_CATEGORIES:
                    cat = OPRA_CATEGORIES[cat_key]
                    template_csv = generate_csv_template(cat_key)
                    st.download_button(
                        label=f"📄 {cat['name']} CSV",
                        data=template_csv,
                        file_name=f"sopra_{cat_key}_script.csv",
                        mime="text/csv",
                        key=f"template_{cat_key}",
                        use_container_width=True
                    )
        
        with template_col2:
            for cat_key in ["physical_security", "data_protection", "identity_access", "monitoring_logging"]:
                if cat_key in OPRA_CATEGORIES:
                    cat = OPRA_CATEGORIES[cat_key]
                    template_csv = generate_csv_template(cat_key)
                    st.download_button(
                        label=f"📄 {cat['name']} CSV",
                        data=template_csv,
                        file_name=f"sopra_{cat_key}_script.csv",
                        mime="text/csv",
                        key=f"template_{cat_key}",
                        use_container_width=True
                    )
        
        st.markdown("---")
        all_templates = generate_master_csv_template()
        st.download_button(
            label="📦 Download All CSV Formats (Combined)",
            data=all_templates,
            file_name="sopra_all_scripts.csv",
            mime="text/csv",
            key="template_all",
            type="primary",
            use_container_width=True
        )
    
    with csv_tab3:
        st.markdown("#### Unified Export Script — Alternative to Assessment Scripts")
        st.markdown("One PowerShell script with an interactive menu. **Alternative to** the 200+ Assessment Scripts (Dashboard). Run on your Windows systems → produces CSV.")
        
        # Generate the unified script
        unified_script = generate_unified_export_script()
        
        st.markdown("""
        <div style="background: rgba(0, 217, 255, 0.1); border: 1px solid rgba(0, 217, 255, 0.3); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0;">📜 SOPRA-Export.ps1</h4>
            <p style="color: #f0f0f0; margin: 0 0 1rem 0;">
                One script with an interactive menu. Run it on any Windows system to export security configuration data.
            </p>
            <ul style="color: #f0f0f0; margin: 0; padding-left: 1.5rem;">
                <li>Interactive menu - select what to export</li>
                <li>Exports data to CSV format</li>
                <li>No external dependencies required</li>
                <li>Safe, read-only operations</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Download button for unified script
        st.download_button(
            label="📥 Download SOPRA-Export.ps1",
            data=unified_script,
            file_name="SOPRA-Export.ps1",
            mime="text/plain",
            key="unified_export_script",
            type="primary",
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Show script preview
        with st.expander("👁️ Preview Script", expanded=False):
            st.code(unified_script, language="powershell")
    
    with csv_tab4:
        st.markdown("""
        <div style="background: linear-gradient(145deg, rgba(0, 217, 255, 0.12), rgba(0, 255, 136, 0.08)); border: 1px solid rgba(0, 217, 255, 0.35); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <h4 style="color: #00d9ff; margin: 0 0 0.5rem 0;">🧪 Technical Demonstration Mode</h4>
            <p style="color: #f0f0f0; margin: 0 0 0.8rem 0;">
                Load realistic pre-built assessment data across <strong>all 8 security categories</strong> to showcase 
                SOPRA's full analytical capabilities — interactive dashboards, risk heatmaps, severity breakdowns, 
                compliance scoring, and AI-powered remediation guidance.
            </p>
            <ul style="color: #c8e6ff; margin: 0; padding-left: 1.5rem; line-height: 1.8;">
                <li><strong>200 security controls</strong> across 20 categories</li>
                <li>Mix of <span style="color:#00d9ff;">Passed</span>, <span style="color:#e94560;">Failed</span>, and <span style="color:#ffc107;">varying severity</span> findings</li>
                <li>Realistic evidence notes and assessor attribution</li>
                <li>Instantly populates Dashboard, Reports, and AI Assistant</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Show preview of what will be loaded
        st.markdown("#### 📋 Test Data Preview")
        st.caption("Click any category tile to drill down into its assessment details")
        
        demo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "demo_csv_data")
        demo_files_found = []
        
        # Reverse lookup: category display name -> category key
        cat_name_to_key = {cat['name']: key for key, cat in OPRA_CATEGORIES.items()}
        
        if os.path.exists(demo_dir):
            demo_files = sorted([f for f in os.listdir(demo_dir) if f.endswith('.csv')])
            
            # Pre-parse all files for data
            demo_data = []
            for fname in demo_files:
                fpath = os.path.join(demo_dir, fname)
                demo_files_found.append(fpath)
                try:
                    df = pd.read_csv(fpath)
                    cat_name = df['category'].iloc[0] if 'category' in df.columns and len(df) > 0 else fname.replace('_assessment.csv', '').replace('_', ' ').title()
                    total = len(df)
                    passed_ct = len(df[df['status'] == 'Passed']) if 'status' in df.columns else 0
                    failed_ct = len(df[df['status'] == 'Failed']) if 'status' in df.columns else 0
                    pass_pct = int(passed_ct / total * 100) if total > 0 else 0
                    
                    if pass_pct >= 70:
                        status_icon = "✅"
                    elif pass_pct >= 40:
                        status_icon = "⚠️"
                    else:
                        status_icon = "🔴"
                    
                    demo_data.append({
                        "fname": fname, "fpath": fpath, "cat_name": cat_name,
                        "total": total, "passed": passed_ct, "failed": failed_ct,
                        "pct": pass_pct, "icon": status_icon
                    })
                except Exception:
                    pass
            
            # Render clickable tiles in 2-column grid
            for row_start in range(0, len(demo_data), 2):
                row_items = demo_data[row_start:row_start + 2]
                cols = st.columns(2)
                for col_idx, item in enumerate(row_items):
                    with cols[col_idx]:
                        btn_label = f"{item['icon']} {item['cat_name']}  |  {item['total']} controls  |  {item['passed']} passed · {item['failed']} failed  |  {item['pct']}%"
                        cat_key = cat_name_to_key.get(item['cat_name'])
                        if st.button(
                            btn_label,
                            key=f"demo_cat_{item['fname']}",
                            use_container_width=True,
                            help=f"Click to view detailed drill-down for {item['cat_name']}"
                        ):
                            if cat_key:
                                st.session_state.opra_selected_category = cat_key
                                st.session_state.opra_active_tab = "Category Details"
                                st.rerun()
            
            # Interactive Summary Intelligence Panel
            try:
                all_dfs = []
                for fpath in demo_files_found:
                    all_dfs.append(pd.read_csv(fpath))
                combined = pd.concat(all_dfs, ignore_index=True)
                total_controls = len(combined)
                total_passed = len(combined[combined['status'] == 'Passed'])
                total_failed = len(combined[combined['status'] == 'Failed'])
                overall_pct = int(total_passed / total_controls * 100) if total_controls > 0 else 0
                
                st.markdown("")
                st.markdown("#### 📊 Assessment Intelligence Dashboard")
                st.caption("Click any metric card below to explore that dimension of the data")
                
                # ── 4 Interactive Metric Buttons ──
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    if st.button(f"📋 {total_controls}\nTotal Controls", key="demo_metric_total", use_container_width=True,
                                 help="View controls distribution by category and family"):
                        st.session_state.demo_insight_panel = "total"
                with m2:
                    if st.button(f"✅ {total_passed}\nPassed", key="demo_metric_passed", use_container_width=True,
                                 help="Explore passed controls and compliance strengths"):
                        st.session_state.demo_insight_panel = "passed"
                with m3:
                    if st.button(f"❌ {total_failed}\nFailed", key="demo_metric_failed", use_container_width=True,
                                 help="Analyze failures by severity and risk priority"):
                        st.session_state.demo_insight_panel = "failed"
                with m4:
                    if st.button(f"🎯 {overall_pct}%\nCompliant", key="demo_metric_compliance", use_container_width=True,
                                 help="View compliance radar across all categories"):
                        st.session_state.demo_insight_panel = "compliance"
                
                # Initialize panel state
                if "demo_insight_panel" not in st.session_state:
                    st.session_state.demo_insight_panel = None
                
                active_panel = st.session_state.get("demo_insight_panel")
                
                # ══════════════════════════════════════════════════════════
                # PANEL: Total Controls — Sunburst + Treemap
                # ══════════════════════════════════════════════════════════
                if active_panel == "total":
                    st.markdown("---")
                    st.markdown("### 🔬 Controls Architecture — Category & Family Breakdown")
                    
                    p1, p2 = st.columns(2)
                    
                    with p1:
                        # Sunburst: Category -> Family -> Control
                        labels, parents, values, colors = [], [], [], []
                        cat_colors = {"Active Directory Security": "#00d9ff", "Network Infrastructure": "#e94560",
                                      "Endpoint Security": "#ffc107", "Server Security": "#00ff88",
                                      "Physical Security": "#a855f7", "Data Protection": "#ff6b6b",
                                      "Identity & Access Management": "#ff9f43", "Monitoring & Logging": "#54a0ff"}
                        
                        for cat_name_val in combined['category'].unique():
                            cat_df = combined[combined['category'] == cat_name_val]
                            labels.append(cat_name_val)
                            parents.append("")
                            values.append(len(cat_df))
                            colors.append(cat_colors.get(cat_name_val, "#4a6fa5"))
                            
                            if 'family' in cat_df.columns:
                                for fam in cat_df['family'].dropna().unique():
                                    fam_count = len(cat_df[cat_df['family'] == fam])
                                    labels.append(f"{fam}")
                                    parents.append(cat_name_val)
                                    values.append(fam_count)
                                    colors.append(cat_colors.get(cat_name_val, "#4a6fa5"))
                        
                        fig_sun = go.Figure(go.Sunburst(
                            labels=labels, parents=parents, values=values,
                            branchvalues="total",
                            marker=dict(colors=colors, line=dict(color="#0f1b2d", width=2)),
                            textfont=dict(size=11, color="#ffffff"),
                            hovertemplate="<b>%{label}</b><br>Controls: %{value}<extra></extra>",
                            insidetextorientation='radial'
                        ))
                        fig_sun.update_layout(**chart_layout(
                            height=400,
                            title=dict(text="Category → Family Hierarchy", font=dict(color=COLOR_PASSED, size=14)),
                            margin=dict(t=40, b=10, l=10, r=10)
                        ))
                        st.plotly_chart(fig_sun, use_container_width=True)
                    
                    with p2:
                        # Treemap: visual area proportional to control count
                        tm_labels, tm_parents, tm_values, tm_colors = ["All Controls"], [""], [0], ["#0f1b2d"]
                        for cat_name_val in combined['category'].unique():
                            cat_count = len(combined[combined['category'] == cat_name_val])
                            tm_labels.append(cat_name_val)
                            tm_parents.append("All Controls")
                            tm_values.append(cat_count)
                            tm_colors.append(cat_colors.get(cat_name_val, "#4a6fa5"))
                        
                        fig_tree = go.Figure(go.Treemap(
                            labels=tm_labels, parents=tm_parents, values=tm_values,
                            marker=dict(colors=tm_colors, line=dict(color="#0f1b2d", width=3)),
                            textfont=dict(size=14, color="#ffffff"),
                            texttemplate="<b>%{label}</b><br>%{value} controls",
                            hovertemplate="<b>%{label}</b><br>%{value} controls<extra></extra>"
                        ))
                        fig_tree.update_layout(**chart_layout(
                            height=400,
                            title=dict(text="Controls Distribution Treemap", font=dict(color=COLOR_PASSED, size=14)),
                            margin=dict(t=40, b=10, l=10, r=10)
                        ))
                        st.plotly_chart(fig_tree, use_container_width=True)
                
                # ══════════════════════════════════════════════════════════
                # PANEL: Passed Controls — Strength Analysis
                # ══════════════════════════════════════════════════════════
                elif active_panel == "passed":
                    st.markdown("---")
                    st.markdown("### ✅ Compliance Strengths — What's Working Well")
                    
                    passed_df = combined[combined['status'] == 'Passed']
                    
                    p1, p2 = st.columns(2)
                    
                    with p1:
                        # Horizontal waterfall showing passed per category (sorted best to worst)
                        cat_pass_counts = passed_df.groupby('category').size().sort_values(ascending=True)
                        cat_totals = combined.groupby('category').size()
                        cat_pass_pcts = ((cat_pass_counts / cat_totals.reindex(cat_pass_counts.index)) * 100).fillna(0).astype(int)
                        
                        fig_pass = go.Figure(go.Bar(
                            y=cat_pass_counts.index,
                            x=cat_pass_counts.values,
                            orientation='h',
                            marker=dict(
                                color=cat_pass_pcts.values,
                                colorscale=[[0, '#e94560'], [0.5, '#ffc107'], [1.0, '#00d9ff']],
                                showscale=True,
                                colorbar=dict(title="Pass %", tickfont=dict(color="#f5f5f5"), titlefont=dict(color="#00d9ff")),
                                line=dict(color="rgba(255,255,255,0.2)", width=1)
                            ),
                            text=[f"{v} ({cat_pass_pcts[k]}%)" for k, v in cat_pass_counts.items()],
                            textposition='auto',
                            textfont=dict(color="#ffffff", size=13)
                        ))
                        fig_pass.update_layout(**chart_layout(
                            height=380,
                            title=dict(text="Passed Controls by Category", font=dict(color=COLOR_PASSED, size=14)),
                            xaxis=dict(title="Controls Passed", gridcolor='rgba(0,217,255,0.1)', zeroline=False),
                            yaxis=dict(tickfont=dict(size=11)),
                            margin=dict(t=40, b=40, l=160, r=20)
                        ))
                        st.plotly_chart(fig_pass, use_container_width=True)
                    
                    with p2:
                        # Donut showing pass/fail/na with animated feel
                        na_count = total_controls - total_passed - total_failed
                        fig_ring = go.Figure(data=[go.Pie(
                            labels=["Passed", "Failed", "Not Assessed"],
                            values=[total_passed, total_failed, na_count],
                            hole=0.65,
                            marker=dict(colors=["#00d9ff", "#e94560", "#4a6fa5"],
                                        line=dict(color="#0f1b2d", width=3)),
                            textinfo="label+value",
                            textfont=dict(size=13, color="#ffffff"),
                            pull=[0.05, 0, 0],
                            rotation=90
                        )])
                        fig_ring.update_layout(**chart_layout(
                            height=380, showlegend=True,
                            title=dict(text="Overall Assessment Outcome", font=dict(color=COLOR_PASSED, size=14)),
                            margin=dict(t=40, b=20, l=20, r=20),
                            annotations=[dict(
                                text=f"<b style='font-size:24px'>{overall_pct}%</b><br><span style='font-size:12px'>Pass Rate</span>",
                                x=0.5, y=0.5, font_size=18, font_color=COLOR_PASSED, showarrow=False
                            )]
                        ))
                        st.plotly_chart(fig_ring, use_container_width=True)
                    
                    # Passed controls detail table
                    if len(passed_df) > 0:
                        with st.expander(f"📋 View All {len(passed_df)} Passed Controls", expanded=False):
                            display_cols = ['category', 'control_id', 'control_name']
                            if 'evidence' in passed_df.columns:
                                display_cols.append('evidence')
                            st.dataframe(passed_df[display_cols].reset_index(drop=True), use_container_width=True, height=300)
                
                # ══════════════════════════════════════════════════════════
                # PANEL: Failed Controls — Risk Intelligence
                # ══════════════════════════════════════════════════════════
                elif active_panel == "failed":
                    st.markdown("---")
                    st.markdown("### 🔴 Risk Intelligence — Failure Analysis & Priority Matrix")
                    
                    failed_df = combined[combined['status'] == 'Failed']
                    
                    p1, p2 = st.columns(2)
                    
                    with p1:
                        # Severity funnel chart — shows risk prioritization
                        sev_order = ["Critical", "High", "Medium", "Low"]
                        sev_colors = ["#e94560", "#ff6b6b", "#ffc107", "#00d9ff"]
                        sev_counts_list = []
                        for sev in sev_order:
                            if 'severity' in failed_df.columns:
                                sev_counts_list.append(len(failed_df[failed_df['severity'] == sev]))
                            else:
                                sev_counts_list.append(0)
                        
                        fig_funnel = go.Figure(go.Funnel(
                            y=sev_order,
                            x=sev_counts_list,
                            marker=dict(color=sev_colors, line=dict(color="#0f1b2d", width=2)),
                            textinfo="value+percent initial",
                            textfont=dict(size=14, color="#ffffff"),
                            connector=dict(line=dict(color="rgba(0,217,255,0.3)", width=2))
                        ))
                        fig_funnel.update_layout(**chart_layout(
                            height=380,
                            title=dict(text="Risk Severity Funnel", font=dict(color=COLOR_FAILED, size=14)),
                            margin=dict(t=40, b=20, l=20, r=20)
                        ))
                        st.plotly_chart(fig_funnel, use_container_width=True)
                    
                    with p2:
                        # Bubble chart: Category x Severity with size = count
                        bubble_data = []
                        for cat in failed_df['category'].unique():
                            cat_fail = failed_df[failed_df['category'] == cat]
                            if 'severity' in cat_fail.columns:
                                for sev_idx, sev in enumerate(sev_order):
                                    count = len(cat_fail[cat_fail['severity'] == sev])
                                    if count > 0:
                                        bubble_data.append({
                                            "category": cat, "severity": sev,
                                            "count": count, "sev_idx": sev_idx,
                                            "color": sev_colors[sev_idx]
                                        })
                        
                        if bubble_data:
                            fig_bubble = go.Figure()
                            for sev_idx, sev in enumerate(sev_order):
                                sev_items = [b for b in bubble_data if b['severity'] == sev]
                                if sev_items:
                                    fig_bubble.add_trace(go.Scatter(
                                        x=[b['category'] for b in sev_items],
                                        y=[b['severity'] for b in sev_items],
                                        mode='markers',
                                        name=sev,
                                        marker=dict(
                                            size=[b['count'] * 18 + 12 for b in sev_items],
                                            color=sev_colors[sev_idx],
                                            opacity=0.85,
                                            line=dict(color="rgba(255,255,255,0.3)", width=1)
                                        ),
                                        text=[f"{b['count']} findings" for b in sev_items],
                                        textposition="middle center",
                                        textfont=dict(color="#ffffff", size=10),
                                        hovertemplate="<b>%{x}</b><br>Severity: %{y}<br>Count: %{text}<extra></extra>"
                                    ))
                            
                            fig_bubble.update_layout(**chart_layout(
                                height=380, showlegend=True,
                                title=dict(text="Risk Bubble Matrix — Category × Severity", font=dict(color=COLOR_FAILED, size=14)),
                                xaxis=dict(tickangle=-20, tickfont=dict(size=10, color=CHART_FONT_COLOR), gridcolor=CHART_GRID_LIGHT),
                                yaxis=dict(tickfont=dict(color=CHART_FONT_COLOR), gridcolor=CHART_GRID_LIGHT,
                                           categoryorder='array', categoryarray=list(reversed(sev_order))),
                                margin=dict(t=40, b=60, l=20, r=20)
                            ))
                            st.plotly_chart(fig_bubble, use_container_width=True)
                    
                    # Critical findings callout
                    if 'severity' in failed_df.columns:
                        critical_df = failed_df[failed_df['severity'] == 'Critical']
                        if len(critical_df) > 0:
                            st.markdown(f"""
                            <div style="background: linear-gradient(145deg, rgba(233, 69, 96, 0.15), rgba(233, 69, 96, 0.08)); 
                                        border: 1px solid rgba(233, 69, 96, 0.5); border-radius: 12px; 
                                        padding: 1rem 1.5rem; margin-top: 0.5rem;">
                                <span style="color: #e94560; font-size: 1.1rem; font-weight: 700;">
                                    ⚠️ {len(critical_df)} CRITICAL Findings Requiring Immediate Action
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                            for _, row in critical_df.iterrows():
                                st.markdown(f"""
                                <div style="background: rgba(233, 69, 96, 0.08); border-left: 3px solid #e94560; 
                                            padding: 0.5rem 1rem; margin: 0.3rem 0; border-radius: 0 8px 8px 0;">
                                    <span style="color: #e94560; font-weight: 600;">{row.get('control_id', 'N/A')}</span>
                                    <span style="color: #f5f5f5;"> — {row.get('control_name', 'Unknown')}</span><br>
                                    <span style="color: #8899bb; font-size: 0.85rem;">📁 {row.get('category', '')} &nbsp;|&nbsp; 📝 {row.get('evidence', 'No evidence recorded')}</span>
                                </div>
                                """, unsafe_allow_html=True)
                
                # ══════════════════════════════════════════════════════════
                # PANEL: Compliance — Radar & Gauge
                # ══════════════════════════════════════════════════════════
                elif active_panel == "compliance":
                    st.markdown("---")
                    st.markdown("### 🎯 Compliance Posture — Cross-Category Analysis")
                    
                    p1, p2 = st.columns(2)
                    
                    with p1:
                        # Spider/Radar chart comparing each category's compliance %
                        cat_names_list = []
                        cat_pcts = []
                        for cat_name_val in combined['category'].unique():
                            cat_df = combined[combined['category'] == cat_name_val]
                            cat_total = len(cat_df)
                            cat_passed_n = len(cat_df[cat_df['status'] == 'Passed'])
                            pct = int(cat_passed_n / cat_total * 100) if cat_total > 0 else 0
                            cat_names_list.append(cat_name_val)
                            cat_pcts.append(pct)
                        
                        # Close the radar polygon
                        cat_names_radar = cat_names_list + [cat_names_list[0]]
                        cat_pcts_radar = cat_pcts + [cat_pcts[0]]
                        
                        fig_radar = go.Figure()
                        fig_radar.add_trace(go.Scatterpolar(
                            r=cat_pcts_radar, theta=cat_names_radar,
                            fill='toself',
                            fillcolor='rgba(0, 217, 255, 0.15)',
                            line=dict(color='#00d9ff', width=3),
                            marker=dict(size=8, color='#00d9ff', symbol='diamond'),
                            name='Compliance %',
                            text=[f"{p}%" for p in cat_pcts_radar],
                            textposition='top center',
                            textfont=dict(color='#00d9ff', size=12)
                        ))
                        # Add a "target" ring at 80%
                        target_vals = [80] * len(cat_names_radar)
                        fig_radar.add_trace(go.Scatterpolar(
                            r=target_vals, theta=cat_names_radar,
                            fill=None,
                            line=dict(color='rgba(255, 193, 7, 0.5)', width=2, dash='dot'),
                            name='Target (80%)',
                            hoverinfo='skip'
                        ))
                        
                        fig_radar.update_layout(
                            title=dict(text="Category Compliance Radar", font=dict(color=COLOR_PASSED, size=14)),
                            paper_bgcolor=CHART_BG,
                            polar=dict(
                                bgcolor='rgba(22, 36, 64, 0.4)',
                                radialaxis=dict(visible=True, range=[0, 100], color="#4a6fa5",
                                                gridcolor=CHART_GRID_COLOR, ticksuffix="%"),
                                angularaxis=dict(color=CHART_FONT_COLOR, gridcolor='rgba(0, 217, 255, 0.1)',
                                                 linecolor='rgba(0, 217, 255, 0.15)')
                            ),
                            font_color=CHART_FONT_COLOR, height=420, showlegend=True,
                            legend=dict(font=dict(color=CHART_FONT_COLOR, size=11), bgcolor='rgba(0,0,0,0)',
                                        yanchor="bottom", y=-0.15, xanchor="center", x=0.5, orientation="h"),
                            margin=dict(t=40, b=60, l=80, r=80)
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)
                    
                    with p2:
                        # Animated-style gauge + bullet bars per category
                        st.markdown("")
                        st.markdown("**Category Compliance Breakdown:**")
                        
                        # Sort by compliance % ascending (worst first)
                        sorted_cats = sorted(zip(cat_names_list, cat_pcts), key=lambda x: x[1])
                        
                        for cat_n, pct in sorted_cats:
                            if pct >= 80:
                                bar_color = "#00d9ff"
                                bar_bg = "rgba(0, 217, 255, 0.15)"
                            elif pct >= 60:
                                bar_color = "#ffc107"
                                bar_bg = "rgba(255, 193, 7, 0.15)"
                            elif pct >= 40:
                                bar_color = "#ff6b6b"
                                bar_bg = "rgba(255, 107, 107, 0.15)"
                            else:
                                bar_color = "#e94560"
                                bar_bg = "rgba(233, 69, 96, 0.15)"
                            
                            st.markdown(f"""
                            <div style="margin-bottom: 0.6rem;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                                    <span style="color: #f5f5f5; font-size: 0.85rem;">{cat_n}</span>
                                    <span style="color: {bar_color}; font-weight: 700; font-size: 0.9rem;">{pct}%</span>
                                </div>
                                <div style="background: {bar_bg}; border-radius: 6px; height: 18px; overflow: hidden; 
                                            border: 1px solid rgba(0,217,255,0.1);">
                                    <div style="background: linear-gradient(90deg, {bar_color}, {bar_color}aa); 
                                                width: {pct}%; height: 100%; border-radius: 6px;
                                                box-shadow: 0 0 8px {bar_color}66; transition: width 1s ease;">
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Overall compliance gauge
                        st.markdown("")
                        st.plotly_chart(create_risk_gauge(overall_pct, height=200, title="Overall Compliance"), use_container_width=True)
                
                st.markdown("")
            except Exception as e:
                st.error(f"Error loading summary data: {e}")
            
            st.markdown("")
            
            if st.button("🚀 Load Test Data & Run Full Assessment", type="primary", use_container_width=True, key="load_test_data_btn"):
                with st.spinner("Loading test data from all 20 categories..."):
                    
                    all_findings = []
                    progress = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, fpath in enumerate(demo_files_found):
                        try:
                            df = pd.read_csv(fpath)
                            cat_name = df['category'].iloc[0] if 'category' in df.columns and len(df) > 0 else "Unknown"
                            status_text.markdown(f"<span style='color: #00d9ff;'>Processing: <strong>{cat_name}</strong>...</span>", unsafe_allow_html=True)
                            
                            for _, row in df.iterrows():
                                finding = {
                                    "control_id": row.get('control_id', 'UNKNOWN'),
                                    "control_name": row.get('control_name', 'Unknown Control'),
                                    "category": row.get('category', 'Uncategorized'),
                                    "family": row.get('family', '') or lookup_family(row.get('control_id', '')),
                                    "status": row.get('status', 'Not Assessed'),
                                    "severity": row.get('severity', None) if row.get('status') == 'Failed' else None,
                                    "evidence": row.get('evidence', ''),
                                    "notes": row.get('notes', ''),
                                    "assessed_by": row.get('assessed_by', 'Demo Data'),
                                    "assessment_date": row.get('assessment_date', datetime.now().isoformat())
                                }
                                all_findings.append(finding)
                            
                            progress.progress((idx + 1) / len(demo_files_found))
                            time.sleep(0.3)
                            
                        except Exception as e:
                            st.error(f"Error loading {os.path.basename(fpath)}: {e}")
                    
                    status_text.empty()
                    progress.empty()
                
                if all_findings:
                    # Store results
                    all_cat_keys = list(OPRA_CATEGORIES.keys())
                    st.session_state.opra_assessment_results = {
                        "timestamp": datetime.now().isoformat(),
                        "findings": all_findings,
                        "categories_assessed": all_cat_keys,
                        "include_remediation": True,
                        "source": "Test Data (Demo)"
                    }
                    save_results_to_file(st.session_state.opra_assessment_results)
                    
                    passed_n = len([f for f in all_findings if f['status'] == 'Passed'])
                    failed_n = len([f for f in all_findings if f['status'] == 'Failed'])
                    
                    st.success(f"✅ Demo assessment loaded! **{len(all_findings)} controls** processed — {passed_n} passed, {failed_n} failed.")
                    binary_rain()
                    
                    st.markdown("")
                    
                    demo_nav_col1, demo_nav_col2 = st.columns(2)
                    with demo_nav_col1:
                        if st.button("📊 View Dashboard", type="primary", use_container_width=True, key="demo_go_dashboard"):
                            st.session_state.opra_active_tab = "Dashboard"
                            st.rerun()
                    with demo_nav_col2:
                        if st.button("📈 View Full Report", type="secondary", use_container_width=True, key="demo_go_reports"):
                            st.session_state.opra_active_tab = "Reports"
                            st.rerun()
                else:
                    st.warning("⚠️ No test data could be loaded.")
        else:
            st.error("⚠️ Demo data directory not found. Expected at: `demo_csv_data/`")
    
    # =========================================================================
    # SECONDARY: Manual Assessment Option
    # =========================================================================
    st.markdown("---")
    with st.expander("📝 Alternative: Manual Assessment Questionnaire", expanded=False):
        st.markdown("""
        <div style="background: rgba(255, 193, 7, 0.1); border-left: 4px solid #ffc107; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <strong style="color: #ffc107;">ℹ️ When to Use Manual Assessment</strong><br>
            <span style="color: #f0f0f0;">Use this option when you cannot export CSV data, or for quick initial assessments. 
            CSV-based assessment is recommended for accuracy and audit trails.</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Manual Assessment", type="secondary", use_container_width=True, key="manual_assess_btn"):
            run_manual_assessment(selected_categories, include_remediation)


def generate_csv_template(category_key):
    """Generate a CSV template for a specific category"""
    category = OPRA_CATEGORIES.get(category_key, {})
    controls = category.get('controls', [])
    
    # Create template with headers and example data
    lines = ["control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date"]
    
    for ctrl in controls:
        detailed = get_control_by_id(ctrl['id'])
        default_sev = detailed.default_severity.value if detailed else "Medium"
        lines.append(f'{ctrl["id"]},"{ctrl["name"]}",Not Assessed,{default_sev},"","",""," "')
    
    return "\n".join(lines)


def generate_master_csv_template():
    """Generate a combined CSV template with all categories"""
    lines = ["category,control_id,control_name,status,severity,evidence,notes,assessed_by,assessment_date"]
    
    for cat_key, category in OPRA_CATEGORIES.items():
        for ctrl in category.get('controls', []):
            detailed = get_control_by_id(ctrl['id'])
            default_sev = detailed.default_severity.value if detailed else "Medium"
            lines.append(f'"{category["name"]}",{ctrl["id"]},"{ctrl["name"]}",Not Assessed,{default_sev},"","",""," "')
    
    return "\n".join(lines)


def generate_unified_export_script():
    """Generate a single unified PowerShell export script with interactive menu"""
    
    script = '''#Requires -Version 5.1
<#
.SYNOPSIS
    SOPRA Data Export Tool - Unified Export Script
    
.DESCRIPTION
    This script exports security configuration data from your Windows environment
    for analysis by SOPRA (SAE On-Premise Risk Assessment). All operations are READ-ONLY
    and do not modify your system.
    
.NOTES
    Version: 1.0
    Author: SOPRA Security Tool
    
.EXAMPLE
    .\\SOPRA-Export.ps1
    Runs the interactive menu to select what data to export.
    
.EXAMPLE
    .\\SOPRA-Export.ps1 -ExportAll
    Exports all available data without prompting.
#>

param(
    [switch]$ExportAll,
    [string]$OutputPath = "C:\\SOPRA_Exports"
)

# ============================================================================
# CONFIGURATION
# ============================================================================
$Script:ExportPath = $OutputPath
$Script:ExportedFiles = @()

# Create output directory
function Initialize-ExportDirectory {
    if (-not (Test-Path $Script:ExportPath)) {
        New-Item -ItemType Directory -Force -Path $Script:ExportPath | Out-Null
    }
    Write-Host ""
    Write-Host "  Export Directory: $Script:ExportPath" -ForegroundColor Cyan
    Write-Host ""
}

# ============================================================================
# BANNER
# ============================================================================
function Show-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║                                                               ║" -ForegroundColor Cyan
    Write-Host "  ║   ██████╗ ██████╗ ██████╗  █████╗                            ║" -ForegroundColor Cyan
    Write-Host "  ║  ██╔═══██╗██╔══██╗██╔══██╗██╔══██╗                           ║" -ForegroundColor Cyan
    Write-Host "  ║  ██║   ██║██████╔╝██████╔╝███████║                           ║" -ForegroundColor Cyan
    Write-Host "  ║  ██║   ██║██╔═══╝ ██╔══██╗██╔══██║                           ║" -ForegroundColor Cyan
    Write-Host "  ║  ╚██████╔╝██║     ██║  ██║██║  ██║                           ║" -ForegroundColor Cyan
    Write-Host "  ║   ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝                           ║" -ForegroundColor Cyan
    Write-Host "  ║                                                               ║" -ForegroundColor Cyan
    Write-Host "  ║          On-Premise Risk Assessment - Data Export            ║" -ForegroundColor White
    Write-Host "  ║                                                               ║" -ForegroundColor Cyan
    Write-Host "  ╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  This tool exports security data for SOPRA analysis." -ForegroundColor Gray
    Write-Host "  All operations are READ-ONLY and safe to run." -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# MAIN MENU
# ============================================================================
function Show-MainMenu {
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │                      MAIN MENU                              │" -ForegroundColor DarkCyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │                                                             │" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Active Directory Security                           │" -ForegroundColor White
    Write-Host "  │   [2]  Network Infrastructure                              │" -ForegroundColor White
    Write-Host "  │   [3]  Endpoint Security                                   │" -ForegroundColor White
    Write-Host "  │   [4]  Server Security                                     │" -ForegroundColor White
    Write-Host "  │   [5]  Data Protection                                     │" -ForegroundColor White
    Write-Host "  │   [6]  Identity & Access Management                        │" -ForegroundColor White
    Write-Host "  │   [7]  Monitoring & Logging                                │" -ForegroundColor White
    Write-Host "  │                                                             │" -ForegroundColor DarkCyan
    Write-Host "  │   [A]  Export ALL Categories                               │" -ForegroundColor Green
    Write-Host "  │   [V]  View Exported Files                                 │" -ForegroundColor Yellow
    Write-Host "  │   [Q]  Quit                                                │" -ForegroundColor Red
    Write-Host "  │                                                             │" -ForegroundColor DarkCyan
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

# ============================================================================
# CATEGORY SUBMENUS
# ============================================================================
function Show-ADMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            ACTIVE DIRECTORY SECURITY                        │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Domain Admins                                       │" -ForegroundColor White
    Write-Host "  │   [2]  Service Accounts                                    │" -ForegroundColor White
    Write-Host "  │   [3]  Group Policy Objects (GPOs)                         │" -ForegroundColor White
    Write-Host "  │   [4]  Privileged Groups                                   │" -ForegroundColor White
    Write-Host "  │   [5]  Stale/Inactive Accounts                             │" -ForegroundColor White
    Write-Host "  │   [A]  Export All AD Data                                  │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-NetworkMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            NETWORK INFRASTRUCTURE                           │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Firewall Rules                                      │" -ForegroundColor White
    Write-Host "  │   [2]  Network Configuration                               │" -ForegroundColor White
    Write-Host "  │   [3]  DNS Configuration                                   │" -ForegroundColor White
    Write-Host "  │   [4]  Open Ports & Listeners                              │" -ForegroundColor White
    Write-Host "  │   [A]  Export All Network Data                             │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-EndpointMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            ENDPOINT SECURITY                                │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Windows Defender Status                             │" -ForegroundColor White
    Write-Host "  │   [2]  Installed Software                                  │" -ForegroundColor White
    Write-Host "  │   [3]  Running Services                                    │" -ForegroundColor White
    Write-Host "  │   [4]  Scheduled Tasks                                     │" -ForegroundColor White
    Write-Host "  │   [A]  Export All Endpoint Data                            │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-ServerMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            SERVER SECURITY                                  │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Installed Roles & Features                          │" -ForegroundColor White
    Write-Host "  │   [2]  Windows Updates                                     │" -ForegroundColor White
    Write-Host "  │   [3]  IIS Configuration (if installed)                    │" -ForegroundColor White
    Write-Host "  │   [A]  Export All Server Data                              │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-DataProtectionMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            DATA PROTECTION                                  │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  BitLocker Status                                    │" -ForegroundColor White
    Write-Host "  │   [2]  Shared Folders & Permissions                        │" -ForegroundColor White
    Write-Host "  │   [A]  Export All Data Protection Info                     │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-IAMMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            IDENTITY & ACCESS MANAGEMENT                     │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Local Administrators                                │" -ForegroundColor White
    Write-Host "  │   [2]  Local Users & Groups                                │" -ForegroundColor White
    Write-Host "  │   [3]  Password Policy                                     │" -ForegroundColor White
    Write-Host "  │   [A]  Export All IAM Data                                 │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

function Show-MonitoringMenu {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            MONITORING & LOGGING                             │" -ForegroundColor Cyan
    Write-Host "  ├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkCyan
    Write-Host "  │   [1]  Audit Policy                                        │" -ForegroundColor White
    Write-Host "  │   [2]  Event Log Configuration                             │" -ForegroundColor White
    Write-Host "  │   [3]  Recent Security Events                              │" -ForegroundColor White
    Write-Host "  │   [A]  Export All Monitoring Data                          │" -ForegroundColor Green
    Write-Host "  │   [B]  Back to Main Menu                                   │" -ForegroundColor Yellow
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

function Write-ExportStatus {
    param([string]$Message, [string]$Status = "INFO")
    
    switch ($Status) {
        "OK"      { Write-Host "  [OK] " -ForegroundColor Green -NoNewline; Write-Host $Message }
        "FAIL"    { Write-Host "  [FAIL] " -ForegroundColor Red -NoNewline; Write-Host $Message }
        "SKIP"    { Write-Host "  [SKIP] " -ForegroundColor Yellow -NoNewline; Write-Host $Message }
        "INFO"    { Write-Host "  [INFO] " -ForegroundColor Cyan -NoNewline; Write-Host $Message }
        default   { Write-Host "  $Message" }
    }
}

# --- ACTIVE DIRECTORY ---
function Export-DomainAdmins {
    try {
        $data = Get-ADGroupMember -Identity "Domain Admins" -ErrorAction Stop | 
            Get-ADUser -Properties LastLogonDate, Enabled, PasswordLastSet, Description |
            Select-Object SamAccountName, Name, Enabled, LastLogonDate, PasswordLastSet, Description
        $file = "$Script:ExportPath\\ad_domain_admins.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Domain Admins -> $file" "OK"
    } catch {
        Write-ExportStatus "Domain Admins - AD module not available or not on domain" "SKIP"
    }
}

function Export-ServiceAccounts {
    try {
        $data = Get-ADUser -Filter {ServicePrincipalName -like "*"} -Properties ServicePrincipalName, PasswordLastSet, Enabled, Description -ErrorAction Stop |
            Select-Object SamAccountName, Name, Enabled, PasswordLastSet, Description, @{N='SPNs';E={$_.ServicePrincipalName -join "; "}}
        $file = "$Script:ExportPath\\ad_service_accounts.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Service Accounts -> $file" "OK"
    } catch {
        Write-ExportStatus "Service Accounts - AD module not available" "SKIP"
    }
}

function Export-GPOs {
    try {
        $data = Get-GPO -All -ErrorAction Stop | 
            Select-Object DisplayName, Id, GpoStatus, CreationTime, ModificationTime
        $file = "$Script:ExportPath\\ad_gpos.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Group Policy Objects -> $file" "OK"
    } catch {
        Write-ExportStatus "GPOs - GroupPolicy module not available" "SKIP"
    }
}

function Export-PrivilegedGroups {
    try {
        $groups = @("Domain Admins", "Enterprise Admins", "Schema Admins", "Administrators", "Account Operators", "Backup Operators")
        $allMembers = @()
        foreach ($group in $groups) {
            try {
                $members = Get-ADGroupMember -Identity $group -ErrorAction SilentlyContinue
                foreach ($member in $members) {
                    $allMembers += [PSCustomObject]@{
                        GroupName = $group
                        MemberName = $member.Name
                        MemberType = $member.objectClass
                        SamAccountName = $member.SamAccountName
                    }
                }
            } catch { }
        }
        $file = "$Script:ExportPath\\ad_privileged_groups.csv"
        $allMembers | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Privileged Groups -> $file" "OK"
    } catch {
        Write-ExportStatus "Privileged Groups - AD module not available" "SKIP"
    }
}

function Export-StaleAccounts {
    try {
        $staleDate = (Get-Date).AddDays(-90)
        $data = Get-ADUser -Filter {LastLogonDate -lt $staleDate -and Enabled -eq $true} -Properties LastLogonDate, PasswordLastSet -ErrorAction Stop |
            Select-Object SamAccountName, Name, LastLogonDate, PasswordLastSet
        $file = "$Script:ExportPath\\ad_stale_accounts.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Stale Accounts (90+ days) -> $file" "OK"
    } catch {
        Write-ExportStatus "Stale Accounts - AD module not available" "SKIP"
    }
}

# --- NETWORK ---
function Export-FirewallRules {
    try {
        $data = Get-NetFirewallRule -ErrorAction Stop | 
            Select-Object Name, DisplayName, Enabled, Direction, Action, Profile
        $file = "$Script:ExportPath\\network_firewall_rules.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Firewall Rules -> $file" "OK"
    } catch {
        Write-ExportStatus "Firewall Rules - NetSecurity module not available" "SKIP"
    }
}

function Export-NetworkConfig {
    try {
        $data = Get-NetIPConfiguration -ErrorAction Stop | 
            Select-Object InterfaceAlias, @{N='IPv4Address';E={$_.IPv4Address.IPAddress}}, 
                          @{N='Gateway';E={$_.IPv4DefaultGateway.NextHop}},
                          @{N='DNS';E={$_.DNSServer.ServerAddresses -join "; "}}
        $file = "$Script:ExportPath\\network_config.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Network Configuration -> $file" "OK"
    } catch {
        Write-ExportStatus "Network Configuration failed" "FAIL"
    }
}

function Export-DNSConfig {
    try {
        $data = Get-DnsClientServerAddress -ErrorAction Stop | 
            Where-Object { $_.ServerAddresses } |
            Select-Object InterfaceAlias, @{N='DNSServers';E={$_.ServerAddresses -join "; "}}
        $file = "$Script:ExportPath\\network_dns.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "DNS Configuration -> $file" "OK"
    } catch {
        Write-ExportStatus "DNS Configuration failed" "FAIL"
    }
}

function Export-OpenPorts {
    try {
        $data = Get-NetTCPConnection -State Listen -ErrorAction Stop | 
            Select-Object LocalAddress, LocalPort, OwningProcess, 
                          @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}}
        $file = "$Script:ExportPath\\network_open_ports.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Open Ports -> $file" "OK"
    } catch {
        Write-ExportStatus "Open Ports failed" "FAIL"
    }
}

# --- ENDPOINT ---
function Export-DefenderStatus {
    try {
        $data = Get-MpComputerStatus -ErrorAction Stop | 
            Select-Object AMServiceEnabled, AntispywareEnabled, AntivirusEnabled, 
                          RealTimeProtectionEnabled, AntivirusSignatureLastUpdated, NISEnabled
        $file = "$Script:ExportPath\\endpoint_defender.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Windows Defender Status -> $file" "OK"
    } catch {
        Write-ExportStatus "Windows Defender - Defender module not available" "SKIP"
    }
}

function Export-InstalledSoftware {
    try {
        $data = Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* -ErrorAction Stop |
            Where-Object { $_.DisplayName } |
            Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
        $file = "$Script:ExportPath\\endpoint_software.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Installed Software -> $file" "OK"
    } catch {
        Write-ExportStatus "Installed Software failed" "FAIL"
    }
}

function Export-RunningServices {
    try {
        $data = Get-Service | 
            Select-Object Name, DisplayName, Status, StartType
        $file = "$Script:ExportPath\\endpoint_services.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Running Services -> $file" "OK"
    } catch {
        Write-ExportStatus "Running Services failed" "FAIL"
    }
}

function Export-ScheduledTasks {
    try {
        $data = Get-ScheduledTask -ErrorAction Stop | 
            Where-Object { $_.State -ne "Disabled" } |
            Select-Object TaskName, TaskPath, State, @{N='Author';E={$_.Principal.UserId}}
        $file = "$Script:ExportPath\\endpoint_scheduled_tasks.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Scheduled Tasks -> $file" "OK"
    } catch {
        Write-ExportStatus "Scheduled Tasks failed" "FAIL"
    }
}

# --- SERVER ---
function Export-ServerFeatures {
    try {
        $data = Get-WindowsFeature -ErrorAction Stop | 
            Where-Object { $_.Installed } |
            Select-Object Name, DisplayName, FeatureType
        $file = "$Script:ExportPath\\server_features.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Server Features -> $file" "OK"
    } catch {
        Write-ExportStatus "Server Features - Not a Windows Server or feature not available" "SKIP"
    }
}

function Export-WindowsUpdates {
    try {
        $Session = New-Object -ComObject Microsoft.Update.Session
        $Searcher = $Session.CreateUpdateSearcher()
        $History = $Searcher.QueryHistory(0, 50)
        $data = $History | Select-Object Title, @{N='Date';E={$_.Date}}, 
                                         @{N='Status';E={switch($_.ResultCode){1{"InProgress"};2{"Succeeded"};3{"SucceededWithErrors"};4{"Failed"};5{"Aborted"}}}}
        $file = "$Script:ExportPath\\server_updates.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Windows Updates (last 50) -> $file" "OK"
    } catch {
        Write-ExportStatus "Windows Updates failed" "FAIL"
    }
}

function Export-IISConfig {
    try {
        Import-Module WebAdministration -ErrorAction Stop
        $data = Get-Website -ErrorAction Stop | 
            Select-Object Name, State, PhysicalPath, @{N='Bindings';E={$_.Bindings.Collection.bindingInformation -join "; "}}
        $file = "$Script:ExportPath\\server_iis.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "IIS Configuration -> $file" "OK"
    } catch {
        Write-ExportStatus "IIS - Not installed or WebAdministration module not available" "SKIP"
    }
}

# --- DATA PROTECTION ---
function Export-BitLocker {
    try {
        $data = Get-BitLockerVolume -ErrorAction Stop | 
            Select-Object MountPoint, VolumeStatus, EncryptionMethod, ProtectionStatus, LockStatus
        $file = "$Script:ExportPath\\data_bitlocker.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "BitLocker Status -> $file" "OK"
    } catch {
        Write-ExportStatus "BitLocker - Module not available or requires elevation" "SKIP"
    }
}

function Export-SharedFolders {
    try {
        $data = Get-SmbShare -ErrorAction Stop | 
            Where-Object { $_.Name -notlike "*$" } |
            Select-Object Name, Path, Description, CurrentUsers
        $file = "$Script:ExportPath\\data_shares.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Shared Folders -> $file" "OK"
    } catch {
        Write-ExportStatus "Shared Folders failed" "FAIL"
    }
}

# --- IAM ---
function Export-LocalAdmins {
    try {
        $data = Get-LocalGroupMember -Group "Administrators" -ErrorAction Stop |
            Select-Object Name, ObjectClass, PrincipalSource
        $file = "$Script:ExportPath\\iam_local_admins.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Local Administrators -> $file" "OK"
    } catch {
        Write-ExportStatus "Local Administrators - LocalAccounts module not available" "SKIP"
    }
}

function Export-LocalUsers {
    try {
        $data = Get-LocalUser -ErrorAction Stop |
            Select-Object Name, Enabled, PasswordRequired, PasswordLastSet, LastLogon
        $file = "$Script:ExportPath\\iam_local_users.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Local Users -> $file" "OK"
    } catch {
        Write-ExportStatus "Local Users failed" "FAIL"
    }
}

function Export-PasswordPolicy {
    try {
        $policy = net accounts 2>&1
        $file = "$Script:ExportPath\\iam_password_policy.txt"
        $policy | Out-File $file
        $Script:ExportedFiles += $file
        Write-ExportStatus "Password Policy -> $file" "OK"
    } catch {
        Write-ExportStatus "Password Policy failed" "FAIL"
    }
}

# --- MONITORING ---
function Export-AuditPolicy {
    try {
        $file = "$Script:ExportPath\\monitoring_audit_policy.csv"
        $auditData = auditpol /get /category:* /r 2>&1 | ConvertFrom-Csv
        $auditData | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Audit Policy -> $file" "OK"
    } catch {
        Write-ExportStatus "Audit Policy failed" "FAIL"
    }
}

function Export-EventLogConfig {
    try {
        $data = Get-WinEvent -ListLog Security, System, Application -ErrorAction Stop |
            Select-Object LogName, MaximumSizeInBytes, RecordCount, IsEnabled, LogMode
        $file = "$Script:ExportPath\\monitoring_eventlog_config.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Event Log Configuration -> $file" "OK"
    } catch {
        Write-ExportStatus "Event Log Configuration failed" "FAIL"
    }
}

function Export-RecentSecurityEvents {
    try {
        $data = Get-WinEvent -LogName Security -MaxEvents 100 -ErrorAction Stop |
            Select-Object TimeCreated, Id, LevelDisplayName, Message
        $file = "$Script:ExportPath\\monitoring_security_events.csv"
        $data | Export-Csv $file -NoTypeInformation
        $Script:ExportedFiles += $file
        Write-ExportStatus "Recent Security Events (100) -> $file" "OK"
    } catch {
        Write-ExportStatus "Security Events - Access denied or log not available" "SKIP"
    }
}

# ============================================================================
# BULK EXPORT FUNCTIONS
# ============================================================================
function Export-AllAD {
    Write-Host ""
    Write-Host "  Exporting Active Directory data..." -ForegroundColor Cyan
    Export-DomainAdmins
    Export-ServiceAccounts
    Export-GPOs
    Export-PrivilegedGroups
    Export-StaleAccounts
}

function Export-AllNetwork {
    Write-Host ""
    Write-Host "  Exporting Network data..." -ForegroundColor Cyan
    Export-FirewallRules
    Export-NetworkConfig
    Export-DNSConfig
    Export-OpenPorts
}

function Export-AllEndpoint {
    Write-Host ""
    Write-Host "  Exporting Endpoint data..." -ForegroundColor Cyan
    Export-DefenderStatus
    Export-InstalledSoftware
    Export-RunningServices
    Export-ScheduledTasks
}

function Export-AllServer {
    Write-Host ""
    Write-Host "  Exporting Server data..." -ForegroundColor Cyan
    Export-ServerFeatures
    Export-WindowsUpdates
    Export-IISConfig
}

function Export-AllDataProtection {
    Write-Host ""
    Write-Host "  Exporting Data Protection info..." -ForegroundColor Cyan
    Export-BitLocker
    Export-SharedFolders
}

function Export-AllIAM {
    Write-Host ""
    Write-Host "  Exporting IAM data..." -ForegroundColor Cyan
    Export-LocalAdmins
    Export-LocalUsers
    Export-PasswordPolicy
}

function Export-AllMonitoring {
    Write-Host ""
    Write-Host "  Exporting Monitoring data..." -ForegroundColor Cyan
    Export-AuditPolicy
    Export-EventLogConfig
    Export-RecentSecurityEvents
}

function Export-Everything {
    Write-Host ""
    Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  EXPORTING ALL CATEGORIES" -ForegroundColor Cyan
    Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Export-AllAD
    Export-AllNetwork
    Export-AllEndpoint
    Export-AllServer
    Export-AllDataProtection
    Export-AllIAM
    Export-AllMonitoring
    Show-ExportSummary
}

function Show-ExportSummary {
    Write-Host ""
    Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  EXPORT COMPLETE" -ForegroundColor Green
    Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Files exported: $($Script:ExportedFiles.Count)" -ForegroundColor White
    Write-Host "  Location: $Script:ExportPath" -ForegroundColor White
    Write-Host ""
    Write-Host "  Upload these CSV files to SOPRA for security assessment." -ForegroundColor Cyan
    Write-Host ""
}

function Show-ExportedFiles {
    Write-Host ""
    Write-Host "  ┌─────────────────────────────────────────────────────────────┐" -ForegroundColor DarkCyan
    Write-Host "  │            EXPORTED FILES                                   │" -ForegroundColor Cyan
    Write-Host "  └─────────────────────────────────────────────────────────────┘" -ForegroundColor DarkCyan
    Write-Host ""
    
    if ($Script:ExportedFiles.Count -eq 0) {
        Write-Host "  No files exported yet." -ForegroundColor Yellow
    } else {
        foreach ($file in $Script:ExportedFiles) {
            $fileName = Split-Path $file -Leaf
            Write-Host "  - $fileName" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "  Location: $Script:ExportPath" -ForegroundColor Cyan
    }
    Write-Host ""
}

# ============================================================================
# MENU HANDLERS
# ============================================================================
function Handle-ADMenu {
    do {
        Show-ADMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-DomainAdmins }
            "2" { Export-ServiceAccounts }
            "3" { Export-GPOs }
            "4" { Export-PrivilegedGroups }
            "5" { Export-StaleAccounts }
            "A" { Export-AllAD }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-NetworkMenu {
    do {
        Show-NetworkMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-FirewallRules }
            "2" { Export-NetworkConfig }
            "3" { Export-DNSConfig }
            "4" { Export-OpenPorts }
            "A" { Export-AllNetwork }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-EndpointMenu {
    do {
        Show-EndpointMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-DefenderStatus }
            "2" { Export-InstalledSoftware }
            "3" { Export-RunningServices }
            "4" { Export-ScheduledTasks }
            "A" { Export-AllEndpoint }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-ServerMenu {
    do {
        Show-ServerMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-ServerFeatures }
            "2" { Export-WindowsUpdates }
            "3" { Export-IISConfig }
            "A" { Export-AllServer }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-DataProtectionMenu {
    do {
        Show-DataProtectionMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-BitLocker }
            "2" { Export-SharedFolders }
            "A" { Export-AllDataProtection }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-IAMMenu {
    do {
        Show-IAMMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-LocalAdmins }
            "2" { Export-LocalUsers }
            "3" { Export-PasswordPolicy }
            "A" { Export-AllIAM }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

function Handle-MonitoringMenu {
    do {
        Show-MonitoringMenu
        $choice = Read-Host "  Select option"
        switch ($choice.ToUpper()) {
            "1" { Export-AuditPolicy }
            "2" { Export-EventLogConfig }
            "3" { Export-RecentSecurityEvents }
            "A" { Export-AllMonitoring }
            "B" { return }
        }
        if ($choice -ne "B") {
            Read-Host "  Press Enter to continue"
        }
    } while ($choice.ToUpper() -ne "B")
}

# ============================================================================
# MAIN
# ============================================================================
Initialize-ExportDirectory

if ($ExportAll) {
    Show-Banner
    Export-Everything
    exit
}

do {
    Show-Banner
    Show-MainMenu
    $choice = Read-Host "  Select option"
    
    switch ($choice.ToUpper()) {
        "1" { Handle-ADMenu }
        "2" { Handle-NetworkMenu }
        "3" { Handle-EndpointMenu }
        "4" { Handle-ServerMenu }
        "5" { Handle-DataProtectionMenu }
        "6" { Handle-IAMMenu }
        "7" { Handle-MonitoringMenu }
        "A" { Export-Everything; Read-Host "  Press Enter to continue" }
        "V" { Show-ExportedFiles; Read-Host "  Press Enter to continue" }
        "Q" { 
            Write-Host ""
            Write-Host "  Thank you for using SOPRA Export Tool!" -ForegroundColor Cyan
            Write-Host ""
            exit 
        }
    }
} while ($true)
'''
    
    return script


def process_csv_assessment(uploaded_files, selected_categories, include_remediation):
    """Process uploaded CSV files and run assessment"""
    all_findings = []
    
    with st.spinner("Processing CSV files..."):
        for uploaded_file in uploaded_files:
            try:
                # Reset file position to beginning (important after preview)
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file)
                
                # Process each row as a finding
                for _, row in df.iterrows():
                    finding = {
                        "control_id": row.get('control_id', 'UNKNOWN'),
                        "control_name": row.get('control_name', 'Unknown Control'),
                        "category": row.get('category', 'Uncategorized'),
                        "family": row.get('family', '') or lookup_family(row.get('control_id', '')),
                        "status": row.get('status', 'Not Assessed'),
                        "severity": row.get('severity', None) if row.get('status') == 'Failed' else None,
                        "evidence": row.get('evidence', ''),
                        "notes": row.get('notes', ''),
                        "assessed_by": row.get('assessed_by', 'CSV Import'),
                        "assessment_date": row.get('assessment_date', datetime.now().isoformat())
                    }
                    all_findings.append(finding)
                    
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
    
    if all_findings:
        # Store results
        st.session_state.opra_assessment_results = {
            "timestamp": datetime.now().isoformat(),
            "findings": all_findings,
            "categories_assessed": selected_categories,
            "include_remediation": include_remediation,
            "source": "CSV Import"
        }
        save_results_to_file(st.session_state.opra_assessment_results)
        
        st.success(f"✅ Assessment complete! Processed {len(all_findings)} controls from {len(uploaded_files)} file(s).")
        binary_rain()
        
        # Show quick summary
        passed = len([f for f in all_findings if f['status'] == 'Passed'])
        failed = len([f for f in all_findings if f['status'] == 'Failed'])
        not_assessed = len([f for f in all_findings if f['status'] == 'Not Assessed'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Passed", passed, delta=None)
        with col2:
            st.metric("Failed", failed, delta=None, delta_color="inverse")
        with col3:
            st.metric("Not Assessed", not_assessed)
        
        if st.button("📊 View Full Report", type="primary", use_container_width=True):
            st.session_state.opra_active_tab = "Reports"
            st.rerun()
    else:
        st.warning("⚠️ No valid assessment data found in the uploaded files.")


def run_manual_assessment(categories, include_remediation):
    """Run a manual assessment questionnaire with detailed control information"""
    findings = []
    
    st.markdown("---")
    st.markdown("### 📝 Assessment Questionnaire")
    
    for cat_key in categories:
        category = OPRA_CATEGORIES[cat_key]
        
        with st.expander(f"{category['icon']} {category['name']}", expanded=False):
            for control_ref in category['controls']:
                # Get detailed control from sopra_controls.py
                detailed_control = get_control_by_id(control_ref['id'])
                
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{control_ref['id']}**: {control_ref['name']}")
                    st.caption(f"Family: {control_ref['family']}")
                    
                    # Show detailed info if available
                    if detailed_control:
                        with st.popover("ℹ️ Details"):
                            st.markdown(f"**Description:** {detailed_control.description}")
                            st.markdown("**Check Procedure:**")
                            st.code(detailed_control.check_procedure.strip(), language=None)
                            st.markdown(f"**Expected Result:** {detailed_control.expected_result}")
                            if detailed_control.nist_mapping:
                                st.markdown(f"**NIST Mapping:** {', '.join(detailed_control.nist_mapping)}")
                            if detailed_control.cis_mapping:
                                st.markdown(f"**CIS Mapping:** {detailed_control.cis_mapping}")
                
                with col2:
                    # Default severity from detailed control
                    default_sev = detailed_control.default_severity.value if detailed_control else "Medium"
                    
                    status = st.selectbox(
                        "Status",
                        ["Not Assessed", "Passed", "Failed", "N/A"],
                        key=f"status_{control_ref['id']}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    if status == "Failed":
                        severity_options = ["Low", "Medium", "High", "Critical"]
                        default_idx = severity_options.index(default_sev) if default_sev in severity_options else 1
                        severity = st.selectbox(
                            "Severity",
                            severity_options,
                            index=default_idx,
                            key=f"severity_{control_ref['id']}",
                            label_visibility="collapsed"
                        )
                    else:
                        severity = "N/A"
                        st.text("N/A")
                
                findings.append({
                    "control_id": control_ref['id'],
                    "control_name": control_ref['name'],
                    "category": category['name'],
                    "family": control_ref['family'],
                    "status": status,
                    "severity": severity if status == "Failed" else None
                })
    
    if st.button("✅ Complete Assessment", type="primary", use_container_width=True):
        st.session_state.opra_assessment_results = {
            "timestamp": datetime.now().isoformat(),
            "findings": findings,
            "categories_assessed": categories,
            "include_remediation": include_remediation
        }
        save_results_to_file(st.session_state.opra_assessment_results)
        st.success("🎉 Assessment completed! View results in the Reports tab.")
        binary_rain()


