#!/usr/bin/env python3
"""
SAELAR Knowledge Base Setup
============================
Creates an Amazon Bedrock Knowledge Base backed by the SAELAR S3 bucket.
This enables Chad (AI) to do RAG (Retrieval-Augmented Generation) over
your stored compliance documents (SSPs, POA&Ms, RARs, assessments).

Usage:
    python3 setup_knowledge_base.py

Prerequisites:
    - AWS credentials with permissions for Bedrock, S3, IAM, and OpenSearch Serverless
    - The saelarallpurpose S3 bucket must exist
    - Bedrock model access enabled in the target region

The script will:
    1. Create an IAM role for the Knowledge Base
    2. Create an OpenSearch Serverless collection (vector store)
    3. Create the Bedrock Knowledge Base pointing at your S3 bucket
    4. Create a data source and trigger initial sync
    5. Save the Knowledge Base ID to .saelar_kb_config.json
"""

import json
import os
import sys
import time
import boto3
from botocore.exceptions import ClientError

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
NC = "\033[0m"

S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "saelarallpurpose")
KB_NAME = "saelar-compliance-kb"
KB_DESCRIPTION = "SAELAR compliance knowledge base - SSPs, POA&Ms, RARs, and assessment reports"
COLLECTION_NAME = "saelar-vectors"
ROLE_NAME = "SaelarKnowledgeBaseRole"
EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".saelar_kb_config.json")


def banner():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SAELAR Knowledge Base Setup                                         ║
║   Enabling RAG for Chad (AI) via Amazon Bedrock                       ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")


def get_account_id():
    sts = boto3.client("sts", region_name=REGION)
    return sts.get_caller_identity()["Account"]


