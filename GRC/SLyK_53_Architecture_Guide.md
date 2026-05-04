# SLyK-53 Architecture Guide

## SAE Lightweight Yaml Kit — Console-Integrated Agentic AI Security Assistant

**Version:** 2.0
**Date:** April 2026
**Prepared by:** SAE Team, CyberSecurity Division (CSD)
**NOAA / NESDIS / OSPO**

---

## 1. What Is SLyK-53?

SLyK-53 (SAE Lightweight Yaml Kit) is a serverless, AI-powered security assistant that lives inside the AWS Console. ISSOs and engineers interact with it using natural language to assess compliance, remediate findings, harden assets, and execute predefined security runbooks — without leaving the Console or logging into a separate tool.

SLyK is part of the **GRCP (GRC Platform)** family of tools built by the SAE Team:

| Tool | Purpose | Deployment |
|---|---|---|
| **SAELAR-53** | Full GRC platform — assessments, documents, dashboards | Streamlit on EC2 |
| **SOPRA** | On-premise / air-gapped risk assessment | Streamlit on EC2 |
| **BeeKeeper** | Container vulnerability scanning | Streamlit on EC2 |
| **SLyK-53** | Console-integrated agentic AI assistant | Serverless (Lambda + Bedrock) |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Console                                  │
│                                                                       │
│   User: "Assess my IAM controls"                                     │
│         "Harden all S3 buckets"                                      │
│         "Run the monthly compliance check"                           │
│                                                                       │
│              ┌────────────────────────────┐                          │
│              │   Amazon Bedrock Agent      │                          │
│              │   SLyK-53 Security         │                          │
│              │   Assistant                 │                          │
│              └─────┬──┬──┬──┬──┬──────────┘                          │
│                    │  │  │  │  │                                      │
│         ┌──────────┘  │  │  │  └──────────┐                          │
│         ▼             ▼  ▼  ▼             ▼                          │
│   ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐     │
│   │  ASSESS  │ │REMEDIATE│ │ HARDEN │ │  TRIAGE  │ │ RUNBOOKS │     │
│   │  Lambda  │ │ Lambda  │ │ Lambda │ │  Lambda  │ │  Lambda  │     │
│   └────┬─────┘ └───┬────┘ └───┬────┘ └────┬─────┘ └────┬─────┘     │
│        │           │          │            │            │            │
│        ▼           ▼          ▼            ▼            ▼            │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    AWS Services                              │   │
│   │                                                               │   │
│   │  IAM    EC2    S3     KMS     CloudTrail   GuardDuty        │   │
│   │  Security Hub   Inspector   Config   Macie   SSM            │   │
│   │                                                               │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  Proactive Alerting                                          │   │
│   │                                                               │   │
│   │  Security Hub Finding (CRITICAL/HIGH)                        │   │
│   │       → EventBridge Rule                                     │   │
│   │            → slyk-alert-triage Lambda                        │   │
│   │                 → AI Risk Assessment (Bedrock)               │   │
│   │                 → Remediation Scripts                         │   │
│   │                 → SNS Alert (email)                           │   │
│   │                 → S3 Audit Log                                │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  Data Layer                                                  │   │
│   │                                                               │   │
│   │  S3 (saelarallpurpose)    CloudTrail     SNS Notifications  │   │
│   │  - Assessment results     - API audit     - Security alerts  │   │
│   │  - Runbook outputs        - All actions   - Email/Slack      │   │
│   │  - SLyK config              logged                           │   │
│   └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Components

### 3.1 Bedrock Agent

| Attribute | Value |
|---|---|
| Name | SLyK-53-Security-Assistant |
| Type | Amazon Bedrock Agent |
| Purpose | Orchestrates multi-step security workflows via natural language |
| Memory | Maintains conversation context across messages |
| Action Groups | 5 (ASSESS, REMEDIATE, HARDEN, TRIAGE, RUNBOOKS) |

