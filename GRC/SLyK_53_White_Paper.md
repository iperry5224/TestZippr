# Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## U.S. Department of Commerce (DOC)
## National Oceanic and Atmospheric Administration (NOAA)
## National Environmental Satellite Data and Information Service (NESDIS)

---

# SLyK-53: An Agentic AI Approach to Continuous Security Compliance and Asset Hardening in AWS

**White Paper**

CSTA FY26 | Version 1.0

Prepared by SAE Team | April 2026

Office of Satellite and Product Operations (OSPO)

CyberSecurity Division (CSD)

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## Record of Changes/Revision

| Version | Date | Description | Section/Pages Affected | Changes Made By |
|---|---|---|---|---|
| 1.0 | 04/22/2026 | Initial white paper. | All | SAE Team |

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## Table of Contents

1. Executive Summary
2. Problem Statement
3. Background
4. Technical Approach
5. Architecture
6. Core Capabilities
7. ISSO Runbook Suite
8. Proactive Alerting
9. AI Model Strategy
10. Security Considerations
11. Cost Analysis
12. Comparison to Existing Tools
13. Implementation Strategy
14. Conclusion
15. References

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 1. Executive Summary

The SAE Team has developed SLyK-53 (SAE Lightweight Yaml Kit), a serverless, Agentic AI security assistant that integrates directly into the AWS Management Console. SLyK-53 enables Information System Security Officers (ISSOs), security engineers, and system administrators to perform NIST 800-53 compliance assessments, remediate security findings, and harden AWS assets through natural language interaction — without leaving the Console, deploying additional infrastructure, or managing separate credentials.

SLyK-53 is built on Amazon Bedrock Agents, AWS Lambda, and Amazon EventBridge. It represents the next evolution of the SAE Team's GRCP (GRC Platform) toolset, which includes SAELAR-53 and SOPRA. While SAELAR provides a comprehensive, standalone assessment platform, SLyK-53 delivers a lightweight, conversational interface embedded in the engineer's daily workflow — reducing the friction between identifying a security gap and closing it.

SLyK-53 is fully serverless, operates entirely within the AWS boundary, requires no additional infrastructure to maintain, and costs an estimated $16–71 per month to operate.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 2. Problem Statement

Federal agencies operating in AWS face a persistent challenge: the distance between detecting a security issue and resolving it is too great. Today's compliance workflow involves multiple disconnected steps:

1. An ISSO runs a periodic assessment using a standalone tool
2. Findings are exported to spreadsheets or documents
3. Remediation scripts are researched and drafted manually
4. Scripts are transferred to the appropriate system and executed
5. Results are verified by re-running the assessment
6. Documentation is updated to reflect the new state

Each handoff introduces delay, human error, and audit risk. Security Hub generates findings continuously, but teams review them periodically. GuardDuty detects threats in real time, but response relies on human interpretation and manual action. The tools exist in separate consoles, require separate navigation, and produce outputs in incompatible formats.

The result: compliance gaps persist longer than necessary, remediation is slower than it should be, and hardening is inconsistent across assets.

SLyK-53 collapses this workflow into a single conversational interface. An ISSO types "Check my IAM controls" and receives pass/fail results with specific findings. They type "Fix the MFA issue" and receive executable remediation scripts — or approve SLyK to apply the fix directly. The entire cycle — assess, remediate, verify — happens within one session, in one Console, in minutes rather than days.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 3. Background

### 3.1 The GRCP Platform

The SAE Team within the NOAA/NESDIS CyberSecurity Division has developed a family of Governance, Risk, and Compliance (GRC) tools collectively known as GRCP:

| Tool | Purpose | Deployment Model |
|---|---|---|
| **SAELAR-53** | Full-featured NIST 800-53 assessment platform with dashboards, document generation, risk scoring, MITRE ATT&CK mapping, and AI-powered analysis | Streamlit on EC2 |
| **SOPRA** | On-premise and air-gapped risk assessment using CSV/STIG import with zero-touch architecture | Streamlit on EC2 |
| **BeeKeeper** | Container vulnerability scanning with AI-powered remediation | Streamlit on EC2 |
| **SLyK-53** | Console-integrated agentic AI security assistant | Serverless (Lambda + Bedrock) |