def create_kb_role(account_id):
    """Create IAM role for Bedrock Knowledge Base with S3 and OpenSearch access."""
    print(f"{BLUE}[1/5]{NC} Creating IAM role: {ROLE_NAME}...")
    iam = boto3.client("iam")

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {"aws:SourceAccount": account_id},
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock:{REGION}:{account_id}:knowledge-base/*"
                    },
                },
            }
        ],
    }

    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "S3Access",
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": [
                    f"arn:aws:s3:::{S3_BUCKET}",
                    f"arn:aws:s3:::{S3_BUCKET}/*",
                ],
            },
            {
                "Sid": "BedrockEmbedding",
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": [
                    f"arn:aws:bedrock:{REGION}::foundation-model/{EMBEDDING_MODEL}"
                ],
            },
            {
                "Sid": "OpenSearchServerless",
                "Effect": "Allow",
                "Action": ["aoss:APIAccessAll"],
                "Resource": [
                    f"arn:aws:aoss:{REGION}:{account_id}:collection/*"
                ],
            },
        ],
    }

    try:
        role = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Allows Bedrock Knowledge Base to access S3 and OpenSearch for SAELAR",
        )
        role_arn = role["Role"]["Arn"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            role_arn = f"arn:aws:iam::{account_id}:role/{ROLE_NAME}"
            print(f"{YELLOW}[!]{NC} Role already exists, reusing: {role_arn}")
            iam.update_assume_role_policy(
                RoleName=ROLE_NAME,
                PolicyDocument=json.dumps(trust_policy),
            )
        else:
            raise

    policy_name = "SaelarKBPermissions"
    try:
        iam.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(permissions_policy),
        )
    except ClientError:
        pass

    print(f"{GREEN}[✓]{NC} IAM role ready: {role_arn}")
    time.sleep(10)
    return role_arn


def create_oss_collection(account_id):
    """Create OpenSearch Serverless collection for vector storage."""
    print(f"{BLUE}[2/5]{NC} Creating OpenSearch Serverless collection: {COLLECTION_NAME}...")
    oss = boto3.client("opensearchserverless", region_name=REGION)

    encryption_policy = {
        "Rules": [{"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"]}],
        "AWSOwnedKey": True,
    }
    try:
        oss.create_security_policy(
            name=f"{COLLECTION_NAME}-enc",
            type="encryption",
            policy=json.dumps(encryption_policy),
        )
    except ClientError as e:
        if "ConflictException" not in str(type(e)):
            if e.response["Error"]["Code"] != "ConflictException":
                pass

    network_policy = [
        {
            "Rules": [
                {"ResourceType": "collection", "Resource": [f"collection/{COLLECTION_NAME}"]},
                {"ResourceType": "dashboard", "Resource": [f"collection/{COLLECTION_NAME}"]},
            ],
            "AllowFromPublic": True,
        }
    ]
    try:
        oss.create_security_policy(
            name=f"{COLLECTION_NAME}-net",
            type="network",
            policy=json.dumps(network_policy),
        )
    except ClientError:
        pass

    data_access_policy = [
        {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{COLLECTION_NAME}"],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems",
                    ],
                },
                {
                    "ResourceType": "index",
                    "Resource": [f"index/{COLLECTION_NAME}/*"],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:UpdateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument",
                    ],
                },
            ],
            "Principal": [
                f"arn:aws:iam::{account_id}:role/{ROLE_NAME}",
                f"arn:aws:iam::{account_id}:root",
            ],
        }
    ]
    try:
        oss.create_access_policy(
            name=f"{COLLECTION_NAME}-access",
            type="data",
            policy=json.dumps(data_access_policy),
        )
    except ClientError:
        pass

    try:
        resp = oss.create_collection(
            name=COLLECTION_NAME,
            type="VECTORSEARCH",
            description="SAELAR vector store for compliance document retrieval",
        )
        collection_id = resp["createCollectionDetail"]["id"]
    except ClientError as e:
        if "ConflictException" in str(type(e)) or e.response["Error"]["Code"] == "ConflictException":
            colls = oss.batch_get_collection(names=[COLLECTION_NAME])
            collection_id = colls["collectionDetails"][0]["id"]
            print(f"{YELLOW}[!]{NC} Collection already exists, reusing")
        else:
            raise

    print(f"  Waiting for collection to become active (this may take 2-3 minutes)...")
    for _ in range(60):
        colls = oss.batch_get_collection(ids=[collection_id])
        status = colls["collectionDetails"][0]["status"]
        if status == "ACTIVE":
            break
        time.sleep(5)

    endpoint = colls["collectionDetails"][0].get("collectionEndpoint", "")
    collection_arn = colls["collectionDetails"][0]["arn"]
    print(f"{GREEN}[✓]{NC} Collection active: {collection_arn}")
    return collection_arn, endpoint


def create_vector_index(endpoint):
    """Create the vector index in OpenSearch Serverless."""
    print(f"  Creating vector index...")
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth

    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        REGION,
        "aoss",
        session_token=credentials.token,
    )

    host = endpoint.replace("https://", "")
    client = OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=60,
    )

    index_name = "bedrock-knowledge-base-default-index"
    index_body = {
        "settings": {
            "index.knn": True,
            "number_of_shards": 2,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "bedrock-knowledge-base-default-vector": {
                    "type": "knn_vector",
                    "dimension": 1024,
                    "method": {
                        "engine": "faiss",
                        "name": "hnsw",
                        "parameters": {"m": 16, "ef_construction": 512},
                    },
                },
                "AMAZON_BEDROCK_METADATA": {"type": "text", "index": False},
                "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
            }
        },
    }

    try:
        client.indices.create(index=index_name, body=index_body)
        print(f"{GREEN}[✓]{NC} Vector index created")
    except Exception as e:
        if "resource_already_exists_exception" in str(e).lower():
            print(f"{YELLOW}[!]{NC} Vector index already exists")
        else:
            raise

    return index_name


def create_knowledge_base(role_arn, collection_arn):
    """Create the Bedrock Knowledge Base."""
    print(f"{BLUE}[3/5]{NC} Creating Bedrock Knowledge Base: {KB_NAME}...")
    bedrock_agent = boto3.client("bedrock-agent", region_name=REGION)

    storage_config = {
        "type": "OPENSEARCH_SERVERLESS",
        "opensearchServerlessConfiguration": {
            "collectionArn": collection_arn,
            "vectorIndexName": "bedrock-knowledge-base-default-index",
            "fieldMapping": {
                "vectorField": "bedrock-knowledge-base-default-vector",
                "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
                "metadataField": "AMAZON_BEDROCK_METADATA",
            },
        },
    }

    try:
        resp = bedrock_agent.create_knowledge_base(
            name=KB_NAME,
            description=KB_DESCRIPTION,
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": f"arn:aws:bedrock:{REGION}::foundation-model/{EMBEDDING_MODEL}"
                },
            },
            storageConfiguration=storage_config,
        )
        kb_id = resp["knowledgeBase"]["knowledgeBaseId"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            kbs = bedrock_agent.list_knowledge_bases()
            for kb in kbs.get("knowledgeBaseSummaries", []):
                if kb["name"] == KB_NAME:
                    kb_id = kb["knowledgeBaseId"]
                    print(f"{YELLOW}[!]{NC} Knowledge Base already exists, reusing: {kb_id}")
                    return kb_id
            raise
        raise

    print(f"{GREEN}[✓]{NC} Knowledge Base created: {kb_id}")
    return kb_id


def create_data_source(kb_id):
    """Create S3 data source and trigger initial sync."""
    print(f"{BLUE}[4/5]{NC} Creating S3 data source for bucket: {S3_BUCKET}...")
    bedrock_agent = boto3.client("bedrock-agent", region_name=REGION)

    try:
        resp = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name="saelar-s3-documents",
            description="SAELAR compliance documents from S3",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": f"arn:aws:s3:::{S3_BUCKET}",
                    "inclusionPrefixes": [
                        "Documentation/",
                        "nist-assessments/",
                    ],
                },
            },
        )
        ds_id = resp["dataSource"]["dataSourceId"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConflictException":
            sources = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
            ds_id = sources["dataSourceSummaries"][0]["dataSourceId"]
            print(f"{YELLOW}[!]{NC} Data source already exists, reusing: {ds_id}")
        else:
            raise

    print(f"{GREEN}[✓]{NC} Data source created: {ds_id}")

    print(f"{BLUE}[5/5]{NC} Starting initial sync (ingesting documents from S3)...")
    try:
        bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
        )
        print(f"{GREEN}[✓]{NC} Sync started — documents are being ingested in the background")
        print(f"  This may take a few minutes depending on how many documents are in S3.")
    except ClientError as e:
        print(f"{YELLOW}[!]{NC} Could not start sync: {e}")
        print(f"  You can manually sync later from the Bedrock console.")

    return ds_id


def save_config(kb_id, ds_id, collection_arn):
    """Save KB configuration for use by the SAELAR app."""
    config = {
        "knowledge_base_id": kb_id,
        "data_source_id": ds_id,
        "collection_arn": collection_arn,
        "s3_bucket": S3_BUCKET,
        "region": REGION,
        "embedding_model": EMBEDDING_MODEL,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\n{GREEN}[✓]{NC} Configuration saved to: {CONFIG_FILE}")


def print_summary(kb_id, ds_id):
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║                KNOWLEDGE BASE SETUP COMPLETE!                          ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}Configuration:{NC}
    Knowledge Base ID:  {kb_id}
    Data Source ID:     {ds_id}
    S3 Bucket:          {S3_BUCKET}
    Region:             {REGION}
    Embedding Model:    {EMBEDDING_MODEL}

  {CYAN}What happens now:{NC}
    ✓ Documents from s3://{S3_BUCKET}/Documentation/ are being indexed
    ✓ Chad (AI) will automatically use the Knowledge Base for RAG
    ✓ New documents uploaded to S3 will be indexed on next sync

  {CYAN}To manually re-sync documents:{NC}
    Set environment variable: SAELAR_KB_ID={kb_id}
    Or it will be read from {CONFIG_FILE}

  {CYAN}To trigger a re-sync:{NC}
    python3 -c "
import boto3
client = boto3.client('bedrock-agent', region_name='{REGION}')
client.start_ingestion_job(knowledgeBaseId='{kb_id}', dataSourceId='{ds_id}')
print('Sync started')
"

  {CYAN}Restart SAELAR to activate RAG:{NC}
    sudo systemctl restart saelar
""")


def main():
    banner()

    if os.geteuid() == 0:
        print(f"{YELLOW}[!]{NC} Running as root. AWS credentials will use the instance role.")

    try:
        account_id = get_account_id()
        print(f"{GREEN}[✓]{NC} AWS Account: {account_id}")
        print(f"{GREEN}[✓]{NC} Region: {REGION}")
        print(f"{GREEN}[✓]{NC} S3 Bucket: {S3_BUCKET}")
        print()
    except Exception as e:
        print(f"{RED}[ERROR]{NC} Cannot access AWS: {e}")
        print(f"  Make sure AWS credentials are configured (IAM role, env vars, or ~/.aws/credentials)")
        sys.exit(1)

    role_arn = create_kb_role(account_id)
    collection_arn, endpoint = create_oss_collection(account_id)

    try:
        create_vector_index(endpoint)
    except ImportError:
        print(f"{YELLOW}[!]{NC} opensearch-py / requests-aws4auth not installed.")
        print(f"  Install with: pip3 install opensearch-py requests-aws4auth")
        print(f"  The vector index will be created automatically by Bedrock on first use.")
    except Exception as e:
        print(f"{YELLOW}[!]{NC} Could not create vector index directly: {e}")
        print(f"  Bedrock will attempt to create it automatically.")

    kb_id = create_knowledge_base(role_arn, collection_arn)
    ds_id = create_data_source(kb_id)
    save_config(kb_id, ds_id, collection_arn)
    print_summary(kb_id, ds_id)


if __name__ == "__main__":
    main()
