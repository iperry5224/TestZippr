# SOPRA AI Capabilities — Executive Briefing
### Automating the ISSO Workflow Through Artificial Intelligence
**Prepared by:** SOPRA Development Team
**Date:** February 9, 2026
**Classification:** Internal Use Only

---

## The Problem

Information System Security Officers (ISSOs) spend **60–70% of their time** on repetitive, document-heavy tasks: writing POA&M milestones, drafting risk acceptance justifications, classifying controls, mapping findings to frameworks, and preparing approval packages. These tasks are critical for Authority to Operate (ATO) compliance but are manual, error-prone, and consume bandwidth that should be spent on actual security operations.

For a system with 200 security controls across 20 assessment categories, an ISSO can expect:

| Manual Task | Estimated Manual Time | Frequency |
|---|---|---|
| Writing POA&M entries for failed findings | 3–5 min per finding | After every assessment |
| Drafting risk acceptance justifications | 15–30 min each | Per accepted risk |
| Classifying control inheritance (200 controls) | 4–6 hours | Per system boundary change |
| Mapping STIG imports to internal controls | 2–4 hours per scan | Monthly |
| Correlating incidents to failed controls | 30–60 min per incident | Per event |
| Writing SSP control narratives (200 controls) | 1–2 hours per control | Per ATO cycle |
| Analyzing evidence sufficiency | 10–15 min per artifact | Ongoing |
| Optimizing assessment schedules | 2–3 hours | Quarterly |
| Preparing approval package summaries | 20–30 min each | Per approval |
| Researching framework crosswalk questions | 15–30 min per query | Ongoing |

**Conservative estimate for a single ATO cycle: 400–600 hours of ISSO labor.**

---

## The Solution: SOPRA AI

SOPRA integrates **13 distinct AI capabilities** powered by AWS Bedrock large language models that automate the most time-consuming ISSO tasks while maintaining full human oversight and auditability.

Every AI feature:
- Operates with a **single button click**
- Produces **auditor-ready output** using formal RMF/ATO language
- Tags all AI-generated content with a **visible 🤖 badge** for transparency
- **Falls back to deterministic templates** when AI is unavailable — zero downtime
- Sends **only aggregate assessment data** to AI — no PII, no raw evidence, no classified content

---

## AI Feature Catalog

### 1. AI-Powered POA&M Generation

**What it does:** Analyzes all failed findings and auto-generates complete Plan of Action & Milestones entries with smart milestones, realistic due dates, role-specific responsible parties, and risk-if-delayed warnings.

**Before SOPRA AI:**
> ISSO manually writes each POA&M entry. For 80 failed findings, this takes 4–6 hours. Milestones are generic. Due dates are guesswork. Responsible parties default to "TBD."

**After SOPRA AI:**
> One click generates 80 POA&M entries in under 30 seconds. Each entry includes three phased milestones (assess → implement → verify), severity-calibrated due dates (Critical: 14 days, High: 30, Medium: 60, Low: 90), and category-aware responsible party assignments (e.g., "AD Administrator" for Active Directory findings, "Network Engineer" for network findings).

**Time saved per assessment cycle: 4–6 hours**

---

### 2. AI-Drafted Risk Acceptance Justifications

**What it does:** Generates complete, AO-ready risk acceptance packages including operational justifications, compensating controls, residual risk assessments, and recommended re-evaluation dates.

**Before SOPRA AI:**
> ISSO spends 15–30 minutes per risk acceptance drafting formal justification language, researching compensating controls, and determining appropriate expiry dates. Language quality varies by individual.

**After SOPRA AI:**
> One click produces a professional justification with 3–5 specific compensating controls tailored to the control domain, a residual risk assessment, and a recommended 180-day review date. ISSO reviews, edits if needed, and submits. Language is consistent and auditor-ready across all acceptances.

**Time saved per acceptance: 15–25 minutes**

---

### 3. AI Evidence Sufficiency Analysis

**What it does:** Reviews each uploaded evidence artifact against its mapped control and assesses whether the evidence is sufficient (Yes/Partial/No), what additional evidence would strengthen the assessment, and specific recommendations for improvement.

**Before SOPRA AI:**
> ISSO manually reviews each evidence artifact, cross-references it against the control requirements, and makes a subjective judgment. Gaps are often missed until audit time.

**After SOPRA AI:**
> Per-artifact analysis identifies sufficiency gaps before the auditor does. SOPRA also calculates overall evidence coverage metrics — how many assessed controls have attached evidence vs. how many have gaps — giving the ISSO a clear remediation target.

**Time saved per audit prep: 6–10 hours**

---

### 4. AI Control Inheritance Auto-Classification

**What it does:** Analyzes all 200 controls and classifies each as Inherited (from provider/organization), Common (enterprise-wide), or System-Specific, with provider attribution and rationale for each classification.

**Before SOPRA AI:**
> ISSO manually reviews each control, determines whether it's inherited from the cloud provider, shared across the organization, or unique to the system. For 200 controls, this takes 4–6 hours and requires deep knowledge of the system boundary.

