"""SOPRA ISSO — STIG & Benchmark Import (AI-Enhanced)"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime

from sopra.persistence import save_results_to_file
from sopra.isso.ai_engine import ai_map_stig_to_sopra

def render_stig_import():
    """Import DISA STIG or CIS Benchmark scan results with AI auto-mapping to SOPRA controls."""
    st.markdown("## 📥 STIG & Benchmark Import")
    st.markdown("Import DISA STIG Viewer XCCDF results or CIS-CAT Benchmark exports to augment SOPRA assessments.")

    st.markdown("### Supported Formats")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **DISA STIG Viewer**
        - `.xml` (XCCDF results)
        - `.ckl` (STIG Checklist)
        - `.csv` (STIG export)
        """)
    with c2:
        st.markdown("""
        **CIS Benchmarks**
        - `.csv` (CIS-CAT Pro export)
        - `.xml` (CIS-CAT XCCDF)
        - `.json` (CIS-CAT JSON)
        """)

    st.markdown("---")

    uploaded = st.file_uploader("Upload STIG/Benchmark results", type=["csv", "xml", "ckl", "json"], key="stig_upload")

    if uploaded:
        fname = uploaded.name.lower()
        content = uploaded.read()

        if fname.endswith('.csv'):
            try:
                uploaded.seek(0)
                df = pd.read_csv(uploaded)
                st.success(f"Loaded CSV: {len(df)} rows, {len(df.columns)} columns")
                st.dataframe(df.head(20), use_container_width=True)

                # Auto-map columns
                st.markdown("### Column Mapping")
                cols = list(df.columns)
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    col_id = st.selectbox("Control ID column", ["(auto-detect)"] + cols, key="stig_col_id")
                with c2:
                    col_title = st.selectbox("Title / Name column", ["(auto-detect)"] + cols, key="stig_col_title")
                with c3:
                    col_status = st.selectbox("Status / Result column", ["(auto-detect)"] + cols, key="stig_col_status")
                with c4:
                    col_sev = st.selectbox("Severity column", ["(auto-detect)"] + cols, key="stig_col_sev")

                # ── AI Auto-Mapping Section ──────────────────────────
                st.markdown("---")
                st.markdown("### 🤖 AI-Assisted STIG → SOPRA Mapping")
                st.caption("After import, AI will attempt to map each STIG finding to the closest SOPRA control for unified reporting.")

                bc1, bc2 = st.columns(2)
                with bc1:
                    import_btn = st.button("🚀 Import into SOPRA Assessment", type="primary", key="stig_import_btn")
                with bc2:
                    ai_map_btn = st.button("🤖 AI Map to SOPRA Controls", key="stig_ai_map_btn")

                if import_btn:
                    _do_csv_import(df, uploaded, col_id, col_title, col_status, col_sev, cols)

                if ai_map_btn:
                    _do_ai_mapping(df, col_id, col_title, cols)

            except Exception as e:
                st.error(f"Error parsing CSV: {e}")

        elif fname.endswith('.xml') or fname.endswith('.ckl'):
            st.info(f"XML/CKL file detected ({len(content)} bytes). Parsing XCCDF/CKL format...")
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(content)
                findings = []
                for vuln in root.iter():
                    if vuln.tag.endswith('VULN') or 'vuln' in vuln.tag.lower():
                        vid = ""
                        title = ""
                        status = ""
                        sev = "Medium"
                        for child in vuln:
                            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                            if tag == "STIG_DATA":
                                for sd in child:
                                    if sd.text and "Vuln_Num" in (sd.tag.split('}')[-1] if '}' in sd.tag else sd.tag):
                                        vid = sd.text
                            elif 'status' in tag.lower():
                                status = child.text or ""
                            elif 'severity' in tag.lower():
                                sev = child.text or "Medium"
                        if vid or title:
                            passed = any(w in status.lower() for w in ["not_a_finding", "notafinding", "pass"])
                            findings.append({
                                "control_id": vid or f"CKL-{len(findings)+1}",
                                "control_name": title or f"STIG Finding {vid}",
                                "status": "Passed" if passed else "Failed",
                                "severity": sev.capitalize() if sev else "Medium",
                                "category": f"STIG Import - {uploaded.name}",
                                "family": "System & Information Integrity"
                            })
                if findings:
                    st.success(f"Parsed {len(findings)} findings from XML/CKL.")
                else:
                    st.warning("Could not auto-parse findings. Ensure the file is XCCDF or CKL format.")
            except Exception as e:
                st.error(f"Error parsing XML/CKL: {e}")

        elif fname.endswith('.json'):
            try:
                data = json.loads(content)
                st.success(f"Loaded JSON: {type(data).__name__}")
                if isinstance(data, list):
                    st.write(f"{len(data)} records found.")
                elif isinstance(data, dict):
                    st.write(f"Keys: {list(data.keys())[:10]}")
                st.json(data if isinstance(data, dict) else data[:5] if isinstance(data, list) else data)
                st.info("JSON import: review the structure above and use CSV export from your tool for best results.")
            except Exception as e:
                st.error(f"Error parsing JSON: {e}")


