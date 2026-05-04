# GRCP — CI/CD Pipeline Documentation

## U.S. Department of Commerce (DOC) | NOAA | NESDIS
### Office of Satellite and Product Operations (OSPO) — CyberSecurity Division (CSD)

**Version:** 2.0
**Date:** April 28, 2026
**Prepared by:** SAE Team

---

## Record of Changes

| Version | Date | Description | Changed By |
|---|---|---|---|
| 1.0 | 04/14/2026 | Initial pipeline documentation. | SAE Team |
| 2.0 | 04/28/2026 | Updated to GRCP naming; added SLyK-53 serverless deployment; added service naming conventions; updated architecture diagrams. | SAE Team |

---

## 1. Overview

The SAE Team has implemented a fully automated Continuous Integration / Continuous Deployment (CI/CD) pipeline for the GRCP (GRC Platform) tool suite. The pipeline supports two deployment models:

- **EC2-based tools** (SAELAR-53, SOPRA, BeeKeeper) — deployed via S3 deploy agent to GRC_Titan
- **Serverless tools** (SLyK-53) — deployed via CloudShell to Lambda + Bedrock

All deployments are zero-SSH — code is packaged, uploaded, and deployed without manual server access.

---

## 2. GRCP Platform Components

| Tool | Service Name | Port | Deployment Model | Location |
|---|---|---|---|---|
| SAELAR-53 | grcp-saelar | 8484 | EC2 (Streamlit) | /home/ec2-user/grcp/saelar/ |
| SOPRA | grcp-sopra | 4444 | EC2 (Streamlit) | /home/ec2-user/grcp/sopra/ |
| BeeKeeper | grcp-beekeeper | 4445 | EC2 (Streamlit) | /home/ec2-user/grcp/beekeeper/ |
| SLyK-53 | grcp-slyk | N/A | Serverless (Lambda + Bedrock) | AWS managed |

---

## 3. Architecture

### 3.1 EC2 Deployment Pipeline (SAELAR, SOPRA, BeeKeeper)

```
Developer pushes code
        ↓
AWS CodeCommit (SAELAR-53 repo, main branch)
        ↓ (auto-detected by CodePipeline)
AWS CodePipeline (ospo-csta)
        ↓
AWS CodeBuild (grcp-deploy-build)
  - Packages application into ZIP artifact
  - Excludes .git, __pycache__, venv, credentials
  - Uploads to S3
        ↓
Amazon S3 (s3://saelarallpurpose/deployments/grcp-latest.zip)
        ↓ (polled every 60 seconds)
EC2 Deploy Agent (grcp-deploy-agent.service)
  - Detects new artifact via ETag comparison
  - Stops running GRCP services
  - Backs up current state
  - Extracts new files
  - Updates dependencies
  - Restarts services
        ↓
GRC_Titan EC2 (i-0f5ecc5cc369e85fe)
  - grcp-saelar  → port 8484
  - grcp-sopra   → port 4444
  - grcp-beekeeper → port 4445
```

### 3.2 Serverless Deployment Pipeline (SLyK-53)

```
Developer runs deploy_slyk.py in CloudShell
        ↓
Script creates/updates:
  - 5 Lambda functions (slyk-assess, slyk-remediate,
    slyk-harden, slyk-alert-triage, slyk-runbooks)
  - Bedrock Agent (SLyK-53-Security-Assistant)
  - 5 Action Groups (ASSESS, REMEDIATE, HARDEN, TRIAGE, RUNBOOKS)
  - EventBridge Rule (SLyK-53-SecurityHub-HighRisk)
  - SNS Topic (SLyK-53-Security-Alerts)
        ↓
SLyK-53 accessible in AWS Console → Bedrock → Agents
```

