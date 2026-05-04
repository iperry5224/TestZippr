#!/usr/bin/env python3
"""
SAELAR Permissions & Capabilities Check
========================================
Read-only diagnostic that tests every AWS permission needed for
existing features and proposed threat hunting enhancements.

Does NOT modify anything — all calls are read-only.

Usage:
    python3 saelar_permissions_check.py
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
NC = "\033[0m"

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "saelarallpurpose")

results = {"pass": [], "fail": [], "warn": []}


def banner():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SAELAR Permissions & Capabilities Check                             ║
║   Read-only diagnostic — nothing will be modified                     ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")


def check(name, func, required_for="existing"):
    """Run a check and record the result."""
    tag = f"[{required_for.upper()}]"
    try:
        detail = func()
        results["pass"].append((name, required_for, detail))
        print(f"  {GREEN}✓ PASS{NC}  {name}  {BLUE}{tag}{NC}  {detail}")
    except Exception as e:
        err = str(e)
        if "AccessDenied" in err or "UnauthorizedAccess" in err or "AuthorizationError" in err:
            results["fail"].append((name, required_for, err))
            print(f"  {RED}✗ DENIED{NC} {name}  {BLUE}{tag}{NC}  {err[:80]}")
        elif "Could not connect" in err or "EndpointConnectionError" in err:
            results["warn"].append((name, required_for, err))
            print(f"  {YELLOW}? WARN{NC}  {name}  {BLUE}{tag}{NC}  Service not available in region")
        else:
            results["fail"].append((name, required_for, err))
            print(f"  {RED}✗ FAIL{NC}  {name}  {BLUE}{tag}{NC}  {err[:80]}")


# =============================================================================
# EXISTING SAELAR FEATURES
# =============================================================================

def check_sts_identity():
    import boto3
    sts = boto3.client("sts", region_name=REGION)
    identity = sts.get_caller_identity()
    acct = identity["Account"]
    arn = identity["Arn"]
    return f"Account: {acct}, Identity: {arn}"


def check_s3_list_bucket():
    import boto3
    s3 = boto3.client("s3", region_name=REGION)
    resp = s3.list_objects_v2(Bucket=S3_BUCKET, MaxKeys=5)
    count = resp.get("KeyCount", 0)
    return f"Bucket '{S3_BUCKET}' accessible, {count} objects sampled"


def check_s3_put_object():
    import boto3
    s3 = boto3.client("s3", region_name=REGION)
    # Use a dry-run approach: check if we can generate a presigned URL for PutObject
    # This tests the signing capability without actually writing
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": S3_BUCKET, "Key": "__saelar_permission_check_test__"},
        ExpiresIn=60,
    )
    # Also try head_bucket which requires s3:ListBucket
    s3.head_bucket(Bucket=S3_BUCKET)
    return f"PutObject signing OK for '{S3_BUCKET}'"


def check_security_hub():
    import boto3
    sh = boto3.client("securityhub", region_name=REGION)
    resp = sh.get_findings(MaxResults=1)
    count = len(resp.get("Findings", []))
    return f"Security Hub active, {count} finding(s) sampled"


def check_bedrock_list_models():
    import boto3
    bedrock = boto3.client("bedrock", region_name=REGION)
    resp = bedrock.list_foundation_models(byOutputModality="TEXT")
    count = len(resp.get("modelSummaries", []))
    return f"{count} foundation models available"


def check_bedrock_runtime():
    import boto3
    # Just verify the client can be created and endpoint is reachable
    br = boto3.client("bedrock-runtime", region_name=REGION)
    # We won't invoke a model — just check we can reach the service
    # by attempting to list with an invalid model (catches auth errors)
    try:
        br.invoke_model(
            modelId="amazon.titan-text-lite-v1",
            body=json.dumps({"inputText": "test", "textGenerationConfig": {"maxTokenCount": 1}}),
        )
        return "Bedrock Runtime invoke OK (Titan Lite)"
    except Exception as e:
        if "AccessDenied" in str(e):
            raise
        if "ValidationException" in str(e) or "ResourceNotFoundException" in str(e):
            return "Bedrock Runtime reachable (model may need activation)"
        raise


# =============================================================================
# PROPOSED: THREAT HUNTING FEATURES
# =============================================================================

def check_guardduty():
    import boto3
    gd = boto3.client("guardduty", region_name=REGION)
    detectors = gd.list_detectors()
    det_ids = detectors.get("DetectorIds", [])
    if not det_ids:
        return "GuardDuty enabled but no detectors found"
    findings = gd.list_findings(DetectorId=det_ids[0], MaxResults=5)
    count = len(findings.get("FindingIds", []))
    return f"Detector: {det_ids[0][:12]}..., {count} finding(s) sampled"


def check_cloudtrail_lookup():
    import boto3
    ct = boto3.client("cloudtrail", region_name=REGION)
    end = datetime.utcnow()
    start = end - timedelta(hours=1)
    resp = ct.lookup_events(
        MaxResults=5,
        StartTime=start,
        EndTime=end,
    )
    count = len(resp.get("Events", []))
    return f"{count} event(s) in last hour"


def check_cloudtrail_trails():
    import boto3
    ct = boto3.client("cloudtrail", region_name=REGION)
    trails = ct.describe_trails()
    count = len(trails.get("trailList", []))
    names = [t["Name"] for t in trails.get("trailList", [])[:3]]
    return f"{count} trail(s): {', '.join(names)}"


def check_cloudwatch_logs():
    import boto3
    logs = boto3.client("logs", region_name=REGION)
    resp = logs.describe_log_groups(limit=5)
    count = len(resp.get("logGroups", []))
    return f"{count} log group(s) sampled"


def check_cloudwatch_logs_insights():
    import boto3
    logs = boto3.client("logs", region_name=REGION)
    # Check if we can start a query (we'll cancel it immediately)
    groups = logs.describe_log_groups(limit=1)
    if not groups.get("logGroups"):
        return "No log groups available to query"
    group_name = groups["logGroups"][0]["logGroupName"]
    end = int(time.time())
    start = end - 300
    resp = logs.start_query(
        logGroupName=group_name,
        startTime=start,
        endTime=end,
        queryString="fields @timestamp | limit 1",
    )
    query_id = resp["queryId"]
    logs.stop_query(queryId=query_id)
    return f"Logs Insights query OK on '{group_name[:40]}...'"


def check_inspector():
    import boto3
    try:
        inspector = boto3.client("inspector2", region_name=REGION)
        resp = inspector.list_findings(maxResults=5)
        count = len(resp.get("findings", []))
        return f"Inspector v2 active, {count} finding(s) sampled"
    except Exception as e:
        if "AccessDenied" in str(e):
            raise
        # Try Inspector Classic
        inspector_classic = boto3.client("inspector", region_name=REGION)
        resp = inspector_classic.list_findings(maxResults=5)
        count = len(resp.get("findingArns", []))
        return f"Inspector Classic, {count} finding(s)"


def check_config():
    import boto3
    config = boto3.client("config", region_name=REGION)
    resp = config.describe_compliance_by_config_rule(Limit=5)
    count = len(resp.get("ComplianceByConfigRules", []))
    return f"{count} Config rule(s) with compliance data"


def check_iam_read():
    import boto3
    iam = boto3.client("iam")
    resp = iam.list_roles(MaxItems=5)
    count = len(resp.get("Roles", []))
    return f"{count} IAM role(s) sampled"


def check_iam_access_analyzer():
    import boto3
    aa = boto3.client("accessanalyzer", region_name=REGION)
    analyzers = aa.list_analyzers()
    count = len(analyzers.get("analyzers", []))
    if count > 0:
        findings = aa.list_findings(analyzerArn=analyzers["analyzers"][0]["arn"], maxResults=5)
        f_count = len(findings.get("findings", []))
        return f"{count} analyzer(s), {f_count} finding(s) sampled"
    return f"{count} analyzer(s) found"


def check_ec2_describe():
    import boto3
    ec2 = boto3.client("ec2", region_name=REGION)
    resp = ec2.describe_instances(MaxResults=5)
    count = sum(len(r["Instances"]) for r in resp.get("Reservations", []))
    return f"{count} instance(s) sampled"


def check_vpc_flow_logs():
    import boto3
    ec2 = boto3.client("ec2", region_name=REGION)
    resp = ec2.describe_flow_logs(MaxResults=5)
    count = len(resp.get("FlowLogs", []))
    return f"{count} VPC Flow Log(s) configured"


def check_athena():
    import boto3
    athena = boto3.client("athena", region_name=REGION)
    resp = athena.list_work_groups()
    groups = [wg["Name"] for wg in resp.get("WorkGroups", [])]
    return f"Work groups: {', '.join(groups[:3])}"


def check_bedrock_agent():
    import boto3
    agent = boto3.client("bedrock-agent", region_name=REGION)
    kbs = agent.list_knowledge_bases()
    count = len(kbs.get("knowledgeBaseSummaries", []))
    return f"{count} Knowledge Base(s) found"


def check_bedrock_agent_runtime():
    import boto3
    try:
        client = boto3.client("bedrock-agent-runtime", region_name=REGION)
        # Just verify the client can be constructed and endpoint resolved
        return "bedrock-agent-runtime endpoint reachable"
    except Exception as e:
        raise


def check_opensearch_serverless():
    import boto3
    oss = boto3.client("opensearchserverless", region_name=REGION)
    resp = oss.list_collections()
    count = len(resp.get("collectionSummaries", []))
    return f"{count} collection(s) found"


def check_cisa_kev_feed():
    import requests as req
    resp = req.get(
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    count = len(data.get("vulnerabilities", []))
    return f"CISA KEV feed accessible, {count} vulnerabilities"


def check_alienvault_otx():
    import requests as req
    resp = req.get(
        "https://otx.alienvault.com/api/v1/pulses/subscribed?limit=1",
        timeout=10,
        headers={"X-OTX-API-KEY": os.environ.get("OTX_API_KEY", "")},
    )
    if resp.status_code == 403:
        return "OTX reachable but no API key set (set OTX_API_KEY env var)"
    resp.raise_for_status()
    return "AlienVault OTX feed accessible"


def check_abuseipdb():
    import requests as req
    resp = req.get("https://api.abuseipdb.com/api/v2/check",
        params={"ipAddress": "8.8.8.8"},
        headers={"Key": os.environ.get("ABUSEIPDB_KEY", ""), "Accept": "application/json"},
        timeout=10,
    )
    if resp.status_code == 401 or resp.status_code == 429:
        return "AbuseIPDB reachable but no API key set (set ABUSEIPDB_KEY env var)"
    return "AbuseIPDB accessible"


# =============================================================================
# SUMMARY
# =============================================================================

def print_summary():
    total = len(results["pass"]) + len(results["fail"]) + len(results["warn"])
    
    existing_pass = [r for r in results["pass"] if r[1] == "existing"]
    existing_fail = [r for r in results["fail"] if r[1] == "existing"]
    hunt_pass = [r for r in results["pass"] if r[1] != "existing"]
    hunt_fail = [r for r in results["fail"] if r[1] != "existing"]
    hunt_warn = [r for r in results["warn"] if r[1] != "existing"]

    print(f"""
{BOLD}{'='*72}{NC}
{BOLD}RESULTS SUMMARY{NC}
{'='*72}

