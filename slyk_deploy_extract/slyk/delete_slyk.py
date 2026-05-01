#!/usr/bin/env python3
"""
Tear down SLyK-53 resources created by deploy_slyk.py (idempotent).
Does NOT delete the S3 bucket; removes slyk/slyk_config.json if the bucket is set.
"""
import os
import sys
from typing import Optional

import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

# Resource naming - set SLYK_VARIANT env var to match deployment (e.g., "new" for New_SLyK-53)
VARIANT = os.environ.get("SLYK_VARIANT", "")
VARIANT_SUFFIX = f"-{VARIANT}" if VARIANT else ""
VARIANT_PREFIX = f"{VARIANT.capitalize()}_" if VARIANT else ""

AGENT_NAME = f"{VARIANT_PREFIX}SLyK-53-Security-Assistant"
LAMBDA_NAMES = (f"slyk{VARIANT_SUFFIX}-assess", f"slyk{VARIANT_SUFFIX}-remediate", f"slyk{VARIANT_SUFFIX}-harden")
LAMBDA_ROLE = f"{VARIANT_PREFIX}SLyK-Lambda-Role"
AGENT_ROLE = f"{VARIANT_PREFIX}SLyK-Agent-Role"
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "slyk-grcp-016230494923")
CONFIG_KEY = "slyk/slyk_config.json"
SLYK_EXPECT = os.environ.get("SLYK_EXPECT_ACCOUNT_ID")


def _fail(msg: str) -> None:
    print(f"  [ERR] {msg}", file=sys.stderr)
    sys.exit(1)


def _find_agent_id(bedrock) -> Optional[str]:
    token = None
    while True:
        kw = {"maxResults": 50}
        if token:
            kw["nextToken"] = token
        r = bedrock.list_agents(**kw)
        for a in r.get("agentSummaries", []):
            if a.get("agentName") == AGENT_NAME:
                return a.get("agentId")
        token = r.get("nextToken")
        if not token:
            return None


def _delete_draft_action_groups(bedrock, agent_id: str) -> None:
    token = None
    while True:
        kw = {"agentId": agent_id, "agentVersion": "DRAFT"}
        if token:
            kw["nextToken"] = token
        r = bedrock.list_agent_action_groups(**kw)
        for s in r.get("actionGroupSummaries", []):
            aid = s.get("actionGroupId")
            if not aid:
                continue
            try:
                bedrock.delete_agent_action_group(
                    agentId=agent_id,
                    agentVersion="DRAFT",
                    actionGroupId=aid,
                )
                print(f"  ✓ Removed action group: {s.get('actionGroupName', aid)}")
            except ClientError as e:
                if e.response["Error"]["Code"] not in ("ResourceNotFoundException",):
                    print(f"  ! delete action group {aid}: {e}")
        token = r.get("nextToken")
        if not token:
            break


def _delete_bedrock_agent(bedrock, agent_id: str) -> None:
    # Clear DRAFT action groups (required before some deletes)
    _delete_draft_action_groups(bedrock, agent_id)
    # All aliases first
    token = None
    while True:
        kw = {"agentId": agent_id, "maxResults": 50}
        if token:
            kw["nextToken"] = token
        r = bedrock.list_agent_aliases(**kw)
        for a in r.get("agentAliasSummaries", []):
            aid, name = a.get("agentAliasId"), a.get("agentAliasName")
            if not aid:
                continue
            # API can return placeholder TSTALIASID (not deletable / not real)
            if aid == "TSTALIASID":
                continue
            try:
                bedrock.delete_agent_alias(agentId=agent_id, agentAliasId=aid)
                print(f"  [ok] Deleted agent alias: {name} ({aid})")
            except ClientError as e:
                if e.response["Error"]["Code"] not in (
                    "ResourceNotFoundException",
                ):
                    print(f"  ! delete alias {aid}: {e}")
        token = r.get("nextToken")
        if not token:
            break

    # All prepared versions (not DRAFT) - may be required before delete_agent
    token = None
    while True:
        kw = {"agentId": agent_id, "maxResults": 50}
        if token:
            kw["nextToken"] = token
        r = bedrock.list_agent_versions(**kw)
        for v in r.get("agentVersionSummaries", []):
            ver = v.get("agentVersion")
            status = (v.get("agentStatus") or "").upper()
            if ver in (None, "DRAFT"):
                continue
            try:
                bedrock.delete_agent_version(agentId=agent_id, agentVersion=ver, skipResourceInUseCheck=True)
                print(f"  [ok] Deleted agent version: {ver} ({status})")
            except ClientError as e:
                print(f"  ! delete version {ver}: {e}")
        token = r.get("nextToken")
        if not token:
            break

    try:
        bedrock.delete_agent(
            agentId=agent_id,
            skipResourceInUseCheck=True,
        )
        print(f"  [ok] Deleted Bedrock agent {agent_id}")
    except ClientError as e:
        print(f"  ! delete_agent: {e}")


