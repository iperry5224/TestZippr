"""SOPRA Settings Page"""
import streamlit as st

def render_settings_page():
    """Render the settings page"""
    st.markdown("## ⚙️ SOPRA Settings")
    
    with st.expander("🎨 Appearance", expanded=True):
        st.selectbox("Theme", ["Dark (Default)", "Light", "High Contrast"])
        st.checkbox("Show control families in reports", value=True)
        st.checkbox("Enable animations", value=True)
    
    with st.expander("🔗 Integrations", expanded=False):
        st.markdown("**Vulnerability Scanners**")
        st.text_input("Nessus API URL")
        st.text_input("Nessus API Key", type="password")
        
        st.markdown("**SIEM Integration**")
        st.text_input("Splunk URL")
        st.text_input("Splunk Token", type="password")
    
    with st.expander("🤖 AI Configuration", expanded=False):
        st.markdown("**AWS Bedrock Settings**")
        st.text_input("AWS Region", value="us-east-1")
        st.selectbox("AI Model", ["NVIDIA Nemotron Nano 12B", "Amazon Titan", "Llama 3", "Mistral"])
        st.slider("Response Temperature", 0.0, 1.0, 0.7)
    
    with st.expander("📊 Report Settings", expanded=False):
        st.text_input("Organization Name", value="Your Organization")
        st.text_area("Report Header Text")
        st.file_uploader("Organization Logo")
