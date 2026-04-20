# SAE GRC Tools — Snowflake Data Warehouse Schema and Implementation Roadmap

## U.S. Department of Commerce (DOC) | NOAA | NESDIS
### Office of Satellite and Product Operations (OSPO) — CyberSecurity Division (CSD)

**Version:** 1.0
**Date:** April 2026
**Prepared by:** SAE Team

---

## 1. Purpose

This document defines the Snowflake data warehouse schema for ingesting, storing, and analyzing security assessment data produced by the SAE GRC tools (SAELAR, SOPRA, BeeKeeper). It also provides a step-by-step implementation roadmap.

---

## 2. Data Sources

| Source | Data Type | Format in S3 | S3 Location | Volume |
|---|---|---|---|---|
| SAELAR | NIST 800-53 assessment results | JSON, CSV | `s3://saelarallpurpose/nist-assessments/json/` | ~50 KB per assessment |
| SAELAR | Assessment summary reports | Markdown | `s3://saelarallpurpose/nist-assessments/reports/` | ~10 KB per report |
| SAELAR | Security Hub findings | JSON | `s3://saelarallpurpose/nist-assessments/json/` | ~100 KB per import |
| SAELAR | SSP/POA&M/RAR documents | Markdown | `s3://saelarallpurpose/Documentation/` | ~20 KB per document |
| SOPRA | On-premise assessment results | JSON | `s3://saelarallpurpose/sopra-assessments/` | ~30 KB per assessment |
| BeeKeeper | Container scan results | JSON | `s3://saelarallpurpose/container-scans/` | ~50 KB per scan |
| CISA KEV | Known Exploited Vulnerabilities | JSON | `s3://saelarallpurpose/kev/` | ~1 MB (catalog) |

---

## 3. Database Schema

### 3.1 Database and Schema Structure

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS GRCP;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS GRCP.RAW;          -- Raw data from S3
CREATE SCHEMA IF NOT EXISTS GRCP.STAGING;      -- Transformed/cleaned data
CREATE SCHEMA IF NOT EXISTS GRCP.ANALYTICS;    -- Aggregated views for dashboards
CREATE SCHEMA IF NOT EXISTS GRCP.AUDIT;        -- Immutable audit trail
```

### 3.2 RAW Schema — Direct S3 Ingestion

```sql
-- =====================================================================
-- RAW.NIST_ASSESSMENTS — Raw NIST 800-53 assessment results from SAELAR
-- =====================================================================
CREATE TABLE GRCP.RAW.NIST_ASSESSMENTS (
    ingestion_id        VARCHAR(64) DEFAULT UUID_STRING(),
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    s3_key              VARCHAR(500),
    file_name           VARCHAR(255),
    raw_json            VARIANT,            -- Full JSON payload
    account_id          VARCHAR(20),
    assessment_date     TIMESTAMP_NTZ,
    family              VARCHAR(10),
    region              VARCHAR(20),
    total_controls      INTEGER,
    passed              INTEGER,
    failed              INTEGER,
    warnings            INTEGER,
    compliance_pct      FLOAT
);

-- =====================================================================
-- RAW.CONTROL_RESULTS — Individual control assessment results
-- =====================================================================
CREATE TABLE GRCP.RAW.CONTROL_RESULTS (
    result_id           VARCHAR(64) DEFAULT UUID_STRING(),
    assessment_id       VARCHAR(64),        -- FK to NIST_ASSESSMENTS
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    control_id          VARCHAR(20),        -- e.g., AC-2, IA-5
    control_name        VARCHAR(255),
    family              VARCHAR(10),        -- e.g., AC, AU, IA
    status              VARCHAR(20),        -- PASS, FAIL, WARNING, ERROR
    findings            ARRAY,              -- Array of finding strings
    recommendations     ARRAY,              -- Array of recommendation strings
    account_id          VARCHAR(20),
    assessment_date     TIMESTAMP_NTZ
);

