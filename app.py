import streamlit as st
import os
import tempfile
import json
import io
from pathlib import Path

from tabs.nist_assessment import render_nist_assessment
from tabs.aws_console import render_aws_console
from tabs.chad_ai import render_chad_ai
from tabs.risk_calculator import render_risk_calculator
from tabs.ssp_generator import render_ssp_generator


def safe_temp_dir():
    """Return a safe temporary directory, creating it if needed."""
    tmp = Path(tempfile.gettempdir()) / "zippr_workspace"
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp


def init_session_state():
    defaults = {
        "nist_data": {},
        "aws_config": {},
        "risk_scores": {},
        "ssp_sections": {},
        "chat_history": [],
        "temp_dir": str(safe_temp_dir()),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    st.set_page_config(
        page_title="Zippr – Compliance Suite",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    init_session_state()

    tab_nist, tab_aws, tab_chad, tab_risk, tab_ssp = st.tabs([
        "🛡️ NIST Assessment",
        "☁️ AWS Console",
        "🤖 Chad (AI)",
        "📊 Risk Calculator",
        "📄 SSP Generator",
    ])

    with tab_nist:
        render_nist_assessment()

    with tab_aws:
        render_aws_console()

    with tab_chad:
        render_chad_ai()

    with tab_risk:
        render_risk_calculator()

    with tab_ssp:
        render_ssp_generator()


if __name__ == "__main__":
    main()
