"""SOPRA AI Assistant Page"""
import re
import tempfile
import streamlit as st
import plotly.graph_objects as go
import json
import os
import base64
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from sopra.utils import calculate_risk_score
from sopra.persistence import load_results_from_file
from wordy import create_report_from_content

# Claude removed per policy
BEDROCK_MODELS = [
    "nvidia.nemotron-nano-12b-v2",
    "amazon.titan-text-express-v1",
    "amazon.titan-text-lite-v1",
    "meta.llama3-8b-instruct-v1:0",
    "mistral.mistral-7b-instruct-v0:2",
]

def call_bedrock_ai(messages: list, system_prompt: str, max_tokens: int = 4096, region: str = "us-east-1") -> str:
    """
    Call AI via Amazon Bedrock (data stays within AWS).
    Tries multiple models until one works.
    """
    try:
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=region
        )
        
        # Format messages for Bedrock Converse API
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": [{"text": msg["content"]}]
            })
        
        # Try each model until one works
        last_error = None
        for model_id in BEDROCK_MODELS:
            try:
                response = bedrock.converse(
                    modelId=model_id,
                    messages=formatted_messages,
                    system=[{"text": system_prompt}],
                    inferenceConfig={
                        "maxTokens": min(max_tokens, 4096),
                        "temperature": 0.7,
                    }
                )
                return response['output']['message']['content'][0]['text']
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code in ['AccessDeniedException', 'ValidationException', 'ResourceNotFoundException']:
                    last_error = f"{model_id}: {error_code}"
                    continue
                else:
                    raise
        
        raise Exception(f"No Bedrock models available. Last error: {last_error}")
        
    except NoCredentialsError:
        raise Exception("AWS credentials not configured. Please configure AWS credentials first.")
    except Exception as e:
        error_msg = str(e)
        if "No Bedrock models available" in error_msg:
            raise Exception("""
⚠️ **Bedrock Not Configured**

    To use SOPRA AI, you need to enable a model in Amazon Bedrock:

1. Go to **AWS Console** → **Amazon Bedrock**
2. Look for **Model catalog** or **Foundation models**
3. Select a model (Titan, Llama, or Mistral)
4. Click **Request access** or **Enable**

Run this to check available models:
```
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[*].modelId'
```
""")
        raise Exception(f"Bedrock error: {error_msg}")


