# SAELAR & SOPRA — Consolidated Team Briefing

### Security Assessment & ISSO Automation Platform
**Prepared by:** SOPSAEL Development Team  
**Date:** February 22, 2026  
**Classification:** Internal Use Only

---

## Executive Overview

**SAELAR** (Security Assessment Engine for Live AWS Resources) and **SOPRA** (SAE On-Premise Risk Assessment) form an integrated platform for automated security assessment and Governance, Risk & Compliance (GRC) workflow automation. Together they address the full cycle from **live AWS assessment** to **ATO-ready documentation and remediation**.

| Component | Role | Key Deliverable |
|-----------|------|-----------------|
| **SAELAR** | Automated NIST 800-53 assessment of live AWS resources | Real-time control pass/fail status, risk scores, evidence |
| **SOPRA** | ISSO workflow automation with 13 AI capabilities | POA&Ms, risk acceptances, SSP narratives, remediation scripts |

This document consolidates technical and executive briefing materials for team distribution.

---

# Part 1: SAELAR — Automated AWS Assessment

## What SAELAR Does

SAELAR-53 performs automated NIST 800-53 Rev 5 security controls assessment against **live AWS resources**. It queries AWS APIs in real time to evaluate configuration state (e.g., CloudTrail enabled, IAM password policy, S3 encryption, GuardDuty status) and produces pass/fail results, risk scores, and audit-ready documentation.

Unlike static snapshots or manual checklists, SAELAR provides accurate, up-to-date security posture for continuous monitoring and ATO preparation.

---

## SAELAR Team Q&A

### Q1: Mapping of APIs and mechanisms used to retrieve each piece of data

See the **Data Source Crosswalk** table below.

### Q2: How does SAELAR align with NIST SP 800-53A Rev 5?

SAELAR aligns primarily through the **Examine** method. It inspects AWS configuration and state via APIs to assess control implementation. It does **not** perform **Interview** (personnel discussions) or active **Test** (e.g., penetration tests). See **800-53A Alignment** below.

---

## Data Source Crosswalk

| Data / Capability | API or Mechanism | AWS Service / Source |
|-------------------|------------------|----------------------|
| Account identity & credentials | `sts.get_caller_identity()` | AWS STS |
| IAM users, policies, MFA | `iam.list_users()`, `iam.list_access_keys()`, `iam.get_policy_version()`, `iam.list_mfa_devices()`, `iam.get_login_profile()`, `iam.get_account_password_policy()` | AWS IAM |
| Access keys last used | `iam.get_access_key_last_used()` | AWS IAM |
| S3 buckets, encryption, policies | `s3.list_buckets()`, `s3.get_bucket_encryption()`, `s3.get_public_access_block()`, `s3.get_bucket_policy()`, `s3.get_bucket_lifecycle_configuration()` | AWS S3 |
| EC2 instances, VPCs, security groups, snapshots | `ec2.describe_instances()`, `ec2.describe_vpcs()`, `ec2.describe_security_groups()`, `ec2.describe_flow_logs()`, `ec2.describe_network_acls()`, `ec2.describe_snapshots()`, `ec2.describe_volumes()`, `ec2.get_ebs_encryption_by_default()` | AWS EC2 |
| CloudTrail trails & status | `cloudtrail.describe_trails()`, `cloudtrail.get_trail_status()`, `cloudtrail.get_event_selectors()` | AWS CloudTrail |
| CloudWatch alarms | `cloudwatch.describe_alarms()` | AWS CloudWatch |
| CloudWatch Logs retention | `logs.describe_log_groups()` | AWS CloudWatch Logs |
| AWS Config recorders & rules | `config.describe_configuration_recorders()`, `config.describe_config_rules()`, `config.get_compliance_details_by_config_rule()`, `config.get_discovered_resource_counts()` | AWS Config |
| Security Hub findings & standards | `securityhub.describe_hub()`, `securityhub.get_enabled_standards()`, `securityhub.get_findings()` | AWS Security Hub |
| GuardDuty detectors & findings | `guardduty.list_detectors()`, `guardduty.get_findings_statistics()`, `guardduty.list_findings()` | AWS GuardDuty |
| Inspector vulnerability findings | `inspector2.list_finding_aggregations()`, `inspector2.list_findings()` | AWS Inspector v2 |
| Macie findings | `macie2.*` (if used) | AWS Macie |
| KMS keys & rotation | `kms.list_keys()`, `kms.describe_key()`, `kms.get_key_rotation_status()` | AWS KMS |
| Secrets Manager | `secretsmanager.list_secrets()` | AWS Secrets Manager |
| RDS instances | `rds.describe_db_instances()` | AWS RDS |
| Backup plans | `backup.list_backup_plans()` | AWS Backup |
| Load balancers & listeners | `elbv2.describe_load_balancers()`, `elbv2.describe_listeners()` | AWS ELB v2 |
| ACM certificates | `acm.list_certificates()` | AWS Certificate Manager |
| WAF policies | `wafv2.*` | AWS WAF v2 |
| CodePipeline, CodeBuild | `codepipeline.list_pipelines()`, `codebuild.list_projects()` | AWS CodePipeline, CodeBuild |
| Lambda functions | `lambda.list_functions()` | AWS Lambda |
| SSM associations, patch baselines | `ssm.list_associations()`, `ssm.describe_patch_baselines()`, `ssm.list_compliance_summaries()` | AWS Systems Manager |
| SNS topics | `sns.list_topics()` | AWS SNS |
| CISA Known Exploited Vulnerabilities (KEV) | HTTP GET to CISA KEV Catalog | CISA (external) |
| AI remediation suggestions | `bedrock-runtime.InvokeModel()` | AWS Bedrock |
| Report upload / storage | `s3.put_object()`, `s3.list_objects_v2()`, `s3.get_object()` | AWS S3 |

