# Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## U.S. Department of Commerce (DOC)
## National Oceanic and Atmospheric Administration (NOAA)
## National Environmental Satellite Data and Information Service (NESDIS)

---

# SLyK-53: Architecture and Standard Operating Procedures

## SAE Lightweight Yaml Kit — Agentic AI Security Assistant

**Version:** 2.0
**Date:** April 2026
**Prepared by:** SAE Team
**Office of Satellite and Product Operations (OSPO) — CyberSecurity Division (CSD)**

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## Record of Changes/Revision

| Version | Date | Description | Sections Affected | Changed By |
|---|---|---|---|---|
| 1.0 | 04/22/2026 | Initial architecture guide. | All | SAE Team |
| 2.0 | 04/28/2026 | Added SOP procedures, sharing guide, YAML specifications, and updated architecture diagram. | All | SAE Team |

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## Table of Contents

1. Purpose
2. Architecture Overview
3. Architecture Diagram
4. Component Details
5. YAML Specifications
6. Data Flow Diagrams
7. Standard Operating Procedures
8. How to Share SLyK-53 with ISSOs
9. Runbook Execution Guide
10. Troubleshooting
11. References

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 1. Purpose

This document provides the detailed architecture and standard operating procedures (SOPs) for SLyK-53 (SAE Lightweight Yaml Kit), a serverless Agentic AI security assistant that operates within the AWS Console. It is intended for the SAE Team, ISSOs, system administrators, and security managers who will operate, maintain, or use SLyK-53.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 2. Architecture Overview

SLyK-53 is a serverless security platform composed of six integrated AWS services:

| Layer | Service | Role in SLyK-53 |
|---|---|---|
| **Interface** | AWS Console + Bedrock Agent | Natural language chat — ISSO types commands, agent responds |
| **Orchestration** | Amazon Bedrock Agent | Parses intent, selects action group, maintains conversation memory |
| **Execution** | AWS Lambda (5 functions) | Runs assessments, generates remediation, hardens assets, triages alerts, executes runbooks |
| **Detection** | Amazon EventBridge | Monitors Security Hub for CRITICAL/HIGH findings, auto-triggers triage |
| **Notification** | Amazon SNS | Delivers alerts with findings, AI analysis, and remediation scripts to email/Slack |
| **Storage** | Amazon S3 | Stores configuration, runbook results, triage logs, and audit trail |

### Design Principles

- **Serverless** — No EC2 instances to maintain; Lambda scales automatically
- **YAML-Defined** — All agent behaviors, API contracts, and event patterns defined in structured YAML
- **Human-in-the-Loop** — Agent asks for approval before any write operation
- **Data Sovereign** — All data stays within the AWS account boundary
- **Model Resilient** — 9-model succession plan ensures availability regardless of model access

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 3. Architecture Diagram

*Reference: SLyK-53 Architecture (generated in eraser.io)*

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                                    │
│                                                                           │
│  ┌──────────┐    login    ┌──────────┐   invoke   ┌─────────────────┐   │
│  │ ISSO     │ ──────────> │  AWS     │ ────────> │  SLyK-53        │   │
│  │ User     │             │ Console  │            │  Bedrock Agent  │   │
│  └──────────┘             └──────────┘            └───┬─┬─┬─┬─┬────┘   │
│                                                       │ │ │ │ │         │
│                           ┌───────────────────────────┘ │ │ │ │         │
│                           │   ┌─────────────────────────┘ │ │ │         │
│                           │   │   ┌───────────────────────┘ │ │         │
│                           │   │   │   ┌─────────────────────┘ │         │
│                           │   │   │   │   ┌───────────────────┘         │
│                           ▼   ▼   ▼   ▼   ▼                            │
│  ┌─ Lambda Functions ──────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  ┌─────────┐ ┌───────────┐ ┌────────┐ ┌────────┐ ┌──────────┐  │    │
│  │  │ ASSESS  │ │ REMEDIATE │ │ HARDEN │ │ TRIAGE │ │ RUNBOOKS │  │    │
│  │  └────┬────┘ └─────┬─────┘ └───┬────┘ └───┬────┘ └────┬─────┘  │    │
│  │       │            │           │           │           │         │    │
│  └───────┼────────────┼───────────┼───────────┼───────────┼────────┘    │
│          │            │           │           │           │              │
│          ▼            ▼           ▼           ▼           ▼              │
│  ┌─ AWS Services ──────────────────────────────────────────────────┐    │
│  │  IAM    EC2    S3    Security Hub    GuardDuty    CloudTrail    │    │
│  │  KMS    Inspector    Config    Macie    SSM                     │    │
│  └──────────────┬──────────────────┬──────────────────────────────┘    │
│                  │                  │                                    │
│                  │ CRITICAL/HIGH    │ audit results                     │
│                  ▼                  ▼                                    │
│  ┌──────────────────┐    ┌──────────────────┐    ┌─────────────────┐   │
│  │  EventBridge      │    │  S3 Audit Logs   │    │  SNS Alerts     │   │
│  │  (auto-trigger)   │───>│  (runbook results│    │  (email/Slack)  │   │
│  │                   │    │   triage logs)    │    │                 │   │
│  └────────┬──────────┘    └──────────────────┘    └────────▲────────┘   │
│           │                                                │            │
│           └── triggers TRIAGE Lambda ──> AI analysis ──> alert ─┘       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 4. Component Details

