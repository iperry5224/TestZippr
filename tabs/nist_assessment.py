"""NIST 800-171 / 800-53 self-assessment tab."""

import json
import io
from typing import Dict, List

import streamlit as st
import pandas as pd

from utils.file_io import safe_read_upload, safe_write_bytes

NIST_FAMILIES = {
    "AC": "Access Control",
    "AT": "Awareness and Training",
    "AU": "Audit and Accountability",
    "CA": "Assessment, Authorization, and Monitoring",
    "CM": "Configuration Management",
    "CP": "Contingency Planning",
    "IA": "Identification and Authentication",
    "IR": "Incident Response",
    "MA": "Maintenance",
    "MP": "Media Protection",
    "PE": "Physical and Environmental Protection",
    "PL": "Planning",
    "PM": "Program Management",
    "PS": "Personnel Security",
    "RA": "Risk Assessment",
    "SA": "System and Services Acquisition",
    "SC": "System and Communications Protection",
    "SI": "System and Information Integrity",
    "SR": "Supply Chain Risk Management",
}

IMPLEMENTATION_STATUS = [
    "Not Implemented",
    "Partially Implemented",
    "Implemented",
    "Not Applicable",
]


def _default_controls() -> Dict[str, List[dict]]:
    controls: Dict[str, List[dict]] = {}
    for code, name in NIST_FAMILIES.items():
        controls[code] = []
        for i in range(1, 4):
            controls[code].append({
                "id": f"{code}-{i}",
                "title": f"{name} – Control {i}",
                "status": "Not Implemented",
                "notes": "",
            })
    return controls


def _init_state():
    if "nist_controls" not in st.session_state:
        st.session_state.nist_controls = _default_controls()


def render_nist_assessment():
    _init_state()
    st.header("NIST Compliance Assessment")
    st.markdown(
        "Assess your organization against NIST 800-171 / 800-53 control families. "
        "Update implementation status and add notes for each control."
    )

    col_upload, col_export = st.columns([1, 1])
    with col_upload:
        uploaded = st.file_uploader(
            "Import previous assessment (JSON)",
            type=["json"],
            key="nist_upload",
        )
        if uploaded is not None:
            raw = safe_read_upload(uploaded)
            if raw:
                try:
                    st.session_state.nist_controls = json.loads(raw)
                    st.success("Assessment imported.")
                except json.JSONDecodeError:
                    st.error("Invalid JSON file.")

    with col_export:
        if st.button("Export Assessment", key="nist_export"):
            payload = json.dumps(st.session_state.nist_controls, indent=2)
            st.download_button(
                "Download JSON",
                data=payload,
                file_name="nist_assessment.json",
                mime="application/json",
                key="nist_dl",
            )

    _render_summary()
    _render_controls()


def _render_summary():
    counts = {"Not Implemented": 0, "Partially Implemented": 0, "Implemented": 0, "Not Applicable": 0}
    for family_controls in st.session_state.nist_controls.values():
        for ctrl in family_controls:
            status = ctrl.get("status", "Not Implemented")
            if status in counts:
                counts[status] += 1

    total = sum(counts.values()) or 1
    st.subheader("Assessment Summary")
    cols = st.columns(4)
    labels = list(counts.keys())
    colors = ["🔴", "🟡", "🟢", "⚪"]
    for col, label, color in zip(cols, labels, colors):
        col.metric(f"{color} {label}", counts[label], f"{counts[label]*100//total}%")

    st.progress(counts["Implemented"] / total)


def _render_controls():
    st.subheader("Control Families")
    family_code = st.selectbox(
        "Select family",
        options=list(NIST_FAMILIES.keys()),
        format_func=lambda c: f"{c} – {NIST_FAMILIES[c]}",
        key="nist_family_select",
    )
    if family_code is None:
        return

    controls = st.session_state.nist_controls.get(family_code, [])
    for idx, ctrl in enumerate(controls):
        with st.expander(f"{ctrl['id']}: {ctrl['title']}", expanded=False):
            new_status = st.selectbox(
                "Status",
                IMPLEMENTATION_STATUS,
                index=IMPLEMENTATION_STATUS.index(ctrl.get("status", "Not Implemented")),
                key=f"nist_status_{ctrl['id']}",
            )
            new_notes = st.text_area(
                "Notes / Evidence",
                value=ctrl.get("notes", ""),
                key=f"nist_notes_{ctrl['id']}",
            )
            ctrl["status"] = new_status
            ctrl["notes"] = new_notes
