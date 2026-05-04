# SLyK-53 Eraser.io Diagrams

Copy and paste each diagram below into eraser.io (https://app.eraser.io)

---

## Diagram 1: SLyK-53 Architecture Overview

```
// SLyK-53 — SAE Lightweight Yaml Kit Architecture

AWS Console [icon: aws-console, color: orange] {
  ISSO / Engineer [icon: user, color: blue]
}

Amazon Bedrock [icon: aws, color: purple] {
  SLyK-53 Agent [icon: aws-bedrock, color: purple, label: "SLyK-53\nBedrock Agent"]
}

Lambda Functions [icon: aws-lambda, color: orange] {
  ASSESS [icon: aws-lambda, color: green, label: "ASSESS\nNIST 800-53"]
  REMEDIATE [icon: aws-lambda, color: yellow, label: "REMEDIATE\nFix Scripts"]
  HARDEN [icon: aws-lambda, color: red, label: "HARDEN\nS3/EC2/IAM"]
  TRIAGE [icon: aws-lambda, color: orange, label: "TRIAGE\nAlert Analysis"]
  RUNBOOKS [icon: aws-lambda, color: blue, label: "RUNBOOKS\nISSO Workflows"]
}

AWS Services [icon: aws, color: gray] {
  IAM [icon: aws-iam]
  EC2 [icon: aws-ec2]
  S3 [icon: aws-simple-storage-service]
  Security Hub [icon: aws-security-hub]
  GuardDuty [icon: aws-guardduty]
  CloudTrail [icon: aws-cloudtrail]
  Inspector [icon: aws-inspector]
  KMS [icon: aws-kms]
}

Alerting [icon: aws-eventbridge, color: red] {
  EventBridge [icon: aws-eventbridge, label: "EventBridge\nCRITICAL/HIGH"]
  SNS [icon: aws-sns, label: "SNS\nEmail/Slack"]
}

Storage [icon: aws-simple-storage-service, color: green] {
  S3 Audit [icon: aws-simple-storage-service, label: "S3\nAudit Trail"]
}

ISSO / Engineer > SLyK-53 Agent: Natural language commands
SLyK-53 Agent > ASSESS
SLyK-53 Agent > REMEDIATE
SLyK-53 Agent > HARDEN
SLyK-53 Agent > TRIAGE
SLyK-53 Agent > RUNBOOKS
ASSESS > IAM
ASSESS > EC2
ASSESS > S3
ASSESS > Security Hub
ASSESS > GuardDuty
REMEDIATE > IAM
REMEDIATE > S3
REMEDIATE > EC2
HARDEN > S3
HARDEN > EC2
HARDEN > IAM
TRIAGE > Security Hub
TRIAGE > SNS: Alert with remediation
Security Hub > EventBridge: CRITICAL/HIGH finding
EventBridge > TRIAGE: Auto-trigger
RUNBOOKS > ASSESS
RUNBOOKS > HARDEN
ASSESS > S3 Audit: Save results
TRIAGE > S3 Audit: Save triage logs
RUNBOOKS > S3 Audit: Save runbook results
```

---

## Diagram 2: SLyK-53 User Workflow (Sequence Diagram)

```
ISSO [icon: user, color: blue]
SLyK Agent [icon: aws-bedrock, color: purple]
ASSESS Lambda [icon: aws-lambda, color: green]
AWS Services [icon: aws, color: gray]
REMEDIATE Lambda [icon: aws-lambda, color: yellow]
S3 [icon: aws-simple-storage-service, color: green]

ISSO > SLyK Agent: "Assess my NIST compliance"
SLyK Agent > ASSESS Lambda: Invoke action group

loop [label: For each NIST control] {
  ASSESS Lambda > AWS Services: Check IAM, EC2, S3, CloudTrail...
  AWS Services > ASSESS Lambda: Configuration data
}

ASSESS Lambda > SLyK Agent: Pass/Fail results
SLyK Agent > ISSO: "8 passed, 2 failed: AC-2 (MFA), SC-28 (encryption)"
ISSO > SLyK Agent: "Fix the AC-2 MFA issue"
SLyK Agent > REMEDIATE Lambda: Invoke with control_id=AC-2
REMEDIATE Lambda > AWS Services: Identify users without MFA
AWS Services > REMEDIATE Lambda: User list
REMEDIATE Lambda > SLyK Agent: CLI scripts + affected users
SLyK Agent > ISSO: "3 users need MFA. Apply fix?"
ISSO > SLyK Agent: "Yes, apply"
SLyK Agent > REMEDIATE Lambda: Execute remediation
REMEDIATE Lambda > AWS Services: Apply MFA configuration
REMEDIATE Lambda > S3: Save audit log
REMEDIATE Lambda > SLyK Agent: Fix applied
SLyK Agent > ISSO: "✅ MFA enabled for 3 users"
```

---

## Diagram 3: Proactive Alerting Flow (Sequence Diagram)

```
Security Hub [icon: aws-security-hub, color: red]
EventBridge [icon: aws-eventbridge, color: orange]
TRIAGE Lambda [icon: aws-lambda, color: red]
Bedrock AI [icon: aws-bedrock, color: purple]
SNS [icon: aws-sns, color: red]
ISSO [icon: user, color: blue]
S3 [icon: aws-simple-storage-service, color: green]

Security Hub > EventBridge: CRITICAL finding detected
EventBridge > TRIAGE Lambda: Auto-trigger (no human action)

TRIAGE Lambda > TRIAGE Lambda: Map finding to NIST control
TRIAGE Lambda > TRIAGE Lambda: Generate remediation scripts
TRIAGE Lambda > Bedrock AI: "Assess risk of this finding"
Bedrock AI > TRIAGE Lambda: AI risk assessment

par [label: Simultaneous notifications] {
  TRIAGE Lambda > SNS: Send alert email with finding + fix + AI analysis
  TRIAGE Lambda > S3: Save triage log for audit
}

SNS > ISSO: 🔴 "CRITICAL: S3 bucket publicly accessible. Fix: apply public access block"
ISSO > ISSO: Reviews alert and remediation
```

---

## Diagram 4: ISSO Runbook Execution Flow

```
ISSO [icon: user, color: blue]
SLyK Agent [icon: aws-bedrock, color: purple]
RUNBOOKS Lambda [icon: aws-lambda, color: blue]
IAM [icon: aws-iam, color: orange]
S3 Check [icon: aws-simple-storage-service, color: green]
Security Hub [icon: aws-security-hub, color: red]
GuardDuty [icon: aws-guardduty, color: blue]
CloudTrail [icon: aws-cloudtrail, color: gray]
Bedrock AI [icon: aws-bedrock, color: purple]
S3 Audit [icon: aws-simple-storage-service, color: green]

ISSO > SLyK Agent: "Run the monthly compliance check"
SLyK Agent > RUNBOOKS Lambda: Execute monthly_compliance

RUNBOOKS Lambda > IAM: Step 1: NIST Control Assessment
RUNBOOKS Lambda > S3 Check: Check encryption, versioning
RUNBOOKS Lambda > CloudTrail: Verify logging active

RUNBOOKS Lambda > Security Hub: Step 2: Import findings
RUNBOOKS Lambda > GuardDuty: Step 3: Check threat detection

RUNBOOKS Lambda > Bedrock AI: Step 4: Generate executive summary
Bedrock AI > RUNBOOKS Lambda: AI summary

RUNBOOKS Lambda > S3 Audit: Step 5: Save compliance report

RUNBOOKS Lambda > SLyK Agent: Complete results
SLyK Agent > ISSO: "Monthly compliance complete:\n✅ 5 controls passed\n❌ 2 failed\n⚠️ 3 Security Hub findings\nReport saved to S3"
```

---

## Diagram 5: GRCP Platform Family

```
GRCP Platform [icon: shield, color: blue] {
  SAELAR-53 [icon: aws-ec2, color: blue, label: "SAELAR-53\nFull GRC Platform\nStreamlit on EC2\nPort 8484"]
  SOPRA [icon: aws-ec2, color: green, label: "SOPRA\nOn-Premise Assessment\nStreamlit on EC2\nPort 4444"]
  BeeKeeper [icon: aws-ec2, color: orange, label: "BeeKeeper\nContainer Security\nStreamlit on EC2\nPort 4445"]
  SLyK-53 [icon: aws-lambda, color: purple, label: "SLyK-53\nAgentic AI Assistant\nServerless\nBedrock + Lambda"]
}

AWS Console [icon: aws-console, color: orange]
EC2 GRC Titan [icon: aws-ec2, color: gray, label: "GRC_Titan EC2\n10.40.25.184"]

AWS Console > SLyK-53: Console-integrated (chat)
EC2 GRC Titan > SAELAR-53: Hosts
EC2 GRC Titan > SOPRA: Hosts
EC2 GRC Titan > BeeKeeper: Hosts
SLyK-53 -- SAELAR-53: Shared assessment logic
```
