# SOPRA — Architecture Design Document
### SAE On-Premise Risk Assessment Platform v3.1 (AI-Enhanced)
**Prepared for:** Security Team Code Review
**Date:** 2026-02-10
**Classification:** Internal Use Only

---

## 1. System Overview

SOPRA is a modular web application built on **Streamlit** (Python) that performs on-premise security assessments against **200 controls** across **20 categories**, aligned to NIST 800-53 Rev 5 control families and CIS Controls v8. It features a full **ISSO Toolkit** with 12 tools, **10 AI-powered automation features** using AWS Bedrock, **FIPS 199 security categorization**, and **bidirectional control crosswalks**.

| Attribute | Value |
|---|---|
| Framework | Streamlit 1.29.0+ |
| Language | Python 3.12+ |
| Port | 8501 (configurable) |
| Database | None — file-based JSON persistence |
| AI Backend | AWS Bedrock (optional, graceful fallback) |
| Total Controls | 200 (20 categories x 10 controls) |
| FIPS 199 Baselines | Low: 75, Moderate: 155, High: 200 |
| Architecture | Modular Python package (`sopra/`) |

---

## 2. Architecture Layers

### 2.1 Presentation Layer

```
Web Browser → http://localhost:8501 → Streamlit Web Server
                                        ↓
                    ┌───────────────────────────────┐
                    │  Query Parameter Routing       │
                    │  ?view=remediation             │
                    │  ?view=isso                    │
                    │  ?view=conmon                  │
                    │  ?view=ssp | assessment |      │
                    │  reports | ai | ai_remed       │
                    │  (separate browser tabs)       │
                    └───────────────────────────────┘
```

- **Modular page architecture** with dedicated Python modules per page (8 pages + ISSO Toolkit)
- State-driven routing via `st.session_state.opra_active_tab`
- **Pop-out windows**: Query parameter `?view=<page>` renders standalone pages; data shared via `.sopra_results.json` on disk
- **Cross-tab data resilience**: All pages implement `load_results_from_file()` fallback when session state is empty, ensuring assessment data is always available regardless of how a page is opened
- **Fixed navigation**: "Back to Dashboard" button in top-right corner on all sub-pages
- **ISSO Toolkit**: Dedicated pop-out window (`?view=isso`) with internal sidebar navigation for 12 tools
- **Continuous Monitoring**: CISA/US-CERT inspired design with threat level banners, category advisory cards, assessment timeline feed, and severity pills
- Custom CSS injected at module level (~700 lines of inline styles)

### 2.2 Application Layer — Package Structure

```
sopra_setup.py                    # Entry point — routing, CSS, sidebar, session init
sopra_controls.py                 # 200 control definitions (dataclasses)
│
sopra/                            # Core package
├── __init__.py
├── theme.py                      # Colors, CSS, category definitions
├── persistence.py                # JSON file I/O, cross-tab data sharing
├── utils.py                      # Chart builders, aggregation, risk scoring
├── fips199.py                    # FIPS 199 baseline maps & filtering
│
├── pages/                        # Main application pages (8 modules)
│   ├── dashboard.py              # Main dashboard, metrics, charts, FIPS selector
│   ├── assessment.py             # CSV import, demo data, manual assessment
│   ├── reports.py                # Report generation, exports
│   ├── ai_assistant.py           # Bedrock-powered chat ("Chad"), chart gen
│   ├── ssp_generator.py          # SSP document generation (AI-enhanced)
│   ├── remediation.py            # AI-Powered Vulnerability Remediation dashboard
│   ├── conmon.py                 # Continuous Monitoring (CISA-style dashboard)
│   └── settings.py               # Application settings and configuration
│
└── isso/                         # ISSO Toolkit (12 tools)
    ├── toolkit.py                # Toolkit hub page & sidebar router
    ├── ai_engine.py              # ★ Central AI engine (10 functions)
    ├── ai_remediation.py         # AI remediation plans, attack chains, tickets
    ├── ai_remed_ui.py            # AI Remediation Center UI
    ├── poam.py                   # POA&M Tracker (AI-enhanced)
    ├── risk_acceptance.py        # Risk Acceptance Log (AI-enhanced)
    ├── evidence.py               # Evidence Collection (AI-enhanced)
    ├── inheritance.py            # Control Inheritance Model (AI-enhanced)
    ├── scheduling.py             # Assessment Scheduling (AI-enhanced)
    ├── approvals.py              # Approval Workflow (AI-enhanced)
    ├── stig_import.py            # STIG/Benchmark Import (AI-enhanced)
    ├── incidents.py              # Incident Correlation (AI-enhanced)
    ├── crosswalk.py              # Bidirectional crosswalk logic
    └── crosswalk_ui.py           # Crosswalk UI (AI-enhanced)
```