def render_ai_assistant():
    """Render the AI assistant page powered by AWS Bedrock"""
    # Load Chad's avatar
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    chad_path = os.path.join(_project_root, "assets", "chad2.jpg")
    chad_b64 = ""
    if os.path.exists(chad_path):
        with open(chad_path, "rb") as img_f:
            chad_b64 = base64.b64encode(img_f.read()).decode()

    # Header with Chad
    if chad_b64:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <img src="data:image/jpeg;base64,{chad_b64}"
                 style="width: 64px; height: 64px; border-radius: 50%; border: 2px solid #00d9ff;
                        box-shadow: 0 0 15px rgba(0,217,255,0.3); object-fit: cover;">
            <div>
                <h2 style="color: #f5f5f5; margin: 0;">Chad — SOPRA AI Assistant</h2>
                <p style="color: #5a7a9a; margin: 0; font-size: 0.85rem;">
                    Your on-premise security expert powered by AWS Bedrock</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("## 💬 SOPRA AI Assistant")
        st.markdown("Your on-premise security expert powered by AWS Bedrock 🔒")

    # Chat interface
    chat_container = st.container()

    with chat_container:
        # Display chat history
        for i, message in enumerate(st.session_state.opra_chat_history):
            if message["role"] == "user":
                st.markdown(
                    '<div style="background:#0f3460;padding:1rem;border-radius:10px;margin:0.5rem 0;border-left:3px solid #00d9ff;">'
                    '<strong style="color:#00d9ff;">You:</strong>'
                    '<p style="color:#f5f5f5;margin:0.5rem 0 0 0;">' + message["content"] + '</p></div>',
                    unsafe_allow_html=True)
            else:
                chad_img = '<img src="data:image/jpeg;base64,' + chad_b64 + '" style="width:28px;height:28px;border-radius:50%;object-fit:cover;vertical-align:middle;margin-right:0.4rem;border:1.5px solid #00d9ff;">' if chad_b64 else ''
                st.markdown(
                    '<div style="background:#16213e;padding:1rem;border-radius:10px;margin:0.5rem 0;border-left:3px solid #00d9ff;">'
                    '<div style="display:flex;align-items:center;gap:0.3rem;">' + chad_img
                    + '<strong style="color:#00d9ff;">Chad — SOPRA AI:</strong></div>'
                    '<p style="color:#f5f5f5;margin:0.5rem 0 0 0;">' + message["content"] + '</p></div>',
                    unsafe_allow_html=True)
                # Render charts after the last assistant message if it was a data question
                if message.get("show_charts"):
                    if "_chart_idx" not in st.session_state:
                        st.session_state._chart_idx = 0
                    st.session_state._chart_idx += 1
                    _render_assessment_charts(st.session_state._chart_idx)
                # Download button for report (Google Docs–compatible .docx) after last assistant message
                is_last_assistant = i == len(st.session_state.opra_chat_history) - 1
                if is_last_assistant and st.session_state.get("opra_report_docx"):
                    fn, data = st.session_state.opra_report_docx
                    st.download_button(
                        label=f"📥 Download Report ({fn}) — upload to Google Drive to open as Google Doc",
                        data=data,
                        file_name=fn,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True,
                        key="opra_report_download"
                    )
    
    # Quick action buttons
    st.markdown("### ⚡ Quick Questions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Calculate My Risk Score", use_container_width=True):
            add_ai_response("Calculate my risk score and show me the assessment results with charts")
    
    with col2:
        if st.button("🔐 AD Security Best Practices", use_container_width=True):
            add_ai_response("What are the best practices for Active Directory security?")
    
    with col3:
        if st.button("🌐 Network Segmentation Tips", use_container_width=True):
            add_ai_response("How should I implement network segmentation?")
    
    with col4:
        if st.button("💻 Endpoint Hardening Guide", use_container_width=True):
            add_ai_response("What are the key endpoint hardening measures?")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        if st.button("🔗 Analyze Attack Chains", use_container_width=True):
            add_ai_response("Analyze my failed controls for attack chains and tell me which single fix would break the most chains")
    with col6:
        if st.button("🧠 Generate Remediation Plan", use_container_width=True):
            add_ai_response("Generate a detailed remediation plan for my most critical failed controls, including step-by-step commands")
    with col7:
        if st.button("⚠️ Change Impact Analysis", use_container_width=True):
            add_ai_response("What are the downstream impacts and risks of remediating my critical and high severity findings?")
    with col8:
        if st.button("🎫 Ticket Summary", use_container_width=True):
            add_ai_response("Summarize my failed controls in a format suitable for creating remediation tickets, with priorities and SLA deadlines")
    with st.expander("📄 Generate Report (Google Docs)", expanded=True):
        st.caption("Ask Chad to create a report—it will produce a download link for a Word/Google Docs–compatible file.")
        with st.form("generate_report_form", clear_on_submit=True):
            report_name = st.text_input("Report name", value="My Security Report", key="report_name_input")
            submitted = st.form_submit_button("📝 Generate Report")
        if submitted and report_name and str(report_name).strip():
            add_ai_response(f"Based on my current assessment, create a comprehensive report including risk profile, predictive analytics, and recommendations. Put it in a report called \"{str(report_name).strip()}\" in Google Docs format.")
    
    # User input
    user_input = st.chat_input("Ask SOPRA AI about on-premise security...")
    
    if user_input:
        add_ai_response(user_input)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.opra_chat_history = []
        if "opra_report_docx" in st.session_state:
            del st.session_state.opra_report_docx
        st.rerun()


