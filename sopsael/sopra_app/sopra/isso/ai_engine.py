"""
SOPRA ISSO AI Engine — Shared AI helper for all ISSO Toolkit tools.
Provides specialized prompt templates and Bedrock calls for each tool.
Falls back to deterministic templates when Bedrock is unavailable.
"""
import json
import os
from datetime import datetime, timedelta

try:
    import boto3
    _HAS_BOTO = True
except ImportError:
    _HAS_BOTO = False

# Claude removed per policy
_MODELS = [
    "nvidia.nemotron-nano-12b-v2",
    "meta.llama3-8b-instruct-v1:0",
    "amazon.titan-text-express-v1",
    "amazon.titan-text-lite-v1",
    "mistral.mistral-7b-instruct-v0:2",
]


def _call_ai(prompt, max_tokens=2048, temperature=0.4):
    """Single-turn Bedrock call with model fallback. Returns text or None."""
    if not _HAS_BOTO:
        return None
    try:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        for model_id in _MODELS:
            try:
                resp = client.converse(
                    modelId=model_id,
                    messages=[{"role": "user", "content": [{"text": prompt}]}],
                    inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
                )
                return resp["output"]["message"]["content"][0]["text"]
            except Exception:
                continue
    except Exception:
        pass
    return None


# =====================================================================
# 1. POA&M AUTO-GENERATION
# =====================================================================
def ai_generate_poam_entries(failed_findings):
    """Generate POA&M entries from failed findings."""
    if not failed_findings:
        return []

    summary = json.dumps([{
        "id": f.get("control_id"), "name": f.get("control_name"),
        "severity": f.get("severity"), "category": f.get("category"),
        "evidence": f.get("evidence", "")[:100]
    } for f in failed_findings[:30]], indent=2)

    prompt = f"""You are a cybersecurity POA&M specialist. Generate POA&M (Plan of Action & Milestones) entries for these failed security controls.

Failed findings:
{summary}

For each finding, generate a JSON array entry with:
- "control_id": the control ID
- "finding": concise description of the weakness
- "milestone_1": first remediation milestone (action + timeframe)
- "milestone_2": second milestone
- "milestone_3": third milestone (verification)
- "responsible_party": suggested role (e.g., "System Administrator", "Network Engineer")
- "estimated_days": number of days to complete remediation
- "risk_if_delayed": one sentence on risk of inaction

Return ONLY valid JSON array. No markdown, no explanation."""

    result = _call_ai(prompt, max_tokens=4096)
    if result:
        try:
            # Extract JSON from response
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass

    # Fallback — generate deterministic entries
    entries = []
    sev_days = {"Critical": 14, "High": 30, "Medium": 60, "Low": 90}
    roles = {
        "Active Directory": "AD Administrator",
        "Network": "Network Engineer",
        "Endpoint": "Desktop Engineering",
        "Server": "Systems Administrator",
        "Physical": "Facilities Manager",
        "Data": "Data Protection Officer",
        "Identity": "IAM Team Lead",
        "Monitoring": "SOC Manager",
        "Vulnerability": "Vulnerability Management Lead",
        "Configuration": "Configuration Manager",
        "Incident": "IR Team Lead",
        "Contingency": "BC/DR Coordinator",
        "Security Awareness": "Training Coordinator",
        "Application": "AppSec Engineer",
        "Supply Chain": "Vendor Risk Manager",
        "Governance": "ISSO/ISSM",
        "Wireless": "Network Engineer",
        "Virtualization": "Virtualization Engineer",
        "Email": "Messaging Administrator",
        "Cryptographic": "PKI/Crypto Engineer",
    }
    for f in failed_findings:
        sev = f.get("severity", "Medium")
        cat = f.get("category", "")
        role = "System Administrator"
        for key, val in roles.items():
            if key.lower() in cat.lower():
                role = val
                break
        days = sev_days.get(sev, 60)
        entries.append({
            "control_id": f.get("control_id", ""),
            "finding": f"{f.get('control_name', 'Unknown')} — {sev} severity finding requiring remediation",
            "milestone_1": f"Assess current state and develop remediation plan ({days//3} days)",
            "milestone_2": f"Implement remediation actions ({days*2//3} days)",
            "milestone_3": f"Verify fix and close finding ({days} days)",
            "responsible_party": role,
            "estimated_days": days,
            "risk_if_delayed": f"Continued exposure to {sev.lower()}-severity risk in {cat}",
        })
    return entries


