"""SOPRA Control Crosswalk — Interactive ISSO Toolkit UI (AI-Enhanced)"""
import streamlit as st
from datetime import datetime

from sopra.persistence import load_results_from_file
from sopra.isso.crosswalk import (
    build_nist_reverse_index, build_nist_reverse_index_with_findings,
    build_cis_reverse_index, build_cis_reverse_index_with_findings,
    build_forward_crosswalk,
    get_nist_coverage_stats, get_cis_coverage_stats,
    export_forward_crosswalk_csv, export_nist_reverse_crosswalk_csv,
    export_cis_reverse_crosswalk_csv,
    NIST_FAMILIES, CIS_CONTROLS,
    _get_nist_family, _get_nist_family_name,
)
from sopra.isso.ai_engine import ai_crosswalk_query


def render_crosswalk_page():
    """Full crosswalk page with NIST and CIS bidirectional mappings."""
    st.markdown(
        '<div style="text-align:center;padding:0.8rem;margin-bottom:1rem;background:linear-gradient(145deg,rgba(0,217,255,0.05),rgba(168,85,247,0.04));border:1px solid rgba(0,217,255,0.2);border-radius:12px;">'
        '<div style="font-size:0.5rem;letter-spacing:4px;color:rgba(0,217,255,0.6);text-transform:uppercase;">&#9670; BIDIRECTIONAL MAPPING &#9670;</div>'
        '<h2 style="color:#fff;margin:0.2rem 0;font-size:1.3rem;font-weight:700;">Control Crosswalk</h2>'
        '<p style="color:#4a6a8a;margin:0;font-size:0.72rem;">SOPRA &harr; NIST 800-53 Rev 5 &bull; SOPRA &harr; CIS Controls v8</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # Load assessment data
    results = st.session_state.get("opra_assessment_results")
    if not results:
        results = load_results_from_file()
        if results:
            st.session_state.opra_assessment_results = results

    findings = results.get("findings", []) if results else []
    has_data = len(findings) > 0

    if has_data:
        st.success(f"Assessment data loaded: {len(findings)} controls assessed")
    else:
        st.info("No assessment data. Crosswalk shows static mappings. Run an assessment for live status.")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Coverage Dashboard",
        "🔄 NIST 800-53 Crosswalk",
        "🔄 CIS v8 Crosswalk",
        "🤖 AI Query",
        "📥 Export Crosswalks",
    ])

    with tab1:
        _render_coverage_dashboard(findings, has_data)
    with tab2:
        _render_nist_crosswalk(findings, has_data)
    with tab3:
        _render_cis_crosswalk(findings, has_data)
    with tab4:
        _render_ai_query(findings, has_data)
    with tab5:
        _render_export(findings)