---

## NIST SP 800-53A Rev 5 Alignment

| Assessment Method | Description | SAELAR Support |
|-------------------|-------------|----------------|
| **Examine** | Review documentation, design specifications, and mechanism behavior | **Primary.** SAELAR uses AWS APIs to examine configuration state. This maps to examining "object evidence" per 800-53A. |
| **Interview** | Discuss with personnel responsible for the control | **Not supported.** SAELAR is automated and does not conduct interviews. |
| **Test** | Execute mechanisms or simulate attacks | **Limited.** SAELAR verifies services are enabled and configured but does not run active tests (e.g., exploit attempts, penetration tests). |

**Summary:** SAELAR performs automated **examine**-based assessments aligned with NIST 800-53A. It is suitable for continuous monitoring and configuration review. For full 800-53A compliance, organizations should supplement SAELAR with **interview** and **test** activities conducted separately.

---

# Part 2: SOPRA — ISSO Workflow Automation with AI

## The Problem

Information System Security Officers (ISSOs) spend **60–70% of their time** on repetitive, document-heavy tasks: writing POA&M milestones, drafting risk acceptance justifications, classifying controls, mapping findings to frameworks, and preparing approval packages.

For a system with 200 security controls across 20 assessment categories:

| Manual Task | Estimated Manual Time | Frequency |
|-------------|----------------------|-----------|
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

SOPRA integrates **13 distinct AI capabilities** powered by AWS Bedrock that automate the most time-consuming ISSO tasks while maintaining full human oversight and auditability.

Every AI feature:
- Operates with a **single button click**
- Produces **auditor-ready output** using formal RMF/ATO language
- Tags all AI-generated content with a **visible 🤖 badge** for transparency
- **Falls back to deterministic templates** when AI is unavailable — zero downtime
- Sends **only aggregate assessment data** to AI — no PII, no raw evidence, no classified content

---

## AI Feature Catalog

### 1. AI-Powered POA&M Generation
One click generates complete Plan of Action & Milestones entries with smart milestones, severity-calibrated due dates, and role-specific responsible parties. **Time saved: 4–6 hours per cycle.**

### 2. AI-Drafted Risk Acceptance Justifications
Generates AO-ready risk acceptance packages with operational justifications, compensating controls, and residual risk assessments. **Time saved: 15–25 minutes per acceptance.**

### 3. AI Evidence Sufficiency Analysis
Reviews each evidence artifact against its mapped control and assesses sufficiency (Yes/Partial/No) with improvement recommendations. **Time saved: 6–10 hours per audit prep.**

### 4. AI Control Inheritance Auto-Classification
Classifies all 200 controls as Inherited, Common, or System-Specific with rationale. **Time saved: 4–6 hours per boundary review.**

### 5. AI STIG-to-SOPRA Auto-Mapping
Maps DISA STIG and CIS Benchmark findings to SOPRA controls with confidence scores. **Time saved: 2–3 hours per STIG import.**

### 6. AI Incident-to-Finding NLP Correlation
Correlates security incidents to failed controls with relevance scores and explanations. **Time saved: 20–40 minutes per incident.**

### 7. AI Natural Language Crosswalk Queries
Plain-English questions about SOPRA, NIST 800-53, and CIS Controls v8 with immediate answers. **Time saved: 15–25 minutes per query.**

### 8. AI-Written SSP Control Implementation Narratives
Generates all 200 control narratives in formal RMF language for the SSP .docx. **Time saved: 150–300+ hours per ATO cycle.**

### 9. AI Risk-Based Assessment Schedule Optimization
Recommends risk-proportionate reassessment frequencies per NIST SP 800-137. **Time saved: 2–3 hours per quarterly review.**

### 10. AI Approval Package Summary Drafting
AO-ready approval summaries for POA&M closures, risk acceptances, SSP approvals. **Time saved: 15–25 minutes per approval.**

### 11. AI Chat Assistant ("Chad") — Risk Analysis & Remediation
Conversational AI that calculates risk scores, generates PowerShell remediation scripts, analyzes attack chains, and provides hardening advice. **Replaces hours of manual research per remediation task.**

### 12. AI Remediation Plans & Attack Chain Detection
Detailed remediation plans, multi-control attack chain detection, validation scripts. **Time saved: 8–15 hours per remediation cycle.**

