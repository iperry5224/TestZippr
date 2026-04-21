# SLyK-53 (SAE Light Yaml Kit): Bedrock Agent + API Gateway + Console Integration

## Implementation Guide

**Version:** 1.0
**Date:** April 2026
**Prepared by:** SAE Team

---

## 1. Architecture Overview

```
AWS Console
    │
    ├─→ Service Catalog Link: "Open SLyK-53 Security Assistant"
    │       │
    │       ▼
    │   API Gateway (HTTPS endpoint)
    │       │
    │       ▼
    │   S3-hosted React UI (static site)
    │       │
    │       ├─→ Bedrock Agent (SLyK Agent — chat + orchestration)
    │       │       │
    │       │       ├─→ Action Group: ASSESS (Lambda)
    │       │       ├─→ Action Group: REMEDIATE (Lambda)
    │       │       ├─→ Action Group: HARDEN (Lambda)
    │       │       ├─→ Action Group: REPORT (Lambda)
    │       │       └─→ Knowledge Base (RAG)
    │       │
    │       └─→ Cognito (uses Console IAM session — no new login)
    │
    └─→ CloudWatch Dashboard (executive posture widget)
```

**How the user experiences it:**
1. User is logged into AWS Console
2. Clicks "SLyK-53 Security Assistant" link (Service Catalog or bookmark)
3. A new tab opens with the SLyK React UI (hosted on S3 + CloudFront)
4. User is auto-authenticated via their existing AWS session
5. Full GUI with chat, dashboards, and action buttons — looks like SAELAR but runs serverless

---

## 2. Components to Build

| # | Component | AWS Service | Purpose |
|---|---|---|---|
| 1 | React UI | S3 + CloudFront | Frontend — chat interface, dashboards, action buttons |
| 2 | API Layer | API Gateway (REST) | Routes UI requests to Bedrock Agent and Lambda |
| 3 | Auth | Cognito Identity Pool | Federates AWS Console IAM session — no separate login |
| 4 | AI Agent | Bedrock Agent | Orchestrates assess/remediate/harden workflows |
| 5 | Assess Logic | Lambda (Python) | Repackaged SAELAR assessment engine |
| 6 | Remediate Logic | Lambda (Python) | Generates + executes remediation via SSM |
| 7 | Harden Logic | Lambda (Python) | Scans and hardens S3, EC2, IAM, RDS |
| 8 | Report Logic | Lambda (Python) | Generates SSP, POA&M, RAR as Markdown |
| 9 | Knowledge Base | Bedrock KB + OpenSearch | RAG over stored compliance documents |
| 10 | State Store | DynamoDB | Assessment history, user sessions, audit log |
| 11 | Document Store | S3 (saelarallpurpose) | SSPs, POA&Ms, RARs, assessment results |
| 12 | Console Link | Service Catalog | Clickable entry point in AWS Console |

---

## 3. Step-by-Step Implementation

### Phase 1: Repackage SAELAR Code into Lambda (Week 1-3)

The existing Python code doesn't change — it gets packaged as Lambda functions.

**Step 1.1 — Create the assessment Lambda**

Take the core assessment logic from `nist_800_53_rev5_full.py` and wrap it:

```python
# lambda_assess/handler.py
import json
from nist_800_53_rev5_full import NIST80053Rev5Assessor

def handler(event, context):
    """Bedrock Agent action group handler for ASSESS."""
    action = event.get("actionGroup", "")
    api_path = event.get("apiPath", "")
    parameters = event.get("parameters", [])

    # Extract parameters from Bedrock Agent
    params = {p["name"]: p["value"] for p in parameters}
    region = params.get("region", "us-east-1")
    families = params.get("families", "ALL").split(",")

    # Run assessment (same code as SAELAR)
    assessor = NIST80053Rev5Assessor(region=region)
    results = assessor.run_assessment(families=families)

    # Format response for Bedrock Agent
    summary = assessor.generate_summary(results)
    controls = []
    for r in results:
        controls.append({
            "control_id": r.control_id,
            "control_name": r.control_name,
            "family": r.family,
            "status": r.status.name,
            "findings": r.findings,
            "recommendations": r.recommendations,
        })

    response_body = {
        "application/json": {
            "body": json.dumps({
                "summary": summary,
                "controls": controls,
            })
        }
    }

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action,
            "apiPath": api_path,
            "httpMethod": "POST",
            "httpStatusCode": 200,
            "responseBody": response_body,
        }
    }
```