-- =====================================================================
-- RAW.SECURITY_HUB_FINDINGS — AWS Security Hub aggregated findings
-- =====================================================================
CREATE TABLE GRCP.RAW.SECURITY_HUB_FINDINGS (
    finding_id          VARCHAR(64) DEFAULT UUID_STRING(),
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    aws_finding_id      VARCHAR(500),
    title               VARCHAR(1000),
    description         VARCHAR(5000),
    severity_label      VARCHAR(20),        -- CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL
    severity_score      FLOAT,
    resource_type       VARCHAR(255),
    resource_id         VARCHAR(500),
    resource_region     VARCHAR(20),
    account_id          VARCHAR(20),
    product_name        VARCHAR(255),       -- GuardDuty, Inspector, Macie, etc.
    compliance_status   VARCHAR(20),
    workflow_status     VARCHAR(20),
    first_observed      TIMESTAMP_NTZ,
    last_observed       TIMESTAMP_NTZ,
    raw_json            VARIANT
);

-- =====================================================================
-- RAW.RISK_ASSESSMENTS — Risk scores from Risk Calculator
-- =====================================================================
CREATE TABLE GRCP.RAW.RISK_ASSESSMENTS (
    risk_id             VARCHAR(64) DEFAULT UUID_STRING(),
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    finding_id          VARCHAR(64),
    title               VARCHAR(500),
    description         VARCHAR(5000),
    control_family      VARCHAR(10),
    control_id          VARCHAR(20),
    likelihood          VARCHAR(20),        -- VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH
    impact              VARCHAR(20),        -- NEGLIGIBLE, LOW, MODERATE, HIGH, VERY_HIGH
    risk_score          FLOAT,              -- 1-25 scale
    risk_level          VARCHAR(20),        -- LOW, MEDIUM, HIGH, CRITICAL
    remediation         VARCHAR(5000),
    status              VARCHAR(20),        -- OPEN, IN_PROGRESS, CLOSED
    threat_sources      ARRAY,
    mitre_techniques    ARRAY,
    ale                 FLOAT,              -- Annualized Loss Expectancy
    sle                 FLOAT,              -- Single Loss Expectancy
    aro                 FLOAT,              -- Annual Rate of Occurrence
    assessment_date     TIMESTAMP_NTZ
);

-- =====================================================================
-- RAW.SOPRA_ASSESSMENTS — On-premise assessment results from SOPRA
-- =====================================================================
CREATE TABLE GRCP.RAW.SOPRA_ASSESSMENTS (
    assessment_id       VARCHAR(64) DEFAULT UUID_STRING(),
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    s3_key              VARCHAR(500),
    raw_json            VARIANT,
    system_name         VARCHAR(255),
    assessment_date     TIMESTAMP_NTZ,
    total_controls      INTEGER,
    passed              INTEGER,
    failed              INTEGER,
    compliance_pct      FLOAT,
    data_source         VARCHAR(50)         -- CSV, STIG, CIS_BENCHMARK
);

-- =====================================================================
-- RAW.CONTAINER_SCANS — BeeKeeper container vulnerability scans
-- =====================================================================
CREATE TABLE GRCP.RAW.CONTAINER_SCANS (
    scan_id             VARCHAR(64) DEFAULT UUID_STRING(),
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    image_name          VARCHAR(500),
    scan_date           TIMESTAMP_NTZ,
    scanner             VARCHAR(20),        -- TRIVY, GRYPE
    total_critical      INTEGER,
    total_high          INTEGER,
    total_medium        INTEGER,
    total_low           INTEGER,
    total_info          INTEGER,
    raw_json            VARIANT
);

-- =====================================================================
-- RAW.CONTAINER_VULNS — Individual container vulnerabilities
-- =====================================================================
CREATE TABLE GRCP.RAW.CONTAINER_VULNS (
    vuln_id             VARCHAR(64) DEFAULT UUID_STRING(),
    scan_id             VARCHAR(64),        -- FK to CONTAINER_SCANS
    cve_id              VARCHAR(30),        -- e.g., CVE-2024-12345
    package_name        VARCHAR(255),
    installed_version   VARCHAR(100),
    fixed_version       VARCHAR(100),
    severity            VARCHAR(20),
    title               VARCHAR(1000),
    description         VARCHAR(5000),
    target              VARCHAR(500),       -- OS, library, etc.
    pkg_type            VARCHAR(50)
);

