# SLyK-53 — SAE Lightweight Yaml Kit

AI-powered security compliance assistant running on AWS serverless infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AWS Console                                    │
│  ┌─────────────────┐                                                    │
│  │ Service Catalog │──→ CloudFront ──→ S3 (React UI)                   │
│  │ or Bookmark     │                        │                           │
│  └─────────────────┘                        │                           │
│                                             ▼                           │
│                                    ┌────────────────┐                   │
│                                    │ Cognito        │                   │
│                                    │ Identity Pool  │                   │
│                                    └───────┬────────┘                   │
│                                            │                            │
│                                            ▼                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Bedrock Agent                                 │   │
│  │                 "SLyK-53-Security-Assistant"                     │   │
│  │                                                                  │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌─────────────┐ │   │
│  │  │ ASSESS   │  │  REMEDIATE   │  │  HARDEN  │  │ Knowledge   │ │   │
│  │  │ Action   │  │  Action      │  │  Action  │  │ Base (RAG)  │ │   │
│  │  │ Group    │  │  Group       │  │  Group   │  │             │ │   │
│  │  └────┬─────┘  └──────┬───────┘  └────┬─────┘  └─────────────┘ │   │
│  └───────┼───────────────┼───────────────┼──────────────────────────┘   │
│          │               │               │                              │
│          ▼               ▼               ▼                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │
│  │ slyk-assess  │ │slyk-remediate│ │ slyk-harden  │                    │
│  │   Lambda     │ │   Lambda     │ │   Lambda     │                    │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘                    │
│         │                │                │                             │
│         └────────────────┼────────────────┘                             │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      AWS APIs                                    │   │
│  │  IAM │ S3 │ EC2 │ CloudTrail │ GuardDuty │ Security Hub │ SSM  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

| Component | Description | Deployment Script |
|-----------|-------------|-------------------|
| **Bedrock Agent** | AI orchestration — routes user requests to appropriate Lambda | `deploy_slyk.py` |
| **Lambda Functions** | ASSESS, REMEDIATE, HARDEN logic | `deploy_slyk.py` |
| **Cognito** | Identity Pool for authentication | `deploy_infrastructure.py` |
| **API Gateway** | REST API (optional, UI uses SDK directly) | `deploy_infrastructure.py` |
| **DynamoDB** | Sessions and audit logging | `deploy_infrastructure.py` |
| **S3 + CloudFront** | UI hosting | `deploy_infrastructure.py` |
| **Knowledge Base** | RAG over compliance documents | `deploy_knowledge_base.py` |
| **React UI** | Web interface | `ui/` folder |

## Quick Start

### Option 1: Full Deployment (CloudShell)

```bash
# Clone the repo
git clone https://github.com/iperry5224/TestZippr.git
cd TestZippr/slyk_deploy_extract/slyk

# Set environment
export AWS_DEFAULT_REGION=us-east-1
export S3_BUCKET_NAME=slyk-grcp-$(aws sts get-caller-identity --query Account --output text)

# Create S3 bucket
aws s3 mb s3://$S3_BUCKET_NAME --region $AWS_DEFAULT_REGION

# Deploy everything
python3 deploy_all.py
```

### Option 2: Core Only (Minimal)

```bash
# Just the agent and Lambdas — test via Bedrock Console
python3 deploy_slyk.py
```

### Option 3: Step by Step

```bash
# 1. Core agent and Lambdas
python3 deploy_slyk.py

# 2. Infrastructure (Cognito, DynamoDB, CloudFront)
python3 deploy_infrastructure.py

# 3. Knowledge Base (optional, for RAG)
python3 deploy_knowledge_base.py
```

## Deployment Scripts

### `deploy_slyk.py`
Creates the core SLyK agent:
- IAM roles (Lambda execution, Bedrock agent)
- Lambda functions (assess, remediate, harden)
- Bedrock Agent with action groups
- Agent alias for production use

### `deploy_infrastructure.py`
Creates supporting infrastructure:
- Cognito User Pool and Identity Pool
- DynamoDB tables (sessions, audit log)
- API Gateway REST API
- S3 bucket for UI hosting
- CloudFront distribution

