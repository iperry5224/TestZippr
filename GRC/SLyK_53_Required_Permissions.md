# SLyK-53 — Required IAM Permissions

## For: AWS Admin / Security Team Ticket Submission
**Purpose:** Deploy and operate SLyK-53 (SAE Lightweight Yaml Kit) — an Agentic AI security assistant integrated into the AWS Console for System 5065.

---

## 1. Permissions Needed by the DEPLOYER (one-time setup)

The person running `deploy_slyk.py` needs these permissions to create the resources:

### IAM (create roles and policies)
```
iam:CreateRole
iam:AttachRolePolicy
iam:PutRolePolicy
iam:PassRole
iam:GetRole
iam:ListRoles
```

### Lambda (create and configure functions)
```
lambda:CreateFunction
lambda:UpdateFunctionCode
lambda:UpdateFunctionConfiguration
lambda:AddPermission
lambda:GetFunction
lambda:ListFunctions
```

### Amazon Bedrock (create agent and action groups)
```
bedrock:CreateAgent
bedrock:CreateAgentActionGroup
bedrock:PrepareAgent
bedrock:CreateAgentAlias
bedrock:ListAgents
bedrock:ListAgentAliases
bedrock:GetAgent
bedrock:InvokeModel
bedrock:InvokeModelWithResponseStream
```

### EventBridge (create alerting rule)
```
events:PutRule
events:PutTargets
events:DescribeRule
events:ListRules
```

### SNS (create alert topic)
```
sns:CreateTopic
sns:Subscribe
sns:Publish
sns:SetTopicAttributes
sns:GetTopicAttributes
```

### S3 (store config and artifacts)
```
s3:PutObject
s3:GetObject
s3:ListBucket
```

### STS (verify identity)
```
sts:GetCallerIdentity
```

---

## 2. Permissions Needed by the LAMBDA EXECUTION ROLE (SLyK-Lambda-Role)

This role is created by the deploy script and attached to all Lambda functions. If your admin prefers to pre-create it, here are the required permissions:

### Read-Only Assessment (ASSESS + RUNBOOKS)
```
iam:ListUsers
iam:ListMFADevices
iam:GetAccountSummary
iam:ListAccessKeys
iam:ListPolicies
iam:GetPolicyVersion
iam:GetAccountPasswordPolicy
iam:GenerateCredentialReport

ec2:DescribeInstances
ec2:DescribeSecurityGroups
ec2:DescribeFlowLogs

s3:ListAllMyBuckets
s3:GetBucketEncryption
s3:GetBucketVersioning
s3:GetBucketLogging
s3:GetPublicAccessBlock
s3:ListBucket
s3:GetObject

cloudtrail:DescribeTrails
cloudtrail:GetTrailStatus
cloudtrail:LookupEvents

guardduty:ListDetectors
guardduty:ListFindings
guardduty:GetFindings

securityhub:GetFindings
securityhub:DescribeHub
securityhub:BatchUpdateFindings

config:DescribeConfigurationRecorders
config:DescribeComplianceByConfigRule

kms:ListKeys
kms:DescribeKey
```

### Hardening Actions (HARDEN)
```
s3:PutBucketEncryption
s3:PutBucketVersioning
s3:PutPublicAccessBlock
s3:PutBucketLogging

ec2:ModifyInstanceMetadataOptions

iam:CreateVirtualMFADevice
iam:EnableMFADevice
```

### Remediation Execution (REMEDIATE)
```
ssm:SendCommand
ssm:GetCommandInvocation
```

### AI Model Access (TRIAGE + RUNBOOKS)
```
bedrock:InvokeModel
bedrock:InvokeModelWithResponseStream
```

### Logging and Storage
```
s3:PutObject          (for saving runbook results and audit logs)
logs:CreateLogGroup
logs:CreateLogStream
logs:PutLogEvents
```

---

## 3. Permissions Needed by the BEDROCK AGENT ROLE (SLyK-Agent-Role)

This role allows the Bedrock Agent to invoke foundation models and call Lambda functions:

```
bedrock:InvokeModel
bedrock:InvokeModelWithResponseStream
lambda:InvokeFunction
```