-- =====================================================================
-- RAW.CISA_KEV — Known Exploited Vulnerabilities catalog
-- =====================================================================
CREATE TABLE GRCP.RAW.CISA_KEV (
    kev_id              VARCHAR(64) DEFAULT UUID_STRING(),
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    cve_id              VARCHAR(30),
    vendor_project      VARCHAR(255),
    product             VARCHAR(255),
    vulnerability_name  VARCHAR(500),
    date_added          DATE,
    due_date            DATE,
    required_action     VARCHAR(2000),
    known_ransomware    VARCHAR(10),
    notes               VARCHAR(5000)
);

-- =====================================================================
-- RAW.COMPLIANCE_DOCUMENTS — SSP, POA&M, RAR metadata
-- =====================================================================
CREATE TABLE GRCP.RAW.COMPLIANCE_DOCUMENTS (
    doc_id              VARCHAR(64) DEFAULT UUID_STRING(),
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    s3_key              VARCHAR(500),
    document_type       VARCHAR(50),        -- SSP, POAM, RAR
    system_name         VARCHAR(255),
    generated_by        VARCHAR(100),
    generated_date      TIMESTAMP_NTZ,
    file_size_bytes     INTEGER
);
```

### 3.3 ANALYTICS Schema — Aggregated Views

```sql
-- =====================================================================
-- Compliance trend over time
-- =====================================================================
CREATE VIEW GRCP.ANALYTICS.COMPLIANCE_TREND AS
SELECT
    DATE_TRUNC('day', assessment_date) AS assessment_day,
    account_id,
    family,
    AVG(compliance_pct) AS avg_compliance,
    SUM(passed) AS total_passed,
    SUM(failed) AS total_failed,
    SUM(total_controls) AS total_controls
FROM GRCP.RAW.NIST_ASSESSMENTS
GROUP BY 1, 2, 3
ORDER BY 1 DESC;

-- =====================================================================
-- Control failure frequency (which controls fail most often)
-- =====================================================================
CREATE VIEW GRCP.ANALYTICS.CONTROL_FAILURE_FREQUENCY AS
SELECT
    control_id,
    control_name,
    family,
    COUNT(*) AS assessment_count,
    SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS fail_count,
    SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) AS pass_count,
    ROUND(SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100, 1) AS fail_rate_pct
FROM GRCP.RAW.CONTROL_RESULTS
GROUP BY 1, 2, 3
ORDER BY fail_count DESC;

-- =====================================================================
-- Security Hub severity distribution
-- =====================================================================
CREATE VIEW GRCP.ANALYTICS.SECURITYHUB_SEVERITY AS
SELECT
    DATE_TRUNC('day', last_observed) AS observation_day,
    severity_label,
    product_name,
    COUNT(*) AS finding_count
FROM GRCP.RAW.SECURITY_HUB_FINDINGS
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 4 DESC;

-- =====================================================================
-- Risk posture summary
-- =====================================================================
CREATE VIEW GRCP.ANALYTICS.RISK_POSTURE AS
SELECT
    DATE_TRUNC('day', assessment_date) AS assessment_day,
    risk_level,
    COUNT(*) AS finding_count,
    AVG(risk_score) AS avg_risk_score,
    SUM(ale) AS total_ale
FROM GRCP.RAW.RISK_ASSESSMENTS
GROUP BY 1, 2
ORDER BY 1 DESC;

-- =====================================================================
-- Container vulnerability trends
-- =====================================================================
CREATE VIEW GRCP.ANALYTICS.CONTAINER_VULN_TREND AS
SELECT
    DATE_TRUNC('day', scan_date) AS scan_day,
    image_name,
    total_critical,
    total_high,
    total_medium,
    total_low,
    (total_critical + total_high + total_medium + total_low) AS total_vulns
FROM GRCP.RAW.CONTAINER_SCANS
ORDER BY 1 DESC;

-- =====================================================================
-- KEV exposure — CVEs in our environment that are on the KEV list
-- =====================================================================
CREATE VIEW GRCP.ANALYTICS.KEV_EXPOSURE AS
SELECT
    k.cve_id,
    k.vulnerability_name,
    k.due_date,
    k.known_ransomware,
    k.required_action,
    cv.image_name,
    cv.package_name,
    cv.installed_version,
    cv.fixed_version,
    CASE WHEN k.due_date < CURRENT_DATE() THEN 'OVERDUE' ELSE 'WITHIN_SLA' END AS sla_status