def _extract_report_request(question: str):
    """Detect if user is asking for a report with a name; extract the report title."""
    q = question.lower()
    if "report" not in q and "document" not in q and "google docs" not in q:
        return False, None
    # Patterns: "report called X", "report named X", "put it in a report called X", "report X in Google Docs"
    patterns = [
        r'report\s+(?:called|named|titled?)\s+["\']?([^"\']{3,120})["\']?',
        r'(?:put|save)\s+(?:it\s+)?(?:in\s+)?(?:a\s+)?report\s+(?:called|named)\s+["\']?([^"\']{3,120})["\']?',
        r'in\s+(?:a\s+)?(?:report\s+)?(?:called|named)\s+["\']?([^"\']{3,120})["\']?\s*(?:in\s+google\s+docs)?',
        r'["\']([^"\']{5,100})["\']\s*(?:in\s+google\s+docs\s+format|as\s+a\s+report)',
        r'report\s+["\']([^"\']{5,100})["\']',
    ]
    for pat in patterns:
        m = re.search(pat, question, re.I)
        if m:
            name = m.group(1).strip()
            # Clean trailing punctuation
            name = re.sub(r'[.,;:\s]+$', '', name)
            if len(name) >= 3:
                return True, name
    # Generic report request - use default name
    if "google docs" in q or "put it in a report" in q:
        return True, "SOPRA Report"
    return False, None


def add_ai_response(question):
    """Add user question and AI response to chat via AWS Bedrock"""
    # Clear any previous report download (new request = fresh state)
    if "opra_report_docx" in st.session_state:
        del st.session_state.opra_report_docx

    st.session_state.opra_chat_history.append({
        "role": "user",
        "content": question
    })

    is_report_request, report_name = _extract_report_request(question)
    show_charts = _should_show_charts(question)

    # Build context from assessment data if available
    context = build_assessment_context()

    # Build the system prompt for SOPRA AI
    _chart_hint = ""
    if show_charts:
        _chart_hint = "\nThe user is asking about assessment data/risk. Provide a concise analytical summary of the numbers. Interactive charts will be displayed automatically below your response — reference them (e.g. 'as shown in the charts below').\n"

    _report_hint = ""
    if is_report_request:
        _report_hint = f"""
REPORT GENERATION (CRITICAL):
The user has requested a report{f' named "{report_name}"' if report_name else ''} for Google Docs/Word format.
You MUST produce a COMPLETE, FINAL report — NOT an outline, NOT placeholders, NOT "[Insert Date]" or "[Your Name]".
- Write the full report content with all sections fully filled in
- Use the exact date: {__import__('datetime').datetime.now().strftime("%B %d, %Y")}
- Include executive summary, findings, predictive analytics, recommendations — all complete
- Format with markdown: # for headings, ** for bold, - for bullet lists
- The report will be exported to a Word document (Google Docs compatible) automatically
"""

    system_prompt = f"""You are SOPRA AI (codename "Chad"), an expert on-premise security analyst and remediation engineer specializing in enterprise infrastructure security.

You help security professionals with:
- Active Directory security and hardening
- Network infrastructure security (firewalls, segmentation, IDS/IPS)
- Endpoint security and hardening (Windows, Linux)
- Server security (databases, web servers, virtualization)
- Physical security controls
- Data protection and encryption
- Identity and access management
- Security monitoring and SIEM

REMEDIATION CAPABILITIES:
When users ask you to "fix", "remediate", "harden", "secure", or "script" something:
1. Provide a COMPLETE, copy-paste-ready PowerShell script with comments explaining each line
2. Include pre-checks (verify current state), the fix itself, and post-checks (verify the fix worked)
3. Wrap dangerous commands in -WhatIf or confirmation prompts
4. Always include a rollback section
5. Specify if a reboot or downtime is required
6. Estimate implementation time

When users ask about risk prioritization or attack chains:
- Explain how multiple failed controls combine to create exploitable paths
- Recommend which single fix would break the most attack chains

You provide practical, actionable advice with specific commands (PowerShell, Cisco IOS, etc.) when appropriate.
Use markdown formatting for clarity. Be concise but thorough.
{_chart_hint}{_report_hint}
{context}"""
    
    # Build messages for Bedrock
    messages = []
    for msg in st.session_state.opra_chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    try:
        with st.spinner("🤔 SOPRA AI is thinking..."):
            response = call_bedrock_ai(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=8192 if is_report_request else 4096
            )
    except Exception as e:
        # Fallback to local responses if Bedrock fails
        response = generate_fallback_response(question, str(e))

    msg = {"role": "assistant", "content": response}
    if show_charts:
        msg["show_charts"] = True
    st.session_state.opra_chat_history.append(msg)

    # Create Word/Google Docs-compatible report when requested
    if is_report_request and report_name and response:
        try:
            safe_fn = re.sub(r'[<>:"/\\|?*]', '_', report_name).strip()[:80] or "SOPRA_Report"
            fd, path = tempfile.mkstemp(suffix=".docx", prefix="sopra_")
            os.close(fd)
            create_report_from_content(title=report_name, content=response, output_path=path)
            with open(path, "rb") as f:
                doc_bytes = f.read()
            os.unlink(path)
            download_fn = f"{safe_fn}.docx"
            st.session_state.opra_report_docx = (download_fn, doc_bytes)
        except Exception as ex:
            st.session_state.opra_report_docx = None

    st.rerun()


