# SOPRA — Architecture Design Document
### SAE On-Premise Risk Assessment Platform v2.0
**Prepared for:** Security Team Code Review  
**Date:** 2026-02-07  
**Classification:** Internal Use Only

---

## Architecture Diagram

![SOPRA Technical Architecture](SOPRA_Technical_Architecture_Diagram.png)

---

## 1. System Overview

SOPRA is a single-page web application built on **Streamlit** (Python) that performs on-premise security assessments against 80 controls across 8 categories, aligned to NIST 800-53 control families. It runs locally on **port 8080** with no external database — all data is file-based or in-memory.

| Attribute | Value |
|---|---|
| Framework | Streamlit 1.29.0+ |
| Language | Python 3.14 |
| Port | 8080 (configurable) |
| Database | None — file-based only |
| AI Backend | AWS Bedrock (optional) |
| Total LOC | ~7,883 (5,118 + 2,765) |

---

## 2. Architecture Layers

### 2.1 Presentation Layer

```
Web Browser → http://localhost:8080 → Streamlit Web Server
                                        ↓
                            ┌───────────────────────┐
                            │  Pop-out Window        │
                            │  ?view=remediation     │
                            │  (separate browser tab)│
                            └───────────────────────┘
```

- **Single-page app** with sidebar navigation (5 main tabs)
- State-driven routing via `st.session_state.opra_active_tab`
- **Pop-out remediation window**: query parameter `?view=remediation` renders a standalone page; data shared via `.sopra_results.json` on disk
- All HTML rendering uses `st.markdown(unsafe_allow_html=True)` for custom styling
- Custom CSS injected at module level (~700 lines of inline styles)

### 2.2 Application Layer

#### Primary Module: `sopra_setup.py` (~5,100 lines)

| Function | Purpose | Tab |
|---|---|---|
| `main()` | Entry point, routing, sidebar | — |
| `render_dashboard()` | Metrics, KPI tiles, charts | Dashboard |
| `render_assessment_page()` | CSV import, demo data, manual assessment | Assessment |
| `render_reports_page()` | Report generation, exports | Reports |
| `render_ai_assistant()` | Bedrock-powered chat | AI Assistant |
| `render_settings_page()` | Configuration UI | Settings |
| `render_remediation_page()` | Standalone pop-out window | Pop-out |
| `render_category_details()` | Category drill-down | Dashboard → Category |
| `render_metric_details()` | Metric analysis | Dashboard → Metric |
| `render_controls_detail()` | Control library browser | Dashboard → Controls |
| `show_remediation_content()` | Remediation report renderer | Shared |
| `aggregate_findings()` | Single-pass metrics aggregation | Shared |
| `calculate_risk_score()` | Weighted risk scoring | Shared |

#### Controls Module: `sopra_controls.py` (~2,765 lines)

| Export | Type | Description |
|---|---|---|
| `ALL_CONTROLS` | `dict[str, Control]` | ~80 control definitions |
| `get_control_by_id()` | Function | Lookup single control |
| `get_controls_by_category()` | Function | Filter by category |
| `get_controls_by_family()` | Function | Filter by NIST family |
| `get_remediation_script()` | Function | Generate PowerShell fix script |
| `ControlStatus` | Enum | PASSED, FAILED, NOT_ASSESSED, etc. |
| `Severity` | Enum | CRITICAL, HIGH, MEDIUM, LOW |
| `ControlFamily` | Enum | 16 NIST 800-53 families |

#### Data Structures

**Control** (dataclass):
```
id, name, description, family, category, check_procedure,
expected_result, remediation_steps[], references[],
nist_mapping[], cis_mapping, default_severity
```

**RemediationStep** (dataclass):
```
step_number, description, command, script_type,
estimated_time, requires_downtime
```

**Finding** (dict at runtime):
```json
{
  "control_id": "AD-001",
  "control_name": "Domain Admin Account Security",
  "category": "Active Directory",
  "family": "Access Control",
  "status": "Failed",
  "severity": "Critical",
  "evidence": "...",
  "notes": "..."
}
```

### 2.3 AI / Cloud Layer — AWS Bedrock

| Attribute | Value |
|---|---|
| Service | `bedrock-runtime` via `boto3` |
| API | Converse API |
| Region | `us-east-1` (default) |
| Auth | Standard boto3 credential chain |
| Max Tokens | 4,096 |
| Temperature | 0.7 |

**Model Fallback Chain** (tried in order):

| Priority | Model ID | Provider |
|---|---|---|
| 1 | `nvidia.nemotron-nano-12b-v2` | NVIDIA |
| 2 | *(Claude removed per policy)* | — |
| 5 | `amazon.titan-text-express-v1` | Amazon |
| 6 | `amazon.titan-text-lite-v1` | Amazon |
| 7 | `meta.llama3-8b-instruct-v1:0` | Meta |
| 8 | `mistral.mistral-7b-instruct-v0:2` | Mistral |

**Failure Mode:** If all models are unavailable (no credentials, no models enabled), the AI assistant falls back to **local canned responses** covering common security topics. No data leaves the local machine in this mode.

**Data sent to Bedrock:**
- User question text
- Assessment context summary (aggregate counts, no raw evidence)
- Chat history (conversation turns)

### 2.4 Data & Storage Layer

**No database.** All persistence is file-based or in-memory.

