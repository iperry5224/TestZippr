"""
NIST 800-53 Security Controls Assessment Script
Control Families: AU (Audit and Accountability) & SA (System and Services Acquisition)

This script performs automated checks against AWS infrastructure to evaluate
compliance with NIST 800-53 security controls.
"""

import boto3
import json
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class ControlStatus(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARNING = "⚠️ WARNING"
    NOT_APPLICABLE = "➖ N/A"
    ERROR = "🔴 ERROR"


@dataclass
class ControlResult:
    control_id: str
    control_name: str
    status: ControlStatus
    findings: List[str]
    recommendations: List[str]


class NIST80053Assessor:
    """
    Assessor class for NIST 800-53 AU and SA control families.
    """
    
    def __init__(self, region: str = None):
        """Initialize AWS clients."""
        self.region = region
        self.results: List[ControlResult] = []
        
        try:
            self.cloudtrail = boto3.client('cloudtrail', region_name=region)
            self.s3 = boto3.client('s3', region_name=region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=region)
            self.logs = boto3.client('logs', region_name=region)
            self.config = boto3.client('config', region_name=region)
            self.iam = boto3.client('iam', region_name=region)
            self.ec2 = boto3.client('ec2', region_name=region)
            self.kms = boto3.client('kms', region_name=region)
            self.codepipeline = boto3.client('codepipeline', region_name=region)
            self.codebuild = boto3.client('codebuild', region_name=region)
            self.sns = boto3.client('sns', region_name=region)
            self.sts = boto3.client('sts', region_name=region)
            
            # Verify credentials
            self.account_id = self.sts.get_caller_identity()['Account']
            print(f"🔐 Connected to AWS Account: {self.account_id}")
            print(f"📍 Region: {region or 'default'}\n")
            
        except NoCredentialsError:
            raise Exception("AWS credentials not found. Please configure your credentials.")
    
    # =========================================================================
    # AU - AUDIT AND ACCOUNTABILITY CONTROLS
    # =========================================================================
    
    def check_au_2_audit_events(self) -> ControlResult:
        """
        AU-2: Audit Events
        Verify that the organization identifies auditable events and CloudTrail is enabled.
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            trails = self.cloudtrail.describe_trails()['trailList']
            
            if not trails:
                status = ControlStatus.FAIL
                findings.append("No CloudTrail trails configured")
                recommendations.append("Enable CloudTrail to capture audit events")
            else:
                multi_region_trail = False
                for trail in trails:
                    trail_status = self.cloudtrail.get_trail_status(Name=trail['Name'])
                    is_logging = trail_status.get('IsLogging', False)
                    
                    if trail.get('IsMultiRegionTrail', False):
                        multi_region_trail = True
                    
                    if is_logging:
                        findings.append(f"Trail '{trail['Name']}' is actively logging")
                    else:
                        status = ControlStatus.WARNING
                        findings.append(f"Trail '{trail['Name']}' exists but is NOT logging")
                        recommendations.append(f"Enable logging for trail '{trail['Name']}'")
                
                if not multi_region_trail:
                    if status != ControlStatus.FAIL:
                        status = ControlStatus.WARNING
                    findings.append("No multi-region trail configured")
                    recommendations.append("Configure a multi-region trail for comprehensive audit coverage")
                        
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking CloudTrail: {e}")
        
        return ControlResult("AU-2", "Audit Events", status, findings, recommendations)
    
    def check_au_3_content_of_audit_records(self) -> ControlResult:
        """
        AU-3: Content of Audit Records
        Verify audit records contain required information (who, what, when, where, outcome).
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            trails = self.cloudtrail.describe_trails()['trailList']
            
            for trail in trails:
                # Check event selectors for management and data events
                selectors = self.cloudtrail.get_event_selectors(TrailName=trail['Name'])
                
                event_selectors = selectors.get('EventSelectors', [])
                advanced_selectors = selectors.get('AdvancedEventSelectors', [])
                
                if event_selectors:
                    for selector in event_selectors:
                        if selector.get('IncludeManagementEvents', False):
                            findings.append(f"Trail '{trail['Name']}' captures management events")
                        if selector.get('DataResources'):
                            findings.append(f"Trail '{trail['Name']}' captures data events")
                elif advanced_selectors:
                    findings.append(f"Trail '{trail['Name']}' uses advanced event selectors")
                else:
                    status = ControlStatus.WARNING
                    findings.append(f"Trail '{trail['Name']}' has minimal event selection")
                    recommendations.append(f"Configure event selectors for '{trail['Name']}' to capture comprehensive audit data")
                
                # Check for CloudWatch Logs integration
                if trail.get('CloudWatchLogsLogGroupArn'):
                    findings.append(f"Trail '{trail['Name']}' integrated with CloudWatch Logs")
                else:
                    if status != ControlStatus.FAIL:
                        status = ControlStatus.WARNING
                    recommendations.append(f"Integrate trail '{trail['Name']}' with CloudWatch Logs for real-time analysis")
                        
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking audit record content: {e}")
        
        return ControlResult("AU-3", "Content of Audit Records", status, findings, recommendations)
    
    def check_au_4_audit_log_storage(self) -> ControlResult:
        """
        AU-4: Audit Log Storage Capacity
        Verify adequate storage is allocated for audit logs.
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            trails = self.cloudtrail.describe_trails()['trailList']
            
            for trail in trails:
                bucket_name = trail.get('S3BucketName')
                if bucket_name:
                    try:
                        # Check if bucket exists and is accessible
                        self.s3.head_bucket(Bucket=bucket_name)
                        findings.append(f"Trail '{trail['Name']}' logs to S3 bucket '{bucket_name}'")
                        
                        # Check bucket versioning
                        versioning = self.s3.get_bucket_versioning(Bucket=bucket_name)
                        if versioning.get('Status') == 'Enabled':
                            findings.append(f"Bucket '{bucket_name}' has versioning enabled")
                        else:
                            recommendations.append(f"Enable versioning on bucket '{bucket_name}'")
                            
                    except ClientError:
                        status = ControlStatus.WARNING
                        findings.append(f"Cannot access S3 bucket '{bucket_name}'")
            
            # Check CloudWatch Log Groups retention
            log_groups = self.logs.describe_log_groups()['logGroups']
            groups_without_retention = []
            
            for lg in log_groups:
                if 'retentionInDays' not in lg:
                    groups_without_retention.append(lg['logGroupName'])
            
            if groups_without_retention:
                findings.append(f"{len(groups_without_retention)} log groups have unlimited retention (ensure storage capacity)")
            else:
                findings.append("All CloudWatch log groups have retention policies configured")
                        
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking audit storage: {e}")
        
        return ControlResult("AU-4", "Audit Log Storage Capacity", status, findings, recommendations)
    
    def check_au_6_audit_review_analysis(self) -> ControlResult:
        """
        AU-6: Audit Review, Analysis, and Reporting
        Check for mechanisms to review and analyze audit records.
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            # Check for CloudWatch Alarms on CloudTrail
            alarms = self.cloudwatch.describe_alarms()['MetricAlarms']
            cloudtrail_alarms = [a for a in alarms if 'cloudtrail' in a['AlarmName'].lower() or 
                                 'trail' in a['AlarmName'].lower()]
            
            if cloudtrail_alarms:
                findings.append(f"Found {len(cloudtrail_alarms)} CloudWatch alarms for audit monitoring")
            else:
                status = ControlStatus.WARNING
                findings.append("No CloudWatch alarms specifically for audit trail monitoring")
                recommendations.append("Create CloudWatch alarms for critical audit events")
            
            # Check for CloudTrail Insights
            trails = self.cloudtrail.describe_trails()['trailList']
            insights_enabled = False
            
            for trail in trails:
                if trail.get('HasInsightSelectors'):
                    insights_enabled = True
                    findings.append(f"CloudTrail Insights enabled on '{trail['Name']}'")
            
            if not insights_enabled:
                recommendations.append("Enable CloudTrail Insights for anomaly detection")
            
            # Check for SNS notifications
            for trail in trails:
                if trail.get('SnsTopicARN'):
                    findings.append(f"Trail '{trail['Name']}' sends notifications to SNS")
                    
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking audit review mechanisms: {e}")
        
        return ControlResult("AU-6", "Audit Review, Analysis, and Reporting", status, findings, recommendations)
    
    def check_au_8_time_stamps(self) -> ControlResult:
        """
        AU-8: Time Stamps
        Verify systems use authoritative time sources.
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            # AWS services automatically use synchronized time
            findings.append("AWS services use Amazon Time Sync Service (NTP)")
            findings.append("CloudTrail timestamps are UTC and automatically synchronized")
            
            # Check EC2 instances for time sync configuration
            instances = self.ec2.describe_instances()['Reservations']
            instance_count = sum(len(r['Instances']) for r in instances)
            
            if instance_count > 0:
                findings.append(f"Found {instance_count} EC2 instances - verify NTP configuration")
                recommendations.append("Ensure EC2 instances use Amazon Time Sync Service (169.254.169.123)")
            
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking time synchronization: {e}")
        
        return ControlResult("AU-8", "Time Stamps", status, findings, recommendations)
    
    def check_au_9_protection_of_audit_info(self) -> ControlResult:
        """
        AU-9: Protection of Audit Information
        Verify audit information is protected from unauthorized access/modification.
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            trails = self.cloudtrail.describe_trails()['trailList']
            
            for trail in trails:
                # Check log file validation
                if trail.get('LogFileValidationEnabled'):
                    findings.append(f"Trail '{trail['Name']}' has log file validation enabled")
                else:
                    status = ControlStatus.WARNING
                    findings.append(f"Trail '{trail['Name']}' does NOT have log file validation")
                    recommendations.append(f"Enable log file validation for '{trail['Name']}'")
                
                # Check KMS encryption
                if trail.get('KMSKeyId'):
                    findings.append(f"Trail '{trail['Name']}' is encrypted with KMS")
                else:
                    if status != ControlStatus.FAIL:
                        status = ControlStatus.WARNING
                    recommendations.append(f"Enable KMS encryption for trail '{trail['Name']}'")
                
                # Check S3 bucket policy
                bucket_name = trail.get('S3BucketName')
                if bucket_name:
                    try:
                        # Check bucket public access
                        public_access = self.s3.get_public_access_block(Bucket=bucket_name)
                        config = public_access['PublicAccessBlockConfiguration']
                        
                        if all([config.get('BlockPublicAcls'), config.get('BlockPublicPolicy'),
                                config.get('IgnorePublicAcls'), config.get('RestrictPublicBuckets')]):
                            findings.append(f"Bucket '{bucket_name}' blocks public access")
                        else:
                            status = ControlStatus.FAIL
                            findings.append(f"Bucket '{bucket_name}' may allow public access")
                            recommendations.append(f"Enable all public access blocks on '{bucket_name}'")
                            
                    except ClientError as e:
                        if 'NoSuchPublicAccessBlockConfiguration' in str(e):
                            status = ControlStatus.FAIL
                            recommendations.append(f"Configure public access block for '{bucket_name}'")
                            
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking audit protection: {e}")
        
        return ControlResult("AU-9", "Protection of Audit Information", status, findings, recommendations)
    
    def check_au_11_audit_record_retention(self) -> ControlResult:
        """
        AU-11: Audit Record Retention
        Verify audit records are retained per organizational requirements.
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            # Check S3 lifecycle policies for CloudTrail buckets
            trails = self.cloudtrail.describe_trails()['trailList']
            
            for trail in trails:
                bucket_name = trail.get('S3BucketName')
                if bucket_name:
                    try:
                        lifecycle = self.s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                        rules = lifecycle.get('Rules', [])
                        
                        if rules:
                            findings.append(f"Bucket '{bucket_name}' has {len(rules)} lifecycle rule(s)")
                            for rule in rules:
                                if rule.get('Status') == 'Enabled':
                                    expiration = rule.get('Expiration', {})
                                    if expiration.get('Days'):
                                        findings.append(f"  - Retention: {expiration['Days']} days")
                        else:
                            findings.append(f"Bucket '{bucket_name}' has no lifecycle rules (indefinite retention)")
                            
                    except ClientError as e:
                        if 'NoSuchLifecycleConfiguration' in str(e):
                            findings.append(f"Bucket '{bucket_name}' has no lifecycle config (indefinite retention)")
            
            # Check CloudWatch Logs retention
            log_groups = self.logs.describe_log_groups()['logGroups']
            retention_summary = {}
            
            for lg in log_groups:
                retention = lg.get('retentionInDays', 'Never expires')
                retention_summary[retention] = retention_summary.get(retention, 0) + 1
            
            findings.append("CloudWatch Log Group Retention Summary:")
            for retention, count in sorted(retention_summary.items(), key=lambda x: str(x[0])):
                findings.append(f"  - {retention} days: {count} log group(s)" if isinstance(retention, int) 
                               else f"  - {retention}: {count} log group(s)")
                               
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking retention policies: {e}")
        
        return ControlResult("AU-11", "Audit Record Retention", status, findings, recommendations)
    
    def check_au_12_audit_generation(self) -> ControlResult:
        """
        AU-12: Audit Generation
        Verify audit record generation capability is enabled across services.
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            # Check CloudTrail
            trails = self.cloudtrail.describe_trails()['trailList']
            active_trails = 0
            
            for trail in trails:
                trail_status = self.cloudtrail.get_trail_status(Name=trail['Name'])
                if trail_status.get('IsLogging'):
                    active_trails += 1
            
            if active_trails > 0:
                findings.append(f"{active_trails} CloudTrail trail(s) actively generating audit records")
            else:
                status = ControlStatus.FAIL
                findings.append("No active CloudTrail trails generating audit records")
                recommendations.append("Enable CloudTrail logging")
            
            # Check AWS Config
            try:
                config_recorders = self.config.describe_configuration_recorders()['ConfigurationRecorders']
                recorder_status = self.config.describe_configuration_recorder_status()['ConfigurationRecordersStatus']
                
                recording = any(s.get('recording') for s in recorder_status)
                
                if config_recorders and recording:
                    findings.append("AWS Config is recording configuration changes")
                else:
                    status = ControlStatus.WARNING
                    findings.append("AWS Config is not actively recording")
                    recommendations.append("Enable AWS Config for configuration change auditing")
                    
            except ClientError:
                findings.append("AWS Config not configured in this region")
                recommendations.append("Consider enabling AWS Config")
            
            # Check VPC Flow Logs
            vpcs = self.ec2.describe_vpcs()['Vpcs']
            flow_logs = self.ec2.describe_flow_logs()['FlowLogs']
            
            vpc_ids_with_flow_logs = set(fl['ResourceId'] for fl in flow_logs if fl['ResourceId'].startswith('vpc-'))
            vpcs_without_flow_logs = [v['VpcId'] for v in vpcs if v['VpcId'] not in vpc_ids_with_flow_logs]
            
            if vpcs_without_flow_logs:
                status = ControlStatus.WARNING
                findings.append(f"{len(vpcs_without_flow_logs)} VPC(s) without flow logs")
                recommendations.append("Enable VPC Flow Logs for network traffic auditing")
            else:
                findings.append("All VPCs have flow logs enabled")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking audit generation: {e}")
        
        return ControlResult("AU-12", "Audit Generation", status, findings, recommendations)
    
    # =========================================================================
    # SA - SYSTEM AND SERVICES ACQUISITION CONTROLS
    # =========================================================================
    
    def check_sa_3_system_development_lifecycle(self) -> ControlResult:
        """
        SA-3: System Development Life Cycle
        Verify SDLC practices are in place.
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            # Check for CodePipeline (CI/CD)
            pipelines = self.codepipeline.list_pipelines()['pipelines']
            
            if pipelines:
                findings.append(f"Found {len(pipelines)} CodePipeline(s) for SDLC automation")
                for pipeline in pipelines[:5]:  # Show first 5
                    findings.append(f"  - {pipeline['name']}")
            else:
                status = ControlStatus.WARNING
                findings.append("No CodePipeline configurations found")
                recommendations.append("Implement CI/CD pipelines for controlled deployments")
            
            # Check for CodeBuild projects
            projects = self.codebuild.list_projects()['projects']
            
            if projects:
                findings.append(f"Found {len(projects)} CodeBuild project(s)")
            else:
                recommendations.append("Consider using CodeBuild for automated builds")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking SDLC controls: {e}")
        
        return ControlResult("SA-3", "System Development Life Cycle", status, findings, recommendations)
    
    def check_sa_4_acquisition_process(self) -> ControlResult:
        """
        SA-4: Acquisition Process
        Review security requirements in acquisition documentation.
        """
        findings = []
        recommendations = []
        status = ControlStatus.WARNING
        
        # This is primarily a policy/documentation check
        findings.append("SA-4 requires manual review of acquisition documentation")
        findings.append("Automated checks can verify:")
        
        try:
            # Check for AWS Organizations SCP (indicates centralized governance)
            try:
                orgs = boto3.client('organizations')
                org_info = orgs.describe_organization()
                findings.append("  ✓ AWS Organizations is configured (centralized governance)")
            except ClientError:
                findings.append("  - AWS Organizations not configured or no access")
            
            # Check for Service Control Policies
            recommendations.append("Document security requirements in procurement processes")
            recommendations.append("Maintain vendor security assessments")
            recommendations.append("Include security clauses in contracts")
            
        except Exception as e:
            findings.append(f"Error: {e}")
        
        return ControlResult("SA-4", "Acquisition Process", status, findings, recommendations)
    
    def check_sa_8_security_engineering_principles(self) -> ControlResult:
        """
        SA-8: Security and Privacy Engineering Principles
        Verify security engineering principles are applied.
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            # Check for encryption at rest (KMS usage)
            keys = self.kms.list_keys()['Keys']
            
            if keys:
                findings.append(f"Found {len(keys)} KMS key(s) for encryption")
                
                enabled_keys = 0
                for key in keys[:10]:
                    try:
                        key_info = self.kms.describe_key(KeyId=key['KeyId'])
                        if key_info['KeyMetadata']['KeyState'] == 'Enabled':
                            enabled_keys += 1
                    except ClientError:
                        continue
                        
                findings.append(f"  - {enabled_keys} key(s) are enabled")
            else:
                status = ControlStatus.WARNING
                findings.append("No KMS keys found")
                recommendations.append("Implement KMS for encryption at rest")
            
            # Check default EBS encryption
            try:
                ebs_encryption = self.ec2.get_ebs_encryption_by_default()
                if ebs_encryption.get('EbsEncryptionByDefault'):
                    findings.append("EBS encryption by default is enabled")
                else:
                    status = ControlStatus.WARNING
                    findings.append("EBS encryption by default is NOT enabled")
                    recommendations.append("Enable EBS encryption by default")
            except ClientError:
                pass
            
            # Check for Security Groups (network segmentation)
            security_groups = self.ec2.describe_security_groups()['SecurityGroups']
            overly_permissive = []
            
            for sg in security_groups:
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            if rule.get('FromPort') not in [80, 443]:  # Allow web ports
                                overly_permissive.append(sg['GroupId'])
                                break
            
            if overly_permissive:
                status = ControlStatus.WARNING
                findings.append(f"{len(set(overly_permissive))} security group(s) with broad inbound rules")
                recommendations.append("Review and restrict overly permissive security groups")
            else:
                findings.append("Security groups appear to follow least privilege")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking security engineering: {e}")
        
        return ControlResult("SA-8", "Security and Privacy Engineering Principles", status, findings, recommendations)
    
    def check_sa_9_external_system_services(self) -> ControlResult:
        """
        SA-9: External System Services
        Identify and assess external service dependencies.
        """
        findings = []
        recommendations = []
        status = ControlStatus.WARNING
        
        try:
            # Check for third-party integrations via IAM roles
            roles = self.iam.list_roles()['Roles']
            external_roles = []
            
            for role in roles:
                trust_policy = role.get('AssumeRolePolicyDocument', {})
                statements = trust_policy.get('Statement', [])
                
                for stmt in statements:
                    principal = stmt.get('Principal', {})
                    if isinstance(principal, dict):
                        aws_principal = principal.get('AWS', '')
                        if isinstance(aws_principal, str) and aws_principal and \
                           not aws_principal.startswith(f'arn:aws:iam::{self.account_id}'):
                            external_roles.append(role['RoleName'])
                            break
            
            if external_roles:
                findings.append(f"Found {len(external_roles)} IAM role(s) with external trust relationships")
                for role in external_roles[:5]:
                    findings.append(f"  - {role}")
                recommendations.append("Review and document all external service integrations")
            else:
                findings.append("No IAM roles with external trust relationships found")
            
            # Check for VPC endpoints (AWS PrivateLink)
            vpc_endpoints = self.ec2.describe_vpc_endpoints()['VpcEndpoints']
            
            if vpc_endpoints:
                findings.append(f"Found {len(vpc_endpoints)} VPC endpoint(s) for private AWS service access")
            else:
                recommendations.append("Consider VPC endpoints for private connectivity to AWS services")
            
            findings.append("Manual review required for third-party SaaS integrations")
            
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking external services: {e}")
        
        return ControlResult("SA-9", "External System Services", status, findings, recommendations)
    
    def check_sa_10_developer_configuration_management(self) -> ControlResult:
        """
        SA-10: Developer Configuration Management
        Verify developer configuration management controls.
        """
        findings = []
        recommendations = []
        status = ControlStatus.PASS
        
        try:
            # Check CodeCommit repositories
            try:
                codecommit = boto3.client('codecommit', region_name=self.region)
                repos = codecommit.list_repositories()['repositories']
                
                if repos:
                    findings.append(f"Found {len(repos)} CodeCommit repository(ies)")
                    for repo in repos[:5]:
                        findings.append(f"  - {repo['repositoryName']}")
                else:
                    status = ControlStatus.WARNING
                    findings.append("No CodeCommit repositories found")
                    recommendations.append("Use version control for all code artifacts")
            except ClientError:
                findings.append("CodeCommit not accessible or not configured")
            
            # Check for branch protection via CodeBuild
            projects = self.codebuild.list_projects()['projects']
            
            if projects:
                findings.append(f"Found {len(projects)} CodeBuild project(s) for build automation")
                
                for proj_name in projects[:3]:
                    try:
                        project = self.codebuild.batch_get_projects(names=[proj_name])['projects'][0]
                        source = project.get('source', {})
                        findings.append(f"  - {proj_name}: {source.get('type', 'Unknown')} source")
                    except ClientError:
                        continue
            
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking developer config management: {e}")
        
        return ControlResult("SA-10", "Developer Configuration Management", status, findings, recommendations)
    
    def check_sa_11_developer_testing(self) -> ControlResult:
        """
        SA-11: Developer Testing and Evaluation
        Verify developer testing controls are in place.
        """
        findings = []
        recommendations = []
        status = ControlStatus.WARNING
        
        try:
            # Check CodeBuild for testing
            projects = self.codebuild.list_projects()['projects']
            
            if projects:
                findings.append(f"Found {len(projects)} CodeBuild project(s)")
                
                test_projects = [p for p in projects if any(t in p.lower() for t in ['test', 'qa', 'check', 'validate'])]
                
                if test_projects:
                    status = ControlStatus.PASS
                    findings.append(f"  - {len(test_projects)} appear to be test-related")
                else:
                    findings.append("  - No projects with 'test' naming convention found")
                    recommendations.append("Implement automated testing in CI/CD pipeline")
            else:
                findings.append("No CodeBuild projects found")
                recommendations.append("Implement automated build and test pipelines")
            
            # Check CodePipeline stages
            pipelines = self.codepipeline.list_pipelines()['pipelines']
            
            for pipeline in pipelines[:3]:
                try:
                    pipeline_detail = self.codepipeline.get_pipeline(name=pipeline['name'])['pipeline']
                    stages = pipeline_detail.get('stages', [])
                    stage_names = [s['name'] for s in stages]
                    
                    test_stages = [s for s in stage_names if any(t in s.lower() for t in ['test', 'qa', 'validate'])]
                    
                    if test_stages:
                        status = ControlStatus.PASS
                        findings.append(f"Pipeline '{pipeline['name']}' has test stage(s): {', '.join(test_stages)}")
                    else:
                        findings.append(f"Pipeline '{pipeline['name']}' stages: {', '.join(stage_names)}")
                        recommendations.append(f"Add testing stage to pipeline '{pipeline['name']}'")
                        
                except ClientError:
                    continue
            
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking developer testing: {e}")
        
        return ControlResult("SA-11", "Developer Testing and Evaluation", status, findings, recommendations)
    
    def check_sa_15_development_process(self) -> ControlResult:
        """
        SA-15: Development Process, Standards, and Tools
        Verify development standards are followed.
        """
        findings = []
        recommendations = []
        status = ControlStatus.WARNING
        
        findings.append("SA-15 requires organizational policy review")
        findings.append("Automated checks for AWS development standards:")
        
        try:
            # Check for CloudFormation usage (Infrastructure as Code)
            cfn = boto3.client('cloudformation', region_name=self.region)
            stacks = cfn.list_stacks(StackStatusFilter=[
                'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE'
            ])['StackSummaries']
            
            if stacks:
                status = ControlStatus.PASS
                findings.append(f"  ✓ Found {len(stacks)} CloudFormation stack(s) (IaC in use)")
            else:
                findings.append("  - No CloudFormation stacks found")
                recommendations.append("Adopt Infrastructure as Code practices")
            
            # Check for AWS Service Catalog
            try:
                sc = boto3.client('servicecatalog', region_name=self.region)
                portfolios = sc.list_portfolios()['PortfolioDetails']
                
                if portfolios:
                    findings.append(f"  ✓ Found {len(portfolios)} Service Catalog portfolio(s)")
                else:
                    findings.append("  - No Service Catalog portfolios found")
            except ClientError:
                findings.append("  - Service Catalog not accessible")
            
            recommendations.append("Document and enforce development standards")
            recommendations.append("Use approved development tools and frameworks")
            
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error checking development process: {e}")
        
        return ControlResult("SA-15", "Development Process, Standards, and Tools", status, findings, recommendations)
    
    # =========================================================================
    # MAIN ASSESSMENT METHODS
    # =========================================================================
    
    def run_au_controls(self) -> List[ControlResult]:
        """Run all AU (Audit and Accountability) control checks."""
        print("=" * 70)
        print("🔍 AU - AUDIT AND ACCOUNTABILITY CONTROLS")
        print("=" * 70)
        
        checks = [
            self.check_au_2_audit_events,
            self.check_au_3_content_of_audit_records,
            self.check_au_4_audit_log_storage,
            self.check_au_6_audit_review_analysis,
            self.check_au_8_time_stamps,
            self.check_au_9_protection_of_audit_info,
            self.check_au_11_audit_record_retention,
            self.check_au_12_audit_generation,
        ]
        
        results = []
        for check in checks:
            result = check()
            results.append(result)
            self._print_result(result)
        
        return results
    
    def run_sa_controls(self) -> List[ControlResult]:
        """Run all SA (System and Services Acquisition) control checks."""
        print("\n" + "=" * 70)
        print("🔍 SA - SYSTEM AND SERVICES ACQUISITION CONTROLS")
        print("=" * 70)
        
        checks = [
            self.check_sa_3_system_development_lifecycle,
            self.check_sa_4_acquisition_process,
            self.check_sa_8_security_engineering_principles,
            self.check_sa_9_external_system_services,
            self.check_sa_10_developer_configuration_management,
            self.check_sa_11_developer_testing,
            self.check_sa_15_development_process,
        ]
        
        results = []
        for check in checks:
            result = check()
            results.append(result)
            self._print_result(result)
        
        return results
    
    def run_all_controls(self) -> List[ControlResult]:
        """Run all control checks."""
        results = []
        results.extend(self.run_au_controls())
        results.extend(self.run_sa_controls())
        return results
    
    def _print_result(self, result: ControlResult):
        """Print a single control result."""
        print(f"\n{result.status.value} {result.control_id}: {result.control_name}")
        print("-" * 60)
        
        for finding in result.findings:
            print(f"  {finding}")
        
        if result.recommendations:
            print("\n  📋 Recommendations:")
            for rec in result.recommendations:
                print(f"    • {rec}")
    
    def generate_summary(self, results: List[ControlResult]) -> Dict[str, Any]:
        """Generate assessment summary."""
        summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'account_id': self.account_id,
            'total_controls': len(results),
            'passed': len([r for r in results if r.status == ControlStatus.PASS]),
            'failed': len([r for r in results if r.status == ControlStatus.FAIL]),
            'warnings': len([r for r in results if r.status == ControlStatus.WARNING]),
            'errors': len([r for r in results if r.status == ControlStatus.ERROR]),
            'not_applicable': len([r for r in results if r.status == ControlStatus.NOT_APPLICABLE]),
        }
        
        return summary
    
    def print_summary(self, results: List[ControlResult]):
        """Print assessment summary."""
        summary = self.generate_summary(results)
        
        print("\n" + "=" * 70)
        print("📊 ASSESSMENT SUMMARY")
        print("=" * 70)
        print(f"Account: {summary['account_id']}")
        print(f"Timestamp: {summary['timestamp']}")
        print(f"\nTotal Controls Assessed: {summary['total_controls']}")
        print(f"  ✅ Passed:      {summary['passed']}")
        print(f"  ❌ Failed:      {summary['failed']}")
        print(f"  ⚠️ Warnings:    {summary['warnings']}")
        print(f"  🔴 Errors:      {summary['errors']}")
        print(f"  ➖ N/A:         {summary['not_applicable']}")
        
        # Calculate compliance score
        applicable = summary['total_controls'] - summary['not_applicable'] - summary['errors']
        if applicable > 0:
            score = (summary['passed'] / applicable) * 100
            print(f"\n📈 Compliance Score: {score:.1f}%")
        
        print("=" * 70)
    
    def export_results(self, results: List[ControlResult], filename: str = None):
        """Export results to JSON file."""
        if not filename:
            filename = f"nist_800_53_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'summary': self.generate_summary(results),
            'results': [
                {
                    'control_id': r.control_id,
                    'control_name': r.control_name,
                    'status': r.status.name,
                    'findings': r.findings,
                    'recommendations': r.recommendations
                }
                for r in results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n💾 Results exported to: {filename}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='NIST 800-53 Security Controls Assessment (AU & SA Families)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nist_800_53_controls.py                    # Run all controls
  python nist_800_53_controls.py --family AU        # Run only AU controls
  python nist_800_53_controls.py --family SA        # Run only SA controls
  python nist_800_53_controls.py --export           # Export results to JSON
  python nist_800_53_controls.py --region us-west-2 # Specify AWS region
        """
    )
    
    parser.add_argument('--family', '-f', choices=['AU', 'SA', 'ALL'], default='ALL',
                        help='Control family to assess (default: ALL)')
    parser.add_argument('--region', '-r', type=str, default=None,
                        help='AWS region to assess')
    parser.add_argument('--export', '-e', action='store_true',
                        help='Export results to JSON file')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output filename for export')
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           NIST 800-53 Security Controls Assessment                   ║
║           Control Families: AU (Audit) & SA (Acquisition)            ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        assessor = NIST80053Assessor(region=args.region)
        
        if args.family == 'AU':
            results = assessor.run_au_controls()
        elif args.family == 'SA':
            results = assessor.run_sa_controls()
        else:
            results = assessor.run_all_controls()
        
        assessor.print_summary(results)
        
        if args.export:
            assessor.export_results(results, args.output)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

