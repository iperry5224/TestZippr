# Controlled Unclassified Information//Information System Vulnerability Information (CUI//ISVI)

## U.S. Department of Commerce (DOC)
## National Oceanic and Atmospheric Administration (NOAA)
## National Environmental Satellite Data and Information Service (NESDIS)

---

# SAELAR and SOPRA Compared to Google Cloud Platform Vertex AI and Security Command Center

**Comparing AWS-native GRC tools to GCP's equivalent platform capabilities**

CSTA FY26 | Version 2.0

Prepared by SAE Team | April 2026

Office of Satellite and Product Operations (OSPO)

CyberSecurity Division (CSD)

---

## Record of Changes/Revision

| Version | Date | Description | Section/Pages Affected | Changes Made By |
|---|---|---|---|---|
| 1.0 | 04/13/2026 | Initial document; compared SAELAR/SOPRA to Gemini chatbot. | All | SAE Team |
| 2.0 | 04/14/2026 | Revised to compare against Vertex AI and Security Command Center platform capabilities; added comparative tables; updated position statement. | All | SAE Team |

---

## Table of Contents

- SAELAR-53 Architecture
- SOPRA Architecture
- Google Cloud Platform: Vertex AI and Security Command Center
- Platform Capability Comparison
- Architectural Similarity Analysis
- Functional Comparison Table
- Key Differences
- Pricing Comparison
- SAE Team Position
- Summary
- References

---

## SAELAR-53 Architecture

SAELAR-53 (Security Architecture and Evaluation Linear Assessment Reporting) is a self-hosted, AWS-native GRC platform deployed on EC2 within the CSTA boundary. It authenticates to 25+ AWS services via IAM role assumption, programmatically assesses NIST 800-53 Rev 5 controls, ingests Security Hub findings, and generates audit-ready compliance documentation (SSPs, POA&Ms, RARs). An integrated AI assistant (Chad) powered by Amazon Bedrock provides context-aware analysis grounded in live assessment data. SAELAR supports both cloud (Bedrock) and air-gapped (Ollama) AI inference modes.

## SOPRA Architecture

SOPRA (SAE On-Premise Risk Assessment) extends the SAE platform to on-premise and hybrid environments. It performs ISSO-oriented security assessments with AI-assisted remediation guidance, generates compliance documentation, and supports deployment scenarios where cloud connectivity is limited or unavailable.

## Google Cloud Platform: Vertex AI and Security Command Center

The original version of this document compared SAELAR and SOPRA to Google's Gemini chatbot — a stateless, general-purpose LLM with no infrastructure access. That comparison was straightforward: a chatbot cannot scan infrastructure.

However, the appropriate comparison is not to Gemini alone, but to the broader Google Cloud Platform (GCP) ecosystem — specifically **Vertex AI** and **Security Command Center (SCC)** — which together provide capabilities that are architecturally similar to what SAELAR and SOPRA deliver on AWS.

**Vertex AI** is Google's enterprise ML/AI platform. It provides access to 200+ foundation models (including Gemini), supports fine-tuning on proprietary data, offers MLOps pipelines with continuous monitoring and drift detection, and integrates with BigQuery for data lake analytics.

**Security Command Center (SCC)** is Google's built-in security and risk management platform. It performs continuous security posture assessment, maps findings to compliance frameworks (NIST 800-53, CIS, PCI DSS, ISO 27001, HIPAA), provides attack path simulation, and includes AI-specific protections for Vertex AI workloads. SCC's Compliance Manager automates control assessments and generates compliance reports.

Together, Vertex AI + SCC constitute GCP's answer to what SAELAR + Bedrock deliver on AWS.

---

## Platform Capability Comparison

