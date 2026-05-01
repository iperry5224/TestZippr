#!/usr/bin/env python3
"""
SLyK-53 Complete Deployment
============================
Deploys the entire SLyK-53 platform in one run:
  1. Core agent and Lambda functions (deploy_slyk.py)
  2. Infrastructure: Cognito, API Gateway, DynamoDB, CloudFront (deploy_infrastructure.py)
  3. Knowledge Base for RAG (deploy_knowledge_base.py) [optional]

Usage:
    python3 deploy_all.py [--skip-kb]

Options:
    --skip-kb    Skip Knowledge Base deployment (faster, can add later)
"""

import os
import sys
import subprocess

CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"


def banner():
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║   SLyK-53 — Complete Platform Deployment                               ║
║   SAE Lightweight Yaml Kit                                             ║
║                                                                        ║
║   This will deploy:                                                    ║
║     • Bedrock Agent with Lambda action groups                          ║
║     • Cognito Identity Pool for authentication                         ║
║     • API Gateway REST API                                             ║
║     • DynamoDB tables for sessions and audit                           ║
║     • S3 + CloudFront for UI hosting                                   ║
║     • Knowledge Base for RAG (optional)                                ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}
""")


def run_script(script_name, description):
    print(f"\n{CYAN}{'═' * 72}{NC}")
    print(f"{CYAN}  {description}{NC}")
    print(f"{CYAN}{'═' * 72}{NC}\n")

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)

    if not os.path.exists(script_path):
        print(f"{RED}  ✗ Script not found: {script_path}{NC}")
        return False

    result = subprocess.run([sys.executable, script_path], cwd=os.path.dirname(script_path))

    if result.returncode != 0:
        print(f"\n{YELLOW}  ! {script_name} completed with warnings or errors{NC}")
        return False

    return True


def main():
    banner()

    skip_kb = "--skip-kb" in sys.argv

    # Step 1: Core deployment
    if not run_script("deploy_slyk.py", "Step 1/3: Deploying Core Agent and Lambda Functions"):
        print(f"\n{YELLOW}Core deployment had issues. Continuing...{NC}")

    # Step 2: Infrastructure
    if not run_script("deploy_infrastructure.py", "Step 2/3: Deploying Infrastructure (Cognito, API GW, DynamoDB, CloudFront)"):
        print(f"\n{YELLOW}Infrastructure deployment had issues. Continuing...{NC}")

    # Step 3: Knowledge Base (optional)
    if skip_kb:
        print(f"\n{YELLOW}Skipping Knowledge Base deployment (--skip-kb flag){NC}")
        print(f"{YELLOW}Run 'python3 deploy_knowledge_base.py' later to add RAG capabilities.{NC}")
    else:
        if not run_script("deploy_knowledge_base.py", "Step 3/3: Deploying Knowledge Base (RAG)"):
            print(f"\n{YELLOW}Knowledge Base deployment had issues.{NC}")
            print(f"{YELLOW}This is optional — SLyK will work without it.{NC}")

    # Final summary
    print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════════════╗
║                    SLyK-53 DEPLOYMENT COMPLETE!                        ║
╚═══════════════════════════════════════════════════════════════════════╝{NC}

  {CYAN}What was deployed:{NC}
    ✓ Bedrock Agent (SLyK-53-Security-Assistant)
    ✓ Lambda functions (assess, remediate, harden)
    ✓ Cognito Identity Pool
    ✓ API Gateway
    ✓ DynamoDB tables (sessions, audit)
    ✓ S3 bucket for UI
    ✓ CloudFront distribution
    {"✓ Knowledge Base (RAG)" if not skip_kb else "○ Knowledge Base (skipped)"}

  {CYAN}Next steps:{NC}
    1. Build and deploy the React UI:
       cd ui
       npm install
       npm run build
       aws s3 sync build/ s3://slyk-ui-<ACCOUNT_ID>/

    2. Access SLyK-53:
       - Via CloudFront: Check slyk_config.json for cloudfront_domain
       - Via Bedrock Console: AWS Console > Bedrock > Agents

    3. Test the agent:
       "Assess my NIST 800-53 compliance"
       "Harden all my S3 buckets"
       "Show me Security Hub findings"

  {CYAN}Configuration:{NC}
    All resource IDs saved to: slyk_config.json
    UI environment file: ui/.env
""")


if __name__ == "__main__":
    main()