### 2.3 AI / Cloud Layer — AWS Bedrock

| Attribute | Value |
|---|---|
| Service | `bedrock-runtime` via `boto3` |
| API | Converse API |
| Region | `us-east-1` (default) |
| Auth | Standard boto3 credential chain |
| Max Tokens | 2,048–4,096 (varies by use case) |
| Temperature | 0.4 (ISSO tools) / 0.7 (chat) |

**Model Fallback Chains:**

*Chat Assistant (ai_assistant.py):*

| Priority | Model ID | Provider |
|---|---|---|
| 1 | `nvidia.nemotron-nano-12b-v2` | NVIDIA |
| 2 | *(Claude removed per policy)* | — |
| 5 | `amazon.titan-text-express-v1` | Amazon |
| 6 | `amazon.titan-text-lite-v1` | Amazon |
| 7 | `meta.llama3-8b-instruct-v1:0` | Meta |
| 8 | `mistral.mistral-7b-instruct-v0:2` | Mistral |

*ISSO AI Engine (ai_engine.py):*

| Priority | Model ID | Provider |
|---|---|---|
| 1 | *(Claude removed per policy)* | — |
| 3 | `amazon.titan-text-express-v1` | Amazon |

**Failure Mode:** If all models are unavailable (no credentials, no models enabled), every AI feature falls back to **deterministic template-based responses**. No data leaves the local machine in this mode. Zero functionality is lost.

### 2.4 Data & Storage Layer

**No database.** All persistence is file-based or in-memory.

| Store | Type | Scope | Contents |
|---|---|---|---|
| `st.session_state` | In-memory dict | Per browser tab | Assessment results, chat history, navigation state |
| `.sopra_results.json` | JSON file | Cross-tab | Assessment results (written after assessment, read by all pages as fallback) |
| `.sopra_assessment_history.json` | JSON file | Cross-tab | Assessment history timeline |
| `.sopra_data/*.json` | JSON files | Persistent | ISSO tool data (POA&M, risk acceptances, evidence, etc.) |
| `.sopra_data/evidence_files/` | Binary files | Persistent | Uploaded evidence artifacts |
| `demo_csv_data/*.csv` | CSV files (20) | Read-only | Pre-built demo assessment data |
| `assets/` | Image files (9) | Read-only | Logos and avatars |
| `.streamlit/config.toml` | TOML | Read-only | Theme and server config |

**ISSO Persistence Files (`.sopra_data/`):**

| File | Tool | Contents |
|---|---|---|
| `poam.json` | POA&M Tracker | POA&M items with milestones, due dates, AI flags |
| `risk_acceptances.json` | Risk Acceptance | Accepted risks, justifications, expiry dates |
| `evidence.json` | Evidence Collection | Evidence metadata (files stored separately) |
| `control_inheritance.json` | Inheritance Model | Control classification (Inherited/Common/System-Specific) |
| `assessment_schedules.json` | Scheduling | Per-category assessment frequencies |
| `approvals.json` | Approval Workflow | AO sign-off records |
| `incidents.json` | Incident Correlation | Security incidents linked to findings |
| `ai_remed_plans.json` | AI Remediation | Cached AI-generated remediation plans |
| `remediation_tracking.json` | Remediation Tracking | Remediation attempt history |

---

## 3. AI Integration Architecture

### 3.1 Central AI Engine (`sopra/isso/ai_engine.py`)

