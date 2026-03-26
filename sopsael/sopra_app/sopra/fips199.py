"""
SOPRA FIPS 199 Security Categorization & NIST 800-53 Baseline Mapping
=====================================================================
Maps each SOPRA control to its minimum required NIST 800-53 baseline:
  - Low:      Core/foundational controls required for ALL systems
  - Moderate: Additional controls for systems processing sensitive data
  - High:     Full control set for mission-critical / national-security systems

Selection logic:
  - If user selects "Low"      → only controls tagged "Low" are assessed
  - If user selects "Moderate"  → controls tagged "Low" + "Moderate"
  - If user selects "High"      → all controls (Low + Moderate + High)

Control counts:
  - Low:      75 controls
  - Moderate: 155 controls  (75 Low + 80 Moderate-only)
  - High:     200 controls  (155 Moderate + 45 High-only)
"""

# Minimum baseline level required for each control
# "Low" = assessed at all levels; "Moderate" = Moderate+High only; "High" = High only
BASELINE_MAP = {
    # ── Active Directory Security ──
    "AD-001": "Low",       # Domain Admin Account Security — fundamental AC-2
    "AD-002": "Moderate",  # Service Account Management — gMSA is moderate+
    "AD-003": "Low",       # Group Policy Security — baseline CM-6
    "AD-004": "Low",       # Password Policy Enforcement — core IA-5
    "AD-005": "High",      # Kerberos Configuration — advanced crypto
    "AD-006": "High",      # LDAP Signing & Channel Binding — advanced hardening
    "AD-007": "Moderate",  # AdminSDHolder Protection — moderate privilege mgmt
    "AD-008": "High",      # Trust Relationship Security — complex AD environments
    "AD-009": "Moderate",  # Replication Security — moderate infrastructure
    "AD-010": "Low",       # Audit Policy Configuration — core AU-2

    # ── Network Infrastructure ──
    "NET-001": "Low",      # Network Segmentation — foundational SC-7
    "NET-002": "Low",      # Firewall Rule Review — baseline perimeter
    "NET-003": "Moderate", # IDS/IPS Configuration — moderate detection
    "NET-004": "Low",      # VPN Security — basic remote access
    "NET-005": "Moderate", # Switch Port Security — moderate LAN hardening
    "NET-006": "Moderate", # Router ACL Review — moderate network control
    "NET-007": "Moderate", # Network Device Hardening — moderate CM-6
    "NET-008": "Low",      # Wireless Security — baseline wireless
    "NET-009": "High",     # DNS Security — DNSSEC is high baseline
    "NET-010": "Low",      # Network Monitoring — core SI-4

    # ── Endpoint Security ──
    "END-001": "Low",      # Endpoint Protection Platform — foundational AV
    "END-002": "Low",      # Patch Management — core SI-2
    "END-003": "Moderate", # Host-based Firewall — moderate endpoint
    "END-004": "High",     # Application Whitelisting — high baseline CM-7(5)
    "END-005": "Moderate", # Local Admin Rights — moderate AC-6
    "END-006": "Moderate", # USB/Removable Media Control — moderate MP-7
    "END-007": "Moderate", # Full Disk Encryption — moderate SC-28
    "END-008": "High",     # EDR/XDR Deployment — advanced detection
    "END-009": "High",     # Secure Boot Configuration — high integrity
    "END-010": "Low",      # Endpoint Logging — core AU-2

    # ── Physical Security ──
    "PHY-001": "Low",      # Physical Access Control — foundational PE-3
    "PHY-002": "Low",      # Visitor Management — baseline PE-8
    "PHY-003": "Moderate", # Surveillance Systems — moderate PE-6
    "PHY-004": "Low",      # Server Room Access — core PE-3
    "PHY-005": "Moderate", # Environmental Controls — moderate PE-14
    "PHY-006": "High",     # Cable Management — high PE-9
    "PHY-007": "Moderate", # Equipment Disposal — moderate MP-6
    "PHY-008": "High",     # Emergency Power — high CP-8
    "PHY-009": "High",     # Fire Suppression — high PE-13
    "PHY-010": "Moderate", # Physical Security Logging — moderate PE-6

    # ── Server Security ──
    "SRV-001": "Low",      # Server Hardening Baseline — core CM-6
    "SRV-002": "Low",      # Unnecessary Services Disabled — baseline CM-7
    "SRV-003": "Moderate", # Database Security — moderate data protection
    "SRV-004": "Moderate", # File Server Permissions — moderate AC-3
    "SRV-005": "Moderate", # Web Server Security — moderate web hardening
    "SRV-006": "High",     # Email Server Security — high comms protection
    "SRV-007": "Low",      # Backup Server Protection — core CP-9
    "SRV-008": "High",     # Virtualization Security — high isolation
    "SRV-009": "High",     # Server Certificate Management — high PKI
    "SRV-010": "Low",      # Server Access Logging — core AU-2

    # ── Data Protection ──
    "DAT-001": "Low",      # Data Classification — foundational RA-2
    "DAT-002": "Moderate", # Data Loss Prevention — moderate AC-4
    "DAT-003": "Moderate", # Encryption at Rest — moderate SC-28
    "DAT-004": "Low",      # Encryption in Transit — baseline SC-8
    "DAT-005": "Low",      # Backup & Recovery — core CP-9
    "DAT-006": "Moderate", # Data Retention Policy — moderate SI-12
    "DAT-007": "Moderate", # Sensitive Data Handling — moderate MP-4
    "DAT-008": "High",     # Database Encryption — high SC-28
    "DAT-009": "High",     # Key Management — high SC-12(1)
    "DAT-010": "Low",      # Data Access Auditing — core AU-2

    # ── Identity & Access Management ──
    "IAM-001": "Low",      # Multi-Factor Authentication — baseline IA-2
    "IAM-002": "Moderate", # Privileged Access Management — moderate AC-6(2)
    "IAM-003": "Low",      # Role-Based Access Control — core AC-3
    "IAM-004": "Low",      # Account Lifecycle Management — baseline AC-2
    "IAM-005": "Moderate", # Password Vault/Management — moderate IA-5(7)
    "IAM-006": "Moderate", # Session Management — moderate AC-12
    "IAM-007": "Moderate", # Access Review Process — moderate CA-7
    "IAM-008": "High",     # Separation of Duties — high AC-5
    "IAM-009": "Low",      # Remote Access Security — baseline AC-17
    "IAM-010": "High",     # Identity Federation — high IA-8(4)

    # ── Monitoring & Logging ──
    "MON-001": "Low",      # SIEM Implementation — foundational SI-4
    "MON-002": "Low",      # Log Collection & Aggregation — core AU-3
    "MON-003": "Moderate", # Log Retention & Protection — moderate AU-9
    "MON-004": "Moderate", # Real-time Alerting — moderate SI-4(5)
    "MON-005": "High",     # Security Event Correlation — high AU-6(5)
    "MON-006": "High",     # Threat Detection Rules — high SI-4
    "MON-007": "High",     # Network Traffic Analysis — high deep inspection
    "MON-008": "High",     # User Behavior Analytics — high AC-2(12)
    "MON-009": "Moderate", # Incident Response Integration — moderate IR-4
    "MON-010": "Moderate", # Compliance Reporting — moderate CA-7
    # -- Vulnerability Management --
    "VM-001": "Low",     # Vulnerability Scanning Program -- RA-5
    "VM-002": "Low",     # Vulnerability Remediation SLAs -- RA-5(5)
    "VM-003": "Low",     # Asset Discovery & Inventory -- CM-8
    "VM-004": "Moderate",# Penetration Testing -- CA-8
    "VM-005": "Moderate",# Threat Intelligence Integration -- RA-5(6)
    "VM-006": "Moderate",# Web Application Scanning -- RA-5
    "VM-007": "High",    # Container Image Scanning -- RA-5
    "VM-008": "Moderate",# Database Vulnerability Assessment -- RA-5
    "VM-009": "Moderate",# Vulnerability Exception Management -- RA-3
    "VM-010": "Low",     # Zero-Day Response Procedure -- IR-4

    # -- Configuration Management --
    "CFG-001": "Low",     # Baseline Configuration Standards -- CM-2
    "CFG-002": "Low",     # Change Management Process -- CM-3
    "CFG-003": "Moderate",# Golden Image Management -- CM-2
    "CFG-004": "Low",     # Software Inventory Control -- CM-7(5)
    "CFG-005": "Low",     # Hardware Inventory Control -- CM-8
    "CFG-006": "Moderate",# Configuration Drift Detection -- CM-3(5)
    "CFG-007": "High",    # Firmware Security Management -- SI-7(9)
    "CFG-008": "Moderate",# Network Device Configuration Backup -- CM-2
    "CFG-009": "Low",     # Least Functionality Enforcement -- CM-7
    "CFG-010": "Moderate",# Security Configuration Compliance Reporting -- CA-7

    # -- Incident Response --
    "IR-001": "Low",     # Incident Response Plan -- IR-1
    "IR-002": "Low",     # Incident Response Team -- IR-2
    "IR-003": "Moderate",# Tabletop Exercises -- IR-3
    "IR-004": "Moderate",# Evidence Preservation & Chain of Custody -- IR-4
    "IR-005": "Low",     # Incident Classification & Prioritization -- IR-4
    "IR-006": "Low",     # External Reporting Requirements -- IR-6
    "IR-007": "High",    # Forensic Readiness -- IR-4
    "IR-008": "High",    # Automated Incident Response -- IR-4(1)
    "IR-009": "Moderate",# Lessons Learned Process -- IR-4(8)
    "IR-010": "Low",     # Incident Communication Plan -- IR-6

    # -- Contingency Planning --
    "CP-001": "Low",     # Business Continuity Plan -- CP-1
    "CP-002": "Low",     # Disaster Recovery Plan -- CP-2
    "CP-003": "Moderate",# DR Testing & Exercises -- CP-4
    "CP-004": "Low",     # Backup Verification & Testing -- CP-9
    "CP-005": "High",    # Alternate Processing Site -- CP-7
    "CP-006": "Moderate",# System Recovery Prioritization -- CP-2(8)
    "CP-007": "Moderate",# Data Backup Offsite Storage -- CP-6
    "CP-008": "High",    # Telecommunications Redundancy -- CP-8
    "CP-009": "Moderate",# Essential Personnel Identification -- CP-2
    "CP-010": "Moderate",# Contingency Plan Training -- CP-3

    # -- Security Awareness & Training --
    "SAT-001": "Low",     # Security Awareness Program -- AT-2
    "SAT-002": "Low",     # Phishing Simulation Program -- AT-2(1)
    "SAT-003": "Moderate",# Role-Based Security Training -- AT-3
    "SAT-004": "Moderate",# Social Engineering Awareness -- AT-2
    "SAT-005": "Low",     # Personnel Screening -- PS-3
    "SAT-006": "Low",     # Personnel Termination Procedures -- PS-4
    "SAT-007": "Low",     # Access Agreements -- PS-6
    "SAT-008": "Moderate",# Insider Threat Awareness -- AT-2(2)
    "SAT-009": "High",    # Security Training Effectiveness Measurement -- AT-4
    "SAT-010": "Moderate",# Third-Party Personnel Security -- PS-7

    # -- Application Security --
    "APP-001": "Moderate",# Secure Software Development Lifecycle -- SA-3
    "APP-002": "Moderate",# Static Application Security Testing -- SA-11
    "APP-003": "Moderate",# Dynamic Application Security Testing -- SA-11(8)
    "APP-004": "Moderate",# Software Composition Analysis -- SA-12
    "APP-005": "Moderate",# Web Application Firewall -- SC-7
    "APP-006": "High",    # API Security -- SC-7
    "APP-007": "High",    # Secure Code Review -- SA-11(4)
    "APP-008": "Low",     # Input Validation -- SI-10
    "APP-009": "Low",     # Secrets Management -- IA-5
    "APP-010": "Low",     # Security Headers & TLS Configuration -- SC-8

    # -- Supply Chain Risk Management --
    "SCR-001": "Moderate",# Vendor Risk Assessment Program -- SA-9
    "SCR-002": "Moderate",# Software Bill of Materials -- SR-4
    "SCR-003": "Low",     # Third-Party Software Patching -- SI-2
    "SCR-004": "Moderate",# Supplier Security Requirements -- SA-4
    "SCR-005": "High",    # Component Authenticity Verification -- SR-4(3)
    "SCR-006": "Moderate",# Supply Chain Incident Notification -- IR-6(3)
    "SCR-007": "Low",     # Vendor Access Controls -- AC-2(12)
    "SCR-008": "High",    # Cloud Service Provider Assessment -- SA-9
    "SCR-009": "Low",     # End-of-Life Technology Management -- SA-22
    "SCR-010": "High",    # Open Source Software Governance -- SR-4

    # -- Governance & Compliance --
    "GOV-001": "Low",     # Information Security Policy -- PL-1
    "GOV-002": "Low",     # Risk Management Framework -- PM-9
    "GOV-003": "Low",     # Security Assessment & Authorization -- CA-2
    "GOV-004": "Moderate",# Continuous Monitoring Program -- CA-7
    "GOV-005": "Low",     # System Security Plan -- PL-2
    "GOV-006": "Moderate",# Regulatory Compliance Tracking -- PM-1
    "GOV-007": "Moderate",# Security Metrics & Reporting -- PM-6
    "GOV-008": "High",    # Security Architecture Review -- PL-8
    "GOV-009": "Moderate",# Interconnection Security Agreements -- CA-3
    "GOV-010": "Moderate",# Privacy Impact Assessment -- PT-1

    # -- Wireless & Mobile Security --
    "WMS-001": "Moderate",# Mobile Device Management -- AC-19
    "WMS-002": "Moderate",# BYOD Security Policy -- AC-19
    "WMS-003": "Low",     # Wireless Network Security -- SC-8
    "WMS-004": "Moderate",# Rogue Wireless Detection -- SI-4
    "WMS-005": "Low",     # Guest Wireless Isolation -- SC-7
    "WMS-006": "High",    # Mobile Application Security -- CM-7(5)
    "WMS-007": "Low",     # Mobile Device Encryption -- SC-28
    "WMS-008": "Low",     # Lost/Stolen Device Response -- MP-6
    "WMS-009": "High",    # Bluetooth Security -- AC-18
    "WMS-010": "High",    # Wireless Penetration Testing -- CA-8

    # -- Virtualization & Container Security --
    "VCS-001": "Low",     # Hypervisor Hardening -- CM-6
    "VCS-002": "Moderate",# VM Isolation & Segmentation -- SC-7
    "VCS-003": "High",    # Container Runtime Security -- SC-39
    "VCS-004": "High",    # Container Registry Security -- SI-7
    "VCS-005": "Moderate",# VM Snapshot Management -- MP-4
    "VCS-006": "High",    # Kubernetes RBAC -- AC-3
    "VCS-007": "Moderate",# Virtual Network Security -- SC-7
    "VCS-008": "Moderate",# Container Secrets Management -- IA-5
    "VCS-009": "Low",     # VM Template Security -- CM-2
    "VCS-010": "High",    # Container Network Policies -- SC-7

    # -- Email & Communications Security --
    "ECS-001": "Low",     # Email Gateway Protection -- SI-8
    "ECS-002": "Low",     # DMARC/DKIM/SPF Implementation -- SC-8
    "ECS-003": "Moderate",# Email Encryption -- SC-8
    "ECS-004": "Moderate",# Phishing Protection -- SI-8
    "ECS-005": "Moderate",# Email Data Loss Prevention -- SC-7
    "ECS-006": "Moderate",# Unified Communications Security -- SC-8
    "ECS-007": "High",    # Email Retention & Archival -- AU-11
    "ECS-008": "Low",     # Secure File Transfer -- SC-8
    "ECS-009": "Moderate",# Collaboration Platform Security -- AC-3
    "ECS-010": "Low",     # External Email Marking -- SI-8

    # -- Cryptographic Controls --
    "CRY-001": "Low",     # Cryptographic Standards Policy -- SC-13
    "CRY-002": "Low",     # TLS Configuration -- SC-8
    "CRY-003": "Low",     # Certificate Lifecycle Management -- SC-17
    "CRY-004": "Moderate",# PKI Infrastructure Security -- SC-17
    "CRY-005": "Moderate",# Encryption Key Rotation -- SC-12
    "CRY-006": "High",    # Hardware Security Module Usage -- SC-12(1)
    "CRY-007": "Low",     # Deprecated Algorithm Remediation -- SC-13
    "CRY-008": "High",    # Crypto Agility Planning -- SC-13
    "CRY-009": "Moderate",# Disk Encryption Key Escrow -- SC-12
    "CRY-010": "High",    # Random Number Generation -- SC-13

}