**Step 1.2 — Create the remediation Lambda**

```python
# lambda_remediate/handler.py
import json
import boto3

def handler(event, context):
    """Generate and optionally execute remediation for a failed control."""
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    control_id = params.get("control_id", "")
    action_type = params.get("action", "generate")  # generate or execute

    remediation_map = {
        "AC-2": {
            "title": "Enable MFA for IAM users",
            "script": "aws iam list-users --query 'Users[*].UserName' --output text | while read user; do echo \"Checking MFA for $user\"; aws iam list-mfa-devices --user-name $user; done",
            "ssm_document": "AWS-EnableMFADevice",
        },
        "IA-5": {
            "title": "Rotate old access keys",
            "script": "aws iam list-access-keys --query 'AccessKeyMetadata[?Status==`Active`]' --output json",
            "ssm_document": "AWS-RotateAccessKey",
        },
        # ... (ported from SAELAR's remediation logic)
    }

    remediation = remediation_map.get(control_id, {
        "title": f"Remediation for {control_id}",
        "script": f"# No automated remediation available for {control_id}",
    })

    if action_type == "execute" and remediation.get("ssm_document"):
        ssm = boto3.client("ssm")
        ssm.send_command(
            DocumentName=remediation["ssm_document"],
            Targets=[{"Key": "tag:Environment", "Values": ["production"]}],
        )
        remediation["execution_status"] = "Submitted via SSM"

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup"),
            "apiPath": event.get("apiPath"),
            "httpMethod": "POST",
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {"body": json.dumps(remediation)}
            },
        }
    }
```

**Step 1.3 — Create the hardening Lambda**

```python
# lambda_harden/handler.py
import json
import boto3

def handler(event, context):
    """Scan and harden AWS assets."""
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}
    asset_type = params.get("asset_type", "s3")  # s3, ec2, iam, rds
    action = params.get("action", "scan")  # scan or fix

    if asset_type == "s3":
        return harden_s3(action)
    elif asset_type == "ec2":
        return harden_ec2(action)
    elif asset_type == "iam":
        return harden_iam(action)

def harden_s3(action):
    s3 = boto3.client("s3")
    buckets = s3.list_buckets()["Buckets"]
    findings = []

    for bucket in buckets:
        name = bucket["Name"]
        issues = []

        # Check public access
        try:
            pab = s3.get_public_access_block(Bucket=name)
            config = pab["PublicAccessBlockConfiguration"]
            if not all(config.values()):
                issues.append({"check": "Public Access Block", "status": "FAIL", "fix": "Enable all public access block settings"})
                if action == "fix":
                    s3.put_public_access_block(Bucket=name, PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True, "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True, "RestrictPublicBuckets": True
                    })
        except:
            issues.append({"check": "Public Access Block", "status": "FAIL", "fix": "Enable public access block"})

        # Check encryption
        try:
            s3.get_bucket_encryption(Bucket=name)
        except:
            issues.append({"check": "Default Encryption", "status": "FAIL", "fix": "Enable SSE-S3"})
            if action == "fix":
                s3.put_bucket_encryption(Bucket=name, ServerSideEncryptionConfiguration={
                    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
                })

        # Check versioning
        versioning = s3.get_bucket_versioning(Bucket=name)
        if versioning.get("Status") != "Enabled":
            issues.append({"check": "Versioning", "status": "FAIL", "fix": "Enable versioning"})
            if action == "fix":
                s3.put_bucket_versioning(Bucket=name, VersioningConfiguration={"Status": "Enabled"})

        if issues:
            findings.append({"bucket": name, "issues": issues})

    return format_response({"asset_type": "s3", "findings": findings, "action": action})
```