All ISSO Toolkit AI features route through a single engine module with specialized prompt templates per tool.

```
┌─────────────────────────────────────────────────────┐
│                    ai_engine.py                       │
│  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │  _call_ai()     │  │  Model Fallback Chain   │   │
│  │  (Bedrock API)  │──│  Nemotron → Titan → Llama │   │
│  └────────┬────────┘  └─────────────────────────┘   │
│           │                                          │
│  ┌────────▼────────────────────────────────────────┐ │
│  │  10 Specialized AI Functions                     │ │
│  │  ┌──────────────────┐ ┌───────────────────────┐ │ │
│  │  │ POA&M Generation │ │ Risk Justification    │ │ │
│  │  │ Evidence Analysis│ │ Inheritance Classify   │ │ │
│  │  │ STIG Mapping     │ │ Incident Correlation  │ │ │
│  │  │ Crosswalk Query  │ │ SSP Narratives        │ │ │
│  │  │ Schedule Optimize│ │ Approval Drafting     │ │ │
│  │  └──────────────────┘ └───────────────────────┘ │ │
│  └─────────────────────────────────────────────────┘ │
│           │                                          │
│  ┌────────▼────────┐                                 │
│  │ Fallback Engine │  (deterministic templates)      │
│  │ (No AI needed)  │                                 │
│  └─────────────────┘                                 │
└─────────────────────────────────────────────────────┘
```

### 3.2 AI Feature Matrix

| # | Tool | AI Function | Trigger | Fallback |
|---|---|---|---|---|
| 1 | POA&M Tracker | `ai_generate_poam_entries()` | "AI Generate POA&M" button | Rule-based milestones/owners |
| 2 | Risk Acceptance | `ai_draft_risk_acceptance()` | "AI Draft Justification" button | Template justification |
| 3 | Evidence Collection | `ai_analyze_evidence()` | "Analyze Sufficiency" per artifact | Generic sufficiency template |
| 4 | Control Inheritance | `ai_classify_inheritance()` | "AI Classify All" button | Keyword-based classification |
| 5 | STIG Import | `ai_map_stig_to_sopra()` | "AI Map to SOPRA Controls" button | No mapping (manual only) |
| 6 | Incident Correlation | `ai_correlate_incident()` | "AI Suggest Related Controls" button | No suggestions (manual only) |
| 7 | Control Crosswalk | `ai_crosswalk_query()` | "AI Query" tab (chat-style) | Static message |
| 8 | SSP Generator | `ai_generate_ssp_narrative()` | "Generate AI Narratives" button | Template narrative |
| 9 | Assessment Scheduling | `ai_recommend_schedule()` | "AI Optimize All Schedules" button | Rule-based frequency |
| 10 | Approval Workflow | `ai_draft_approval_summary()` | "AI Draft Summary" button | Template summary |

### 3.3 AI Chat Assistant ("Chad")

Separate from the ISSO engine. Full conversational AI with:
- Dynamic assessment context injection
- Risk score chart generation (Plotly) with unique keys per render
- PowerShell remediation script generation
- Attack chain analysis
- Quick question buttons

### 3.4 Continuous Monitoring — CISA/US-CERT Design

The ConMon page (`conmon.py`) is modeled after the CISA.gov advisory style:

| Component | Description |
|---|---|
| **Threat Level Banner** | Dynamic posture indicator (SEVERE/HIGH/ELEVATED/GUARDED/LOW) based on compliance rate and critical findings |
| **Severity Pills** | Four color-coded counters (Critical, High, Medium, Low) for at-a-glance severity breakdown |
| **Category Advisory Cards** | Each category displayed as a card with compliance %, status label, progress bar, and delta from previous assessment. Sorted worst-first. |
| **Assessment Timeline** | Advisory-feed style history of past assessments with color-coded compliance rates |
| **Findings Requiring Action** | Severity-ordered list of failed controls styled as security advisories |
| **Change Summary** | Automated comparison between current and previous assessment showing regressions, improvements, and resolved findings |
| **SOPRA Logo** | Embedded logo in top-left header with "Continuous Monitoring" title at 3.4rem |