def build_assessment_context():
    """Build context from current assessment data"""
    if not st.session_state.get('opra_assessment_results'):
        st.session_state.opra_assessment_results = load_results_from_file()

    if not st.session_state.opra_assessment_results:
        return "No assessment data available yet."
    
    results = st.session_state.opra_assessment_results
    findings = results.get("findings", [])
    
    total = len(findings)
    passed = len([f for f in findings if f["status"] == "Passed"])
    failed = len([f for f in findings if f["status"] == "Failed"])
    score = calculate_risk_score(findings)
    
    context = f"""Current Assessment Context:
- Total Controls: {total}
- Passed: {passed}
- Failed: {failed}
- Risk Score: {score}%

Failed Controls (top issues):
"""
    failed_findings = [f for f in findings if f["status"] == "Failed"][:10]
    for f in failed_findings:
        context += f"- {f['control_id']}: {f['control_name']} ({f.get('severity', 'Unknown')} severity)\n"
    
    return context


def _should_show_charts(question):
    """Detect if user question is about risk score, assessment data, or visualizations"""
    q = question.lower()
    triggers = [
        "risk score", "risk gauge", "calculate", "assessment",
        "chart", "graph", "pie", "visual", "show me", "display",
        "score", "findings", "compliance", "severity", "posture",
        "how are we doing", "status", "overview", "summary",
        "data", "results", "metrics", "statistics", "stats",
        "passed", "failed", "critical", "high", "medium", "low"
    ]
    return any(t in q for t in triggers)


