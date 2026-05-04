# Compliance Assistance with RAG: Architecture Comparison

## SAELAR/SOPRA vs. the AWS Reference Architecture

The diagram depicts AWS's reference architecture for "Compliance Assistance with RAG" — a pattern where users interact with a SageMaker Notebook that calls Bedrock (Claude) with a Knowledge Base backed by S3 to answer compliance questions. Below is a detailed comparison of how this reference architecture differs from what the SAE Team has built.

---

## Architectural Component Mapping

| Component | AWS Reference Architecture (Diagram) | SAELAR/SOPRA (SAE Team) |
|---|---|---|
| **User Interface** | Amazon SageMaker Notebook (code cells, data science-oriented) | Streamlit web application (browser-based, 8 interactive tabs, accessible to non-technical users) |
| **Compute Platform** | SageMaker managed notebook instance | EC2 instance (self-managed, full control) |
| **API Layer** | Boto3 from notebook | Boto3 from Streamlit app (25+ AWS service clients) |
| **AI Model** | Claude (via Bedrock) | NVIDIA Nemotron, Titan, Llama 3, Mistral via Bedrock (Claude removed per policy); Ollama for air-gapped |
| **RAG / Knowledge Base** | Amazon Bedrock Knowledge Base → S3 | Amazon Bedrock Knowledge Base → OpenSearch Serverless → S3 (recently added) |
| **Document Storage** | Amazon S3 (knowledge documents) | Amazon S3 (SSPs, POA&Ms, RARs, assessment results, knowledge documents) |
| **Purpose** | Answer compliance questions using retrieved documents | Full GRC lifecycle: assess, score, document, monitor, remediate |

---

## Capability Comparison

| Capability | AWS Reference (Diagram) | SAELAR/SOPRA |
|---|---|---|
| **Answer compliance questions via RAG** | Yes — primary purpose | Yes — Chad (AI) with Knowledge Base retrieval |
| **Live infrastructure scanning** | No | Yes — 36+ NIST 800-53 controls assessed against live AWS services |
| **Security Hub finding ingestion** | No | Yes — aggregates GuardDuty, Inspector, Macie, IAM Analyzer |
| **CISA BOD 22-01 / KEV tracking** | No | Yes — live KEV catalog with remediation deadlines |
| **SSP document generation** | No | Yes — DOCX with live assessment data |
| **POA&M generation** | No | Yes — from assessment findings |
| **Risk Assessment Report (RAR)** | No | Yes — NIST 800-30 methodology |
| **Quantitative risk scoring** | No | Yes — likelihood × impact, ALE, control effectiveness |
| **MITRE ATT&CK mapping** | No | Yes — all 14 tactics mapped to controls |
| **Threat modeling** | No | Yes — control-threat mapping, asset-threat matrix, actuarial data |
| **Continuous monitoring** | No | Yes — persistent state, S3 history, baseline drift |
| **Air-gapped operation** | No — requires SageMaker + Bedrock | Yes — Ollama for disconnected environments |
| **Multi-user web access** | No — notebook is single-user | Yes — browser-accessible to any authorized user |
| **Report generation** | No | Yes — 8 report types (executive summary, audit package, board briefing, etc.) |

---

## Key Differences

### 1. Scope
The reference architecture is a **question-answering tool**. Users ask compliance questions, the system retrieves relevant documents from S3 via the Knowledge Base, and Claude generates an answer. That is the entire workflow.

SAELAR/SOPRA is a **full GRC platform** that includes question-answering (Chad AI with RAG) as one of eight capabilities. It also scans infrastructure, generates compliance documents, scores risk, maps to MITRE ATT&CK, tracks vulnerabilities, and provides continuous monitoring.

### 2. Interface
The reference architecture uses a **SageMaker Notebook** — a code-cell environment designed for data scientists. Users must write Python code to interact with the system.

SAELAR uses a **Streamlit web application** with a browser-based UI accessible to ISSOs, auditors, and security analysts without coding knowledge. It includes interactive dashboards, one-click assessments, and downloadable reports.

### 3. Assessment vs. Retrieval
The reference architecture **retrieves and summarizes existing documents**. It does not assess whether controls are actually implemented in the environment.

SAELAR **programmatically verifies control implementation** by making authenticated API calls to AWS services and returning evidence-backed pass/fail results. The documents it retrieves via RAG supplement — not replace — the live assessment data.

### 4. Document Generation
The reference architecture **consumes** documents stored in S3. It does not create new compliance documents.

SAELAR **produces** documents — SSPs, POA&Ms, and RARs — populated with live assessment evidence, and stores them back to S3 where the Knowledge Base can index them for future retrieval.

### 5. AI Model
The reference architecture specifies **Claude** as the model.

SAELAR uses **multiple Bedrock models** (Nemotron, Titan, Llama 3, Mistral) with automatic failover, and supports **Ollama** for air-gapped environments. Claude was removed per organizational policy.

---

## What SAELAR Already Incorporates from the Reference Architecture

The SAE Team has already implemented the core RAG pattern shown in the diagram:

| Reference Architecture Component | SAELAR Implementation | Status |
|---|---|---|
| Boto3 API calls | Yes — 25+ service clients | ✅ Operational |
| Amazon Bedrock model invocation | Yes — call_bedrock_ai() with multi-model failover | ✅ Operational |
| Bedrock Knowledge Base | Yes — retrieve_from_knowledge_base() + call_ai_with_rag() | ✅ Built, pending KB provisioning |
| S3 document storage | Yes — saelarallpurpose bucket | ✅ Operational |
| RAG retrieval → model generation | Yes — Chad retrieves docs, injects into prompt, generates answer | ✅ Built, pending KB provisioning |

---

## Summary

The AWS reference architecture for "Compliance Assistance with RAG" represents a **subset** of what SAELAR and SOPRA deliver. It is a document retrieval and question-answering pattern — a single feature within SAELAR's broader platform. The SAE Team has already incorporated this RAG pattern into Chad (AI) while also providing live infrastructure assessment, compliance document generation, risk scoring, threat modeling, and continuous monitoring capabilities that the reference architecture does not address.

**The reference architecture is the engine. SAELAR is the entire vehicle.**
