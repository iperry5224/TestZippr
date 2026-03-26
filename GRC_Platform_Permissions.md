# GRC Platform Permissions

**Purpose:** Explicit list of all AWS IAM permissions and roles required to deploy SAELAR and SOPRA in a new AWS sandbox account.

**Last Updated:** February 2026

---

## Executive Summary

| Application | Primary AWS Services | Deployment Mode |
|-------------|---------------------|-----------------|
| **SAELAR** | Bedrock, STS, S3, IAM, EC2, CloudTrail, Config, Security Hub, GuardDuty, Inspector2, KMS, and 15+ others | Cloud assessments + optional S3 document storage |
| **SOPRA** | Bedrock only | AI features; platform is on-premise |

---

## 1. IAM Roles

### 1.1 SAELAR/SOPRA EC2 Instance Role (Recommended for EC2 Deployment)

**Role Name:** `SaelarSopraEC2Role` (or equivalent)  
**Trust Policy:** EC2 service principal  
**Use Case:** When running SAELAR and SOPRA on an EC2 instance; credentials are assumed via instance profile.

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

**Why:** Allows the EC2 instance to assume this role without storing long-term credentials. Both apps use the default credential chain (environment variables, ~/.aws/credentials, or instance profile).

---

### 1.2 IAM User or Role (Access Key Credentials)

**Use Case:** When running SAELAR or SOPRA locally, in Docker, or with explicit access keys.  
**Why:** The applications support both IAM roles (EC2 instance profile) and IAM user access keys. For sandbox setup, you may use either; access keys are validated via `sts:GetCallerIdentity`.

---

## 2. AWS Permissions by Service

### 2.1 STS (Security Token Service)

| Permission | Why Required |
|------------|--------------|
| `sts:GetCallerIdentity` | **SAELAR:** Validates AWS credentials on login and displays account ID. Called when user configures credentials or runs assessments. **SOPRA:** Not used directly; Bedrock calls use default credential chain. |

---

### 2.2 Amazon Bedrock (bedrock-runtime)

| Permission | Why Required |
|------------|--------------|
| `bedrock:InvokeModel` | **SAELAR:** Powers AI-assisted NIST 800-53 remediation guidance, chat, and analysis. Uses Converse API with Titan/Llama/Mistral models. |
| `bedrock:InvokeModelWithResponseStream` | Optional; used if streaming responses are implemented. |
| `bedrock-runtime:InvokeModel` | Alternative API for model invocation. |
| `bedrock-runtime:Converse` | **Primary API used.** SAELAR (`nist_setup.py`), SOPRA (`ai_assistant.py`, `ai_engine.py`, `ai_remediation.py`), and legacy OPRA all call `bedrock.converse()`. |

**Note:** Both SAELAR and SOPRA gracefully fall back when Bedrock is unavailable (e.g., air-gapped mode for SAELAR with Ollama; template-based output for SOPRA).

**Minimal Policy (recommended):**

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

**Alternative (broader):** `bedrock:*` and `bedrock-runtime:*` if you prefer a single policy.

---

### 2.3 Amazon S3

| Permission | Why Required |
|------------|--------------|
| `s3:ListAllMyBuckets` | **SAELAR:** Lists S3 buckets for bucket selection in settings and document upload UI. |
| `s3:ListBucket` | **SAELAR:** Lists objects in the configured bucket for document management (list, download, delete). |
| `s3:GetObject` | **SAELAR:** Downloads documents from S3 (Documentation folder). |
| `s3:PutObject` | **SAELAR:** Uploads SSP, POA&M, and other generated documents to `Documentation/SSPs/` and `Documentation/POA&Ms/`. |
| `s3:DeleteObject` | **SAELAR:** Allows users to delete documents from the S3 document repository. |
| `s3:GetBucketEncryption` | **SAELAR:** NIST 800-53 Rev 5 assessment checks S3 bucket encryption (SC-28). |
| `s3:GetBucketPolicy` | **SAELAR:** Assessment checks bucket policies for public access (AC-4, SC-7). |
| `s3:GetPublicAccessBlock` | **SAELAR:** Assessment verifies S3 public access block settings (AU-9). |
| `s3:GetBucketLifecycleConfiguration` | **SAELAR:** Assessment checks lifecycle rules for log retention (AU-11). |