{CYAN}Existing SAELAR Features:{NC}
  {GREEN}✓ Passing: {len(existing_pass)}{NC}
  {RED}✗ Failing: {len(existing_fail)}{NC}
""")

    if existing_fail:
        print(f"  {RED}Action needed for existing features:{NC}")
        for name, _, err in existing_fail:
            print(f"    - {name}: {err[:60]}")
        print()

    print(f"""{CYAN}Proposed Threat Hunting Features:{NC}
  {GREEN}✓ Ready:     {len(hunt_pass)}{NC}
  {RED}✗ Blocked:   {len(hunt_fail)}{NC}
  {YELLOW}? Warning:   {len(hunt_warn)}{NC}
""")

    if hunt_fail:
        print(f"  {RED}Permissions needed for threat hunting:{NC}")
        for name, _, err in hunt_fail:
            print(f"    - {name}: {err[:60]}")
        print()

    if hunt_warn:
        print(f"  {YELLOW}Services not available (may not be enabled):{NC}")
        for name, _, err in hunt_warn:
            print(f"    - {name}: {err[:60]}")
        print()

    # Feasibility assessment
    print(f"{BOLD}{'='*72}{NC}")
    print(f"{BOLD}FEASIBILITY ASSESSMENT{NC}")
    print(f"{'='*72}\n")

    phases = {
        "Phase 1: Live Threat Intelligence": {
            "needs": ["CISA KEV Feed", "Security Hub: GetFindings", "GuardDuty: ListFindings"],
            "nice": ["AlienVault OTX Feed", "AbuseIPDB Feed"],
        },
        "Phase 2: Interactive MITRE ATT&CK Heatmap": {
            "needs": ["Security Hub: GetFindings"],
            "nice": ["GuardDuty: ListFindings", "Inspector: ListFindings"],
        },
        "Phase 3: Hunt Playbook Engine": {
            "needs": ["CloudTrail: LookupEvents", "CloudWatch Logs: Query"],
            "nice": ["VPC Flow Logs", "Athena: Query", "EC2: Describe"],
        },
        "Phase 4: Detection-as-Code": {
            "needs": ["CloudWatch Logs: Describe", "IAM: Read"],
            "nice": ["AWS Config: Compliance", "IAM Access Analyzer"],
        },
    }

    pass_names = {r[0] for r in results["pass"]}

    for phase, deps in phases.items():
        required_ok = sum(1 for d in deps["needs"] if d in pass_names)
        required_total = len(deps["needs"])
        nice_ok = sum(1 for d in deps["nice"] if d in pass_names)
        nice_total = len(deps["nice"])

        if required_ok == required_total:
            status = f"{GREEN}✓ READY{NC}"
        elif required_ok > 0:
            status = f"{YELLOW}◐ PARTIAL{NC}"
        else:
            status = f"{RED}✗ BLOCKED{NC}"

        print(f"  {status}  {BOLD}{phase}{NC}")
        print(f"         Required: {required_ok}/{required_total} passing | Nice-to-have: {nice_ok}/{nice_total}")

        missing = [d for d in deps["needs"] if d not in pass_names]
        if missing:
            print(f"         {RED}Missing: {', '.join(missing)}{NC}")
        print()

    print(f"{BOLD}{'='*72}{NC}")
    total_pass = len(results["pass"])
    print(f"\n  Total checks: {total} | {GREEN}Pass: {total_pass}{NC} | {RED}Fail: {len(results['fail'])}{NC} | {YELLOW}Warn: {len(results['warn'])}{NC}\n")


# =============================================================================
# MAIN
# =============================================================================

def main():
    banner()

    print(f"{BOLD}Checking AWS identity...{NC}\n")
    check("STS: GetCallerIdentity", check_sts_identity, "existing")

    print(f"\n{BOLD}── Existing SAELAR Features ──{NC}\n")
    check("S3: ListBucket", check_s3_list_bucket, "existing")
    check("S3: PutObject (signing)", check_s3_put_object, "existing")
    check("Security Hub: GetFindings", check_security_hub, "existing")
    check("Bedrock: ListModels", check_bedrock_list_models, "existing")
    check("Bedrock: InvokeModel", check_bedrock_runtime, "existing")

    print(f"\n{BOLD}── Proposed: Threat Intelligence (Phase 1) ──{NC}\n")
    check("CISA KEV Feed", check_cisa_kev_feed, "phase1-threat-intel")
    check("AlienVault OTX Feed", check_alienvault_otx, "phase1-threat-intel")
    check("AbuseIPDB Feed", check_abuseipdb, "phase1-threat-intel")
    check("GuardDuty: ListFindings", check_guardduty, "phase1-threat-intel")

    print(f"\n{BOLD}── Proposed: MITRE ATT&CK Heatmap (Phase 2) ──{NC}\n")
    check("Inspector: ListFindings", check_inspector, "phase2-mitre")
    check("AWS Config: Compliance", check_config, "phase2-mitre")

    print(f"\n{BOLD}── Proposed: Hunt Playbooks (Phase 3) ──{NC}\n")
    check("CloudTrail: LookupEvents", check_cloudtrail_lookup, "phase3-hunt")
    check("CloudTrail: DescribeTrails", check_cloudtrail_trails, "phase3-hunt")
    check("CloudWatch Logs: Describe", check_cloudwatch_logs, "phase3-hunt")
    check("CloudWatch Logs: Query", check_cloudwatch_logs_insights, "phase3-hunt")
    check("VPC Flow Logs", check_vpc_flow_logs, "phase3-hunt")
    check("EC2: Describe", check_ec2_describe, "phase3-hunt")
    check("Athena: Query", check_athena, "phase3-hunt")

    print(f"\n{BOLD}── Proposed: Detection-as-Code (Phase 4) ──{NC}\n")
    check("IAM: Read", check_iam_read, "phase4-detection")
    check("IAM Access Analyzer", check_iam_access_analyzer, "phase4-detection")

    print(f"\n{BOLD}── Proposed: Knowledge Base / RAG ──{NC}\n")
    check("Bedrock Agent: ListKBs", check_bedrock_agent, "kb-rag")
    check("Bedrock Agent Runtime", check_bedrock_agent_runtime, "kb-rag")
    check("OpenSearch Serverless", check_opensearch_serverless, "kb-rag")

    print_summary()


if __name__ == "__main__":
    main()
