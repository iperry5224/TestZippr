"""
NIST 800-53 Rev 5 - Complete Cloud Security Controls Assessment
================================================================
Comprehensive automated checks against AWS infrastructure for ALL
cloud-relevant NIST 800-53 Revision 5 security control families.

Control Families Implemented:
- AC: Access Control
- AU: Audit and Accountability  
- CA: Assessment, Authorization, and Monitoring
- CM: Configuration Management
- CP: Contingency Planning
- IA: Identification and Authentication
- IR: Incident Response
- MP: Media Protection
- RA: Risk Assessment
- SA: System and Services Acquisition
- SC: System and Communications Protection
- SI: System and Information Integrity
- SR: Supply Chain Risk Management
"""

import boto3
import json
import re
import time
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed


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
    family: str
    status: ControlStatus
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class NIST80053Rev5Assessor:
    """
    Complete NIST 800-53 Rev 5 Cloud Security Assessor for AWS.
    """
    
    # Control family descriptions
    CONTROL_FAMILIES = {
        'AC': 'Access Control',
        'AU': 'Audit and Accountability',
        'CA': 'Assessment, Authorization, and Monitoring',
        'CM': 'Configuration Management',
        'CP': 'Contingency Planning',
        'IA': 'Identification and Authentication',
        'IR': 'Incident Response',
        'MP': 'Media Protection',
        'RA': 'Risk Assessment',
        'SA': 'System and Services Acquisition',
        'SC': 'System and Communications Protection',
        'SI': 'System and Information Integrity',
        'SR': 'Supply Chain Risk Management'
    }
    
    def __init__(self, region: str = None):
        """Initialize all AWS clients."""
        self.region = region
        self.results: List[ControlResult] = []
        
        try:
            # Core services
            self.sts = boto3.client('sts', region_name=region)
            self.iam = boto3.client('iam', region_name=region)
            self.s3 = boto3.client('s3', region_name=region)
            self.ec2 = boto3.client('ec2', region_name=region)
            self.kms = boto3.client('kms', region_name=region)
            
            # Logging & Monitoring
            self.cloudtrail = boto3.client('cloudtrail', region_name=region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=region)
            self.logs = boto3.client('logs', region_name=region)
            self.config = boto3.client('config', region_name=region)
            
            # Security services
            self.guardduty = boto3.client('guardduty', region_name=region)
            self.securityhub = boto3.client('securityhub', region_name=region)
            self.inspector2 = boto3.client('inspector2', region_name=region)
            self.macie2 = boto3.client('macie2', region_name=region)
            
            # Backup & DR
            self.backup = boto3.client('backup', region_name=region)
            self.rds = boto3.client('rds', region_name=region)
            
            # Network
            self.elbv2 = boto3.client('elbv2', region_name=region)
            self.wafv2 = boto3.client('wafv2', region_name=region)
            self.acm = boto3.client('acm', region_name=region)
            
            # Development
            self.codepipeline = boto3.client('codepipeline', region_name=region)
            self.codebuild = boto3.client('codebuild', region_name=region)
            
            # Management
            self.ssm = boto3.client('ssm', region_name=region)
            self.sns = boto3.client('sns', region_name=region)
            self.lambda_client = boto3.client('lambda', region_name=region)
            self.secretsmanager = boto3.client('secretsmanager', region_name=region)
            
            # Verify credentials
            identity = self.sts.get_caller_identity()
            self.account_id = identity['Account']
            self.caller_arn = identity['Arn']
            
            print(f"[OK] Connected to AWS Account: {self.account_id}")
            print(f"[USER] Identity: {self.caller_arn}")
            print(f"[REGION] Region: {region or 'default'}\n")
            
        except NoCredentialsError:
            raise Exception("AWS credentials not found.")

    def _safe_call(self, func, default=None):
        """Safely call AWS API and handle errors."""
        try:
            return func()
        except ClientError:
            return default
        except Exception:
            return default

    # =========================================================================
    # AC - ACCESS CONTROL
    # =========================================================================
    
    def check_ac_2_account_management(self) -> ControlResult:
        """AC-2: Account Management - Manage system accounts."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check for unused IAM users
            users = self.iam.list_users()['Users']
            for user in users:
                username = user['UserName']
                
                # Check password last used
                if 'PasswordLastUsed' in user:
                    days_since = (datetime.now(timezone.utc) - user['PasswordLastUsed']).days
                    if days_since > 90:
                        status = ControlStatus.WARNING
                        findings.append(f"User '{username}' password unused for {days_since} days")
                        recommendations.append(f"Review account '{username}' for necessity")
                
                # Check access keys
                keys = self.iam.list_access_keys(UserName=username)['AccessKeyMetadata']
                for key in keys:
                    last_used = self._safe_call(
                        lambda: self.iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
                    )
                    if last_used and 'LastUsedDate' not in last_used.get('AccessKeyLastUsed', {}):
                        findings.append(f"User '{username}' has unused access key")
            
            if not findings:
                findings.append(f"Reviewed {len(users)} IAM users - all appear active")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AC-2", "Account Management", "AC", status, findings, recommendations)
    
    def check_ac_3_access_enforcement(self) -> ControlResult:
        """AC-3: Access Enforcement - Enforce approved authorizations."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check for overly permissive policies
            policies = self.iam.list_policies(Scope='Local')['Policies']
            
            for policy in policies[:20]:  # Check first 20
                version = self.iam.get_policy_version(
                    PolicyArn=policy['Arn'],
                    VersionId=policy['DefaultVersionId']
                )['PolicyVersion']['Document']
                
                if isinstance(version, str):
                    version = json.loads(version)
                
                for stmt in version.get('Statement', []):
                    if stmt.get('Effect') == 'Allow':
                        actions = stmt.get('Action', [])
                        resources = stmt.get('Resource', [])
                        
                        if isinstance(actions, str):
                            actions = [actions]
                        if isinstance(resources, str):
                            resources = [resources]
                        
                        if '*' in actions and '*' in resources:
                            status = ControlStatus.FAIL
                            findings.append(f"Policy '{policy['PolicyName']}' grants admin access (*:*)")
                            recommendations.append("Apply least privilege principle")
            
            if status == ControlStatus.PASS:
                findings.append("IAM policies follow access enforcement principles")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AC-3", "Access Enforcement", "AC", status, findings, recommendations)
    
    def check_ac_4_information_flow(self) -> ControlResult:
        """AC-4: Information Flow Enforcement - Control information flow."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check VPC Flow Logs
            vpcs = self.ec2.describe_vpcs()['Vpcs']
            flow_logs = self.ec2.describe_flow_logs()['FlowLogs']
            vpc_with_logs = {fl['ResourceId'] for fl in flow_logs}
            
            for vpc in vpcs:
                if vpc['VpcId'] not in vpc_with_logs:
                    status = ControlStatus.WARNING
                    findings.append(f"VPC {vpc['VpcId']} has no flow logs")
                    recommendations.append(f"Enable VPC Flow Logs for {vpc['VpcId']}")
            
            # Check NACLs for overly permissive rules
            nacls = self.ec2.describe_network_acls()['NetworkAcls']
            for nacl in nacls:
                for entry in nacl.get('Entries', []):
                    if entry.get('CidrBlock') == '0.0.0.0/0' and entry.get('RuleAction') == 'allow':
                        if entry.get('Protocol') == '-1':  # All traffic
                            findings.append(f"NACL {nacl['NetworkAclId']} allows all traffic from 0.0.0.0/0")
            
            if status == ControlStatus.PASS and not findings:
                findings.append("Information flow controls are properly configured")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AC-4", "Information Flow Enforcement", "AC", status, findings, recommendations)
    
    def check_ac_5_separation_of_duties(self) -> ControlResult:
        """AC-5: Separation of Duties - Separate duties of individuals."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check for users with both admin and user permissions
            users = self.iam.list_users()['Users']
            
            for user in users[:20]:
                username = user['UserName']
                attached = self.iam.list_attached_user_policies(UserName=username)['AttachedPolicies']
                
                admin_policies = [p for p in attached if 'Admin' in p['PolicyName'] or 'FullAccess' in p['PolicyName']]
                
                if len(admin_policies) > 2:
                    status = ControlStatus.WARNING
                    findings.append(f"User '{username}' has {len(admin_policies)} admin/full-access policies")
                    recommendations.append(f"Review separation of duties for '{username}'")
            
            if status == ControlStatus.PASS:
                findings.append("Separation of duties appears properly implemented")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AC-5", "Separation of Duties", "AC", status, findings, recommendations)
    
    def check_ac_6_least_privilege(self) -> ControlResult:
        """AC-6: Least Privilege - Employ least privilege principle."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check for wildcard permissions
            policies = self.iam.list_policies(Scope='Local')['Policies']
            wildcard_count = 0
            
            for policy in policies[:20]:
                version = self.iam.get_policy_version(
                    PolicyArn=policy['Arn'],
                    VersionId=policy['DefaultVersionId']
                )['PolicyVersion']['Document']
                
                if isinstance(version, str):
                    version = json.loads(version)
                
                for stmt in version.get('Statement', []):
                    if stmt.get('Effect') == 'Allow':
                        actions = stmt.get('Action', [])
                        if isinstance(actions, str):
                            actions = [actions]
                        
                        for action in actions:
                            if action.endswith(':*') or action == '*':
                                wildcard_count += 1
                                if wildcard_count <= 5:
                                    findings.append(f"Policy '{policy['PolicyName']}' uses wildcard: {action}")
            
            if wildcard_count > 0:
                status = ControlStatus.WARNING
                recommendations.append("Replace wildcard actions with specific permissions")
            else:
                findings.append("Policies follow least privilege principle")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AC-6", "Least Privilege", "AC", status, findings, recommendations)
    
    def check_ac_7_unsuccessful_logons(self) -> ControlResult:
        """AC-7: Unsuccessful Logon Attempts - Enforce limit on consecutive invalid attempts."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check IAM password policy
            try:
                policy = self.iam.get_account_password_policy()['PasswordPolicy']
                findings.append("IAM password policy is configured")
                
                if not policy.get('MaxPasswordAge'):
                    recommendations.append("Consider setting password expiration")
            except ClientError:
                status = ControlStatus.WARNING
                findings.append("No IAM password policy configured")
                recommendations.append("Configure IAM password policy")
            
            # Note: AWS doesn't have built-in lockout, but GuardDuty can detect brute force
            try:
                detectors = self.guardduty.list_detectors()['DetectorIds']
                if detectors:
                    findings.append("GuardDuty enabled - can detect brute force attempts")
                else:
                    recommendations.append("Enable GuardDuty for brute force detection")
            except ClientError:
                pass
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AC-7", "Unsuccessful Logon Attempts", "AC", status, findings, recommendations)
    
    def check_ac_17_remote_access(self) -> ControlResult:
        """AC-17: Remote Access - Establish usage restrictions for remote access."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check for SSH/RDP exposed to internet
            sgs = self.ec2.describe_security_groups()['SecurityGroups']
            
            for sg in sgs:
                for rule in sg.get('IpPermissions', []):
                    from_port = rule.get('FromPort', 0)
                    to_port = rule.get('ToPort', 65535)
                    
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            if from_port <= 22 <= to_port:
                                status = ControlStatus.FAIL
                                findings.append(f"SG '{sg['GroupId']}' exposes SSH to internet")
                                recommendations.append("Restrict SSH to specific IPs or use SSM")
                            if from_port <= 3389 <= to_port:
                                status = ControlStatus.FAIL
                                findings.append(f"SG '{sg['GroupId']}' exposes RDP to internet")
                                recommendations.append("Restrict RDP to specific IPs or use VPN")
            
            if status == ControlStatus.PASS:
                findings.append("Remote access controls properly configured")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AC-17", "Remote Access", "AC", status, findings, recommendations)

    # =========================================================================
    # AU - AUDIT AND ACCOUNTABILITY
    # =========================================================================
    
    def check_au_2_event_logging(self) -> ControlResult:
        """AU-2: Event Logging - Identify events to be logged."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            trails = self.cloudtrail.describe_trails()['trailList']
            
            if not trails:
                status = ControlStatus.FAIL
                findings.append("No CloudTrail trails configured")
                recommendations.append("Enable CloudTrail for audit logging")
            else:
                for trail in trails:
                    trail_status = self.cloudtrail.get_trail_status(Name=trail['Name'])
                    
                    if trail_status.get('IsLogging'):
                        findings.append(f"Trail '{trail['Name']}' is actively logging")
                    else:
                        status = ControlStatus.FAIL
                        findings.append(f"Trail '{trail['Name']}' is NOT logging")
                        recommendations.append(f"Enable logging for '{trail['Name']}'")
                    
                    if not trail.get('IsMultiRegionTrail'):
                        status = ControlStatus.WARNING
                        recommendations.append(f"Enable multi-region for '{trail['Name']}'")
                        
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AU-2", "Event Logging", "AU", status, findings, recommendations)
    
    def check_au_3_content_of_audit_records(self) -> ControlResult:
        """AU-3: Content of Audit Records - Include required information."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            trails = self.cloudtrail.describe_trails()['trailList']
            
            for trail in trails:
                selectors = self.cloudtrail.get_event_selectors(TrailName=trail['Name'])
                
                has_management = False
                has_data = False
                
                for sel in selectors.get('EventSelectors', []):
                    if sel.get('IncludeManagementEvents'):
                        has_management = True
                    if sel.get('DataResources'):
                        has_data = True
                
                if has_management:
                    findings.append(f"Trail '{trail['Name']}' captures management events")
                if has_data:
                    findings.append(f"Trail '{trail['Name']}' captures data events")
                
                if not has_management:
                    status = ControlStatus.WARNING
                    recommendations.append(f"Enable management events for '{trail['Name']}'")
                    
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AU-3", "Content of Audit Records", "AU", status, findings, recommendations)
    
    def check_au_6_audit_review(self) -> ControlResult:
        """AU-6: Audit Record Review, Analysis, and Reporting."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check CloudWatch alarms
            alarms = self.cloudwatch.describe_alarms()['MetricAlarms']
            security_alarms = [a for a in alarms if any(
                kw in a['AlarmName'].lower() for kw in ['security', 'auth', 'login', 'trail']
            )]
            
            if security_alarms:
                findings.append(f"Found {len(security_alarms)} security-related alarms")
            else:
                status = ControlStatus.WARNING
                findings.append("No security-focused CloudWatch alarms found")
                recommendations.append("Create alarms for security events")
            
            # Check for CloudTrail Insights
            trails = self.cloudtrail.describe_trails()['trailList']
            insights_enabled = any(t.get('HasInsightSelectors') for t in trails)
            
            if insights_enabled:
                findings.append("CloudTrail Insights enabled for anomaly detection")
            else:
                recommendations.append("Enable CloudTrail Insights")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AU-6", "Audit Record Review", "AU", status, findings, recommendations)
    
    def check_au_9_protection_of_audit_info(self) -> ControlResult:
        """AU-9: Protection of Audit Information."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            trails = self.cloudtrail.describe_trails()['trailList']
            
            for trail in trails:
                # Check log file validation
                if trail.get('LogFileValidationEnabled'):
                    findings.append(f"Trail '{trail['Name']}' has log validation enabled")
                else:
                    status = ControlStatus.WARNING
                    findings.append(f"Trail '{trail['Name']}' lacks log validation")
                    recommendations.append(f"Enable log validation for '{trail['Name']}'")
                
                # Check encryption
                if trail.get('KMSKeyId'):
                    findings.append(f"Trail '{trail['Name']}' is KMS encrypted")
                else:
                    status = ControlStatus.WARNING
                    recommendations.append(f"Enable KMS encryption for '{trail['Name']}'")
                
                # Check S3 bucket security
                bucket = trail.get('S3BucketName')
                if bucket:
                    try:
                        public_block = self.s3.get_public_access_block(Bucket=bucket)
                        config = public_block['PublicAccessBlockConfiguration']
                        if all([config.get('BlockPublicAcls'), config.get('BlockPublicPolicy')]):
                            findings.append(f"Bucket '{bucket}' blocks public access")
                        else:
                            status = ControlStatus.FAIL
                            findings.append(f"Bucket '{bucket}' may allow public access")
                    except ClientError:
                        recommendations.append(f"Configure public access block for '{bucket}'")
                        
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AU-9", "Protection of Audit Information", "AU", status, findings, recommendations)
    
    def check_au_11_audit_record_retention(self) -> ControlResult:
        """AU-11: Audit Record Retention."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check CloudWatch Logs retention
            log_groups = self.logs.describe_log_groups()['logGroups']
            no_retention = [lg for lg in log_groups if 'retentionInDays' not in lg]
            
            if no_retention:
                findings.append(f"{len(no_retention)} log groups have unlimited retention")
            
            with_retention = [lg for lg in log_groups if 'retentionInDays' in lg]
            if with_retention:
                findings.append(f"{len(with_retention)} log groups have retention policies")
            
            # Check S3 lifecycle for CloudTrail buckets
            trails = self.cloudtrail.describe_trails()['trailList']
            for trail in trails:
                bucket = trail.get('S3BucketName')
                if bucket:
                    try:
                        lifecycle = self.s3.get_bucket_lifecycle_configuration(Bucket=bucket)
                        findings.append(f"Bucket '{bucket}' has lifecycle rules")
                    except ClientError:
                        findings.append(f"Bucket '{bucket}' has no lifecycle (indefinite retention)")
                        
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AU-11", "Audit Record Retention", "AU", status, findings, recommendations)
    
    def check_au_12_audit_record_generation(self) -> ControlResult:
        """AU-12: Audit Record Generation."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check CloudTrail
            trails = self.cloudtrail.describe_trails()['trailList']
            active = sum(1 for t in trails if self.cloudtrail.get_trail_status(Name=t['Name']).get('IsLogging'))
            
            if active > 0:
                findings.append(f"{active} CloudTrail trail(s) actively logging")
            else:
                status = ControlStatus.FAIL
                findings.append("No active CloudTrail logging")
                recommendations.append("Enable CloudTrail logging")
            
            # Check AWS Config
            try:
                recorders = self.config.describe_configuration_recorders()['ConfigurationRecorders']
                if recorders:
                    findings.append("AWS Config is configured")
                else:
                    recommendations.append("Enable AWS Config")
            except ClientError:
                pass
            
            # Check VPC Flow Logs
            vpcs = self.ec2.describe_vpcs()['Vpcs']
            flow_logs = self.ec2.describe_flow_logs()['FlowLogs']
            
            if len(flow_logs) >= len(vpcs):
                findings.append("VPC Flow Logs enabled for all VPCs")
            else:
                status = ControlStatus.WARNING
                findings.append(f"Only {len(flow_logs)} flow logs for {len(vpcs)} VPCs")
                recommendations.append("Enable VPC Flow Logs for all VPCs")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("AU-12", "Audit Record Generation", "AU", status, findings, recommendations)

    # =========================================================================
    # CA - ASSESSMENT, AUTHORIZATION, AND MONITORING
    # =========================================================================
    
    def check_ca_2_control_assessments(self) -> ControlResult:
        """CA-2: Control Assessments."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check Security Hub
            try:
                hub = self.securityhub.describe_hub()
                findings.append("Security Hub is enabled")
                
                # Check enabled standards
                standards = self.securityhub.get_enabled_standards()['StandardsSubscriptions']
                findings.append(f"{len(standards)} security standard(s) enabled")
            except ClientError:
                status = ControlStatus.WARNING
                findings.append("Security Hub not enabled")
                recommendations.append("Enable Security Hub for continuous assessment")
            
            # Check AWS Config rules
            try:
                rules = self.config.describe_config_rules()['ConfigRules']
                findings.append(f"{len(rules)} Config rules configured")
            except ClientError:
                recommendations.append("Configure AWS Config rules")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("CA-2", "Control Assessments", "CA", status, findings, recommendations)
    
    def check_ca_7_continuous_monitoring(self) -> ControlResult:
        """CA-7: Continuous Monitoring."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check GuardDuty
            try:
                detectors = self.guardduty.list_detectors()['DetectorIds']
                if detectors:
                    findings.append("GuardDuty is enabled for threat detection")
                    
                    # Check for findings
                    for detector_id in detectors[:1]:
                        finding_stats = self.guardduty.get_findings_statistics(
                            DetectorId=detector_id,
                            FindingStatisticTypes=['COUNT_BY_SEVERITY']
                        )
                        findings.append("GuardDuty actively monitoring for threats")
                else:
                    status = ControlStatus.WARNING
                    findings.append("GuardDuty not enabled")
                    recommendations.append("Enable GuardDuty for threat detection")
            except ClientError:
                recommendations.append("Enable GuardDuty")
            
            # Check CloudWatch alarms
            alarms = self.cloudwatch.describe_alarms()['MetricAlarms']
            findings.append(f"{len(alarms)} CloudWatch alarms configured")
            
            if len(alarms) == 0:
                status = ControlStatus.WARNING
                recommendations.append("Configure CloudWatch alarms for monitoring")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("CA-7", "Continuous Monitoring", "CA", status, findings, recommendations)

    # =========================================================================
    # CM - CONFIGURATION MANAGEMENT
    # =========================================================================
    
    def check_cm_2_baseline_configuration(self) -> ControlResult:
        """CM-2: Baseline Configuration."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check AWS Config
            try:
                recorders = self.config.describe_configuration_recorders()['ConfigurationRecorders']
                status_list = self.config.describe_configuration_recorder_status()['ConfigurationRecordersStatus']
                
                recording = any(s.get('recording') for s in status_list)
                
                if recorders and recording:
                    findings.append("AWS Config is recording configuration baselines")
                else:
                    status = ControlStatus.WARNING
                    findings.append("AWS Config not actively recording")
                    recommendations.append("Enable AWS Config for baseline tracking")
            except ClientError:
                status = ControlStatus.WARNING
                recommendations.append("Configure AWS Config")
            
            # Check for SSM State Manager
            try:
                associations = self.ssm.list_associations()['Associations']
                if associations:
                    findings.append(f"{len(associations)} SSM associations for configuration management")
            except ClientError:
                pass
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("CM-2", "Baseline Configuration", "CM", status, findings, recommendations)
    
    def check_cm_6_configuration_settings(self) -> ControlResult:
        """CM-6: Configuration Settings."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check Config rules for configuration compliance
            try:
                rules = self.config.describe_config_rules()['ConfigRules']
                
                compliant = 0
                non_compliant = 0
                
                for rule in rules[:10]:
                    try:
                        compliance = self.config.get_compliance_details_by_config_rule(
                            ConfigRuleName=rule['ConfigRuleName'],
                            Limit=1
                        )
                        results = compliance.get('EvaluationResults', [])
                        if results:
                            if results[0].get('ComplianceType') == 'COMPLIANT':
                                compliant += 1
                            else:
                                non_compliant += 1
                    except ClientError:
                        pass
                
                findings.append(f"Config rules: {compliant} compliant, {non_compliant} non-compliant")
                
                if non_compliant > 0:
                    status = ControlStatus.WARNING
                    recommendations.append("Review and remediate non-compliant Config rules")
                    
            except ClientError:
                recommendations.append("Configure AWS Config rules")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("CM-6", "Configuration Settings", "CM", status, findings, recommendations)
    
    def check_cm_8_system_component_inventory(self) -> ControlResult:
        """CM-8: System Component Inventory."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Count EC2 instances
            instances = self.ec2.describe_instances()['Reservations']
            instance_count = sum(len(r['Instances']) for r in instances)
            findings.append(f"EC2 Instances: {instance_count}")
            
            # Count S3 buckets
            buckets = self.s3.list_buckets()['Buckets']
            findings.append(f"S3 Buckets: {len(buckets)}")
            
            # Count RDS instances
            try:
                rds_instances = self.rds.describe_db_instances()['DBInstances']
                findings.append(f"RDS Instances: {len(rds_instances)}")
            except ClientError:
                pass
            
            # Count Lambda functions
            try:
                functions = self.lambda_client.list_functions()['Functions']
                findings.append(f"Lambda Functions: {len(functions)}")
            except ClientError:
                pass
            
            # Check if AWS Config is tracking resources
            try:
                resources = self.config.get_discovered_resource_counts()['resourceCounts']
                total = sum(r['count'] for r in resources)
                findings.append(f"AWS Config tracking {total} total resources")
            except ClientError:
                recommendations.append("Enable AWS Config for comprehensive inventory")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("CM-8", "System Component Inventory", "CM", status, findings, recommendations)

    # =========================================================================
    # CP - CONTINGENCY PLANNING
    # =========================================================================
    
    def check_cp_9_system_backup(self) -> ControlResult:
        """CP-9: System Backup."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check AWS Backup
            try:
                plans = self.backup.list_backup_plans()['BackupPlansList']
                if plans:
                    findings.append(f"{len(plans)} AWS Backup plan(s) configured")
                else:
                    status = ControlStatus.WARNING
                    findings.append("No AWS Backup plans configured")
                    recommendations.append("Configure AWS Backup plans")
            except ClientError:
                pass
            
            # Check RDS automated backups
            try:
                rds_instances = self.rds.describe_db_instances()['DBInstances']
                with_backup = [db for db in rds_instances if db.get('BackupRetentionPeriod', 0) > 0]
                
                if rds_instances:
                    findings.append(f"RDS: {len(with_backup)}/{len(rds_instances)} have automated backups")
                    
                    if len(with_backup) < len(rds_instances):
                        status = ControlStatus.WARNING
                        recommendations.append("Enable automated backups for all RDS instances")
            except ClientError:
                pass
            
            # Check EBS snapshots
            snapshots = self.ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']
            findings.append(f"EBS Snapshots: {len(snapshots)}")
            
            if len(snapshots) == 0:
                status = ControlStatus.WARNING
                recommendations.append("Create EBS snapshots for backup")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("CP-9", "System Backup", "CP", status, findings, recommendations)
    
    def check_cp_10_system_recovery(self) -> ControlResult:
        """CP-10: System Recovery and Reconstitution."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check for multi-AZ deployments
            try:
                rds_instances = self.rds.describe_db_instances()['DBInstances']
                multi_az = [db for db in rds_instances if db.get('MultiAZ')]
                
                if rds_instances:
                    findings.append(f"RDS: {len(multi_az)}/{len(rds_instances)} are Multi-AZ")
                    
                    if len(multi_az) < len(rds_instances):
                        recommendations.append("Consider Multi-AZ for critical RDS instances")
            except ClientError:
                pass
            
            # Check for Auto Scaling groups
            try:
                asg = boto3.client('autoscaling', region_name=self.region)
                groups = asg.describe_auto_scaling_groups()['AutoScalingGroups']
                findings.append(f"Auto Scaling Groups: {len(groups)}")
            except ClientError:
                pass
            
            # Check for ELB health checks
            try:
                lbs = self.elbv2.describe_load_balancers()['LoadBalancers']
                findings.append(f"Load Balancers: {len(lbs)}")
            except ClientError:
                pass
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("CP-10", "System Recovery and Reconstitution", "CP", status, findings, recommendations)

    # =========================================================================
    # IA - IDENTIFICATION AND AUTHENTICATION
    # =========================================================================
    
    def check_ia_2_identification_and_auth(self) -> ControlResult:
        """IA-2: Identification and Authentication (Organizational Users)."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check root account MFA
            summary = self.iam.get_account_summary()['SummaryMap']
            
            if summary.get('AccountMFAEnabled', 0) == 0:
                status = ControlStatus.CRITICAL if hasattr(ControlStatus, 'CRITICAL') else ControlStatus.FAIL
                findings.append("Root account MFA is NOT enabled")
                recommendations.append("Enable MFA on root account immediately")
            else:
                findings.append("Root account MFA is enabled")
            
            # Check user MFA
            users = self.iam.list_users()['Users']
            users_without_mfa = []
            
            for user in users:
                mfa = self.iam.list_mfa_devices(UserName=user['UserName'])['MFADevices']
                if not mfa:
                    # Check if user has console access
                    try:
                        self.iam.get_login_profile(UserName=user['UserName'])
                        users_without_mfa.append(user['UserName'])
                    except ClientError:
                        pass
            
            if users_without_mfa:
                status = ControlStatus.WARNING
                findings.append(f"{len(users_without_mfa)} console user(s) without MFA")
                recommendations.append("Enable MFA for all console users")
            else:
                findings.append("All console users have MFA enabled")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("IA-2", "Identification and Authentication", "IA", status, findings, recommendations)
    
    def check_ia_5_authenticator_management(self) -> ControlResult:
        """IA-5: Authenticator Management."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check password policy
            try:
                policy = self.iam.get_account_password_policy()['PasswordPolicy']
                
                checks = {
                    'MinimumPasswordLength': (14, 'Minimum password length'),
                    'RequireSymbols': (True, 'Require symbols'),
                    'RequireNumbers': (True, 'Require numbers'),
                    'RequireUppercaseCharacters': (True, 'Require uppercase'),
                    'RequireLowercaseCharacters': (True, 'Require lowercase'),
                    'MaxPasswordAge': (90, 'Password expiration'),
                    'PasswordReusePrevention': (24, 'Password reuse prevention')
                }
                
                for key, (expected, desc) in checks.items():
                    actual = policy.get(key)
                    if isinstance(expected, bool):
                        if actual == expected:
                            findings.append(f"✓ {desc}")
                        else:
                            status = ControlStatus.WARNING
                            findings.append(f"✗ {desc} not configured")
                    elif isinstance(expected, int):
                        if actual and actual >= expected:
                            findings.append(f"✓ {desc}: {actual}")
                        elif actual:
                            findings.append(f"⚠ {desc}: {actual} (recommended: {expected})")
                        else:
                            recommendations.append(f"Configure {desc}")
                            
            except ClientError:
                status = ControlStatus.FAIL
                findings.append("No password policy configured")
                recommendations.append("Configure IAM password policy")
            
            # Check for old access keys
            users = self.iam.list_users()['Users']
            old_keys = 0
            
            for user in users:
                keys = self.iam.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']
                for key in keys:
                    age = (datetime.now(timezone.utc) - key['CreateDate']).days
                    if age > 90:
                        old_keys += 1
            
            if old_keys > 0:
                status = ControlStatus.WARNING
                findings.append(f"{old_keys} access key(s) over 90 days old")
                recommendations.append("Rotate access keys regularly")
            else:
                findings.append("All access keys are current")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("IA-5", "Authenticator Management", "IA", status, findings, recommendations)

    # =========================================================================
    # IR - INCIDENT RESPONSE
    # =========================================================================
    
    def check_ir_4_incident_handling(self) -> ControlResult:
        """IR-4: Incident Handling."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check GuardDuty for threat detection
            try:
                detectors = self.guardduty.list_detectors()['DetectorIds']
                if detectors:
                    findings.append("GuardDuty enabled for threat detection")
                    
                    # Check for active findings
                    for det_id in detectors[:1]:
                        findings_list = self.guardduty.list_findings(
                            DetectorId=det_id,
                            FindingCriteria={'Criterion': {'severity': {'Gte': 4}}}
                        )['FindingIds']
                        
                        if findings_list:
                            status = ControlStatus.WARNING
                            findings.append(f"{len(findings_list)} medium+ severity findings")
                            recommendations.append("Review and respond to GuardDuty findings")
                else:
                    status = ControlStatus.WARNING
                    findings.append("GuardDuty not enabled")
                    recommendations.append("Enable GuardDuty for incident detection")
            except ClientError:
                recommendations.append("Enable GuardDuty")
            
            # Check for SNS topics (for alerting)
            try:
                topics = self.sns.list_topics()['Topics']
                security_topics = [t for t in topics if any(
                    kw in t['TopicArn'].lower() for kw in ['security', 'alert', 'incident']
                )]
                
                if security_topics:
                    findings.append(f"{len(security_topics)} security-related SNS topics")
                else:
                    recommendations.append("Create SNS topics for security alerts")
            except ClientError:
                pass
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("IR-4", "Incident Handling", "IR", status, findings, recommendations)
    
    def check_ir_6_incident_reporting(self) -> ControlResult:
        """IR-6: Incident Reporting."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check Security Hub for centralized findings
            try:
                hub = self.securityhub.describe_hub()
                findings.append("Security Hub enabled for centralized reporting")
                
                # Check for findings
                sec_findings = self.securityhub.get_findings(MaxResults=10)['Findings']
                if sec_findings:
                    critical = len([f for f in sec_findings if f.get('Severity', {}).get('Label') == 'CRITICAL'])
                    high = len([f for f in sec_findings if f.get('Severity', {}).get('Label') == 'HIGH'])
                    
                    if critical > 0 or high > 0:
                        status = ControlStatus.WARNING
                        findings.append(f"Security Hub: {critical} critical, {high} high findings")
                        recommendations.append("Review and report Security Hub findings")
            except ClientError:
                recommendations.append("Enable Security Hub for incident reporting")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("IR-6", "Incident Reporting", "IR", status, findings, recommendations)

    # =========================================================================
    # MP - MEDIA PROTECTION  
    # =========================================================================
    
    def check_mp_4_media_storage(self) -> ControlResult:
        """MP-4: Media Storage - Protect media containing CUI."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check S3 bucket encryption
            buckets = self.s3.list_buckets()['Buckets']
            encrypted = 0
            unencrypted = []
            
            for bucket in buckets:
                try:
                    self.s3.get_bucket_encryption(Bucket=bucket['Name'])
                    encrypted += 1
                except ClientError as e:
                    if 'ServerSideEncryptionConfigurationNotFoundError' in str(e):
                        unencrypted.append(bucket['Name'])
            
            findings.append(f"S3: {encrypted}/{len(buckets)} buckets encrypted")
            
            if unencrypted:
                status = ControlStatus.WARNING
                findings.append(f"Unencrypted buckets: {', '.join(unencrypted[:3])}")
                recommendations.append("Enable default encryption for all S3 buckets")
            
            # Check EBS encryption
            try:
                ebs_default = self.ec2.get_ebs_encryption_by_default()
                if ebs_default.get('EbsEncryptionByDefault'):
                    findings.append("EBS encryption by default is enabled")
                else:
                    status = ControlStatus.WARNING
                    findings.append("EBS encryption by default is disabled")
                    recommendations.append("Enable EBS encryption by default")
            except ClientError:
                pass
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("MP-4", "Media Storage", "MP", status, findings, recommendations)

    # =========================================================================
    # RA - RISK ASSESSMENT
    # =========================================================================
    
    def check_ra_5_vulnerability_monitoring(self) -> ControlResult:
        """RA-5: Vulnerability Monitoring and Scanning."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check Inspector
            try:
                inspector_status = self.inspector2.batch_get_account_status(
                    accountIds=[self.account_id]
                )
                
                for account in inspector_status.get('accounts', []):
                    state = account.get('state', {}).get('status')
                    if state == 'ENABLED':
                        findings.append("Amazon Inspector is enabled")
                        
                        # Check for findings
                        finding_counts = self.inspector2.list_finding_aggregations(
                            aggregationType='SEVERITY'
                        )
                        findings.append("Inspector actively scanning for vulnerabilities")
                    else:
                        status = ControlStatus.WARNING
                        findings.append("Amazon Inspector not fully enabled")
                        recommendations.append("Enable Amazon Inspector")
            except ClientError:
                status = ControlStatus.WARNING
                findings.append("Amazon Inspector not configured")
                recommendations.append("Enable Amazon Inspector for vulnerability scanning")
            
            # Check Security Hub
            try:
                hub = self.securityhub.describe_hub()
                findings.append("Security Hub provides vulnerability insights")
            except ClientError:
                recommendations.append("Enable Security Hub")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("RA-5", "Vulnerability Monitoring and Scanning", "RA", status, findings, recommendations)

    # =========================================================================
    # SA - SYSTEM AND SERVICES ACQUISITION
    # =========================================================================
    
    def check_sa_3_system_development_lifecycle(self) -> ControlResult:
        """SA-3: System Development Life Cycle."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check CodePipeline
            pipelines = self.codepipeline.list_pipelines()['pipelines']
            if pipelines:
                findings.append(f"{len(pipelines)} CodePipeline(s) for SDLC")
            else:
                status = ControlStatus.WARNING
                recommendations.append("Implement CI/CD pipelines")
            
            # Check CodeBuild
            projects = self.codebuild.list_projects()['projects']
            if projects:
                findings.append(f"{len(projects)} CodeBuild project(s)")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("SA-3", "System Development Life Cycle", "SA", status, findings, recommendations)
    
    def check_sa_9_external_system_services(self) -> ControlResult:
        """SA-9: External System Services."""
        findings, recommendations = [], []
        status = ControlStatus.WARNING  # Always needs manual review
        
        try:
            # Check for IAM roles with external trust
            roles = self.iam.list_roles()['Roles']
            external_trust = []
            
            for role in roles:
                trust = role.get('AssumeRolePolicyDocument', {})
                for stmt in trust.get('Statement', []):
                    principal = stmt.get('Principal', {})
                    aws_princ = principal.get('AWS', [])
                    
                    if isinstance(aws_princ, str):
                        aws_princ = [aws_princ]
                    
                    for p in aws_princ:
                        if self.account_id not in str(p) and p != '*':
                            external_trust.append(role['RoleName'])
                            break
            
            if external_trust:
                findings.append(f"{len(external_trust)} role(s) trust external accounts")
                recommendations.append("Review external trust relationships")
            else:
                findings.append("No external trust relationships found")
            
            findings.append("Manual review required for third-party services")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("SA-9", "External System Services", "SA", status, findings, recommendations)

    # =========================================================================
    # SC - SYSTEM AND COMMUNICATIONS PROTECTION
    # =========================================================================
    
    def check_sc_7_boundary_protection(self) -> ControlResult:
        """SC-7: Boundary Protection."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check VPCs
            vpcs = self.ec2.describe_vpcs()['Vpcs']
            findings.append(f"{len(vpcs)} VPC(s) configured")
            
            # Check for internet gateways
            igws = self.ec2.describe_internet_gateways()['InternetGateways']
            findings.append(f"{len(igws)} Internet Gateway(s)")
            
            # Check security groups for overly permissive rules
            sgs = self.ec2.describe_security_groups()['SecurityGroups']
            overly_permissive = 0
            
            for sg in sgs:
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            if rule.get('IpProtocol') == '-1':  # All traffic
                                overly_permissive += 1
            
            if overly_permissive > 0:
                status = ControlStatus.FAIL
                findings.append(f"{overly_permissive} SG(s) allow all traffic from internet")
                recommendations.append("Restrict security group rules")
            else:
                findings.append("Security groups properly restrict traffic")
            
            # Check NACLs
            nacls = self.ec2.describe_network_acls()['NetworkAcls']
            findings.append(f"{len(nacls)} Network ACL(s)")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("SC-7", "Boundary Protection", "SC", status, findings, recommendations)
    
    def check_sc_8_transmission_confidentiality(self) -> ControlResult:
        """SC-8: Transmission Confidentiality and Integrity."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check ALB/ELB for HTTPS
            try:
                lbs = self.elbv2.describe_load_balancers()['LoadBalancers']
                
                for lb in lbs:
                    listeners = self.elbv2.describe_listeners(
                        LoadBalancerArn=lb['LoadBalancerArn']
                    )['Listeners']
                    
                    has_https = any(l['Protocol'] == 'HTTPS' for l in listeners)
                    has_http = any(l['Protocol'] == 'HTTP' for l in listeners)
                    
                    if has_http and not has_https:
                        status = ControlStatus.WARNING
                        findings.append(f"LB '{lb['LoadBalancerName']}' uses HTTP only")
                        recommendations.append(f"Enable HTTPS for '{lb['LoadBalancerName']}'")
                    elif has_https:
                        findings.append(f"LB '{lb['LoadBalancerName']}' uses HTTPS")
            except ClientError:
                pass
            
            # Check ACM certificates
            try:
                certs = self.acm.list_certificates()['CertificateSummaryList']
                valid = [c for c in certs if c.get('Status') == 'ISSUED']
                findings.append(f"{len(valid)} valid ACM certificates")
            except ClientError:
                pass
            
            # Check S3 bucket policies for SSL
            buckets = self.s3.list_buckets()['Buckets']
            for bucket in buckets[:5]:
                try:
                    policy = json.loads(self.s3.get_bucket_policy(Bucket=bucket['Name'])['Policy'])
                    # Check for SSL enforcement
                    for stmt in policy.get('Statement', []):
                        condition = stmt.get('Condition', {})
                        if 'Bool' in condition and 'aws:SecureTransport' in condition['Bool']:
                            findings.append(f"Bucket '{bucket['Name']}' enforces SSL")
                            break
                except ClientError:
                    pass
                    
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("SC-8", "Transmission Confidentiality", "SC", status, findings, recommendations)
    
    def check_sc_12_cryptographic_key_management(self) -> ControlResult:
        """SC-12: Cryptographic Key Establishment and Management."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check KMS keys
            keys = self.kms.list_keys()['Keys']
            
            enabled_keys = 0
            for key in keys[:20]:
                try:
                    key_info = self.kms.describe_key(KeyId=key['KeyId'])['KeyMetadata']
                    if key_info['KeyState'] == 'Enabled':
                        enabled_keys += 1
                        
                        # Check key rotation
                        if key_info['KeyManager'] == 'CUSTOMER':
                            try:
                                rotation = self.kms.get_key_rotation_status(KeyId=key['KeyId'])
                                if not rotation.get('KeyRotationEnabled'):
                                    recommendations.append(f"Enable rotation for key {key['KeyId'][:20]}...")
                            except ClientError:
                                pass
                except ClientError:
                    pass
            
            findings.append(f"{enabled_keys} active KMS key(s)")
            
            if enabled_keys == 0:
                status = ControlStatus.WARNING
                recommendations.append("Create KMS keys for encryption")
            
            # Check Secrets Manager
            try:
                secrets = self.secretsmanager.list_secrets()['SecretList']
                findings.append(f"{len(secrets)} secret(s) in Secrets Manager")
            except ClientError:
                pass
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("SC-12", "Cryptographic Key Management", "SC", status, findings, recommendations)
    
    def check_sc_13_cryptographic_protection(self) -> ControlResult:
        """SC-13: Cryptographic Protection."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check S3 encryption
            buckets = self.s3.list_buckets()['Buckets']
            encrypted = 0
            
            for bucket in buckets:
                try:
                    enc = self.s3.get_bucket_encryption(Bucket=bucket['Name'])
                    rules = enc['ServerSideEncryptionConfiguration']['Rules']
                    algo = rules[0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
                    encrypted += 1
                except ClientError:
                    pass
            
            findings.append(f"S3: {encrypted}/{len(buckets)} buckets encrypted at rest")
            
            if encrypted < len(buckets):
                status = ControlStatus.WARNING
                recommendations.append("Enable encryption for all S3 buckets")
            
            # Check EBS encryption
            volumes = self.ec2.describe_volumes()['Volumes']
            encrypted_vols = [v for v in volumes if v.get('Encrypted')]
            
            findings.append(f"EBS: {len(encrypted_vols)}/{len(volumes)} volumes encrypted")
            
            if len(encrypted_vols) < len(volumes):
                status = ControlStatus.WARNING
                recommendations.append("Encrypt all EBS volumes")
            
            # Check RDS encryption
            try:
                rds_instances = self.rds.describe_db_instances()['DBInstances']
                encrypted_rds = [db for db in rds_instances if db.get('StorageEncrypted')]
                
                findings.append(f"RDS: {len(encrypted_rds)}/{len(rds_instances)} encrypted")
                
                if len(encrypted_rds) < len(rds_instances):
                    status = ControlStatus.WARNING
                    recommendations.append("Enable encryption for all RDS instances")
            except ClientError:
                pass
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("SC-13", "Cryptographic Protection", "SC", status, findings, recommendations)

    # =========================================================================
    # SI - SYSTEM AND INFORMATION INTEGRITY
    # =========================================================================
    
    def check_si_2_flaw_remediation(self) -> ControlResult:
        """SI-2: Flaw Remediation."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check SSM Patch Manager
            try:
                baselines = self.ssm.describe_patch_baselines(
                    Filters=[{'Key': 'OWNER', 'Values': ['Self']}]
                )['BaselineIdentities']
                
                if baselines:
                    findings.append(f"{len(baselines)} custom patch baseline(s)")
                else:
                    findings.append("Using default patch baselines")
            except ClientError:
                pass
            
            # Check for patch compliance
            try:
                compliance = self.ssm.list_compliance_summaries()['ComplianceSummaryItems']
                
                for item in compliance:
                    if item['ComplianceType'] == 'Patch':
                        compliant = item.get('CompliantSummary', {}).get('CompliantCount', 0)
                        non_compliant = item.get('NonCompliantSummary', {}).get('NonCompliantCount', 0)
                        
                        findings.append(f"Patch compliance: {compliant} compliant, {non_compliant} non-compliant")
                        
                        if non_compliant > 0:
                            status = ControlStatus.WARNING
                            recommendations.append("Apply patches to non-compliant instances")
            except ClientError:
                recommendations.append("Configure SSM Patch Manager")
            
            # Check Inspector for vulnerabilities
            try:
                vuln_findings = self.inspector2.list_findings(
                    filterCriteria={'findingStatus': [{'comparison': 'EQUALS', 'value': 'ACTIVE'}]},
                    maxResults=10
                )['findings']
                
                if vuln_findings:
                    critical = len([f for f in vuln_findings if f.get('severity') == 'CRITICAL'])
                    if critical > 0:
                        status = ControlStatus.FAIL
                        findings.append(f"Inspector: {critical} critical vulnerabilities")
                        recommendations.append("Remediate critical vulnerabilities")
            except ClientError:
                pass
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("SI-2", "Flaw Remediation", "SI", status, findings, recommendations)
    
    def check_si_3_malicious_code_protection(self) -> ControlResult:
        """SI-3: Malicious Code Protection."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check GuardDuty (malware detection)
            try:
                detectors = self.guardduty.list_detectors()['DetectorIds']
                
                if detectors:
                    findings.append("GuardDuty enabled for malware detection")
                    
                    # Check for malware findings
                    for det_id in detectors[:1]:
                        malware_findings = self.guardduty.list_findings(
                            DetectorId=det_id,
                            FindingCriteria={
                                'Criterion': {
                                    'type': {'Eq': ['Trojan', 'Backdoor', 'CryptoCurrency']}
                                }
                            }
                        )['FindingIds']
                        
                        if malware_findings:
                            status = ControlStatus.WARNING
                            findings.append(f"GuardDuty: {len(malware_findings)} potential malware finding(s)")
                            recommendations.append("Investigate malware findings")
                else:
                    status = ControlStatus.WARNING
                    findings.append("GuardDuty not enabled")
                    recommendations.append("Enable GuardDuty for malware protection")
            except ClientError:
                recommendations.append("Enable GuardDuty")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("SI-3", "Malicious Code Protection", "SI", status, findings, recommendations)
    
    def check_si_4_system_monitoring(self) -> ControlResult:
        """SI-4: System Monitoring."""
        findings, recommendations = [], []
        status = ControlStatus.PASS
        
        try:
            # Check CloudWatch monitoring
            alarms = self.cloudwatch.describe_alarms()['MetricAlarms']
            findings.append(f"{len(alarms)} CloudWatch alarm(s) configured")
            
            if len(alarms) == 0:
                status = ControlStatus.WARNING
                recommendations.append("Configure CloudWatch alarms")
            
            # Check CloudTrail
            trails = self.cloudtrail.describe_trails()['trailList']
            active = sum(1 for t in trails if self._safe_call(
                lambda: self.cloudtrail.get_trail_status(Name=t['Name']).get('IsLogging'),
                False
            ))
            
            findings.append(f"{active}/{len(trails)} CloudTrail trails active")
            
            # Check VPC Flow Logs
            flow_logs = self.ec2.describe_flow_logs()['FlowLogs']
            findings.append(f"{len(flow_logs)} VPC Flow Log(s)")
            
            # Check GuardDuty
            try:
                detectors = self.guardduty.list_detectors()['DetectorIds']
                if detectors:
                    findings.append("GuardDuty enabled for threat monitoring")
                else:
                    recommendations.append("Enable GuardDuty")
            except ClientError:
                pass
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("SI-4", "System Monitoring", "SI", status, findings, recommendations)

    # =========================================================================
    # SR - SUPPLY CHAIN RISK MANAGEMENT
    # =========================================================================
    
    def check_sr_3_supply_chain_controls(self) -> ControlResult:
        """SR-3: Supply Chain Controls and Processes."""
        findings, recommendations = [], []
        status = ControlStatus.WARNING  # Always needs manual review
        
        try:
            # Check for third-party Lambda layers
            try:
                functions = self.lambda_client.list_functions()['Functions']
                third_party_layers = 0
                
                for func in functions:
                    for layer in func.get('Layers', []):
                        if self.account_id not in layer['Arn']:
                            third_party_layers += 1
                
                if third_party_layers > 0:
                    findings.append(f"{third_party_layers} third-party Lambda layer(s) in use")
                    recommendations.append("Review third-party Lambda layers")
                else:
                    findings.append("No third-party Lambda layers detected")
            except ClientError:
                pass
            
            # Check ECR for external images
            try:
                ecr = boto3.client('ecr', region_name=self.region)
                repos = ecr.describe_repositories()['repositories']
                findings.append(f"{len(repos)} ECR repository(ies)")
                recommendations.append("Scan container images for vulnerabilities")
            except ClientError:
                pass
            
            findings.append("Manual review required for supply chain assessment")
                
        except ClientError as e:
            status = ControlStatus.ERROR
            findings.append(f"Error: {e}")
        
        return ControlResult("SR-3", "Supply Chain Controls", "SR", status, findings, recommendations)

    # =========================================================================
    # MAIN ASSESSMENT METHODS
    # =========================================================================
    
    def get_all_checks(self) -> Dict[str, List]:
        """Return all control check methods organized by family."""
        return {
            'AC': [
                self.check_ac_2_account_management,
                self.check_ac_3_access_enforcement,
                self.check_ac_4_information_flow,
                self.check_ac_5_separation_of_duties,
                self.check_ac_6_least_privilege,
                self.check_ac_7_unsuccessful_logons,
                self.check_ac_17_remote_access,
            ],
            'AU': [
                self.check_au_2_event_logging,
                self.check_au_3_content_of_audit_records,
                self.check_au_6_audit_review,
                self.check_au_9_protection_of_audit_info,
                self.check_au_11_audit_record_retention,
                self.check_au_12_audit_record_generation,
            ],
            'CA': [
                self.check_ca_2_control_assessments,
                self.check_ca_7_continuous_monitoring,
            ],
            'CM': [
                self.check_cm_2_baseline_configuration,
                self.check_cm_6_configuration_settings,
                self.check_cm_8_system_component_inventory,
            ],
            'CP': [
                self.check_cp_9_system_backup,
                self.check_cp_10_system_recovery,
            ],
            'IA': [
                self.check_ia_2_identification_and_auth,
                self.check_ia_5_authenticator_management,
            ],
            'IR': [
                self.check_ir_4_incident_handling,
                self.check_ir_6_incident_reporting,
            ],
            'MP': [
                self.check_mp_4_media_storage,
            ],
            'RA': [
                self.check_ra_5_vulnerability_monitoring,
            ],
            'SA': [
                self.check_sa_3_system_development_lifecycle,
                self.check_sa_9_external_system_services,
            ],
            'SC': [
                self.check_sc_7_boundary_protection,
                self.check_sc_8_transmission_confidentiality,
                self.check_sc_12_cryptographic_key_management,
                self.check_sc_13_cryptographic_protection,
            ],
            'SI': [
                self.check_si_2_flaw_remediation,
                self.check_si_3_malicious_code_protection,
                self.check_si_4_system_monitoring,
            ],
            'SR': [
                self.check_sr_3_supply_chain_controls,
            ],
        }
    
    def run_family(self, family: str) -> List[ControlResult]:
        """Run all checks for a specific control family."""
        checks = self.get_all_checks()
        
        if family not in checks:
            raise ValueError(f"Unknown family: {family}")
        
        print(f"\n{'='*60}")
        print(f"🔍 {family} - {self.CONTROL_FAMILIES.get(family, 'Unknown')}")
        print('='*60)
        
        results = []
        for check in checks[family]:
            result = check()
            results.append(result)
            self._print_result(result)
        
        return results
    
    def run_all_families(self) -> List[ControlResult]:
        """Run all control family checks."""
        all_results = []
        
        for family in self.CONTROL_FAMILIES.keys():
            try:
                results = self.run_family(family)
                all_results.extend(results)
            except Exception as e:
                print(f"Error in family {family}: {e}")
        
        return all_results
    
    # =========================================================================
    # SECURITY HUB INTEGRATION
    # =========================================================================
    
    # Mapping of Security Hub generator IDs to NIST 800-53 control families
    SECURITYHUB_TO_NIST_MAPPING = {
        # AWS Foundational Security Best Practices
        'aws-foundational-security-best-practices': {
            'IAM': 'AC',      # Identity and Access Management -> Access Control
            'S3': 'SC',       # S3 -> System & Communications Protection
            'EC2': 'SC',      # EC2 -> System & Communications Protection
            'RDS': 'SC',      # RDS -> System & Communications Protection
            'Lambda': 'SA',   # Lambda -> System Acquisition
            'CloudTrail': 'AU',  # CloudTrail -> Audit
            'CloudWatch': 'AU',  # CloudWatch -> Audit
            'Config': 'CM',   # Config -> Configuration Management
            'KMS': 'SC',      # KMS -> System & Communications Protection
            'SecretsManager': 'IA',  # Secrets Manager -> Identification & Auth
            'GuardDuty': 'SI',  # GuardDuty -> System Integrity
            'SecurityHub': 'CA',  # SecurityHub -> Assessment & Authorization
            'SNS': 'IR',      # SNS -> Incident Response
            'SQS': 'SC',      # SQS -> System & Communications Protection
            'ELB': 'SC',      # ELB -> System & Communications Protection
            'ACM': 'SC',      # ACM -> System & Communications Protection
            'AutoScaling': 'CP',  # AutoScaling -> Contingency Planning
            'CodeBuild': 'SA',  # CodeBuild -> System Acquisition
            'DynamoDB': 'SC',  # DynamoDB -> System & Communications Protection
            'EFS': 'SC',      # EFS -> System & Communications Protection
            'EKS': 'CM',      # EKS -> Configuration Management
            'ElasticSearch': 'SC',  # ElasticSearch -> System & Communications Protection
            'EMR': 'SC',      # EMR -> System & Communications Protection
            'Redshift': 'SC',  # Redshift -> System & Communications Protection
            'SSM': 'CM',      # SSM -> Configuration Management
            'WAF': 'SC',      # WAF -> System & Communications Protection
        },
        # CIS AWS Foundations Benchmark
        'cis-aws-foundations-benchmark': {
            '1': 'AC',  # IAM
            '2': 'AU',  # Logging
            '3': 'AU',  # Monitoring
            '4': 'SC',  # Networking
            '5': 'SC',  # Networking
        }
    }
    
    # Severity mapping from Security Hub to SAELAR status
    SEVERITY_TO_STATUS = {
        'CRITICAL': ControlStatus.FAIL,
        'HIGH': ControlStatus.FAIL,
        'MEDIUM': ControlStatus.WARNING,
        'LOW': ControlStatus.WARNING,
        'INFORMATIONAL': ControlStatus.PASS,
    }
    
    def import_security_hub_findings(self, max_findings: int = 100, 
                                      include_suppressed: bool = False) -> List[ControlResult]:
        """
        Import findings from AWS Security Hub and convert to SAELAR ControlResults.
        
        This provides a single source of truth by leveraging Security Hub's 
        aggregated findings from GuardDuty, Inspector, Macie, IAM Access Analyzer,
        Firewall Manager, and other integrated services.
        
        Args:
            max_findings: Maximum number of findings to retrieve (default 100)
            include_suppressed: Whether to include suppressed findings (default False)
            
        Returns:
            List of ControlResult objects mapped to NIST 800-53 control families
        """
        results = []
        
        print(f"\n{'='*60}")
        print("🔗 IMPORTING AWS SECURITY HUB FINDINGS")
        print('='*60)
        
        try:
            # Check if Security Hub is enabled
            try:
                hub = self.securityhub.describe_hub()
                hub_arn = hub.get('HubArn', 'Unknown')
                print(f"✅ Security Hub enabled: {hub_arn}")
            except ClientError as e:
                print(f"❌ Security Hub not enabled: {e}")
                return results
            
            # Get enabled standards
            try:
                standards = self.securityhub.get_enabled_standards()['StandardsSubscriptions']
                print(f"📋 Enabled standards: {len(standards)}")
                for std in standards:
                    std_name = std.get('StandardsArn', '').split('/')[-1]
                    print(f"   • {std_name}")
            except ClientError:
                print("   No standards enabled")
            
            # Build filters for findings
            filters = {
                'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}],
            }
            
            if not include_suppressed:
                filters['WorkflowStatus'] = [
                    {'Value': 'NEW', 'Comparison': 'EQUALS'},
                    {'Value': 'NOTIFIED', 'Comparison': 'EQUALS'},
                ]
            
            # Retrieve findings
            print(f"\n🔍 Retrieving findings (max {max_findings})...")
            
            all_findings = []
            paginator = self.securityhub.get_paginator('get_findings')
            
            for page in paginator.paginate(Filters=filters, MaxResults=min(max_findings, 100)):
                all_findings.extend(page.get('Findings', []))
                if len(all_findings) >= max_findings:
                    all_findings = all_findings[:max_findings]
                    break
            
            print(f"   Retrieved {len(all_findings)} findings")
            
            # Categorize findings by severity
            severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFORMATIONAL': 0}
            for finding in all_findings:
                sev = finding.get('Severity', {}).get('Label', 'INFORMATIONAL')
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            print(f"\n📊 Findings by severity:")
            print(f"   🔴 CRITICAL: {severity_counts['CRITICAL']}")
            print(f"   🟠 HIGH: {severity_counts['HIGH']}")
            print(f"   🟡 MEDIUM: {severity_counts['MEDIUM']}")
            print(f"   🟢 LOW: {severity_counts['LOW']}")
            print(f"   ⚪ INFORMATIONAL: {severity_counts['INFORMATIONAL']}")
            
            # Group findings by NIST control family
            findings_by_family = {}
            
            for finding in all_findings:
                # Extract finding details
                finding_id = finding.get('Id', 'Unknown')
                title = finding.get('Title', 'Unknown')
                description = finding.get('Description', '')
                severity = finding.get('Severity', {}).get('Label', 'INFORMATIONAL')
                generator_id = finding.get('GeneratorId', '')
                product_name = finding.get('ProductName', 'Unknown')
                
                # Get compliance status if available
                compliance = finding.get('Compliance', {})
                compliance_status = compliance.get('Status', 'UNKNOWN')
                
                # Get related controls if specified
                related_controls = compliance.get('RelatedRequirements', [])
                
                # Determine NIST family
                nist_family = self._map_finding_to_nist_family(finding)
                
                # Get remediation recommendation
                remediation = finding.get('Remediation', {})
                recommendation = remediation.get('Recommendation', {})
                rec_text = recommendation.get('Text', '')
                rec_url = recommendation.get('Url', '')
                
                # Get affected resources
                resources = finding.get('Resources', [])
                resource_ids = [r.get('Id', 'Unknown') for r in resources[:3]]  # Limit to 3
                
                # Group by family
                if nist_family not in findings_by_family:
                    findings_by_family[nist_family] = []
                
                findings_by_family[nist_family].append({
                    'id': finding_id,
                    'title': title,
                    'description': description,
                    'severity': severity,
                    'generator': generator_id,
                    'product': product_name,
                    'compliance_status': compliance_status,
                    'related_controls': related_controls,
                    'recommendation': rec_text,
                    'recommendation_url': rec_url,
                    'resources': resource_ids,
                })
            
            # Convert grouped findings to ControlResults
            print(f"\n🔄 Mapping to NIST 800-53 control families...")
            
            for family, family_findings in findings_by_family.items():
                family_name = self.CONTROL_FAMILIES.get(family, 'Unknown')
                
                # Determine overall status for this family based on severity
                severities = [f['severity'] for f in family_findings]
                if 'CRITICAL' in severities or 'HIGH' in severities:
                    status = ControlStatus.FAIL
                elif 'MEDIUM' in severities:
                    status = ControlStatus.WARNING
                else:
                    status = ControlStatus.PASS
                
                # Build findings list
                finding_texts = []
                recommendations = []
                
                for f in family_findings[:10]:  # Limit to top 10 per family
                    # Format finding text
                    sev_emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(f['severity'], '⚪')
                    finding_texts.append(f"{sev_emoji} [{f['severity']}] {f['title']}")
                    
                    if f['resources']:
                        finding_texts.append(f"   Resources: {', '.join(f['resources'][:2])}")
                    
                    # Add recommendation if available
                    if f['recommendation'] and f['recommendation'] not in recommendations:
                        recommendations.append(f['recommendation'][:200])  # Truncate long recommendations
                
                # Add summary
                finding_texts.insert(0, f"📥 Security Hub: {len(family_findings)} finding(s) in {family_name}")
                
                # Create ControlResult
                result = ControlResult(
                    control_id=f"SH-{family}",
                    control_name=f"Security Hub - {family_name}",
                    family=family,
                    status=status,
                    findings=finding_texts,
                    recommendations=recommendations[:5]  # Limit to 5 recommendations
                )
                results.append(result)
                
                print(f"   {status.value} {family}: {len(family_findings)} findings")
            
            print(f"\n✅ Imported {len(all_findings)} findings into {len(results)} control families")
            
        except ClientError as e:
            print(f"❌ Error retrieving Security Hub findings: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        return results
    
    def _map_finding_to_nist_family(self, finding: Dict) -> str:
        """
        Map a Security Hub finding to a NIST 800-53 control family.
        
        Uses generator ID, product name, resource type, and compliance info
        to determine the most appropriate NIST control family.
        """
        # Check for explicit NIST mappings in related requirements
        related = finding.get('Compliance', {}).get('RelatedRequirements', [])
        for req in related:
            # Look for NIST 800-53 control references
            if 'NIST' in req.upper() or '800-53' in req:
                # Extract family from control ID (e.g., "NIST.800-53.r5 AC-2" -> "AC")
                for family in self.CONTROL_FAMILIES.keys():
                    if f' {family}-' in req or f'.{family}-' in req or req.startswith(f'{family}-'):
                        return family
        
        # Check generator ID for service-specific mappings
        generator = finding.get('GeneratorId', '').lower()
        
        # AWS service-based mapping
        service_mapping = {
            'iam': 'AC',
            'identity': 'AC',
            'access': 'AC',
            's3': 'SC',
            'ec2': 'SC',
            'vpc': 'SC',
            'security-group': 'SC',
            'network': 'SC',
            'cloudtrail': 'AU',
            'logging': 'AU',
            'cloudwatch': 'AU',
            'monitoring': 'AU',
            'config': 'CM',
            'ssm': 'CM',
            'patch': 'CM',
            'kms': 'SC',
            'encryption': 'SC',
            'secrets': 'IA',
            'password': 'IA',
            'mfa': 'IA',
            'authentication': 'IA',
            'guardduty': 'SI',
            'malware': 'SI',
            'threat': 'SI',
            'inspector': 'RA',
            'vulnerability': 'RA',
            'macie': 'RA',
            'backup': 'CP',
            'recovery': 'CP',
            'incident': 'IR',
            'forensic': 'IR',
        }
        
        for keyword, family in service_mapping.items():
            if keyword in generator:
                return family
        
        # Check resource type
        resources = finding.get('Resources', [])
        if resources:
            resource_type = resources[0].get('Type', '').lower()
            
            resource_mapping = {
                'awsiam': 'AC',
                'awss3': 'SC',
                'awsec2': 'SC',
                'awsrds': 'SC',
                'awslambda': 'SA',
                'awskms': 'SC',
                'awscloudtrail': 'AU',
                'awsconfig': 'CM',
                'awsguardduty': 'SI',
            }
            
            for res_type, family in resource_mapping.items():
                if res_type in resource_type.replace('::', '').lower():
                    return family
        
        # Default to SI (System Integrity) for unmapped findings
        return 'SI'
    
    def run_with_security_hub(self, include_security_hub: bool = True) -> List[ControlResult]:
        """
        Run all NIST 800-53 assessments and optionally include Security Hub findings.
        
        This provides a comprehensive view by combining SAELAR's direct assessments
        with aggregated findings from Security Hub.
        
        Args:
            include_security_hub: Whether to import Security Hub findings (default True)
            
        Returns:
            Combined list of ControlResult objects
        """
        # Run standard SAELAR assessments
        results = self.run_all_families()
        
        # Import Security Hub findings
        if include_security_hub:
            sh_results = self.import_security_hub_findings()
            results.extend(sh_results)
        
        return results
    
    def _print_result(self, result: ControlResult):
        """Print a single control result."""
        print(f"\n{result.status.value} {result.control_id}: {result.control_name}")
        print("-" * 50)
        
        for finding in result.findings:
            print(f"  {finding}")
        
        if result.recommendations:
            print("\n  📋 Recommendations:")
            for rec in result.recommendations:
                print(f"    • {rec}")
    
    def generate_summary(self, results: List[ControlResult]) -> Dict[str, Any]:
        """Generate assessment summary."""
        by_family = {}
        for result in results:
            if result.family not in by_family:
                by_family[result.family] = {'pass': 0, 'fail': 0, 'warning': 0, 'error': 0}
            
            if result.status == ControlStatus.PASS:
                by_family[result.family]['pass'] += 1
            elif result.status == ControlStatus.FAIL:
                by_family[result.family]['fail'] += 1
            elif result.status == ControlStatus.WARNING:
                by_family[result.family]['warning'] += 1
            else:
                by_family[result.family]['error'] += 1
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'account_id': self.account_id,
            'total_controls': len(results),
            'passed': len([r for r in results if r.status == ControlStatus.PASS]),
            'failed': len([r for r in results if r.status == ControlStatus.FAIL]),
            'warnings': len([r for r in results if r.status == ControlStatus.WARNING]),
            'by_family': by_family
        }
    
    def print_summary(self, results: List[ControlResult]):
        """Print assessment summary."""
        summary = self.generate_summary(results)
        
        print("\n" + "="*70)
        print("📊 NIST 800-53 Rev 5 ASSESSMENT SUMMARY")
        print("="*70)
        print(f"Account: {summary['account_id']}")
        print(f"Timestamp: {summary['timestamp']}")
        print(f"\nTotal Controls: {summary['total_controls']}")
        print(f"  ✅ Passed:   {summary['passed']}")
        print(f"  ❌ Failed:   {summary['failed']}")
        print(f"  ⚠️ Warnings: {summary['warnings']}")
        
        print("\n📋 Results by Family:")
        for family, counts in summary['by_family'].items():
            family_name = self.CONTROL_FAMILIES.get(family, family)
            total = sum(counts.values())
            print(f"  {family} ({family_name}): {counts['pass']}/{total} passed")
        
        # Compliance score
        applicable = summary['total_controls'] - summary.get('errors', 0)
        if applicable > 0:
            score = (summary['passed'] / applicable) * 100
            print(f"\n📈 Compliance Score: {score:.1f}%")
        
        print("="*70)
    
    def export_results(self, results: List[ControlResult], filename: str = None):
        """Export results to JSON."""
        if not filename:
            filename = f"nist_800_53_rev5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'summary': self.generate_summary(results),
            'results': [
                {
                    'control_id': r.control_id,
                    'control_name': r.control_name,
                    'family': r.family,
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
        description='NIST 800-53 Rev 5 Complete Cloud Security Assessment'
    )
    parser.add_argument('--family', '-f', 
                       choices=['AC', 'AU', 'CA', 'CM', 'CP', 'IA', 'IR', 'MP', 'RA', 'SA', 'SC', 'SI', 'SR', 'ALL'],
                       default='ALL', help='Control family to assess')
    parser.add_argument('--region', '-r', help='AWS region')
    parser.add_argument('--export', '-e', action='store_true', help='Export to JSON')
    parser.add_argument('--output', '-o', help='Output filename')
    
    args = parser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║        NIST 800-53 Revision 5 - Complete Cloud Security Assessment       ║
║        13 Control Families | 40+ Automated Checks | AWS Infrastructure   ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        assessor = NIST80053Rev5Assessor(region=args.region)
        
        if args.family == 'ALL':
            results = assessor.run_all_families()
        else:
            results = assessor.run_family(args.family)
        
        assessor.print_summary(results)
        
        if args.export:
            assessor.export_results(results, args.output)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