FROM GRCP.RAW.CISA_KEV k
INNER JOIN GRCP.RAW.CONTAINER_VULNS cv ON k.cve_id = cv.cve_id
ORDER BY k.due_date;

-- =====================================================================
-- Executive dashboard — single-row current posture
-- =====================================================================
CREATE VIEW GRCP.ANALYTICS.EXECUTIVE_POSTURE AS
SELECT
    (SELECT MAX(assessment_date) FROM GRCP.RAW.NIST_ASSESSMENTS) AS last_assessment,
    (SELECT AVG(compliance_pct) FROM GRCP.RAW.NIST_ASSESSMENTS
     WHERE assessment_date = (SELECT MAX(assessment_date) FROM GRCP.RAW.NIST_ASSESSMENTS)) AS current_compliance_pct,
    (SELECT COUNT(*) FROM GRCP.RAW.SECURITY_HUB_FINDINGS WHERE severity_label = 'CRITICAL') AS critical_findings,
    (SELECT COUNT(*) FROM GRCP.RAW.SECURITY_HUB_FINDINGS WHERE severity_label = 'HIGH') AS high_findings,
    (SELECT COUNT(*) FROM GRCP.RAW.RISK_ASSESSMENTS WHERE status = 'OPEN' AND risk_level = 'CRITICAL') AS open_critical_risks,
    (SELECT COUNT(*) FROM GRCP.ANALYTICS.KEV_EXPOSURE WHERE sla_status = 'OVERDUE') AS overdue_kev_count,
    (SELECT COUNT(*) FROM GRCP.RAW.COMPLIANCE_DOCUMENTS WHERE document_type = 'SSP') AS total_ssps,
    (SELECT COUNT(*) FROM GRCP.RAW.COMPLIANCE_DOCUMENTS WHERE document_type = 'POAM') AS total_poams;
```

### 3.4 AUDIT Schema — Immutable History

```sql
-- =====================================================================
-- Assessment audit trail — append-only, never modified
-- =====================================================================
CREATE TABLE GRCP.AUDIT.ASSESSMENT_LOG (
    log_id              VARCHAR(64) DEFAULT UUID_STRING(),
    logged_at           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    event_type          VARCHAR(50),        -- ASSESSMENT_RUN, DOCUMENT_GENERATED, FINDING_IMPORTED
    source_system       VARCHAR(50),        -- SAELAR, SOPRA, BEEKEEPER
    account_id          VARCHAR(20),
    user_id             VARCHAR(100),
    details             VARIANT,
    s3_key              VARCHAR(500)
);
```

---

## 4. Data Ingestion Architecture

```
S3 (saelarallpurpose)
    ↓ Snowpipe (auto-ingest on new file)
Snowflake RAW schema
    ↓ Scheduled tasks (transform)
Snowflake STAGING schema
    ↓ Views
Snowflake ANALYTICS schema
    ↓
Dashboards (Streamlit / QuickSight)
```

### 4.1 Snowpipe Configuration

```sql
-- Create storage integration for S3
CREATE STORAGE INTEGRATION grcp_s3_integration
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'S3'
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::656443597515:role/saelar-role'
    STORAGE_ALLOWED_LOCATIONS = ('s3://saelarallpurpose/');

-- Create file format for JSON
CREATE FILE FORMAT GRCP.RAW.JSON_FORMAT
    TYPE = JSON
    STRIP_OUTER_ARRAY = TRUE
    IGNORE_UTF8_ERRORS = TRUE;

-- Create file format for CSV
CREATE FILE FORMAT GRCP.RAW.CSV_FORMAT
    TYPE = CSV
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL', 'null');

-- Create external stage
CREATE STAGE GRCP.RAW.S3_STAGE
    STORAGE_INTEGRATION = grcp_s3_integration
    URL = 's3://saelarallpurpose/'
    FILE_FORMAT = GRCP.RAW.JSON_FORMAT;

-- Create Snowpipe for auto-ingestion of assessments
CREATE PIPE GRCP.RAW.NIST_ASSESSMENT_PIPE
    AUTO_INGEST = TRUE
