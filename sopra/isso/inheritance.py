"""SOPRA ISSO — Control Inheritance Model (AI-Enhanced)"""
import streamlit as st

from sopra.persistence import _load_json, _save_json, load_results_from_file
from sopra.isso.ai_engine import ai_classify_inheritance

def render_control_inheritance():
    """Mark controls as inherited, common, or system-specific with AI auto-classification."""
    st.markdown("## 🏛️ Control Inheritance Model")
    st.markdown("Classify controls as **Inherited** (from provider), **Common** (organization-wide), or **System-Specific** to document responsibility boundaries.")

    inheritance = _load_json("control_inheritance.json", {})
    results = st.session_state.get("opra_assessment_results")
    if not results or not results.get("findings"):
        results = load_results_from_file()
        if results:
            st.session_state.opra_assessment_results = results
    findings = results.get("findings", []) if results else []

    if not findings:
        st.warning("Run an assessment first to populate the control inventory.")
        return

    # Auto-init any controls not yet classified
    changed = False
    for f in findings:
        cid = f.get("control_id", "")
        if cid and cid not in inheritance:
            inheritance[cid] = {
                "type": "System-Specific",
                "provider": "",
                "notes": "",
                "control_name": f.get("control_name", ""),
                "family": f.get("family", f.get("category", ""))
            }
            changed = True
    if changed:
        _save_json("control_inheritance.json", inheritance)

    # Summary
    types = {}
    for cid, data in inheritance.items():
        t = data.get("type", "System-Specific")
        types[t] = types.get(t, 0) + 1
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Inherited", types.get("Inherited", 0))
    with k2:
        st.metric("Common", types.get("Common", 0))
    with k3:
        st.metric("System-Specific", types.get("System-Specific", 0))

    st.markdown("---")

    # ── AI Auto-Classification ───────────────────────────────────────
    st.markdown("### 🤖 AI Auto-Classification")
    st.caption("Let AI analyze each control and recommend Inherited / Common / System-Specific classification with provider suggestions.")

    ai_c1, ai_c2 = st.columns([3, 1])
    with ai_c1:
        st.markdown(f"**{len(inheritance)}** controls ready for AI classification")
    with ai_c2:
        ai_classify = st.button("🤖 AI Classify All", type="primary", key="ci_ai_classify")

    if ai_classify:
        ctrl_list = [
            {"control_id": cid, "control_name": d.get("control_name", ""), "family": d.get("family", ""), "category": d.get("family", "")}
            for cid, d in inheritance.items()
        ]
        with st.spinner("AI is analyzing controls and recommending classifications..."):
            classifications = ai_classify_inheritance(ctrl_list)

        if classifications:
            update_count = 0
            for c in classifications:
                cid = c.get("id", "")
                if cid in inheritance:
                    new_type = c.get("type", "System-Specific")
                    if new_type in ("Inherited", "Common", "Hybrid", "System-Specific"):
                        # Map Hybrid to a valid type
                        if new_type == "Hybrid":
                            new_type = "Inherited"  # Treat hybrid as inherited with notes
                        inheritance[cid]["type"] = new_type
                        inheritance[cid]["provider"] = c.get("provider", inheritance[cid].get("provider", ""))
                        if c.get("rationale"):
                            inheritance[cid]["notes"] = c["rationale"]
                        update_count += 1
            _save_json("control_inheritance.json", inheritance)
            st.success(f"AI classified **{update_count}** controls. Review and adjust below.")
            st.rerun()
        else:
            st.warning("AI classification returned no results. Using rule-based fallback.")

    st.markdown("---")

    # Bulk assignment
    st.markdown("### Bulk Classification")
    bulk_type = st.selectbox("Set selected controls to:", ["Inherited", "Common", "System-Specific"], key="ci_bulk_type")
    bulk_provider = st.text_input("Provider / Source (for Inherited)", key="ci_bulk_prov")

    # Group by family for organized display
    by_family = {}
    for cid, data in inheritance.items():
        fam = data.get("family", "Other")
        by_family.setdefault(fam, []).append((cid, data))

    for fam, ctrls in sorted(by_family.items()):
        with st.expander(f"📂 {fam} ({len(ctrls)} controls)"):
            for cid, data in sorted(ctrls, key=lambda x: x[0]):
                type_icon = {"Inherited": "🏢", "Common": "🌐", "System-Specific": "🖥️"}.get(data["type"], "📌")
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    label = f"{type_icon} **{cid}** — {data.get('control_name', '')[:45]}"
                    if data.get("notes"):
                        label += f" _({data['notes'][:30]}...)_"
                    st.markdown(label)
                with c2:
                    new_type = st.selectbox("Type", ["Inherited", "Common", "System-Specific"],
                                           index=["Inherited", "Common", "System-Specific"].index(data["type"]),
                                           key=f"ci_type_{cid}", label_visibility="collapsed")
                with c3:
                    new_prov = st.text_input("Provider", value=data.get("provider", ""), key=f"ci_prov_{cid}", label_visibility="collapsed", placeholder="Provider")
                if new_type != data["type"] or new_prov != data.get("provider", ""):
                    inheritance[cid]["type"] = new_type
                    inheritance[cid]["provider"] = new_prov
                    _save_json("control_inheritance.json", inheritance)