SAELAR-53 has been in operation since early FY26, performing live assessments against 25+ AWS services and generating audit-ready compliance documentation. SLyK-53 builds on this foundation by repackaging the core assessment logic into serverless Lambda functions and exposing them through an Agentic AI interface that integrates directly into the AWS Console.

### 3.2 Why Agentic AI

Traditional chatbots respond to individual prompts without context, memory, or the ability to take action. Agentic AI represents a fundamental shift: the agent maintains conversation state, orchestrates multi-step workflows, invokes tools (Lambda functions) to interact with real infrastructure, and makes decisions about which actions to take based on the user's intent.

SLyK-53 leverages Amazon Bedrock Agents to provide this agentic capability. When an ISSO asks SLyK to "run the monthly compliance check," the agent does not merely generate text about compliance — it executes a predefined runbook that calls AWS APIs, aggregates findings from multiple services, generates an AI-powered executive summary, and saves the results to S3 for audit. The agent is doing real work, not producing simulated output.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 4. Technical Approach

SLyK-53 is implemented as a five-component serverless architecture:

**1. Amazon Bedrock Agent** — The conversational orchestrator. Receives natural language input from the user, determines intent, selects the appropriate action group, invokes Lambda functions, and formats the response. Maintains conversation memory across the session.

**2. Lambda Functions (5)** — The execution layer. Each function encapsulates a domain of security operations: assessment, remediation, hardening, alert triage, and runbook execution. Functions use boto3 to make authenticated API calls to AWS services.

**3. Amazon EventBridge** — The proactive trigger. An EventBridge rule monitors Security Hub for CRITICAL and HIGH severity findings. When detected, it automatically invokes the alert triage Lambda, which analyzes the finding, generates remediation, and sends an alert — without any user interaction.

**4. Amazon SNS** — The notification layer. Delivers formatted security alerts to email or Slack when high-risk findings are detected, including AI-generated risk assessments and recommended remediation scripts.

**5. Amazon S3** — The data layer. Stores agent configuration, runbook execution history, and alert triage logs for audit trail and historical analysis.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 5. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Console                                  │
│                                                                       │
│   ISSO / Engineer / Manager                                          │
│   "Assess my compliance"  "Harden my S3 buckets"  "Run IR triage"   │
│                                                                       │
│              ┌────────────────────────────┐                          │
│              │   Amazon Bedrock Agent      │                          │
│              │   SLyK-53                   │                          │
│              │   (9-model succession)      │                          │
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
│   │  AWS Services (Read + Targeted Write)                        │   │
│   │  IAM · EC2 · S3 · KMS · CloudTrail · GuardDuty ·            │   │
│   │  Security Hub · Inspector · Config · Macie · SSM             │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│   ┌─────────────────────┐  ┌──────────────┐  ┌───────────────┐     │
│   │  EventBridge         │  │  SNS          │  │  S3            │     │
│   │  Auto-trigger on     │  │  Email/Slack  │  │  Audit trail   │     │
│   │  CRITICAL/HIGH       │→ │  alerts       │  │  Runbook logs  │     │
│   │  findings            │  │               │  │  Config        │     │
│   └─────────────────────┘  └──────────────┘  └───────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 6. Core Capabilities

### 6.1 NIST 800-53 Compliance Assessment

SLyK-53 programmatically assesses NIST 800-53 Rev 5 controls by making authenticated API calls to AWS services. Each control check evaluates the actual configuration state of the environment — not estimated or self-reported data.

| Control | Check Performed | Services Queried |
|---|---|---|
| AC-2 | IAM users without MFA | IAM |
| AC-6 | Overly permissive policies (Action:* Resource:*) | IAM |
| AU-2 | CloudTrail logging active | CloudTrail |
| IA-2 | Root account MFA | IAM |
| SC-7 | Security groups with unrestricted access | EC2 |
| SC-28 | S3 buckets without default encryption | S3 |
| SI-4 | GuardDuty threat detection enabled | GuardDuty |

