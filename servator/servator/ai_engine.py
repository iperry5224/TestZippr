"""
Servator AI Engine — LLM-powered insights for retail loss prevention.

Uses AWS Bedrock (Claude, Llama, Titan) for:
- Recommended actions from operational context
- Event summaries (natural language)
- SCO vision analysis (image/video frame)

Falls back to rule-based logic when Bedrock is unavailable.
"""
import json
import base64
from typing import Optional

try:
    import boto3
    _HAS_BOTO = True
except ImportError:
    _HAS_BOTO = False

_MODELS = [
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "meta.llama3-8b-instruct-v1:0",
    "amazon.titan-text-express-v1",
]

_VISION_MODELS = [
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
]


def _call_ai(prompt: str, max_tokens: int = 2048, temperature: float = 0.4) -> Optional[str]:
    """Single-turn Bedrock call with model fallback."""
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


def _call_vision_ai(image_bytes: bytes, prompt: str, image_format: str = "jpeg") -> Optional[str]:
    """Multimodal Bedrock call for image analysis. Claude 3.x supports vision."""
    if not _HAS_BOTO:
        return None
    try:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        content = [
            {"image": {"format": image_format, "source": {"bytes": image_bytes}}},
            {"text": prompt},
        ]
        for model_id in _VISION_MODELS:
            try:
                resp = client.converse(
                    modelId=model_id,
                    messages=[{"role": "user", "content": content}],
                    inferenceConfig={"maxTokens": 1024, "temperature": 0.3},
                )
                return resp["output"]["message"]["content"][0]["text"]
            except Exception:
                continue
    except Exception:
        pass
    return None


# =====================================================================
# 1. RECOMMENDED ACTIONS (Phase 1)
# =====================================================================
def ai_recommend_actions(
    events: list,
    risk_data: dict,
    store: str,
    date_range: str,
) -> list[dict]:
    """
    Generate AI-powered recommended actions from operational context.
    Returns list of {"action": str, "reason": str}.
    """
    context = {
        "store": store,
        "date_range": date_range,
        "events": events[:15],
        "risk_summary": risk_data,
    }
    prompt = f"""You are Servator AI, an operational intelligence assistant for retail loss prevention.

Context:
- Store: {store}
- Time range: {date_range}
- Recent operational events: {json.dumps(events[:15], indent=2)}
- Risk summary: {json.dumps(risk_data, indent=2)}

Generate 3-5 recommended actions for the loss prevention team. Use neutral, professional language.
Focus on: staffing alignment, high-risk areas, process exceptions, inventory checks, SCO review.
Each action should be actionable and specific (e.g., "Consider visibility at Aisle 12 during 6-8 PM").
Do NOT use accusatory language. Frame as "operational variance" or "process exception" not "theft".

Return a JSON array: [{{"action": "...", "reason": "..."}}]
Return ONLY valid JSON array. No markdown, no explanation."""

    result = _call_ai(prompt, max_tokens=1024)
    if result:
        try:
            start = result.find("[")
            end = result.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass

    # Fallback — rule-based actions
    actions = []
    if events:
        actions.append({
            "action": "Review recent operational events in Command Center",
            "reason": f"{len(events)} events in selected period. Prioritize SCO and shelf activity.",
        })
    if risk_data.get("high_risk_categories"):
        cat = risk_data["high_risk_categories"][0] if risk_data["high_risk_categories"] else "high-shrink"
        actions.append({
            "action": f"Inventory check recommended for {cat}",
            "reason": "Predictive risk score elevated. No recent physical count.",
        })
    actions.append({
        "action": "Staffing alignment: review peak hours in Analytics tab",
        "reason": "Historical patterns suggest optimal LP visibility during evening shift.",
    })
    return actions[:5]


# =====================================================================
# 2. EVENT SUMMARIES (Phase 1)
# =====================================================================
def ai_summarize_events(events: list, store: str) -> Optional[str]:
    """Generate natural language executive summary of operational events."""
    if not events:
        return None
    prompt = f"""You are Servator AI. Summarize these operational events for the loss prevention team.

Store: {store}
Events: {json.dumps(events[:20], indent=2)}

Write a 2-4 sentence executive summary. Use neutral language ("operational variance", "process exception").
Highlight: main focus areas, any patterns, recommended priority. Be concise."""

    return _call_ai(prompt, max_tokens=256)


