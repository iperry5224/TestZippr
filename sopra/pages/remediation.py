"""SOPRA Remediation Pop-out Page"""
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import time

from sopra_controls import get_control_by_id, get_remediation_script
from sopra.theme import (
    COLOR_PASSED, COLOR_FAILED, COLOR_CRITICAL, COLOR_HIGH, COLOR_MEDIUM, COLOR_LOW,
    SEV_COLORS, SEV_ICONS, SEV_ORDER, FAMILY_ABBREV
)
from sopra.persistence import load_results_from_file
from sopra.utils import calculate_risk_score
from sopra.isso.ai_remediation import detect_attack_chains, get_validation_script

def binary_rain():
    """Display a Matrix-style binary code rain animation"""
    st.markdown("""
    <style>
    @keyframes binaryFall {
        0% { transform: translateY(-100vh); opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { transform: translateY(100vh); opacity: 0; }
    }
    .binary-rain-container {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        pointer-events: none; z-index: 99999; overflow: hidden;
    }
    .binary-column {
        position: absolute; top: -100vh;
        font-family: 'Courier New', monospace;
        font-size: 14px; line-height: 1.2;
        color: #00d9ff; text-shadow: 0 0 8px #00d9ff, 0 0 20px #00d9ff55;
        white-space: pre; writing-mode: vertical-rl;
        animation: binaryFall var(--fall-duration) linear forwards;
        opacity: 0;
    }
    </style>
    <div class="binary-rain-container" id="binaryRain"></div>
    <script>
    (function() {
        const container = document.getElementById('binaryRain');
        if (!container) return;
        const cols = 35;
        const colors = ['#00d9ff', '#00ff88', '#00d9ff', '#00ffcc', '#00d9ff'];
        for (let i = 0; i < cols; i++) {
            const col = document.createElement('div');
            col.className = 'binary-column';
            let bits = '';
            const len = 15 + Math.floor(Math.random() * 25);
            for (let j = 0; j < len; j++) {
                bits += Math.random() > 0.5 ? '1' : '0';
                if (Math.random() > 0.85) bits += ' ';
            }
            col.textContent = bits;
            col.style.left = (Math.random() * 100) + 'vw';
            const duration = 2 + Math.random() * 3;
            col.style.setProperty('--fall-duration', duration + 's');
            col.style.animationDelay = (Math.random() * 2) + 's';
            col.style.color = colors[Math.floor(Math.random() * colors.length)];
            col.style.fontSize = (10 + Math.floor(Math.random() * 8)) + 'px';
            col.style.opacity = (0.4 + Math.random() * 0.6);
            container.appendChild(col);
        }
        setTimeout(() => { container.remove(); }, 6000);
    })();
    </script>
    """, unsafe_allow_html=True)


