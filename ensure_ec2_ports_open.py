#!/usr/bin/env python3
"""Ensure EC2 security group has ports 8080 and 8484 open for SAELAR/SOPRA.
   Also checks NACL and prints diagnostics."""
import boto3

SG_NAME = "saelar-sopra-sg"
REGION = "us-east-1"

ec2 = boto3.client("ec2", region_name=REGION)

# Get security group
sgs = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": [SG_NAME]}])
if not sgs["SecurityGroups"]:
    print(f"Security group {SG_NAME} not found")
    exit(1)

sg = sgs["SecurityGroups"][0]
sg_id = sg["GroupId"]
rules = sg.get("IpPermissions", [])

ports_needed = {80: "Splash", 8080: "SOPRA", 8484: "SAELAR", 2323: "BeeKeeper", 8443: "SAELAR-HTTPS", 8444: "SOPRA-HTTPS"}
ports_have = set()
for r in rules:
    if r.get("FromPort") == r.get("ToPort"):
        ports_have.add(r["FromPort"])

missing = [p for p in ports_needed if p not in ports_have]
if not missing:
    print(f"All required ports already open in {sg_id}")
else:
    for port in missing:
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                "IpProtocol": "tcp", "FromPort": port, "ToPort": port,
                "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": ports_needed[port]}],
            }],
        )
        print(f"Added port {port} ({ports_needed[port]}) to security group")

# Get instance and subnet
r = ec2.describe_instances(
    Filters=[
        {"Name": "tag:Name", "Values": ["SAELAR-SOPRA-Server"]},
        {"Name": "instance-state-name", "Values": ["running"]},
    ]
)
instance_id = None
subnet_id = None
ip = None
for res in r.get("Reservations", []):
    for inst in res.get("Instances", []):
        ip = inst.get("PublicIpAddress")
        subnet_id = inst.get("SubnetId")
        instance_id = inst.get("InstanceId")
        break
    if ip:
        break

print(f"\nEC2 IP: {ip}")
print(f"  SOPRA:       http://{ip}:8080  | https://{ip}:8444")
print(f"  SAELAR:      http://{ip}:8484  | https://{ip}:8443")
print(f"  BeeKeeper:   http://{ip}:2323")

# Check NACL for subnet
if subnet_id:
    nacls = ec2.describe_network_acls(
        Filters=[{"Name": "association.subnet-id", "Values": [subnet_id]}]
    )
    if nacls.get("NetworkAcls"):
        nacl = nacls["NetworkAcls"][0]
        nacl_id = nacl.get("NetworkAclId", "")
        entries = nacl.get("Entries", [])
        inbound_8080 = any(
            e.get("RuleAction") == "allow" and e.get("FromPort") in (8080, None)
            and (e.get("ToPort") in (8080, None) or e.get("CidrBlock") == "0.0.0.0/0")
            for e in entries if e.get("Egress") is False
        )
        has_allow_all = any(
            e.get("RuleAction") == "allow" and e.get("CidrBlock") == "0.0.0.0/0"
            and e.get("Protocol") in ("-1", "6")  # all or tcp
            for e in entries if e.get("Egress") is False
        )
        if has_allow_all or inbound_8080:
            print(f"\nNACL ({nacl_id}): allows traffic (OK)")
        else:
            print(f"\nNACL ({nacl_id}): may block 8080/8484 - check rules for ports")