**After SOPRA AI:**
> One click classifies all 200 controls in seconds. AI considers control name, family, and category to make intelligent classifications (e.g., physical security controls → Common/Organization, application-level controls → System-Specific/System Owner). ISSO reviews and adjusts outliers. Each classification includes a rationale note.

**Time saved per system boundary review: 4–6 hours**

---

### 5. AI STIG-to-SOPRA Auto-Mapping

**What it does:** When DISA STIG or CIS Benchmark scan results are imported, AI maps each external finding to the closest matching SOPRA control with confidence scores (High/Medium/Low) and mapping rationale.

**Before SOPRA AI:**
> ISSO manually reviews each STIG finding, searches the internal control library, and creates a manual mapping. For a 300-item STIG checklist, this takes 2–4 hours and is error-prone.

**After SOPRA AI:**
> AI analyzes finding titles and descriptions against SOPRA's 200-control library and produces confidence-scored mappings. The ISSO reviews high-confidence matches and focuses manual effort only on low-confidence items.

**Time saved per STIG import: 2–3 hours**

---

### 6. AI Incident-to-Finding NLP Correlation

**What it does:** When a security incident is logged, AI analyzes the incident description using natural language processing and suggests which failed assessment controls are most likely related, with relevance scores and explanations.

**Before SOPRA AI:**
> ISSO manually reads the incident report, mentally maps it to the control framework, and manually links findings. This requires deep institutional knowledge and is often incomplete.

**After SOPRA AI:**
> AI reads the incident description, identifies keywords and concepts, and correlates them to specific failed controls with High/Medium/Low relevance scores and plain-language explanations (e.g., "This unauthorized access incident relates to AD-003 because weak password policies were identified as a failed control"). ISSO accepts or adjusts suggestions.

**Time saved per incident: 20–40 minutes**

---

### 7. AI Natural Language Crosswalk Queries

**What it does:** Provides a conversational interface where the ISSO can ask plain-English questions about control mappings between SOPRA, NIST 800-53 Rev 5, and CIS Controls v8 — and get immediate, data-driven answers.

**Example queries:**
- "Which NIST families have the most failures?"
- "What CIS benchmarks cover access control?"
- "Show me all failed controls mapped to NIST SI family"
- "What is our weakest NIST control family?"

**Before SOPRA AI:**
> ISSO manually navigates spreadsheets, cross-references NIST and CIS documentation, and builds ad-hoc queries. Each research question takes 15–30 minutes.

**After SOPRA AI:**
> Type a question, get an answer in seconds. AI has full context of the bidirectional crosswalk data and live assessment results.

**Time saved per query: 15–25 minutes**

---

### 8. AI-Written SSP Control Implementation Narratives

**What it does:** Generates professional System Security Plan implementation descriptions for all 200 controls using formal RMF language. Narratives are included directly in the exported SSP Word document.

**Before SOPRA AI:**
> Writing SSP control narratives is the single most time-consuming ATO task. At 1–2 hours per control, 200 controls would take **200–400 hours** — often spread across multiple team members over weeks.

**After SOPRA AI:**
> One click generates all 200 narratives. Each narrative (150–250 words) includes implementation status, specific technologies and configurations, responsible parties, and planned enhancements. ISSO reviews and refines. The output is inserted directly into the downloadable SSP .docx document.

**Time saved per ATO cycle: 150–300+ hours**

---

### 9. AI Risk-Based Assessment Schedule Optimization

**What it does:** Analyzes failure rates and severity profiles for each assessment category and recommends optimal reassessment frequencies based on NIST SP 800-137 Information Security Continuous Monitoring (ISCM) guidance.

**Before SOPRA AI:**
> ISSO sets all categories to the same default (typically 90-day) schedule regardless of risk. High-risk categories are under-assessed; low-risk categories waste resources.

**After SOPRA AI:**
> AI recommends risk-proportionate schedules: categories with 50%+ failure rates get monthly assessment; categories with critical findings get 60-day cycles; stable categories get standard 90-day cycles. Each recommendation includes rationale and risk factors. ISSO can apply recommendations with one click.

**Time saved per quarterly review: 2–3 hours**

---

### 10. AI Approval Package Summary Drafting

**What it does:** Generates AO-ready approval package summaries for POA&M closures, risk acceptances, assessment completions, SSP approvals, and ATO recommendations. Pulls context from related ISSO data (linked POA&Ms, risk acceptances) to produce informed summaries.

**Before SOPRA AI:**
> ISSO manually drafts each approval summary, cross-references related documentation, and formats for AO review. Each package takes 20–30 minutes.

**After SOPRA AI:**
> AI drafts the summary with relevant context automatically pulled from the ISSO data store. Output includes what's being approved, security posture summary, conditions/caveats, and a recommendation. ISSO reviews and submits.

**Time saved per approval: 15–25 minutes**

---

### 11. AI Chat Assistant ("Chad") — Risk Analysis & Remediation

**What it does:** Full conversational AI security analyst that can:
- Calculate and visualize risk scores with interactive charts (pie, bar, gauge, radar)
- Generate complete PowerShell remediation scripts with pre-checks, post-checks, and rollback procedures
- Analyze attack chains across multiple failed controls
- Provide real-time security hardening advice
- Answer complex security questions with SOPRA assessment context

