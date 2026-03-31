# SAE Team GRC Platform (SAELAR-53): Capabilities Beyond Multimodal LLMs

Large Language Models — including multimodal variants like GPT-4o, Claude, and Gemini — excel at generating text, analyzing documents, and answering questions. However, they fundamentally cannot perform the following capabilities that SAELAR-53 delivers as an integrated GRC platform.

## Live AWS Infrastructure Assessment

SAELAR executes real-time, authenticated API calls against 25+ AWS services — IAM, EC2, S3, KMS, CloudTrail, GuardDuty, Security Hub, Inspector2, Macie, WAF, RDS, Lambda, Secrets Manager, and others — to programmatically assess the actual state of an environment. It evaluates 36+ individual NIST 800-53 Rev 5 controls across 13 control families by querying live configurations, not by generating assumptions. An LLM can discuss what *should* be checked; SAELAR checks it and returns evidence-backed pass/fail/warning results tied to specific resources.

## Automated Security Hub Finding Ingestion

SAELAR pulls and normalizes findings from AWS Security Hub, which aggregates detections from GuardDuty, Inspector, Macie, IAM Access Analyzer, and third-party tools. It maps these findings to NIST control families and incorporates them into assessment scoring. LLMs have no mechanism to authenticate to AWS, retrieve findings, or maintain a persistent connection to a customer's security data.

## CISA BOD 22-01 Compliance Enforcement

SAELAR integrates the CISA Known Exploited Vulnerabilities (KEV) catalog, cross-references it against the organization's environment, calculates remediation deadlines per BOD 22-01 timelines (6 months for pre-2021 CVEs, 2 weeks for post-2021), and tracks compliance status. This requires both live vulnerability data and organizational context that LLMs do not possess.

## Auditor-Ready Document Generation

SAELAR generates complete, structured DOCX documents — System Security Plans (SSPs), Plans of Action & Milestones (POA&Ms), and Risk Assessment Reports (RARs) — populated with actual assessment data, control implementation status, and system-specific metadata. These are formatted to NIST/FedRAMP/FISMA submission standards with proper section numbering, tables, and document control pages. LLMs can draft *template* language, but cannot populate documents with verified assessment evidence from a live environment.

## Quantitative Risk Scoring

SAELAR implements NIST SP 800-30 risk methodology with calculable, repeatable scoring — likelihood and impact matrices, annualized loss expectancy, and control effectiveness ratings derived from actual assessment results. Risk scores are deterministic and auditable. LLM outputs are probabilistic and non-reproducible; the same prompt may yield different risk ratings on successive runs, making them unsuitable for formal risk determinations.

## MITRE ATT&CK Control Mapping

SAELAR maps assessed NIST 800-53 controls to all 14 MITRE ATT&CK tactics with technique-level coverage analysis, driven by real pass/fail data from the environment. This provides a defensive coverage heatmap grounded in evidence, not estimation.

## Persistent State and Continuous Monitoring

SAELAR maintains session state, stores assessment history to S3, and operates as a continuously available service on the organization's infrastructure. It preserves assessment baselines for trend analysis, re-assessment, and audit trail. LLMs are stateless — each conversation starts from zero with no memory of prior assessments, no access to historical data, and no ability to detect drift between assessment cycles.

## Data Sovereignty

SAELAR runs entirely within the organization's AWS boundary. Assessment data, credentials, and findings never leave the customer's VPC. All AI capabilities (via Amazon Bedrock) execute within AWS. Multimodal LLMs hosted by third-party providers require transmitting potentially sensitive security posture data to external infrastructure, which may violate data handling requirements for CUI, FISMA, and FedRAMP environments.