| Store | Type | Scope | Contents |
|---|---|---|---|
| `st.session_state` | In-memory dict | Per browser tab | Assessment results, chat history, navigation state |
| `.sopra_results.json` | JSON file | Cross-tab | Assessment results (written after assessment, read by pop-out) |
| `demo_csv_data/*.csv` | CSV files (8) | Read-only | Pre-built demo assessment data |
| `assets/` | Image files (9) | Read-only | Logos and avatars |
| `.streamlit/config.toml` | TOML | Read-only | Theme + server config |
| `templates/` | Document templates | Read-only | RAR template |

**Session State Keys:**

| Key | Type | Purpose |
|---|---|---|
| `opra_assessment_results` | dict / None | Primary assessment data |
| `opra_active_tab` | str | Current navigation tab |
| `opra_chat_history` | list | AI conversation turns |
| `opra_selected_category` | str / None | Category drill-down target |
| `opra_selected_control` | str / None | Control detail target |
| `opra_selected_metric` | str / None | Metric detail target |

---

## 3. Data Flow

```
                    ┌─────────────────┐
                    │  CSV Upload     │  (or Demo Data / Manual Assessment)
                    └────────┬────────┘
                             │ pd.read_csv()
                             ▼
                    ┌─────────────────┐
                    │  Parse & Map    │  Validate columns, map to controls
                    │  Finding Objects│  Look up family from sopra_controls
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Session State  │  st.session_state.opra_assessment_results
                    └──┬──────────┬───┘
                       │          │
              save_results_to_file()
                       │          │
              ┌────────▼──┐  ┌───▼─────────────┐
              │ .sopra_    │  │ Dashboard /      │
              │ results.   │  │ Reports /        │
              │ json       │  │ Remediation      │
              └────────┬───┘  └──────┬──────────┘
                       │             │
              ┌────────▼──┐  ┌──────▼──────────┐
              │ Pop-out   │  │ Export Downloads  │
              │ Remediation│  │ • Executive .md  │
              │ Window    │  │ • Full Report .md│
              └───────────┘  │ • POA&M .csv     │
                             │ • Scripts .ps1    │
                             └──────────────────┘
```

---

## 4. Security Assessment Categories

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

**Compliance Mappings:** Each control maps to NIST 800-53 controls and CIS Controls.

**Risk Scoring:** `100 - ((weighted_failed / total_weight) * 100)`
- Critical = 10, High = 7, Medium = 4, Low = 1

---

## 5. External Dependencies

| Package | Version | Purpose | Network Required |
|---|---|---|---|
| `streamlit` | ≥1.29.0 | Web UI framework | Install only |
| `pandas` | ≥2.0.0 | CSV/data processing | Install only |
| `plotly` | ≥5.18.0 | Interactive charts | Install only |
| `boto3` | ≥1.34.0 | AWS Bedrock SDK | AI calls only |
| `botocore` | ≥1.34.0 | AWS SDK core | AI calls only |
| `python-dateutil` | ≥2.8.0 | Date utilities | Install only |
| `python-docx` | ≥1.1.0 | Document generation | Install only |
| `rich` | ≥13.0.0 | Terminal output (optional) | Install only |
| `tabulate` | ≥0.9.0 | Table formatting (optional) | Install only |

**Runtime Network:** Only `boto3` calls to AWS Bedrock require network. All other functionality is **fully air-gapped**.

---

## 6. Deployment Model

```
SOPRA_Deploy_YYYYMMDD.zip
├── sopra_setup.py              # Main application
├── sopra_controls.py           # Control library
├── sopra.bat                   # Windows batch launcher
├── sopra.ps1                   # PowerShell launcher (with ngrok option)
├── requirements.txt            # Python dependencies
├── .streamlit/
│   └── config.toml             # Theme and server config
├── demo_csv_data/              # 8 demo assessment CSV files
│   ├── active_directory_assessment.csv
│   ├── data_protection_assessment.csv
│   ├── endpoint_security_assessment.csv
│   ├── identity_access_management_assessment.csv
│   ├── monitoring_logging_assessment.csv
│   ├── network_infrastructure_assessment.csv
│   ├── physical_security_assessment.csv
│   └── server_security_assessment.csv
├── assets/                     # Logos and images
│   ├── SOPRA_logo_dark.png
│   └── ... (9 image files)
└── templates/
    └── SAE_RAR_Template_2026.doc
```

**Installation:**
1. Extract ZIP to target directory
2. `pip install -r requirements.txt`
3. Configure AWS credentials (optional, for AI features)
4. `sopra.bat` or `python -m streamlit run sopra_setup.py --server.port 8080`

---

## 7. Security Considerations for Code Review

| Area | Notes |
|---|---|
| **Authentication** | None — runs on localhost, no built-in auth |
| **Authorization** | None — single-user model |
| **Input Validation** | CSV parsing via pandas; no explicit sanitization of HTML content |
| **XSS Surface** | Extensive use of `unsafe_allow_html=True` for custom UI rendering |
| **Secrets Management** | AWS credentials via standard boto3 chain (env vars, IAM role, or `~/.aws/`) |
| **Data at Rest** | `.sopra_results.json` stored in plaintext on disk |
| **Data in Transit** | HTTP only (no TLS by default); Bedrock calls use HTTPS via boto3 |
| **Dependencies** | Standard PyPI packages; no vendored or custom-compiled binaries |
| **File System Access** | Reads/writes limited to application directory |
| **Process Model** | Single Streamlit process; no background workers or queues |
| **Logging** | Streamlit default logging; no custom audit trail |
| **Session Management** | Streamlit session state (in-memory, per-tab, non-persistent) |

---

*Document generated for SOPRA v2.0.0 — SAE On-Premise Risk Assessment Platform*
