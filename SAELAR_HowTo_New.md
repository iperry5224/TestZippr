# SAELAR How-To

**One-stop reference for SAELAR: how it works, ports, navigation, and workflows.**

**Document Version:** 1.0  
**Last Updated:** February 22, 2026

---

## Table of Contents

1. [What Is SAELAR?](#1-what-is-saelar)
2. [How Does SAELAR Work? (Data Collection)](#2-how-does-saelar-work-data-collection)
3. [Ports & Deployment](#3-ports--deployment)
4. [Prerequisites](#4-prerequisites)
5. [Platform Navigation](#5-platform-navigation)
6. [Key Workflows](#6-key-workflows)
7. [Tips & Troubleshooting](#7-tips--troubleshooting)
8. [Related Documentation](#8-related-documentation)

---

## 1. What Is SAELAR?

**SAELAR** (Security Assessment Engine for Live AWS Resources) is an automated NIST 800-53 Rev 5 security controls assessment platform for live AWS environments. It produces pass/fail results, risk scores, evidence, and audit-ready documentation.

---

## 2. How Does SAELAR Work? (Data Collection)

SAELAR performs automated assessments by querying **live AWS resources** via AWS APIs—no agents or network scans.

### What Is boto3 and Why Is It Necessary?

**boto3** is the official Amazon Web Services (AWS) Software Development Kit (SDK) for Python. It provides a programmatic interface to call AWS APIs from Python code.

| Aspect | Description |
|--------|--------------|
| **What it does** | Lets Python applications create clients (e.g., `boto3.client('iam')`, `boto3.client('s3')`) and call AWS API operations (e.g., `list_users()`, `describe_trails()`). |
| **Why SAELAR needs it** | SAELAR must **read** AWS configuration and state—IAM users, S3 encryption, CloudTrail status, GuardDuty findings, etc. The only way to do that is to call AWS APIs. boto3 is the standard, maintained way to do that from Python. |
| **Without boto3** | SAELAR could not query AWS at all; it would have no data to assess. There is no alternative for programmatic AWS access from Python. |
| **Read-only** | SAELAR uses boto3 for **read** operations (list, describe, get). It does not create, modify, or delete AWS resources except for storing reports in S3. |

### How It Collects Data

| Step | What Happens |
|------|--------------|
| 1. **Direct API calls** | Uses boto3 to call each AWS service listed below. |
| 2. **Read-only configuration checks** | Examines configuration state (e.g., CloudTrail enabled, MFA status, S3 encryption, GuardDuty status). |
| 3. **NIST mapping** | Maps each API response to NIST 800-53 controls and assigns pass/fail. |
| 4. **Security Hub (optional)** | Can import GuardDuty, Inspector, Macie, and other findings to supplement assessments. |

### AWS Services Used and Data Provided

| # | AWS Service | Data / Capability Provided |
|---|-------------|----------------------------|
| 1 | **STS** | Account identity and credential validation (`get_caller_identity`) |
| 2 | **IAM** | Users, access keys, last-used dates, password policy, MFA status, root login profile, attached policies, policy versions, roles, account summary |
| 3 | **S3** | Bucket list, encryption configuration, public access block, bucket policies, lifecycle configuration; report upload/storage |
| 4 | **EC2** | Instances, VPCs, security groups, flow logs, network ACLs, snapshots, volumes, EBS encryption default, internet gateways |
| 5 | **CloudTrail** | Trail list, logging status, event selectors (data events, management events) |
| 6 | **CloudWatch** | Alarms (metric alarms for audit, monitoring, alerting) |
| 7 | **CloudWatch Logs** | Log groups (retention, audit log storage) |
| 8 | **AWS Config** | Configuration recorders, recorder status, config rules, compliance details by rule, discovered resource counts |
| 9 | **Security Hub** | Hub status, enabled standards subscriptions, findings (aggregates from GuardDuty, Inspector, Macie, etc.) |
| 10 | **GuardDuty** | Detector list, findings statistics, individual findings (threat detection) |
| 11 | **Inspector v2** | Finding aggregations, vulnerability findings |
| 12 | **Macie** | Findings (sensitive data discovery)—if enabled |
| 13 | **KMS** | Key list, key metadata, key rotation status |
| 14 | **Secrets Manager** | Secret list (secrets storage) |
| 15 | **RDS** | DB instance list (encryption, backup, configuration) |
| 16 | **Backup** | Backup plan list |
| 17 | **ELB v2** | Load balancers, listeners (TLS/encryption in transit) |
| 18 | **ACM** | Certificate list (TLS certificates) |
| 19 | **WAF v2** | WAF policies (if used) |
| 20 | **CodePipeline** | Pipeline list |
| 21 | **CodeBuild** | Project list |
| 22 | **Lambda** | Function list |
| 23 | **SSM** | Associations, patch baselines, compliance summaries |
| 24 | **SNS** | Topic list (notifications, alerting) |
| 25 | **Auto Scaling** | Auto scaling group list |
| 26 | **ECR** | Repository list |
| 27 | **Bedrock** | AI remediation suggestions (Chad); not used for config collection |
| — | **CISA KEV Catalog** | Known Exploited Vulnerabilities (external HTTP, not AWS) |

### What SAELAR Does **Not** Do

- **No agents** — Nothing installed in your account
- **No vulnerability or penetration scanning** — Read-only configuration review
- **No Interview or Test methods** — Uses the **Examine** method per NIST 800-53A (inspects documentation and configuration via APIs)

### Bottom Line

SAELAR evaluates your AWS configuration through **read-only API examination**, aligned with NIST 800-53A’s Examine method.

---

## 3. Ports & Deployment

### SAELAR Ports (Streamlit UI)

| Deployment | Port | Access |
|------------|------|--------|
| **Non-containerized** (EC2 venv) | **8484** | `http://<EC2_IP>:8484` |
| **Containerized** (Docker/sopsael) | **8443** | `http://<EC2_IP>:8443` |

**WebSockets:** Streamlit uses WebSockets on the **same port** (HTTP upgrade). No separate port needed.

### SOPRA Ports (for reference)

| Deployment | Port | Access |
|------------|------|--------|
| Non-containerized | 8080 | `http://<EC2_IP>:8080` |
| Containerized | 5224 | `http://<EC2_IP>:5224` |

### Security Group (typical)

| Port | Purpose |
|------|---------|
| 22 | SSH |
| 80 | Optional landing page |
| 8080 or 5224 | SOPRA |
| 8484 or 8443 | SAELAR |

---

## 4. Prerequisites

| Requirement | Description |
|-------------|-------------|
| **Access** | Valid credentials (if authentication is enabled) |
| **AWS** | Credentials with permissions for CloudTrail, IAM, S3, Config, Security Hub, GuardDuty, etc. |
| **Browser** | Modern browser; 1280px+ width recommended |
| **URL** | SAELAR URL (e.g., `https://saelar.ngrok.dev` or your deployment) |

---

## 5. Platform Navigation

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  SIDEBAR (left)              │  MAIN CONTENT (right)             │
│  • System Info               │  NIST | AWS | Chad | Risk |       │
│  • AWS Account               │  SSP | BOD 22-01 | Threat |       │
│  • Assessment Config         │  Artifacts                        │
│  • Control Families          │                                   │
│  • Run Assessment            │  Selected tab content            │
│  • Chad (AI) chat            │                                   │
│  • Saved Results & Export    │                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Sidebar (Top to Bottom)

| Section | Purpose |
|---------|---------|
| **System** | Store system details for SSP/RAR; enter before generating documents |
| **AWS Account** | View or change AWS credentials |
| **Assessment Configuration** | Region and Impact Level (Low/Moderate/High) |
| **Control Families** | Select NIST families; use **Select All** / **Clear All** |
| **Security Hub** | Optionally include GuardDuty, Inspector, Macie findings |
| **Run Assessment** | Start the assessment (enable when ≥1 family selected) |
| **Chad (AI)** | Quick questions about findings and remediation |
| **Saved Results & Export** | S3 paths and download links |

### Main Tabs

| Tab | Purpose |
|-----|---------|
| **NIST Assessment** | Results, dashboard, findings, risk matrix, report |
| **AWS Console** | Links to AWS service consoles |
| **Chad (AI)** | Full chat with preset questions and report generation |
| **Risk Calculator** | Risk scoring; auto-filled from NIST results |
| **SSP Generator** | SSP, POA&Ms, Risk Acceptance (RAR) |
| **BOD 22-01** | CISA KEV CVE checks |
| **Threat Modeling** | Threat and control mapping |
| **Artifacts** | Saved reports and documents |

---

## 6. Key Workflows

### First-Time Assessment

1. Configure AWS credentials (sidebar → AWS Account)
2. Enter System details (sidebar → System)
3. Select Impact Level and Control Families
4. Optionally check **Include in Assessment** for Security Hub
5. Click **Run Assessment**
6. View results in **NIST Assessment** tab
7. Use **Chad (AI)** for remediation guidance

### Generate SSP

1. Complete System info in sidebar
2. Run at least one NIST Assessment
3. Go to **SSP Generator** → **Generate SSP**
4. Choose options and click **Generate System Security Plan**
5. Download from **Saved Results & Export**

### Check CVE (BOD 22-01)

1. Open **BOD 22-01** tab → **Check CVEs**
2. Enter CVE ID(s) and run the check
3. Use **Full Catalog** or **Report** for broader analysis

### Create Risk Acceptance (RAR)

1. Run NIST Assessment
2. Go to **SSP Generator** → **Risk Acceptance**
3. Select a finding
4. Click **Chad AI Draft** to fill justification and compensating controls
5. Review and generate the RAR

---

## 7. Tips & Troubleshooting

### Tips for ISSOs

| Tip | Description |
|-----|-------------|
| Control Families | Start with AU, AC, SC, IA for core infrastructure |
| Security Hub | Enable “Include in Assessment” for richer results |
| Chad (AI) | Use for remediation, executive summaries, POA&M drafts |
| System Info | Complete early; it feeds SSP, POA&M, and RAR |
| S3 Auto-Save | Results are saved automatically; paths in **Saved Results** |

### Troubleshooting

| Issue | Action |
|-------|--------|
| “AWS credentials not found” | Re-enter credentials in sidebar or set environment variables |
| “No system configured” | Enter system details in sidebar → System |
| “Please select at least one family” | Select at least one control family before Run Assessment |
| Chad (AI) not responding | Check AWS Bedrock access; in air-gapped mode, ensure Ollama is running |
| SSP generation fails | Ensure System Name, Owner, and Description are set; run NIST Assessment first |

---

## 8. Related Documentation

| Document | Description |
|----------|-------------|
| **SAELAR_User_Navigation_SOP.md** | Detailed navigation and screenshots |
| **SAELAR_SOPRA_Consolidated_Briefing.md** | Platform overview and data sources |
| **SAELAR_SOPRA_AWS_Test_Environment_Provisioning_Guide.md** | Deployment and provisioning |
| **user_manuals/screenshots/SAELAR_SCREENSHOTS_GUIDE.md** | Screenshot capture guide |

---

*End of How-To*
