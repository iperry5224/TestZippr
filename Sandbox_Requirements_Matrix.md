# SAELAR & SOPRA — Sandbox Requirements Matrix

Quick reference for roles, permissions, and ports needed in a new AWS cloud sandbox.

---

## 1. Ports

| Port | App | Protocol | Purpose |
|------|-----|----------|---------|
| **8443** | SAELAR | HTTP | SAELAR web UI (saelar_deploy default) |
| **8484** | SAELAR | HTTP | SAELAR web UI (deploy_to_aws default) |
| **8080** | SOPRA | HTTP | SOPRA web UI |
| **8501** | SOPRA | HTTP | SOPRA alternate port (Streamlit default) |
| **22** | Both | SSH | Remote access to EC2 |
| **11434** | SAELAR | HTTP | Ollama (air-gapped AI) — only if using local AI |

**Security Group:** Open inbound ports for the app(s) you run. Add your IP or `0.0.0.0/0` for testing.

---

## 2. IAM Roles

| Role | Trust | Purpose |
|------|-------|---------|
| **EC2 Instance Role** | `ec2.amazonaws.com` | Lets the instance call AWS APIs without access keys; used when SAELAR/SOPRA run on EC2 |
| **IAM User** | N/A | For local, Docker, or key-based auth; credentials validated via `sts:GetCallerIdentity` |

---

## 3. Permissions Matrix

| Service | Permission(s) | SAELAR | SOPRA | Why |
|---------|---------------|--------|-------|-----|
| **STS** | `sts:GetCallerIdentity` | ✓ | — | Credential check and account display |
| **Bedrock** | `bedrock:InvokeModel`, `bedrock-runtime:Converse` | ✓ | ✓ | AI (Chad, POA&M, remediation, etc.) |
| **S3** | `ListAllMyBuckets`, `ListBucket`, `GetObject`, `PutObject`, `DeleteObject`, `GetBucket*` | ✓ | — | Document upload, SSP/POA&M storage, NIST checks |
| **IAM** | `ListUsers`, `ListAccessKeys`, `GetAccessKeyLastUsed`, `ListPolicies`, `GetPolicyVersion`, `GetAccountPasswordPolicy`, `ListMfaDevices`, `ListRoles`, etc. | ✓ | — | NIST AC-2, IA-2, AC-3, IA-5 |
| **EC2** | `DescribeVpcs`, `DescribeFlowLogs`, `DescribeSecurityGroups`, `DescribeInstances`, `DescribeVolumes`, etc. | ✓ | — | NIST network/config assessment |
| **CloudTrail** | `DescribeTrails`, `GetTrailStatus`, `GetEventSelectors` | ✓ | — | NIST AU-2, AU-9, AU-12 |
| **CloudWatch** | `DescribeAlarms` | ✓ | — | NIST AU-6, SI-4 |
| **CloudWatch Logs** | `DescribeLogGroups` | ✓ | — | NIST AU-3 |
| **Config** | `DescribeConfigurationRecorders`, `DescribeConfigRules`, `GetComplianceDetailsByConfigRule`, etc. | ✓ | — | NIST CM-6, CA-7 |
| **Security Hub** | `DescribeHub`, `GetEnabledStandards`, `GetFindings` | ✓ | — | Findings and NIST mapping |
| **GuardDuty** | `ListDetectors`, `GetFindingsStatistics`, `ListFindings` | ✓ | — | NIST SI-4, IR-4 |
| **Inspector2** | `ListFindingAggregations`, `ListFindings` | ✓ | — | NIST RA-5 |
| **KMS** | `ListKeys`, `DescribeKey`, `GetKeyRotationStatus` | ✓ | — | NIST SC-28 |
| **RDS** | `DescribeDBInstances` | ✓ | — | NIST CP-10, SC-28 |
| **ELBv2** | `DescribeLoadBalancers`, `DescribeListeners` | ✓ | — | NIST CP-10, SC-8 |
| **ACM** | `ListCertificates` | ✓ | — | NIST SC-8 |
| **Backup** | `ListBackupPlans` | ✓ | — | NIST CP-9 |
| **CodePipeline** | `ListPipelines` | ✓ | — | NIST SA-3 |
| **CodeBuild** | `ListProjects` | ✓ | — | NIST SA-3 |
| **SSM** | `ListAssociations`, `DescribePatchBaselines`, `ListComplianceSummaries` | ✓ | — | NIST CM-6, SI-2 |
| **SNS** | `ListTopics` | ✓ | — | NIST IR-4 |
| **Lambda** | `ListFunctions` | ✓ | — | NIST CM-8, SA-9 |
| **Secrets Manager** | `ListSecrets` | ✓ | — | NIST SC-28 |
| **Auto Scaling** | `DescribeAutoScalingGroups` | ✓ | — | NIST CP-10 |
| **ECR** | `DescribeRepositories` | ✓ | — | NIST SR-3 |

---

## 4. Summary by Application

| App | Ports | AWS Services Used | Minimal Setup |
|-----|-------|-------------------|---------------|
| **SAELAR** | 8443 or 8484 | Bedrock, STS, S3, IAM, EC2, CloudTrail, Config, Security Hub, GuardDuty, Inspector2, KMS, RDS, ELB, ACM, Backup, Code*, SSM, SNS, Lambda, Secrets Manager, Auto Scaling, ECR | Bedrock + STS for AI; add others for full cloud assessment |
| **SOPRA** | 8080 or 8501 | Bedrock only | Bedrock; no other AWS APIs |

---

## 5. Quick Setup Checklist

1. **Create IAM user or EC2 role** in the sandbox.
2. **Attach Bedrock policy** (both apps).
3. **Attach SAELAR assessment policy** (SAELAR only; see `GRC_Platform_Permissions.md` for full JSON).
4. **Create S3 bucket** (optional; for SAELAR document storage).
5. **Enable Bedrock model access** in the Bedrock console (Titan, Llama, Mistral).
6. **Configure security group** — open app port(s) (and SSH if needed).

---

*Full policy JSON and details: `GRC_Platform_Permissions.md`*