**Step 1.4 — Package and deploy Lambdas**

```bash
# For each Lambda function:
cd lambda_assess
pip install -r requirements.txt -t .
zip -r ../grcp-assess.zip .
aws lambda create-function \
    --function-name grcp-assess-controls \
    --runtime python3.12 \
    --handler handler.handler \
    --zip-file fileb://../grcp-assess.zip \
    --role arn:aws:iam::656443597515:role/saelar-role \
    --timeout 300 \
    --memory-size 512 \
    --region us-east-1
```

---

### Phase 2: Create the Bedrock Agent (Week 3-4)

**Step 2.1 — Create the Agent**

```bash
aws bedrock-agent create-agent \
    --agent-name "SLyK-53-Security-Assistant" \
    --description "SLyK-53 security compliance, remediation, and hardening assistant for System 5065" \
    --foundation-model "amazon.titan-text-express-v1" \
    --instruction "You are SLyK, the SAE Light Yaml Kit security assistant for NOAA System 5065. You are part of the GRCP (GRC Platform) family of tools. You help users assess NIST 800-53 controls, remediate findings, and harden AWS assets. Always explain what you're doing and ask for confirmation before making changes. Provide specific, actionable guidance with AWS CLI commands." \
    --agent-resource-role-arn "arn:aws:iam::656443597515:role/saelar-role" \
    --region us-east-1
```

**Step 2.2 — Define OpenAPI Schema for Action Groups**

```yaml
# grcp-agent-api.yaml
openapi: 3.0.0
info:
  title: SLyK-53 Security Assistant API
  version: 1.0.0

paths:
  /assess:
    post:
      operationId: assessCompliance
      summary: Run NIST 800-53 compliance assessment
      parameters:
        - name: region
          in: query
          schema:
            type: string
          description: AWS region to assess
        - name: families
          in: query
          schema:
            type: string
          description: Comma-separated control families (AC,AU,IA) or ALL
      responses:
        '200':
          description: Assessment results with pass/fail per control

  /remediate:
    post:
      operationId: remediateControl
      summary: Generate or execute remediation for a failed control
      parameters:
        - name: control_id
          in: query
          schema:
            type: string
          description: NIST control ID (e.g., AC-2, IA-5)
        - name: action
          in: query
          schema:
            type: string
            enum: [generate, execute]
          description: Generate script only, or execute via SSM
      responses:
        '200':
          description: Remediation script and execution status

  /harden:
    post:
      operationId: hardenAssets
      summary: Scan and harden AWS assets
      parameters:
        - name: asset_type
          in: query
          schema:
            type: string
            enum: [s3, ec2, iam, rds]
          description: Type of asset to harden
        - name: action
          in: query
          schema:
            type: string
            enum: [scan, fix]
          description: Scan only, or scan and apply fixes
      responses:
        '200':
          description: Hardening findings and applied fixes

  /report:
    post:
      operationId: generateReport
      summary: Generate compliance document
      parameters:
        - name: report_type
          in: query
          schema:
            type: string
            enum: [ssp, poam, rar, executive_summary]
          description: Type of report to generate
        - name: system_name
          in: query
          schema:
            type: string
          description: System name for the report
      responses:
        '200':
          description: Generated report content
```

**Step 2.3 — Create Action Groups**

```bash
# Upload schema to S3
aws s3 cp grcp-agent-api.yaml s3://saelarallpurpose/agent/grcp-agent-api.yaml

# Create action groups (run for each)
aws bedrock-agent create-agent-action-group \
    --agent-id <AGENT_ID> \
    --agent-version DRAFT \
    --action-group-name "ASSESS" \
    --action-group-executor '{"lambda": "arn:aws:lambda:us-east-1:656443597515:function:grcp-assess-controls"}' \
    --api-schema '{"s3": {"s3BucketName": "saelarallpurpose", "s3ObjectKey": "agent/grcp-agent-api.yaml"}}' \
    --region us-east-1
```

