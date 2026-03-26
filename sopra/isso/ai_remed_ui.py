"""SOPRA AI Remediation Dashboard — ISSO Toolkit UI"""
import streamlit as st
import json
from datetime import datetime

from sopra.persistence import load_results_from_file
from sopra.isso.ai_remediation import (
    generate_ai_remediation_plan,
    detect_attack_chains,
    get_validation_script,
    get_impact_analysis,
    load_remediation_tracking,
    record_remediation_attempt,
    get_remediation_success_rate,
    generate_ticket,
    generate_bulk_tickets,
)


def render_ai_remediation_dashboard():
    """Full AI Remediation Dashboard with all 6 AI features."""
    st.markdown(
        '<div style="text-align:center;padding:0.8rem;margin-bottom:1rem;background:linear-gradient(145deg,rgba(0,217,255,0.05),rgba(168,85,247,0.04));border:1px solid rgba(0,217,255,0.2);border-radius:12px;">'
        '<div style="font-size:0.5rem;letter-spacing:4px;color:rgba(0,217,255,0.6);">&#9670; AI-powered Remediation &#9670;</div>'
        '<h2 style="color:#fff;margin:0.2rem 0;font-size:1.3rem;font-weight:700;">Automated Vulnerability Management</h2>'
        '<p style="color:#4a6a8a;margin:0;font-size:0.72rem;">Attack Chain Analysis &bull; AI Plans &bull; Impact Analysis &bull; Validation &bull; Tickets &bull; Learning</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # Load assessment data
    results = st.session_state.get('opra_assessment_results')
    if not results:
        results = load_results_from_file()
        if results:
            st.session_state.opra_assessment_results = results

    if not results or not results.get("findings"):
        st.warning("No assessment data available. Run an assessment first.")
        return

    findings = results["findings"]
    failed = [f for f in findings if f.get("status") == "Failed"]

    if not failed:
        st.success("No failed controls found. Your security posture is strong!")
        return

    # Sub-navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔗 Attack Chains",
        "🤖 AI Remediation Plans",
        "✅ Validation Scripts",
        "⚠️ Impact Analysis",
        "📈 Remediation Tracking",
        "🎫 Ticket Generator",
    ])

    # ── TAB 1: Attack Chain Detection ──
    with tab1:
        _render_attack_chains(findings, failed)

    # ── TAB 2: AI Remediation Plans ──
    with tab2:
        _render_ai_plans(failed)

    # ── TAB 3: Validation Scripts ──
    with tab3:
        _render_validation_scripts(failed)

    # ── TAB 4: Impact Analysis ──
    with tab4:
        _render_impact_analysis(failed)

    # ── TAB 5: Remediation Tracking / Continuous Learning ──
    with tab5:
        _render_tracking(failed)

    # ── TAB 6: Ticket Generator ──
    with tab6:
        _render_ticket_generator(findings, failed)


def _render_attack_chains(findings, failed):
    """Render attack chain detection results."""
    st.markdown("#### 🔗 Automated Risk Prioritization — Attack Chain Detection")
    st.caption("SOPRA analyzes combinations of failed controls to identify exploitable attack paths.")

    chains = detect_attack_chains(findings)

    if not chains:
        st.success("No active attack chains detected based on current findings.")
        return

    st.error(f"**{len(chains)} attack chain(s) detected** from your failed controls.")

    for i, chain in enumerate(chains):
        color = chain["color"]
        pct = chain["match_pct"]
        bar_color = "#e94560" if pct >= 70 else "#ffc107" if pct >= 40 else "#00d9ff"

        with st.expander(f"{'🔴' if pct >= 70 else '🟡' if pct >= 40 else '🔵'} {chain['name']} — {pct}% exposed ({len(chain['matched_controls'])}/{chain['total_controls']} controls failed)", expanded=(i == 0)):
            st.markdown(f"**Description:** {chain['description']}")
            st.markdown(f"**Impact:** {chain['impact']}")

            # Progress bar
            st.markdown(
                '<div style="background:rgba(255,255,255,0.06);border-radius:4px;height:8px;margin:0.5rem 0;overflow:hidden;">'
                '<div style="width:' + str(pct) + '%;height:100%;background:' + bar_color + ';border-radius:4px;"></div></div>',
                unsafe_allow_html=True
            )

            st.markdown(f"**Failed Controls in this Chain:**")
            for cid in chain["matched_controls"]:
                ctrl = next((f for f in findings if f.get("control_id") == cid), None)
                if ctrl:
                    st.markdown(f"- `{cid}` — {ctrl.get('control_name', 'Unknown')} ({ctrl.get('severity', '?')})")

            st.markdown(f"**🎯 Chain-Breaking Fix:** {chain['break_point']}")