def _render_coverage_dashboard(findings, has_data):
    """Coverage overview with family-level stats."""
    st.markdown("#### 📊 Framework Coverage Dashboard")

    # NIST stats
    st.markdown("##### NIST 800-53 Rev 5 Coverage")
    nist_stats = get_nist_coverage_stats(findings if has_data else None)

    # Summary metrics
    total_nist = sum(s["nist_control_count"] for s in nist_stats.values())
    total_sopra = sum(s["sopra_control_count"] for s in nist_stats.values())
    families_covered = len(nist_stats)

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("NIST Families Covered", f"{families_covered} / {len(NIST_FAMILIES)}")
    mc2.metric("Unique NIST Controls Mapped", total_nist)
    mc3.metric("SOPRA Controls with NIST Mapping", total_sopra)

    # Per-family table
    for family_id, stats in nist_stats.items():
        fname = stats["family_name"]
        nist_count = stats["nist_control_count"]
        sopra_count = stats["sopra_control_count"]

        if has_data:
            passed = stats["passed"]
            failed = stats["failed"]
            total = passed + failed + stats["not_assessed"]
            pct = round(passed / max(total, 1) * 100)
            bar_color = "#00ff88" if pct >= 80 else "#ffc107" if pct >= 50 else "#e94560"

            st.markdown(
                '<div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0.5rem;margin:0.15rem 0;'
                'background:rgba(13,17,23,0.5);border-radius:6px;border:1px solid rgba(255,255,255,0.04);">'
                '<code style="color:#00d9ff;min-width:28px;">' + family_id + '</code>'
                '<span style="color:#c8d6e5;font-size:0.8rem;min-width:280px;">' + fname + '</span>'
                '<span style="color:#6b839e;font-size:0.72rem;min-width:90px;">' + str(nist_count) + ' NIST ctrls</span>'
                '<span style="color:#6b839e;font-size:0.72rem;min-width:100px;">' + str(sopra_count) + ' SOPRA ctrls</span>'
                '<div style="flex:1;background:rgba(255,255,255,0.06);border-radius:3px;height:6px;overflow:hidden;">'
                '<div style="width:' + str(pct) + '%;height:100%;background:' + bar_color + ';border-radius:3px;"></div></div>'
                '<span style="color:' + bar_color + ';font-size:0.75rem;font-weight:600;min-width:45px;text-align:right;">' + str(pct) + '%</span>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0.5rem;margin:0.15rem 0;'
                'background:rgba(13,17,23,0.5);border-radius:6px;border:1px solid rgba(255,255,255,0.04);">'
                '<code style="color:#00d9ff;min-width:28px;">' + family_id + '</code>'
                '<span style="color:#c8d6e5;font-size:0.8rem;min-width:280px;">' + fname + '</span>'
                '<span style="color:#6b839e;font-size:0.72rem;">' + str(nist_count) + ' NIST ctrls &rarr; ' + str(sopra_count) + ' SOPRA ctrls</span>'
                '</div>',
                unsafe_allow_html=True
            )

    # CIS stats
    st.markdown("---")
    st.markdown("##### CIS Controls v8 Coverage")
    cis_stats = get_cis_coverage_stats(findings if has_data else None)

    total_cis_benchmarks = sum(s["benchmark_count"] for s in cis_stats.values())
    cis_families = len(cis_stats)

    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("CIS Families Covered", f"{cis_families} / {len(CIS_CONTROLS)}")
    cc2.metric("CIS Benchmarks Mapped", total_cis_benchmarks)
    cc3.metric("SOPRA Controls with CIS Mapping", sum(s["sopra_control_count"] for s in cis_stats.values()))

    for fam_id, stats in cis_stats.items():
        fname = stats["family_name"]
        bcount = stats["benchmark_count"]
        scount = stats["sopra_control_count"]

        if has_data:
            passed = stats["passed"]
            failed = stats["failed"]
            total = passed + failed + stats["not_assessed"]
            pct = round(passed / max(total, 1) * 100)
            bar_color = "#00ff88" if pct >= 80 else "#ffc107" if pct >= 50 else "#e94560"

            st.markdown(
                '<div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0.5rem;margin:0.15rem 0;'
                'background:rgba(13,17,23,0.5);border-radius:6px;border:1px solid rgba(255,255,255,0.04);">'
                '<code style="color:#a855f7;min-width:28px;">CIS ' + fam_id + '</code>'
                '<span style="color:#c8d6e5;font-size:0.8rem;min-width:280px;">' + fname + '</span>'
                '<span style="color:#6b839e;font-size:0.72rem;min-width:90px;">' + str(bcount) + ' benchmarks</span>'
                '<span style="color:#6b839e;font-size:0.72rem;min-width:100px;">' + str(scount) + ' SOPRA ctrls</span>'
                '<div style="flex:1;background:rgba(255,255,255,0.06);border-radius:3px;height:6px;overflow:hidden;">'
                '<div style="width:' + str(pct) + '%;height:100%;background:' + bar_color + ';border-radius:3px;"></div></div>'
                '<span style="color:' + bar_color + ';font-size:0.75rem;font-weight:600;min-width:45px;text-align:right;">' + str(pct) + '%</span>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0.5rem;margin:0.15rem 0;'
                'background:rgba(13,17,23,0.5);border-radius:6px;border:1px solid rgba(255,255,255,0.04);">'
                '<code style="color:#a855f7;min-width:28px;">CIS ' + fam_id + '</code>'
                '<span style="color:#c8d6e5;font-size:0.8rem;min-width:280px;">' + fname + '</span>'
                '<span style="color:#6b839e;font-size:0.72rem;">' + str(bcount) + ' benchmarks &rarr; ' + str(scount) + ' SOPRA ctrls</span>'
                '</div>',
                unsafe_allow_html=True
            )