**Model Succession Plan** — SLyK auto-selects the first available model:

| Priority | Model | Provider |
|---|---|---|
| 1 | Amazon Nova Pro | Amazon |
| 2 | Amazon Nova Lite | Amazon |
| 3 | Amazon Nova Micro | Amazon |
| 4 | Llama 3.1 70B | Meta |
| 5 | Llama 3.1 8B | Meta |
| 6 | Mistral Large | Mistral AI |
| 7 | Mixtral 8x7B | Mistral AI |
| 8 | Titan Text Express | Amazon |
| 9 | Titan Text Lite | Amazon |

### 3.2 Lambda Functions

| Function | Purpose | Trigger | AWS Services Accessed |
|---|---|---|---|
| **slyk-assess** | NIST 800-53 compliance assessment + Security Hub finding import | Bedrock Agent | IAM, EC2, S3, KMS, CloudTrail, GuardDuty, Security Hub |
| **slyk-remediate** | Generate and execute remediation scripts for failed controls or Security Hub findings | Bedrock Agent | IAM, S3, EC2, SSM, Security Hub |
| **slyk-harden** | Scan and fix misconfigurations on S3 buckets, EC2 instances, and IAM users | Bedrock Agent | S3, EC2, IAM |
| **slyk-alert-triage** | Analyze CRITICAL/HIGH findings, generate remediation, call Bedrock for AI risk assessment, send SNS alert | EventBridge (automatic) or Bedrock Agent (on-demand) | Security Hub, Bedrock, SNS, S3 |
| **slyk-runbooks** | Execute predefined ISSO workflows (6 runbooks) | Bedrock Agent | All services (varies by runbook) |

### 3.3 EventBridge Rule

| Attribute | Value |
|---|---|
| Rule Name | SLyK-53-SecurityHub-HighRisk |
| Event Source | aws.securityhub |
| Event Type | Security Hub Findings - Imported |
| Filter | Severity = CRITICAL or HIGH, RecordState = ACTIVE, Workflow = NEW |
| Targets | slyk-alert-triage Lambda + SNS direct notification |

### 3.4 SNS Topic

| Attribute | Value |
|---|---|
| Topic Name | SLyK-53-Security-Alerts |
| Purpose | Deliver security alerts to email/Slack |
| Content | Finding title, severity, resource, AI risk assessment, remediation scripts |

### 3.5 Data Storage

| Location | Content |
|---|---|
| `s3://saelarallpurpose/slyk/slyk_config.json` | Agent configuration |
| `s3://saelarallpurpose/slyk/alerts/` | EventBridge alert triage logs |
| `s3://saelarallpurpose/slyk/runbook_results/` | Runbook execution history |
| CloudTrail | All API calls made by Lambda functions |

---

## 4. Action Groups (Bedrock Agent Capabilities)

### 4.1 ASSESS

**What the user says:**
- *"Assess my NIST 800-53 compliance"*
- *"Check my IAM controls"*
- *"Show me Security Hub findings"*
- *"Run an assessment and include Security Hub"*

**What SLyK does:**
1. Runs 7+ NIST 800-53 control checks (AC-2, AC-6, AU-2, IA-2, SC-7, SC-28, SI-4)
2. Optionally imports Security Hub findings (GuardDuty, Inspector, Macie, IAM Analyzer)
3. Maps Security Hub findings to NIST control families
4. Returns pass/fail/warning per control with specific findings and recommendations

### 4.2 REMEDIATE

**What the user says:**
- *"Fix the AC-2 MFA issue"*
- *"Generate remediation for SC-28"*
- *"Remediate that S3 encryption finding from Security Hub"*

**What SLyK does:**
1. Looks up the control or Security Hub finding
2. Identifies affected resources
3. Generates specific AWS CLI remediation scripts
4. Offers to execute via SSM with user approval
5. Updates Security Hub finding workflow status after fix

