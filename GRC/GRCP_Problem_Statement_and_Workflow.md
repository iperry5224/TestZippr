# GRCP Agentic AI Solution — Problem Statement and Proposed Workflow

## U.S. Department of Commerce (DOC) | NOAA | NESDIS
### Office of Satellite and Product Operations (OSPO) — CyberSecurity Division (CSD)

**Version:** 1.0
**Date:** April 2026
**Prepared by:** SAE Team

---

## 1. Problem Statement

The NOAA/NESDIS System 5065 environment requires continuous security compliance assessment, remediation, and asset hardening across its AWS footprint. Today, this process is fragmented:

- **Security control compliance** is assessed manually or through periodic scans, producing point-in-time snapshots that become stale within days. ISSOs must cross-reference NIST 800-53 controls against AWS service configurations by hand, leading to inconsistent results and audit gaps.

- **Security control remediation** relies on tribal knowledge. When a control fails, there is no standardized, AI-assisted workflow to generate remediation scripts, track progress, or verify the fix. Remediation steps are documented in spreadsheets or email threads that are difficult to audit.

- **Asset hardening** (EC2, S3, RDS, IAM, etc.) is reactive rather than proactive. Misconfigurations are discovered through Security Hub findings or external audits after they occur, rather than prevented through continuous posture enforcement. There is no integrated tool that detects a misconfiguration, explains the risk, generates the fix, and applies it — within the same workflow.

- **Tool fragmentation** compounds the problem. The team currently uses SAELAR and SOPRA as standalone Streamlit applications accessed via separate URLs. While these tools provide significant capability, they operate outside the AWS Console and require separate navigation, creating workflow friction for engineers who spend their day in the Console.

**The result:** compliance gaps persist longer than necessary, remediation is slower than it should be, and hardening is inconsistent across assets — all because the tools exist outside the engineer's primary workspace.

---

## 2. Requirements

Based on the stated goals, the solution must satisfy these requirements:

| # | Requirement | Priority |
|---|---|---|
| R1 | Provide AI-assisted security control compliance assessment against NIST 800-53 Rev 5 for AWS resources | Must Have |
| R2 | Generate actionable remediation scripts (AWS CLI, CloudFormation, Terraform) for failed controls | Must Have |
| R3 | Perform automated asset hardening checks and provide one-click fix recommendations for EC2, S3, IAM, RDS, and other AWS services | Must Have |
| R4 | Integrate into the AWS Console via a clickable link — no new login, no new infrastructure | Must Have |
| R5 | Use existing AWS credentials (IAM role, SSO) — no separate authentication | Must Have |
| R6 | Leverage Agentic AI to orchestrate multi-step assessment, remediation, and hardening workflows autonomously | Should Have |
| R7 | Maintain audit trail of all assessments, remediations, and hardening actions | Should Have |
| R8 | Support the SAELAR/SOPRA feature set as the baseline capability | Must Have |
| R9 | Keep all data within the AWS boundary (no external API calls for sensitive data) | Must Have |

---

## 3. Current State vs. Proposed State