### `deploy_knowledge_base.py`
Creates RAG capabilities:
- OpenSearch Serverless collection
- Bedrock Knowledge Base
- S3 data source for documents
- Associates KB with agent

### `delete_slyk.py`
Tears down all SLyK resources (idempotent).

## React UI

The `ui/` folder contains a React application for the SLyK web interface.

### Build and Deploy

```bash
cd ui
npm install
npm run build

# Deploy to S3 (get bucket name from slyk_config.json)
aws s3 sync build/ s3://slyk-ui-<ACCOUNT_ID>/ --delete
```

### Configuration

The UI reads configuration from environment variables (set in `.env`):
- `REACT_APP_AGENT_ID` — Bedrock Agent ID
- `REACT_APP_AGENT_ALIAS_ID` — Agent alias ID
- `REACT_APP_IDENTITY_POOL_ID` — Cognito Identity Pool
- `REACT_APP_AWS_REGION` — AWS region

These are auto-generated by `deploy_infrastructure.py`.

## Lambda Functions

### slyk-assess
Runs NIST 800-53 compliance checks:
- AC-2: Account Management (MFA)
- AC-6: Least Privilege
- AU-2: Event Logging (CloudTrail)
- IA-2: Root MFA
- SC-7: Boundary Protection (Security Groups)
- SC-28: Encryption at Rest (S3)
- SI-4: System Monitoring (GuardDuty)

Also integrates with AWS Security Hub for additional findings.

### slyk-remediate
Generates and executes remediation:
- Playbooks for each NIST control
- AWS CLI commands for fixes
- SSM integration for execution
- Security Hub finding remediation

### slyk-harden
Scans and hardens AWS resources:
- **S3**: Encryption, versioning, public access block
- **EC2**: IMDSv2, security groups, IAM roles
- **IAM**: MFA, access key rotation

## Testing

### Via Bedrock Console
1. Go to AWS Console > Amazon Bedrock > Agents
2. Select "SLyK-53-Security-Assistant"
3. Click "Test" in the right panel
4. Try these prompts:
   - "Assess my NIST 800-53 compliance"
   - "Harden all my S3 buckets"
   - "Generate remediation for AC-2"
   - "Show me critical Security Hub findings"

### Via React UI
1. Deploy the UI to CloudFront
2. Navigate to the CloudFront URL
3. Use the chat interface or quick action buttons

## Cost Estimate

| Component | Monthly Cost |
|-----------|--------------|
| Bedrock Agent | ~$0 (pay per invocation) |
| Bedrock model calls | ~$10-50 |
| Lambda | ~$5-20 |
| API Gateway | ~$3 |
| S3 + CloudFront | ~$2 |
| DynamoDB | ~$5 |
| Cognito | Free (<50K MAU) |
| OpenSearch Serverless | ~$20-50 (if KB enabled) |
| **Total** | **~$25-130/month** |

## Files

```
slyk/
├── deploy_slyk.py              # Core agent deployment
├── deploy_infrastructure.py    # Cognito, DynamoDB, CloudFront
├── deploy_knowledge_base.py    # RAG Knowledge Base
├── deploy_all.py               # Master deployment script
├── delete_slyk.py              # Teardown script
├── slyk_config.json            # Generated config (after deploy)
├── lambda_functions/
│   ├── assess.py               # NIST 800-53 assessment
│   ├── remediate.py            # Remediation playbooks
│   └── harden.py               # Asset hardening
├── ui/
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.jsx
│       ├── config.js
│       ├── index.js
│       ├── index.css
│       ├── components/
│       │   ├── ChatInterface.jsx
│       │   ├── Dashboard.jsx
│       │   └── Sidebar.jsx
│       └── services/
│           ├── agent.js
│           ├── auth.js
│           └── storage.js
└── README.md
```

## GRCP Platform

SLyK-53 is part of the GRCP (GRC Platform) family:

| Tool | Description | Access |
|------|-------------|--------|
| **SAELAR** | Full-featured compliance dashboard | EC2: port 8484 |
| **SOPRA** | Security operations and remediation | EC2: port 4444 |
| **SLyK-53** | Serverless AI assistant | Bedrock Console / CloudFront |

## Support

For issues or questions, contact the SAE Team.