**Time saved: Replaces hours of manual research and script development per remediation task**

---

### 12. AI Remediation Plans & Attack Chain Detection

**What it does:** Generates detailed AI remediation plans for each failed finding, detects multi-control attack chain patterns, provides post-remediation validation scripts, and performs change impact analysis.

**Time saved per remediation cycle: 8–15 hours**

---

### 13. AI Automated Ticket Generation

**What it does:** Generates pre-filled ServiceNow or Jira tickets from failed findings with severity-mapped priority, detailed descriptions, and remediation steps. Supports bulk ticket generation for entire assessment cycles.

**Time saved per assessment: 2–4 hours**

---

## Total Impact Analysis

### Time Savings Per ATO Cycle

| AI Feature | Manual Time | AI-Assisted Time | Savings |
|---|---|---|---|
| POA&M Generation | 6 hours | 30 min (review) | **5.5 hours** |
| Risk Acceptance Drafting (10 items) | 5 hours | 1 hour (review) | **4 hours** |
| Evidence Sufficiency Review | 10 hours | 2 hours (review) | **8 hours** |
| Control Inheritance Classification | 6 hours | 1 hour (review) | **5 hours** |
| STIG Import Mapping (4 imports/year) | 12 hours | 2 hours | **10 hours** |
| Incident Correlation (12 incidents) | 8 hours | 2 hours | **6 hours** |
| Crosswalk Research (20 queries) | 8 hours | 1 hour | **7 hours** |
| SSP Narrative Writing (200 controls) | 300 hours | 20 hours (review) | **280 hours** |
| Schedule Optimization (quarterly) | 8 hours | 1 hour | **7 hours** |
| Approval Summaries (20 packages) | 8 hours | 2 hours | **6 hours** |
| Risk Analysis & Remediation Scripts | 20 hours | 4 hours | **16 hours** |
| Attack Chain Detection & Tickets | 6 hours | 1 hour | **5 hours** |
| **TOTAL** | **~397 hours** | **~37.5 hours** | **~359.5 hours** |

### Key Metrics

| Metric | Value |
|---|---|
| **Total ISSO hours saved per ATO cycle** | ~360 hours |
| **Percentage reduction in manual effort** | ~90% |
| **Full-time equivalent freed up** | ~2.25 FTEs per ATO cycle |
| **Time to generate full SSP (200 controls)** | Minutes vs. weeks |
| **Assessment categories covered** | 20 (200 controls) |
| **Compliance frameworks mapped** | NIST 800-53 Rev 5 + CIS v8 |
| **FIPS 199 baselines supported** | Low (75) / Moderate (155) / High (200) |

---

## Security & Compliance Assurance

| Concern | SOPRA's Answer |
|---|---|
| **"Does AI have access to classified data?"** | No. Only aggregate assessment metrics (pass/fail counts, control IDs) are sent to AI. No PII, no evidence files, no classified content. |
| **"What if AI is wrong?"** | Every AI output requires human review before action. All AI-generated items are tagged with 🤖 badges for auditor transparency. |
| **"What if AI is unavailable?"** | Every feature has a deterministic fallback. If AWS Bedrock is unreachable, SOPRA generates template-based outputs. Zero functionality is lost. |
| **"Does this meet RMF requirements?"** | SOPRA outputs are formatted to NIST RMF standards. AI-generated SSP narratives use formal ATO language. All POA&M entries follow standard POAM structure. |
| **"Is the AI auditable?"** | Yes. AI-generated vs. human-written content is distinguishable via badges. Approval workflow maintains a full audit trail of who approved what and when. |
| **"Can this run air-gapped?"** | Yes. SOPRA runs fully on-premise. AI features are the only optional network dependency. Without AI, all tools function with template-based automation. |
| **"What about FedRAMP?"** | AWS Bedrock is FedRAMP-authorized. The SOPRA application itself runs on-premise with no inbound network requirements. |

---

## Implementation Roadmap

| Phase | Timeline | Deliverable |
|---|---|---|
| **Phase 1: Deploy** | Week 1 | Install SOPRA, configure AWS credentials, run first assessment |
| **Phase 2: Baseline** | Week 2 | Establish FIPS 199 categorization, run full 200-control assessment |
| **Phase 3: ISSO Onboard** | Weeks 3–4 | Train ISSO on AI features, begin using POA&M and risk acceptance automation |
| **Phase 4: ATO Prep** | Weeks 5–8 | Generate AI-assisted SSP, complete evidence collection, prepare approval packages |
| **Phase 5: Continuous** | Ongoing | AI-optimized assessment scheduling, continuous monitoring, incident correlation |

---

## Bottom Line

SOPRA transforms the ISSO role from **document author** to **security decision-maker**. AI handles the writing, classifying, mapping, and drafting. The ISSO focuses on reviewing, deciding, and securing.

**One platform. 200 controls. 13 AI capabilities. ~360 hours saved per ATO cycle.**

---

*SOPRA v3.0 — SAE On-Premise Risk Assessment Platform*
*For questions or demonstration requests, contact the SOPRA development team.*