def _render_ai_plans(failed):
    """Render AI-generated remediation plans."""
    st.markdown("#### 🤖 AI-Generated Remediation Plans")
    st.caption("Select a failed control to generate a custom AI-powered remediation playbook.")

    options = [f"{f['control_id']} — {f['control_name']} ({f.get('severity', '?')})" for f in failed]
    selected = st.selectbox("Select a finding:", options, key="ai_plan_select")

    if selected:
        idx = options.index(selected)
        finding = failed[idx]

        if st.button("🧠 Generate AI Remediation Plan", use_container_width=True, key="gen_ai_plan"):
            with st.spinner("Generating AI remediation plan..."):
                plan = generate_ai_remediation_plan(finding)
            st.markdown(plan)
            st.download_button(
                "📥 Download Plan",
                data=plan,
                file_name=f"ai_plan_{finding['control_id']}.md",
                mime="text/markdown",
                key="dl_ai_plan"
            )


def _render_validation_scripts(failed):
    """Render post-remediation validation scripts."""
    st.markdown("#### ✅ Remediation Validation Scripts")
    st.caption("Download PowerShell scripts that verify your remediation was successful.")

    for f in failed:
        cid = f.get("control_id", "")
        script = get_validation_script(cid)
        if script:
            with st.expander(f"🔍 {cid} — {f.get('control_name', 'Unknown')}"):
                st.code(script, language="powershell")
                st.download_button(
                    f"📥 Download {cid} Validation Script",
                    data=script,
                    file_name=f"validate_{cid}.ps1",
                    mime="text/plain",
                    key=f"dl_val_{cid}"
                )


def _render_impact_analysis(failed):
    """Render change impact analysis for each failed control."""
    st.markdown("#### ⚠️ Change Impact Analysis")
    st.caption("Understand downstream effects before applying remediation.")

    for f in failed:
        cid = f.get("control_id", "")
        impact = get_impact_analysis(cid)
        if impact:
            sev = f.get("severity", "Unknown")
            sev_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🔵"}.get(sev, "⚪")

            with st.expander(f"{sev_icon} {cid} — {f.get('control_name', 'Unknown')}"):
                st.markdown(f"**Potential Impact:** {impact['impact']}")
                st.markdown(f"**Affected Systems:** {impact['affected']}")
                st.markdown(f"**Downtime Required:** {impact['downtime']}")
                st.markdown(f"**Rollback Plan:** {impact['rollback']}")


def _render_tracking(failed):
    """Render continuous learning / remediation tracking."""
    st.markdown("#### 📈 Remediation Tracking — Continuous Learning")
    st.caption("Track remediation attempts and success rates to improve over time.")

    stats = get_remediation_success_rate()

    # Overall metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Attempts", stats["total_attempts"])
    c2.metric("Overall Success Rate", f"{stats['overall_rate']}%")
    c3.metric("Controls Tracked", len(stats["per_control"]))

    # Record new attempt
    st.markdown("---")
    st.markdown("**Log a Remediation Attempt:**")
    col1, col2, col3 = st.columns([2, 1, 2])

    options = [f"{f['control_id']} — {f['control_name']}" for f in failed]
    with col1:
        selected = st.selectbox("Control:", options, key="track_select")
    with col2:
        status = st.selectbox("Result:", ["success", "failed", "in_progress"], key="track_status")
    with col3:
        notes = st.text_input("Notes:", key="track_notes", placeholder="e.g., Applied GPO fix")

    if st.button("📝 Record Attempt", use_container_width=True, key="record_attempt"):
        if selected:
            cid = selected.split(" — ")[0]
            record_remediation_attempt(cid, status, notes)
            st.success(f"Recorded {status} for {cid}")
            st.rerun()

    # Per-control stats
    if stats["per_control"]:
        st.markdown("---")
        st.markdown("**Per-Control Success Rates:**")
        for cid, s in sorted(stats["per_control"].items()):
            rate = s["success_rate"]
            color = "#00ff88" if rate >= 80 else "#ffc107" if rate >= 50 else "#e94560"
            st.markdown(
                '<div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0;">'
                '<code style="color:#00d9ff;">' + cid + '</code>'
                '<div style="flex:1;background:rgba(255,255,255,0.06);border-radius:3px;height:6px;overflow:hidden;">'
                '<div style="width:' + str(rate) + '%;height:100%;background:' + color + ';border-radius:3px;"></div></div>'
                '<span style="color:' + color + ';font-size:0.8rem;font-weight:600;min-width:50px;text-align:right;">' + str(rate) + '%</span>'
                '<span style="color:#4a6a8a;font-size:0.7rem;">(' + str(s["attempts"]) + ' attempts)</span>'
                '</div>',
                unsafe_allow_html=True
            )