def _render_nist_crosswalk(findings, has_data):
    """Interactive NIST 800-53 reverse crosswalk."""
    st.markdown("#### 🔄 NIST 800-53 Rev 5 → SOPRA Crosswalk")
    st.caption("Select a NIST control to see which SOPRA findings map to it.")

    index = build_nist_reverse_index_with_findings(findings) if has_data else build_nist_reverse_index()
    nist_ids = list(index.keys())

    # Family filter
    families = sorted(set(_get_nist_family(n) for n in nist_ids))
    family_options = ["All Families"] + [f"{f} — {NIST_FAMILIES.get(f, 'Unknown')}" for f in families]
    selected_family = st.selectbox("Filter by NIST Family:", family_options, key="nist_cw_family")

    if selected_family != "All Families":
        fam_prefix = selected_family.split(" —")[0]
        nist_ids = [n for n in nist_ids if _get_nist_family(n) == fam_prefix]

    # Search
    search = st.text_input("Search NIST Control ID:", key="nist_cw_search", placeholder="e.g., AC-2, SI-4")
    if search:
        nist_ids = [n for n in nist_ids if search.upper() in n.upper()]

    st.markdown(f"**Showing {len(nist_ids)} NIST controls**")

    # Display
    for nist_id in nist_ids:
        entries = index.get(nist_id, [])
        family_name = _get_nist_family_name(nist_id)

        if has_data:
            passed = sum(1 for e in entries if e.get("status") == "Passed")
            failed = sum(1 for e in entries if e.get("status") == "Failed")
            icon = "🟢" if failed == 0 and passed > 0 else "🔴" if failed > 0 else "⚪"
            label = f"{icon} {nist_id} ({family_name}) — {len(entries)} SOPRA controls | {passed} passed, {failed} failed"
        else:
            label = f"📋 {nist_id} ({family_name}) — {len(entries)} SOPRA controls"

        with st.expander(label):
            for entry in entries:
                sid = entry["sopra_id"]
                sname = entry["sopra_name"]
                cat = entry["category"]
                status = entry.get("status", "Not Assessed")
                sev = entry.get("finding_severity", "") or entry.get("severity", entry.get("default_severity", ""))

                status_color = {"Passed": "#00ff88", "Failed": "#e94560", "Not Assessed": "#6b839e"}.get(status, "#6b839e")
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:0.6rem;padding:0.25rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
                    '<code style="color:#00d9ff;font-size:0.8rem;">' + sid + '</code>'
                    '<span style="color:#c8d6e5;font-size:0.8rem;flex:1;">' + sname + '</span>'
                    '<span style="color:#6b839e;font-size:0.7rem;">' + cat + '</span>'
                    '<span style="color:' + status_color + ';font-size:0.75rem;font-weight:600;min-width:80px;text-align:right;">' + status + '</span>'
                    '</div>',
                    unsafe_allow_html=True
                )