# Ordered levels for comparison
_LEVEL_ORDER = {"Low": 0, "Moderate": 1, "High": 2}

# Human-readable descriptions
FIPS_DESCRIPTIONS = {
    "Low": {
        "label": "Low Impact",
        "description": "Loss of confidentiality, integrity, or availability would have a LIMITED adverse effect on operations, assets, or individuals.",
        "color": "#00d9ff",
        "icon": "🔵",
    },
    "Moderate": {
        "label": "Moderate Impact",
        "description": "Loss of confidentiality, integrity, or availability would have a SERIOUS adverse effect on operations, assets, or individuals.",
        "color": "#ffc107",
        "icon": "🟡",
    },
    "High": {
        "label": "High Impact",
        "description": "Loss of confidentiality, integrity, or availability would have a SEVERE or CATASTROPHIC adverse effect on operations, assets, or individuals.",
        "color": "#e94560",
        "icon": "🔴",
    },
}


def get_controls_for_level(level):
    """Return the set of control IDs that should be assessed at the given FIPS 199 level."""
    max_order = _LEVEL_ORDER.get(level, 2)
    return {cid for cid, min_level in BASELINE_MAP.items()
            if _LEVEL_ORDER.get(min_level, 0) <= max_order}


def get_control_count_by_level():
    """Return dict of level → control count."""
    return {
        "Low": len(get_controls_for_level("Low")),
        "Moderate": len(get_controls_for_level("Moderate")),
        "High": len(get_controls_for_level("High")),
    }


def get_baseline_for_control(control_id):
    """Return the minimum baseline level for a control ID."""
    return BASELINE_MAP.get(control_id, "High")