**Supported controls:** AC-2, AC-6, AU-2, IA-2, SC-7, SC-28, SI-4, plus any Security Hub finding

### 4.3 HARDEN

**What the user says:**
- *"Harden all my S3 buckets"*
- *"Scan my EC2 instances for misconfigs"*
- *"Check my IAM users"*
- *"Apply the fixes"*

**What SLyK does:**

| Asset Type | Checks Performed | Auto-Fix Available |
|---|---|---|
| **S3** | Public access block, default encryption, versioning, access logging | Yes — enables encryption, versioning, public access block |
| **EC2** | IMDSv2 enforcement, public IP exposure, IAM role attachment | Yes — enforces IMDSv2 |
| **IAM** | MFA enabled, access key age (>90 days) | Partial — reports for manual action |

### 4.4 TRIAGE

**What the user says:**
- *"Triage my security alerts"*
- *"What critical findings do I have?"*

**What SLyK does (also runs automatically via EventBridge):**
1. Pulls CRITICAL/HIGH findings from Security Hub
2. Maps each finding to NIST control family
3. Generates remediation scripts per finding
4. Calls Bedrock for AI risk assessment (threat level, impact, priority)
5. Sends SNS alert with finding + fix + AI analysis
6. Logs to S3 audit trail

### 4.5 RUNBOOKS

**What the user says:**
- *"Show me available runbooks"*
- *"Run the monthly compliance check"*
- *"Check our ATO readiness"*

**Available runbooks:**

| Runbook | Audience | Frequency | Steps |
|---|---|---|---|
| **Monthly Compliance Assessment** | ISSO, Security Manager | Monthly | NIST assessment → Security Hub import → GuardDuty check → AI executive summary → Save report |
| **Quarterly Hardening Review** | ISSO, System Admin | Quarterly | S3 scan → EC2 scan → IAM scan → AI recommendations |
| **Incident Response Triage** | ISSO, IR Team, SOC | On-demand | GuardDuty threats → Security Hub critical → CloudTrail anomalies → AI threat assessment |
| **ATO Readiness Check** | ISSO, Authorizing Official | Pre-assessment | Control coverage → Doc inventory → Services check → AI readiness assessment |
| **POA&M Review** | ISSO | Monthly | Failed controls scan → AI milestone recommendations |
| **New System Onboarding** | ISSO, System Owner | Per new system | Account baseline → Required services → AI onboarding checklist |

All runbook results are saved to `s3://saelarallpurpose/slyk/runbook_results/` for audit.

---

## 5. Data Flow

### 5.1 On-Demand (User-Initiated)

```
ISSO types command in Bedrock Console
    → Bedrock Agent parses intent
    → Routes to appropriate action group
    → Lambda executes (calls AWS APIs)
    → Results returned to Agent
    → Agent formats natural language response
    → ISSO sees results + recommendations
```

### 5.2 Proactive (EventBridge-Triggered)

```
Security Hub detects CRITICAL/HIGH finding
    → EventBridge rule fires
    → slyk-alert-triage Lambda:
        1. Analyzes finding
        2. Maps to NIST control
        3. Generates remediation
        4. Calls Bedrock for AI assessment
        5. Sends SNS alert
        6. Logs to S3
    → ISSO receives email with finding + fix
    → ISSO can ask SLyK to apply the fix
```

---

## 6. Security Model

| Control | Implementation |
|---|---|
| **Authentication** | AWS Console IAM session — no additional login |
| **Authorization** | Lambda execution role scoped to ReadOnlyAccess + targeted hardening actions |
| **Hardening approval** | Agent asks for user confirmation before applying changes |
| **Data boundary** | All data stays within the AWS account — no external API calls |
| **AI model boundary** | All models run within Amazon Bedrock — data does not leave AWS |
| **Audit trail** | CloudTrail logs every API call; runbook results saved to S3 |
| **Alerting** | EventBridge + SNS — no third-party services |
| **Encryption** | S3 SSE for stored data; HTTPS for all API calls |