def _render_cis_crosswalk(findings, has_data):
    """Interactive CIS Controls v8 reverse crosswalk."""
    st.markdown("#### 🔄 CIS Controls v8 → SOPRA Crosswalk")
    st.caption("Select a CIS benchmark to see which SOPRA findings map to it.")

    index = build_cis_reverse_index_with_findings(findings) if has_data else build_cis_reverse_index()
    cis_ids = list(index.keys())

    # Family filter
    from sopra.isso.crosswalk import _get_cis_family
    cis_families = sorted(set(_get_cis_family(c) for c in cis_ids if _get_cis_family(c)), key=int)
    family_options = ["All CIS Controls"] + [f"CIS {f} — {CIS_CONTROLS.get(f, 'Unknown')}" for f in cis_families]
    selected = st.selectbox("Filter by CIS Control:", family_options, key="cis_cw_family")

    if selected != "All CIS Controls":
        fam_num = selected.split(" — ")[0].replace("CIS ", "")
        cis_ids = [c for c in cis_ids if _get_cis_family(c) == fam_num]

    st.markdown(f"**Showing {len(cis_ids)} CIS benchmarks**")

    for cis_id in cis_ids:
        entries = index.get(cis_id, [])
        fam = _get_cis_family(cis_id)
        family_name = CIS_CONTROLS.get(fam, "Unknown") if fam else "Unknown"

        if has_data:
            passed = sum(1 for e in entries if e.get("status") == "Passed")
            failed = sum(1 for e in entries if e.get("status") == "Failed")
            icon = "🟢" if failed == 0 and passed > 0 else "🔴" if failed > 0 else "⚪"
            label = f"{icon} CIS {cis_id} ({family_name}) — {len(entries)} SOPRA controls | {passed} passed, {failed} failed"
        else:
            label = f"📋 CIS {cis_id} ({family_name}) — {len(entries)} SOPRA controls"

        with st.expander(label):
            for entry in entries:
                sid = entry["sopra_id"]
                sname = entry["sopra_name"]
                cat = entry["category"]
                status = entry.get("status", "Not Assessed")

                status_color = {"Passed": "#00ff88", "Failed": "#e94560", "Not Assessed": "#6b839e"}.get(status, "#6b839e")
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:0.6rem;padding:0.25rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
                    '<code style="color:#a855f7;font-size:0.8rem;">' + sid + '</code>'
                    '<span style="color:#c8d6e5;font-size:0.8rem;flex:1;">' + sname + '</span>'
                    '<span style="color:#6b839e;font-size:0.7rem;">' + cat + '</span>'
                    '<span style="color:' + status_color + ';font-size:0.75rem;font-weight:600;min-width:80px;text-align:right;">' + status + '</span>'
                    '</div>',
                    unsafe_allow_html=True
                )


def _render_export(findings):
    """Download crosswalk documents."""
    st.markdown("#### 📥 Export Crosswalk Documents")
    st.caption("Download audit-ready crosswalk spreadsheets.")

    has_data = len(findings) > 0
    timestamp = datetime.now().strftime("%Y%m%d")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            '<div style="text-align:center;padding:0.8rem;border:1px solid rgba(0,217,255,0.2);border-radius:10px;background:rgba(13,17,23,0.6);min-height:140px;">'
            '<div style="font-size:1.5rem;">📋</div>'
            '<div style="color:#00d9ff;font-weight:700;font-size:0.9rem;margin:0.3rem 0;">Forward Crosswalk</div>'
            '<div style="color:#6b839e;font-size:0.72rem;">SOPRA → NIST + CIS</div>'
            '<div style="color:#6b839e;font-size:0.68rem;">200 controls with all mappings</div>'
            '</div>',
            unsafe_allow_html=True
        )
        csv_data = export_forward_crosswalk_csv(findings if has_data else None)
        st.download_button(
            "📥 Download Forward Crosswalk",
            data=csv_data,
            file_name=f"SOPRA_Forward_Crosswalk_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_fwd_cw"
        )

    with col2:
        st.markdown(
            '<div style="text-align:center;padding:0.8rem;border:1px solid rgba(0,217,255,0.2);border-radius:10px;background:rgba(13,17,23,0.6);min-height:140px;">'
            '<div style="font-size:1.5rem;">🏛️</div>'
            '<div style="color:#00d9ff;font-weight:700;font-size:0.9rem;margin:0.3rem 0;">NIST Reverse Crosswalk</div>'
            '<div style="color:#6b839e;font-size:0.72rem;">NIST 800-53 → SOPRA</div>'
            '<div style="color:#6b839e;font-size:0.68rem;">Every NIST control with SOPRA findings</div>'
            '</div>',
            unsafe_allow_html=True
        )
        nist_csv = export_nist_reverse_crosswalk_csv(findings if has_data else None)
        st.download_button(
            "📥 Download NIST Crosswalk",
            data=nist_csv,
            file_name=f"SOPRA_NIST_Reverse_Crosswalk_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_nist_cw"
        )

    with col3:
        st.markdown(
            '<div style="text-align:center;padding:0.8rem;border:1px solid rgba(0,217,255,0.2);border-radius:10px;background:rgba(13,17,23,0.6);min-height:140px;">'
            '<div style="font-size:1.5rem;">🛡️</div>'
            '<div style="color:#a855f7;font-weight:700;font-size:0.9rem;margin:0.3rem 0;">CIS Reverse Crosswalk</div>'
            '<div style="color:#6b839e;font-size:0.72rem;">CIS v8 → SOPRA</div>'
            '<div style="color:#6b839e;font-size:0.68rem;">Every CIS benchmark with SOPRA findings</div>'
            '</div>',
            unsafe_allow_html=True
        )
        cis_csv = export_cis_reverse_crosswalk_csv(findings if has_data else None)
        st.download_button(
            "📥 Download CIS Crosswalk",
            data=cis_csv,
            file_name=f"SOPRA_CIS_Reverse_Crosswalk_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_cis_cw"
        )

    if has_data:
        st.success("All exports include live assessment data (pass/fail status, severity, evidence).")
    else:
        st.info("Exports include static mappings only. Run an assessment to include live status data.")


