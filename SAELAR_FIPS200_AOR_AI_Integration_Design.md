# SAELAR: FIPS 200 AOR AI Integration Design

## AI-Powered Generation of FIPS 200 Assessment of Risk (AOR) with System-Aware Compensating Controls

**Version:** 1.0  
**Date:** February 22, 2026  
**Purpose:** Design for integrating AI-powered FIPS 200 AOR generation where the AI identifies compensating or mitigating controls for user-selected controls, using its understanding of the cloud system's unique SSP, security architecture, and processes.

---

## 1. What Is FIPS 200 AOR?

**FIPS 200** (Minimum Security Requirements for Federal Information and Information Systems) establishes 17 security control families that federal systems must address. An **Assessment of Risk (AOR)** documents risks to the system and how they are addressed—including gaps where compensating or mitigating controls are used instead of full control implementation.

**Key need:** When a control is not fully implemented, the ISSO must identify **compensating controls**—alternative measures that reduce residual risk. These should be **tailored to the system** (its architecture, boundary, processes), not generic boilerplate.

---

## 2. Current State in SAELAR

| Component | Current Behavior | Gap |
|-----------|------------------|-----|
| **Chad (AI) Draft** (Risk Acceptance) | Drafts justification + compensating controls for a single finding | Context is limited to assessment results (failed/warning controls). Does **not** include system info, SSP, or architecture. |
| **`_chad_build_context()`** | Passes: assessment summary, failed controls, warnings | Omits: `system_info`, SSP data, authorization boundary, system description |
| **System Info** | Stored in session (name, acronym, description, boundary, categorization, owner, ISSO, AO) | Not passed to AI |
| **SSP Data** | Generated and stored in `st.session_state.ssp_data` when SSP is generated | Not passed to AI |
| **User Selection** | User picks one finding from dropdown in Risk Acceptance tab | No multi-select; no explicit "FIPS 200 AOR" workflow |

**Result:** Chad's compensating control suggestions are generic and not grounded in the system's actual SSP, architecture, or processes.

---

## 3. Integration Approach

### 3.1 Extend AI Context (Core Change)

**Extend `_chad_build_context()`** (or create `_chad_build_aor_context()`) to include:

| Data Source | Content to Pass | Session State Keys |
|-------------|-----------------|---------------------|
| **System Info** | System name, acronym, description, authorization boundary, categorization, owner, ISSO | `system_info_name`, `system_info_description`, `system_info_boundary`, `system_info_categorization`, etc. |
| **SSP Data** (if available) | Control implementation statements, evidence, POA&M items, system type, deployment model | `ssp_data`, `ssp_system_name`, `ssp_description`, `ssp_boundary` |
| **Assessment Results** | Failed controls, findings, risk levels (already passed) | `results`, `assessor` |
| **Risk Assessment** (optional) | Risk scores, likelihood, impact | `risk_assessment` |

**Token budget:** System info + SSP excerpts should stay within Bedrock context limits (~4K–8K tokens for prompt). Summarize or truncate SSP control narratives if needed.

### 3.2 New Feature: FIPS 200 AOR Generator

Add a dedicated workflow (new tab or sub-tab under SSP Generator):

1. **User selects controls** — Multi-select from failed/warning controls (or any control family)
2. **User confirms context** — "Use my system info and SSP" (with preview)
3. **AI generates AOR section** — For each selected control:
   - Gap / weakness description
   - **Compensating controls** (3–5) tailored to:
     - System's authorization boundary (e.g., AWS Commercial Cloud)
     - Architecture (e.g., serverless, hybrid, multi-account)
     - Existing controls and processes (from SSP)
     - Categorization level (Low/Moderate/High)
   - Mitigating factors
   - Residual risk assessment
4. **Export** — Download as Word/JSON for inclusion in AOR/ATO package

### 3.3 AI Prompt Design

**System prompt (conceptual):**

```
You are an ISSO preparing a FIPS 200 Assessment of Risk (AOR). For each control gap provided:

1. Consider the system's unique context:
   - System name, description, authorization boundary
   - Security categorization (FIPS 199)
   - Deployment model (e.g., AWS IaaS)
   - Control implementation details from the SSP (implemented controls, evidence, architecture)

2. Identify 3–5 COMPENSATING or MITIGATING controls that:
   - Are specific to this cloud system's architecture and processes
   - Leverage existing controls or AWS services where possible
   - Reduce residual risk in a measurable way
   - Avoid generic advice; reference the system's actual boundary and design

3. Output format:
   - Control ID, Control Name
   - Gap Summary (1–2 sentences)
   - Compensating/Mitigating Controls (numbered list, specific to this system)
   - Residual Risk (Low/Moderate/High with brief rationale)
```

**User message:** Include the selected controls, findings, and the full system/SSP context string.

### 3.4 Optional: SSP / Architecture Upload

To improve AI understanding of "unique" architecture:

- **Option A:** Allow user to paste or upload SSP narrative text (or key sections)
- **Option B:** Add an "Architecture Description" field to System Info (free-text)
- **Option C:** Parse generated SSP document and feed control implementation statements into context

Option B is the simplest and does not require file upload or parsing.

---

## 4. Implementation Tasks

| # | Task | Effort |
|---|------|--------|
| 1 | Extend `_chad_build_context()` to include system info (name, description, boundary, categorization) | Small |
| 2 | Extend context to include `ssp_data` summary (control statements, evidence) when available | Small |
| 3 | Add "Architecture Description" or "Security Architecture" field to System Info form | Small |
| 4 | Create `_chad_build_aor_context()` that aggregates system + SSP + assessment for AOR | Medium |
| 5 | Add FIPS 200 AOR Generator sub-tab under SSP Generator (or new main tab) | Medium |
| 6 | Implement multi-select for controls + "Generate AOR" button | Medium |
| 7 | Create AOR-specific AI prompt and response parser | Small |
| 8 | Add export (Word/JSON) for generated AOR sections | Medium |

---

## 5. Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  USER                                                                   │
│  • Selects controls (failed/warning or any)                             │
│  • Optionally adds architecture description                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CONTEXT AGGREGATOR                                                     │
│  • System info (sidebar)                                                │
│  • SSP data (if generated)                                              │
│  • Assessment results                                                    │
│  • Selected control details                                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  AI (Bedrock / Ollama)                                                   │
│  • System prompt: FIPS 200 AOR, system-aware compensating controls     │
│  • User message: controls + full context                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OUTPUT                                                                  │
│  • Per-control: gap, compensating controls, residual risk               │
│  • Export to Word / JSON                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. File Changes Summary

| File | Change |
|------|--------|
| `nist_dashboard.py` | Add "Architecture Description" to System Info form; persist in `system_info_*` |
| `nist_setup.py` | Extend `_chad_build_context()` with system info + SSP; add `_chad_build_aor_context()`; add FIPS 200 AOR tab/sub-tab and generation logic |
| `ssp_generator.py` | (Optional) Helper to extract control narratives for context |
| `wordy.py` or new module | AOR document generation (Word export) |

---

## 7. Success Criteria

- [ ] AI receives system name, description, boundary, and categorization
- [ ] AI receives SSP control implementation data when available
- [ ] User can select multiple controls for AOR generation
- [ ] Compensating controls are specific to the system (reference architecture, boundary, AWS services)
- [ ] Output is structured and exportable for AOR/ATO documentation

---

*End of Design*