def _render_assessment_charts(idx=0):
    """Render interactive assessment charts inline in the AI assistant"""
    # Load from session or file
    results = st.session_state.get('opra_assessment_results')
    if not results:
        results = load_results_from_file()
    if not results or not results.get("findings"):
        st.info("No assessment data available yet. Run an assessment or Run Security Controls Assessment first.")
        return

    findings = results["findings"]
    total = len(findings)
    passed = len([f for f in findings if f.get("status") == "Passed"])
    failed = len([f for f in findings if f.get("status") == "Failed"])
    not_assessed = total - passed - failed
    score = calculate_risk_score(findings)

    # Severity breakdown
    sev_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for f in findings:
        if f.get("status") == "Failed" and f.get("severity") in sev_counts:
            sev_counts[f["severity"]] += 1

    # Category breakdown
    cat_passed = {}
    cat_failed = {}
    for f in findings:
        cat = f.get("category", "Unknown")
        if f.get("status") == "Passed":
            cat_passed[cat] = cat_passed.get(cat, 0) + 1
        elif f.get("status") == "Failed":
            cat_failed[cat] = cat_failed.get(cat, 0) + 1

    _bg = 'rgba(0,0,0,0)'
    _font = dict(color='#c8d6e5')

    # --- Row 1: Risk Gauge + Compliance Donut ---
    c1, c2 = st.columns(2)

    with c1:
        # Risk gauge
        gauge_color = "#00ff88" if score >= 80 else "#ffc107" if score >= 50 else "#e94560"
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title=dict(text="Risk Score", font=dict(color='#00d9ff', size=16)),
            number=dict(suffix="%", font=dict(color=gauge_color, size=36)),
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor='#4a6a8a', tickfont=dict(color='#4a6a8a')),
                bar=dict(color=gauge_color),
                bgcolor='rgba(22,36,64,0.4)',
                bordercolor='rgba(0,217,255,0.15)',
                steps=[
                    dict(range=[0, 40], color='rgba(233,69,96,0.2)'),
                    dict(range=[40, 60], color='rgba(255,107,107,0.2)'),
                    dict(range=[60, 80], color='rgba(255,193,7,0.2)'),
                    dict(range=[80, 100], color='rgba(0,217,255,0.2)'),
                ]
            )
        ))
        fig_gauge.update_layout(paper_bgcolor=_bg, plot_bgcolor=_bg, height=260,
                                margin=dict(t=50, b=10, l=30, r=30), font=_font)
        st.plotly_chart(fig_gauge, use_container_width=True, key=f"chad_gauge_{idx}")

    with c2:
        # Compliance donut
        fig_donut = go.Figure(go.Pie(
            labels=["Passed", "Failed", "Not Assessed"],
            values=[passed, failed, not_assessed],
            hole=0.6,
            marker=dict(colors=["#00d9ff", "#e94560", "#4a6a8a"],
                        line=dict(color='#0d1117', width=2)),
            textinfo='label+value',
            textfont=dict(size=11, color='#c8d6e5'),
            hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
        ))
        fig_donut.add_annotation(text=f"{round(passed/max(total,1)*100)}%",
                                 x=0.5, y=0.5, font=dict(size=28, color='#00d9ff'), showarrow=False)
        fig_donut.update_layout(paper_bgcolor=_bg, plot_bgcolor=_bg, height=260,
                                margin=dict(t=30, b=10, l=10, r=10), font=_font,
                                showlegend=True,
                                legend=dict(font=dict(size=10, color='#c8d6e5'),
                                            bgcolor=_bg, orientation='h',
                                            x=0.5, xanchor='center', y=-0.05),
                                title=dict(text="Compliance Breakdown", font=dict(size=16, color='#00d9ff'), x=0.5))
        st.plotly_chart(fig_donut, use_container_width=True, key=f"chad_donut_{idx}")

    # --- Row 2: Severity Bar + Category Horizontal Bar ---
    c3, c4 = st.columns(2)

    with c3:
        # Severity bar chart
        sev_names = list(sev_counts.keys())
        sev_vals = list(sev_counts.values())
        sev_colors = ["#e94560", "#ff6b6b", "#ffc107", "#00d9ff"]
        fig_sev = go.Figure(go.Bar(
            x=sev_names, y=sev_vals,
            marker_color=sev_colors,
            text=sev_vals, textposition='outside',
            textfont=dict(color='#c8d6e5', size=13)
        ))
        fig_sev.update_layout(paper_bgcolor=_bg, plot_bgcolor=_bg, height=260,
                              margin=dict(t=40, b=30, l=20, r=20), font=_font,
                              title=dict(text="Findings by Severity", font=dict(size=16, color='#00d9ff'), x=0.5),
                              xaxis=dict(tickfont=dict(color='#c8d6e5'), gridcolor='rgba(0,217,255,0.06)'),
                              yaxis=dict(tickfont=dict(color='#4a6a8a'), gridcolor='rgba(0,217,255,0.06)'))
        st.plotly_chart(fig_sev, use_container_width=True, key=f"chad_sev_{idx}")

    with c4:
        # Category horizontal bar (pass vs fail)
        all_cats = sorted(set(list(cat_passed.keys()) + list(cat_failed.keys())))
        # Shorten category names
        short_cats = [c[:18] + "..." if len(c) > 20 else c for c in all_cats]
        p_vals = [cat_passed.get(c, 0) for c in all_cats]
        f_vals = [cat_failed.get(c, 0) for c in all_cats]
        fig_cat = go.Figure()
        fig_cat.add_trace(go.Bar(y=short_cats, x=p_vals, name='Passed',
                                  orientation='h', marker_color='#00d9ff'))
        fig_cat.add_trace(go.Bar(y=short_cats, x=f_vals, name='Failed',
                                  orientation='h', marker_color='#e94560'))
        fig_cat.update_layout(paper_bgcolor=_bg, plot_bgcolor=_bg, height=260,
                              margin=dict(t=40, b=10, l=10, r=10), font=_font,
                              barmode='stack',
                              title=dict(text="By Category", font=dict(size=16, color='#00d9ff'), x=0.5),
                              xaxis=dict(tickfont=dict(color='#4a6a8a'), gridcolor='rgba(0,217,255,0.06)'),
                              yaxis=dict(tickfont=dict(color='#c8d6e5', size=9), autorange='reversed'),
                              legend=dict(font=dict(size=10, color='#c8d6e5'), bgcolor=_bg,
                                          orientation='h', x=0.5, xanchor='center', y=-0.08))
        st.plotly_chart(fig_cat, use_container_width=True, key=f"chad_cat_{idx}")