**Step 2.4 — Prepare and test the Agent**

```bash
aws bedrock-agent prepare-agent --agent-id <AGENT_ID> --region us-east-1

# Create an alias for the prepared version
aws bedrock-agent create-agent-alias \
    --agent-id <AGENT_ID> \
    --agent-alias-name "production" \
    --region us-east-1
```

Test in the Bedrock Console:
1. Go to **Bedrock** > **Agents** > **SLyK-53-Security-Assistant**
2. Click **Test** in the right panel
3. Type: "Assess my NIST 800-53 compliance for AC controls"
4. Verify the agent invokes the Lambda and returns results

---

### Phase 3: Build the React UI (Week 4-6)

**Step 3.1 — Create the React app**

```bash
npx create-react-app grcp-ui
cd grcp-ui
npm install @aws-sdk/client-bedrock-agent-runtime @aws-amplify/auth aws-amplify
```

**Step 3.2 — Core chat component**

```jsx
// src/components/ChatInterface.jsx
import React, { useState } from 'react';
import { BedrockAgentRuntimeClient, InvokeAgentCommand } from '@aws-sdk/client-bedrock-agent-runtime';

const AGENT_ID = '<YOUR_AGENT_ID>';
const AGENT_ALIAS = '<YOUR_ALIAS_ID>';

function ChatInterface({ credentials }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(crypto.randomUUID());

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');

    const client = new BedrockAgentRuntimeClient({
      region: 'us-east-1',
      credentials,
    });

    const command = new InvokeAgentCommand({
      agentId: AGENT_ID,
      agentAliasId: AGENT_ALIAS,
      sessionId,
      inputText: input,
    });

    try {
      const response = await client.send(command);
      let fullResponse = '';
      for await (const event of response.completion) {
        if (event.chunk?.bytes) {
          fullResponse += new TextDecoder().decode(event.chunk.bytes);
        }
      }
      setMessages(prev => [...prev, { role: 'assistant', content: fullResponse }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <strong>{msg.role === 'user' ? 'You' : '🛡️ SLyK'}:</strong>
            <p>{msg.content}</p>
          </div>
        ))}
      </div>
      <div className="input-row">
        <input value={input} onChange={e => setInput(e.target.value)}
               onKeyDown={e => e.key === 'Enter' && sendMessage()}
               placeholder="Ask SLyK: 'Assess my S3 buckets' or 'Harden my EC2 instances'" />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default ChatInterface;
```

**Step 3.3 — Authentication (use existing AWS session)**

```jsx
// src/auth/AwsAuth.js
import { CognitoIdentityClient, GetIdCommand, GetCredentialsForIdentityCommand } from '@aws-sdk/client-cognito-identity';

const IDENTITY_POOL_ID = '<YOUR_IDENTITY_POOL_ID>';
const REGION = 'us-east-1';

export async function getCredentials() {
  const client = new CognitoIdentityClient({ region: REGION });

  // For Console-authenticated users, use IAM federation
  const idResponse = await client.send(new GetIdCommand({
    IdentityPoolId: IDENTITY_POOL_ID,
  }));

  const credResponse = await client.send(new GetCredentialsForIdentityCommand({
    IdentityId: idResponse.IdentityId,
  }));

  return credResponse.Credentials;
}
```

**Step 3.4 — Build and deploy to S3 + CloudFront**

```bash
# Build
cd grcp-ui
npm run build

# Deploy to S3
aws s3 sync build/ s3://slyk-ui-5065/ --delete

# Create CloudFront distribution
aws cloudfront create-distribution \
    --origin-domain-name slyk-ui-5065.s3.amazonaws.com \
    --default-root-object index.html
```

---

### Phase 4: Console Integration (Week 6-7)

**Step 4.1 — Create API Gateway**

