# Servator AI Enhancement Phases

All four phases have been implemented.

---

## Phase 1: LLM-Powered Recommended Actions & Incident Summaries

**Servator:**
- **Generate AI Recommendations** — Button on dashboard. Uses AWS Bedrock (Claude) to generate 3–5 actionable recommendations from operational context (events, risk data, store, date range).
- **Generate AI Event Summary** — Button in Operational Events tab. Produces 2–4 sentence executive summary of recent events.

**SOPRA:**
- **Generate AI Executive Summary** — Button in each incident expander (Incident Correlation tool). Produces leadership-ready incident summary with root cause, impact, next steps.

**Requirements:** `boto3`, AWS credentials configured for Bedrock.

---

## Phase 2: Vision API for SCO Video Samples

**Servator → SCO Vision tab:**
- Upload JPEG/PNG image from self-checkout camera.
- **Analyze with AI Vision** — Sends image to Bedrock Claude 3.5 (multimodal). Returns:
  - Anomalies observed (bagging without scan, rapid movement, etc.)
  - Summary
  - Confidence (low/medium/high)
  - Recommendation (e.g., "Review transaction log", "No action needed")

**Requirements:** `boto3`, Bedrock with Claude 3.5 Sonnet or Haiku (vision-capable).

---

## Phase 3: Prophet + Anomaly Detection for Risk Analytics

**Servator → Analytics tab:**
- **Risk by Category** — Uses Isolation Forest (scikit-learn) for anomaly-adjusted risk scores.
- **Activity by Hour** — Time-series pattern (peak 6–8 PM, lunch). Prophet optional for forecasting.
- **Executive Summary metrics** — Computed from predictive models instead of static mock data.

**Requirements:** `scikit-learn`. Optional: `prophet` for time-series forecasting (comment in `requirements.txt`; fallback works without it).

---

## Phase 4: Agentic Workflows

**Servator → Investigation Agent tab:**
- Select alert type and enter description.
- **Run Investigation** — AI agent synthesizes context (simulated POS logs, video timestamp, inventory) into:
  - Likely cause
  - Evidence to review
  - Recommended action
  - Priority (Low/Medium/High)

**Prioritization Agent** — `ai_prioritize_alerts()` in `ai_engine.py` ranks alerts by risk, recency, staffing. Can be wired to a prioritization view.

---

## File Summary

| File | Purpose |
|------|---------|
| `servator/ai_engine.py` | LLM calls (Bedrock), vision, investigation, prioritization |
| `servator/analytics/predictive.py` | Prophet, Isolation Forest, risk/activity metrics |
| `servator/app/dashboard.py` | UI integration for all phases |
| `sopra/isso/ai_engine.py` | Added `ai_summarize_incident()` |
| `sopra/isso/incidents.py` | AI Executive Summary button per incident |

---

## Running Without AWS

If Bedrock is unavailable (no credentials, no access):
- **Recommended Actions** — Fallback to rule-based suggestions.
- **Event Summary** — No summary (button does nothing).
- **SCO Vision** — Returns "AI vision unavailable. Manual review recommended."
- **Investigation Agent** — Returns generic investigation template.

All features degrade gracefully.