# =====================================================================
# 3. SCO VISION ANALYSIS (Phase 2)
# =====================================================================
def ai_analyze_sco_image(image_bytes: bytes, image_format: str = "jpeg") -> dict:
    """
    Analyze SCO (self-checkout) camera image/frame for anomalies.
    Returns: {"anomalies": [...], "summary": str, "confidence": str}
    """
    prompt = """You are analyzing a self-checkout (SCO) camera image for a retail loss prevention system.

Describe what you see in terms of:
1. SCO LANE ACTIVITY: Is someone at the register? What are they doing? (scanning, bagging, waiting)
2. POTENTIAL ANOMALIES: Any concerning patterns? (e.g., bagging without visible scan, rapid item movement, obscured barcode area, multiple items in bagging area without scans)
3. CONFIDENCE: Low/Medium/High - how confident are you in any anomaly?
4. RECOMMENDATION: If anomaly detected, suggest next step (e.g., "Review transaction log", "Low confidence - possible scanner lag"). If no anomaly, say "No action needed."

Use neutral language. Do NOT accuse. Frame as "process variance" or "operational observation."
Return a JSON object: {"anomalies": ["..."], "summary": "1-2 sentence summary", "confidence": "low|medium|high", "recommendation": "..."}
Return ONLY valid JSON."""

    result = _call_vision_ai(image_bytes, prompt, image_format)
    if result:
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass

    return {
        "anomalies": [],
        "summary": "AI vision unavailable. Manual review recommended.",
        "confidence": "low",
        "recommendation": "Upload image when AI is configured (AWS Bedrock with vision model).",
    }


# =====================================================================
# 4. INVESTIGATION AGENT (Phase 4)
# =====================================================================
def ai_investigate_alert(
    alert_type: str,
    alert_desc: str,
    context: dict,
) -> dict:
    """
    Agentic investigation: synthesize context into investigation summary.
    Simulates pulling POS logs, video timestamps, inventory — returns AI synthesis.
    """
    prompt = f"""You are Servator Investigation Agent. An operational alert was raised.

Alert Type: {alert_type}
Description: {alert_desc}

Available context (simulated from store systems):
{json.dumps(context, indent=2)}

Synthesize an investigation summary:
1. LIKELY CAUSE: What might explain this? (process issue, training gap, equipment, normal variance)
2. EVIDENCE TO REVIEW: What would you check? (transaction logs, video timestamp, inventory)
3. RECOMMENDED ACTION: Next step for LP team
4. PRIORITY: Low/Medium/High

Return JSON: {{"likely_cause": "...", "evidence_to_review": ["..."], "recommended_action": "...", "priority": "..."}}
Return ONLY valid JSON."""

    result = _call_ai(prompt, max_tokens=512)
    if result:
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception:
            pass

    return {
        "likely_cause": "Insufficient context. Manual investigation required.",
        "evidence_to_review": ["Transaction logs", "Video footage", "Inventory records"],
        "recommended_action": "Review in Command Center; escalate if pattern repeats.",
        "priority": "medium",
    }


# =====================================================================
# 5. PRIORITIZATION AGENT (Phase 4)
# =====================================================================
def ai_prioritize_alerts(alerts: list) -> list[dict]:
    """
    Rank alerts by risk, staffing, ROI. Returns alerts with priority_score and rationale.
    """
    if not alerts:
        return []
    prompt = f"""You are Servator Prioritization Agent. Rank these operational alerts.

Alerts: {json.dumps(alerts[:15], indent=2)}

For each alert, assign:
- priority_score: 1-10 (10 = highest priority)
- rationale: One sentence why

Consider: severity, recency, category risk, staffing availability, potential loss.
Return JSON array: [{{"alert_id": "...", "priority_score": N, "rationale": "..."}}]
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

    # Fallback — simple recency + severity
    for i, a in enumerate(alerts):
        a["priority_score"] = 10 - i
        a["rationale"] = "Ranked by recency"
    return alerts
