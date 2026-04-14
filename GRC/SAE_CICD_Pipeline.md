# SAE GRC Tools — CI/CD Pipeline Documentation

## U.S. Department of Commerce (DOC) | NOAA | NESDIS
### Office of Satellite and Product Operations (OSPO) — CyberSecurity Division (CSD)

**Version:** 1.0
**Date:** April 14, 2026
**Prepared by:** SAE Team

---

## 1. Overview

The SAE Team has implemented a fully automated Continuous Integration / Continuous Deployment (CI/CD) pipeline for deploying GRC tools (SAELAR-53, SOPRA, BeeKeeper, and future applications) to the CSTA AWS environment. The pipeline enables zero-SSH deployments — code pushed to the repository is automatically packaged, uploaded, and deployed to the target EC2 instance without manual intervention.

---

## 2. Architecture

```
Developer pushes code
        ↓
AWS CodeCommit (SAELAR-53 repo, main branch)
        ↓ (auto-detected by CodePipeline)
AWS CodePipeline (ospo-csta)
        ↓
AWS CodeBuild (sae-grc-deploy-build)
  - Packages application into ZIP artifact
  - Excludes .git, __pycache__, venv, credentials
  - Uploads to S3
        ↓
Amazon S3 (s3://saelarallpurpose/deployments/grc-tools-latest.zip)
        ↓ (polled every 60 seconds)
EC2 Deploy Agent (grc-deploy-agent.service)
  - Detects new artifact via ETag comparison
  - Stops running GRC services
  - Backs up current state
  - Extracts new files
  - Updates dependencies
  - Restarts services
        ↓
GRC_Titan EC2 (i-0f5ecc5cc369e85fe)
  - Applications live at /home/ec2-user/grc_tools/
  - SAELAR runs on port 8484
  - Accessible via https://nih-saelar.nesdis-hq.noaa.gov:4443/
```

---

## 3. Pipeline Components

### 3.1 Source Stage — AWS CodeCommit

| Parameter | Value |
|---|---|
| Repository | SAELAR-53 |
| Branch | main |
| Trigger | Automatic on push (PollForSourceChanges) |
| Region | us-east-1 |

CodeCommit serves as the authoritative source repository for SAELAR-53 and other GRC tools within the AWS boundary. Code changes pushed to the `main` branch automatically trigger the pipeline.

### 3.2 Build Stage — AWS CodeBuild

| Parameter | Value |
|---|---|
| Project Name | sae-grc-deploy-build |
| Build Environment | Amazon Linux 2, x86_64, BUILD_GENERAL1_SMALL |
| Service Role | LambdaCodeBuildRole |
| Artifact Output | s3://saelarallpurpose/deployments/grc-tools-latest.zip |

CodeBuild executes the following steps:
1. Checks out source from CodeCommit
2. Packages all application files into a ZIP artifact, excluding development files (.git, __pycache__, .pyc, .env, .pem, .key, venv)
3. Uploads the artifact to the S3 deployments prefix

### 3.3 Artifact Storage — Amazon S3

| Parameter | Value |
|---|---|
| Bucket | saelarallpurpose |
| Artifact Key | deployments/grc-tools-latest.zip |
| Pipeline Artifact Bucket | codepipeline-us-east-1-724312423486 |

The S3 bucket serves dual purpose:
- **Pipeline artifacts**: CodeBuild output stored for deployment
- **Application data**: Assessment results, SSPs, POA&Ms, and other GRC documents

### 3.4 Deployment — EC2 S3 Deploy Agent

| Parameter | Value |
|---|---|
| Service Name | grc-deploy-agent.service |
| Target Directory | /home/ec2-user/grc_tools/ |
| Poll Interval | 60 seconds |
| Detection Method | S3 ETag comparison |
| Backup Location | /home/ec2-user/.grc_backups/ |
| Backup Retention | Last 5 deployments |

The deploy agent is a systemd service running on the EC2 instance that continuously polls S3 for new artifacts. When a new artifact is detected (via ETag change), it:

1. **Downloads** the new artifact from S3
2. **Stops** all running GRC services (saelar, sopra, beekeeper)
3. **Backs up** the current application state
4. **Extracts** new files to /home/ec2-user/grc_tools/
5. **Sets permissions** (chown ec2-user)
6. **Updates dependencies** for each application (pip install -r requirements.txt)
7. **Restarts** all registered systemd services
8. **Records** the deployment in the deploy history log

---

## 4. EC2 Target Environment

### 4.1 Instance Details

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

### 4.2 Directory Structure

```
/home/ec2-user/grc_tools/
├── saelar/              ← SAELAR-53 (active)
├── sopra/               ← SOPRA (future)
├── beekeeper/           ← BeeKeeper (future)
└── <new_app>/           ← Any future GRC tool
```

### 4.3 Running Services