### 4.1 Bedrock Agent: SLyK-53-Security-Assistant

| Attribute | Value |
|---|---|
| Agent Name | SLyK-53-Security-Assistant |
| Agent ID | WCHOG8B8WDR |
| Status | PREPARED |
| Foundation Model | amazon.nova-pro-v1:0 (with 9-model succession) |
| Action Groups | 5 (ASSESS, REMEDIATE, HARDEN, TRIAGE, RUNBOOKS) |
| Session Timeout | 30 minutes |
| Memory | Maintains conversation context within session |

**Model Succession Plan:**

| Priority | Model | Provider |
|---|---|---|
| 1 | amazon.nova-pro-v1:0 | Amazon |
| 2 | amazon.nova-lite-v1:0 | Amazon |
| 3 | amazon.nova-micro-v1:0 | Amazon |
| 4 | meta.llama3-1-70b-instruct-v1:0 | Meta |
| 5 | meta.llama3-1-8b-instruct-v1:0 | Meta |
| 6 | mistral.mistral-large-2407-v1:0 | Mistral AI |
| 7 | mistral.mixtral-8x7b-instruct-v0:1 | Mistral AI |
| 8 | amazon.titan-text-express-v1 | Amazon |
| 9 | amazon.titan-text-lite-v1 | Amazon |

### 4.2 Lambda Functions

| Function | ARN | Purpose | Timeout | Memory |
|---|---|---|---|---|
| slyk-assess | arn:aws:lambda:us-east-1:656443597515:function:slyk-assess | NIST 800-53 assessment + Security Hub import | 300s | 512 MB |
| slyk-remediate | arn:aws:lambda:us-east-1:656443597515:function:slyk-remediate | Remediation script generation + execution | 300s | 512 MB |
| slyk-harden | arn:aws:lambda:us-east-1:656443597515:function:slyk-harden | S3/EC2/IAM hardening scan + fix | 300s | 512 MB |
| slyk-alert-triage | arn:aws:lambda:us-east-1:656443597515:function:slyk-alert-triage | AI-powered alert analysis + SNS notification | 300s | 512 MB |
| slyk-runbooks | arn:aws:lambda:us-east-1:656443597515:function:slyk-runbooks | ISSO runbook execution engine | 300s | 512 MB |

### 4.3 IAM Roles

| Role | ARN | Trust | Purpose |
|---|---|---|---|
| SLyK-Lambda-Role | arn:aws:iam::656443597515:role/SLyK-Lambda-Role | lambda.amazonaws.com | Lambda execution — ReadOnlyAccess + scoped hardening writes |
| SLyK-Agent-Role | arn:aws:iam::656443597515:role/SLyK-Agent-Role | bedrock.amazonaws.com | Bedrock Agent — InvokeModel + InvokeFunction |

### 4.4 EventBridge Rule

| Attribute | Value |
|---|---|
| Rule Name | SLyK-53-SecurityHub-HighRisk |
| Source | aws.securityhub |
| Detail Type | Security Hub Findings - Imported |
| Filter | Severity = CRITICAL or HIGH, RecordState = ACTIVE, Workflow = NEW |
| Target 1 | slyk-alert-triage Lambda |
| Target 2 | SLyK-53-Security-Alerts SNS topic |

### 4.5 SNS Topic

| Attribute | Value |
|---|---|
| Topic Name | SLyK-53-Security-Alerts |
| ARN | arn:aws:sns:us-east-1:656443597515:SLyK-53-Security-Alerts |
| Subscribers | Email addresses of ISSOs and security team |

