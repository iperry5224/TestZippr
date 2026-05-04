# CSTA - Cyber Security Tools Analysis
## Architecture Overview & Standard Operating Procedures

**Document Version:** 1.0  
**Last Updated:** May 4, 2026  
**Classification:** Internal Use  
**Account ID:** 656443597515 (nesdis-ncis-ospocsta-5006)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Security Controls](#security-controls)
6. [Standard Operating Procedures](#standard-operating-procedures)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Appendix](#appendix)

---

## Executive Summary

CSTA (Cyber Security Tools Analysis) is an agentic AI-based security assessment platform built on AWS serverless architecture. It provides Information System Security Officers (ISSOs) with automated NIST 800-53 compliance monitoring, AI-powered security analysis, and remediation guidance through an intuitive web dashboard.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Automated Compliance** | Real-time NIST 800-53 control assessment via AWS Security Hub |
| **AI Security Assistant** | Natural language queries powered by Amazon Bedrock |
| **Remediation Guidance** | Pre-built scripts for common security misconfigurations |
| **Resource Inventory** | Live AWS resource tracking with compliance status |
| **Knowledge Base** | Curated security documentation and semantic search |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CSTA Architecture                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐   │
│  │   Browser   │────▶│ CloudFront  │────▶│  S3 (Static Dashboard)      │   │
│  │   (ISSO)    │     │   (CDN)     │     │  slyk-view-656443597515-*   │   │
│  └─────────────┘     └─────────────┘     └─────────────────────────────┘   │
│         │                                                                   │
│         │ API Calls                                                         │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        API Gateway (REST)                            │   │
│  │                    zc06lwmk4j.execute-api.us-east-1                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                    │                    │                         │
│         ▼                    ▼                    ▼                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │   Lambda    │     │   Lambda    │     │   Lambda    │                   │
│  │ securityhub │     │  inventory  │     │   assess    │                   │
│  └─────────────┘     └─────────────┘     └─────────────┘                   │
│         │                    │                    │                         │
│         ▼                    ▼                    ▼                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │  Security   │     │  S3, EC2,   │     │   Config    │                   │
│  │    Hub      │     │  IAM, RDS   │     │   Rules     │                   │
│  └─────────────┘     └─────────────┘     └─────────────┘                   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Amazon Bedrock                                │   │
│  │  ┌─────────────────┐     ┌─────────────────────────────────────┐    │   │
│  │  │  Bedrock Agent  │────▶│  Knowledge Base (NIST 800-53 Docs)  │    │   │
│  │  │  SLyK-53        │     │  Security Documentation             │    │   │
│  │  └─────────────────┘     └─────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React + TypeScript + Vite | Interactive dashboard UI |
| **CDN** | Amazon CloudFront | Global content delivery, HTTPS |
| **Static Hosting** | Amazon S3 | Dashboard file storage |
| **API** | Amazon API Gateway | REST API endpoints |
| **Compute** | AWS Lambda | Serverless business logic |
| **AI/ML** | Amazon Bedrock | Foundation models, agents, knowledge bases |
| **Security Data** | AWS Security Hub | Aggregated security findings |
| **Configuration** | AWS Config | Resource compliance rules |

---

## Component Details

### 1. CSTA Dashboard (Frontend)

**Location:** `s3://slyk-view-656443597515-us-east-1/`  
**Distribution:** CloudFront (E3STZQQDVPKXS9)  
**URL:** `https://dymaxfdlmvkiy.cloudfront.net`

#### Dashboard Pages

| Page | Function |
|------|----------|
| **Dashboard** | Compliance score, control status, alerts feed |
| **Controls** | NIST 800-53 control details and assessment status |
| **Security Hub** | AWS Security Hub findings integration |
| **Ask SLyK** | AI chat interface for security queries |
| **Inventory** | AWS resource inventory with compliance status |
| **Remediation** | Fix scripts for security misconfigurations |
| **Reports** | Compliance reports and exports |
| **Knowledge Base** | Security documentation and requirements |
| **Settings** | Configuration and tenant settings |

### 2. API Gateway

**Endpoint:** `https://zc06lwmk4j.execute-api.us-east-1.amazonaws.com/prod`

| Route | Method | Lambda | Description |
|-------|--------|--------|-------------|
| `/securityhub` | GET | slyk-securityhub-findings | Security Hub findings |
| `/inventory` | GET | slyk-inventory | AWS resource inventory |
| `/assess` | POST | slyk-assess | Run control assessment |

### 3. Lambda Functions

#### slyk-securityhub-findings
- **Runtime:** Python 3.11
- **Memory:** 256 MB
- **Timeout:** 60 seconds
- **Purpose:** Fetches and aggregates Security Hub findings by NIST control

#### slyk-inventory
- **Runtime:** Python 3.11
- **Memory:** 256 MB
- **Timeout:** 60 seconds
- **Purpose:** Lists AWS resources (S3, EC2, IAM, RDS) with compliance status

### 4. Amazon Bedrock Agent

**Agent Name:** New_SLyK-53-Security-Assistant  
**Foundation Model:** Claude (Anthropic)

#### Action Groups

| Action Group | Function |
|--------------|----------|
| assess_controls | Run NIST 800-53 control assessments |
| get_findings | Retrieve security findings by control |
| generate_report | Create compliance reports |

#### Knowledge Base

- NIST SP 800-53 Rev 5 control catalog
- AWS security best practices
- Organizational security policies

---

## Data Flow

### 1. Dashboard Load Sequence

```
User Browser
    │
    ▼
CloudFront (CDN)
    │
    ▼
S3 Bucket (React App)
    │
    ▼
Browser renders dashboard
    │
    ▼
API calls to API Gateway
    │
    ▼
Lambda functions execute
    │
    ▼
Data returned to dashboard
```

### 2. Security Assessment Flow

```
ISSO initiates assessment
    │
    ▼
API Gateway receives request
    │
    ▼
Lambda invokes Security Hub API
    │
    ▼
Findings aggregated by NIST control
    │
    ▼
Compliance score calculated
    │
    ▼
Results displayed in dashboard
```

### 3. AI Query Flow

```
ISSO asks question in chat
    │
    ▼
Request sent to Bedrock Agent
    │
    ▼
Agent queries Knowledge Base
    │
    ▼
Agent may invoke Action Groups
    │
    ▼
Response generated and returned
    │
    ▼
Answer displayed in chat
```

---

## Security Controls

### Authentication & Authorization

| Control | Implementation |
|---------|----------------|
| **User Authentication** | AWS IAM / Cognito (optional) |
| **API Authorization** | IAM roles, API keys |
| **Dashboard Access** | CloudFront signed URLs (optional) |

### Data Protection

| Control | Implementation |
|---------|----------------|
| **Encryption in Transit** | TLS 1.2+ via CloudFront/API Gateway |
| **Encryption at Rest** | S3 SSE, Lambda environment encryption |
| **Secrets Management** | AWS Secrets Manager (API keys) |

### Network Security

| Control | Implementation |
|---------|----------------|
| **DDoS Protection** | AWS Shield (CloudFront) |
| **WAF** | AWS WAF (optional) |
| **VPC** | Lambda in VPC (optional for private resources) |

### Logging & Monitoring

| Control | Implementation |
|---------|----------------|
| **API Logging** | CloudWatch Logs, API Gateway access logs |
| **Lambda Logging** | CloudWatch Logs |
| **CloudFront Logging** | S3 access logs |
| **Audit Trail** | AWS CloudTrail |

---

## Standard Operating Procedures

### SOP-001: Daily Security Review

**Purpose:** Review daily security posture and address critical findings

**Frequency:** Daily (business days)

**Procedure:**

1. **Access Dashboard**
   - Navigate to CSTA dashboard
   - Review compliance score on main dashboard

2. **Check Critical Alerts**
   - Review alerts feed for CRITICAL/HIGH findings
   - Note any new findings since last review

3. **Review Security Hub**
   - Click "Security Hub" tab
   - Filter by severity: CRITICAL, HIGH
   - Document any new findings

4. **Take Action**
   - For CRITICAL findings: Initiate remediation within 24 hours
   - For HIGH findings: Create POA&M entry within 72 hours
   - Document actions in ticketing system

5. **Update Status**
   - Mark reviewed findings as acknowledged
   - Update POA&M tracker as needed

---

### SOP-002: Weekly Compliance Assessment

**Purpose:** Comprehensive weekly compliance review

**Frequency:** Weekly (Mondays)

**Procedure:**

1. **Run Full Assessment**
   - Navigate to Dashboard
   - Click "Refresh" to pull latest data
   - Document compliance score

2. **Review All Controls**
   - Go to "Controls" tab
   - Review each control family status
   - Note any degradation from previous week

3. **Inventory Check**
   - Go to "Inventory" tab
   - Verify resource counts match expectations
   - Check for non-compliant resources

4. **Generate Report**
   - Go to "Reports" tab
   - Generate weekly compliance report
   - Export as PDF for records

5. **Update Documentation**
   - Update SSP if control status changed
   - Update POA&M for any new findings
   - Brief leadership on significant changes

---

### SOP-003: Remediation Execution

**Purpose:** Execute remediation for security findings

**Frequency:** As needed

**Procedure:**

1. **Identify Finding**
   - Note the control ID and resource affected
   - Review finding details in Security Hub

2. **Get Remediation Script**
   - Go to "Remediation" tab
   - Find the relevant control
   - Copy the remediation script

3. **Test in Non-Production**
   - If possible, test script in dev/test environment
   - Verify script executes without errors

4. **Execute Remediation**
   - Run script against affected resource
   - Document execution time and results

5. **Verify Fix**
   - Wait for Security Hub to re-evaluate (up to 24 hours)
   - Or manually verify the configuration change
   - Confirm finding status changes to PASSED

6. **Document**
   - Update POA&M with closure date
   - Document remediation in change management system

---

### SOP-004: AI Assistant Usage

**Purpose:** Effectively use the AI security assistant

**Frequency:** As needed

**Procedure:**

1. **Access Chat**
   - Click "Ask SLyK" in sidebar

2. **Formulate Query**
   - Be specific about the control or topic
   - Include context (e.g., "for our S3 buckets")
   
   **Example queries:**
   - "What are the requirements for AC-2 Account Management?"
   - "How do I remediate public S3 bucket access?"
   - "Generate a POA&M entry for missing MFA"

3. **Review Response**
   - Verify AI response against official documentation
   - Note any citations provided

4. **Take Action**
   - Use AI guidance to inform decisions
   - Always verify critical actions with official sources

---

### SOP-005: Incident Response Integration

**Purpose:** Use CSTA during security incidents

**Frequency:** During incidents

**Procedure:**

1. **Initial Triage**
   - Check CSTA dashboard for related findings
   - Review affected resource in Inventory

2. **Gather Context**
   - Use "Ask SLyK" to understand relevant controls
   - Query: "What controls apply to [affected resource type]?"

3. **Check Compliance Status**
   - Review if affected resource was compliant
   - Document pre-incident compliance state

4. **Support Investigation**
   - Export relevant findings for incident report
   - Document timeline of compliance changes

5. **Post-Incident**
   - Update controls based on lessons learned
   - Add new remediation scripts if needed

---

## Troubleshooting Guide

### Issue: Dashboard Not Loading

**Symptoms:** Blank page, loading spinner indefinitely

**Resolution:**
1. Check CloudFront distribution status
2. Verify S3 bucket has index.html
3. Clear browser cache (Ctrl+Shift+R)
4. Check browser console for errors

### Issue: API Errors (500)

**Symptoms:** "Failed to fetch" errors in dashboard

**Resolution:**
1. Check Lambda function logs in CloudWatch
2. Verify Lambda has correct IAM permissions
3. Check API Gateway deployment status
4. Test API directly: `curl https://[api-url]/securityhub`

### Issue: No Security Hub Data

**Symptoms:** Dashboard shows 0 findings

**Resolution:**
1. Verify Security Hub is enabled in account
2. Check Security Hub standards are enabled
3. Verify Lambda role has `securityhub:GetFindings` permission
4. Wait 24 hours for initial findings to populate

### Issue: AI Chat Not Responding

**Symptoms:** Chat shows error or no response

**Resolution:**
1. Verify Bedrock agent is deployed and active
2. Check agent alias ID in settings
3. Verify IAM role has Bedrock permissions
4. Check Bedrock service quotas

---

## Appendix

### A. AWS Services Used

| Service | Purpose | Pricing Model |
|---------|---------|---------------|
| S3 | Static hosting | Per GB stored + requests |
| CloudFront | CDN | Per GB transferred |
| API Gateway | REST API | Per million requests |
| Lambda | Compute | Per invocation + duration |
| Security Hub | Findings | Per finding ingested |
| Bedrock | AI/ML | Per token processed |
| CloudWatch | Logging | Per GB ingested |

### B. IAM Permissions Required

**For Dashboard Deployment:**
- `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`
- `cloudfront:CreateInvalidation`

**For Lambda Functions:**
- `securityhub:GetFindings`, `securityhub:BatchGetSecurityControls`
- `s3:ListAllMyBuckets`, `s3:GetBucketEncryption`
- `ec2:DescribeInstances`, `ec2:DescribeSecurityGroups`
- `iam:ListUsers`, `iam:ListRoles`, `iam:GetLoginProfile`
- `rds:DescribeDBInstances`

**For Bedrock Agent:**
- `bedrock:InvokeAgent`
- `bedrock:Retrieve` (Knowledge Base)

### C. Contact Information

| Role | Contact |
|------|---------|
| System Owner | [TBD] |
| ISSO | [TBD] |
| Technical Lead | [TBD] |
| AWS Support | AWS Support Console |

### D. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-04 | CSTA Team | Initial release |

---

*This document is maintained as part of the CSTA project. For updates, contact the system administrator.*