Results include pass/fail/warning status, specific findings (e.g., "3 users without MFA: user1, user2, svc-account"), and actionable recommendations.

### 6.2 Security Hub Integration

SLyK-53 imports and analyzes findings from AWS Security Hub, which aggregates detections from:

- Amazon GuardDuty (threat detection)
- Amazon Inspector (vulnerability scanning)
- Amazon Macie (sensitive data discovery)
- IAM Access Analyzer (permission analysis)
- AWS Config (configuration compliance)
- Third-party integrated tools

Each Security Hub finding is mapped to its corresponding NIST 800-53 control family, enabling ISSOs to view findings in compliance context rather than as isolated alerts.

### 6.3 Automated Remediation

For each failed control or Security Hub finding, SLyK-53 generates specific AWS CLI remediation scripts. The remediation engine:

1. Identifies the affected resources by querying the environment
2. Generates targeted scripts (not generic templates)
3. Presents the scripts to the user for review
4. Offers optional execution via AWS Systems Manager
5. Updates the Security Hub finding workflow status after successful remediation

### 6.4 Asset Hardening

SLyK-53 scans S3 buckets, EC2 instances, and IAM users against security baselines and can apply fixes with user approval:

| Asset | Checks | Auto-Fix |
|---|---|---|
| S3 Buckets | Public access block, default encryption, versioning, access logging | Yes |
| EC2 Instances | IMDSv2 enforcement, public IP exposure, IAM role attachment | Partial |
| IAM Users | MFA enabled, access key rotation (>90 days) | Report only |

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 7. ISSO Runbook Suite

SLyK-53 includes six predefined runbooks designed for ISSO workflows. Each runbook orchestrates multiple assessment, analysis, and reporting steps in a single execution.

| Runbook | Description | Audience | Frequency |
|---|---|---|---|
| **Monthly Compliance Assessment** | NIST control checks + Security Hub import + GuardDuty status + AI executive summary | ISSO, Security Manager | Monthly |
| **Quarterly Hardening Review** | S3/EC2/IAM hardening scan with AI-generated remediation recommendations | ISSO, System Admin | Quarterly |
| **Incident Response Triage** | GuardDuty threats + Security Hub critical findings + CloudTrail anomalies + AI threat level assessment | ISSO, IR Team, SOC | On-demand |
| **ATO Readiness Check** | Control coverage + documentation inventory + security services verification + AI readiness assessment | ISSO, Authorizing Official | Pre-assessment |
| **POA&M Review** | Open failed controls scan + AI-generated milestone dates and priority rankings | ISSO | Monthly |
| **New System Onboarding** | Account security baseline + required services check + AI onboarding checklist | ISSO, System Owner | Per new system |

All runbook results are automatically saved to S3 for audit trail and historical trending.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 8. Proactive Alerting

SLyK-53 does not wait for users to ask questions. An EventBridge rule continuously monitors Security Hub for new CRITICAL and HIGH severity findings. When detected:

1. The alert triage Lambda is invoked automatically
2. The finding is analyzed and mapped to a NIST control family
3. Remediation scripts are generated for the specific resource
4. Amazon Bedrock generates an AI risk assessment covering threat level, potential impact, and priority
5. An SNS notification is sent to subscribed ISSOs containing the finding, risk assessment, and remediation scripts
6. The complete triage is logged to S3 for audit

This transforms SLyK-53 from a reactive tool into a continuous security monitoring capability that proactively notifies the team and provides actionable guidance before they even open the Console.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 9. AI Model Strategy

SLyK-53 implements a nine-model succession plan to ensure availability regardless of which foundation models are enabled in the account. The deployment script probes each model at startup and selects the first one that responds.