| Aspect | Current State (SAELAR/SOPRA) | Proposed State (GRCP Agentic AI) |
|---|---|---|
| **Access** | Separate URL (https://nih-saelar...:4443) | Clickable link inside AWS Console |
| **Authentication** | Separate login (SAELAR auth) | AWS Console session (IAM/SSO) — no additional login |
| **Infrastructure** | Dedicated EC2 (GRC_Titan) running Streamlit | AWS-managed services (Bedrock Agent, Lambda, Systems Manager) — no EC2 to maintain |
| **Compliance Assessment** | SAELAR scans 25+ services, 36+ controls | Bedrock Agent invokes same assessment logic via Lambda action groups |
| **Remediation** | Chad AI generates scripts; manual copy-paste execution | Agent generates AND optionally executes remediation via SSM Run Command |
| **Hardening** | Manual — user interprets findings and applies fixes | Agent identifies misconfiguration, explains risk, generates fix, offers one-click apply |
| **AI Engine** | Bedrock (Titan, Llama, Mistral) via API calls | Bedrock Agent with orchestration, memory, and action groups |
| **State / Memory** | Streamlit session state (lost on refresh) | Bedrock Agent memory + DynamoDB persistent state |
| **Audit Trail** | S3 JSON files | CloudTrail + DynamoDB + S3 (immutable) |

---

## 4. Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AWS Console (System 5065)                   │
│                                                                   │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  GRCP Widget (CloudFormation Custom Resource / Console    │   │
│   │  Extension / Service Catalog Link)                        │   │
│   │                                                            │   │
│   │  [🛡️ Open GRCP Security Assistant]  ← clickable link     │   │
│   └──────────────┬───────────────────────────────────────────┘   │
│                   │                                               │
│                   ▼                                               │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  Amazon Bedrock Agent (GRCP Agent)                        │   │
│   │  - Orchestrates multi-step security workflows             │   │
│   │  - Maintains conversation memory                          │   │
│   │  - Routes to appropriate action group                     │   │
│   └──────┬──────────┬──────────┬─────────────────────────────┘   │
│          │          │          │                                   │
│          ▼          ▼          ▼                                   │
│   ┌──────────┐┌──────────┐┌──────────┐                           │
│   │ Action   ││ Action   ││ Action   │                           │
│   │ Group 1  ││ Group 2  ││ Group 3  │                           │
│   │          ││          ││          │                           │
│   │ Assess   ││ Remediate││ Harden   │                           │
│   └────┬─────┘└────┬─────┘└────┬─────┘                           │
│        │           │           │                                   │
│        ▼           ▼           ▼                                   │
│   ┌──────────┐┌──────────┐┌──────────┐                           │
│   │ Lambda   ││ Lambda   ││ Lambda   │                           │
│   │          ││          ││          │                           │
│   │ NIST     ││ SSM Run  ││ Config   │                           │
│   │ 800-53   ││ Command  ││ Rules +  │                           │
│   │ Assessor ││ Executor ││ Auto-    │                           │
│   │          ││          ││ Remediate│                           │
│   └────┬─────┘└────┬─────┘└────┬─────┘                           │
│        │           │           │                                   │
│        ▼           ▼           ▼                                   │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  AWS Services                                              │   │
│   │  IAM, EC2, S3, KMS, CloudTrail, GuardDuty, Security Hub, │   │
│   │  Inspector, Config, Systems Manager, Macie, WAF, RDS...  │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  Data Layer                                                │   │
│   │  S3 (assessments, docs) │ DynamoDB (state) │ CloudTrail   │   │
│   └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Console Integration Options

The requirement states "clickable link in the AWS Console, no new login or infrastructure." Here are the viable approaches:

| Option | How It Works | Complexity | User Experience |
|---|---|---|---|
| **A. AWS Chatbot + Bedrock Agent** | User opens AWS Chatbot in Console, types security questions. Chatbot routes to Bedrock Agent which executes action groups. | Low | Chat-based — natural language in Console sidebar |
| **B. Service Catalog Self-Service Action** | Create a Service Catalog product with SSM Automation documents. User clicks "Launch" in Service Catalog to trigger assessments. | Medium | Click-to-run — wizard-style in Console |
| **C. Systems Manager OpsCenter + Runbooks** | Create SSM Automation runbooks for each workflow. Link from OpsCenter as operational actions. | Medium | Integrated into existing Ops workflow |
| **D. CloudWatch Dashboard Custom Widget** | Embed a custom Lambda-backed widget in a CloudWatch Dashboard showing compliance posture with action buttons. | Medium | Dashboard with live metrics and action buttons |
| **E. Bedrock Agent + API Gateway + Console Bookmark** | Bedrock Agent fronted by API Gateway, accessed via a Console bookmark or Service Catalog link opening a lightweight React UI. | High | Full GUI — closest to current SAELAR experience |

**Recommended approach: Option A (AWS Chatbot) for immediate value + Option D (CloudWatch Dashboard) for executive visibility.**

---

## 6. Proposed Workflow

### Workflow 1: Security Control Compliance Assessment

```
User (in AWS Console):
  "Assess my NIST 800-53 compliance for AC and IA control families"
       │
       ▼
Bedrock Agent (GRCP Agent):
  1. Parses intent → routes to ASSESS action group
  2. Invokes Lambda: NIST 800-53 Assessor
       │
       ▼
Lambda (assess_controls):
  - Calls IAM, STS, EC2, S3, KMS, CloudTrail, etc.
  - Evaluates 36+ controls
  - Returns pass/fail/warning for each control
       │
       ▼
Bedrock Agent:
  3. Receives results
  4. Generates natural language summary:
     "I assessed 12 controls across AC and IA families.
      ✅ 8 passed | ⚠️ 2 warnings | ❌ 2 failed
      
      Failed controls:
      - AC-2: 3 IAM users without MFA
      - IA-5: 2 access keys older than 90 days
      
      Would you like me to generate remediation scripts?"
  5. Stores results in S3 + DynamoDB
  6. Logs to CloudTrail
```

### Workflow 2: Security Control Remediation

```
User:
  "Yes, fix the AC-2 MFA issue"
       │
       ▼
Bedrock Agent:
  1. Retrieves AC-2 finding details from memory
  2. Routes to REMEDIATE action group
  3. Invokes Lambda: generate_remediation
       │
       ▼
Lambda (generate_remediation):
  - Identifies affected IAM users without MFA
  - Generates AWS CLI script:
    aws iam create-virtual-mfa-device ...
    aws iam enable-mfa-device ...
  - Returns script + explanation
       │
       ▼
Bedrock Agent:
  4. Presents remediation plan:
     "Here's the remediation for AC-2 (Account Management):
      
      3 users need MFA enabled:
      - user1@noaa.gov
      - user2@noaa.gov  
      - svc-account-01
      
      Option A: I can generate the CLI commands for you to review and run
      Option B: I can execute via SSM Run Command (requires approval)
      
      Which would you prefer?"
  5. If Option B selected → invokes SSM Run Command
  6. Logs remediation action to audit trail
```

### Workflow 3: Asset Hardening

```
User:
  "Harden all my S3 buckets"
       │
       ▼
Bedrock Agent:
  1. Routes to HARDEN action group
  2. Invokes Lambda: harden_assets
       │
       ▼
Lambda (harden_assets):
  - Lists all S3 buckets
  - Checks each bucket for:
    □ Public access blocked?
    □ Default encryption enabled?
    □ Versioning enabled?
    □ Access logging enabled?
    □ Lifecycle policy configured?
    □ Object Lock enabled?
  - Returns findings per bucket
       │
       ▼
Bedrock Agent:
  3. Presents hardening report:
     "Scanned 8 S3 buckets. 3 need hardening:
      
      🔴 saelarallpurpose:
         - Public access: ✅ Blocked
         - Encryption: ❌ Not enabled → Fix: Enable SSE-S3
         - Versioning: ❌ Disabled → Fix: Enable versioning
      
      🟡 codepipeline-us-east-1-724312423486:
         - Access logging: ❌ Not enabled → Fix: Enable server access logging
      
      🟡 config-bucket-5065:
         - Lifecycle policy: ❌ Missing → Fix: Add 90-day transition to Glacier
      
      I can apply these fixes now. Shall I proceed?"
  4. If approved → executes fixes via Lambda
  5. Re-scans to verify → confirms hardening applied
  6. Generates hardening report → saves to S3
```

---

## 7. Action Group Definitions

| Action Group | Purpose | Lambda Functions | AWS Services Used |
|---|---|---|---|
| **ASSESS** | Run NIST 800-53 compliance assessments | `grcp-assess-controls`, `grcp-import-securityhub`, `grcp-check-kev` | IAM, EC2, S3, KMS, CloudTrail, GuardDuty, Security Hub, Inspector, Config, Macie |
| **REMEDIATE** | Generate and execute remediation scripts | `grcp-generate-remediation`, `grcp-execute-ssm`, `grcp-verify-fix` | SSM, Lambda, IAM, S3, EC2 |
| **HARDEN** | Scan and harden AWS assets | `grcp-harden-s3`, `grcp-harden-ec2`, `grcp-harden-iam`, `grcp-harden-rds` | S3, EC2, IAM, RDS, KMS, Config |
| **REPORT** | Generate compliance documents | `grcp-generate-ssp`, `grcp-generate-poam`, `grcp-generate-rar` | S3 (storage), Bedrock (content generation) |
| **QUERY** | Answer security questions using RAG | `grcp-query-kb` | Bedrock Knowledge Base, S3 |

---

## 8. Mapping to SAELAR/SOPRA Capabilities

Every existing SAELAR/SOPRA capability maps to the new architecture:

| Current Capability | Current Tool | GRCP Agent Equivalent |
|---|---|---|
| NIST 800-53 assessment | SAELAR (nist_800_53_rev5_full.py) | ASSESS action group → Lambda |
| Security Hub ingestion | SAELAR (import_security_hub_findings) | ASSESS action group → Lambda |
| CISA BOD 22-01 / KEV | SAELAR (cisa_kev_checker.py) | ASSESS action group → Lambda |
| Chad AI chat | SAELAR (call_ai / Bedrock) | Bedrock Agent native chat |
| SSP generation | SAELAR (wordy.py / ssp_generator.py) | REPORT action group → Lambda |
| POA&M generation | SAELAR (wordy.py) | REPORT action group → Lambda |
| RAR generation | SAELAR (wordy.py) | REPORT action group → Lambda |
| Risk scoring | SAELAR (risk_score_calculator.py) | ASSESS action group → Lambda |
| MITRE ATT&CK mapping | SAELAR (nist_dashboard.py) | ASSESS action group → Lambda |
| Threat modeling | SAELAR (nist_dashboard.py) | ASSESS action group → Lambda |
| On-prem CSV assessment | SOPRA (sopra_controls.py) | ASSESS action group (CSV upload variant) |
| STIG import | SOPRA (stig_import.py) | ASSESS action group (STIG variant) |
| Evidence collection | SOPRA (evidence.py) | REPORT action group → S3 |
| Container scanning | BeeKeeper (scanner.py) | HARDEN action group → Lambda + Trivy |
| Knowledge Base / RAG | SAELAR (retrieve_from_knowledge_base) | QUERY action group → Bedrock KB |

---

## 9. Implementation Phases

| Phase | Scope | Duration | Outcome |
|---|---|---|---|
| **Phase 1** | Deploy Bedrock Agent with ASSESS action group (repackage existing assessment code into Lambda) | 3-4 weeks | Compliance assessment via Console chat |
| **Phase 2** | Add REMEDIATE action group with SSM integration | 2-3 weeks | AI-generated remediation with optional auto-apply |
| **Phase 3** | Add HARDEN action group for S3, EC2, IAM | 2-3 weeks | One-command asset hardening |
| **Phase 4** | Add REPORT action group (SSP, POA&M, RAR generation) | 2 weeks | Document generation via chat |
| **Phase 5** | CloudWatch Dashboard with compliance posture widget | 1-2 weeks | Executive visibility in Console |
| **Phase 6** | Knowledge Base RAG integration | 1-2 weeks | Contextual Q&A over stored compliance documents |

---

## 10. What This Means for SAELAR/SOPRA

SAELAR and SOPRA are not being replaced — they are being **repackaged**. The assessment logic, risk scoring, document generation, and AI analysis code remains the same. What changes is the delivery mechanism:

| Aspect | Before | After |
|---|---|---|
| **Runtime** | Streamlit on EC2 | Lambda functions |
| **UI** | Streamlit web app | AWS Console (Chatbot / Dashboard) |
| **AI orchestration** | Custom Python (call_ai) | Bedrock Agent with action groups |
| **State management** | Streamlit session state | DynamoDB + Bedrock Agent memory |
| **Authentication** | Custom (.nist_users.json) | AWS IAM / SSO (Console session) |
| **Infrastructure** | EC2 instance to maintain | Serverless (Lambda, Bedrock, DynamoDB) |
| **Deployment** | CI/CD pipeline → EC2 | CloudFormation / CDK → Lambda + Bedrock |

The team's existing Python code — the assessment engine, the remediation logic, the document generators — becomes the Lambda function payload. The intellectual property and domain expertise built into SAELAR and SOPRA is preserved and enhanced, not discarded.

---

## 11. SAE Team Position

The proposed GRCP Agentic AI solution achieves the stated goal: an AI-driven security tool integrated directly into the AWS Console for System 5065, requiring no new login and no new infrastructure. It builds on the proven assessment, remediation, and hardening capabilities the SAE Team has already developed in SAELAR and SOPRA, repackaging them as Bedrock Agent action groups backed by Lambda functions.

This approach gives the team the best of both worlds: the deep AWS security assessment capabilities we have already built, delivered through the native AWS Console experience the engineers already use every day.