| Capability | **SAELAR/SOPRA (AWS)** | **Vertex AI + SCC (GCP)** | **Similarity** |
|---|---|---|---|
| **Live Infrastructure Assessment** | Yes — authenticated API calls to 25+ AWS services (IAM, EC2, S3, KMS, CloudTrail, etc.) | Yes — SCC scans GCP resources continuously via Security Health Analytics detectors | **Similar** — both scan their native cloud; neither scans the other's cloud natively |
| **NIST 800-53 Rev 5 Compliance** | Yes — 36+ automated control checks with pass/fail/warning | Yes — SCC maps detectors to NIST 800-53 R5 controls with compliance dashboards | **Similar** |
| **Security Finding Aggregation** | Yes — ingests from Security Hub (GuardDuty, Inspector, Macie, IAM Analyzer) | Yes — SCC aggregates findings from Security Health Analytics, Web Security Scanner, Event Threat Detection | **Similar** |
| **AI-Powered Analysis** | Yes — Chad (AI) via Amazon Bedrock (Titan, Llama 3, Mistral, Nemotron) | Yes — Vertex AI with 200+ models (Gemini, PaLM, open-source) | **Similar** — both use cloud-hosted foundation models |
| **Compliance Documentation (SSP/POA&M)** | Yes — generates DOCX documents populated with live assessment data | Partial — SCC generates compliance reports; no native SSP/POA&M DOCX generation | **SAELAR advantage** |
| **Risk Assessment Report (RAR)** | Yes — NIST 800-30 methodology with quantitative scoring | Partial — SCC provides risk scores and attack path simulation; no standalone RAR document | **SAELAR advantage** |
| **MITRE ATT&CK Mapping** | Yes — all 14 tactics mapped to NIST controls with technique coverage | Yes — SCC Event Threat Detection maps to MITRE ATT&CK tactics | **Similar** |
| **Continuous Monitoring** | Yes — persistent state, assessment history in S3, baseline drift detection | Yes — SCC provides continuous posture monitoring with Compliance Manager | **Similar** |
| **Vulnerability Management** | Yes — CISA KEV integration, Inspector2 findings, BOD 22-01 tracking | Yes — SCC includes vulnerability scanning, container image analysis | **Similar** |
| **AI Workload Protection** | N/A | Yes — AI Protection with Model Armor, agent threat detection, AI asset inventory | **Vertex AI advantage** |
| **Attack Path Analysis** | No | Yes — SCC Risk Engine simulates attack paths and identifies chokepoints | **Vertex AI/SCC advantage** |
| **Multi-Framework Support** | NIST 800-53 Rev 5 | NIST 800-53, CIS, PCI DSS, ISO 27001, HIPAA, SOC 2, OWASP, CCM 4 | **Vertex AI/SCC advantage** |
| **Data Sovereignty** | Yes — all data stays within CSTA AWS VPC | Yes — GCP supports data residency zones (US, EU) | **Similar** |
| **Air-Gapped Operation** | Yes — Ollama for disconnected environments | No — requires GCP connectivity | **SAELAR advantage** |
| **Cost** | $0 licensing (EC2 compute ~$600/yr) | Pay-as-you-go (SCC Enterprise: ~$15-25/resource/yr + Vertex AI token/compute costs) | **SAELAR advantage** |

---

## Architectural Similarity Analysis

The following table maps the architectural components of SAELAR/SOPRA on AWS to their equivalents on GCP. The platforms are structurally parallel.

