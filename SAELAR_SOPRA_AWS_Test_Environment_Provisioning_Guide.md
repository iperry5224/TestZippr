# SAELAR & SOPRA — AWS Test Environment Provisioning Guide

**Audience:** System administrators provisioning SAELAR and SOPRA in an AWS test/sandbox account  
**Classification:** Internal  
**Last Updated:** March 2026  
**Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [VPC & Network Requirements](#3-vpc--network-requirements)
4. [EC2 Instance Specifications](#4-ec2-instance-specifications)
5. [IAM Roles & Permissions](#5-iam-roles--permissions)
6. [AWS Services to Enable](#6-aws-services-to-enable)
7. [Software Stack](#7-software-stack)
8. [Security Group Rules (Exact)](#8-security-group-rules-exact)
9. [File Layout & Paths](#9-file-layout--paths)
10. [Verification Checklist](#10-verification-checklist)
11. [Appendix A: Full IAM Policy JSON](#appendix-a-full-iam-policy-json)
12. [Appendix B: Python Requirements](#appendix-b-python-requirements)

---

## 1. Executive Summary

**SAELAR** (Security Assessment Engine for Live AWS Resources) and **SOPRA** (SAE On-Premise Risk Assessment) are web applications that run on a single EC2 instance in an AWS test environment. They require:

| Category | SAELAR | SOPRA |
|----------|--------|-------|
| **Port** | 8484 | 8080 |
| **Primary AWS Services** | Bedrock, STS, S3, IAM, EC2, CloudTrail, Config, Security Hub, GuardDuty, Inspector2, KMS, RDS, ELB, ACM, and 15+ others | Bedrock only |
| **Outbound Internet** | Yes (AWS APIs, CISA KEV catalog) | Yes (AWS Bedrock only) |
| **Database** | None (file-based) | None (file-based) |
| **Deployment** | Python + Streamlit | Python + Streamlit |

Both applications run as long-lived Streamlit processes. They use **instance profile** credentials (no stored access keys) when run on EC2.

---

## 2. Architecture Overview

### Deployment Modes

| Mode | SAELAR Port | SOPRA Port | Notes |
|------|-------------|------------|-------|
| **Non-containerized (recommended for test)** | 8484 | 8080 | Single EC2, Python venv, systemd or nohup |
| **Containerized (Docker)** | 8443 | 5224 | Two containers, different ports |

This guide focuses on the **non-containerized** setup (ports 8484 and 8080), which is the production reference.

### High-Level Diagram

```
Internet → [Security Group: 22, 80, 8080, 8484]
                ↓
         EC2 Instance (Ubuntu)
         ├── SAELAR (Streamlit on 8484)
         ├── SOPRA (Streamlit on 8080)
         └── nginx (optional, port 80 landing page)
                ↓
         IAM Instance Profile
                ↓
         AWS APIs (Bedrock, S3, IAM, EC2, etc.)
```

---

## 3. VPC & Network Requirements

### 3.1 Subnet

- **Subnet type:** Public (route to Internet Gateway for outbound)
- **Auto-assign public IP:** Enabled for the instance
- **Network ACL:** Default NACL (allow all) is sufficient; custom NACLs must allow inbound/egress for ports 22, 80, 8080, 8484

### 3.2 Outbound Connectivity (Egress)

The EC2 instance **must** have outbound internet access for:

| Destination | Port | Protocol | Purpose |
|-------------|------|----------|---------|
| **AWS APIs** (e.g. `*.amazonaws.com`) | 443 | HTTPS | Bedrock, S3, IAM, EC2, CloudTrail, Config, Security Hub, GuardDuty, Inspector, KMS, RDS, etc. |
| **CISA KEV Catalog** | 443 | HTTPS | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` — SAELAR fetches this for vulnerability mapping |
| **Python package index** (install time) | 443 | HTTPS | `pypi.org` — for `pip install` |

**No inbound connections from the internet are required** for AWS API calls (all outbound). Inbound is only for users accessing the web UIs (ports 80, 8080, 8484) and SSH (22).

---

## 4. EC2 Instance Specifications

### 4.1 Recommended Instance Types

| Use Case | Instance Type | vCPU | Memory | Notes |
|----------|---------------|------|--------|-------|
| **Minimum (test)** | t3.small | 2 | 4 GB | Adequate for both apps |
| **Recommended** | t3.medium | 2 | 4 GB | Better headroom for Bedrock + Streamlit |
| **Production** | t3.large | 2 | 8 GB | More concurrent users |

### 4.2 AMI & OS

- **AMI:** Ubuntu Server 22.04 LTS (64-bit x86)
- **SSH user:** `ubuntu` (NOT `ec2-user`)

### 4.3 Storage

- **Root volume:** 20 GB gp3 minimum (30 GB recommended for logs, documents)
- **Additional volumes:** None required

### 4.4 Placement

- **Subnet:** Public subnet with route `0.0.0.0/0 → igw-*`
- **Auto-assign Public IPv4:** Enabled
- **Elastic IP:** Optional; recommended if instance may be stopped/started (public IP changes otherwise)

---

## 5. IAM Roles & Permissions

### 5.1 Instance Profile

Create an IAM role with **trust policy** for EC2:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ec2.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
```

**Role name (example):** `SaelarSopraEC2Role`

### 5.2 Attach Instance Profile to EC2

- Create an **Instance Profile** with the same name as the role
- Attach the instance profile to the EC2 instance at launch (or later via EC2 console → Instance → Actions → Security → Modify IAM role)

### 5.3 Permissions by Application

| Application | Policy Scope | Notes |
|-------------|--------------|-------|
| **SAELAR** | Full cloud assessment | Requires 25+ AWS services; see Appendix A |
| **SOPRA** | Bedrock only | Minimal policy; see Section 5.5 |

### 5.4 SAELAR — Consolidated IAM Policy

SAELAR needs read-only (and limited write) access to the AWS account for NIST 800-53 assessment and document storage. **Full policy JSON** is in [Appendix A](#appendix-a-full-iam-policy-json).

**Service summary:**

| AWS Service | Actions (summary) | Purpose |
|-------------|-------------------|---------|
| STS | GetCallerIdentity | Credential validation |
| Bedrock | InvokeModel, Converse | AI (Chad, remediation) |
| S3 | List*, Get*, Put*, Delete*, GetBucket* | Document storage, NIST checks |
| IAM | ListUsers, ListAccessKeys, GetPolicyVersion, GetAccountPasswordPolicy, ListMfaDevices, ListRoles, etc. | NIST AC-2, IA-2, AC-3 |
| EC2 | DescribeVpcs, DescribeInstances, DescribeSecurityGroups, DescribeVolumes, etc. | NIST network/config |
| CloudTrail | DescribeTrails, GetTrailStatus, GetEventSelectors | NIST AU-2, AU-12 |
| CloudWatch | DescribeAlarms | NIST AU-6 |
| CloudWatch Logs | DescribeLogGroups | NIST AU-3 |
| Config | DescribeConfigurationRecorders, DescribeConfigRules, GetComplianceDetailsByConfigRule, etc. | NIST CM-6, CA-7 |
| Security Hub | DescribeHub, GetEnabledStandards, GetFindings | Findings |
| GuardDuty | ListDetectors, GetFindingsStatistics, ListFindings | NIST SI-4, IR-4 |
| Inspector2 | ListFindingAggregations, ListFindings | NIST RA-5 |
| KMS | ListKeys, DescribeKey, GetKeyRotationStatus | NIST SC-28 |
| RDS | DescribeDBInstances | NIST CP-10, SC-28 |
| ELBv2 | DescribeLoadBalancers, DescribeListeners | NIST SC-8 |
| ACM | ListCertificates | NIST SC-8 |
| Backup | ListBackupPlans | NIST CP-9 |
| CodePipeline | ListPipelines | NIST SA-3 |
| CodeBuild | ListProjects | NIST SA-3 |
| SSM | ListAssociations, DescribePatchBaselines, ListComplianceSummaries | NIST SI-2 |
| SNS | ListTopics | NIST IR-4 |
| Lambda | ListFunctions | NIST CM-8 |
| Secrets Manager | ListSecrets | NIST SC-28 |
| Auto Scaling | DescribeAutoScalingGroups | NIST CP-10 |
| ECR | DescribeRepositories | NIST SR-3 |

### 5.5 SOPRA — Minimal IAM Policy

SOPRA uses **only** Bedrock for AI features. Attach this policy for SOPRA-only or combined role:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "bedrock:InvokeModel",
      "bedrock-runtime:InvokeModel",
      "bedrock-runtime:Converse"
    ],
    "Resource": "*"
  }]
}
```

**Combined role:** Attach both the SAELAR policy (Appendix A) and the SOPRA Bedrock policy to the same role. The SOPRA policy is a subset; SAELAR policy already includes Bedrock.

---

## 6. AWS Services to Enable

### 6.1 Required (Both Applications)

| Service | Region | Action |
|---------|--------|--------|
| **Amazon Bedrock** | Same as EC2 | Enable in Bedrock console; request model access (e.g. Titan Text, Llama, Mistral) |

**Bedrock model access:** In AWS Console → Bedrock → Model access, request access to at least one text model (e.g. `us.anthropic.claude-v2`, `amazon.titan-text-express-v1`). Without this, AI features will fall back to templates.

### 6.2 Optional (SAELAR Full Assessment)

SAELAR will still run if these are not enabled, but corresponding NIST checks will show as "not applicable" or "service not enabled":

| Service | Purpose |
|---------|---------|
| AWS Config | Configuration compliance |
| Security Hub | Security findings |
| GuardDuty | Threat detection |
| Inspector v2 | Vulnerability scanning |
| CloudTrail | Audit logging |

Enable in the same region as the EC2 instance and the AWS account being assessed.

### 6.3 S3 Bucket (SAELAR Document Storage)

- **Create:** One S3 bucket for SSP, POA&M, and document storage
- **Naming:** e.g. `saelar-docs-<account-id>-<region>`
- **Permissions:** IAM role must have `s3:ListBucket`, `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on the bucket (and `s3:ListAllMyBuckets` for bucket selection)
- **Encryption:** SSE-S3 or SSE-KMS recommended

---

## 7. Software Stack

### 7.1 Operating System

- **OS:** Ubuntu 22.04 LTS
- **Architecture:** x86_64 (amd64)

### 7.2 Python

- **Version:** Python 3.10 or 3.11
- **Install:** `sudo apt update && sudo apt install -y python3 python3-pip python3-venv`

### 7.3 System Packages

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx curl unzip
```

- **nginx:** Optional; used for port 80 landing page with links to SAELAR/SOPRA
- **curl:** For health checks and CISA KEV fetch
- **unzip:** For extracting deployment packages

### 7.4 Python Virtual Environment

Create a dedicated venv for SAELAR/SOPRA:

```bash
python3 -m venv /opt/apps/venv
/opt/apps/venv/bin/pip install --upgrade pip
```

### 7.5 Python Dependencies

Install into the venv. **Exact package list** in [Appendix B](#appendix-b-python-requirements). Core packages:

| Package | Minimum Version | Purpose |
|---------|-----------------|---------|
| boto3 | 1.34.0 | AWS SDK |
| streamlit | 1.29.0 | Web UI |
| pandas | 2.0.0 | Data processing |
| python-docx | 1.1.0 | Document generation |
| plotly | 5.18.0 | Charts |
| requests | 2.31.0 | HTTP (CISA KEV) |
| openpyxl | 3.1.0 | Excel support |
| XlsxWriter | 3.1.0 | Excel export |
| python-dateutil | 2.8.0 | Date handling |
| rich | 13.0.0 | CLI formatting |
| tabulate | 0.9.0 | Tables |

---

## 8. Security Group Rules (Exact)

Create a security group (e.g. `saelar-sopra-sg`) with the following **inbound** rules:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | 0.0.0.0/0 (or restrict to admin IPs) | SSH access |
| Custom TCP | TCP | 8080 | 0.0.0.0/0 (or restrict) | SOPRA web UI |
| Custom TCP | TCP | 8484 | 0.0.0.0/0 (or restrict) | SAELAR web UI |
| HTTP | TCP | 80 | 0.0.0.0/0 (or restrict) | Optional landing page |

**Restrict source** in production: Replace `0.0.0.0/0` with your organization's IP range (e.g. `10.0.0.0/8` or specific VPN CIDR).

**Outbound:** Default allow all (or allow 443 to 0.0.0.0/0 for HTTPS, plus any internal VPC requirements).

### AWS CLI — Add Rules

```bash
aws ec2 authorize-security-group-ingress --group-id sg-XXXXXXXX \
  --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id sg-XXXXXXXX \
  --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id sg-XXXXXXXX \
  --protocol tcp --port 8080 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id sg-XXXXXXXX \
  --protocol tcp --port 8484 --cidr 0.0.0.0/0
```

---

## 9. File Layout & Paths

### 9.1 Non-Containerized Layout

```
/opt/apps/
├── venv/                    # Python virtual environment
├── nist_setup.py            # SAELAR entry point
├── nist_dashboard.py        # SAELAR UI components
├── nist_800_53_rev5_full.py # SAELAR assessment engine
├── ssp_generator.py         # SSP/POA&M generator
├── sopra_setup.py           # SOPRA entry point
├── sopra_controls.py        # SOPRA control definitions
├── sopra/                   # SOPRA module
├── demo_csv_data/           # SOPRA demo data
└── (other supporting files)
```

### 9.2 Start Commands

**SAELAR:**
```bash
/opt/apps/venv/bin/streamlit run nist_setup.py \
  --server.port 8484 \
  --server.address 0.0.0.0 \
  --server.headless true
```

**SOPRA:**
```bash
/opt/apps/venv/bin/streamlit run sopra_setup.py \
  --server.port 8080 \
  --server.address 0.0.0.0 \
  --server.headless true
```

---

## 10. Verification Checklist

### Pre-Production

- [ ] EC2 instance in public subnet with public IP
- [ ] Security group allows 22, 80, 8080, 8484 from authorized IPs
- [ ] Instance profile attached with SAELAR + SOPRA IAM policies
- [ ] Bedrock model access enabled in account
- [ ] S3 bucket created (if using SAELAR document storage)
- [ ] Python 3.10+ and venv with all dependencies installed

### Post-Deploy

- [ ] SAELAR responds: `curl -s -o /dev/null -w '%{http_code}' http://<EC2-IP>:8484/` → 200
- [ ] SOPRA responds: `curl -s -o /dev/null -w '%{http_code}' http://<EC2-IP>:8080/` → 200
- [ ] AWS credentials work: In SAELAR, AWS Console tab shows account ID
- [ ] Bedrock works: Run a NIST assessment; Chad AI or remediation should respond (or show fallback message)

### Troubleshooting

| Symptom | Check |
|---------|-------|
| Connection timeout | Security group, NACL, instance firewall (ufw) |
| 500 / credential error | Instance profile attached? IAM policy includes required actions? |
| Bedrock "model not available" | Enable model access in Bedrock console |
| CISA KEV fetch fails | Outbound 443 to cisa.gov allowed |

---

## Appendix A: Full IAM Policy JSON

Attach this policy to the EC2 instance role for **SAELAR full cloud assessment**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Bedrock",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock-runtime:InvokeModel",
        "bedrock-runtime:Converse"
      ],
      "Resource": "*"
    },
    {
      "Sid": "STS",
      "Effect": "Allow",
      "Action": ["sts:GetCallerIdentity"],
      "Resource": "*"
    },
    {
      "Sid": "S3",
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetBucketEncryption",
        "s3:GetBucketPolicy",
        "s3:GetPublicAccessBlock",
        "s3:GetBucketLifecycleConfiguration"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAM",
      "Effect": "Allow",
      "Action": [
        "iam:ListUsers",
        "iam:ListAccessKeys",
        "iam:GetAccessKeyLastUsed",
        "iam:ListAttachedUserPolicies",
        "iam:ListPolicies",
        "iam:GetPolicyVersion",
        "iam:GetAccountPasswordPolicy",
        "iam:GetAccountSummary",
        "iam:ListMfaDevices",
        "iam:GetLoginProfile",
        "iam:ListRoles"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EC2",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVpcs",
        "ec2:DescribeFlowLogs",
        "ec2:DescribeNetworkAcls",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeInstances",
        "ec2:DescribeSnapshots",
        "ec2:DescribeVolumes",
        "ec2:DescribeInternetGateways",
        "ec2:GetEbsEncryptionByDefault"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudTrail",
      "Effect": "Allow",
      "Action": [
        "cloudtrail:DescribeTrails",
        "cloudtrail:GetTrailStatus",
        "cloudtrail:GetEventSelectors"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatch",
      "Effect": "Allow",
      "Action": ["cloudwatch:DescribeAlarms"],
      "Resource": "*"
    },
    {
      "Sid": "Logs",
      "Effect": "Allow",
      "Action": ["logs:DescribeLogGroups"],
      "Resource": "*"
    },
    {
      "Sid": "Config",
      "Effect": "Allow",
      "Action": [
        "config:DescribeConfigurationRecorders",
        "config:DescribeConfigurationRecorderStatus",
        "config:DescribeConfigRules",
        "config:GetComplianceDetailsByConfigRule",
        "config:GetDiscoveredResourceCounts"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecurityHub",
      "Effect": "Allow",
      "Action": [
        "securityhub:DescribeHub",
        "securityhub:GetEnabledStandards",
        "securityhub:GetFindings"
      ],
      "Resource": "*"
    },
    {
      "Sid": "GuardDuty",
      "Effect": "Allow",
      "Action": [
        "guardduty:ListDetectors",
        "guardduty:GetFindingsStatistics",
        "guardduty:ListFindings"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Inspector2",
      "Effect": "Allow",
      "Action": [
        "inspector2:ListFindingAggregations",
        "inspector2:ListFindings"
      ],
      "Resource": "*"
    },
    {
      "Sid": "KMS",
      "Effect": "Allow",
      "Action": [
        "kms:ListKeys",
        "kms:DescribeKey",
        "kms:GetKeyRotationStatus"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RDS",
      "Effect": "Allow",
      "Action": ["rds:DescribeDBInstances"],
      "Resource": "*"
    },
    {
      "Sid": "ELB",
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeListeners"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ACM",
      "Effect": "Allow",
      "Action": ["acm:ListCertificates"],
      "Resource": "*"
    },
    {
      "Sid": "Backup",
      "Effect": "Allow",
      "Action": ["backup:ListBackupPlans"],
      "Resource": "*"
    },
    {
      "Sid": "CodePipeline",
      "Effect": "Allow",
      "Action": ["codepipeline:ListPipelines"],
      "Resource": "*"
    },
    {
      "Sid": "CodeBuild",
      "Effect": "Allow",
      "Action": ["codebuild:ListProjects"],
      "Resource": "*"
    },
    {
      "Sid": "SSM",
      "Effect": "Allow",
      "Action": [
        "ssm:ListAssociations",
        "ssm:DescribePatchBaselines",
        "ssm:ListComplianceSummaries"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SNS",
      "Effect": "Allow",
      "Action": ["sns:ListTopics"],
      "Resource": "*"
    },
    {
      "Sid": "Lambda",
      "Effect": "Allow",
      "Action": ["lambda:ListFunctions"],
      "Resource": "*"
    },
    {
      "Sid": "SecretsManager",
      "Effect": "Allow",
      "Action": ["secretsmanager:ListSecrets"],
      "Resource": "*"
    },
    {
      "Sid": "AutoScaling",
      "Effect": "Allow",
      "Action": ["autoscaling:DescribeAutoScalingGroups"],
      "Resource": "*"
    },
    {
      "Sid": "ECR",
      "Effect": "Allow",
      "Action": ["ecr:DescribeRepositories"],
      "Resource": "*"
    }
  ]
}
```

---

## Appendix B: Python Requirements

Save as `requirements.txt` and install with `pip install -r requirements.txt`:

```
boto3>=1.34.0
botocore>=1.34.0
streamlit>=1.29.0
pandas>=2.0.0
numpy>=1.24.0
python-docx>=1.1.0
openpyxl>=3.1.0
XlsxWriter>=3.1.0
plotly>=5.18.0
python-dateutil>=2.8.0
requests>=2.31.0
rich>=13.0.0
tabulate>=0.9.0
```

---

*For questions or clarifications, contact the SAELAR/SOPRA development team.*
