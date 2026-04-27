#!/usr/bin/env python3
"""
Create the S3 bucket expected by SLyK deploy_slyk.py (config upload + Lambda IAM).

Important:
  - This uses your **AWS API credentials** (same as `aws sts get-caller-identity`).
  - An EC2 **.pem** file is for **SSH only**; it does not authenticate S3. Use
    `aws configure`, an IAM role, SSO, or **AWS CloudShell** (browser, no key file).

S3 names are **globally unique** across all AWS accounts. If `saelarallpurpose` is
already taken, pass --bucket with a unique name (e.g. saelarallpurpose-ipperry-016230494923)
and set the same in deploy: export S3_BUCKET_NAME=that-name

Usage:
  python create_slyk_s3_bucket.py
  python create_slyk_s3_bucket.py --bucket my-unique-bucket --region us-east-1
"""
from __future__ import annotations

import argparse
import sys

import boto3
from botocore.exceptions import ClientError

DEFAULT_SLYK_BUCKET = "saelarallpurpose"


def main() -> None:
    p = argparse.ArgumentParser(description="Create S3 bucket for SLyK deploy_slyk.py.")
    p.add_argument(
        "--bucket",
        default=DEFAULT_SLYK_BUCKET,
        help=f"Bucket name (default: {DEFAULT_SLYK_BUCKET}; must be globally unique).",
    )
    p.add_argument("--region", default=None, help="Region (default: session or us-east-1).")
    args = p.parse_args()

    b = args.bucket.strip().lower()
    if b != args.bucket.strip():
        print("[!] Normalized bucket name to lowercase:", b)
    if not (3 <= len(b) <= 63):
        print("[!] Bucket name length must be 3-63 characters.", file=sys.stderr)
        sys.exit(1)

    session = boto3.session.Session()
    region = args.region or session.region_name or "us-east-1"
    s3 = session.client("s3", region_name=region)

    # Verify caller (same account as deploy_slyk will use)
    sts = session.client("sts", region_name=region)
    try:
        who = sts.get_caller_identity()
        print(f"Account: {who.get('Account')}")
        print(f"ARN:     {who.get('Arn', '')[:80]}...")
    except Exception as e:
        print(f"[!] Cannot get caller identity. Configure AWS credentials. {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Region:  {region}")
    print(f"Bucket:  {b}")
    print()

    try:
        if region == "us-east-1":
            s3.create_bucket(Bucket=b)
        else:
            s3.create_bucket(
                Bucket=b,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        print("  [OK] Created bucket")
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("BucketAlreadyOwnedByYou",):
            print("  [—] You already own this bucket (OK)")
        elif code in ("BucketAlreadyExists", "OperationAborted"):
            print(
                f"  [!] {code}: the name {b!r} is not available globally.",
                file=sys.stderr,
            )
            print(
                "      Choose another: --bucket saelarallpurpose-YOURACCOUNT-UNIQUETAG",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            print(f"  [!] create_bucket: {e}", file=sys.stderr)
            sys.exit(1)

    s3.put_public_access_block(
        Bucket=b,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    print("  [OK] Blocked public access")

    s3.put_bucket_encryption(
        Bucket=b,
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )
    print("  [OK] Default encryption: SSE-S3 (AES256)")

    s3.put_object(
        Bucket=b,
        Key="slyk/README.txt",
        Body=(
            b"SLyK deploy writes: slyk/slyk_config.json\n"
            b"Set S3_BUCKET_NAME to this bucket name for deploy_slyk.py\n"
        ),
        ContentType="text/plain; charset=utf-8",
    )
    print("  [OK] slyk/README.txt")

    print()
    print("Before running deploy_slyk.py:")
    print(f"  export S3_BUCKET_NAME={b}")
    print(f"  export AWS_DEFAULT_REGION={region}")
    print()


if __name__ == "__main__":
    main()