---

## 7. Cost Model

| Component | Monthly Estimate |
|---|---|
| Lambda (5 functions, ~100 invocations/day) | $5–20 |
| Bedrock Agent (per invocation) | ~$0 |
| Bedrock model calls (~500/month) | $10–50 |
| EventBridge rule | ~$0 |
| SNS alerts (~100/month) | ~$0 |
| S3 storage (config + audit logs) | ~$1 |
| **Total** | **$16–71/month** |

No EC2 instances. No server maintenance. No patching. Fully serverless.

---

## 8. Comparison: SLyK vs SAELAR

| Aspect | SAELAR-53 | SLyK-53 |
|---|---|---|
| **Interface** | Browser (Streamlit web app with 8 tabs) | AWS Console (natural language chat) |
| **Infrastructure** | EC2 instance (must maintain) | Serverless (Lambda + Bedrock — zero maintenance) |
| **Authentication** | Separate SAELAR login | AWS Console session (already logged in) |
| **Assessment depth** | 36+ controls, 25+ services | 7+ controls (expandable), Security Hub integration |
| **Document generation** | SSP, POA&M, RAR (Markdown) | Via runbooks (AI-generated) |
| **Hardening** | Manual (view findings, copy scripts) | Automated (scan → recommend → apply with approval) |
| **Proactive alerts** | None | EventBridge → SNS on CRITICAL/HIGH findings |
| **Runbooks** | None | 6 predefined ISSO workflows |
| **Sharing** | Share URL, separate logins | Anyone with Console access — zero setup |
| **Cost** | ~$50/month (EC2) | ~$16–71/month (serverless) |

**SLyK does not replace SAELAR.** SAELAR remains the deep-dive platform for comprehensive assessments, dashboards, and document management. SLyK provides the quick, conversational interface for daily security tasks directly in the Console.

---

## 9. How to Access SLyK-53

### For Testing (Today)
1. Go to **AWS Console** → **Amazon Bedrock** → **Agents**
2. Select **SLyK-53-Security-Assistant**
3. Click **Test** in the right panel
4. Type any command from Section 4

### For Production (After Console Integration)
1. Click **SLyK-53** link in Service Catalog or Console bookmarks
2. Chat interface opens — already authenticated
3. Ask SLyK anything

### Subscribe to Alerts
```bash
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:<account-id>:SLyK-53-Security-Alerts \
    --protocol email \
    --notification-endpoint your@email.com
```

---

## 10. Deployment

One command in CloudShell:

```bash
unzip slyk-53-deploy.zip
cd slyk
python3 deploy_slyk.py
```

Creates all resources in approximately 3 minutes.

---

## Appendix: Resource Inventory

| Resource | ARN Pattern |
|---|---|
| Lambda: slyk-assess | arn:aws:lambda:us-east-1:*:function:slyk-assess |
| Lambda: slyk-remediate | arn:aws:lambda:us-east-1:*:function:slyk-remediate |
| Lambda: slyk-harden | arn:aws:lambda:us-east-1:*:function:slyk-harden |
| Lambda: slyk-alert-triage | arn:aws:lambda:us-east-1:*:function:slyk-alert-triage |
| Lambda: slyk-runbooks | arn:aws:lambda:us-east-1:*:function:slyk-runbooks |
| IAM Role: SLyK-Lambda-Role | arn:aws:iam::*:role/SLyK-Lambda-Role |
| IAM Role: SLyK-Agent-Role | arn:aws:iam::*:role/SLyK-Agent-Role |
| Bedrock Agent | arn:aws:bedrock:us-east-1:*:agent/* |
| EventBridge Rule | arn:aws:events:us-east-1:*:rule/SLyK-53-SecurityHub-HighRisk |
| SNS Topic | arn:aws:sns:us-east-1:*:SLyK-53-Security-Alerts |
| S3 Config | s3://saelarallpurpose/slyk/ |