Threat level is computed dynamically:
- **SEVERE**: Critical > 5 or compliance < 40%
- **HIGH**: Critical > 0 or compliance < 60%
- **ELEVATED**: High > 5 or compliance < 75%
- **GUARDED**: Compliance < 90%
- **LOW**: Compliance >= 90%

---

## 4. Security Assessment Categories (20)

| # | Category | Controls | Key Focus Areas |
|---|---|---|---|
| 1 | Active Directory | 10 | Domain admins, GPOs, Kerberos, LDAP, password policy |
| 2 | Network Infrastructure | 10 | Segmentation, firewalls, IDS/IPS, VPN, DNS |
| 3 | Endpoint Security | 10 | EDR/AV, patching, encryption, app whitelisting |
| 4 | Server Security | 10 | Hardening, services, databases, certificates |
| 5 | Physical Security | 10 | Access control, surveillance, environmental |
| 6 | Data Protection | 10 | Classification, DLP, encryption, key management |
| 7 | Identity & Access Mgmt | 10 | MFA, PAM, RBAC, session management |
| 8 | Monitoring & Logging | 10 | SIEM, log retention, alerting, threat detection |
| 9 | Vulnerability Management | 10 | Scanning, prioritization, SLAs, remediation tracking |
| 10 | Configuration Management | 10 | Baselines, change control, GPO backup, drift detection |
| 11 | Incident Response | 10 | IR plans, playbooks, communication, forensics |
| 12 | Contingency Planning | 10 | BCP/DR, backup verification, failover testing |
| 13 | Security Awareness & Training | 10 | Phishing simulation, role-based training, compliance |
| 14 | Application Security | 10 | SAST/DAST, dependency scanning, secure SDLC |
| 15 | Supply Chain Risk Mgmt | 10 | Vendor assessment, SBOM, third-party monitoring |
| 16 | Governance & Compliance | 10 | Policy lifecycle, audit scheduling, regulatory mapping |
| 17 | Wireless & Mobile Security | 10 | Rogue AP detection, MDM, certificate auth |
| 18 | Virtualization & Container Security | 10 | Image scanning, runtime protection, orchestration |
| 19 | Email & Communications Security | 10 | SPF/DKIM/DMARC, email encryption, DLP |
| 20 | Cryptographic Controls | 10 | Certificate management, key rotation, TLS enforcement |

### FIPS 199 Security Categorization

| Impact Level | Control Count | Description |
|---|---|---|
| Low | 75 | Minimum baseline controls |
| Moderate | 155 | Low + 80 additional controls |
| High | 200 | Full assessment (all controls) |

### Compliance Mappings

- **NIST 800-53 Rev 5**: Every control maps to one or more NIST control families
- **CIS Controls v8**: Every control maps to CIS benchmark IDs
- **Bidirectional Crosswalk**: Forward (SOPRA → NIST/CIS) and reverse (NIST/CIS → SOPRA)
- **Exportable CSVs**: Three crosswalk documents available for download

### Risk Scoring

`100 - ((weighted_failed / total_weight) * 100)`

| Severity | Weight |
|---|---|
| Critical | 10 |
| High | 7 |
| Medium | 4 |
| Low | 1 |

---

## 5. ISSO Toolkit Architecture

The ISSO Toolkit is a self-contained pop-out window with 12 tools accessible via internal sidebar navigation.

