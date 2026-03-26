# SAELAR Team Q&A

| # | Question | Response |
|---|----------|----------|
| **1** | Could you produce some kind of mapping or crosswalk illustrating which API or mechanisms get used to retrieve each piece of data? | See the **Data Source Crosswalk** table below. |
| **2** | How does the SAELAR-53 controls assessment align with NIST SP 800-53A, Revision 5, Assessing Security and Privacy Controls in Information Systems and Organizations? | SAELAR aligns with NIST 800-53A Rev 5 primarily through the **Examine** method. It inspects AWS configuration and state via APIs to assess control implementation. It does **not** perform **Interview** (personnel discussions) or active **Test** (e.g., penetration tests). See the **800-53A Alignment** section below. |

---

## Data Source Crosswalk

| Data / Capability | API or Mechanism | AWS Service / Source |
|-------------------|------------------|----------------------|
| Account identity & credentials | `sts.get_caller_identity()` | AWS STS |
| IAM users, policies, MFA | `iam.list_users()`, `iam.list_access_keys()`, `iam.get_policy_version()`, `iam.list_mfa_devices()`, `iam.get_login_profile()`, `iam.get_account_password_policy()` | AWS IAM |
| Access keys last used | `iam.get_access_key_last_used()` | AWS IAM |
| S3 buckets, encryption, policies | `s3.list_buckets()`, `s3.get_bucket_encryption()`, `s3.get_public_access_block()`, `s3.get_bucket_policy()`, `s3.get_bucket_lifecycle_configuration()` | AWS S3 |
| EC2 instances, VPCs, security groups, snapshots | `ec2.describe_instances()`, `ec2.describe_vpcs()`, `ec2.describe_security_groups()`, `ec2.describe_flow_logs()`, `ec2.describe_network_acls()`, `ec2.describe_snapshots()`, `ec2.describe_volumes()`, `ec2.get_ebs_encryption_by_default()` | AWS EC2 |
| CloudTrail trails & status | `cloudtrail.describe_trails()`, `cloudtrail.get_trail_status()`, `cloudtrail.get_event_selectors()` | AWS CloudTrail |
| CloudWatch alarms | `cloudwatch.describe_alarms()` | AWS CloudWatch |
| CloudWatch Logs retention | `logs.describe_log_groups()` | AWS CloudWatch Logs |
| AWS Config recorders & rules | `config.describe_configuration_recorders()`, `config.describe_config_rules()`, `config.get_compliance_details_by_config_rule()`, `config.get_discovered_resource_counts()` | AWS Config |
| Security Hub findings & standards | `securityhub.describe_hub()`, `securityhub.get_enabled_standards()`, `securityhub.get_findings()` | AWS Security Hub |
| GuardDuty detectors & findings | `guardduty.list_detectors()`, `guardduty.get_findings_statistics()`, `guardduty.list_findings()` | AWS GuardDuty |
| Inspector vulnerability findings | `inspector2.list_finding_aggregations()`, `inspector2.list_findings()` | AWS Inspector v2 |
| Macie findings | `macie2.*` (if used) | AWS Macie |
| KMS keys & rotation | `kms.list_keys()`, `kms.describe_key()`, `kms.get_key_rotation_status()` | AWS KMS |
| Secrets Manager | `secretsmanager.list_secrets()` | AWS Secrets Manager |
| RDS instances | `rds.describe_db_instances()` | AWS RDS |
| Backup plans | `backup.list_backup_plans()` | AWS Backup |
| Load balancers & listeners | `elbv2.describe_load_balancers()`, `elbv2.describe_listeners()` | AWS ELB v2 |
| ACM certificates | `acm.list_certificates()` | AWS Certificate Manager |
| WAF policies | `wafv2.*` | AWS WAF v2 |
| CodePipeline, CodeBuild | `codepipeline.list_pipelines()`, `codebuild.list_projects()` | AWS CodePipeline, CodeBuild |
| Lambda functions | `lambda.list_functions()` | AWS Lambda |
| SSM associations, patch baselines | `ssm.list_associations()`, `ssm.describe_patch_baselines()`, `ssm.list_compliance_summaries()` | AWS Systems Manager |
| SNS topics | `sns.list_topics()` | AWS SNS |
| CISA Known Exploited Vulnerabilities (KEV) | HTTP GET to `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` | CISA KEV Catalog (external) |
| AI remediation suggestions | `bedrock-runtime.InvokeModel()` | AWS Bedrock |
| Report upload / storage | `s3.put_object()`, `s3.list_objects_v2()`, `s3.get_object()` | AWS S3 |

---

## NIST SP 800-53A Rev 5 Alignment

NIST SP 800-53A defines three assessment methods:

| Assessment Method | Description | SAELAR Support |
|-------------------|-------------|----------------|
| **Examine** | Review documentation, design specifications, and mechanism behavior | **Primary.** SAELAR uses AWS APIs to examine configuration state (e.g., CloudTrail enabled, IAM password policy, S3 encryption, GuardDuty status). This maps to examining “object evidence” per 800-53A. |
| **Interview** | Discuss with personnel responsible for the control | **Not supported.** SAELAR is automated and does not conduct interviews. |
| **Test** | Execute mechanisms or simulate attacks | **Limited.** SAELAR verifies that services are enabled and configured but does not run active tests (e.g., exploit attempts, penetration tests). |

**Summary:** SAELAR performs automated **examine**-based assessments aligned with NIST 800-53A. It is suitable for continuous monitoring and configuration review. For full 800-53A compliance, organizations should supplement SAELAR with **interview** and **test** activities conducted separately.