### 4.6 S3 Storage

| Path | Content | Retention |
|---|---|---|
| s3://saelarallpurpose/slyk/slyk_config.json | Agent configuration | Permanent |
| s3://saelarallpurpose/slyk/alerts/ | EventBridge alert triage logs | 1 year |
| s3://saelarallpurpose/slyk/runbook_results/ | Runbook execution history | 1 year |

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 5. YAML Specifications

SLyK-53's behavior is defined through three YAML-based configurations:

### 5.1 Agent API Schema (OpenAPI)

Defines what actions the agent can take:

```yaml
openapi: 3.0.0
info:
  title: SLyK-53 API
  version: 1.0.0
paths:
  /assess:
    post:
      operationId: assessCompliance
      summary: Run NIST 800-53 compliance assessment
      parameters:
        - name: families
          description: Control families (AC,AU,IA) or ALL
        - name: include_securityhub
          description: Include Security Hub findings (true/false)

  /securityhub:
    post:
      operationId: getSecurityHubFindings
      summary: Import Security Hub findings
      parameters:
        - name: max_findings
          description: Maximum findings to retrieve
        - name: severity
          description: CRITICAL,HIGH,MEDIUM filter

  /remediate:
    post:
      operationId: remediateControl
      summary: Generate or execute remediation
      parameters:
        - name: control_id
          description: NIST control ID (e.g., AC-2)
        - name: finding_id
          description: Security Hub finding ID
        - name: action
          description: generate or execute

  /harden:
    post:
      operationId: hardenAssets
      summary: Scan and harden AWS assets
      parameters:
        - name: asset_type
          description: s3, ec2, or iam
        - name: action
          description: scan or fix

  /triage:
    post:
      operationId: triageAlerts
      summary: Triage Security Hub alerts with AI analysis
      parameters:
        - name: severity
          description: CRITICAL,HIGH,MEDIUM
        - name: max_findings
          description: Max findings to triage

  /runbooks:
    post:
      operationId: executeRunbook
      summary: List or execute ISSO runbooks
      parameters:
        - name: action
          description: list or execute
        - name: runbook_id
          description: Runbook identifier
```

### 5.2 EventBridge Event Pattern

Defines what triggers proactive alerting:

```yaml
source:
  - aws.securityhub
detail-type:
  - Security Hub Findings - Imported
detail:
  findings:
    Severity:
      Label:
        - CRITICAL
        - HIGH
    RecordState:
      - ACTIVE
    Workflow:
      Status:
        - NEW
```

### 5.3 Agent Instruction Set

Defines the agent's personality and behavioral guidelines:

```yaml
identity:
  name: SLyK
  full_name: SAE Lightweight Yaml Kit
  version: "53"
  organization: NOAA NESDIS
  team: SAE Team (GRCP)

capabilities:
  - ASSESS: Run NIST 800-53 compliance assessments
  - REMEDIATE: Generate and execute remediation scripts
  - HARDEN: Scan and harden S3, EC2, IAM assets
  - TRIAGE: Analyze Security Hub alerts with AI
  - RUNBOOKS: Execute predefined ISSO workflows

guidelines:
  - Always explain actions before executing
  - Present results with pass/fail status and specific findings
  - Show remediation scripts before executing
  - Ask for confirmation before any write operation
  - Reference NIST control IDs when discussing compliance
  - Be concise but thorough
```

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 6. Data Flow Diagrams

### 6.1 On-Demand Assessment Flow

```
ISSO                    SLyK Agent              ASSESS Lambda           AWS Services
  │                         │                        │                       │
  │ "Assess my IAM"        │                        │                       │
  │ ──────────────────────> │                        │                       │
  │                         │  Invoke ASSESS          │                       │
  │                         │ ──────────────────────> │                       │
  │                         │                        │  Check IAM users      │
  │                         │                        │ ────────────────────> │
  │                         │                        │  Check MFA            │
  │                         │                        │ ────────────────────> │
  │                         │                        │  Check policies       │
  │                         │                        │ ────────────────────> │
  │                         │                        │ <──── Results ─────── │
  │                         │ <──── Pass/Fail ─────── │                       │
  │ "AC-2: 3 users no MFA" │                        │                       │
  │ <────────────────────── │                        │                       │
```

### 6.2 Proactive Alert Flow