| Component | **SAELAR/SOPRA (AWS)** | **Vertex AI + SCC (GCP)** |
|---|---|---|
| **Compute Platform** | EC2 instance (t5a.medium) | Vertex AI Workbench / Compute Engine |
| **AI Foundation Models** | Amazon Bedrock (Titan, Llama 3, Mistral) | Vertex AI Model Garden (Gemini, PaLM, 200+ models) |
| **Security Posture Assessment** | Custom Python assessor + Security Hub | Security Command Center + Security Health Analytics |
| **Finding Aggregation** | AWS Security Hub | SCC Finding Aggregation |
| **Threat Detection** | GuardDuty | Event Threat Detection + Chronicle |
| **Vulnerability Scanning** | Inspector2 | SCC Vulnerability Scanning + Container Analysis |
| **Compliance Framework Mapping** | NIST 800-53 via custom code | NIST 800-53, CIS, PCI DSS via Compliance Manager |
| **Data Lake / Storage** | S3 (saelarallpurpose) | BigQuery + Cloud Storage |
| **Document Generation** | python-docx (SSP, POA&M, RAR) | No native equivalent |
| **Knowledge Base / RAG** | Bedrock Knowledge Base + OpenSearch Serverless | Vertex AI Search + Vertex AI Conversation |
| **Identity / AuthN** | IAM role assumption, instance profiles | IAM, Workload Identity Federation |
| **Encryption** | KMS, S3 SSE | Cloud KMS, CMEK |
| **Network Boundary** | VPC, Security Groups | VPC, VPC Service Controls |
| **Continuous Monitoring** | Re-assessment + S3 history | SCC Compliance Manager |
| **Air-Gapped AI** | Ollama (local inference) | Not supported |

---

## Functional Comparison: What Each Platform Can and Cannot Do

| Function | **SAELAR/SOPRA** | **Vertex AI + SCC** |
|---|---|---|
| Scan AWS infrastructure for compliance | **Yes** | No (SCC Enterprise can scan AWS, but with limited detector coverage) |
| Scan GCP infrastructure for compliance | No | **Yes** |
| Generate SSP documents from live data | **Yes** | No |
| Generate POA&M documents from findings | **Yes** | No |
| Generate Risk Assessment Reports | **Yes** | No (provides risk scores, not formatted RARs) |
| AI chat assistant with assessment context | **Yes** (Chad via Bedrock) | **Yes** (Gemini via Vertex AI) |
| CISA BOD 22-01 KEV tracking | **Yes** | No |
| MITRE ATT&CK technique mapping | **Yes** | **Yes** |
| Quantitative risk scoring (NIST 800-30) | **Yes** | Partial (risk scores, no ALE/SLE methodology) |
| Attack path simulation | No | **Yes** |
| AI model security monitoring | No | **Yes** (AI Protection, Model Armor) |
| Fine-tune models on proprietary data | No | **Yes** (Vertex AI custom training) |
| Operate in air-gapped environments | **Yes** (Ollama) | No |
| Multi-cloud assessment | No (AWS only) | Partial (SCC Enterprise supports AWS) |
| FedRAMP authorization | No | **Yes** (SCC is FedRAMP High authorized) |

---

## Key Differences

Despite the architectural similarities, three fundamental differences remain:

**1. Cloud Specificity.** SAELAR was purpose-built for AWS. SCC was purpose-built for GCP. Each excels at assessing its native cloud and has limited or no capability to assess the other. A GCP security tool does not provide native insight into an AWS environment since the API calls, configuration models, and security architectures are inherently different. To perform an apples-to-apples comparison, GCP tools would have to be evaluated in their ability to assess an AWS tenant — which is the environment SAELAR was designed to protect.

**2. Compliance Documentation.** SAELAR generates audit-ready DOCX documents (SSPs, POA&Ms, RARs) populated with live assessment evidence. Neither Vertex AI nor SCC produces these document types. SCC generates compliance posture reports, but these are dashboard views and data exports, not the structured submission packages required by FISMA, FedRAMP, and NIST authorization processes.

**3. Cost Model.** SAELAR is an open-source tool with zero licensing cost. Vertex AI and SCC Enterprise operate on pay-as-you-go pricing that can range from tens of thousands to hundreds of thousands of dollars annually depending on resource count, API consumption, and feature tier.

---

## Pricing Comparison

| Cost Category | **SAELAR/SOPRA (AWS)** | **Vertex AI + SCC (GCP)** |
|---|---|---|
| **Software Licensing** | $0 | SCC Enterprise: ~$15-25/resource/year |
| **Compute** | EC2 t5a.medium: ~$50/mo (~$600/yr) | Vertex AI Workbench: ~$100-500/mo depending on instance |
| **AI Model Usage** | Bedrock: pay-per-token (Titan Lite: ~$0.15/1M input tokens) | Vertex AI: pay-per-token (Gemini Flash: ~$0.30/1M input tokens) |
| **Storage** | S3: ~$0.023/GB/mo | Cloud Storage: ~$0.020/GB/mo |
| **Estimated Annual (Moderate Env)** | **~$1,200/yr** | **~$25,000-75,000/yr** |