# =====================================================================
# 2. RISK ACCEPTANCE JUSTIFICATION
# =====================================================================
def ai_draft_risk_acceptance(control_id, control_name, severity, category, evidence=""):
    """Draft a risk acceptance justification with compensating controls."""
    prompt = f"""You are an ISSO drafting a risk acceptance for an authorizing official.

Control: {control_id} — {control_name}
Category: {category}
Severity: {severity}
Evidence: {evidence}

Generate:
1. OPERATIONAL JUSTIFICATION (2-3 sentences explaining why the risk is acceptable)
2. COMPENSATING CONTROLS (3-5 specific compensating controls that mitigate the residual risk)
3. RESIDUAL RISK ASSESSMENT (1-2 sentences on remaining risk after compensating controls)
4. RECOMMENDED EXPIRY (when this acceptance should be re-evaluated)

Be specific, professional, and auditor-ready. Use formal RMF language."""

    result = _call_ai(prompt, max_tokens=1024)
    if result:
        return result

    # Fallback
    return f"""**OPERATIONAL JUSTIFICATION:**
The implementation of {control_name} ({control_id}) cannot be fully achieved at this time due to operational constraints in the {category} domain. The current system architecture and mission requirements necessitate a temporary risk acceptance while alternative solutions are evaluated.

**COMPENSATING CONTROLS:**
1. Enhanced monitoring and logging of all activities related to {control_id}
2. Quarterly manual review of {category.lower()} configurations by the ISSO
3. Implementation of additional network segmentation to limit exposure
4. Increased audit frequency for related control families
5. Documented standard operating procedures for manual verification

**RESIDUAL RISK ASSESSMENT:**
With compensating controls in place, the residual risk is reduced from {severity} to Medium-Low. The compensating controls provide reasonable assurance that the security objective is partially met through alternative means.

**RECOMMENDED EXPIRY:** 180 days from approval date. Re-evaluate when system upgrade is scheduled."""


# =====================================================================
# 3. EVIDENCE SUFFICIENCY ANALYSIS
# =====================================================================
def ai_analyze_evidence(control_id, control_name, evidence_type, description, filename=""):
    """Analyze if uploaded evidence is sufficient for the mapped control."""
    prompt = f"""You are a security auditor reviewing evidence submitted for a control assessment.

Control: {control_id} — {control_name}
Evidence Type: {evidence_type}
Evidence Description: {description}
Filename: {filename}

Assess:
1. SUFFICIENCY: Is this evidence type appropriate for this control? (Yes/Partial/No)
2. COMPLETENESS: What additional evidence would strengthen the assessment?
3. RECOMMENDATIONS: Specific suggestions for improvement (2-3 items)

Be concise and practical."""

    result = _call_ai(prompt, max_tokens=512)
    if result:
        return result

    return f"""**SUFFICIENCY:** Partial — {evidence_type} provides supporting evidence for {control_id} but may not be sufficient as standalone proof.

**COMPLETENESS:** Consider also providing:
- Configuration screenshots showing current settings
- Policy documentation referencing {control_name}
- Automated scan results validating the control implementation

**RECOMMENDATIONS:**
1. Include timestamps in evidence to prove currency
2. Add approver signature or attestation
3. Cross-reference with related control evidence for consistency"""


# =====================================================================
# 4. CONTROL INHERITANCE CLASSIFICATION
# =====================================================================
def ai_classify_inheritance(controls_data):
    """Auto-classify controls as Common/Hybrid/System-Specific."""
    summary = json.dumps([{
        "id": c.get("control_id", c.get("id", "")),
        "name": c.get("control_name", c.get("name", "")),
        "family": c.get("family", ""),
        "category": c.get("category", ""),
    } for c in controls_data[:50]], indent=2)

    prompt = f"""You are an ISSO classifying controls for a System Security Plan.

Controls:
{summary}

For each control, classify as:
- "Common" — provided by the organization/cloud/shared infrastructure (e.g., physical security, org policy)
- "Hybrid" — partially inherited, partially system-specific (e.g., access control with org policy + system config)
- "System-Specific" — unique to this system (e.g., application-level controls)

Also suggest the inheritance provider (e.g., "Organization", "Cloud Provider", "Data Center", "System Owner").

Return a JSON array with objects: {{"id": "...", "type": "...", "provider": "...", "rationale": "..."}}
Return ONLY valid JSON array."""

    result = _call_ai(prompt, max_tokens=4096)
    if result:
        try:
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass

    # Fallback — rule-based classification
    classifications = []
    common_keywords = ["physical", "policy", "awareness", "training", "governance", "personnel", "planning"]
    hybrid_keywords = ["access", "identity", "monitoring", "configuration", "contingency", "incident"]

    for c in controls_data:
        cat = (c.get("category", "") + " " + c.get("family", "")).lower()
        name = c.get("control_name", c.get("name", "")).lower()
        cid = c.get("control_id", c.get("id", ""))

        if any(kw in cat or kw in name for kw in common_keywords):
            ctype, provider = "Common", "Organization"
        elif any(kw in cat or kw in name for kw in hybrid_keywords):
            ctype, provider = "Hybrid", "Organization + System Owner"
        else:
            ctype, provider = "System-Specific", "System Owner"

        classifications.append({
            "id": cid, "type": ctype, "provider": provider,
            "rationale": f"Classified based on {c.get('category', 'Unknown')} domain characteristics"
        })
    return classifications


