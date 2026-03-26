# SAELAR & SOPRA — Success Criteria & Metrics

**Purpose:** Measurable success criteria for adoption and effectiveness of SAELAR and SOPRA in the customer environment  
**Prepared for:** Customer engagement  
**Version:** 1.0  
**Date:** March 2026

---

## Overview

This document defines success criteria (metrics) to evaluate the value and effectiveness of SAELAR and SOPRA. Metrics are organized by platform, timeframe, and stakeholder (ISSO, Security Team, Management).

---

## SAELAR Success Criteria

### 1. Assessment Efficiency

| Metric | Definition | Target | Baseline (Manual) | Measurement |
|--------|------------|--------|-------------------|-------------|
| **Time to complete full NIST 800-53 assessment** | Hours from assessment initiation to completion of all selected control families | ≤ 4 hours | 40–80 hours (manual checklist) | Track start/end timestamps per assessment run |
| **Controls assessed per hour** | Number of controls evaluated per person-hour | ≥ 50 controls/hour | ~5–10 (manual) | (Controls completed ÷ person-hours) |
| **Assessment cycle frequency** | How often a full or partial assessment is run | Monthly or per change event | Quarterly (typical manual cadence) | Count assessments per quarter |
| **Time to first results** | Minutes from "Run Assessment" to first control results displayed | ≤ 5 minutes | N/A (manual is incremental) | Stopwatch or log timestamp |

### 2. Coverage & Completeness

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **Control family coverage** | % of 20 NIST families assessed (vs. skipped) | 100% of selected families | (Families run ÷ Families selected) × 100 |
| **Real-time data freshness** | Age of AWS data at assessment time | < 1 hour | SAELAR uses live APIs; document "last run" timestamp |
| **Assessment completion rate** | % of started assessments completed without error | ≥ 95% | (Completed ÷ Started) × 100 |

### 3. Risk & Remediation

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **Time to identify failed controls** | Minutes from assessment run to list of failed controls | ≤ 10 minutes | Timestamp of assessment completion |
| **Risk score availability** | Time from assessment to quantitative risk score | Immediate (same run) | Built-in; verify risk calculator populates |
| **AI remediation suggestions used** | % of failed findings where Chad AI suggestion was viewed or applied | Track adoption | Optional: analytics or survey |
| **Mean time to remediation (MTTR) awareness** | Whether MTTR can be tracked per finding | Supported | SAELAR provides POA&M; link to tracking |

### 4. Documentation & Audit Readiness

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **Time to generate SSP section** | Hours to produce assessable SSP content for 200 controls | ≤ 2 hours (with AI) | 200–400 hours manual | Track from "Generate SSP" to export |
| **Time to generate POA&M** | Minutes to produce POA&M entries for N failed findings | ≤ 30 minutes | 4–6 hours manual | Track from "Generate POA&M" to export |
| **Document export success rate** | % of export attempts (SSP, POA&M, evidence) that succeed | ≥ 99% | (Successful exports ÷ Attempted) × 100 |
| **Evidence attachment rate** | % of assessed controls with at least one evidence artifact | Track improvement | (Controls with evidence ÷ Assessed) × 100 |

### 5. Operational

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **Platform availability** | % uptime (excluding planned maintenance) | ≥ 99% | Uptime monitoring, health checks |
| **Assessment run success rate** | % of assessment runs that complete without fatal error | ≥ 95% | Log analysis |
| **User adoption** | Number of distinct users running assessments per month | Track growth | Auth/session logs or survey |

---

## SOPRA Success Criteria

### 1. ISSO Time Savings

| Metric | Definition | Target | Baseline (Manual) | Measurement |
|--------|------------|--------|-------------------|-------------|
| **Hours saved per ATO cycle** | Reduction in manual hours vs. manual process | ≥ 250 hours | ~400–600 hours manual | Time-tracking, survey, or estimated from artifact counts |
| **POA&M entry generation time** | Minutes to generate N POA&M entries via AI | ≤ 1 min per 10 entries | 3–5 min per entry manual | Time from click to export |
| **Risk acceptance draft time** | Minutes to generate one risk acceptance justification | ≤ 2 minutes | 15–30 min manual | Time from click to draft ready |
| **SSP narrative generation time** | Hours to generate 200 control narratives | ≤ 1 hour | 200–400 hours manual | Time from "Generate SSP" to review |

### 2. AI Feature Adoption

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **AI artifacts generated per cycle** | Count of POA&Ms, risk acceptances, SSP narratives, etc. generated by AI | Track per ATO cycle | Sum of AI-generated outputs (tagged with 🤖) |
| **AI feature usage rate** | % of users who use ≥ 1 AI feature per month | ≥ 80% | (Users with AI usage ÷ Total users) × 100 |
| **AI fallback rate** | % of AI requests that fall back to template (Bedrock unavailable) | ≤ 5% | Log Bedrock errors vs. successful invocations |
| **Human review rate** | % of AI outputs reviewed before use | 100% (policy) | Audit/training; not automated |