AS
COPY INTO GRCP.RAW.NIST_ASSESSMENTS (
    s3_key, file_name, raw_json, account_id, assessment_date,
    family, region, total_controls, passed, failed, warnings, compliance_pct
)
FROM (
    SELECT
        METADATA$FILENAME,
        SPLIT_PART(METADATA$FILENAME, '/', -1),
        $1,
        $1:summary:account_id::VARCHAR,
        TO_TIMESTAMP_NTZ($1:assessment_info:timestamp::VARCHAR),
        $1:assessment_info:scope::VARCHAR,
        $1:assessment_info:region::VARCHAR,
        $1:summary:total_controls::INTEGER,
        $1:summary:passed::INTEGER,
        $1:summary:failed::INTEGER,
        $1:summary:warnings::INTEGER,
        ROUND($1:summary:passed::FLOAT / NULLIF($1:summary:total_controls::FLOAT, 0) * 100, 1)
    FROM @GRCP.RAW.S3_STAGE/nist-assessments/json/
);
```

---

## 5. Cost Estimate

| Component | Monthly | Annual |
|---|---|---|
| Compute (X-Small, ~4 hrs/day) | $176 | $2,100 |
| Compute (ETL loading, ~1 hr/day) | $120 | $1,440 |
| Storage (50 GB compressed) | $1 | $14 |
| Snowpipe (serverless ingestion) | $5 | $60 |
| **Total Snowflake** | **~$302** | **~$3,614** |
| Integration development (one-time) | — | $10,000 |
| Dashboard buildout (one-time) | — | $7,000 |
| Training (one-time) | — | $3,000 |
| Buffer | — | $6,386 |
| **Year 1 Total** | — | **~$30,000** |

---

## 6. Implementation Roadmap

| Phase | Duration | Deliverables |
|---|---|---|
| Phase 1: Foundation | Week 1-2 | Snowflake account, database, schemas, tables, S3 integration |
| Phase 2: Ingestion | Week 3-4 | Snowpipe setup, initial data load, validation |
| Phase 3: Analytics | Week 5-6 | Views, stored procedures, data quality checks |
| Phase 4: Dashboards | Week 7-8 | Executive posture dashboard, compliance trending |
| Phase 5: Automation | Week 9-10 | Scheduled tasks, alerting, documentation |

---

## Annex A: Step-by-Step Implementation Instructions

### Phase 1: Foundation (Week 1-2)

**Step 1.1 — Provision Snowflake Account**

1. Log into the Snowflake console (or request account from your admin)
2. Select AWS us-east-1 region (same region as S3 bucket)
3. Select Standard Edition
4. Create an admin user for the SAE Team

**Step 1.2 — Create Database and Schemas**

Run in the Snowflake worksheet:

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS GRCP;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS GRCP.RAW;
CREATE SCHEMA IF NOT EXISTS GRCP.STAGING;
CREATE SCHEMA IF NOT EXISTS GRCP.ANALYTICS;
CREATE SCHEMA IF NOT EXISTS GRCP.AUDIT;

-- Create warehouses
CREATE WAREHOUSE IF NOT EXISTS GRCP_LOAD_WH
    WITH WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'ETL data loading';

CREATE WAREHOUSE IF NOT EXISTS GRCP_QUERY_WH
    WITH WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Dashboard queries and analysis';
```

**Step 1.3 — Create Tables**

Run all the `CREATE TABLE` statements from Section 3.2 above in the Snowflake worksheet.

**Step 1.4 — Set Up Resource Monitors**

```sql
-- Alert at 80%, suspend at 100% of monthly budget
CREATE RESOURCE MONITOR GRCP_BUDGET
    WITH CREDIT_QUOTA = 150          -- ~$300/month at $2/credit
    FREQUENCY = MONTHLY
    START_TIMESTAMP = CURRENT_TIMESTAMP()
    TRIGGERS
        ON 80 PERCENT DO NOTIFY
        ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE GRCP_LOAD_WH SET RESOURCE_MONITOR = GRCP_BUDGET;
ALTER WAREHOUSE GRCP_QUERY_WH SET RESOURCE_MONITOR = GRCP_BUDGET;
```

**Step 1.5 — Create Roles and Users**