# =====================================================================
# 5. STIG-TO-SOPRA AUTO-MAPPING
# =====================================================================
def ai_map_stig_to_sopra(stig_findings, sopra_controls_summary):
    """Map imported STIG findings to SOPRA control IDs using AI."""
    stig_summary = json.dumps(stig_findings[:20], indent=2)

    prompt = f"""You are a security assessment expert. Map these STIG/benchmark findings to the most relevant SOPRA controls.

STIG Findings:
{stig_summary}

Available SOPRA Controls (ID: Name):
{sopra_controls_summary}

For each STIG finding, suggest the best SOPRA control ID match.
Return a JSON array: [{{"stig_id": "...", "sopra_id": "...", "confidence": "high/medium/low", "reason": "..."}}]
Return ONLY valid JSON array."""

    result = _call_ai(prompt, max_tokens=2048)
    if result:
        try:
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass
    return []


# =====================================================================
# 6. INCIDENT-TO-FINDING CORRELATION
# =====================================================================
def ai_correlate_incident(incident_title, incident_desc, failed_findings):
    """Suggest which failed controls relate to an incident."""
    findings_summary = "\n".join([
        f"- {f.get('control_id')}: {f.get('control_name')} ({f.get('category')})"
        for f in failed_findings[:40]
    ])

    prompt = f"""You are a SOC analyst correlating a security incident to failed assessment controls.

Incident: {incident_title}
Description: {incident_desc}

Failed Controls:
{findings_summary}

Which failed controls are most likely related to this incident?
Return a JSON array of objects: [{{"control_id": "...", "relevance": "high/medium/low", "explanation": "..."}}]
Only include controls with medium or high relevance.
Return ONLY valid JSON array."""

    result = _call_ai(prompt, max_tokens=1024)
    if result:
        try:
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass
    return []


# =====================================================================
# 7. NATURAL LANGUAGE CROSSWALK QUERY
# =====================================================================
def ai_crosswalk_query(question, nist_index_summary, cis_index_summary):
    """Answer natural language questions about control mappings."""
    prompt = f"""You are a NIST 800-53 and CIS Controls expert. Answer this question using the provided mapping data.

Question: {question}

NIST 800-53 Mappings (SOPRA controls → NIST):
{nist_index_summary}

CIS v8 Mappings (SOPRA controls → CIS):
{cis_index_summary}

Provide a clear, concise answer referencing specific control IDs and mapping relationships. Use markdown formatting."""

    result = _call_ai(prompt, max_tokens=1024)
    if result:
        return result
    return "AI is unavailable. Please use the interactive crosswalk tables to explore control mappings."


# =====================================================================
# 8. SSP CONTROL IMPLEMENTATION NARRATIVES
# =====================================================================
def ai_generate_ssp_narrative(control_id, control_name, family, category, status, evidence=""):
    """Generate SSP implementation narrative for a control."""
    prompt = f"""You are a cybersecurity author writing System Security Plan (SSP) control implementation descriptions.

Control: {control_id} — {control_name}
Family: {family}
Category: {category}
Implementation Status: {status}
Assessment Evidence: {evidence}

Write a professional SSP control implementation description (150-250 words) that:
1. States the implementation status
2. Describes HOW the control is implemented (specific technologies, configurations, processes)
3. Identifies responsible parties
4. Notes any planned enhancements

Use formal RMF/ATO language suitable for federal SSP documentation."""

    result = _call_ai(prompt, max_tokens=512)
    if result:
        return result

    status_text = "fully implemented" if status == "Passed" else "not fully implemented and requires remediation"
    return f"""{control_name} ({control_id}) is {status_text} within the {category} domain.

The organization addresses this control through a combination of technical configurations, administrative policies, and operational procedures managed by the {category} team. {"The current implementation meets all assessment criteria as validated through automated scanning and manual review." if status == "Passed" else "A Plan of Action and Milestones (POA&M) has been created to track remediation activities. Compensating controls are in place to mitigate risk during the remediation period."}

Responsible parties include the Information System Security Officer (ISSO) for oversight and the system administration team for technical implementation. The control is reviewed as part of the organization's continuous monitoring program per the assessment schedule.

{"No enhancements are currently planned as the control meets all requirements." if status == "Passed" else "Planned enhancements include full implementation of all control requirements within the POA&M timeline."}"""