```
Security Hub            EventBridge             TRIAGE Lambda           Bedrock AI            SNS
     │                       │                       │                     │                   │
     │ CRITICAL finding      │                       │                     │                   │
     │ ────────────────────> │                       │                     │                   │
     │                       │ Auto-trigger           │                     │                   │
     │                       │ ────────────────────> │                     │                   │
     │                       │                       │ Analyze finding      │                   │
     │                       │                       │ Generate scripts     │                   │
     │                       │                       │ ──────────────────> │                   │
     │                       │                       │ <── AI assessment ── │                   │
     │                       │                       │                     │                   │
     │                       │                       │ Send alert           │                   │
     │                       │                       │ ─────────────────────────────────────> │
     │                       │                       │                     │                   │
     │                       │                       │ Save to S3           │          Email to │
     │                       │                       │ (audit trail)        │            ISSO   │
```

### 6.3 Runbook Execution Flow

```
ISSO                    SLyK Agent              RUNBOOKS Lambda         Multiple Services
  │                         │                        │                       │
  │ "Run monthly check"    │                        │                       │
  │ ──────────────────────> │                        │                       │
  │                         │ ──────────────────────> │                       │
  │                         │                        │ Step 1: NIST assess  │
  │                         │                        │ ────────────────────> │
  │                         │                        │ Step 2: SecHub import│
  │                         │                        │ ────────────────────> │
  │                         │                        │ Step 3: GuardDuty    │
  │                         │                        │ ────────────────────> │
  │                         │                        │ Step 4: AI summary   │
  │                         │                        │ (calls Bedrock)      │
  │                         │                        │ Step 5: Save to S3   │
  │                         │ <──── Complete ──────── │                       │
  │ "5 passed, 2 failed,   │                        │                       │
  │  report saved to S3"   │                        │                       │
  │ <────────────────────── │                        │                       │
```

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 7. Standard Operating Procedures

### SOP-001: Running a Compliance Assessment

**Purpose:** Assess the AWS environment against NIST 800-53 Rev 5 controls.

**Who:** ISSO, Security Engineer

**Steps:**

1. Open **AWS Console** → **Amazon Bedrock** → **Agents**
2. Select **SLyK-53-Security-Assistant**
3. Click **Test** (right panel)
4. Type: `Assess my NIST 800-53 compliance`
5. Review results — each control shows PASS, FAIL, or WARNING with specific findings
6. For failed controls, type: `Generate remediation for [control_id]`
7. Review the remediation scripts before executing

**Variations:**
- Assess specific families: `Check my IAM controls` or `Assess AC and AU families`
- Include Security Hub: `Assess compliance and include Security Hub findings`
- Security Hub only: `Show me my Security Hub findings`

---

### SOP-002: Remediating a Failed Control

**Purpose:** Fix a security control that failed assessment.

**Who:** ISSO, Security Engineer

**Steps:**

1. Run an assessment per SOP-001
2. Identify the failed control (e.g., AC-2)
3. Type: `Generate remediation for AC-2`
4. Review the scripts SLyK provides
5. Choose one of:
   - **Manual execution:** Copy the scripts and run them yourself in CloudShell
   - **SLyK execution:** Type `Execute the remediation for AC-2` and confirm when prompted
6. After remediation, re-assess: `Assess AC controls` to verify the fix

**Important:** SLyK will always show you the scripts and ask for confirmation before executing any changes.

---

### SOP-003: Hardening AWS Assets

**Purpose:** Scan S3 buckets, EC2 instances, or IAM users for misconfigurations and apply fixes.

**Who:** ISSO, System Administrator

**Steps:**

1. Open SLyK-53 in the Bedrock Console
2. Type: `Scan my S3 buckets for hardening issues`
3. Review the findings — each bucket shows specific issues (encryption, versioning, public access)
4. To apply fixes: `Apply the S3 hardening fixes`
5. SLyK lists what it will change and asks for confirmation
6. Confirm to proceed
7. SLyK applies fixes and reports results

**Supported asset types:**
- `Harden my S3 buckets` — checks encryption, versioning, public access block, logging
- `Harden my EC2 instances` — checks IMDSv2, public IP, IAM role
- `Harden my IAM users` — checks MFA, access key age

---

### SOP-004: Responding to a Security Alert

**Purpose:** Triage a CRITICAL or HIGH Security Hub finding.

**Who:** ISSO, Incident Response Team