| Priority | Model | Provider | Characteristics |
|---|---|---|---|
| 1 | Amazon Nova Pro | Amazon | Best reasoning capability |
| 2 | Amazon Nova Lite | Amazon | Fast, capable, lower cost |
| 3 | Amazon Nova Micro | Amazon | Ultra-lightweight, lowest cost |
| 4 | Llama 3.1 70B | Meta | Strong open-weight reasoning |
| 5 | Llama 3.1 8B | Meta | Lightweight open-weight |
| 6 | Mistral Large | Mistral AI | Strong multilingual capability |
| 7 | Mixtral 8x7B | Mistral AI | Good speed/quality balance |
| 8 | Titan Text Express | Amazon | Legacy Amazon model |
| 9 | Titan Text Lite | Amazon | Absolute fallback |

At runtime, if the primary model becomes unavailable, Lambda functions automatically fall through the succession list. This design ensures SLyK-53 remains operational even during model deprecations or access changes.

All models execute within Amazon Bedrock. No data is transmitted outside the AWS boundary.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 10. Security Considerations

### 10.1 Authentication and Authorization

SLyK-53 uses the existing AWS Console IAM session. No additional credentials, API keys, or login pages are introduced. Access to SLyK is governed by the same IAM policies that control Console access.

Lambda functions execute under a dedicated role (SLyK-Lambda-Role) with:
- ReadOnlyAccess for assessment operations
- Scoped write permissions limited to specific hardening actions (e.g., `s3:PutBucketEncryption`, `ec2:ModifyInstanceMetadataOptions`)
- No ability to delete resources, modify IAM policies, or access data plane content

### 10.2 Data Sovereignty

All data remains within the AWS account boundary:
- Assessment results → S3 (same account)
- AI model inference → Amazon Bedrock (same region)
- Alerts → SNS (same account)
- Audit logs → CloudTrail (same account)

No data is transmitted to external services, third-party APIs, or cross-account destinations.

### 10.3 Human-in-the-Loop

SLyK-53 follows a confirm-before-act model for any write operations:
- Hardening fixes are presented as scripts before execution
- The agent asks for explicit approval before applying changes
- Remediation execution is optional — users can copy scripts and run them manually
- EventBridge-triggered alerts generate recommendations but do not auto-remediate

### 10.4 Audit Trail

Every action is logged through multiple channels:
- CloudTrail captures all API calls made by Lambda functions
- Runbook results are saved to S3 with timestamps and full execution details
- Alert triage logs include the finding, AI analysis, and remediation scripts
- Security Hub finding workflow status is updated after remediation

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 11. Cost Analysis

SLyK-53 operates on a fully serverless, pay-per-use model with no fixed infrastructure costs.

| Component | Monthly Estimate | Notes |
|---|---|---|
| Lambda (5 functions) | $5–20 | ~100 invocations/day |
| Bedrock model calls | $10–50 | ~500 invocations/month |
| Bedrock Agent | ~$0 | Per-invocation, minimal cost |
| EventBridge | ~$0 | Per-event, minimal volume |
| SNS | ~$0 | Per-notification |
| S3 (config + audit) | ~$1 | <1 GB stored |
| **Total** | **$16–71/month** | |

### Cost Comparison

| Platform | Monthly Cost | Infrastructure |
|---|---|---|
| SAELAR-53 (EC2) | ~$50 | EC2 t5a.medium (must maintain) |
| SLyK-53 (serverless) | ~$16–71 | Zero infrastructure (fully managed) |
| Paramify (commercial) | ~$2,000–10,000 | Vendor-managed SaaS |
| AWS Security Hub alone | ~$0.0010/check | No remediation, no AI, no runbooks |

SLyK-53 delivers comparable or superior capability to commercial GRC tools at a fraction of the cost, with no licensing fees and no vendor dependency.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 12. Comparison to Existing Tools

### 12.1 SLyK-53 vs SAELAR-53

| Aspect | SAELAR-53 | SLyK-53 |
|---|---|---|
| Interface | Browser (8-tab Streamlit app) | AWS Console (natural language chat) |
| Infrastructure | EC2 instance | Serverless (zero maintenance) |
| Authentication | Separate login | AWS Console session |
| Assessment depth | 36+ controls, 25+ services | 7+ controls (expandable) + Security Hub |
| Document generation | SSP, POA&M, RAR | AI-generated via runbooks |
| Hardening | Manual (copy scripts) | Automated (scan → approve → apply) |
| Proactive alerts | None | EventBridge + SNS |
| Runbooks | None | 6 predefined ISSO workflows |
| Sharing | Share URL, each user logs in | Anyone with Console access |