| Service | Port | Description |
|---|---|---|
| saelar.service | 8484 | SAELAR-53 NIST assessment platform |
| grc-deploy-agent.service | N/A | S3 deploy agent (polls for updates) |
| codedeploy-agent.service | N/A | AWS CodeDeploy agent (standby for future use) |

---

## 5. Deployment Methods

### 5.1 Automatic (via CodePipeline)

Push code to the SAELAR-53 CodeCommit repository on the `main` branch. The pipeline triggers automatically.

```bash
git push origin main
```

Deployment completes within approximately 2-3 minutes (CodeBuild build time + 60-second poll interval).

### 5.2 Manual Quick Deploy (via CloudShell)

For immediate deployments without going through CodePipeline:

```bash
cd /path/to/your/project
zip -r /tmp/grc-tools-latest.zip . -x '.git/*' 'venv/*' '__pycache__/*'
aws s3 cp /tmp/grc-tools-latest.zip s3://saelarallpurpose/deployments/grc-tools-latest.zip
```

The EC2 deploy agent picks up the artifact within 60 seconds.

---

## 6. Monitoring and Troubleshooting

### 6.1 Pipeline Status

```bash
aws codepipeline get-pipeline-state --name ospo-csta \
  --query 'stageStates[*].{Stage:stageName,Status:latestExecution.status}' \
  --output table
```

### 6.2 CodeBuild Logs

```bash
aws codebuild list-builds-for-project --project-name sae-grc-deploy-build --max-items 5
aws codebuild batch-get-builds --ids <build-id> --query 'builds[0].buildStatus'
```

### 6.3 Deploy Agent Logs (on EC2)

```bash
sudo journalctl -u grc-deploy-agent -f           # live logs
sudo journalctl -u grc-deploy-agent --since "1 hour ago"  # recent logs
sudo systemctl status grc-deploy-agent            # service status
```

### 6.4 SAELAR Service Logs (on EC2)

```bash
sudo journalctl -u saelar -f                     # live logs
sudo systemctl status saelar                      # service status
```

### 6.5 Deployment History (on EC2)

```bash
cat /home/ec2-user/.grc_deploy_state/deploy_history.log
```

### 6.6 Rollback

Backups are stored automatically. To rollback to a previous version:

```bash
sudo bash
BACKUP=$(ls -dt /home/ec2-user/.grc_backups/*/ | head -1)
systemctl stop saelar
cp -r "$BACKUP/grc_tools/"* /home/ec2-user/grc_tools/
chown -R ec2-user:ec2-user /home/ec2-user/grc_tools
systemctl start saelar
```

---

## 7. Security Considerations

| Control | Implementation |
|---|---|
| **Authentication** | All AWS API calls authenticated via IAM instance role (saelar-role) |
| **Encryption in Transit** | S3 transfers over HTTPS; CodeCommit over HTTPS |
| **Encryption at Rest** | S3 bucket uses default encryption (SSE-S3) |
| **Access Control** | CodeCommit access governed by IAM policies; EC2 access via Session Manager |
| **Credential Management** | No static credentials; IAM role assumption only |
| **Audit Trail** | CloudTrail logs all CodeCommit, CodeBuild, CodePipeline, and S3 API calls |
| **Backup** | Last 5 deployment states retained automatically |
| **Rollback** | Automatic rollback on deployment failure; manual rollback available via backups |
| **Network** | EC2 on private subnet; no public IP; accessible only through load balancer and Session Manager |

---

## 8. Adding a New Application

To add a new GRC tool to the pipeline:

1. Create a new subdirectory in the repository (e.g., `sopra/`)
2. Include a `requirements.txt` if the app has Python dependencies
3. Include a `start_<appname>.sh` launch script
4. Create a systemd service file on the EC2 for the app
5. Push to CodeCommit — the deploy agent will automatically deploy it alongside existing apps

The deploy agent iterates over all subdirectories in `/home/ec2-user/grc_tools/` and processes each independently.

---

## 9. Cost

| Component | Monthly Cost |
|---|---|
| CodeCommit | Free (first 5 users) |
| CodePipeline | $1.00/pipeline/month |
| CodeBuild | ~$0.50/month (BUILD_GENERAL1_SMALL, minimal builds) |
| S3 Storage | <$0.10/month (deployment artifacts) |
| EC2 (existing) | ~$50/month (t5a.medium, already provisioned) |
| **Total Pipeline Cost** | **~$1.60/month** |

---

## 10. References

- AWS CodePipeline: https://docs.aws.amazon.com/codepipeline/
- AWS CodeBuild: https://docs.aws.amazon.com/codebuild/
- AWS CodeCommit: https://docs.aws.amazon.com/codecommit/
- SAELAR-53: https://nih-saelar.nesdis-hq.noaa.gov:4443/