def show_remediation_content(results=None):
    """Render remediation report content (used by both pop-out page and inline)"""
    if results is None:
        results = st.session_state.get("opra_assessment_results")
    if not results or not results.get("findings"):
        from sopra.persistence import load_results_from_file
        results = load_results_from_file()
        if results:
            st.session_state.opra_assessment_results = results
    if not results or not results.get("findings"):
        st.warning("No assessment data available. Run an assessment first.")
        return
    
    findings = results["findings"]
    failed_findings = [f for f in findings if f["status"] == "Failed"]
    
    if not failed_findings:
        st.success("No failed controls — your environment is fully compliant!")
        return
    
    # ── Compute metrics ──
    severity_order = SEV_ORDER
    sev_colors = SEV_COLORS
    sev_icons = SEV_ICONS
    sev_timelines = {"Critical": "Immediate", "High": "7 days", "Medium": "30 days", "Low": "Next window"}
    total_findings = len(findings)

    sev_counts = {}
    for sev in severity_order:
        sev_counts[sev] = len([f for f in failed_findings if f.get("severity") == sev])

    compliance_pct = round(((total_findings - len(failed_findings)) / max(total_findings, 1)) * 100, 1)
    risk_score = min(100, sev_counts.get("Critical", 0) * 25 + sev_counts.get("High", 0) * 15
                     + sev_counts.get("Medium", 0) * 8 + sev_counts.get("Low", 0) * 3)
    threat_color = "#e94560" if risk_score >= 70 else "#ff6b6b" if risk_score >= 40 else "#ffc107" if risk_score >= 20 else "#00ff88"
    threat_label = "CRITICAL" if risk_score >= 70 else "HIGH" if risk_score >= 40 else "ELEVATED" if risk_score >= 20 else "LOW"

    # ── Threat Overview — 3 big KPI cards ──
    _cb = "background:rgba(13,17,23,0.7);backdrop-filter:blur(12px);border-radius:14px;padding:0.9rem 0.7rem;text-align:center;"
    _kl = "font-size:0.58rem;letter-spacing:2.5px;color:#4a6a8a;text-transform:uppercase;"
    _bar_bg = "margin-top:0.5rem;height:3px;background:rgba(255,255,255,0.06);border-radius:2px;overflow:hidden;"
    _passed = total_findings - len(failed_findings)
    _fail_pct = f"{min(100, len(failed_findings) / max(total_findings, 1) * 100):.0f}"

    kpi_html = (
        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.7rem;margin-bottom:1rem;">'
        # Threat Level
        + '<div style="' + _cb + 'border:1px solid ' + threat_color + '40;box-shadow:0 4px 24px ' + threat_color + '18;animation:fade-up 0.5s ease-out both;">'
        + '<div style="' + _kl + '">Threat Level</div>'
        + '<div style="font-size:2rem;font-weight:800;color:' + threat_color + ';text-shadow:0 0 24px ' + threat_color + '55;line-height:1.2;margin:0.3rem 0 0.1rem;">' + str(risk_score) + '</div>'
        + '<div style="font-size:0.6rem;font-weight:700;color:' + threat_color + ';letter-spacing:3px;">' + threat_label + '</div>'
        + '<div style="' + _bar_bg + '"><div style="width:' + str(risk_score) + '%;height:100%;border-radius:2px;background:linear-gradient(90deg,#00ff88,#ffc107,#e94560);"></div></div>'
        + '</div>'
        # Compliance Rate
        + '<div style="' + _cb + 'border:1px solid rgba(0,255,136,0.18);animation:fade-up 0.5s ease-out 0.1s both;">'
        + '<div style="' + _kl + '">Compliance Rate</div>'
        + '<div style="font-size:2rem;font-weight:800;color:#00ff88;text-shadow:0 0 24px rgba(0,255,136,0.35);line-height:1.2;margin:0.3rem 0 0.1rem;">' + str(compliance_pct) + '%</div>'
        + '<div style="font-size:0.6rem;color:#4a6a8a;">' + str(_passed) + ' of ' + str(total_findings) + ' passed</div>'
        + '<div style="' + _bar_bg + '"><div style="width:' + str(compliance_pct) + '%;height:100%;background:#00ff88;border-radius:2px;"></div></div>'
        + '</div>'
        # Failed Controls
        + '<div style="' + _cb + 'border:1px solid rgba(233,69,96,0.18);animation:fade-up 0.5s ease-out 0.2s both;">'
        + '<div style="' + _kl + '">Failed Controls</div>'
        + '<div style="font-size:2rem;font-weight:800;color:#e94560;text-shadow:0 0 24px rgba(233,69,96,0.35);line-height:1.2;margin:0.3rem 0 0.1rem;">' + str(len(failed_findings)) + '</div>'
        + '<div style="font-size:0.6rem;color:#4a6a8a;">Require remediation</div>'
        + '<div style="' + _bar_bg + '"><div style="width:' + _fail_pct + '%;height:100%;background:#e94560;border-radius:2px;"></div></div>'
        + '</div>'
        + '</div>'
    )
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ── Attack Chain Alerts (AI feature) ──
    chains = detect_attack_chains(findings)
    if chains:
        top_chain = chains[0]
        chain_count = len(chains)
        st.markdown(
            '<div style="background:linear-gradient(135deg,rgba(233,69,96,0.08),rgba(168,85,247,0.06));border:1px solid rgba(233,69,96,0.25);border-radius:12px;padding:0.7rem 1rem;margin-bottom:0.8rem;display:flex;align-items:center;gap:0.8rem;">'
            '<div style="font-size:1.5rem;">🔗</div>'
            '<div style="flex:1;">'
            '<div style="color:#e94560;font-weight:700;font-size:0.85rem;">' + str(chain_count) + ' Attack Chain' + ('s' if chain_count != 1 else '') + ' Detected</div>'
            '<div style="color:#6b839e;font-size:0.72rem;">Most critical: <b style="color:#c8d6e5;">' + top_chain["name"] + '</b> — ' + str(top_chain["match_pct"]) + '% exposed</div>'
            '<div style="color:#a855f7;font-size:0.68rem;margin-top:0.15rem;">🎯 ' + top_chain["break_point"] + '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    # Link to full AI Remediation Center
    st.link_button("🧠 Open AI Remediation Center (Attack Chains, Plans, Tickets & More)", "?view=ai_remed", use_container_width=True)

    # ── Severity Cards — animated glassmorphism with fill bars ──
    cards_html = '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.55rem; margin-bottom: 1rem;">'
    for i, sev in enumerate(severity_order):
        color = sev_colors[sev]
        count = sev_counts[sev]
        icon = sev_icons[sev]
        timeline = sev_timelines[sev]
        pct = round((count / max(len(failed_findings), 1)) * 100)
        pulse = "animation: pulse-critical 2s ease-in-out infinite;" if sev == "Critical" and count > 0 else ""
        delay = f"animation: fade-up 0.5s ease-out {0.3 + i * 0.12}s both;"

        sev_lower = sev.lower()
        cards_html += f"""
        <a href="#sev-{sev_lower}" style="text-decoration: none; color: inherit; display: block;
                    background: rgba(13,17,23,0.7); backdrop-filter: blur(12px);
                    border: 1px solid {color}28; border-radius: 12px; padding: 0.7rem 0.5rem;
                    text-align: center; position: relative; overflow: hidden; {delay} {pulse}
                    cursor: pointer; transition: all 0.25s ease;"
           onmouseover="this.style.borderColor='{color}';this.style.boxShadow='0 0 20px {color}33'"
           onmouseout="this.style.borderColor='{color}28';this.style.boxShadow='none'">
            <div style="position: absolute; bottom: 0; left: 0; width: 100%; height: {pct}%;
                        background: linear-gradient(to top, {color}12, transparent); pointer-events: none;
                        transition: height 1.2s ease;"></div>
            <div style="font-size: 1.5rem; filter: drop-shadow(0 0 8px {color}66); margin-bottom: 0.15rem;">{icon}</div>
            <div style="font-size: 1.7rem; font-weight: 800; color: {color}; text-shadow: 0 0 18px {color}44;
                        line-height: 1.1;">{count}</div>
            <div style="font-size: 0.62rem; font-weight: 600; color: #6b839e; text-transform: uppercase;
                        letter-spacing: 1.5px; margin: 0.15rem 0;">{sev}</div>
            <div style="font-size: 0.55rem; color: {color}77; border-top: 1px solid {color}18;
                        padding-top: 0.25rem; margin-top: 0.15rem;">{timeline}</div>
        </a>"""
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

    # ── Charts Row — Severity Donut + Category Breakdown ──
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        sev_vals = [sev_counts[s] for s in severity_order]
        sev_clrs = [sev_colors[s] for s in severity_order]
        fig_donut = go.Figure(go.Pie(
            labels=severity_order, values=sev_vals, hole=0.68,
            marker=dict(colors=sev_clrs, line=dict(color='#0d1117', width=2)),
            textinfo='label+value', textfont=dict(size=10, color='#c8d6e5'),
            hovertemplate='%{label}: %{value} findings<extra></extra>',
            direction='clockwise', sort=False
        ))
        fig_donut.update_layout(
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=210, margin=dict(l=8, r=8, t=28, b=8),
            title=dict(text='Severity Distribution', font=dict(size=11, color='#4a6a8a'), x=0.5, y=0.97),
            annotations=[dict(
                text=f'<b style="font-size:20px;color:#e0e0e0">{len(failed_findings)}</b><br>'
                     f'<span style="font-size:9px;color:#4a6a8a">FINDINGS</span>',
                x=0.5, y=0.5, font=dict(size=14, color='#e0e0e0'), showarrow=False)]
        )
        st.plotly_chart(fig_donut, use_container_width=True, key="remed_sev_donut")

    with chart_col2:
        cat_counts = {}
        for f in failed_findings:
            cat = f.get("category", "Unknown")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        cat_names = [c[0][:22] for c in sorted_cats]
        cat_vals = [c[1] for c in sorted_cats]
        fig_bar = go.Figure(go.Bar(
            x=cat_vals, y=cat_names, orientation='h',
            marker=dict(color=cat_vals,
                        colorscale=[[0, '#00d9ff'], [0.5, '#a855f7'], [1, '#e94560']],
                        line=dict(width=0), cornerradius=3),
            text=cat_vals, textposition='auto', textfont=dict(color='#fff', size=10)
        ))
        fig_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=210,
            margin=dict(l=8, r=8, t=28, b=8), bargap=0.25,
            title=dict(text='Failures by Category', font=dict(size=11, color='#4a6a8a'), x=0.5, y=0.97),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(tickfont=dict(size=8, color='#6b839e'), autorange='reversed')
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="remed_cat_bar")

    # ── Priority Timeline Bar ──
    total_fail = len(failed_findings)
    tl_html = """<div style="margin: 0.2rem 0 0.8rem;">
        <div style="font-size: 0.6rem; letter-spacing: 2.5px; color: #4a6a8a; text-transform: uppercase;
                    margin-bottom: 0.45rem;">&#9654; Remediation Priority</div>
        <div style="display: flex; gap: 3px; height: 24px; border-radius: 6px; overflow: hidden;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.3);">"""
    for sev in severity_order:
        cnt = sev_counts[sev]
        if cnt == 0:
            continue
        pct = (cnt / total_fail) * 100
        color = sev_colors[sev]
        tl_html += f"""<div style="width: {pct}%; background: linear-gradient(135deg, {color}, {color}bb);
                    display: flex; align-items: center; justify-content: center;
                    font-size: 0.55rem; font-weight: 700; color: #fff; text-shadow: 0 1px 3px rgba(0,0,0,0.5);
                    min-width: 28px;" title="{sev}: {cnt}">{sev[0]}:{cnt}</div>"""
    tl_html += '</div></div>'
    st.markdown(tl_html, unsafe_allow_html=True)
    
    # Findings by Severity
    downtime_required = []
    
    for sev in severity_order:
        sev_findings = [f for f in failed_findings if f.get("severity") == sev]
        if not sev_findings:
            continue
        
        color = sev_colors[sev]
        icon = sev_icons[sev]
        timeline = sev_timelines[sev]
        
        sev_anchor = sev.lower()
        _fc = str(len(sev_findings))
        _fs = 's' if len(sev_findings) != 1 else ''
        st.markdown(
            '<div id="sev-' + sev_anchor + '" style="background:linear-gradient(90deg,' + color + '14,' + color + '08,transparent);border-left:3px solid ' + color + ';padding:0.65rem 1rem;margin:1rem 0 0.45rem 0;border-radius:0 10px 10px 0;position:relative;overflow:hidden;scroll-margin-top:1rem;">'
            '<div style="position:absolute;right:0.8rem;top:50%;transform:translateY(-50%);font-size:2.2rem;font-weight:900;opacity:0.05;color:' + color + ';pointer-events:none;">' + _fc + '</div>'
            '<span style="color:' + color + ';font-size:1rem;font-weight:700;">' + icon + ' ' + sev + ' Severity</span>'
            '<span style="color:#c8d6e5;font-size:0.85rem;margin-left:0.25rem;">&mdash; ' + _fc + ' finding' + _fs + '</span>'
            '<span style="display:inline-block;background:' + color + '18;color:' + color + ';font-size:0.58rem;font-weight:600;padding:0.12rem 0.45rem;border-radius:20px;margin-left:0.5rem;letter-spacing:1px;border:1px solid ' + color + '30;">' + timeline + '</span>'
            '</div>',
            unsafe_allow_html=True
        )
        
        for finding in sev_findings:
            control = get_control_by_id(finding.get("control_id", ""))
            
            with st.expander(f"{icon} {finding.get('control_id', 'N/A')} — {finding.get('control_name', 'Unknown')}", expanded=(sev == "Critical")):
                st.markdown(f"**Category:** {finding.get('category', 'N/A')} | **Family:** {finding.get('family', 'N/A')}")
                if finding.get('evidence'):
                    st.markdown(f"**Evidence:** {finding['evidence']}")
                if finding.get('notes'):
                    st.markdown(f"**Notes:** {finding['notes']}")
                
                if control:
                    st.markdown("---")
                    st.markdown(f"**Description:** {control.description}")
                    st.markdown(f"**Expected Result:** {control.expected_result}")
                    
                    st.markdown("**Check Procedure:**")
                    st.code(control.check_procedure.strip(), language=None)
                    
                    mapping_parts = []
                    if control.nist_mapping:
                        mapping_parts.append(f"**NIST 800-53:** {', '.join(control.nist_mapping)}")
                    if control.cis_mapping:
                        mapping_parts.append(f"**CIS Controls:** {control.cis_mapping}")
                    if mapping_parts:
                        st.markdown(" | ".join(mapping_parts))
                    
                    st.markdown("---")
                    st.markdown("#### Remediation Steps")
                    
                    if control.remediation_steps:
                        for step in control.remediation_steps:
                            downtime_badge = " **Requires Downtime**" if step.requires_downtime else ""
                            time_badge = f" `{step.estimated_time}`" if step.estimated_time else ""
                            
                            if step.requires_downtime:
                                downtime_required.append(finding.get('control_id', 'N/A'))
                            
                            st.markdown(
                                '<div style="background:linear-gradient(135deg,rgba(13,17,23,0.6),rgba(22,36,64,0.4));border-left:3px solid #00d9ff;padding:0.5rem 0.8rem 0.5rem 0.6rem;margin:0.35rem 0;border-radius:0 8px 8px 0;display:flex;align-items:flex-start;gap:0.5rem;">'
                                '<span style="display:inline-flex;align-items:center;justify-content:center;min-width:22px;height:22px;border-radius:50%;font-size:0.65rem;font-weight:800;color:#0d1117;background:#00d9ff;box-shadow:0 0 8px rgba(0,217,255,0.35);">' + str(step.step_number) + '</span>'
                                '<span style="flex:1;"><span style="color:#e0e0e0;font-size:0.88rem;">' + step.description + '</span>'
                                '<span style="color:#ffc107;font-size:0.78rem;">' + time_badge + '</span>'
                                '<span style="color:#e94560;font-size:0.78rem;">' + downtime_badge + '</span></span>'
                                '</div>',
                                unsafe_allow_html=True
                            )
                            
                            if step.command:
                                st.code(step.command, language=step.script_type or "powershell")
                        
                        ps_script = get_remediation_script(finding.get('control_id', ''), "powershell")
                        if ps_script and len(ps_script) > 100:
                            st.download_button(
                                label=f"Download Remediation Script — {finding.get('control_id', '')}",
                                data=ps_script,
                                file_name=f"remediate_{finding.get('control_id', 'unknown')}.ps1",
                                mime="text/plain",
                                key=f"dlg_remed_{finding.get('control_id', '')}",
                                use_container_width=True
                            )

                        # Validation script (AI feature)
                        val_script = get_validation_script(finding.get('control_id', ''))
                        if val_script:
                            st.download_button(
                                label=f"✅ Download Validation Script — {finding.get('control_id', '')}",
                                data=val_script,
                                file_name=f"validate_{finding.get('control_id', 'unknown')}.ps1",
                                mime="text/plain",
                                key=f"dlg_val_{finding.get('control_id', '')}",
                                use_container_width=True
                            )
                    else:
                        st.info("Remediation steps not yet defined. Consult your security team.")
                else:
                    st.info("Detailed control information not available in the controls library.")
    
    # ── Visual Summary Dashboard ──
    st.markdown('<div style="height: 1px; background: linear-gradient(90deg, transparent, rgba(0,217,255,0.2), transparent); margin: 1.2rem 0;"></div>', unsafe_allow_html=True)
    unique_downtime = list(set(downtime_required))

    # Summary header
    st.markdown(
        '<div style="text-align:center;margin-bottom:0.8rem;">'
        '<div style="font-size:0.6rem;letter-spacing:3px;color:#4a6a8a;text-transform:uppercase;">&#9670; Remediation Summary &#9670;</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Summary metric cards
    summary_rows = [
        ("Total Findings",  str(len(failed_findings)), "#e94560", len(failed_findings), max(total_findings, 1)),
        ("Critical",        str(sev_counts.get('Critical', 0)),  "#e94560", sev_counts.get('Critical', 0), len(failed_findings)),
        ("High",            str(sev_counts.get('High', 0)),      "#ff6b6b", sev_counts.get('High', 0), len(failed_findings)),
        ("Medium",          str(sev_counts.get('Medium', 0)),    "#ffc107", sev_counts.get('Medium', 0), len(failed_findings)),
        ("Low",             str(sev_counts.get('Low', 0)),       "#00d9ff", sev_counts.get('Low', 0), len(failed_findings)),
        ("Require Downtime", str(len(unique_downtime)),          "#a855f7", len(unique_downtime), max(len(failed_findings), 1)),
    ]

    summary_html = '<div style="display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 1rem;">'
    for label, val, color, num, denom in summary_rows:
        bar_pct = min(100, (num / max(denom, 1)) * 100)
        summary_html += f"""
        <div style="background: rgba(13,17,23,0.55); backdrop-filter: blur(10px); border: 1px solid {color}18;
                    border-radius: 8px; padding: 0.45rem 0.8rem; display: flex; align-items: center; gap: 0.6rem;">
            <div style="flex: 1; font-size: 0.78rem; color: #8899bb;">{label}</div>
            <div style="width: 120px; height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden;">
                <div style="width: {bar_pct}%; height: 100%; background: {color}; border-radius: 3px;
                            box-shadow: 0 0 8px {color}44;"></div>
            </div>
            <div style="min-width: 28px; text-align: right; font-size: 0.9rem; font-weight: 700; color: {color};
                        text-shadow: 0 0 10px {color}33;">{val}</div>
        </div>"""
    summary_html += '</div>'
    st.markdown(summary_html, unsafe_allow_html=True)

    # Compliance gauge at bottom
    gauge_color = "#00ff88" if compliance_pct >= 80 else "#ffc107" if compliance_pct >= 50 else "#e94560"
    _p = str(total_findings - len(failed_findings))
    _f = str(len(failed_findings))
    st.markdown(
        '<div style="background:rgba(13,17,23,0.6);backdrop-filter:blur(10px);border:1px solid ' + gauge_color + '25;border-radius:14px;padding:1rem;text-align:center;margin-bottom:0.8rem;">'
        '<div style="font-size:0.58rem;letter-spacing:2.5px;color:#4a6a8a;text-transform:uppercase;margin-bottom:0.4rem;">Overall Compliance Score</div>'
        '<div style="font-size:2.4rem;font-weight:800;color:' + gauge_color + ';text-shadow:0 0 30px ' + gauge_color + '44;line-height:1;">' + str(compliance_pct) + '%</div>'
        '<div style="max-width:280px;margin:0.6rem auto 0;height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden;">'
        '<div style="width:' + str(compliance_pct) + '%;height:100%;border-radius:3px;background:linear-gradient(90deg,#e94560,#ffc107,#00ff88);box-shadow:0 0 12px ' + gauge_color + '44;"></div></div>'
        '<div style="font-size:0.6rem;color:#4a6a8a;margin-top:0.35rem;">' + _p + ' passed &bull; ' + _f + ' failed &bull; ' + str(total_findings) + ' total controls</div>'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Download Full Report
    report_lines = ["SOPRA AI-POWERED VULNERABILITY REMEDIATION REPORT", "=" * 60, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f"Total Failed Controls: {len(failed_findings)}", ""]
    for sev in severity_order:
        sev_findings = [f for f in failed_findings if f.get("severity") == sev]
        if sev_findings:
            report_lines.append(f"\n{'=' * 60}")
            report_lines.append(f"{sev.upper()} SEVERITY — {len(sev_findings)} Findings")
            report_lines.append(f"{'=' * 60}\n")
            for ff in sev_findings:
                ctrl = get_control_by_id(ff.get("control_id", ""))
                report_lines.append(f"[{ff.get('control_id', 'N/A')}] {ff.get('control_name', 'Unknown')}")
                report_lines.append(f"  Category: {ff.get('category', 'N/A')}")
                report_lines.append(f"  Family: {ff.get('family', 'N/A')}")
                if ff.get('evidence'):
                    report_lines.append(f"  Evidence: {ff['evidence']}")
                if ctrl:
                    report_lines.append(f"  Description: {ctrl.description}")
                    report_lines.append(f"  Expected: {ctrl.expected_result}")
                    if ctrl.nist_mapping:
                        report_lines.append(f"  NIST: {', '.join(ctrl.nist_mapping)}")
                    if ctrl.cis_mapping:
                        report_lines.append(f"  CIS: {ctrl.cis_mapping}")
                    if ctrl.remediation_steps:
                        report_lines.append(f"  Remediation:")
                        for step in ctrl.remediation_steps:
                            report_lines.append(f"    Step {step.step_number}: {step.description}")
                            if step.command:
                                report_lines.append(f"      Command: {step.command}")
                            if step.estimated_time:
                                report_lines.append(f"      Estimated Time: {step.estimated_time}")
                            if step.requires_downtime:
                                report_lines.append(f"      REQUIRES DOWNTIME")
                report_lines.append("")
    
    report_text = "\n".join(report_lines)
    st.download_button(
        label="Download Complete Remediation Report",
        data=report_text,
        file_name=f"SOPRA_Remediation_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        key="dlg_full_remediation_report",
        type="primary",
        use_container_width=True
    )


def render_remediation_page():
    """Standalone remediation page for the pop-out window — reads data from shared JSON file."""
    # Hide sidebar and inject premium dark-ops styling
    st.markdown("""
    <style>
        /* ── Layout ── */
        section[data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        header[data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stAppViewContainer"], .stApp {
            background: linear-gradient(160deg, #0d1117 0%, #151d2b 40%, #1a1a2e 100%) !important;
        }

        /* ── Typography ── */
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] span,
        [data-testid="stAppViewContainer"] li,
        [data-testid="stAppViewContainer"] td,
        [data-testid="stAppViewContainer"] th,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] h4 {
            color: #c8d6e5 !important;
        }

        /* ── Glassmorphism Expanders ── */
        [data-testid="stExpander"],
        [data-testid="stExpander"] > div {
            background: rgba(18, 28, 48, 0.65) !important;
            backdrop-filter: blur(14px) !important;
            -webkit-backdrop-filter: blur(14px) !important;
            border: 1px solid rgba(0, 217, 255, 0.12) !important;
            border-radius: 10px !important;
        }
        [data-testid="stExpanderToggleIcon"] { color: #00d9ff !important; }
        [data-testid="stExpander"] summary span { color: #c8d6e5 !important; }

        /* ── Animations ── */
        @keyframes scan-sweep {
            0%   { transform: translateX(-100%); opacity: 0; }
            10%  { opacity: 1; }
            90%  { opacity: 1; }
            100% { transform: translateX(250%); opacity: 0; }
        }
        @keyframes pulse-critical {
            0%, 100% { box-shadow: 0 0 12px rgba(233,69,96,0.25); }
            50%      { box-shadow: 0 0 28px rgba(233,69,96,0.55), 0 0 56px rgba(233,69,96,0.15); }
        }
        @keyframes fade-up {
            from { opacity: 0; transform: translateY(16px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes shimmer {
            0%   { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        @keyframes border-breathe {
            0%, 100% { border-color: rgba(0,217,255,0.15); }
            50%      { border-color: rgba(0,217,255,0.45); }
        }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: rgba(13,17,23,0.4); }
        ::-webkit-scrollbar-thumb { background: rgba(0,217,255,0.25); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(0,217,255,0.45); }
    </style>
    """, unsafe_allow_html=True)

    # ── Animated Header ──
    _gen_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(
        '<div style="position:relative;text-align:center;padding:1.3rem 1.5rem 1.1rem;margin-bottom:1.2rem;background:linear-gradient(145deg,rgba(0,217,255,0.05),rgba(168,85,247,0.04),rgba(0,255,136,0.02));border:1px solid rgba(0,217,255,0.2);border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.04);overflow:hidden;">'
        '<div style="position:absolute;top:0;left:0;width:40%;height:100%;background:linear-gradient(90deg,transparent,rgba(0,217,255,0.06),transparent);animation:scan-sweep 4s ease-in-out infinite;"></div>'
        '<div style="font-size:0.6rem;letter-spacing:5px;color:rgba(0,217,255,0.7);text-transform:uppercase;margin-bottom:0.5rem;">&#9670; SOPRA SECURITY INTELLIGENCE &#9670;</div>'
        '<h2 style="color:#ffffff;margin:0 0 0.35rem 0;font-size:1.3rem;font-weight:700;text-shadow:0 0 30px rgba(0,217,255,0.35);">AI-Powered Vulnerability Remediation</h2>'
        '<p style="color:#4a6a8a;margin:0;font-size:0.72rem;letter-spacing:1.5px;">Automated threat analysis &bull; Prioritized remediation &bull; Enterprise-grade intelligence</p>'
        '<div style="margin-top:0.7rem;font-size:0.6rem;color:rgba(0,217,255,0.5);">Generated ' + _gen_ts + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # Load data from shared file (not session state — this is a separate browser tab)
    results = load_results_from_file()
    show_remediation_content(results)