```
┌─────────────────────────────────────────────────────────────┐
│  ISSO Toolkit (?view=isso)                                  │
│  ┌────────────┐  ┌──────────────────────────────────────┐   │
│  │  Sidebar   │  │  Tool Content Area                    │   │
│  │            │  │                                       │   │
│  │  Home      │  │  ┌─────────────────────────────────┐  │   │
│  │  Crosswalk │  │  │  Each tool has:                 │  │   │
│  │  POA&M     │  │  │  • KPI metrics at top           │  │   │
│  │  Risk Acc. │  │  │  • Data entry forms             │  │   │
│  │  Evidence  │  │  │  • 🤖 AI buttons                │  │   │
│  │  Inherit.  │  │  │  • Item list/display            │  │   │
│  │  Scheduling│  │  │  • Export capabilities           │  │   │
│  │  Approvals │  │  │  • AI-generated badges (🤖)     │  │   │
│  │  STIG      │  │  └─────────────────────────────────┘  │   │
│  │  Incidents │  │                                       │   │
│  │  AI Remed. │  │                                       │   │
│  └────────────┘  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Data Flow

```
                    ┌──────────────────┐
                    │  CSV Upload      │  (or Demo Data / Manual Assessment)
                    │  STIG Import     │  (AI-assisted mapping)
                    └────────┬─────────┘
                             │ pd.read_csv() / parse
                             ▼
                    ┌──────────────────┐
                    │  Parse & Map     │  Validate columns, map to controls
                    │  FIPS 199 Filter │  Filter by impact level
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Session State   │  st.session_state.opra_assessment_results
                    └──┬───────────┬───┘
                       │           │
              save_results_to_file()
                       │           │
              ┌────────▼──┐  ┌────▼──────────────┐
              │ .sopra_    │  │ All Pages:         │
              │ results.   │◄─│ Dashboard, Reports │
              │ json       │  │ SSP Gen, AI Asst   │
              └────────┬───┘  │ Remediation, ConMon│
                       │      │ Settings           │
              ┌────────▼──┐   └──────┬─────────────┘
              │ Fallback   │         │
              │ load_      │  ┌──────▼────────────┐
              │ results_   │──│ ISSO Toolkit       │
              │ from_file()│  │ (12 tools)         │
              │ (all pages)│  │ POA&M → AI Engine  │
              └────────────┘  │ Risk → AI Engine   │
                              │ Evidence, STIG...  │
                              └─────┬─────────────┘
                                    │
                              ┌─────▼──────────────┐
                              │ .sopra_data/*.json  │
                              │ (persistent state)  │
                              └─────┬──────────────┘
                                    │
                              ┌─────▼──────────────┐
                              │ Export Downloads     │
                              │ • SSP .docx (AI)    │
                              │ • POA&M .docx       │
                              │ • Crosswalk .csv    │
                              │ • Reports .md       │
                              │ • Scripts .ps1      │
                              │ • Tickets (SN/Jira) │
                              └────────────────────┘
```

---

## 7. External Dependencies

| Package | Version | Purpose | Network Required |
|---|---|---|---|
| `streamlit` | >=1.29.0 | Web UI framework | Install only |
| `pandas` | >=2.0.0 | CSV/data processing | Install only |
| `plotly` | >=5.18.0 | Interactive charts | Install only |
| `boto3` | >=1.34.0 | AWS Bedrock SDK | AI calls only |
| `botocore` | >=1.34.0 | AWS SDK core | AI calls only |
| `python-dateutil` | >=2.8.0 | Date utilities | Install only |
| `python-docx` | >=1.1.0 | Document generation | Install only |
| `rich` | >=13.0.0 | Terminal output (optional) | Install only |
| `tabulate` | >=0.9.0 | Table formatting (optional) | Install only |
| `psutil` | >=5.9.0 | Process management | Install only |

**Runtime Network:** Only `boto3` calls to AWS Bedrock require network. All other functionality is **fully air-gapped**. AI features degrade gracefully to deterministic templates without network.

---

## 8. Deployment Model

```
SOPRA_Deploy_20260209.zip
├── sopra_setup.py                # Entry point — routing, CSS, sidebar
├── sopra_controls.py             # 200 control definitions
├── sopra.bat                     # Windows batch launcher
├── sopra.ps1                     # PowerShell launcher
├── requirements.txt              # Python dependencies
├── .streamlit/
│   └── config.toml               # Theme and server config
├── sopra/                        # Core application package
│   ├── __init__.py
│   ├── theme.py                  # UI constants, CSS, categories
│   ├── persistence.py            # File I/O
│   ├── utils.py                  # Charts, aggregation, scoring
│   ├── fips199.py                # FIPS 199 baselines
│   ├── pages/                    # 8 page modules
│   │   ├── dashboard.py
│   │   ├── assessment.py
│   │   ├── reports.py
│   │   ├── ai_assistant.py
│   │   ├── ssp_generator.py
│   │   ├── remediation.py
│   │   ├── conmon.py
│   │   └── settings.py
│   └── isso/                     # 14 ISSO toolkit modules
│       ├── toolkit.py
│       ├── ai_engine.py          # ★ Central AI engine
│       ├── ai_remediation.py
│       ├── ai_remed_ui.py
│       ├── poam.py
│       ├── risk_acceptance.py
│       ├── evidence.py
│       ├── inheritance.py
│       ├── scheduling.py
│       ├── approvals.py
│       ├── stig_import.py
│       ├── incidents.py
│       ├── crosswalk.py
│       └── crosswalk_ui.py
├── demo_csv_data/                # 20 demo assessment CSV files
├── assets/                       # Logos and images (9 files)
└── templates/
    └── SAE_RAR_Template_2026.doc
```

**Installation:**
1. Extract ZIP to target directory
2. `pip install -r requirements.txt`
3. Configure AWS credentials (optional, for AI features)
4. `sopra.bat` or `python -m streamlit run sopra_setup.py --server.port 8501`

---

## 9. UI/UX Design Standards

| Element | Value | Notes |
|---|---|---|
| **COLOR_PASSED** | `#00ff88` (green) | Used for all "passed/compliant" indicators |
| **COLOR_FAILED** | `#e94560` (red) | Used for all "failed/non-compliant" indicators |
| **Background** | `#0b1120` → `#0d1b2a` | Dark navy gradient |
| **Accent** | `#00d9ff` (cyan) | Headers, highlights, interactive elements |
| **Chart Library** | Plotly (Graph Objects) | Interactive, dark-themed, responsive |
| **ConMon Style** | CISA.gov advisory pattern | Threat levels, advisory cards, timeline feed |
| **Font Sizing** | Large (1rem+ body, 2-3.4rem headings) | Optimized for readability on projectors and shared screens |

---

## 10. Security Considerations

| Area | Notes |
|---|---|
| **Authentication** | None — runs on localhost, no built-in auth |
| **Authorization** | None — single-user model |
| **Input Validation** | CSV parsing via pandas; file uploads restricted by type |
| **XSS Surface** | Extensive use of `unsafe_allow_html=True` for custom UI rendering |
| **Secrets Management** | AWS credentials via standard boto3 chain (env vars, IAM role, or `~/.aws/`) |
| **Data at Rest** | JSON files stored in plaintext on disk; evidence files stored as-is |
| **Data in Transit** | HTTP only (no TLS by default); Bedrock calls use HTTPS via boto3 |
| **AI Data Privacy** | Only aggregate assessment data sent to Bedrock; no PII or raw evidence |
| **Dependencies** | Standard PyPI packages; no vendored or custom-compiled binaries |
| **File System Access** | Reads/writes limited to application directory and `.sopra_data/` |
| **Process Model** | Single Streamlit process; no background workers or queues |
| **Audit Trail** | Approval workflow records all AO sign-offs with timestamps |
| **Session Management** | Streamlit session state (in-memory, per-tab, non-persistent) |
| **AI Fallback** | All AI features degrade gracefully to templates — zero functionality loss |

---

## 11. Version History

| Version | Date | Changes |
|---|---|---|
| v1.0 | 2026-01-xx | Initial release — 80 controls, 8 categories, basic dashboard |
| v2.0 | 2026-02-07 | Modular refactor, AI assistant, remediation dashboard, ISSO toolkit |
| v3.0 | 2026-02-09 | 200 controls (20 categories), FIPS 199, control crosswalks, **10 AI automations in ISSO toolkit**, green/red chart colors |
| v3.1 | 2026-02-10 | CISA/US-CERT ConMon redesign (threat levels, advisory cards, timeline), cross-tab data resilience (file fallback on all 8 pages + ISSO tools), settings page, duplicate key fix in AI chart rendering, UI/UX design standards documented, SOPRA Automation Matrix (28 automated ISSO tasks) |

---

*Document generated for SOPRA v3.1.0 — SAE On-Premise Risk Assessment Platform (AI-Enhanced)*