def _render_ai_query(findings, has_data):
    """AI-powered natural language crosswalk query interface."""
    st.markdown("#### 🤖 AI Crosswalk Query")
    st.caption("Ask natural language questions about control mappings, coverage gaps, and compliance relationships.")

    st.markdown(
        '<div style="background:rgba(168,85,247,0.05);border:1px solid rgba(168,85,247,0.15);border-radius:10px;padding:0.8rem;margin:0.5rem 0;">'
        '<div style="color:#a855f7;font-weight:700;font-size:0.85rem;margin-bottom:0.4rem;">Example Questions</div>'
        '<div style="color:#c8d6e5;font-size:0.8rem;">'
        '&bull; Which NIST 800-53 controls have no SOPRA mapping?<br>'
        '&bull; What CIS benchmarks cover access control?<br>'
        '&bull; Show me all failed controls mapped to NIST AC family<br>'
        '&bull; Which SOPRA controls map to both NIST SI and CIS 10?<br>'
        '&bull; What is our weakest NIST control family?'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    question = st.text_input("Ask a question about control crosswalks:", key="cw_ai_query", placeholder="e.g., Which NIST families have the most failures?")

    if st.button("🤖 Ask AI", type="primary", key="cw_ai_submit") and question:
        # Build summary indexes for AI context
        nist_index = build_nist_reverse_index_with_findings(findings) if has_data else build_nist_reverse_index()
        cis_index = build_cis_reverse_index_with_findings(findings) if has_data else build_cis_reverse_index()

        # Summarize for prompt
        nist_summary_lines = []
        for nid, entries in list(nist_index.items())[:40]:
            statuses = [e.get("status", "N/A") for e in entries]
            sopra_ids = [e["sopra_id"] for e in entries]
            nist_summary_lines.append(f"{nid}: SOPRA [{', '.join(sopra_ids)}] Status: {', '.join(statuses)}")
        nist_summary = "\n".join(nist_summary_lines)

        cis_summary_lines = []
        for cid, entries in list(cis_index.items())[:30]:
            statuses = [e.get("status", "N/A") for e in entries]
            sopra_ids = [e["sopra_id"] for e in entries]
            cis_summary_lines.append(f"CIS {cid}: SOPRA [{', '.join(sopra_ids)}] Status: {', '.join(statuses)}")
        cis_summary = "\n".join(cis_summary_lines)

        with st.spinner("AI is analyzing crosswalk data..."):
            answer = ai_crosswalk_query(question, nist_summary, cis_summary)

        st.markdown(
            '<div style="background:rgba(0,217,255,0.04);border:1px solid rgba(0,217,255,0.15);border-radius:10px;padding:1rem;margin:0.5rem 0;">'
            '<div style="color:#00d9ff;font-weight:700;font-size:0.85rem;margin-bottom:0.5rem;">🤖 AI Response</div>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown(answer)