**Automatic flow (no action needed):**
1. Security Hub detects a CRITICAL/HIGH finding
2. EventBridge triggers slyk-alert-triage Lambda within seconds
3. Lambda analyzes the finding, generates remediation, calls Bedrock for AI risk assessment
4. SNS sends an email to subscribed ISSOs with the full analysis
5. ISSO reviews the email and decides whether to act

**Manual triage:**
1. Open SLyK-53 in the Bedrock Console
2. Type: `Triage my security alerts`
3. Review findings with severity, NIST mapping, and recommended fixes
4. Type: `Remediate [finding description]` to generate fix scripts

---

### SOP-005: Running a Predefined Runbook

**Purpose:** Execute a multi-step ISSO workflow.

**Who:** ISSO

**Steps:**

1. Open SLyK-53 in the Bedrock Console
2. Type: `Show me available runbooks`
3. SLyK lists all 6 runbooks with descriptions
4. Type: `Run the [runbook name]`
5. SLyK executes each step sequentially and reports progress
6. Results are automatically saved to S3

**Available runbooks:**

| Command | Runbook |
|---|---|
| `Run the monthly compliance check` | NIST assessment + Security Hub + GuardDuty + AI summary |
| `Run the quarterly hardening review` | S3/EC2/IAM scan with AI recommendations |
| `Run incident response triage` | GuardDuty + Security Hub + CloudTrail + AI threat assessment |
| `Check our ATO readiness` | Controls + docs + services + AI readiness assessment |
| `Review our POA&M items` | Failed controls + AI milestone recommendations |
| `Run the system onboarding check` | Baseline + services + AI checklist |

---

### SOP-006: Subscribing to Alerts

**Purpose:** Receive email notifications when CRITICAL/HIGH findings are detected.

**Who:** ISSO, Security Manager

**Steps:**

1. Open **CloudShell** in the AWS Console
2. Run:
   ```
   aws sns subscribe \
       --topic-arn arn:aws:sns:us-east-1:656443597515:SLyK-53-Security-Alerts \
       --protocol email \
       --notification-endpoint your.email@noaa.gov
   ```
3. Check your email for a confirmation link from AWS
4. Click **Confirm subscription**
5. You will now receive alerts whenever a CRITICAL/HIGH finding is detected

**To unsubscribe:**
```
aws sns unsubscribe --subscription-arn [your-subscription-arn]
```

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 8. How to Share SLyK-53 with ISSOs

### 8.1 Prerequisites

SLyK-53 requires **no additional setup** for end users. Any person with AWS Console access can use it immediately.

**What users need:**
- An AWS Console login (IAM user or SSO) — they already have this
- Permission to access Amazon Bedrock in the Console

**What users do NOT need:**
- A separate account or API key
- Any software installed
- Training on Python, CLI, or infrastructure

### 8.2 Sharing Instructions

**Step 1: Send this to your ISSOs:**

> **Subject: SLyK-53 Security Assistant — Now Available**
>
> SLyK-53 is an AI-powered security assistant available in the AWS Console. You can use it to:
> - Assess NIST 800-53 compliance
> - Get remediation scripts for failed controls
> - Harden S3 buckets, EC2 instances, and IAM users
> - Triage Security Hub alerts
> - Run predefined compliance runbooks
>
> **How to access:**
> 1. Log into the AWS Console
> 2. Go to **Amazon Bedrock** → **Agents**
> 3. Click **SLyK-53-Security-Assistant**
> 4. Click **Test** in the right panel
> 5. Type any command in plain English
>
> **Try these:**
> - "Assess my NIST 800-53 compliance"
> - "Harden all my S3 buckets"
> - "Show me available runbooks"
> - "Run the monthly compliance check"
>
> **Subscribe to security alerts:**
> Run in CloudShell:
> ```
> aws sns subscribe --topic-arn arn:aws:sns:us-east-1:656443597515:SLyK-53-Security-Alerts --protocol email --notification-endpoint your.email@noaa.gov
> ```
>
> No installation, no separate login, no setup required.

**Step 2: Add a Console bookmark (optional):**

ISSOs can bookmark this URL for quick access:
```
https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/agents/WCHOG8B8WDR
```

**Step 3: Set up a shared SNS distribution:**

For team-wide alerts, create an email list and subscribe it:
```bash
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:656443597515:SLyK-53-Security-Alerts \
    --protocol email \
    --notification-endpoint sae-team@noaa.gov
```