SLyK-53 does not replace SAELAR-53. SAELAR remains the deep-dive platform for comprehensive assessments and compliance documentation. SLyK provides the fast, conversational interface for daily security operations.

### 12.2 SLyK-53 vs Google Cloud Security Command Center

| Capability | SLyK-53 | GCP SCC |
|---|---|---|
| Cloud target | AWS | GCP (limited AWS via Enterprise tier) |
| AI assistant | Bedrock Agent with action groups | SCC AI features |
| Compliance frameworks | NIST 800-53 | NIST 800-53, CIS, PCI DSS, ISO 27001 |
| Auto-remediation | Yes (with approval) | Partial |
| Proactive alerting | Yes (EventBridge + SNS) | Yes (SCC notifications) |
| ISSO runbooks | Yes (6 predefined) | No |
| Cost | $16–71/month | $15–25/resource/year |
| Data boundary | AWS-native | GCP-native |

### 12.3 SLyK-53 vs Commercial GRC Platforms

| Feature | SLyK-53 | Paramify | Drata |
|---|---|---|---|
| Live infrastructure scanning | Yes | No | Partial |
| AI-powered remediation | Yes | No | No |
| Console integration | Yes (native) | No | No |
| Runbooks | Yes (6) | No | No |
| Proactive alerting | Yes | No | Yes |
| Cost | $16–71/month | $25K–125K/year | $10K–50K/year |
| Licensing | $0 | Per-framework | Per-framework |

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 13. Implementation Strategy

SLyK-53 deploys in a single command execution from AWS CloudShell:

```bash
unzip slyk-53-deploy.zip
cd slyk
python3 deploy_slyk.py
```

The deployment script:

1. Probes Bedrock for available models and selects the best one
2. Creates or reuses IAM roles (SLyK-Lambda-Role, SLyK-Agent-Role)
3. Deploys 5 Lambda functions with assessment, remediation, hardening, triage, and runbook logic
4. Creates a Bedrock Agent with 5 action groups and an OpenAPI schema
5. Creates an EventBridge rule for proactive Security Hub alerting
6. Creates an SNS topic for email/Slack notifications
7. Tests the agent with a sample invocation
8. Saves configuration to S3

Total deployment time: approximately 3 minutes.

### Post-Deployment

1. **Test**: AWS Console → Bedrock → Agents → SLyK-53-Security-Assistant → Test
2. **Subscribe**: `aws sns subscribe --topic-arn <ARN> --protocol email --notification-endpoint your@email.com`
3. **Share**: Send the Bedrock Agent link to team members with Console access

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 14. Conclusion

SLyK-53 represents a new approach to security compliance in federal AWS environments. By embedding an Agentic AI assistant directly into the AWS Console, the SAE Team has eliminated the friction between security assessment and security action. ISSOs no longer need to navigate between tools, translate findings into scripts, or manually track remediation progress. They describe what they need in plain language, and SLyK does the rest.

The tool is serverless, operates entirely within the AWS boundary, costs less than $71 per month, and deploys in three minutes. It builds on the proven assessment logic developed for SAELAR-53 while delivering it through a modern, conversational interface that meets engineers where they already work.

SLyK-53 is not a replacement for comprehensive GRC platforms — it is a force multiplier that makes every ISSO more effective, every assessment faster, and every remediation more consistent.

---

Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## 15. References

- Amazon Bedrock Agents Documentation: https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
- Amazon Bedrock Action Groups: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-action-create.html
- AWS Security Hub: https://docs.aws.amazon.com/securityhub/latest/userguide/
- Amazon EventBridge: https://docs.aws.amazon.com/eventbridge/latest/userguide/
- NIST SP 800-53 Rev 5: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- NIST SP 800-30 Rev 1: https://csrc.nist.gov/publications/detail/sp/800-30/rev-1/final
- CISA Known Exploited Vulnerabilities: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- AWS Well-Architected Security Pillar: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/
