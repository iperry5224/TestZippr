#!/usr/bin/env python3
"""
Launch SOPSAEL EC2 Instance
===========================
Creates a new EC2 instance named "sopsael" for containerized SAELAR + SOPRA.
Ports: 8443 (SAELAR), 5224 (SOPRA), 22 (SSH)

Requires: AWS CLI configured or boto3 with credentials
Usage: python deploy/launch_sopsael_ec2.py
"""
import json
import os
import sys
import time
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("Error: boto3 required. Run: pip install boto3")
    sys.exit(1)

# Config
REGION = os.environ.get("AWS_REGION", "us-east-1")
INSTANCE_TYPE = "t3.medium"
KEY_NAME = "saelar-sopra-key"
SG_NAME = "sopsael-sg"
INSTANCE_NAME = "sopsael"
IAM_PROFILE = "SaelarSopraEC2Profile"  # Reuse for Bedrock access
DISK_GB = 25
SAELAR_PORT = 8443
SOPRA_PORT = 5224

ec2 = boto3.client("ec2", region_name=REGION)


def get_ubuntu_ami():
    try:
        ssm = boto3.client("ssm", region_name=REGION)
        r = ssm.get_parameter(
            Name="/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"
        )
        return r["Parameter"]["Value"]
    except Exception as e:
        print(f"Warning: Could not get AMI from SSM: {e}")
        return "ami-0c7217cdde317cfec"  # Ubuntu 22.04 us-east-1 fallback


def get_default_vpc():
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "is-default", "Values": ["true"]}])
    if not vpcs["Vpcs"]:
        raise SystemExit("No default VPC found")
    return vpcs["Vpcs"][0]["VpcId"]


def ensure_security_group(vpc_id):
    try:
        sgs = ec2.describe_security_groups(
            Filters=[
                {"Name": "group-name", "Values": [SG_NAME]},
                {"Name": "vpc-id", "Values": [vpc_id]},
            ]
        )
        if sgs["SecurityGroups"]:
            return sgs["SecurityGroups"][0]["GroupId"]
    except ClientError:
        pass

    sg = ec2.create_security_group(
        GroupName=SG_NAME,
        Description=f"SOPSAEL - SSH, SAELAR ({SAELAR_PORT}), SOPRA ({SOPRA_PORT})",
        VpcId=vpc_id,
    )
    sg_id = sg["GroupId"]

    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH"}]},
            {"IpProtocol": "tcp", "FromPort": SAELAR_PORT, "ToPort": SAELAR_PORT, "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SAELAR"}]},
            {"IpProtocol": "tcp", "FromPort": SOPRA_PORT, "ToPort": SOPRA_PORT, "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SOPRA"}]},
        ],
    )
    print(f"  Created security group: {sg_id}")
    return sg_id


def main():
    print("=" * 60)
    print("  Launch SOPSAEL EC2 Instance")
    print("=" * 60)

    # Check key pair
    try:
        ec2.describe_key_pairs(KeyNames=[KEY_NAME])
    except ClientError:
        print(f"\nError: Key pair '{KEY_NAME}' not found.")
        print("Create it in AWS Console or run deploy_to_aws.py first.")
        sys.exit(1)
    print(f"  Using key pair: {KEY_NAME}")

    vpc_id = get_default_vpc()
    sg_id = ensure_security_group(vpc_id)
    ami_id = get_ubuntu_ami()

    user_data = """#!/bin/bash
set -ex
exec > /var/log/sopsael-userdata.log 2>&1

apt-get update -y
apt-get install -y docker.io docker-compose-plugin git python3-pip

systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# Create app dir
mkdir -p /home/ubuntu/sopsael
chown -R ubuntu:ubuntu /home/ubuntu/sopsael

touch /tmp/sopsael_bootstrap_done
echo "Bootstrap complete"
"""

    # Optional: use IAM profile for Bedrock (if it exists)
    iam_profile = None
    try:
        iam = boto3.client("iam", region_name=REGION)
        iam.get_instance_profile(InstanceProfileName=IAM_PROFILE)
        iam_profile = {"Name": IAM_PROFILE}
        print(f"  Using IAM profile: {IAM_PROFILE} (Bedrock access)")
    except ClientError:
        print("  No IAM profile - Bedrock will need credentials via env or ~/.aws")

    print("\n  Launching instance...")
    run_params = dict(
        ImageId=ami_id,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        SecurityGroupIds=[sg_id],
        MinCount=1,
        MaxCount=1,
        BlockDeviceMappings=[
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {"VolumeSize": DISK_GB, "VolumeType": "gp3"},
            }
        ],
        UserData=user_data,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": INSTANCE_NAME},
                    {"Key": "Project", "Value": "SOPSAEL"},
                ],
            }
        ],
    )
    if iam_profile:
        run_params["IamInstanceProfile"] = iam_profile

    r = ec2.run_instances(**run_params)
    instance_id = r["Instances"][0]["InstanceId"]
    print(f"  Instance ID: {instance_id}")
    print("  Waiting for instance to run...")

    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])

    # Get public IP
    desc = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = desc["Reservations"][0]["Instances"][0].get("PublicIpAddress", "pending")

    print("\n" + "=" * 60)
    print("  SOPSAEL EC2 Launched Successfully!")
    print("=" * 60)
    print(f"\n  Instance ID: {instance_id}")
    print(f"  Public IP:   {public_ip}")
    print(f"\n  Allow 2-3 min for Docker install, then:")
    print(f"  ssh -i {KEY_NAME}.pem ubuntu@{public_ip}")
    print(f"\n  SAELAR: http://{public_ip}:{SAELAR_PORT}")
    print(f"  SOPRA:  http://{public_ip}:{SOPRA_PORT}")
    print(f"\n  Deploy containers: scp -r sopsael ubuntu@{public_ip}:~/ && ssh ubuntu@{public_ip} 'cd sopsael && docker compose up -d'")
    print()


if __name__ == "__main__":
    main()