```sql
-- Create roles
CREATE ROLE IF NOT EXISTS GRCP_ADMIN;
CREATE ROLE IF NOT EXISTS GRCP_ANALYST;
CREATE ROLE IF NOT EXISTS GRCP_VIEWER;

-- Grant privileges
GRANT ALL ON DATABASE GRCP TO ROLE GRCP_ADMIN;
GRANT USAGE ON DATABASE GRCP TO ROLE GRCP_ANALYST;
GRANT USAGE ON DATABASE GRCP TO ROLE GRCP_VIEWER;

GRANT ALL ON ALL SCHEMAS IN DATABASE GRCP TO ROLE GRCP_ADMIN;
GRANT USAGE ON SCHEMA GRCP.ANALYTICS TO ROLE GRCP_ANALYST;
GRANT USAGE ON SCHEMA GRCP.ANALYTICS TO ROLE GRCP_VIEWER;

GRANT SELECT ON ALL VIEWS IN SCHEMA GRCP.ANALYTICS TO ROLE GRCP_VIEWER;

-- Assign to SAE Team users
GRANT ROLE GRCP_ADMIN TO USER <your_admin_user>;
```

---

### Phase 2: Ingestion (Week 3-4)

**Step 2.1 — Create S3 Storage Integration**

```sql
CREATE STORAGE INTEGRATION grcp_s3_integration
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'S3'
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::656443597515:role/saelar-role'
    STORAGE_ALLOWED_LOCATIONS = ('s3://saelarallpurpose/');

-- Get the Snowflake IAM user and external ID for trust policy
DESC INTEGRATION grcp_s3_integration;
```

**Step 2.2 — Update IAM Trust Policy**

Take the `STORAGE_AWS_IAM_USER_ARN` and `STORAGE_AWS_EXTERNAL_ID` from Step 2.1 and update the `saelar-role` trust policy in the AWS Console:

```json
{
    "Effect": "Allow",
    "Principal": {
        "AWS": "<STORAGE_AWS_IAM_USER_ARN>"
    },
    "Action": "sts:AssumeRole",
    "Condition": {
        "StringEquals": {
            "sts:ExternalId": "<STORAGE_AWS_EXTERNAL_ID>"
        }
    }
}
```

**Step 2.3 — Create Stage and File Formats**

Run the `CREATE FILE FORMAT` and `CREATE STAGE` statements from Section 4.1.

**Step 2.4 — Test Manual Ingestion**

```sql
-- Test: list files in S3
LIST @GRCP.RAW.S3_STAGE/nist-assessments/json/;

-- Test: load one file manually
COPY INTO GRCP.RAW.NIST_ASSESSMENTS (s3_key, raw_json)
FROM (
    SELECT METADATA$FILENAME, $1
    FROM @GRCP.RAW.S3_STAGE/nist-assessments/json/
)
FILE_FORMAT = GRCP.RAW.JSON_FORMAT
ON_ERROR = 'CONTINUE';

-- Verify
SELECT COUNT(*) FROM GRCP.RAW.NIST_ASSESSMENTS;
SELECT * FROM GRCP.RAW.NIST_ASSESSMENTS LIMIT 5;
```

**Step 2.5 — Set Up Snowpipe for Auto-Ingestion**

Run the `CREATE PIPE` statement from Section 4.1.

Configure S3 event notification to trigger Snowpipe:

```bash
# In CloudShell — get the Snowpipe SQS ARN
# (shown in DESC PIPE output from Snowflake)

aws s3api put-bucket-notification-configuration \
    --bucket saelarallpurpose \
    --notification-configuration '{
        "QueueConfigurations": [{
            "QueueArn": "<SNOWPIPE_SQS_ARN>",
            "Events": ["s3:ObjectCreated:*"],
            "Filter": {
                "Key": {
                    "FilterRules": [
                        {"Name": "prefix", "Value": "nist-assessments/"},
                        {"Name": "suffix", "Value": ".json"}
                    ]
                }
            }
        }]
    }'
```

**Step 2.6 — Validate Auto-Ingestion**

1. Run a NIST assessment in SAELAR
2. Wait 2-3 minutes
3. Check Snowflake:

```sql
SELECT * FROM GRCP.RAW.NIST_ASSESSMENTS ORDER BY ingested_at DESC LIMIT 5;
```

---

### Phase 3: Analytics (Week 5-6)

**Step 3.1 — Create Analytics Views**

Run all the `CREATE VIEW` statements from Section 3.3.

**Step 3.2 — Validate Views**

```sql
-- Test each view
SELECT * FROM GRCP.ANALYTICS.COMPLIANCE_TREND LIMIT 10;
SELECT * FROM GRCP.ANALYTICS.CONTROL_FAILURE_FREQUENCY LIMIT 10;
SELECT * FROM GRCP.ANALYTICS.SECURITYHUB_SEVERITY LIMIT 10;
SELECT * FROM GRCP.ANALYTICS.RISK_POSTURE LIMIT 10;
SELECT * FROM GRCP.ANALYTICS.EXECUTIVE_POSTURE;
```

**Step 3.3 — Create Scheduled Transformation Task**

```sql
-- Flatten control results from raw JSON into CONTROL_RESULTS table
CREATE TASK GRCP.RAW.FLATTEN_CONTROL_RESULTS
    WAREHOUSE = GRCP_LOAD_WH
    SCHEDULE = 'USING CRON 0 */6 * * * America/New_York'   -- Every 6 hours
AS
INSERT INTO GRCP.RAW.CONTROL_RESULTS (
    assessment_id, control_id, control_name, family, status,
    findings, recommendations, account_id, assessment_date
)
SELECT
    a.ingestion_id,
    r.value:control_id::VARCHAR,
    r.value:control_name::VARCHAR,
    r.value:family::VARCHAR,
    r.value:status::VARCHAR,
    r.value:findings::ARRAY,
    r.value:recommendations::ARRAY,
    a.account_id,
    a.assessment_date
FROM GRCP.RAW.NIST_ASSESSMENTS a,
     LATERAL FLATTEN(input => a.raw_json:results) r
WHERE a.ingestion_id NOT IN (SELECT DISTINCT assessment_id FROM GRCP.RAW.CONTROL_RESULTS);

-- Enable the task
ALTER TASK GRCP.RAW.FLATTEN_CONTROL_RESULTS RESUME;
```

**Step 3.4 — Data Quality Checks**

```sql
-- Create a monitoring view
CREATE VIEW GRCP.ANALYTICS.DATA_QUALITY AS
SELECT
    'NIST_ASSESSMENTS' AS table_name,
    COUNT(*) AS row_count,
    MIN(ingested_at) AS earliest_record,
    MAX(ingested_at) AS latest_record,
    COUNT(DISTINCT account_id) AS distinct_accounts
FROM GRCP.RAW.NIST_ASSESSMENTS
UNION ALL
SELECT
    'CONTROL_RESULTS',
    COUNT(*),
    MIN(ingested_at),
    MAX(ingested_at),
    COUNT(DISTINCT account_id)
FROM GRCP.RAW.CONTROL_RESULTS
UNION ALL
SELECT
    'SECURITY_HUB_FINDINGS',
    COUNT(*),
    MIN(ingested_at),
    MAX(ingested_at),
    COUNT(DISTINCT account_id)
FROM GRCP.RAW.SECURITY_HUB_FINDINGS;
```

---

### Phase 4: Dashboards (Week 7-8)

**Step 4.1 — Executive Security Posture Dashboard**

Build a Streamlit dashboard that queries Snowflake:

```python
# pip install snowflake-connector-python streamlit plotly

import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px

conn = snowflake.connector.connect(
    account='<account>',
    user='<user>',
    password='<password>',
    warehouse='GRCP_QUERY_WH',
    database='GRCP',
    schema='ANALYTICS'
)

st.title("GRCP Executive Security Posture")

# Current posture
posture = pd.read_sql("SELECT * FROM EXECUTIVE_POSTURE", conn)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Compliance", f"{posture['CURRENT_COMPLIANCE_PCT'][0]:.1f}%")
col2.metric("Critical Findings", posture['CRITICAL_FINDINGS'][0])
col3.metric("Open Critical Risks", posture['OPEN_CRITICAL_RISKS'][0])
col4.metric("Overdue KEVs", posture['OVERDUE_KEV_COUNT'][0])

# Compliance trend
trend = pd.read_sql("SELECT * FROM COMPLIANCE_TREND ORDER BY assessment_day", conn)
fig = px.line(trend, x='ASSESSMENT_DAY', y='AVG_COMPLIANCE', color='FAMILY',
              title='Compliance Trend by Control Family')
st.plotly_chart(fig, use_container_width=True)
```