### Vertex AI Additional Cost Factors

| Cost Category | Description | Pricing Details |
|---|---|---|
| Generative AI Token Consumption | API access to foundation models billed on a token-based structure | Gemini 2.5 Flash: ~USD 0.30 per 1M input tokens & ~USD 2.50 per 1M output tokens |
| Compute and Custom Training | Training models and running prediction endpoints, billed per node-hour | Custom AutoML Training: starts ~USD 21.25 per hour |
| Persistent Deployment Costs | Deploying custom models to dedicated endpoints | Continuous hourly compute charges, even during idle periods |
| Ancillary and Ecosystem Fees | Operational tools, Vector Search indexing, Cloud Storage, enterprise features | Vertex AI Pipelines: USD 0.03 per execution + backend compute; Google Search Grounding: USD 35 per 1,000 grounded prompts |

---

## SAE Team Position

**REVISED POSITION:** The SAE Team acknowledges that Google Cloud Platform — through the combination of Vertex AI and Security Command Center — provides a platform with capabilities that are architecturally parallel to SAELAR-53 and SOPRA. Both platforms perform automated compliance assessments, aggregate security findings, map to NIST 800-53, provide AI-powered analysis, and support continuous monitoring within their respective cloud environments.

However, the SAE Team's GRC tools were purpose-built for the CSTA AWS environment. They generate the specific compliance deliverables (SSPs, POA&Ms, RARs) required by NOAA/NESDIS authorization processes, integrate directly with the AWS services deployed in CSTA, enforce CISA BOD 22-01 timelines, and operate at zero licensing cost. Migrating these capabilities to GCP would require re-engineering the entire assessment engine for GCP APIs, procuring SCC Enterprise licensing, and abandoning the air-gapped deployment capability — without a clear operational benefit, given that the systems being assessed reside in AWS.

The appropriate framing is not that one platform is superior, but that **SAELAR and SOPRA are the right tools for an AWS environment, just as Vertex AI and SCC are the right tools for a GCP environment.** The SAE Team has built the AWS equivalent of what Google offers commercially at significant cost.

---

## Summary

The original comparison between SAELAR/SOPRA and the Gemini chatbot was clear-cut: a chatbot cannot scan infrastructure. The revised comparison against the full GCP platform (Vertex AI + Security Command Center) reveals that Google has built equivalent capabilities for its own cloud — and so has the SAE Team for AWS.

The platforms are similar in architecture, capability scope, and design philosophy. The differences lie in cloud specificity, document generation maturity, and cost. SAELAR and SOPRA deliver these capabilities for the CSTA AWS environment at a fraction of the cost of the GCP equivalent, with the additional benefits of full source code ownership, air-gapped deployment support, and compliance document generation tailored to NOAA/NESDIS requirements.

We continue to invite all stakeholders to visit SAELAR-53 at https://nih-saelar.nesdis-hq.noaa.gov:4443/ to evaluate the platform firsthand.

---

## References

- Google Cloud Security Command Center Documentation: https://cloud.google.com/security-command-center/docs
- Google Vertex AI Documentation: https://cloud.google.com/vertex-ai/docs
- Google Cloud Compliance Manager: https://cloud.google.com/security-command-center/docs/compliance-management
- NIST SP 800-53 Rev 5: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- AWS Security Hub NIST 800-53: https://docs.aws.amazon.com/securityhub/latest/userguide/nist-standard.html
- CISA Known Exploited Vulnerabilities Catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- Google Vertex AI Pricing: https://cloud.google.com/vertex-ai/pricing
- Google SCC Pricing: https://cloud.google.com/security-command-center/pricing