### 3.3 Combined Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         GRCP CI/CD Pipeline                           │
│                                                                        │
│  ┌─────────────┐      ┌──────────────┐      ┌─────────────────┐     │
│  │ CodeCommit   │ ───> │ CodePipeline  │ ───> │ CodeBuild       │     │
│  │ (SAELAR-53)  │      │ (ospo-csta)   │      │ (grcp-deploy-   │     │
│  │              │      │               │      │  build)          │     │
│  └──────────────┘      └───────────────┘      └────────┬────────┘     │
│                                                         │              │
│                                                         ▼              │
│                                               ┌─────────────────┐     │
│                                               │ S3 Artifact      │     │
│                                               │ grcp-latest.zip  │     │
│                                               └────────┬────────┘     │
│                                                         │              │
│                              ┌──────────────────────────┘              │
│                              │ (polled every 60s)                      │
│                              ▼                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                    GRC_Titan EC2                                │    │
│  │                    (i-0f5ecc5cc369e85fe)                        │    │
│  │                                                                 │    │
│  │  ┌─────────────────┐  ┌──────────┐  ┌──────────────────┐     │    │
│  │  │ grcp-deploy-     │  │ grcp-    │  │ grcp-sopra       │     │    │
│  │  │ agent            │  │ saelar   │  │ (port 4444)      │     │    │
│  │  │ (polls S3)       │  │ (8484)   │  │                  │     │    │
│  │  └─────────────────┘  └──────────┘  └──────────────────┘     │    │
│  │                                                                 │    │
│  │  ┌──────────────────┐                                          │    │
│  │  │ grcp-beekeeper   │                                          │    │
│  │  │ (port 4445)      │                                          │    │
│  │  └──────────────────┘                                          │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                 SLyK-53 (Serverless)                            │    │
│  │                                                                 │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │    │
│  │  │ slyk-    │ │ slyk-    │ │ slyk-    │ │ slyk-    │         │    │
│  │  │ assess   │ │ remediate│ │ harden   │ │ alert-   │         │    │
│  │  │ (Lambda) │ │ (Lambda) │ │ (Lambda) │ │ triage   │         │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │    │
│  │  ┌──────────┐ ┌──────────────────────────┐                     │    │
│  │  │ slyk-    │ │ SLyK-53-Security-         │                     │    │
│  │  │ runbooks │ │ Assistant (Bedrock Agent)  │                     │    │
│  │  │ (Lambda) │ │                            │                     │    │
│  │  └──────────┘ └──────────────────────────┘                     │    │
│  │  ┌──────────────────────┐ ┌────────────────────────┐           │    │
│  │  │ EventBridge Rule     │ │ SNS Topic              │           │    │
│  │  │ (CRITICAL/HIGH)      │ │ (SLyK-53-Security-     │           │    │
│  │  │                      │ │  Alerts)               │           │    │
│  │  └──────────────────────┘ └────────────────────────┘           │    │
│  └───────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Pipeline Components

### 4.1 Source Stage — AWS CodeCommit

| Parameter | Value |
|---|---|
| Repository | SAELAR-53 |
| Branch | main |
| Trigger | Automatic on push (PollForSourceChanges) |
| Region | us-east-1 |

### 4.2 Build Stage — AWS CodeBuild

| Parameter | Value |
|---|---|
| Project Name | sae-grc-deploy-build |
| Build Environment | Amazon Linux 2, x86_64, BUILD_GENERAL1_SMALL |
| Service Role | LambdaCodeBuildRole |
| Artifact Output | s3://saelarallpurpose/deployments/grcp-latest.zip |

### 4.3 Artifact Storage — Amazon S3

| Parameter | Value |
|---|---|
| Bucket | saelarallpurpose |
| EC2 Artifact Key | deployments/grcp-latest.zip |
| SLyK Config | slyk/slyk_config.json |
| SLyK Alerts | slyk/alerts/ |
| SLyK Runbook Results | slyk/runbook_results/ |
| Pipeline Artifact Bucket | codepipeline-us-east-1-724312423486 |

### 4.4 EC2 Deployment — GRCP Deploy Agent

| Parameter | Value |
|---|---|
| Service Name | grcp-deploy-agent.service |
| Target Directory | /home/ec2-user/grcp/ |
| Poll Interval | 60 seconds |
| Detection Method | S3 ETag comparison |
| Backup Location | /home/ec2-user/.grcp_backups/ |
| Backup Retention | Last 5 deployments |

### 4.5 SLyK-53 Serverless Components

| Component | Resource Name | Type |
|---|---|---|
| Lambda | slyk-assess | NIST assessment + Security Hub |
| Lambda | slyk-remediate | Remediation script generation |
| Lambda | slyk-harden | Asset hardening (S3, EC2, IAM) |
| Lambda | slyk-alert-triage | EventBridge-triggered alert handler |
| Lambda | slyk-runbooks | ISSO runbook execution engine |
| Bedrock Agent | SLyK-53-Security-Assistant | Agentic AI orchestrator |
| EventBridge Rule | SLyK-53-SecurityHub-HighRisk | CRITICAL/HIGH finding trigger |
| SNS Topic | SLyK-53-Security-Alerts | Email/Slack notifications |

---

## 5. Service Naming Convention

All GRCP services follow the `grcp-` prefix convention:

| Service | systemctl Name | Description |
|---|---|---|
| SAELAR-53 | grcp-saelar | NIST assessment platform |
| SOPRA | grcp-sopra | On-premise risk assessment |
| BeeKeeper | grcp-beekeeper | Container security scanner |
| SLyK-53 | grcp-slyk | Serverless AI assistant (Lambda) |
| Deploy Agent | grcp-deploy-agent | S3 artifact polling agent |