def _delete_lambdas(lam) -> None:
    for name in LAMBDA_NAMES:
        try:
            lam.delete_function(FunctionName=name)
            print(f"  [ok] Deleted Lambda: {name}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                print(f"  (skip) Lambda not found: {name}")
            else:
                print(f"  ! delete_function {name}: {e}")


def _iam_strip_and_delete(iam, role_name: str) -> None:
    try:
        iam.get_role(RoleName=role_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            print(f"  (skip) IAM role not found: {role_name}")
            return
        raise
    for ap in iam.list_attached_role_policies(RoleName=role_name).get("AttachedPolicies", []):
        try:
            iam.detach_role_policy(
                RoleName=role_name, PolicyArn=ap["PolicyArn"]
            )
            print(f"  [ok] Detached {ap['PolicyName']}")
        except ClientError as e:
            print(f"  ! detach {ap['PolicyName']}: {e}")
    for inline in iam.list_role_policies(RoleName=role_name).get("PolicyNames", []):
        try:
            iam.delete_role_policy(RoleName=role_name, PolicyName=inline)
            print(f"  [ok] Removed inline policy {inline}")
        except ClientError as e:
            print(f"  ! delete inline {inline}: {e}")
    try:
        iam.delete_role(RoleName=role_name)
        print(f"  [ok] Deleted IAM role: {role_name}")
    except ClientError as e:
        print(f"  ! delete_role {role_name}: {e}")


def main() -> None:
    sts = boto3.client("sts", region_name=REGION)
    acct = sts.get_caller_identity()["Account"]
    if SLYK_EXPECT and acct != SLYK_EXPECT:
        _fail(
            f"Account mismatch: caller {acct} != SLYK_EXPECT_ACCOUNT_ID {SLYK_EXPECT}"
        )
    print(f"SLyK teardown - account {acct} region {REGION}\n")

    bedrock = boto3.client("bedrock-agent", region_name=REGION)
    agent_id = _find_agent_id(bedrock)
    if agent_id:
        print(f"Bedrock agent {AGENT_NAME}  id={agent_id}")
        _delete_bedrock_agent(bedrock, agent_id)
    else:
        print("No matching Bedrock agent (skipped).")

    print("\nLambda functions")
    _delete_lambdas(boto3.client("lambda", region_name=REGION))

    print("\nIAM roles")
    iam = boto3.client("iam")
    _iam_strip_and_delete(iam, LAMBDA_ROLE)
    _iam_strip_and_delete(iam, AGENT_ROLE)

    if S3_BUCKET:
        s3 = boto3.client("s3", region_name=REGION)
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=CONFIG_KEY)
            print(f"\n  [ok] Removed s3://{S3_BUCKET}/{CONFIG_KEY}")
        except ClientError as e:
            print(f"\n  ! S3 delete {CONFIG_KEY}: {e}")

    local_cfg = os.path.join(os.path.dirname(__file__), "slyk_config.json")
    if os.path.isfile(local_cfg):
        try:
            os.remove(local_cfg)
            print(f"  [ok] Removed local {local_cfg}")
        except OSError as e:
            print(f"  ! remove local config: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