**Step 4.2 — Control Failure Analysis Dashboard**

```python
# Top failing controls
failures = pd.read_sql("SELECT * FROM CONTROL_FAILURE_FREQUENCY LIMIT 20", conn)
fig = px.bar(failures, x='CONTROL_ID', y='FAIL_RATE_PCT', color='FAMILY',
             title='Control Failure Rate (%)')
st.plotly_chart(fig, use_container_width=True)
```

---

### Phase 5: Automation (Week 9-10)

**Step 5.1 — Set Up Alerts**

```sql
-- Alert when compliance drops below 70%
CREATE ALERT GRCP.ANALYTICS.LOW_COMPLIANCE_ALERT
    WAREHOUSE = GRCP_QUERY_WH
    SCHEDULE = 'USING CRON 0 8 * * * America/New_York'     -- Daily at 8 AM
    IF (EXISTS (
        SELECT 1 FROM GRCP.RAW.NIST_ASSESSMENTS
        WHERE assessment_date > DATEADD('day', -1, CURRENT_TIMESTAMP())
        AND compliance_pct < 70
    ))
    THEN
        CALL SYSTEM$SEND_EMAIL(
            'grcp_notifications',
            'sae-team@noaa.gov',
            'GRCP Alert: Compliance Below 70%',
            'A recent NIST assessment scored below 70% compliance. Review immediately.'
        );

ALTER ALERT GRCP.ANALYTICS.LOW_COMPLIANCE_ALERT RESUME;
```

**Step 5.2 — Document the Deployment**

Update the CI/CD pipeline documentation to include Snowflake ingestion as part of the data flow.

**Step 5.3 — Training**

1. Snowflake worksheet basics (SQL queries)
2. Dashboard usage and interpretation
3. How to add new data sources
4. Cost monitoring via resource monitors

---

## Annex B: Key SQL Queries for Daily Use

### Current compliance by control family

```sql
SELECT family, AVG(compliance_pct) AS avg_compliance
FROM GRCP.RAW.NIST_ASSESSMENTS
WHERE assessment_date > DATEADD('month', -1, CURRENT_TIMESTAMP())
GROUP BY family ORDER BY avg_compliance;
```

### Controls that have never passed

```sql
SELECT control_id, control_name, family, COUNT(*) AS times_assessed
FROM GRCP.RAW.CONTROL_RESULTS
WHERE status = 'FAIL'
AND control_id NOT IN (SELECT control_id FROM GRCP.RAW.CONTROL_RESULTS WHERE status = 'PASS')
GROUP BY 1, 2, 3 ORDER BY times_assessed DESC;
```

### Month-over-month compliance improvement

```sql
SELECT
    DATE_TRUNC('month', assessment_date) AS month,
    AVG(compliance_pct) AS avg_compliance,
    LAG(AVG(compliance_pct)) OVER (ORDER BY DATE_TRUNC('month', assessment_date)) AS prev_month,
    AVG(compliance_pct) - LAG(AVG(compliance_pct)) OVER (ORDER BY DATE_TRUNC('month', assessment_date)) AS improvement
FROM GRCP.RAW.NIST_ASSESSMENTS
GROUP BY 1 ORDER BY 1;
```

### Open critical risks with remediation

```sql
SELECT control_id, title, risk_score, risk_level, remediation
FROM GRCP.RAW.RISK_ASSESSMENTS
WHERE status = 'OPEN' AND risk_level IN ('CRITICAL', 'HIGH')
ORDER BY risk_score DESC;
```

### Container images with most vulnerabilities

```sql
SELECT image_name, total_critical, total_high,
       (total_critical + total_high) AS urgent_total
FROM GRCP.RAW.CONTAINER_SCANS
WHERE scan_date > DATEADD('week', -1, CURRENT_TIMESTAMP())
ORDER BY urgent_total DESC LIMIT 10;
```