### Trust Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": "<ACCOUNT_ID>"
                }
            }
        }
    ]
}
```

---

## 4. Bedrock Model Access

The following foundation models must be enabled in the Bedrock Console (Model Access page). SLyK will use the first available model:

| Priority | Model ID | Provider |
|---|---|---|
| 1 | amazon.nova-pro-v1:0 | Amazon |
| 2 | amazon.nova-lite-v1:0 | Amazon |
| 3 | amazon.nova-micro-v1:0 | Amazon |
| 4 | meta.llama3-1-70b-instruct-v1:0 | Meta |
| 5 | meta.llama3-1-8b-instruct-v1:0 | Meta |
| 6 | mistral.mistral-large-2407-v1:0 | Mistral AI |
| 7 | mistral.mixtral-8x7b-instruct-v0:1 | Mistral AI |
| 8 | amazon.titan-text-express-v1 | Amazon |
| 9 | amazon.titan-text-lite-v1 | Amazon |

**Minimum requirement:** Enable at least one model. Amazon Nova or Titan models require no third-party agreement.

---

## 5. Resources Created by the Deploy Script

| Resource | Name | Type |
|---|---|---|
| IAM Role | SLyK-Lambda-Role | Lambda execution role |
| IAM Role | SLyK-Agent-Role | Bedrock Agent service role |
| Lambda | slyk-assess | NIST assessment + Security Hub |
| Lambda | slyk-remediate | Remediation script generation |
| Lambda | slyk-harden | Asset hardening (S3, EC2, IAM) |
| Lambda | slyk-alert-triage | EventBridge-triggered alert handler |
| Lambda | slyk-runbooks | ISSO runbook execution engine |
| Bedrock Agent | SLyK-53-Security-Assistant | Agentic AI orchestrator |
| EventBridge Rule | SLyK-53-SecurityHub-HighRisk | Triggers on CRITICAL/HIGH findings |
| SNS Topic | SLyK-53-Security-Alerts | Email/Slack alert notifications |

---

## 6. Ticket Template

You can copy-paste this into your ticket:

---

**Subject:** IAM Permissions Request — SLyK-53 Security Assistant Deployment

**Requesting Team:** SAE Team, CyberSecurity Division (CSD)

**System:** 5065

**Purpose:** Deploy SLyK-53, an Agentic AI security compliance and hardening assistant that integrates into the AWS Console. SLyK automates NIST 800-53 assessments, Security Hub finding remediation, and asset hardening.

**Permissions Requested:**

1. **For deployer IAM user (ira.perry@noaa.gov):**
   - iam:CreateRole, iam:AttachRolePolicy, iam:PutRolePolicy, iam:PassRole
   - lambda:CreateFunction, lambda:UpdateFunctionCode, lambda:AddPermission
   - bedrock:CreateAgent, bedrock:CreateAgentActionGroup, bedrock:PrepareAgent, bedrock:CreateAgentAlias
   - events:PutRule, events:PutTargets
   - sns:CreateTopic, sns:Subscribe, sns:SetTopicAttributes
   - s3:PutObject on saelarallpurpose bucket

2. **Create two IAM roles (or grant permission for SAE Team to create):**
   - SLyK-Lambda-Role — Lambda execution with ReadOnlyAccess + targeted hardening permissions (see attached)
   - SLyK-Agent-Role — Bedrock Agent service role with InvokeModel + InvokeFunction

3. **Enable Bedrock model access:**
   - Amazon Nova Pro (amazon.nova-pro-v1:0) — preferred
   - Amazon Titan Text Express (amazon.titan-text-express-v1) — fallback

**Security Notes:**
- All data stays within the AWS boundary (no external API calls)
- Lambda functions use read-only access for assessments; hardening actions are scoped to specific API calls
- All actions logged via CloudTrail
- EventBridge alerts are read-only (triggered by Security Hub findings, does not modify findings unless explicitly approved)

**Estimated Resources:** 5 Lambda functions, 1 Bedrock Agent, 1 EventBridge rule, 1 SNS topic, 2 IAM roles

---