**Useful commands:**

```bash
# Check all GRCP services
sudo systemctl status grcp-saelar grcp-sopra grcp-beekeeper grcp-deploy-agent

# Restart a specific tool
sudo systemctl restart grcp-saelar

# View logs
sudo journalctl -u grcp-saelar -f
sudo journalctl -u grcp-deploy-agent -f
```

---

## 6. EC2 Target Environment

### 6.1 Instance Details

| Parameter | Value |
|---|---|
| Instance ID | i-0f5ecc5cc369e85fe |
| Name | GRC_Titan |
| Instance Type | t5a.medium |
| Private IP | 10.40.25.184 |
| IAM Role | saelar-role |
| Subnet | subnet-0001ee907af2db1fe |
| Security Group | sg-08852ba5ab72e1159 |
| OS | Amazon Linux 2023 |

### 6.2 Directory Structure

```
/home/ec2-user/grcp/
├── saelar/              ← SAELAR-53 (grcp-saelar, port 8484)
├── sopra/               ← SOPRA (grcp-sopra, port 4444)
├── beekeeper/           ← BeeKeeper (grcp-beekeeper, port 4445)
└── <future_tool>/       ← Any new GRCP tool
```

### 6.3 Running Services

| Service | Port | Status |
|---|---|---|
| grcp-saelar | 8484 | Active (auto-start, auto-restart) |
| grcp-sopra | 4444 | Active (auto-start, auto-restart) |
| grcp-deploy-agent | N/A | Active (polls S3 every 60s) |
| codedeploy-agent | N/A | Active (standby) |

### 6.4 External Access

| Tool | Internal | External |
|---|---|---|
| SAELAR-53 | http://10.40.25.184:8484 | https://nih-saelar.nesdis-hq.noaa.gov:4443/ |
| SOPRA | http://10.40.25.184:4444 | https://nih-sopra.nesdis-hq.noaa.gov:4444/ |
| SLyK-53 | N/A (serverless) | AWS Console → Bedrock → Agents |

---

## 7. Deployment Methods

### 7.1 Automatic (via CodePipeline) — EC2 Tools

Push code to the SAELAR-53 CodeCommit repository on the `main` branch. The pipeline triggers automatically.

```bash
# From CloudShell — push a file to CodeCommit
PARENT=$(aws codecommit get-branch --repository-name SAELAR-53 --branch-name main --query 'branch.commitId' --output text)
aws codecommit put-file \
    --repository-name SAELAR-53 --branch-name main \
    --file-path "nist_setup.py" --file-content fileb://nist_setup.py \
    --parent-commit-id "$PARENT" \
    --commit-message "Update nist_setup.py" \
    --name "SAE Team" --email "sae@noaa.gov" --region us-east-1
```

Deployment completes within ~3 minutes (CodeBuild + 60-second poll).

### 7.2 Manual Quick Deploy — EC2 Tools

Skip CodePipeline and push straight to S3 from CloudShell:

```bash
cd /path/to/your/project
zip -r /tmp/grcp-latest.zip . -x '.git/*' 'venv/*' '__pycache__/*'
aws s3 cp /tmp/grcp-latest.zip s3://saelarallpurpose/deployments/grcp-latest.zip
```

The EC2 deploy agent picks it up within 60 seconds.

### 7.3 SLyK-53 Deployment (Serverless)

Deploy or update from CloudShell:

```bash
cd ~/slyk
python3 deploy_slyk.py
```

Creates/updates all Lambda functions, Bedrock Agent, EventBridge rule, and SNS topic.

---

## 8. IAM Roles

| Role | Used By | Purpose |
|---|---|---|
| saelar-role | GRC_Titan EC2 instance | EC2 instance profile — access to AWS services |
| SLyK-Lambda-Role | 5 slyk-* Lambda functions | ReadOnlyAccess + scoped hardening writes |
| SLyK-Agent-Role | Bedrock Agent | InvokeModel + InvokeFunction |
| LambdaCodeBuildRole | CodeBuild | Build and upload artifacts |
| codedeploy | CodeDeploy (standby) | EC2 deployment (future use) |
| codepipeline | CodePipeline | Pipeline orchestration |

---

## 9. Monitoring and Troubleshooting

### 9.1 Pipeline Status

```bash
aws codepipeline get-pipeline-state --name ospo-csta \
    --query 'stageStates[*].{Stage:stageName,Status:latestExecution.status}' --output table
```

### 9.2 CodeBuild Logs

```bash
aws codebuild list-builds-for-project --project-name sae-grc-deploy-build --max-items 5
```

### 9.3 EC2 Deploy Agent Logs

