"""SOPRA ISSO — Signature & Approval Workflow (AI-Enhanced)"""
import streamlit as st
from datetime import datetime

from sopra.persistence import _load_json, _save_json, _next_id
from sopra.isso.ai_engine import ai_draft_approval_summary

def render_approval_workflow():
    """Simple approval trail with AI-drafted package summaries."""
    st.markdown("## ✍️ Signature & Approval Workflow")
    st.markdown("Record AO sign-off on risk acceptances, POA&M closures, and assessment completions.")

    approvals = _load_json("approvals.json", [])

    # New approval form
    with st.expander("➕ Record New Approval", expanded=not bool(approvals)):
        ap_type = st.selectbox("Approval Type", ["Assessment Completion", "POA&M Closure", "Risk Acceptance", "SSP Approval", "ATO Recommendation", "Other"], key="ap_type")
        ap_item = st.text_input("Item Reference", placeholder="e.g., POAM-0012, RA-0003, Assessment 2026-02-08", key="ap_item")

        # ── AI Draft Approval Summary ────────────────────────────────
        if ap_type and ap_item:
            if st.button("🤖 AI Draft Summary", key="ap_ai_draft"):
                # Gather related data context
                related = ""
                if "POAM" in ap_item.upper():
                    poam_items = _load_json("poam.json", [])
                    matched = [p for p in poam_items if p.get("id", "") == ap_item.strip()]
                    if matched:
                        related = f"POA&M: {matched[0].get('control_id','')} - {matched[0].get('finding','')}, Status: {matched[0].get('status','')}, Severity: {matched[0].get('severity','')}"
                elif "RA" in ap_item.upper():
                    ra_items = _load_json("risk_acceptances.json", [])
                    matched = [r for r in ra_items if r.get("id", "") == ap_item.strip()]
                    if matched:
                        related = f"Risk Acceptance: {matched[0].get('control_id','')} - {matched[0].get('finding','')}, Level: {matched[0].get('risk_level','')}"

                with st.spinner("AI is drafting approval package summary..."):
                    draft = ai_draft_approval_summary(ap_type, ap_item, related)
                if draft:
                    st.session_state["_ap_ai_draft"] = draft
                    st.rerun()

        # Pre-fill conditions from AI if available
        ai_draft = st.session_state.pop("_ap_ai_draft", "")

        ap_authority = st.text_input("Approving Authority", placeholder="Name, Title", key="ap_auth")
        ap_role = st.selectbox("Role", ["Authorizing Official (AO)", "ISSO", "ISSM", "System Owner", "Risk Executive", "Other"], key="ap_role")
        ap_decision = st.selectbox("Decision", ["Approved", "Approved with Conditions", "Denied", "Deferred"], key="ap_dec")

        default_cond = ai_draft if ai_draft else ""
        if ai_draft:
            st.success("🤖 AI draft loaded. Review and edit below.")
        ap_conditions = st.text_area("Conditions / Notes", value=default_cond, placeholder="Any conditions, caveats, or notes...", key="ap_cond")

        if st.button("✍️ Record Approval", type="primary", key="ap_submit"):
            if ap_item and ap_authority:
                approvals.append({
                    "id": _next_id(approvals, "APR"),
                    "type": ap_type,
                    "item_reference": ap_item,
                    "approved_by": ap_authority,
                    "role": ap_role,
                    "decision": ap_decision,
                    "conditions": ap_conditions,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "ai_drafted": bool(ai_draft),
                })
                _save_json("approvals.json", approvals)
                st.success("Approval recorded.")
                st.rerun()
            else:
                st.warning("Item Reference and Approving Authority are required.")

    if not approvals:
        st.info("No approvals recorded yet.")
        return

    st.markdown("---")
    ai_count = len([a for a in approvals if a.get("ai_drafted")])
    st.markdown(f"### Approval History ({len(approvals)} records)")
    if ai_count:
        st.caption(f"🤖 {ai_count} approval(s) drafted with AI assistance")

    for ap in reversed(approvals):
        dec_color = {"Approved": "#00ff88", "Approved with Conditions": "#ffc107", "Denied": "#e94560", "Deferred": "#6b839e"}.get(ap["decision"], "#888")
        ai_tag = " 🤖" if ap.get("ai_drafted") else ""
        st.markdown(
            '<div style="background: rgba(0,217,255,0.03); border: 1px solid rgba(0,217,255,0.1);'
            'border-radius: 10px; padding: 0.7rem; margin: 0.4rem 0;">'
            '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">'
            '<span style="font-weight: 700; color: #c8d6e5;">' + ap['id'] + ' &mdash; ' + ap['type'] + ai_tag + '</span>'
            '<span style="color: ' + dec_color + '; font-weight: 700; background: ' + dec_color + '18;'
            'padding: 2px 10px; border-radius: 12px; font-size: 0.8rem;">' + ap['decision'] + '</span>'
            '</div>'
            '<div style="color: #6b839e; font-size: 0.8rem; margin-top: 0.3rem;">'
            '<strong>Item:</strong> ' + ap['item_reference'] + ' &nbsp;|&nbsp;'
            '<strong>By:</strong> ' + ap['approved_by'] + ' (' + ap['role'] + ') &nbsp;|&nbsp;'
            '<strong>Date:</strong> ' + ap['date'] +
            '</div>' +
            ('<p style="color:#c8d6e5;font-size:0.8rem;margin:0.3rem 0 0 0;"><em>' + ap['conditions'] + '</em></p>' if ap.get('conditions') else '') +
            '</div>',
            unsafe_allow_html=True
        )
