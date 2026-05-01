#!/usr/bin/env python3
"""
SLyK-53 Knowledge Base Deployment
==================================
Creates a Bedrock Knowledge Base for RAG over compliance documents.

This enables SLyK to answer questions about:
  - Previous assessment results
  - System Security Plans (SSPs)
  - POA&Ms
  - NIST 800-53 control documentation
  - Organization-specific policies

Usage:
    python3 deploy_knowledge_base.py
"""

import json
import os
import sys
import time
import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
ACCOUNT_ID = None
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "saelarallpurpose")

# Resource naming - set SLYK_VARIANT env var to customize (e.g., "new" for New_SLyK-53)
VARIANT = os.environ.get("SLYK_VARIANT", "")
VARIANT_SUFFIX = f"-{VARIANT}" if VARIANT else ""
VARIANT_PREFIX = f"{VARIANT.capitalize()}_" if VARIANT else ""

KB_NAME = f"{VARIANT_PREFIX}SLyK-Knowledge-Base"
KB_DESCRIPTION = f"{VARIANT_PREFIX}SLyK-53 compliance documentation knowledge base"
DATA_SOURCE_NAME = f"slyk{VARIANT_SUFFIX}-compliance-docs"
COLLECTION_NAME = f"slyk{VARIANT_SUFFIX}-kb-collection"

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
NC = "\033[0m"

config = {}


def log(msg):
    print(f"{BLUE}[slyk-kb]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}  ✓{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}  !{NC} {msg}")


def fail(msg):
    print(f"{RED}  ✗{NC} {msg}")


def get_account_id():
    global ACCOUNT_ID
    sts = boto3.client("sts", region_name=REGION)
    ACCOUNT_ID = sts.get_caller_identity()["Account"]
    return ACCOUNT_ID


def banner():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SLyK-53 Knowledge Base Deployment                                    ║
║   RAG for Compliance Documentation                                     ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")