# =====================================================================
# 9. RISK-BASED ASSESSMENT FREQUENCY
# =====================================================================
def ai_recommend_schedule(category, current_frequency, failure_rate=0, severity_profile=""):
    """Recommend assessment frequency based on risk factors."""
    prompt = f"""You are a risk management specialist recommending assessment frequencies.

Category: {category}
Current Frequency: Every {current_frequency} days
Historical Failure Rate: {failure_rate}%
Severity Profile: {severity_profile}

Recommend:
1. Optimal assessment frequency (in days)
2. Rationale (2-3 sentences)
3. Risk factors considered

Be concise. Consider NIST SP 800-137 ISCM guidance."""

    result = _call_ai(prompt, max_tokens=512)
    if result:
        return result

    # Rule-based fallback
    if failure_rate > 50:
        freq = 30
        rationale = "High failure rate warrants monthly reassessment"
    elif failure_rate > 25:
        freq = 60
        rationale = "Moderate failure rate suggests bi-monthly reassessment"
    elif "Critical" in severity_profile or "High" in severity_profile:
        freq = 60
        rationale = "High-severity findings in this category recommend more frequent assessment"
    else:
        freq = 90
        rationale = "Standard quarterly assessment per NIST SP 800-137 ISCM guidance"

    return f"""**Recommended Frequency:** Every {freq} days

**Rationale:** {rationale}. The {category} category {"has a {:.0f}% failure rate which ".format(failure_rate) if failure_rate else ""}requires {"increased" if freq < int(current_frequency) else "standard"} monitoring cadence.

**Risk Factors:** Control criticality, historical compliance rate, threat landscape for {category.lower()} domain."""


# =====================================================================
# 10. INCIDENT NATURAL LANGUAGE SUMMARY (Phase 1)
# =====================================================================
def ai_summarize_incident(incident_title: str, incident_desc: str, linked_controls: list = None):
    """Generate natural language executive summary of an incident for reports."""
    linked = linked_controls or []
    linked_summary = "\n".join([f"- {c}" for c in linked[:10]]) if linked else "None linked"

    prompt = f"""You are an ISSO preparing an incident summary for leadership.

Incident: {incident_title}
Description: {incident_desc}

Linked Failed Controls:
{linked_summary}

Write a 3-5 sentence executive summary suitable for a status report. Include:
1. What happened (concise)
2. Likely root cause / contributing factors
3. Impact assessment
4. Recommended next steps

Use professional, non-alarmist language. No jargon."""

    result = _call_ai(prompt, max_tokens=512)
    if result:
        return result

    return f"""**Incident Summary:** {incident_title}

{incident_desc[:200]}{"..." if len(incident_desc) > 200 else ""}

**Linked Controls:** {len(linked)} control(s) may relate to this incident. Review correlation in Incident Correlation tool.

**Recommendation:** Document timeline, contain if needed, and update POA&M with any new findings."""


# =====================================================================
# 11. APPROVAL PACKAGE SUMMARY
# =====================================================================
def ai_draft_approval_summary(approval_type, item_reference, related_data=""):
    """Draft an approval package summary for AO review."""
    prompt = f"""You are an ISSO preparing an approval package summary for the Authorizing Official.

Approval Type: {approval_type}
Item Reference: {item_reference}
Related Data: {related_data}

Draft a concise approval summary (100-150 words) that:
1. States what is being approved
2. Summarizes the security posture / risk level
3. Notes any conditions or caveats
4. Recommends a decision

Use formal RMF language suitable for AO review."""

    result = _call_ai(prompt, max_tokens=512)
    if result:
        return result

    return f"""**APPROVAL SUMMARY — {approval_type}**

Reference: {item_reference}

This package requests {approval_type.lower()} authorization. The associated security controls have been assessed and documented per NIST SP 800-53 Rev 5 requirements. The current risk posture has been evaluated and is within acceptable organizational risk tolerance.

All supporting documentation including assessment results, POA&M items, and risk acceptance decisions are current and available for review. The ISSO recommends approval with standard continuous monitoring conditions.

**Recommendation:** Approve with standard conditions. Next review in 365 days or upon significant system change."""