def _render_ticket_generator(findings, failed):
    """Render automated ticket generation."""
    st.markdown("#### 🎫 Automated Ticket Generator")
    st.caption("Generate pre-filled remediation tickets for ServiceNow or Jira.")

    col1, col2 = st.columns(2)
    with col1:
        ticket_format = st.selectbox("Ticket System:", ["ServiceNow", "Jira"], key="ticket_format")
    with col2:
        mode = st.selectbox("Mode:", ["Single Finding", "Bulk — All Failed Controls"], key="ticket_mode")

    fmt = "servicenow" if ticket_format == "ServiceNow" else "jira"

    if mode == "Single Finding":
        options = [f"{f['control_id']} — {f['control_name']} ({f.get('severity', '?')})" for f in failed]
        selected = st.selectbox("Select finding:", options, key="ticket_finding")

        if st.button("🎫 Generate Ticket", use_container_width=True, key="gen_single_ticket"):
            idx = options.index(selected)
            ticket = generate_ticket(failed[idx], fmt)
            st.json(ticket)
            st.download_button(
                f"📥 Download {ticket_format} Ticket JSON",
                data=json.dumps(ticket, indent=2, default=str),
                file_name=f"ticket_{failed[idx]['control_id']}_{fmt}.json",
                mime="application/json",
                key="dl_single_ticket"
            )
    else:
        if st.button(f"🎫 Generate All {len(failed)} Tickets", use_container_width=True, key="gen_bulk_tickets"):
            with st.spinner(f"Generating {len(failed)} tickets..."):
                tickets = generate_bulk_tickets(findings, fmt)

            st.success(f"Generated {len(tickets)} {ticket_format} tickets.")

            # Show summary
            for t in tickets[:5]:
                key_field = "short_description" if fmt == "servicenow" else "summary"
                st.markdown(f"- **{t.get(key_field, 'N/A')}** — Priority: {t.get('priority', 'N/A')}")
            if len(tickets) > 5:
                st.caption(f"... and {len(tickets) - 5} more")

            # Download bulk
            bulk_json = json.dumps(tickets, indent=2, default=str)
            st.download_button(
                f"📥 Download All {len(tickets)} Tickets (JSON)",
                data=bulk_json,
                file_name=f"sopra_tickets_bulk_{fmt}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                key="dl_bulk_tickets"
            )

            # CSV option
            if fmt == "servicenow":
                csv_lines = ["short_description,priority,impact,urgency,category,assignment_group,due_date"]
                for t in tickets:
                    csv_lines.append(f"\"{t['short_description']}\",{t['priority']},{t['impact']},{t['urgency']},{t['category']},{t['assignment_group']},{t['due_date']}")
            else:
                csv_lines = ["summary,priority,issuetype,labels,duedate"]
                for t in tickets:
                    csv_lines.append(f"\"{t['summary']}\",{t['priority']},{t['issuetype']},\"{';'.join(t['labels'])}\",{t['duedate']}")

            st.download_button(
                f"📥 Download All {len(tickets)} Tickets (CSV)",
                data="\n".join(csv_lines),
                file_name=f"sopra_tickets_bulk_{fmt}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="dl_bulk_csv"
            )