**Scope:** Restrict `Resource` to specific buckets if desired:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListAllMyBuckets"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET-NAME",
        "arn:aws:s3:::YOUR-BUCKET-NAME/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketEncryption",
        "s3:GetBucketPolicy",
        "s3:GetPublicAccessBlock",
        "s3:GetBucketLifecycleConfiguration"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
    }
  ]
}
```

---

### 2.4 IAM (Identity and Access Management)

| Permission | Why Required |
|------------|--------------|
| `iam:ListUsers` | **SAELAR:** NIST AC-2 (Account Management), IA-2 (Identification/Authentication). Checks for unused users, MFA. |
| `iam:ListAccessKeys` | **SAELAR:** Identifies access keys per user. |
| `iam:GetAccessKeyLastUsed` | **SAELAR:** Flags unused access keys (AC-2). |
| `iam:ListAttachedUserPolicies` | **SAELAR:** AC-3 (Access Enforcement) – reviews attached policies. |
| `iam:ListPolicies` | **SAELAR:** Enumerates customer-managed policies. |
| `iam:GetPolicyVersion` | **SAELAR:** Retrieves policy documents to check for overly permissive (*:*) statements. |
| `iam:GetAccountPasswordPolicy` | **SAELAR:** IA-5 (Authenticator Management) – password complexity. |
| `iam:GetAccountSummary` | **SAELAR:** Account-level IAM metrics. |
| `iam:ListMfaDevices` | **SAELAR:** IA-2 – MFA enforcement check. |
| `iam:GetLoginProfile` | **SAELAR:** IA-2 – determines if console access exists (MFA check). |
| `iam:ListRoles` | **SAELAR:** SA-9 (External System Services) – role review. |

---

### 2.5 EC2

| Permission | Why Required |
|------------|--------------|
| `ec2:DescribeVpcs` | **SAELAR:** AC-4, CM-7 – VPC flow logs, network config. |
| `ec2:DescribeFlowLogs` | **SAELAR:** AC-4, IR-4 – information flow enforcement. |
| `ec2:DescribeNetworkAcls` | **SAELAR:** AC-4 – NACL review. |
| `ec2:DescribeSecurityGroups` | **SAELAR:** SC-7 (Boundary Protection), CM-7. |
| `ec2:DescribeInstances` | **SAELAR:** CM-8 (System Inventory), CP-10. |
| `ec2:DescribeSnapshots` | **SAELAR:** MP-6 (Media Sanitization), CP-10. |
| `ec2:DescribeVolumes` | **SAELAR:** SC-28 – EBS encryption. |
| `ec2:GetEbsEncryptionByDefault` | **SAELAR:** SC-28 – default EBS encryption. |
| `ec2:DescribeInternetGateways` | **SAELAR:** SC-7 – network topology. |

---

### 2.6 CloudTrail

| Permission | Why Required |
|------------|--------------|
| `cloudtrail:DescribeTrails` | **SAELAR:** AU-2 (Audit Events), AU-9, AU-12 – trail existence and config. |
| `cloudtrail:GetTrailStatus` | **SAELAR:** Verifies trails are logging. |
| `cloudtrail:GetEventSelectors` | **SAELAR:** AU-12 – data events (e.g., S3). |

---

### 2.7 CloudWatch

| Permission | Why Required |
|------------|--------------|
| `cloudwatch:DescribeAlarms` | **SAELAR:** AU-6 (Audit Review), SI-4 – monitoring alarms. |

---

### 2.8 CloudWatch Logs

| Permission | Why Required |
|------------|--------------|
| `logs:DescribeLogGroups` | **SAELAR:** AU-3 – log retention and availability. |

---

### 2.9 AWS Config

| Permission | Why Required |
|------------|--------------|
| `config:DescribeConfigurationRecorders` | **SAELAR:** CM-6 (Configuration Settings), CA-7. |
| `config:DescribeConfigurationRecorderStatus` | **SAELAR:** Recorder status. |
| `config:DescribeConfigRules` | **SAELAR:** Compliance rules. |
| `config:GetComplianceDetailsByConfigRule` | **SAELAR:** CA-7 – compliance details. |
| `config:GetDiscoveredResourceCounts` | **SAELAR:** CA-7 – resource inventory. |

---

### 2.10 Security Hub

| Permission | Why Required |
|------------|--------------|
| `securityhub:DescribeHub` | **SAELAR:** Verifies Security Hub is enabled. |
| `securityhub:GetEnabledStandards` | **SAELAR:** Lists enabled standards. |
| `securityhub:GetFindings` | **SAELAR:** Fetches findings for display and IR-4 (Incident Handling). |
| `securityhub:GetPaginator` (get_findings) | **SAELAR:** Paginated findings in Security Hub UI. |

---

### 2.11 GuardDuty

| Permission | Why Required |
|------------|--------------|
| `guardduty:ListDetectors` | **SAELAR:** SI-4 (System Monitoring), IR-4 – detector status. |
| `guardduty:GetFindingsStatistics` | **SAELAR:** Finding summaries. |
| `guardduty:ListFindings` | **SAELAR:** IR-4 – incident correlation. |

---

### 2.12 Inspector (Inspector2)

| Permission | Why Required |
|------------|--------------|
| `inspector2:ListFindingAggregations` | **SAELAR:** RA-5 (Vulnerability Scanning) – vulnerability counts. |
| `inspector2:ListFindings` | **SAELAR:** RA-5 – vulnerability details. |

---

### 2.13 Macie

| Permission | Why Required |
|------------|--------------|
| `macie2:*` (or read-only) | **SAELAR:** Optional; used if Macie-based checks are enabled. Macie2 client is initialized in `nist_800_53_rev5_full.py`; specific calls may be limited. |

---

### 2.14 KMS

| Permission | Why Required |
|------------|--------------|
| `kms:ListKeys` | **SAELAR:** SC-28 – key inventory. |
| `kms:DescribeKey` | **SAELAR:** Key metadata. |
| `kms:GetKeyRotationStatus` | **SAELAR:** SC-28 – key rotation. |

---

### 2.15 RDS

| Permission | Why Required |
|------------|--------------|
| `rds:DescribeDBInstances` | **SAELAR:** CP-10 (System Recovery), SC-28 – RDS encryption. |

---

### 2.16 Elastic Load Balancing (ELBv2)

| Permission | Why Required |
|------------|--------------|
| `elasticloadbalancing:DescribeLoadBalancers` | **SAELAR:** CP-10, SC-7. |
| `elasticloadbalancing:DescribeListeners` | **SAELAR:** SC-8 – TLS/HTTP listener config. |

---

### 2.17 WAF (WAFv2)

| Permission | Why Required |
|------------|--------------|
| `wafv2:*` (or read-only) | **SAELAR:** WAFv2 client initialized; used for SC-7/WAF checks if implemented. |

---

### 2.18 ACM (Certificate Manager)

| Permission | Why Required |
|------------|--------------|
| `acm:ListCertificates` | **SAELAR:** SC-8 – certificate inventory. |

---

### 2.19 AWS Backup

| Permission | Why Required |
|------------|--------------|
| `backup:ListBackupPlans` | **SAELAR:** CP-9 (Information System Backup). |

---

### 2.20 CodePipeline

| Permission | Why Required |
|------------|--------------|
| `codepipeline:ListPipelines` | **SAELAR:** SA-3 (Development Process) – pipeline visibility. |

---

### 2.21 CodeBuild

| Permission | Why Required |
|------------|--------------|
| `codebuild:ListProjects` | **SAELAR:** SA-3 – build project visibility. |

---

### 2.22 SSM (Systems Manager)

| Permission | Why Required |
|------------|--------------|
| `ssm:ListAssociations` | **SAELAR:** CM-6 – SSM associations. |
| `ssm:DescribePatchBaselines` | **SAELAR:** SI-2 (Flaw Remediation). |
| `ssm:ListComplianceSummaries` | **SAELAR:** SI-2 – patch compliance. |

---

### 2.23 SNS

| Permission | Why Required |
|------------|--------------|
| `sns:ListTopics` | **SAELAR:** IR-4 – notification topics. |

---

### 2.24 Lambda

| Permission | Why Required |
|------------|--------------|
| `lambda:ListFunctions` | **SAELAR:** CM-8, SA-9 – Lambda inventory. |

---

### 2.25 Secrets Manager

| Permission | Why Required |
|------------|--------------|
| `secretsmanager:ListSecrets` | **SAELAR:** SC-28 – secrets inventory. |

---

### 2.26 Auto Scaling

| Permission | Why Required |
|------------|--------------|
| `autoscaling:DescribeAutoScalingGroups` | **SAELAR:** CP-10 – recovery and reconstitution. |

---

### 2.27 ECR (Elastic Container Registry)

| Permission | Why Required |
|------------|--------------|
| `ecr:DescribeRepositories` | **SAELAR:** SR-3 (Supply Chain Controls) – container image source. |

---

## 3. Deployment-Specific Permissions (deploy_to_aws.py)

If you use the `deploy_to_aws.py` script to provision EC2 instances:

| Service | Permissions | Why |
|---------|-------------|-----|
| **EC2** | `ec2:CreateKeyPair`, `ec2:DeleteKeyPair`, `ec2:DescribeKeyPairs`, `ec2:DescribeVpcs`, `ec2:DescribeSecurityGroups`, `ec2:CreateSecurityGroup`, `ec2:AuthorizeSecurityGroupIngress`, `ec2:RunInstances`, `ec2:DescribeInstances`, `ec2:DescribeImages` | Creates key pair, security group, and launches EC2 instance. |
| **IAM** | `iam:CreateRole`, `iam:GetRole`, `iam:PutRolePolicy`, `iam:CreateInstanceProfile`, `iam:GetInstanceProfile`, `iam:AddRoleToInstanceProfile` | Creates IAM role and instance profile for EC2. |
| **SSM** | `ssm:GetParameter` | Retrieves latest Amazon Linux AMI (optional). |

---

## 4. Consolidated IAM Policy (SAELAR Full Cloud Assessment)

Below is a single policy that grants all permissions needed for SAELAR's full NIST 800-53 Rev 5 cloud assessment:

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
      "Action": [
        "sts:GetCallerIdentity"
      ],
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
      "Action": [
        "cloudwatch:DescribeAlarms"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Logs",
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups"
      ],
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
      "Action": [
        "rds:DescribeDBInstances"
      ],
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
      "Action": [
        "acm:ListCertificates"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Backup",
      "Effect": "Allow",
      "Action": [
        "backup:ListBackupPlans"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CodePipeline",
      "Effect": "Allow",
      "Action": [
        "codepipeline:ListPipelines"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CodeBuild",
      "Effect": "Allow",
      "Action": [
        "codebuild:ListProjects"
      ],
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
      "Action": [
        "sns:ListTopics"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Lambda",
      "Effect": "Allow",
      "Action": [
        "lambda:ListFunctions"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecretsManager",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:ListSecrets"
      ],
      "Resource": "*"
    },
    {
      "Sid": "AutoScaling",
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECR",
      "Effect": "Allow",
      "Action": [
        "ecr:DescribeRepositories"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 5. Minimal Policy (SOPRA Only)

SOPRA uses **only** Bedrock for AI. No other AWS services are required.

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

---

## 6. Sandbox Setup Checklist

1. **Create IAM user or role** in the target sandbox account.
2. **Attach the consolidated SAELAR policy** (Section 4) if running full cloud assessments.
3. **Attach the minimal SOPRA policy** (Section 5) if using SOPRA AI features only.
4. **Create S3 bucket** for document storage (SAELAR); apply bucket policy if restricting access.
5. **Enable Bedrock model access** in the Bedrock console (e.g., Titan, Llama, Mistral).
6. **Optional:** Use `deploy_to_aws.py` to create EC2 role with Bedrock permissions; ensure EC2 instance has the instance profile attached.

---

## 7. Optional / Air-Gapped Modes

- **SAELAR air-gapped:** Set `SAELAR_AIRGAPPED=true` and use Ollama. No AWS permissions required.
- **SOPRA without AI:** All 13 AI features fall back to deterministic templates. No AWS permissions required.