def generate_fallback_response(question, error_msg=""):
    """Generate fallback response when Bedrock is unavailable"""
    # Check if it's a Bedrock configuration issue
    if "Bedrock" in error_msg or "credentials" in error_msg.lower():
        bedrock_help = f"""
⚠️ **AWS Bedrock Not Available**

{error_msg}

In the meantime, here's some general guidance:

"""
    else:
        bedrock_help = ""
    
    # Keyword-based fallback responses
    fallback_responses = {
        "active directory": """**Active Directory Security Best Practices:**

1. **Privileged Access Management**: Implement a tiered admin model (Tier 0/1/2) to protect domain admin credentials
2. **Password Policy**: Enforce 14+ character passwords with complexity requirements
3. **Service Accounts**: Use Group Managed Service Accounts (gMSA) where possible
4. **AdminSDHolder**: Monitor and protect this critical container
5. **LDAP Signing**: Require LDAP signing and channel binding
6. **Kerberos**: Enable AES encryption, disable RC4
7. **Audit Policies**: Enable advanced audit policies for logon events and directory service access
8. **Protected Users Group**: Add sensitive accounts to this security group
9. **LAPS**: Deploy Local Administrator Password Solution
10. **Regular Reviews**: Conduct quarterly access reviews for privileged groups""",
        
        "network segmentation": """**Network Segmentation Implementation Guide:**

1. **Identify Critical Assets**: Map your crown jewels and their data flows
2. **Define Security Zones**: Create zones based on trust levels (DMZ, Internal, Restricted, PCI, etc.)
3. **Implement VLANs**: Use 802.1Q VLANs to logically separate traffic
4. **Deploy Firewalls**: Place next-gen firewalls between zones with explicit allow rules
5. **Microsegmentation**: Consider software-defined segmentation for east-west traffic
6. **Zero Trust**: Implement "never trust, always verify" between segments
7. **Jump Servers**: Use bastion hosts for administrative access to secure zones
8. **Network Access Control**: Deploy 802.1X for port-based authentication
9. **Monitor Traffic**: Implement IDS/IPS at segment boundaries
10. **Regular Testing**: Conduct periodic penetration tests to validate segmentation""",
        
        "endpoint hardening": """**Endpoint Hardening Checklist:**

1. **OS Hardening**: Apply CIS benchmarks or DISA STIGs
2. **Patch Management**: Automated patching within 14 days for critical vulnerabilities
3. **EDR/XDR**: Deploy endpoint detection and response on all endpoints
4. **Application Control**: Implement allowlisting (AppLocker, WDAC)
5. **Local Admin Rights**: Remove local admin rights, use PAM for elevation
6. **Disk Encryption**: Enable BitLocker with TPM + PIN
7. **USB Controls**: Restrict removable media via GPO
8. **Host Firewall**: Enable Windows Defender Firewall with strict rules
9. **PowerShell**: Enable constrained language mode and script block logging
10. **Credential Guard**: Enable Credential Guard on Windows 10/11 Enterprise"""
    }
    
    question_lower = question.lower()
    
    if "active directory" in question_lower or "ad " in question_lower:
        return bedrock_help + fallback_responses["active directory"]
    elif "network" in question_lower or "segment" in question_lower:
        return bedrock_help + fallback_responses["network segmentation"]
    elif "endpoint" in question_lower or "hardening" in question_lower:
        return bedrock_help + fallback_responses["endpoint hardening"]
    else:
        return bedrock_help + f"""I can help you with on-premise security topics including:

- **Active Directory Security**: Domain controller hardening, GPO security, privileged access
- **Network Infrastructure**: Segmentation, firewall rules, IDS/IPS configuration
- **Endpoint Security**: Hardening, patching, EDR deployment
- **Server Security**: Windows/Linux hardening, database security
- **Physical Security**: Access controls, surveillance, environmental
- **Data Protection**: Encryption, DLP, backup strategies
- **Identity Management**: MFA, PAM, access reviews
- **Monitoring**: SIEM, logging, threat detection

Please ask a more specific question about any of these areas!"""


