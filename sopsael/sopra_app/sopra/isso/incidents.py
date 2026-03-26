"""SOPRA ISSO — Incident Correlation (AI-Enhanced)"""
import streamlit as st
from datetime import datetime

from sopra.persistence import _load_json, _save_json, _next_id, load_results_from_file
from sopra.isso.ai_engine import ai_correlate_incident, ai_summarize_incident

def render_incident_correlation():
    """Link findings to actual security incidents with AI-powered NLP correlation."""
    st.markdown("## 🔗 Incident Correlation")
    st.markdown("Link assessment findings to security incidents to demonstrate real-world impact of control failures.")

    incidents = _load_json("incidents.json", [])
    results = st.session_state.get("opra_assessment_results")
    if not results or not results.get("findings"):
        results = load_results_from_file()
        if results:
            st.session_state.opra_assessment_results = results
    failed = []
    if results and results.get("findings"):
        failed = [f for f in results["findings"] if f["status"] == "Failed"]

    # New incident form
    with st.expander("➕ Log New Incident", expanded=not bool(incidents)):
        inc_title = st.text_input("Incident Title", placeholder="e.g., Unauthorized access to file server", key="inc_title")
        inc_date = st.text_input("Incident Date", value=datetime.now().strftime("%Y-%m-%d"), key="inc_date")
        inc_severity = st.selectbox("Incident Severity", ["Critical", "High", "Medium", "Low"], key="inc_sev")
        inc_desc = st.text_area("Description", placeholder="Describe the incident, impact, and timeline...", key="inc_desc")
        inc_status = st.selectbox("Status", ["Open", "Investigating", "Contained", "Resolved", "Closed"], key="inc_status")

        # Link to controls (manual)
        ctrl_options = [f"{f['control_id']} — {f['control_name']}" for f in failed] if failed else []
        linked = st.multiselect("Link to Failed Controls (manual)", ctrl_options, key="inc_linked")

        # ── AI NLP Correlation ───────────────────────────────────────
        ai_suggestions = []
        if inc_title and inc_desc and failed:
            if st.button("🤖 AI Suggest Related Controls", key="inc_ai_correlate"):
                with st.spinner("AI is analyzing incident description and correlating to failed controls..."):
                    ai_results = ai_correlate_incident(inc_title, inc_desc, failed)

                if ai_results:
                    st.session_state["_inc_ai_suggestions"] = ai_results
                    st.rerun()

        # Show AI suggestions if available
        stored_suggestions = st.session_state.get("_inc_ai_suggestions", [])
        if stored_suggestions:
            st.markdown("#### 🤖 AI-Suggested Control Correlations")
            for sug in stored_suggestions:
                rel_color = {"high": "#e94560", "medium": "#ffc107", "low": "#00d9ff"}.get(sug.get("relevance", "low"), "#888")
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0.5rem;margin:0.1rem 0;'
                    'background:rgba(168,85,247,0.05);border:1px solid rgba(168,85,247,0.15);border-radius:6px;">'
                    '<code style="color:#00d9ff;">' + sug.get("control_id", "") + '</code>'
                    '<span style="color:' + rel_color + ';font-size:0.75rem;font-weight:700;">' + sug.get("relevance", "").upper() + '</span>'
                    '<span style="color:#c8d6e5;font-size:0.8rem;flex:1;">' + sug.get("explanation", "") + '</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
            # Build auto-link list from high/medium suggestions
            ai_ctrl_ids = [s["control_id"] for s in stored_suggestions if s.get("relevance") in ("high", "medium")]
            ai_linked_opts = [opt for opt in ctrl_options if any(cid in opt for cid in ai_ctrl_ids)]
            if ai_linked_opts:
                st.info(f"AI recommends linking **{len(ai_linked_opts)}** controls. Accept below or adjust manually above.")
                if st.button("✅ Accept AI Suggestions", key="inc_accept_ai"):
                    # Merge AI suggestions with manual selections
                    all_linked = list(set(linked + ai_linked_opts))
                    st.session_state["_inc_merged_links"] = all_linked
                    st.rerun()

        # Use merged links if available
        final_linked = st.session_state.pop("_inc_merged_links", linked)

        if st.button("🔗 Log Incident", type="primary", key="inc_submit"):
            if inc_title and inc_desc:
                incidents.append({
                    "id": _next_id(incidents, "INC"),
                    "title": inc_title,
                    "date": inc_date,
                    "severity": inc_severity,
                    "description": inc_desc,
                    "status": inc_status,
                    "linked_controls": [l.split(" — ")[0] for l in final_linked],
                    "linked_display": final_linked,
                    "ai_correlated": bool(stored_suggestions),
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                _save_json("incidents.json", incidents)
                # Clear AI suggestions
                st.session_state.pop("_inc_ai_suggestions", None)
                st.success("Incident logged and correlated.")
                st.rerun()
            else:
                st.warning("Title and Description are required.")

    if not incidents:
        st.info("No incidents logged yet.")
        return

    # Summary KPIs
    open_inc = len([i for i in incidents if i["status"] not in ("Resolved", "Closed")])
    total_linked = sum(len(i.get("linked_controls", [])) for i in incidents)
    ai_inc = len([i for i in incidents if i.get("ai_correlated")])
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Total Incidents", len(incidents))
    with k2:
        st.metric("Open / Active", open_inc)
    with k3:
        st.metric("Controls Linked", total_linked)

    if ai_inc:
        st.caption(f"🤖 {ai_inc} incident(s) correlated with AI assistance")

    st.markdown("---")

    for inc in reversed(incidents):
        sev_color = {"Critical": "#e94560", "High": "#ff6b6b", "Medium": "#ffc107", "Low": "#00d9ff"}.get(inc["severity"], "#888")
        status_icon = {"Open": "🔴", "Investigating": "🟠", "Contained": "🟡", "Resolved": "🟢", "Closed": "✅"}.get(inc["status"], "⚪")
        ai_tag = " 🤖" if inc.get("ai_correlated") else ""

        with st.expander(f"{inc['id']} — {inc['title']} | {status_icon} {inc['status']}{ai_tag}"):
            st.markdown(
                '<div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;">'
                '<span style="color: ' + sev_color + '; font-weight: 700;">Severity: ' + inc['severity'] + '</span>'
                '<span style="color: #6b839e;">Date: ' + inc['date'] + '</span>'
                '<span style="color: #6b839e;">Status: ' + inc['status'] + '</span>'
                '</div>',
                unsafe_allow_html=True
            )

            st.markdown(f"**Description:** {inc['description']}")

            # AI Executive Summary (Phase 1)
            if st.button("🤖 Generate AI Executive Summary", key=f"inc_summary_{inc['id']}"):
                with st.spinner("Generating incident summary..."):
                    summary = ai_summarize_incident(
                        inc["title"],
                        inc["description"],
                        inc.get("linked_display", inc.get("linked_controls", [])),
                    )
                    st.session_state[f"_inc_summary_{inc['id']}"] = summary
                    st.rerun()
            if st.session_state.get(f"_inc_summary_{inc['id']}"):
                st.markdown("**🤖 AI Executive Summary:**")
                st.markdown(st.session_state[f"_inc_summary_{inc['id']}"])

            if inc.get("linked_controls"):
                st.markdown("**Linked Controls:**")
                for lc in inc.get("linked_display", inc["linked_controls"]):
                    st.markdown(f"- 🔗 {lc}")
            else:
                st.markdown("*No controls linked to this incident.*")

            # Update status
            new_status = st.selectbox("Update Status", ["Open", "Investigating", "Contained", "Resolved", "Closed"],
                                      index=["Open", "Investigating", "Contained", "Resolved", "Closed"].index(inc["status"]),
                                      key=f"inc_st_{inc['id']}")
            if new_status != inc["status"]:
                if st.button("💾 Update", key=f"inc_save_{inc['id']}"):
                    inc["status"] = new_status
                    _save_json("incidents.json", incidents)
                    st.success(f"Incident {inc['id']} updated to {new_status}")
                    st.rerun()