```bash
sudo journalctl -u grcp-deploy-agent -f           # live
sudo journalctl -u grcp-deploy-agent --since "1 hour ago"
```

### 9.4 GRCP Service Logs

```bash
sudo journalctl -u grcp-saelar -f                 # SAELAR logs
sudo journalctl -u grcp-sopra -f                   # SOPRA logs
sudo systemctl status grcp-saelar grcp-sopra       # status check
```

### 9.5 SLyK-53 Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/slyk-assess --follow
aws logs tail /aws/lambda/slyk-alert-triage --follow

# Agent status
aws bedrock-agent list-agents --query 'agentSummaries[?agentName==`SLyK-53-Security-Assistant`].{ID:agentId,Status:agentStatus}' --output table --region us-east-1
```

### 9.6 Deployment History

```bash
# EC2 deployments
cat /home/ec2-user/.grcp_deploy_state/deploy_history.log

# SLyK runbook history
aws s3 ls s3://saelarallpurpose/slyk/runbook_results/ --recursive

# SLyK alert history
aws s3 ls s3://saelarallpurpose/slyk/alerts/ --recursive
```

### 9.7 Rollback (EC2 Tools)

```bash
sudo bash
BACKUP=$(ls -dt /home/ec2-user/.grcp_backups/*/ | head -1)
systemctl stop grcp-saelar grcp-sopra
cp -r "$BACKUP/grcp/"* /home/ec2-user/grcp/
chown -R ec2-user:ec2-user /home/ec2-user/grcp
systemctl start grcp-saelar grcp-sopra
```

---

## 10. Adding a New GRCP Tool

To add a new tool to the platform:

**For EC2-based tools:**

1. Create a new subdirectory in `/home/ec2-user/grcp/` (e.g., `newtool/`)
2. Include `requirements.txt` and a launch script
3. Create a systemd service file: `grcp-newtool.service`
4. Enable: `sudo systemctl enable grcp-newtool`
5. The deploy agent will automatically process it on next deployment

**For serverless tools:**

1. Create Lambda function(s) with `slyk-` or `grcp-` prefix
2. Add action group to existing Bedrock Agent, or create a new agent
3. Update `deploy_slyk.py` to include the new functions
4. Run `python3 deploy_slyk.py` from CloudShell

---

## 11. Security Controls

| Control | Implementation |
|---|---|
| Authentication | EC2: IAM instance role. SLyK: IAM Console session. No separate credentials. |
| Encryption in Transit | S3 over HTTPS. CodeCommit over HTTPS. Bedrock over HTTPS. |
| Encryption at Rest | S3 default encryption (SSE-S3). |
| Access Control | CodeCommit via IAM. EC2 via Session Manager. SLyK via Console. |
| Credential Management | No static credentials. IAM role assumption only. |
| Audit Trail | CloudTrail logs all API calls. Deploy history in S3. Runbook results in S3. |
| Backup | EC2: last 5 deployment states retained. SLyK: stateless (Lambda redeployable). |
| Rollback | EC2: restore from backup. SLyK: redeploy previous version. |
| Network | EC2 on private subnet. No public IP. Load balancer for external access. |

---

## 12. Cost

| Component | Monthly Cost |
|---|---|
| **EC2 Pipeline** | |
| CodeCommit | Free (first 5 users) |
| CodePipeline | $1.00/pipeline |
| CodeBuild | ~$0.50 (minimal builds) |
| S3 (artifacts) | <$0.10 |
| EC2 (GRC_Titan) | ~$50 (t5a.medium) |
| **EC2 Subtotal** | **~$52/month** |
| | |
| **SLyK-53 Serverless** | |
| Lambda (5 functions) | $5–20 |
| Bedrock Agent | ~$0 |
| Bedrock model calls | $10–50 |
| EventBridge | ~$0 |
| SNS | ~$0 |
| S3 (config + audit) | ~$1 |
| **SLyK Subtotal** | **~$16–71/month** |
| | |
| **GRCP Total** | **~$68–123/month** |

---

## 13. References

- AWS CodePipeline: https://docs.aws.amazon.com/codepipeline/
- AWS CodeBuild: https://docs.aws.amazon.com/codebuild/
- AWS CodeCommit: https://docs.aws.amazon.com/codecommit/
- Amazon Bedrock Agents: https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html
- Amazon EventBridge: https://docs.aws.amazon.com/eventbridge/latest/userguide/
- SAELAR-53: https://nih-saelar.nesdis-hq.noaa.gov:4443/
- SOPRA: https://nih-sopra.nesdis-hq.noaa.gov:4444/
- SLyK-53: AWS Console → Amazon Bedrock → Agents → SLyK-53-Security-Assistant