# =========================================================================
# STEP 1: Create IAM Role for Knowledge Base
# =========================================================================
def create_kb_role():
    log("Step 1: Creating Knowledge Base IAM role...")
    iam = boto3.client("iam")

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {"aws:SourceAccount": ACCOUNT_ID},
                "ArnLike": {
                    "aws:SourceArn": f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:knowledge-base/*"
                }
            }
        }]
    }

    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": [
                    f"arn:aws:s3:::{S3_BUCKET}",
                    f"arn:aws:s3:::{S3_BUCKET}/slyk/knowledge-base/*",
                    f"arn:aws:s3:::{S3_BUCKET}/slyk/documents/*",
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "aoss:APIAccessAll",
                ],
                "Resource": [
                    f"arn:aws:aoss:{REGION}:{ACCOUNT_ID}:collection/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                ],
                "Resource": [
                    f"arn:aws:bedrock:{REGION}::foundation-model/*"
                ]
            }
        ]
    }

    try:
        role = iam.create_role(
            RoleName="SLyK-KnowledgeBase-Role",
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="SLyK-53 Knowledge Base execution role",
        )
        config["kb_role_arn"] = role["Role"]["Arn"]
        ok(f"Created role: SLyK-KnowledgeBase-Role")

        iam.put_role_policy(
            RoleName="SLyK-KnowledgeBase-Role",
            PolicyName="SLyK-KB-Permissions",
            PolicyDocument=json.dumps(permissions_policy),
        )
        ok("Attached permissions policy")

        # Wait for role to propagate
        time.sleep(10)

    except ClientError as e:
        if "EntityAlreadyExists" in str(e):
            config["kb_role_arn"] = f"arn:aws:iam::{ACCOUNT_ID}:role/SLyK-KnowledgeBase-Role"
            warn("Role already exists — reusing")
        else:
            fail(f"Could not create role: {e}")
            return False

    return True


# =========================================================================
# STEP 2: Create OpenSearch Serverless Collection
# =========================================================================
def create_opensearch_collection():
    log("Step 2: Creating OpenSearch Serverless collection...")
    aoss = boto3.client("opensearchserverless", region_name=REGION)

    # Create encryption policy
    try:
        aoss.create_security_policy(
            name=f"slyk-kb-encryption",
            type="encryption",
            policy=json.dumps({
                "Rules": [{"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"]}],
                "AWSOwnedKey": True
            }),
        )
        ok("Created encryption policy")
    except ClientError as e:
        if "ConflictException" in str(e):
            warn("Encryption policy already exists")
        else:
            warn(f"Could not create encryption policy: {e}")

    # Create network policy
    try:
        aoss.create_security_policy(
            name=f"slyk-kb-network",
            type="network",
            policy=json.dumps([{
                "Rules": [{"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"]}],
                "AllowFromPublic": True,
            }]),
        )
        ok("Created network policy")
    except ClientError as e:
        if "ConflictException" in str(e):
            warn("Network policy already exists")
        else:
            warn(f"Could not create network policy: {e}")

    # Create data access policy
    try:
        aoss.create_access_policy(
            name=f"slyk-kb-access",
            type="data",
            policy=json.dumps([{
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{COLLECTION_NAME}"],
                        "Permission": ["aoss:*"],
                    },
                    {
                        "ResourceType": "index",
                        "Resource": [f"index/{COLLECTION_NAME}/*"],
                        "Permission": ["aoss:*"],
                    }
                ],
                "Principal": [
                    config.get("kb_role_arn", f"arn:aws:iam::{ACCOUNT_ID}:role/SLyK-KnowledgeBase-Role"),
                    f"arn:aws:iam::{ACCOUNT_ID}:root",
                ],
            }]),
        )
        ok("Created data access policy")
    except ClientError as e:
        if "ConflictException" in str(e):
            warn("Data access policy already exists")
        else:
            warn(f"Could not create data access policy: {e}")

    # Create collection
    try:
        collection = aoss.create_collection(
            name=COLLECTION_NAME,
            type="VECTORSEARCH",
            description="SLyK-53 Knowledge Base vector store",
        )
        config["collection_id"] = collection["createCollectionDetail"]["id"]
        config["collection_arn"] = collection["createCollectionDetail"]["arn"]
        ok(f"Created collection: {COLLECTION_NAME}")

        # Wait for collection to be active
        log("  Waiting for collection to become active (this may take a few minutes)...")
        while True:
            status = aoss.batch_get_collection(ids=[config["collection_id"]])
            state = status["collectionDetails"][0]["status"]
            if state == "ACTIVE":
                config["collection_endpoint"] = status["collectionDetails"][0]["collectionEndpoint"]
                ok(f"Collection active: {config['collection_endpoint']}")
                break
            elif state == "FAILED":
                fail("Collection creation failed")
                return False
            time.sleep(30)

    except ClientError as e:
        if "ConflictException" in str(e):
            # Get existing collection
            collections = aoss.list_collections()
            for c in collections.get("collectionSummaries", []):
                if c["name"] == COLLECTION_NAME:
                    config["collection_id"] = c["id"]
                    config["collection_arn"] = c["arn"]
                    # Get endpoint
                    details = aoss.batch_get_collection(ids=[c["id"]])
                    config["collection_endpoint"] = details["collectionDetails"][0].get("collectionEndpoint", "")
                    break
            warn(f"Collection already exists: {config.get('collection_id', 'unknown')}")
        else:
            fail(f"Could not create collection: {e}")
            return False

    return True


# =========================================================================
# STEP 3: Create Knowledge Base
# =========================================================================
def create_knowledge_base():
    log("Step 3: Creating Bedrock Knowledge Base...")
    bedrock = boto3.client("bedrock-agent", region_name=REGION)

    # Check if KB already exists
    try:
        kbs = bedrock.list_knowledge_bases(maxResults=100)
        for kb in kbs.get("knowledgeBaseSummaries", []):
            if kb["name"] == KB_NAME:
                config["kb_id"] = kb["knowledgeBaseId"]
                warn(f"Knowledge Base already exists: {config['kb_id']}")
                return True
    except ClientError:
        pass

    try:
        kb = bedrock.create_knowledge_base(
            name=KB_NAME,
            description=KB_DESCRIPTION,
            roleArn=config.get("kb_role_arn", f"arn:aws:iam::{ACCOUNT_ID}:role/SLyK-KnowledgeBase-Role"),
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": f"arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v2:0",
                }
            },
            storageConfiguration={
                "type": "OPENSEARCH_SERVERLESS",
                "opensearchServerlessConfiguration": {
                    "collectionArn": config.get("collection_arn", ""),
                    "vectorIndexName": "slyk-kb-index",
                    "fieldMapping": {
                        "vectorField": "embedding",
                        "textField": "text",
                        "metadataField": "metadata",
                    }
                }
            },
        )
        config["kb_id"] = kb["knowledgeBase"]["knowledgeBaseId"]
        ok(f"Created Knowledge Base: {config['kb_id']}")

        # Wait for KB to be active
        while True:
            status = bedrock.get_knowledge_base(knowledgeBaseId=config["kb_id"])
            state = status["knowledgeBase"]["status"]
            if state == "ACTIVE":
                ok("Knowledge Base is active")
                break
            elif state == "FAILED":
                fail("Knowledge Base creation failed")
                return False
            time.sleep(10)

    except ClientError as e:
        fail(f"Could not create Knowledge Base: {e}")
        return False

    return True


# =========================================================================
# STEP 4: Create Data Source
# =========================================================================
def create_data_source():
    log("Step 4: Creating data source...")
    bedrock = boto3.client("bedrock-agent", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)

    # Ensure the knowledge base folder exists in S3
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key="slyk/knowledge-base/.keep",
            Body=b"",
        )
        ok(f"Created S3 folder: s3://{S3_BUCKET}/slyk/knowledge-base/")
    except ClientError as e:
        warn(f"Could not create S3 folder: {e}")

    # Upload sample NIST documentation
    sample_doc = """# NIST 800-53 Rev 5 Quick Reference

## Access Control (AC) Family

### AC-2: Account Management
- Manage system accounts including establishing, activating, modifying, reviewing, disabling, and removing accounts
- Require MFA for all privileged accounts
- Review accounts at least annually

### AC-6: Least Privilege
- Employ the principle of least privilege
- Authorize access only for functions that users need to perform their duties
- Review privileges periodically

## Audit and Accountability (AU) Family

### AU-2: Event Logging
- Identify events that need to be logged
- Coordinate logging requirements with other organizational entities
- Provide rationale for why the events are deemed adequate

## Identification and Authentication (IA) Family

### IA-2: Identification and Authentication
- Uniquely identify and authenticate organizational users
- Implement multi-factor authentication for network access to privileged accounts
- Implement multi-factor authentication for network access to non-privileged accounts

## System and Communications Protection (SC) Family

### SC-7: Boundary Protection
- Monitor and control communications at external boundaries
- Implement subnetworks for publicly accessible system components
- Connect to external networks only through managed interfaces

### SC-28: Protection of Information at Rest
- Protect the confidentiality and integrity of information at rest
- Employ cryptographic mechanisms to prevent unauthorized disclosure and modification

## System and Information Integrity (SI) Family

### SI-4: System Monitoring
- Monitor the system to detect attacks and indicators of potential attacks
- Identify unauthorized use of the system
- Deploy monitoring devices strategically within the system
"""

    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key="slyk/knowledge-base/nist-800-53-quick-reference.md",
            Body=sample_doc.encode("utf-8"),
            ContentType="text/markdown",
        )
        ok("Uploaded sample NIST documentation")
    except ClientError as e:
        warn(f"Could not upload sample doc: {e}")

    # Create data source
    try:
        ds = bedrock.create_data_source(
            knowledgeBaseId=config["kb_id"],
            name=DATA_SOURCE_NAME,
            description="Compliance documents from S3",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": f"arn:aws:s3:::{S3_BUCKET}",
                    "inclusionPrefixes": ["slyk/knowledge-base/", "slyk/documents/"],
                }
            },
            vectorIngestionConfiguration={
                "chunkingConfiguration": {
                    "chunkingStrategy": "FIXED_SIZE",
                    "fixedSizeChunkingConfiguration": {
                        "maxTokens": 512,
                        "overlapPercentage": 20,
                    }
                }
            },
        )
        config["data_source_id"] = ds["dataSource"]["dataSourceId"]
        ok(f"Created data source: {config['data_source_id']}")

    except ClientError as e:
        if "ConflictException" in str(e):
            # Get existing data source
            sources = bedrock.list_data_sources(knowledgeBaseId=config["kb_id"])
            for s in sources.get("dataSourceSummaries", []):
                if s["name"] == DATA_SOURCE_NAME:
                    config["data_source_id"] = s["dataSourceId"]
                    break
            warn(f"Data source already exists: {config.get('data_source_id', 'unknown')}")
        else:
            fail(f"Could not create data source: {e}")
            return False

    return True


# =========================================================================
# STEP 5: Start Ingestion
# =========================================================================
def start_ingestion():
    log("Step 5: Starting document ingestion...")
    bedrock = boto3.client("bedrock-agent", region_name=REGION)

    try:
        job = bedrock.start_ingestion_job(
            knowledgeBaseId=config["kb_id"],
            dataSourceId=config["data_source_id"],
        )
        job_id = job["ingestionJob"]["ingestionJobId"]
        ok(f"Started ingestion job: {job_id}")

        # Wait for ingestion to complete
        log("  Waiting for ingestion to complete...")
        while True:
            status = bedrock.get_ingestion_job(
                knowledgeBaseId=config["kb_id"],
                dataSourceId=config["data_source_id"],
                ingestionJobId=job_id,
            )
            state = status["ingestionJob"]["status"]
            if state == "COMPLETE":
                stats = status["ingestionJob"].get("statistics", {})
                ok(f"Ingestion complete: {stats.get('numberOfDocumentsScanned', 0)} docs scanned, "
                   f"{stats.get('numberOfDocumentsIndexed', 0)} indexed")
                break
            elif state == "FAILED":
                fail("Ingestion failed")
                return False
            time.sleep(15)

    except ClientError as e:
        warn(f"Could not start ingestion: {e}")
        return False

    return True


# =========================================================================
# STEP 6: Associate with Agent
# =========================================================================
def associate_with_agent():
    log("Step 6: Associating Knowledge Base with SLyK agent...")
    bedrock = boto3.client("bedrock-agent", region_name=REGION)

    # Load existing config to get agent ID
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slyk_config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            existing = json.load(f)
            config["agent_id"] = existing.get("agent_id", "")

    if not config.get("agent_id"):
        warn("No agent ID found — run deploy_slyk.py first")
        warn("You can manually associate the KB in the Bedrock console")
        return False

    try:
        bedrock.associate_agent_knowledge_base(
            agentId=config["agent_id"],
            agentVersion="DRAFT",
            knowledgeBaseId=config["kb_id"],
            description="SLyK compliance documentation for RAG queries",
            knowledgeBaseState="ENABLED",
        )
        ok(f"Associated KB with agent {config['agent_id']}")

        # Prepare agent to apply changes
        bedrock.prepare_agent(agentId=config["agent_id"])
        ok("Agent prepared with Knowledge Base")

    except ClientError as e:
        if "ConflictException" in str(e):
            warn("Knowledge Base already associated with agent")
        else:
            warn(f"Could not associate KB with agent: {e}")
            return False

    return True


# =========================================================================
# STEP 7: Save Config
# =========================================================================
def save_config():
    log("Step 7: Saving configuration...")

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slyk_config.json")
    existing = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            existing = json.load(f)

    full_config = {**existing, **config}
    full_config["kb_enabled"] = True

    with open(config_path, "w") as f:
        json.dump(full_config, f, indent=2)
    ok(f"Config saved to {config_path}")


# =========================================================================
# SUMMARY
# =========================================================================
def print_summary():
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║           SLyK-53 KNOWLEDGE BASE DEPLOYMENT COMPLETE!                  ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}Resources Created:{NC}

    Knowledge Base:
      KB ID:          {config.get('kb_id', 'N/A')}
      Data Source:    {config.get('data_source_id', 'N/A')}

    OpenSearch Serverless:
      Collection:     {config.get('collection_id', 'N/A')}
      Endpoint:       {config.get('collection_endpoint', 'N/A')}

    S3 Document Location:
      s3://{S3_BUCKET}/slyk/knowledge-base/
      s3://{S3_BUCKET}/slyk/documents/

  {CYAN}How to Add Documents:{NC}
    Upload documents to the S3 folders above, then run:
    
    aws bedrock-agent start-ingestion-job \\
        --knowledge-base-id {config.get('kb_id', 'KB_ID')} \\
        --data-source-id {config.get('data_source_id', 'DS_ID')}

  {CYAN}Test in Chat:{NC}
    "What does NIST 800-53 say about MFA?"
    "Summarize our latest assessment results"
    "What's in our System Security Plan?"
""")


# =========================================================================
# MAIN
# =========================================================================
def main():
    banner()

    try:
        acct = get_account_id()
        ok(f"AWS Account: {acct}")
        ok(f"Region: {REGION}")
    except Exception as e:
        fail(f"Cannot access AWS: {e}")
        sys.exit(1)

    print()
    if not create_kb_role():
        sys.exit(1)
    print()
    if not create_opensearch_collection():
        sys.exit(1)
    print()
    if not create_knowledge_base():
        sys.exit(1)
    print()
    if not create_data_source():
        sys.exit(1)
    print()
    start_ingestion()
    print()
    associate_with_agent()
    print()
    save_config()
    print_summary()


if __name__ == "__main__":
    main()
