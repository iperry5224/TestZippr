"""Chad (AI) – AI assistant tab for compliance questions."""

import streamlit as st


def _init_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


KNOWLEDGE_BASE = {
    "nist 800-171": (
        "NIST SP 800-171 defines requirements for protecting Controlled Unclassified "
        "Information (CUI) in non-federal systems and organizations. It contains 14 "
        "families of security requirements derived from NIST SP 800-53."
    ),
    "nist 800-53": (
        "NIST SP 800-53 provides a catalog of security and privacy controls for "
        "information systems and organizations. Rev 5 includes over 1,000 controls "
        "organized into 20 families."
    ),
    "cmmc": (
        "The Cybersecurity Maturity Model Certification (CMMC) is a unified standard "
        "for implementing cybersecurity across the Defense Industrial Base. CMMC 2.0 "
        "has three levels aligning with NIST 800-171."
    ),
    "ssp": (
        "A System Security Plan (SSP) describes the security controls in place for an "
        "information system. It documents the system boundary, environment, "
        "interconnections, and how each applicable control is implemented."
    ),
    "poam": (
        "A Plan of Action and Milestones (POA&M) documents weaknesses found during "
        "assessment, planned corrective actions, milestones, and responsible parties."
    ),
    "risk assessment": (
        "Risk assessment identifies threats and vulnerabilities, evaluates the "
        "likelihood and impact of exploitation, and determines risk levels. NIST "
        "SP 800-30 provides guidance for conducting risk assessments."
    ),
    "access control": (
        "Access Control (AC) limits system access to authorized users, processes, "
        "and devices. Key controls include least privilege, separation of duties, "
        "unsuccessful logon attempts, and session management."
    ),
    "incident response": (
        "Incident Response (IR) establishes an operational capability for handling "
        "security incidents. This includes preparation, detection, analysis, "
        "containment, eradication, and recovery."
    ),
    "encryption": (
        "Encryption protects data confidentiality. FIPS 140-validated cryptographic "
        "modules should be used. CUI in transit must be encrypted with TLS 1.2+ or "
        "equivalent, and CUI at rest should use AES-256 or equivalent."
    ),
    "aws security hub": (
        "AWS Security Hub provides a comprehensive view of security posture across "
        "AWS accounts. It aggregates findings from services like GuardDuty, Inspector, "
        "and Macie, and checks against frameworks like CIS Benchmarks and NIST 800-53."
    ),
}


def _get_response(user_msg: str) -> str:
    lower = user_msg.lower()
    for topic, answer in KNOWLEDGE_BASE.items():
        if topic in lower:
            return answer

    if any(kw in lower for kw in ["help", "what can you do", "hi", "hello"]):
        return (
            "Hi! I'm Chad, your compliance AI assistant. I can help with questions "
            "about NIST 800-171, NIST 800-53, CMMC, SSPs, POA&Ms, risk assessments, "
            "encryption requirements, and AWS Security Hub. Ask me anything!"
        )

    return (
        "I'm not sure about that specific topic yet. Try asking about NIST 800-171, "
        "NIST 800-53, CMMC, SSP, POA&M, risk assessment, access control, incident "
        "response, encryption, or AWS Security Hub."
    )


def render_chad_ai():
    _init_state()
    st.header("Chad – AI Compliance Assistant")
    st.markdown(
        "Ask Chad about NIST frameworks, compliance requirements, "
        "and security best practices."
    )

    for msg in st.session_state.chat_history:
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask Chad a compliance question…")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        response = _get_response(user_input)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
