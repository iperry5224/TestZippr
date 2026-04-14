Controlled Unclassified Information//Information System Vulnerability Information
(CUI//ISVI)

U.S. Department of Commerce (DOC)
National Oceanic and Atmospheric Administration (NOAA)
National Environmental Satellite Data and Information Service (NESDIS)

# SAELAR and SOPRA Compared to Google Cloud Platform Vertex AI and Security Command Center

Comparing tools built on AWS to GCP

CSTA FY26

Version 2.0

Prepared by SAE Team

April 14, 2026

Office of Satellite and Product Operations (OSPO)

CyberSecurity Division (CSD)

---

Controlled Unclassified Information//Information System Vulnerability Information
(CUI//ISVI)

## Record of Changes/Revision

| Version Number | Date | Description of Change/Revision | Section/Pages Affected | Changes Made by Name/Title/Organization |
|---|---|---|---|---|
| 1.0 | 04/13/2026 | Initial document; Updated/resolved comments. | All | SAE Team |
| 2.0 | 04/14/2026 | Revised to compare against full GCP platform (Vertex AI + Security Command Center) rather than Gemini chatbot alone; added comparative tables; updated position statement. | All | SAE Team |

---

Controlled Unclassified Information//Information System Vulnerability Information
(CUI//ISVI)

## Table of Contents

Record of Changes/Revision......................................................................................................2

Table of Contents.........................................................................................................................3

SAELAR's Architecture...............................................................................................................4

SOPRA's Architecture.................................................................................................................4

Gemini Capabilities......................................................................................................................4

Vertex AI Capabilities..................................................................................................................4

Google Cloud Security Command Center.................................................................................5

Vertex AI Pricing and Costs.......................................................................................................5

Platform Capability Comparison................................................................................................6

Architectural Similarity Analysis...............................................................................................7

Live AWS Infrastructure Assessment.......................................................................................8

Automated Security Hub Finding Ingestion.............................................................................8

CISA BOD 22-01 Compliance Enforcement..............................................................................8

Assessment-Ready Document Generation...............................................................................9

Quantitative Risk Scoring...........................................................................................................9

MITRE ATT&CK Control Mapping..............................................................................................9

Persistent State and Continuous Monitoring............................................................................9

Data Sovereignty..........................................................................................................................9

Key Differences..........................................................................................................................10

Pricing Comparison...................................................................................................................10

SAE Team Position.....................................................................................................................11

Summary......................................................................................................................................11

References...................................................................................................................................12

Vertex AI Costs Details/Explanations......................................................................................12

---

Controlled Unclassified Information//Information System Vulnerability Information
(CUI//ISVI)

## SAELAR's Architecture:

SAELAR-53 (Security Architecture and Evaluation Linear Assessment Reporting) is a self-hosted, AWS-native GRC platform deployed on EC2 within the CSTA boundary. It authenticates to 25+ AWS services via IAM role assumption, programmatically assesses NIST 800-53 Rev 5 controls, ingests Security Hub findings, and generates audit-ready compliance documentation (SSPs, POA&Ms, RARs). An integrated AI assistant (Chad) powered by Amazon Bedrock provides context-aware analysis grounded in live assessment data. SAELAR supports both cloud (Bedrock) and air-gapped (Ollama) AI inference modes.

## SOPRA's Architecture:

SOPRA (SAE On-Premise Risk Assessment) extends the SAE platform to on-premise and hybrid environments. It performs ISSO-oriented security assessments with AI-assisted remediation guidance, generates compliance documentation, and supports deployment scenarios where cloud connectivity is limited or unavailable.

## Gemini Capabilities:

The original version of this document compared SAELAR and SOPRA to Google's Gemini chatbot — a stateless, general-purpose large language model (LLM) with no infrastructure access. That comparison was straightforward: a chatbot cannot scan infrastructure, authenticate to cloud services, or generate compliance documents populated with live assessment evidence. However, Gemini alone is not the appropriate comparison. The relevant comparison is to the broader Google Cloud Platform ecosystem in which Gemini operates — specifically Vertex AI and Security Command Center.

## Vertex AI Capabilities

While the standalone Gemini chatbot provides accessible generative AI, Google's Vertex AI serves as a comprehensive, enterprise-grade machine learning (ML) platform designed to manage the entire AI lifecycle. Unlike a stateless chatbot, Vertex AI allows organizations to build, deploy, and scale both traditional predictive ML models and advanced generative AI applications within a unified Google Cloud environment. It features a Model Garden with access to over 200 foundation models—including Google's Gemini series, open-source options, and partner models—enabling teams to securely fine-tune models on proprietary data. The platform supports low-code development via AutoML, custom model training, integrated MLOps pipelines for continuous monitoring (such as detecting model drift), and native integrations with enterprise data lakes like BigQuery.

## Google Cloud Security Command Center

Security Command Center (SCC) is Google's built-in security and risk management platform — the GCP equivalent of what SAELAR delivers on AWS. SCC performs continuous security posture assessment, maps findings to compliance frameworks (NIST 800-53, CIS, PCI DSS, ISO 27001, HIPAA, SOC 2), provides attack path simulation via its Risk Engine, and includes AI-specific protections for Vertex AI workloads through AI Protection. SCC's Compliance Manager automates control assessments and generates compliance reports. In its Enterprise tier, SCC can also extend limited assessment coverage to AWS environments. Together, Vertex AI and Security Command Center constitute GCP's answer to what SAELAR + Amazon Bedrock deliver on AWS.

## Vertex AI Pricing and Costs

Vertex AI operates on a complex, pay-as-you-go pricing model where costs are dictated by compute consumption, deployment methods, and API usage rather than a flat licensing fee. Organizations must maintain stringent resource monitoring, as workloads scale dynamically and can lead to unexpected billing spikes. See below: (Vertex AI Costs Details/Explanations:)

---

Controlled Unclassified Information//Information System Vulnerability Information
(CUI//ISVI)

Google Cloud Platform (GCP) tools are most efficient within the confines of the GCP environment. A GCP security assessment tool does NOT provide native insight into an AWS environment since the API calls, configuration and security architectures are inherently diverse. In order to perform an "apples-to-apples" comparison, GCP security assessment tools would have to be evaluated in their propensity to assess an AWS tenant. SAELAR-53 was NEVER intended to assess anything but AWS. However, it is important to acknowledge that GCP has built platform capabilities — through Vertex AI and Security Command Center — that are architecturally parallel to what the SAE Team has built on AWS.

## Platform Capability Comparison

| Capability | SAELAR/SOPRA (AWS) | Vertex AI + SCC (GCP) | Similarity |
|---|---|---|---|
| Live Infrastructure Assessment | Yes — authenticated API calls to 25+ AWS services (IAM, EC2, S3, KMS, CloudTrail, etc.) | Yes — SCC scans GCP resources continuously via Security Health Analytics detectors | Similar — both scan their native cloud |
| NIST 800-53 Rev 5 Compliance | Yes — 36+ automated control checks with pass/fail/warning | Yes — SCC maps detectors to NIST 800-53 R5 controls with compliance dashboards | Similar |
| Security Finding Aggregation | Yes — ingests from Security Hub (GuardDuty, Inspector, Macie, IAM Analyzer) | Yes — SCC aggregates from Security Health Analytics, Web Security Scanner, Event Threat Detection | Similar |
| AI-Powered Analysis | Yes — Chad (AI) via Amazon Bedrock (Titan, Llama 3, Mistral, Nemotron) | Yes — Vertex AI with 200+ models (Gemini, PaLM, open-source) | Similar |
| Compliance Documentation (SSP/POA&M) | Yes — generates DOCX documents populated with live assessment data | Partial — SCC generates compliance reports; no native SSP/POA&M DOCX generation | SAELAR advantage |
| Risk Assessment Report (RAR) | Yes — NIST 800-30 methodology with quantitative scoring | Partial — SCC provides risk scores and attack path simulation; no standalone RAR document | SAELAR advantage |
| MITRE ATT&CK Mapping | Yes — all 14 tactics mapped to NIST controls with technique coverage | Yes — SCC Event Threat Detection maps to MITRE ATT&CK tactics | Similar |
| Continuous Monitoring | Yes — persistent state, assessment history in S3, baseline drift detection | Yes — SCC provides continuous posture monitoring with Compliance Manager | Similar |
| Vulnerability Management | Yes — CISA KEV integration, Inspector2 findings, BOD 22-01 tracking | Yes — SCC includes vulnerability scanning, container image analysis | Similar |
| AI Workload Protection | N/A | Yes — AI Protection with Model Armor, agent threat detection | Vertex AI/SCC advantage |
| Attack Path Analysis | No | Yes — SCC Risk Engine simulates attack paths and identifies chokepoints | Vertex AI/SCC advantage |
| Multi-Framework Support | NIST 800-53 Rev 5 | NIST 800-53, CIS, PCI DSS, ISO 27001, HIPAA, SOC 2, OWASP, CCM 4 | Vertex AI/SCC advantage |
| Air-Gapped Operation | Yes — Ollama for disconnected environments | No — requires GCP connectivity | SAELAR advantage |
| Cost | $0 licensing (EC2 compute ~$600/yr) | Pay-as-you-go (SCC Enterprise: ~$15-25/resource/yr + Vertex AI costs) | SAELAR advantage |

---

Controlled Unclassified Information//Information System Vulnerability Information
(CUI//ISVI)

## Architectural Similarity Analysis

The following table maps the architectural components of SAELAR/SOPRA on AWS to their equivalents on GCP. The platforms are structurally parallel.

| Component | SAELAR/SOPRA (AWS) | Vertex AI + SCC (GCP) |
|---|---|---|
| Compute Platform | EC2 instance (t5a.medium) | Vertex AI Workbench / Compute Engine |
| AI Foundation Models | Amazon Bedrock (Titan, Llama 3, Mistral) | Vertex AI Model Garden (Gemini, PaLM, 200+ models) |
| Security Posture Assessment | Custom Python assessor + Security Hub | Security Command Center + Security Health Analytics |
| Finding Aggregation | AWS Security Hub | SCC Finding Aggregation |
| Threat Detection | GuardDuty | Event Threat Detection + Chronicle |
| Vulnerability Scanning | Inspector2 | SCC Vulnerability Scanning + Container Analysis |
| Compliance Framework Mapping | NIST 800-53 via custom assessment engine | NIST 800-53, CIS, PCI DSS via Compliance Manager |
| Data Lake / Storage | S3 (saelarallpurpose) | BigQuery + Cloud Storage |
| Document Generation | python-docx (SSP, POA&M, RAR) | No native equivalent |
| Knowledge Base / RAG | Bedrock Knowledge Base + OpenSearch Serverless | Vertex AI Search + Vertex AI Conversation |
| Identity / AuthN | IAM role assumption, instance profiles | IAM, Workload Identity Federation |
| Encryption | KMS, S3 SSE | Cloud KMS, CMEK |
| Network Boundary | VPC, Security Groups | VPC, VPC Service Controls |
| Continuous Monitoring | Re-assessment + S3 history | SCC Compliance Manager |
| Air-Gapped AI | Ollama (local inference) | Not supported |

## Live AWS Infrastructure Assessment

SAELAR-53 executes real-time, authenticated Application Programming Interface (API) calls against 25+ Amazon Web Services (AWS) services including Identity and Access Management (IAM), Elastic Compute Cloud (EC2), Simple Storage Service (S3), Key Management Service (KMS), CloudTrail, GuardDuty, Security Hub, Inspector2, Macie, Web Application Firewall (WAF), Relational Database Service (RDS), Lambda, Secrets Manager, and others to programmatically assess the actual state of an environment. It evaluates 36+ individual NIST SP 800-53, Rev 5 controls across 13 cloud-related control families by querying live configurations, not by generating assumptions. Google's Security Command Center performs an equivalent function for GCP resources — scanning infrastructure continuously via Security Health Analytics detectors and mapping findings to NIST 800-53 controls. Both platforms assess their native cloud; neither natively assesses the other's environment.

## Automated Security Hub Finding Ingestion

SAELAR-53 pulls and normalizes findings from AWS Security Hub, which aggregates detections from AWS GuardDuty, Inspector, Macie, IAM Access Analyzer, and third-party tools. It maps these findings to NIST control families and incorporates them into assessment scoring. Similarly, SCC aggregates findings from Security Health Analytics, Web Security Scanner, Event Threat Detection, and Chronicle into a unified security posture view. Both platforms serve as centralized finding aggregation engines for their respective clouds.

## CISA BOD 22-01 Compliance Enforcement

SAELAR-53 integrates the Cybersecurity and Infrastructure Security Agency (CISA) Known Exploited Vulnerabilities (KEV) catalog, cross-references it against the organization's environment, calculates remediation deadlines per BOD 22-01 timelines (6 months for pre-2021 Common Vulnerabilities and Exposures (CVEs), 2 weeks for post-2021), and tracks compliance status. This capability is unique to SAELAR — neither Vertex AI nor SCC provides native CISA KEV integration with BOD 22-01 deadline tracking.

---

Controlled Unclassified Information//Information System Vulnerability Information
(CUI//ISVI)

## Assessment-Ready Document Generation

SAELAR-53 generates complete, structured DOCX (Document (XML)) documents — System Security Plans (SSPs), Plans of Action & Milestones (POA&Ms), and Risk Assessment Reports (RARs) — populated with actual assessment data, control implementation status, and system-specific metadata. These are formatted to NIST/FedRAMP/FISMA (Federal Risk and Authorization Management Program) submission standards with proper section numbering, tables, and document control pages. SCC generates compliance posture reports and dashboards, but does not produce these specific document types. This remains a distinct SAELAR advantage.

## Quantitative Risk Scoring

SAELAR-53 implements NIST SP 800-30 risk methodology with calculable, repeatable scoring — likelihood and impact matrices, annualized loss expectancy, and control effectiveness ratings derived from actual assessment results. Risk scores are deterministic and auditable. SCC provides risk scores and attack path simulation through its Risk Engine, but does not implement the formal NIST 800-30 ALE/SLE methodology. Both approaches produce actionable risk data; SAELAR's methodology is more directly aligned with federal audit requirements.

## MITRE ATT&CK Control Mapping

SAELAR maps assessed NIST SP 800-53 controls to all 14 MITRE ATT&CK (MITRE Adversarial Tactics, Techniques, and Common Knowledge) tactics with technique-level coverage analysis, driven by real pass/fail data from the environment. SCC's Event Threat Detection similarly maps detected threats to MITRE ATT&CK tactics. Both platforms provide ATT&CK coverage analysis grounded in their respective assessment data.

## Persistent State and Continuous Monitoring

SAELAR maintains session state, stores assessment history to S3, and operates as a continuously available service. It preserves assessment baselines for trend analysis, re-assessment, and audit trail. SCC provides equivalent continuous monitoring through its Compliance Manager, which automatically scans environments and generates compliance posture reports over time. Both platforms support persistent state and historical trend analysis.

## Data Sovereignty

SAELAR is contained within its host environment's designated boundary, currently the CSTA AWS. Assessment data, credentials, and findings never leave that internal VPC. All AI capabilities (via Amazon Bedrock) execute within AWS. GCP provides equivalent data residency controls through Data Residency Zones (US, EU) and VPC Service Controls. Both platforms can be configured to keep data within designated boundaries. The key consideration is that CSTA's systems reside in AWS — meaning SAELAR's data sovereignty is inherent to the deployment, while using GCP tools would require transmitting AWS environment data to Google's infrastructure.

---

Controlled Unclassified Information//Information System Vulnerability Information
(CUI//ISVI)

## Key Differences

Despite the architectural similarities, three fundamental differences remain:

**1. Cloud Specificity.** SAELAR was purpose-built for AWS. SCC was purpose-built for GCP. Each excels at assessing its native cloud and has limited or no capability to assess the other. A GCP security tool does not provide native insight into an AWS environment since the API calls, configuration models, and security architectures are inherently different.

**2. Compliance Documentation.** SAELAR generates audit-ready DOCX documents (SSPs, POA&Ms, RARs) populated with live assessment evidence. Neither Vertex AI nor SCC produces these document types. SCC generates compliance dashboard views and data exports, but not the structured submission packages required by FISMA, FedRAMP, and NIST authorization processes.

**3. Cost Model.** SAELAR is an open-source tool with zero licensing cost. Vertex AI and SCC Enterprise operate on pay-as-you-go pricing that can range from tens of thousands to hundreds of thousands of dollars annually depending on resource count, API consumption, and feature tier.

## Pricing Comparison

| Cost Category | SAELAR/SOPRA (AWS) | Vertex AI + SCC (GCP) |
|---|---|---|
| Software Licensing | $0 | SCC Enterprise: ~$15-25/resource/year |
| Compute | EC2 t5a.medium: ~$50/mo (~$600/yr) | Vertex AI Workbench: ~$100-500/mo |
| AI Model Usage | Bedrock: pay-per-token (Titan Lite: ~$0.15/1M input tokens) | Vertex AI: pay-per-token (Gemini Flash: ~$0.30/1M input tokens) |
| Storage | S3: ~$0.023/GB/mo | Cloud Storage: ~$0.020/GB/mo |
| Estimated Annual (Moderate Env) | ~$1,200/yr | ~$25,000-75,000/yr |

---

Controlled Unclassified Information//Information System Vulnerability Information
(CUI//ISVI)

## SAE Team Position

**REVISED POSITION:** The SAE Team acknowledges that Google Cloud Platform — through the combination of Vertex AI and Security Command Center — provides a platform with capabilities that are architecturally parallel to SAELAR-53 and SOPRA. Both platforms perform automated compliance assessments, aggregate security findings, map to NIST 800-53, provide AI-powered analysis, and support continuous monitoring within their respective cloud environments.

However, the SAE Team's GRC tools were purpose-built for the CSTA AWS environment. They generate the specific compliance deliverables (SSPs, POA&Ms, RARs) required by NOAA/NESDIS authorization processes, integrate directly with the AWS services deployed in CSTA, enforce CISA BOD 22-01 timelines, and operate at zero licensing cost. Migrating these capabilities to GCP would require re-engineering the entire assessment engine for GCP APIs, procuring SCC Enterprise licensing, and abandoning the air-gapped deployment capability — without a clear operational benefit, given that the systems being assessed reside in AWS.

**The appropriate framing is not that one platform is superior, but that SAELAR and SOPRA are the right tools for an AWS environment, just as Vertex AI and SCC are the right tools for a GCP environment.** The SAE Team has built the AWS equivalent of what Google offers commercially at significant cost.

## Summary

The original comparison between SAELAR/SOPRA and the Gemini chatbot was clear-cut: a chatbot cannot scan infrastructure. The revised comparison against the full GCP platform (Vertex AI + Security Command Center) reveals that Google has built equivalent capabilities for its own cloud — and so has the SAE Team for AWS.

The platforms are similar in architecture, capability scope, and design philosophy. The differences lie in cloud specificity, document generation maturity, and cost. SAELAR and SOPRA deliver these capabilities for the CSTA AWS environment at a fraction of the cost of the GCP equivalent, with the additional benefits of full source code ownership, air-gapped deployment support, and compliance document generation tailored to NOAA/NESDIS requirements.

We continue to invite all stakeholders to visit SAELAR-53 at https://nih-saelar.nesdis-hq.noaa.gov:4443/ to evaluate the platform firsthand.

---

Controlled Unclassified Information//Information System Vulnerability Information
(CUI//ISVI)

## References:

- Google Cloud Security Command Center Documentation: https://cloud.google.com/security-command-center/docs
- Google Vertex AI Documentation: https://cloud.google.com/vertex-ai/docs
- Google Cloud Compliance Manager: https://cloud.google.com/security-command-center/docs/compliance-management
- Google Cloud Control Navigator for Vertex AI: https://security.googlecloudcommunity.com/ciso-blog-77/accelerating-secure-ai-adoption-in-regulated-industries-introducing-control-navigator-for-vertex-ai-6470
- NIST SP 800-53 Rev 5: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- AWS Security Hub NIST 800-53: https://docs.aws.amazon.com/securityhub/latest/userguide/nist-standard.html
- CISA Known Exploited Vulnerabilities Catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- Google Vertex AI Pricing: https://cloud.google.com/vertex-ai/pricing
- Google SCC Pricing: https://cloud.google.com/security-command-center/pricing

## Vertex AI Costs Details/Explanations:

- **Generative AI Token Consumption:** API access to foundation models is billed on a token-based structure. For example, utilizing a lightweight model like Gemini 2.5 Flash costs approximately USD 0.30 per million input tokens and USD 2.50 per million output tokens, while more complex reasoning models carry higher rates.
- **Compute and Custom Training:** Training models and running prediction endpoints are billed per node-hour, fluctuating based on the machine type and hardware accelerators (GPUs/TPUs) selected. Custom AutoML training node pricing typically starts around USD 21.25 per hour.
- **Persistent Deployment Costs:** Deploying custom models to dedicated endpoints incurs continuous hourly compute charges, even during idle periods, unless specific shared infrastructure or batch processing is utilized.
- **Ancillary and Ecosystem Fees:** Additional costs accumulate for operational tools, including Vertex AI Pipelines (USD 0.03 per execution plus backend compute), Vector Search indexing, Cloud Storage for datasets, and enterprise features like Google Search Grounding (USD 35 per 1,000 grounded prompts).

| Cost Category | Description | Pricing Details / Examples |
|---|---|---|
| Generative AI Token Consumption | API access to foundation models billed on a token-based structure. | Gemini 2.5 Flash: ~USD 0.30 per 1M input tokens & ~USD 2.50 per 1M output tokens. (More complex reasoning models carry higher rates). |
| Compute and Custom Training | Training models and running prediction endpoints, billed per node-hour (fluctuates based on machine type/accelerators). | Custom AutoML Training: Node pricing typically starts around USD 21.25 per hour. |
| Persistent Deployment Costs | Deploying custom models to dedicated endpoints. | Incurs continuous hourly compute charges, even during idle periods, unless specific shared infrastructure or batch processing is utilized. |
| Ancillary and Ecosystem Fees | Additional costs accumulated for operational tools, Vector Search indexing, Cloud Storage, and enterprise features. | Vertex AI Pipelines: USD 0.03 per execution + backend compute. Google Search Grounding: USD 35 per 1,000 grounded prompts. |