def _do_csv_import(df, uploaded, col_id, col_title, col_status, col_sev, cols):
    """Standard CSV import logic."""
    id_col = _auto_detect_col(cols, col_id, ["vuln_id", "rule_id", "control", "id", "stig_id", "v-id", "cci"])
    title_col = _auto_detect_col(cols, col_title, ["title", "name", "description", "rule_title", "check_name"])
    status_col = _auto_detect_col(cols, col_status, ["status", "result", "finding", "pass_fail", "compliance"])
    sev_col = _auto_detect_col(cols, col_sev, ["severity", "cat", "risk", "impact", "sev"])

    findings = []
    for _, row in df.iterrows():
        raw_status = str(row.get(status_col, "")).lower() if status_col else ""
        passed = any(w in raw_status for w in ["pass", "not a finding", "notafinding", "compliant", "true"])
        sev_raw = str(row.get(sev_col, "Medium")) if sev_col else "Medium"
        sev_map = {"cat i": "Critical", "cat ii": "High", "cat iii": "Medium",
                   "high": "High", "critical": "Critical", "medium": "Medium", "low": "Low",
                   "1": "Critical", "2": "High", "3": "Medium", "4": "Low"}
        severity = sev_map.get(sev_raw.lower().strip(), "Medium")
        findings.append({
            "control_id": str(row.get(id_col, f"STIG-{len(findings)+1}")) if id_col else f"STIG-{len(findings)+1}",
            "control_name": str(row.get(title_col, "Imported Finding")) if title_col else "Imported Finding",
            "status": "Passed" if passed else "Failed",
            "severity": severity,
            "category": f"STIG Import - {uploaded.name}",
            "family": "System & Information Integrity"
        })

    if findings:
        existing = st.session_state.get("opra_assessment_results")
        if existing and existing.get("findings"):
            existing["findings"].extend(findings)
            existing["source"] = existing.get("source", "") + f" + STIG({uploaded.name})"
        else:
            existing = {
                "findings": findings,
                "timestamp": datetime.now().isoformat(),
                "source": f"STIG Import ({uploaded.name})"
            }
        st.session_state.opra_assessment_results = existing
        save_results_to_file(existing)
        st.success(f"Imported {len(findings)} findings ({len([f for f in findings if f['status']=='Failed'])} failed). Assessment data updated.")
    else:
        st.warning("No findings could be parsed from the file.")


def _do_ai_mapping(df, col_id, col_title, cols):
    """AI-powered mapping of STIG findings to SOPRA controls."""
    from sopra_controls import ALL_CONTROLS

    id_col = _auto_detect_col(cols, col_id, ["vuln_id", "rule_id", "control", "id", "stig_id", "v-id", "cci"])
    title_col = _auto_detect_col(cols, col_title, ["title", "name", "description", "rule_title", "check_name"])

    stig_findings = []
    for _, row in df.head(25).iterrows():
        stig_findings.append({
            "stig_id": str(row.get(id_col, "")) if id_col else "",
            "title": str(row.get(title_col, "")) if title_col else "",
        })

    sopra_summary = "\n".join([f"{cid}: {ctrl.name}" for cid, ctrl in list(ALL_CONTROLS.items())[:60]])

    with st.spinner("AI is mapping STIG findings to SOPRA controls..."):
        mappings = ai_map_stig_to_sopra(stig_findings, sopra_summary)

    if mappings:
        st.success(f"AI mapped **{len(mappings)}** STIG findings to SOPRA controls:")
        for m in mappings:
            conf_color = {"high": "#00ff88", "medium": "#ffc107", "low": "#e94560"}.get(m.get("confidence", "low"), "#888")
            st.markdown(
                '<div style="display:flex;align-items:center;gap:0.6rem;padding:0.3rem 0.5rem;margin:0.15rem 0;'
                'background:rgba(13,17,23,0.5);border-radius:6px;border:1px solid rgba(255,255,255,0.04);">'
                '<code style="color:#ff6b6b;min-width:100px;">' + m.get("stig_id", "N/A") + '</code>'
                '<span style="color:#6b839e;">&#x2192;</span>'
                '<code style="color:#00d9ff;min-width:80px;">' + m.get("sopra_id", "N/A") + '</code>'
                '<span style="color:' + conf_color + ';font-size:0.75rem;font-weight:600;">' + m.get("confidence", "N/A").upper() + '</span>'
                '<span style="color:#c8d6e5;font-size:0.8rem;flex:1;">' + m.get("reason", "") + '</span>'
                '</div>',
                unsafe_allow_html=True
            )
    else:
        st.warning("AI could not map findings. Import the file first, then try mapping.")


def _auto_detect_col(cols, user_choice, patterns):
    """Auto-detect a column from common naming patterns."""
    if user_choice and user_choice != "(auto-detect)":
        return user_choice
    for pat in patterns:
        for c in cols:
            if pat in c.lower():
                return c
    return cols[0] if cols else None