```bash
aws apigateway create-rest-api \
    --name "SLyK-API" \
    --description "SLyK-53 Security Assistant API" \
    --endpoint-configuration types=REGIONAL \
    --region us-east-1
```

**Step 4.2 — Create Cognito Identity Pool (no new login)**

```bash
aws cognito-identity create-identity-pool \
    --identity-pool-name "SLyK-Identity-Pool" \
    --allow-unauthenticated-identities false \
    --supported-login-providers '{}' \
    --region us-east-1
```

Configure the identity pool to accept IAM authentication (Console session).

**Step 4.3 — Add to Service Catalog**

```bash
# Create a Service Catalog portfolio for SLyK
aws servicecatalog create-portfolio \
    --display-name "SLyK-53 Security Tools" \
    --description "SLyK-53 — Console-integrated security compliance and hardening (part of GRCP)" \
    --provider-name "SAE Team" \
    --region us-east-1

# Create a product that links to the UI
aws servicecatalog create-product \
    --name "SLyK-53 Security Assistant" \
    --description "AI-powered security compliance, remediation, and hardening (GRCP)" \
    --product-type CLOUD_FORMATION_TEMPLATE \
    --provisioning-artifact-parameters '{"Info": {"LoadTemplateFromURL": "https://s3.amazonaws.com/grcp-ui-5065/cfn-template.yaml"}, "Name": "v1.0", "Type": "CLOUD_FORMATION_TEMPLATE"}' \
    --region us-east-1
```

**Step 4.4 — Create Console Bookmark**

Add a custom link in the AWS Console:
1. Go to **AWS Console** > **Resource Groups** > **Tag Editor** (or any bookmarkable service)
2. Bookmark: `https://<cloudfront-distribution>.cloudfront.net`
3. Or use **myApplications** to register SLyK-53 as an application with a direct link

---

### Phase 5: Testing and Launch (Week 7-8)

**Step 5.1 — Test each workflow**

| Test | Command | Expected Result |
|---|---|---|
| Compliance scan | "Assess my NIST 800-53 compliance" | Returns pass/fail for all controls |
| Single family | "Check my IAM controls" | Returns IA family results only |
| Remediation | "Fix the AC-2 finding" | Generates CLI commands |
| S3 hardening | "Harden all my S3 buckets" | Scans buckets, lists issues |
| S3 fix | "Apply the S3 fixes" | Enables encryption, versioning, etc. |
| SSP generation | "Generate an SSP for System 5065" | Returns Markdown SSP |
| RAG query | "What does our latest POA&M say?" | Retrieves from Knowledge Base |

**Step 5.2 — Security review**

- Verify Lambda execution roles follow least privilege
- Confirm no data leaves the AWS boundary
- Validate CloudTrail logging for all agent actions
- Test that remediation requires explicit user confirmation

**Step 5.3 — Launch**

1. Share the CloudFront URL or Service Catalog link with the team
2. Add the link to the AWS Console favorites
3. Conduct a 30-minute walkthrough with ISSOs

---

## 4. Cost Estimate

| Component | Monthly Cost |
|---|---|
| Bedrock Agent | ~$0 (pay per invocation) |
| Bedrock model calls | ~$10-50 (depending on usage) |
| Lambda (assess/remediate/harden) | ~$5-20 |
| API Gateway | ~$3 |
| S3 (UI hosting + documents) | ~$1 |
| CloudFront | ~$1 |
| Cognito | Free (under 50K MAU) |
| DynamoDB | ~$5 |
| **Total** | **~$25-80/month** |

Compared to the current EC2-based deployment (~$50/month for t5a.medium), the serverless approach is comparable in cost but eliminates server maintenance entirely.

---

## 5. Timeline Summary

| Week | Deliverable |
|---|---|
| 1-2 | Lambda functions packaged from SAELAR code |
| 3 | Bedrock Agent created with action groups |
| 4-5 | React UI built and deployed to S3/CloudFront |
| 6 | Cognito + API Gateway + Service Catalog integration |
| 7 | Testing all workflows |
| 8 | Launch to team |