### 13. AI Automated Ticket Generation
Pre-filled ServiceNow or Jira tickets from failed findings with severity-mapped priority. **Time saved: 2–4 hours per assessment.**

---

## Total Impact (SOPRA AI)

| Metric | Value |
|--------|-------|
| **Total ISSO hours saved per ATO cycle** | ~360 hours |
| **Percentage reduction in manual effort** | ~90% |
| **Full-time equivalent freed up** | ~2.25 FTEs per ATO cycle |
| **Time to generate full SSP (200 controls)** | Minutes vs. weeks |
| **Assessment categories covered** | 20 (200 controls) |
| **Compliance frameworks mapped** | NIST 800-53 Rev 5 + CIS v8 |
| **FIPS 199 baselines supported** | Low (75) / Moderate (155) / High (200) |

---

## Security & Compliance Assurance

| Concern | Answer |
|---------|--------|
| **"Does AI have access to classified data?"** | No. Only aggregate assessment metrics (pass/fail counts, control IDs) are sent to AI. No PII, no evidence files, no classified content. |
| **"What if AI is wrong?"** | Every AI output requires human review before action. All AI-generated items are tagged with 🤖 badges for auditor transparency. |
| **"What if AI is unavailable?"** | Every feature has a deterministic fallback. If AWS Bedrock is unreachable, SOPRA generates template-based outputs. Zero functionality is lost. |
| **"Does this meet RMF requirements?"** | SOPRA outputs are formatted to NIST RMF standards. AI-generated SSP narratives use formal ATO language. |
| **"Is the AI auditable?"** | Yes. AI-generated vs. human-written content is distinguishable via badges. Full audit trail of approvals. |
| **"Can this run air-gapped?"** | Yes. SOPRA runs fully on-premise. AI features are the only optional network dependency. |
| **"What about FedRAMP?"** | AWS Bedrock is FedRAMP-authorized. The SOPRA application runs on-premise with no inbound network requirements. |

---

## Implementation Roadmap

| Phase | Timeline | Deliverable |
|-------|----------|-------------|
| **Phase 1: Deploy** | Week 1 | Install SAELAR/SOPRA, configure AWS credentials, run first assessment |
| **Phase 2: Baseline** | Week 2 | Establish FIPS 199 categorization, run full 200-control assessment |
| **Phase 3: ISSO Onboard** | Weeks 3–4 | Train ISSO on AI features, begin POA&M and risk acceptance automation |
| **Phase 4: ATO Prep** | Weeks 5–8 | Generate AI-assisted SSP, complete evidence collection, prepare approval packages |
| **Phase 5: Continuous** | Ongoing | AI-optimized assessment scheduling, continuous monitoring, incident correlation |

---

## Bottom Line

**SAELAR** provides real-time, automated NIST 800-53 assessment of live AWS resources.  
**SOPRA** transforms the ISSO role from document author to security decision-maker through 13 AI capabilities.

Together: **One platform. 200 controls. ~360 hours saved per ATO cycle.**

### SAELAR vs. AWS Native Tools — Comparative Analysis

| Dimension | AWS Native Tools (Config, Security Hub, Inspector, Audit Manager) | SAELAR | Time & Cost Advantage |
|-----------|-------------------------------------------------------------------|--------|------------------------|
| **Assessment framework** | CIS, AWS Foundational Best Practices — requires manual NIST 800-53 mapping | Native NIST 800-53 Rev 5 — direct control mapping | Saves 20–40 hrs mapping findings to NIST controls |
| **Tool integration** | 4–5 separate consoles (Config, Security Hub, Inspector, Audit Manager, Trusted Advisor) | Single platform — one assessment, one dashboard | Saves 10–15 hrs per cycle consolidating findings |
| **ATO deliverables** | Evidence collection only — ISSO manually writes SSP, POA&M, risk acceptances | Auto-generates SSP narratives, POA&M entries, risk acceptance drafts | Saves 200–360 hrs (see SOPRA AI impact) |
| **Setup & configuration** | Multiple services to enable, cross-account setup, framework selection per service | Single credential setup, select control families, run assessment | Saves 8–16 hrs initial setup; 2–4 hrs per new account |
| **Ongoing monitoring** | Custom dashboards, multiple alert streams, manual correlation | Unified risk score, control-family view, continuous monitoring | Saves 5–10 hrs/month on status reporting |
| **Licensing & operational cost** | Config + Security Hub + Inspector + Audit Manager fees; multiple data scans | Leverages same AWS APIs — no duplicate scan costs; runs on-premise | Reduces tool sprawl; lower total cost of ownership |

**Summary:** SAELAR consolidates what AWS native tools do separately into one NIST 800-53–focused workflow. Combined with SOPRA AI, expect **250–400+ hours saved per ATO cycle** versus using AWS native tools alone, plus reduced licensing and operational overhead.

---

*SOPSAEL — SAELAR + SOPRA Integrated Platform*  
*For questions or demonstration requests, contact the development team.*
