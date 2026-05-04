"""AWS Console integration tab for viewing security posture."""

import json

import streamlit as st

from utils.file_io import safe_read_upload


def _init_state():
    if "aws_regions" not in st.session_state:
        st.session_state.aws_regions = [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-central-1", "ap-southeast-1",
        ]
    if "aws_findings" not in st.session_state:
        st.session_state.aws_findings = []
    if "aws_credentials_set" not in st.session_state:
        st.session_state.aws_credentials_set = False


def render_aws_console():
    _init_state()
    st.header("AWS Security Console")
    st.markdown(
        "Connect to your AWS environment to pull Security Hub findings, "
        "IAM reports, and compliance status."
    )

    _render_connection_panel()
    st.divider()
    _render_findings()
    st.divider()
    _render_import()


def _render_connection_panel():
    st.subheader("Connection Settings")
    col1, col2 = st.columns(2)
    with col1:
        region = st.selectbox(
            "AWS Region",
            st.session_state.aws_regions,
            key="aws_region_select",
        )
        access_key = st.text_input("Access Key ID", type="password", key="aws_ak")
    with col2:
        secret_key = st.text_input("Secret Access Key", type="password", key="aws_sk")
        session_token = st.text_input(
            "Session Token (optional)", type="password", key="aws_st"
        )

    if st.button("Connect", key="aws_connect"):
        if not access_key or not secret_key:
            st.warning("Please provide Access Key ID and Secret Access Key.")
        else:
            try:
                import boto3

                client = boto3.client(
                    "securityhub",
                    region_name=region,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    aws_session_token=session_token or None,
                )
                resp = client.get_findings(MaxResults=20)
                st.session_state.aws_findings = resp.get("Findings", [])
                st.session_state.aws_credentials_set = True
                st.success(
                    f"Connected. Retrieved {len(st.session_state.aws_findings)} findings."
                )
            except ImportError:
                st.error(
                    "boto3 is not installed. Install it with: pip install boto3"
                )
            except Exception as exc:
                st.error(f"AWS connection failed: {exc}")


def _render_findings():
    st.subheader("Security Hub Findings")
    findings = st.session_state.aws_findings
    if not findings:
        st.info(
            "No findings loaded. Connect to AWS or import a findings JSON file below."
        )
        return

    severity_map = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "INFORMATIONAL": "⚪"}

    for i, finding in enumerate(findings):
        severity = finding.get("Severity", {}).get("Label", "INFORMATIONAL")
        icon = severity_map.get(severity, "⚪")
        title = finding.get("Title", f"Finding {i + 1}")
        with st.expander(f"{icon} [{severity}] {title}"):
            st.json(finding)


def _render_import():
    st.subheader("Import Findings")
    uploaded = st.file_uploader(
        "Upload AWS Security Hub findings export (JSON)",
        type=["json"],
        key="aws_upload",
    )
    if uploaded is not None:
        raw = safe_read_upload(uploaded)
        if raw:
            try:
                data = json.loads(raw)
                if isinstance(data, list):
                    st.session_state.aws_findings = data
                elif isinstance(data, dict) and "Findings" in data:
                    st.session_state.aws_findings = data["Findings"]
                else:
                    st.session_state.aws_findings = [data]
                st.success(f"Imported {len(st.session_state.aws_findings)} findings.")
            except json.JSONDecodeError:
                st.error("Invalid JSON file.")