### 3. Audit & Compliance Readiness

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **Evidence sufficiency score** | % of controls with sufficient evidence (Yes vs. Partial/No) | Improve quarter over quarter | SOPRA evidence analysis feature |
| **Approval package readiness** | Time from "request approval" to package ready for AO | ≤ 1 day | Track request to submission |
| **Crosswalk query resolution time** | Minutes to answer "Which NIST families have most failures?" type questions | ≤ 1 minute | Manual: 15–30 min | Time from query to answer |
| **STIG/import mapping time** | Hours to map external findings to SOPRA controls | ≤ 1 hour per import | 2–4 hours manual | Time from import to mapping complete |

### 4. Workflow Efficiency

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **Control inheritance classification time** | Hours to classify 200 controls | ≤ 1 hour | 4–6 hours manual | Time from click to completion |
| **Incident-to-finding correlation time** | Minutes per incident to correlate to controls | ≤ 5 minutes | 30–60 min manual | Time from incident log to correlation |
| **Schedule optimization application** | One-click apply of AI-recommended assessment schedules | Supported | Feature usage count |
| **Ticket generation time** | Minutes to generate N ServiceNow/Jira tickets from findings | ≤ 5 min per 20 findings | 2–4 hours manual | Time from bulk generate to export |

### 5. Quality & Consistency

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **AI output review edits** | % of AI-generated text used as-is vs. edited | Track; lower edits = higher quality | Sampling of reviewed outputs |
| **Consistency of language** | Subjective: AI outputs use formal RMF language | Auditor feedback | Survey or audit feedback |
| **Audit finding rate** | # of audit findings related to SOPRA-generated artifacts | 0 (no new findings) | Post-audit review |

---

## Combined Platform Metrics

### 1. End-to-End ATO Cycle

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **Total ATO prep time (assessment + documentation)** | Hours from assessment start to ATO package ready | ≥ 50% reduction vs. baseline | Compare to pre-platform baseline |
| **First-time audit readiness** | % of artifacts deemed "audit ready" on first submission | ≥ 90% | Auditor or internal QA review |
| **Rework rate** | % of artifacts requiring significant revision post-review | ≤ 10% | (Artifacts revised ÷ Total submitted) × 100 |

### 2. ROI & Value

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **FTE equivalent freed** | Person-hours saved ÷ 2,080 (annual FTE hours) | ≥ 2 FTE per ATO cycle | Hours saved ÷ 2,080 |
| **Cost avoidance** | (Hours saved × hourly rate) − platform cost | Positive ROI | Financial tracking |
| **Time to value** | Weeks from go-live to first measurable time savings | ≤ 4 weeks | Project timeline |

### 3. User Satisfaction

| Metric | Definition | Target | Measurement |
|--------|------------|--------|--------------|
| **User satisfaction (NPS or survey)** | Would users recommend SAELAR/SOPRA to a peer? | NPS ≥ 30 or satisfaction ≥ 4/5 | Quarterly survey |
| **Ease of use** | Perceived difficulty of running assessment or generating artifacts | "Easy" or "Very easy" | Survey |
| **Feature utilization** | % of available features used in first 90 days | ≥ 60% | Feature usage analytics |

---

## Implementation Notes

### Baseline Collection

- **Before go-live:** Capture current metrics (manual assessment time, POA&M time, SSP time, etc.) via time-tracking or survey.
- **Establish baseline** for "Hours per ATO cycle" and "Controls assessed per hour."

### Reporting Cadence

| Stakeholder | Cadence | Metrics Focus |
|-------------|---------|---------------|
| **ISSO/Operational** | Weekly or per assessment | Time to complete, controls assessed, AI usage |
| **Security Lead** | Monthly | Risk scores, coverage, remediation velocity |
| **Management** | Quarterly | ROI, FTE freed, satisfaction, audit readiness |
| **Customer/Steering** | Per ATO cycle or quarterly | Full dashboard; ROI; audit outcomes |

### Data Collection Methods

1. **Platform logs** — Assessment run times, export success, AI invocation counts
2. **Time-tracking** — Optional: ISSOs log hours pre/post for comparison
3. **Surveys** — Quarterly satisfaction, ease of use, adoption
4. **Audit feedback** — Post-ATO: rework rate, first-time readiness

---

## Summary Table (Quick Reference)

| Category | SAELAR Key Metrics | SOPRA Key Metrics |
|----------|--------------------|-------------------|
| **Efficiency** | ≤ 4 hrs full assessment; ≥ 50 controls/hr | ≥ 250 hrs saved per ATO; ≤ 30 min POA&M |
| **Coverage** | 100% of selected families; < 1 hr data freshness | 200 controls; evidence sufficiency trend |
| **Documentation** | ≤ 2 hrs SSP; ≤ 30 min POA&M | AI artifacts per cycle; 100% review |
| **Quality** | ≥ 95% run success; ≥ 99% export success | ≤ 5% AI fallback; 0 audit findings from platform |
| **Adoption** | Users per month; assessment frequency | ≥ 80% AI feature usage; NPS ≥ 30 |
| **ROI** | Cost avoidance; FTE freed | ≥ 2 FTE per ATO; positive ROI |

---

*For questions or to customize metrics for your environment, contact the SAELAR/SOPRA development team.*