### 8.3 Access Control

| Role | What They Can Do | How to Grant |
|---|---|---|
| **ISSO** | Run assessments, view findings, generate remediation, execute runbooks | AWS Console access + Bedrock read |
| **Security Engineer** | Everything an ISSO can do + execute hardening fixes | Console access + Bedrock read |
| **Security Manager** | View results, run reports, receive alerts | Console access + SNS subscription |
| **Auditor** | View runbook results and assessment history in S3 | S3 read access to saelarallpurpose/slyk/ |

### 8.4 Restricting Access (if needed)

To prevent specific users from using SLyK, add a deny policy:

```json
{
    "Effect": "Deny",
    "Action": "bedrock:InvokeAgent",
    "Resource": "arn:aws:bedrock:us-east-1:656443597515:agent/WCHOG8B8WDR"
}
```

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 9. Runbook Execution Guide

### 9.1 Monthly Compliance Assessment

**When:** First Monday of each month

**Command:** `Run the monthly compliance check`

**Steps executed automatically:**

| Step | Action | Services |
|---|---|---|
| 1 | NIST 800-53 control assessment | IAM, EC2, S3, CloudTrail |
| 2 | Security Hub finding import (CRITICAL/HIGH) | Security Hub |
| 3 | GuardDuty threat detection status | GuardDuty |
| 4 | AI executive summary generation | Bedrock |
| 5 | Save report to S3 | S3 |

**Output:** Executive summary with pass/fail counts, critical findings, and recommended actions.

**Saved to:** `s3://saelarallpurpose/slyk/runbook_results/monthly_compliance_[timestamp].json`

### 9.2 Quarterly Hardening Review

**When:** First week of each quarter

**Command:** `Run the quarterly hardening review`

**Steps:** S3 hardening scan → EC2 hardening scan → IAM hardening scan → AI recommendations

**Output:** Prioritized remediation plan with specific fixes per asset.

### 9.3 Incident Response Triage

**When:** On-demand or when alerted

**Command:** `Run incident response triage`

**Steps:** GuardDuty high-severity check → Security Hub critical scan → CloudTrail anomaly check (24h) → AI threat assessment

**Output:** Threat level (Critical/High/Medium/Low), recommended containment actions, affected resources.

### 9.4 ATO Readiness Check

**When:** Before scheduled security assessments

**Command:** `Check our ATO readiness`

**Steps:** Control coverage assessment → Documentation inventory → Security services verification → AI readiness assessment

**Output:** Readiness level, gaps to close, estimated remediation effort.

### 9.5 POA&M Review

**When:** Monthly

**Command:** `Review our POA&M items`

**Steps:** Scan currently failing controls → AI-generated milestone dates, priorities, and resource estimates

**Output:** Structured POA&M with weakness descriptions and recommended timelines.

### 9.6 New System Onboarding

**When:** Per new system

**Command:** `Run the system onboarding check`

**Steps:** Account security baseline → Required services check → AI onboarding checklist

**Output:** Prioritized checklist of what must be completed before assessment.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 10. Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| "I do not have access to the AWS Account ID" | Action groups not connected | Re-run the action group creation commands (see deployment guide) |
| Agent says "I cannot perform assessments" | Lambda functions not wired to agent | Verify action groups exist in Bedrock Console |
| "AccessDeniedException" in agent response | Lambda role missing permissions | Check SLyK-Lambda-Role has ReadOnlyAccess |
| No email alerts received | Not subscribed to SNS | Run `aws sns subscribe` command per SOP-006 |
| Agent not responding | Agent not prepared | Run `aws bedrock-agent prepare-agent --agent-id WCHOG8B8WDR` |
| Lambda timeout | Assessment taking too long | Increase Lambda timeout in Console (default 300s) |
| "Model not available" | Primary model not enabled | SLyK auto-falls through 9 models; enable at least one in Bedrock Console |

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 11. References

- SLyK-53 White Paper: `GRC/SLyK_53_White_Paper.md`
- SLyK-53 Required Permissions: `GRC/SLyK_53_Required_Permissions.md`
- SLyK-53 Implementation Guide: `GRC/SLyK_53_Implementation.md`
- Amazon Bedrock Agents: https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
- Amazon EventBridge: https://docs.aws.amazon.com/eventbridge/latest/userguide/
- NIST SP 800-53 Rev 5: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- GRCP Platform Repository: https://github.com/iperry5224/TestZippr
