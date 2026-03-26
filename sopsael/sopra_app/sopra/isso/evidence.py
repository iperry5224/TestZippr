"""SOPRA ISSO — Audit-Ready Evidence Collection (AI-Enhanced)"""
import streamlit as st
from datetime import datetime
import os
import html

from sopra.persistence import _load_json, _save_json, _next_id, _DATA_DIR, load_results_from_file
from sopra.isso.ai_engine import ai_analyze_evidence

def render_evidence_collection():
    """Attach evidence (screenshots, configs, logs) to findings with AI sufficiency analysis."""
    st.markdown("## 📎 Audit-Ready Evidence Collection")
    st.markdown("Attach evidence artifacts to findings for auditor review.")

    evidence = _load_json("evidence.json", [])
    results = st.session_state.get("opra_assessment_results")
    if not results or not results.get("findings"):
        results = load_results_from_file()
        if results:
            st.session_state.opra_assessment_results = results
    findings = results.get("findings", []) if results else []

    # Upload form
    with st.expander("➕ Attach New Evidence", expanded=not bool(evidence)):
        ctrl_options = [f"{f['control_id']} — {f['control_name']}" for f in findings] if findings else ["No findings available — run assessment first"]
        ev_ctrl = st.selectbox("Link to Control / Finding", ctrl_options, key="ev_ctrl")
        ev_type = st.selectbox("Evidence Type", ["Screenshot", "Configuration Export", "Log File", "Policy Document", "Scan Report", "Other"], key="ev_type")
        ev_desc = st.text_area("Description", placeholder="Describe what this evidence demonstrates...", key="ev_desc")
        ev_file = st.file_uploader("Upload File", type=["png", "jpg", "jpeg", "pdf", "txt", "csv", "log", "xml", "json", "docx"], key="ev_file")

        if st.button("📎 Attach Evidence", type="primary", key="ev_submit"):
            if ev_desc and ev_file:
                ev_dir = os.path.join(_DATA_DIR, "evidence_files")
                os.makedirs(ev_dir, exist_ok=True)
                safe_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ev_file.name}"
                fpath = os.path.join(ev_dir, safe_name)
                with open(fpath, 'wb') as out_f:
                    out_f.write(ev_file.getbuffer())
                cid = ev_ctrl.split(" — ")[0] if " — " in ev_ctrl else ev_ctrl
                evidence.append({
                    "id": _next_id(evidence, "EV"),
                    "control_id": cid,
                    "finding": ev_ctrl,
                    "evidence_type": ev_type,
                    "description": ev_desc,
                    "filename": safe_name,
                    "original_name": ev_file.name,
                    "uploaded_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "uploaded_by": "ISSO"
                })
                _save_json("evidence.json", evidence)
                st.success(f"Evidence attached: {ev_file.name}")
                st.rerun()
            else:
                st.warning("Description and file upload are required.")

    if not evidence:
        st.info("No evidence artifacts attached yet.")
        return

    # ── AI Evidence Sufficiency Analysis ─────────────────────────────
    st.markdown("---")
    st.markdown("### 🤖 AI Evidence Sufficiency Analysis")
    st.caption("Analyze whether attached evidence meets audit requirements for each control.")

    # Group by control
    by_ctrl = {}
    for ev in evidence:
        k = ev.get("control_id", "Unknown")
        by_ctrl.setdefault(k, []).append(ev)

    # Calculate coverage stats
    assessed_cids = {f.get("control_id") for f in findings} if findings else set()
    covered_cids = set(by_ctrl.keys())
    gaps = assessed_cids - covered_cids
    coverage_pct = round(len(covered_cids) / max(len(assessed_cids), 1) * 100)

    # Batch "Verify All" and "Clear" buttons
    if "evidence_batch_results" not in st.session_state:
        st.session_state.evidence_batch_results = {}
    btn_col1, btn_col2 = st.columns([1, 4])
    with btn_col1:
        verify_all_clicked = st.button("🤖 **Verify All Evidence**", type="primary", key="ev_verify_all", use_container_width=True)
    with btn_col2:
        has_results = bool(st.session_state.evidence_batch_results)
        if has_results and st.button("Clear results", key="ev_clear_batch", help="Clear verification results to re-run"):
            st.session_state.evidence_batch_results = {}
            st.rerun()
    if verify_all_clicked:
        progress = st.progress(0, text="Analyzing artifacts...")
        results = {}
        for i, ev in enumerate(evidence):
            progress.progress((i + 1) / len(evidence), text=f"Analyzing {ev.get('original_name', ev['filename'])}...")
            ctrl = ev.get("control_id", "Unknown")
            ctrl_name = ""
            matched_f = next((f for f in findings if f.get("control_id") == ctrl), None)
            if matched_f:
                ctrl_name = matched_f.get("control_name", "")
            analysis = ai_analyze_evidence(ctrl, ctrl_name, ev["evidence_type"], ev["description"], ev.get("original_name", ""))
            results[ev["id"]] = analysis
        st.session_state.evidence_batch_results = results
        progress.empty()
        st.success(f"Verified {len(results)} artifact(s). Results shown below.")
        st.rerun()

    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.metric("Evidence Artifacts", len(evidence))
    with mc2:
        st.metric("Controls Covered", f"{len(covered_cids)} / {len(assessed_cids)}")
    with mc3:
        st.metric("Coverage Rate", f"{coverage_pct}%")

    if gaps:
        with st.expander(f"⚠️ {len(gaps)} controls missing evidence", expanded=False):
            for g in sorted(gaps):
                matched = next((f for f in findings if f.get("control_id") == g), {})
                st.markdown(f"- **{g}** — {matched.get('control_name', 'Unknown')}")

    st.markdown("---")

    # Analyze individual evidence
    for ctrl, evs in sorted(by_ctrl.items()):
        with st.expander(f"🔗 {ctrl} — {len(evs)} artifact(s)"):
            for ev in evs:
                type_icon = {"Screenshot": "🖼️", "Configuration Export": "⚙️", "Log File": "📄",
                             "Policy Document": "📑", "Scan Report": "🔍", "Other": "📦"}.get(ev["evidence_type"], "📦")
                st.markdown(
                    '<div style="background: rgba(0,217,255,0.04); border: 1px solid rgba(0,217,255,0.12);'
                    'border-radius: 8px; padding: 0.6rem; margin: 0.3rem 0;">'
                    '<div style="display: flex; justify-content: space-between; align-items: center;">'
                    '<span>' + type_icon + ' <strong>' + ev['evidence_type'] + '</strong> &mdash; ' + ev.get('original_name', ev['filename']) + '</span>'
                    '<span style="color: #6b839e; font-size: 0.75rem;">' + ev['uploaded_date'] + '</span>'
                    '</div>'
                    '<p style="color: #c8d6e5; margin: 0.3rem 0 0 0; font-size: 0.85rem;">' + ev['description'] + '</p>'
                    '</div>',
                    unsafe_allow_html=True
                )

                # Show batch result if available, else per-item analysis button
                batch_results = st.session_state.get("evidence_batch_results", {})
                if ev["id"] in batch_results:
                    analysis = batch_results[ev["id"]]
                    st.markdown(
                        '<div style="background:rgba(168,85,247,0.06);border:1px solid rgba(168,85,247,0.2);border-radius:8px;padding:0.8rem;margin:0.3rem 0;">'
                        '<div style="color:#a855f7;font-weight:700;font-size:0.85rem;margin-bottom:0.4rem;">🤖 AI Sufficiency Analysis</div>'
                        '<div style="color:#c8d6e5;font-size:0.82rem;">' + html.escape(analysis).replace('\n', '<br>') + '</div>'
                        '</div>',
                        unsafe_allow_html=True
                    )
                if st.button(f"🤖 Analyze Sufficiency", key=f"ev_ai_{ev['id']}"):
                    ctrl_name = ""
                    matched_f = next((f for f in findings if f.get("control_id") == ctrl), None)
                    if matched_f:
                        ctrl_name = matched_f.get("control_name", "")
                    with st.spinner("AI analyzing evidence sufficiency..."):
                        analysis = ai_analyze_evidence(ctrl, ctrl_name, ev["evidence_type"], ev["description"], ev.get("original_name", ""))
                    # Update batch results so this item shows the new analysis
                    if "evidence_batch_results" not in st.session_state:
                        st.session_state.evidence_batch_results = {}
                    st.session_state.evidence_batch_results[ev["id"]] = analysis
                    st.rerun()

                # Download button
                ev_fpath = os.path.join(_DATA_DIR, "evidence_files", ev["filename"])
                if os.path.exists(ev_fpath):
                    with open(ev_fpath, 'rb') as dl_f:
                        st.download_button(f"📥 {ev.get('original_name', ev['filename'])}", data=dl_f.read(),
                                           file_name=ev.get('original_name', ev['filename']),
                                           key=f"ev_dl_{ev['id']}")
