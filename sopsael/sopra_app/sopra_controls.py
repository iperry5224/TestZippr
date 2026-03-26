"""
SOPRA Controls Library
Detailed control definitions with remediation guidance for on-premise environments
SAE On-Premise Risk Assessment
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class ControlStatus(Enum):
    NOT_ASSESSED = "Not Assessed"
    PASSED = "Passed"
    FAILED = "Failed"
    NOT_APPLICABLE = "N/A"
    PARTIALLY_IMPLEMENTED = "Partially Implemented"

class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"

class ControlFamily(Enum):
    ACCESS_CONTROL = "Access Control"
    AUDIT_ACCOUNTABILITY = "Audit & Accountability"
    CONFIG_MANAGEMENT = "Configuration Management"
    CONTINGENCY_PLANNING = "Contingency Planning"
    IDENTIFICATION_AUTH = "Identification & Authentication"
    INCIDENT_RESPONSE = "Incident Response"
    MAINTENANCE = "Maintenance"
    MEDIA_PROTECTION = "Media Protection"
    PHYSICAL_ENVIRONMENTAL = "Physical & Environmental Protection"
    PLANNING = "Planning"
    PERSONNEL_SECURITY = "Personnel Security"
    RISK_ASSESSMENT = "Risk Assessment"
    SYSTEM_SERVICES = "System & Services Acquisition"
    SYSTEM_COMM_PROTECTION = "System & Communications Protection"
    SYSTEM_INFO_INTEGRITY = "System & Information Integrity"

@dataclass
class RemediationStep:
    """Individual remediation step"""
    step_number: int
    description: str
    command: Optional[str] = None
    script_type: Optional[str] = None  # powershell, bash, gpo, etc.
    estimated_time: Optional[str] = None
    requires_downtime: bool = False

@dataclass
class Control:
    """On-premise security control definition"""
    id: str
    name: str
    description: str
    family: ControlFamily
    category: str
    check_procedure: str
    expected_result: str
    remediation_steps: List[RemediationStep] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    nist_mapping: List[str] = field(default_factory=list)
    cis_mapping: Optional[str] = None
    default_severity: Severity = Severity.MEDIUM

# ============================================================================
# ACTIVE DIRECTORY CONTROLS
# ============================================================================

AD_CONTROLS = {
    "AD-001": Control(
        id="AD-001",
        name="Domain Admin Account Security",
        description="Domain Admin accounts should be limited in number, regularly audited, and protected with strong authentication.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Active Directory Security",
        check_procedure="""
1. Open Active Directory Users and Computers
2. Navigate to the Domain Admins group
3. Review membership list
4. Verify each member has a documented business justification
5. Check if accounts have MFA enabled
6. Review last logon times for dormant accounts
        """,
        expected_result="Fewer than 5 Domain Admin accounts, all with documented justification and MFA enabled",
        remediation_steps=[
            RemediationStep(1, "Audit current Domain Admin membership", 
                          "Get-ADGroupMember -Identity 'Domain Admins' | Select-Object Name, SamAccountName, Enabled | Export-CSV DomainAdmins.csv",
                          "powershell", "5 minutes"),
            RemediationStep(2, "Remove unnecessary accounts from Domain Admins",
                          "Remove-ADGroupMember -Identity 'Domain Admins' -Members '<username>' -Confirm:$false",
                          "powershell", "2 minutes per account"),
            RemediationStep(3, "Create dedicated admin accounts (separate from daily use accounts)",
                          None, None, "30 minutes"),
            RemediationStep(4, "Implement Privileged Access Workstations (PAWs) for admin tasks",
                          None, None, "4-8 hours", True),
        ],
        references=["Microsoft Tier Model", "NIST SP 800-53 AC-2", "CIS Controls v8 5.4"],
        nist_mapping=["AC-2", "AC-6", "IA-2"],
        cis_mapping="5.4",
        default_severity=Severity.CRITICAL
    ),
    
    "AD-002": Control(
        id="AD-002",
        name="Service Account Management",
        description="Service accounts should use Group Managed Service Accounts (gMSA) where possible, with passwords rotated regularly.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Active Directory Security",
        check_procedure="""
1. Identify all service accounts in the domain
2. Check account types (standard vs gMSA)
3. Review password age for standard service accounts
4. Verify service accounts have minimum required permissions
5. Check for interactive logon capability (should be disabled)
        """,
        expected_result="All compatible services use gMSA; standard service accounts have passwords <90 days old",
        remediation_steps=[
            RemediationStep(1, "Inventory all service accounts",
                          "Get-ADServiceAccount -Filter * | Select-Object Name, Enabled, PasswordLastSet",
                          "powershell", "10 minutes"),
            RemediationStep(2, "Create KDS Root Key (if not exists)",
                          "Add-KdsRootKey -EffectiveTime ((Get-Date).AddHours(-10))",
                          "powershell", "5 minutes"),
            RemediationStep(3, "Create Group Managed Service Account",
                          "New-ADServiceAccount -Name 'gMSA_ServiceName' -DNSHostName 'gmsa.domain.com' -PrincipalsAllowedToRetrieveManagedPassword 'ServerGroup'",
                          "powershell", "15 minutes"),
            RemediationStep(4, "Install gMSA on target server",
                          "Install-ADServiceAccount -Identity 'gMSA_ServiceName'",
                          "powershell", "5 minutes"),
        ],
        references=["Microsoft gMSA Documentation", "NIST SP 800-53 IA-5"],
        nist_mapping=["IA-5", "AC-2"],
        cis_mapping="5.3",
        default_severity=Severity.HIGH
    ),
    
    "AD-003": Control(
        id="AD-003",
        name="Group Policy Security",
        description="Group Policy Objects should be secured, audited, and follow least privilege principles.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Active Directory Security",
        check_procedure="""
1. Review GPO permissions (who can edit)
2. Check for GPO inheritance blocking
3. Verify critical security GPOs are linked at appropriate levels
4. Review GPO change history/versioning
5. Check for orphaned GPOs
        """,
        expected_result="GPO edit permissions limited to authorized admins; all GPOs documented and versioned",
        remediation_steps=[
            RemediationStep(1, "Export current GPO permissions",
                          "Get-GPO -All | ForEach-Object { Get-GPPermission -Guid $_.Id -All } | Export-CSV GPOPermissions.csv",
                          "powershell", "15 minutes"),
            RemediationStep(2, "Remove unauthorized GPO edit permissions",
                          "Set-GPPermission -Name 'GPO Name' -TargetName 'UnauthorizedGroup' -TargetType Group -PermissionLevel None",
                          "powershell", "5 minutes per GPO"),
            RemediationStep(3, "Enable GPO change auditing",
                          "Configure 'Audit Directory Service Changes' via Default Domain Controllers Policy",
                          "gpo", "30 minutes"),
            RemediationStep(4, "Implement GPO backup strategy",
                          "Backup-GPO -All -Path 'C:\\GPOBackups'",
                          "powershell", "10 minutes"),
        ],
        references=["Microsoft GPO Best Practices", "NIST SP 800-53 CM-6"],
        nist_mapping=["CM-6", "CM-7", "AU-2"],
        cis_mapping="5.1",
        default_severity=Severity.HIGH
    ),
    
    "AD-004": Control(
        id="AD-004",
        name="Password Policy Enforcement",
        description="Domain password policy should enforce strong passwords with appropriate complexity, length, and history requirements.",
        family=ControlFamily.IDENTIFICATION_AUTH,
        category="Active Directory Security",
        check_procedure="""
1. Review Default Domain Policy password settings
2. Check for Fine-Grained Password Policies (FGPPs)
3. Verify minimum password length (14+ characters recommended)
4. Check password history (24+ passwords recommended)
5. Review account lockout policy
        """,
        expected_result="Minimum 14 character passwords, 24 password history, complexity enabled, 30-minute lockout",
        remediation_steps=[
            RemediationStep(1, "Review current password policy",
                          "Get-ADDefaultDomainPasswordPolicy",
                          "powershell", "5 minutes"),
            RemediationStep(2, "Update Default Domain Policy password settings",
                          """Set-ADDefaultDomainPasswordPolicy -Identity 'domain.com' -MinPasswordLength 14 -PasswordHistoryCount 24 -ComplexityEnabled $true -MaxPasswordAge '90.00:00:00' -MinPasswordAge '1.00:00:00'""",
                          "powershell", "10 minutes"),
            RemediationStep(3, "Create Fine-Grained Password Policy for privileged accounts",
                          """New-ADFineGrainedPasswordPolicy -Name 'PrivilegedAccountPolicy' -Precedence 10 -MinPasswordLength 20 -PasswordHistoryCount 30 -ComplexityEnabled $true -MaxPasswordAge '60.00:00:00'""",
                          "powershell", "15 minutes"),
            RemediationStep(4, "Apply FGPP to privileged groups",
                          "Add-ADFineGrainedPasswordPolicySubject -Identity 'PrivilegedAccountPolicy' -Subjects 'Domain Admins'",
                          "powershell", "5 minutes"),
        ],
        references=["NIST SP 800-63B", "CIS Controls v8 5.2"],
        nist_mapping=["IA-5", "IA-5(1)"],
        cis_mapping="5.2",
        default_severity=Severity.HIGH
    ),
    
    "AD-005": Control(
        id="AD-005",
        name="Kerberos Configuration",
        description="Kerberos should be configured with strong encryption and appropriate ticket lifetimes.",
        family=ControlFamily.IDENTIFICATION_AUTH,
        category="Active Directory Security",
        check_procedure="""
1. Check supported Kerberos encryption types
2. Verify RC4 is disabled (if environment supports it)
3. Review Kerberos ticket lifetime settings
4. Check for accounts with SPN that don't require Kerberos pre-authentication
5. Audit for Kerberoastable accounts
        """,
        expected_result="AES256 encryption required; RC4 disabled; ticket lifetime <10 hours; all accounts require pre-auth",
        remediation_steps=[
            RemediationStep(1, "Check current Kerberos encryption types",
                          "Get-ADObject -Filter 'msDS-SupportedEncryptionTypes -like \"*\"' -Properties msDS-SupportedEncryptionTypes | Where-Object {$_.'msDS-SupportedEncryptionTypes' -band 4}",
                          "powershell", "10 minutes"),
            RemediationStep(2, "Configure Domain Controller Kerberos policy via GPO",
                          "Set 'Network security: Configure encryption types allowed for Kerberos' to AES128, AES256 only",
                          "gpo", "30 minutes", True),
            RemediationStep(3, "Find accounts vulnerable to Kerberoasting",
                          "Get-ADUser -Filter {ServicePrincipalName -ne '$null'} -Properties ServicePrincipalName | Select-Object Name, ServicePrincipalName",
                          "powershell", "10 minutes"),
            RemediationStep(4, "Ensure pre-authentication is required for all accounts",
                          "Get-ADUser -Filter {DoesNotRequirePreAuth -eq $true} | Set-ADUser -DoesNotRequirePreAuth $false",
                          "powershell", "15 minutes"),
        ],
        references=["Microsoft Kerberos Documentation", "MITRE ATT&CK T1558"],
        nist_mapping=["IA-5", "SC-12", "SC-13"],
        cis_mapping="5.1",
        default_severity=Severity.HIGH
    ),
    
    "AD-006": Control(
        id="AD-006",
        name="LDAP Signing & Channel Binding",
        description="LDAP signing and channel binding should be required to prevent man-in-the-middle attacks.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Active Directory Security",
        check_procedure="""
1. Check LDAP signing requirements on domain controllers
2. Verify LDAP channel binding settings
3. Review client compatibility for LDAP signing
4. Check for applications using simple LDAP binds
5. Audit LDAP connection security
        """,
        expected_result="LDAP signing required on all DCs; channel binding enabled; no simple binds",
        remediation_steps=[
            RemediationStep(1, "Check current LDAP signing configuration",
                          "Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\NTDS\\Parameters' -Name 'LDAPServerIntegrity' -ErrorAction SilentlyContinue",
                          "powershell", "5 minutes"),
            RemediationStep(2, "Enable LDAP signing requirement via GPO",
                          "Set 'Domain controller: LDAP server signing requirements' to 'Require signing'",
                          "gpo", "30 minutes", True),
            RemediationStep(3, "Enable LDAP channel binding",
                          "Set-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\NTDS\\Parameters' -Name 'LdapEnforceChannelBinding' -Value 2",
                          "powershell", "15 minutes", True),
            RemediationStep(4, "Test LDAP connectivity after changes",
                          "Test LDAP applications to ensure compatibility",
                          None, "2-4 hours"),
        ],
        references=["Microsoft ADV190023", "NIST SP 800-53 SC-8"],
        nist_mapping=["SC-8", "SC-8(1)", "SC-23"],
        cis_mapping="5.6",
        default_severity=Severity.HIGH
    ),
    
    "AD-007": Control(
        id="AD-007",
        name="AdminSDHolder Protection",
        description="AdminSDHolder container should be monitored and protected from unauthorized modifications.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Active Directory Security",
        check_procedure="""
1. Review AdminSDHolder permissions
2. Check SDProp process frequency
3. Audit protected group membership
4. Review accounts with adminCount=1
5. Check for orphaned adminCount attributes
        """,
        expected_result="AdminSDHolder has default secure permissions; protected groups properly managed",
        remediation_steps=[
            RemediationStep(1, "Review AdminSDHolder permissions",
                          "Get-ACL 'AD:\\CN=AdminSDHolder,CN=System,DC=domain,DC=com' | Format-List",
                          "powershell", "10 minutes"),
            RemediationStep(2, "Find accounts with adminCount=1",
                          "Get-ADUser -Filter {adminCount -eq 1} -Properties adminCount,memberOf | Select-Object Name,adminCount",
                          "powershell", "10 minutes"),
            RemediationStep(3, "Clear orphaned adminCount attributes",
                          "# Review and clear adminCount for users no longer in protected groups",
                          "powershell", "30 minutes"),
            RemediationStep(4, "Enable auditing on AdminSDHolder",
                          "Configure auditing via SACL on AdminSDHolder container",
                          "gpo", "20 minutes"),
        ],
        references=["Microsoft AdminSDHolder Documentation", "NIST SP 800-53 AC-6"],
        nist_mapping=["AC-6", "AU-2", "AU-12"],
        cis_mapping="5.1",
        default_severity=Severity.HIGH
    ),
    
    "AD-008": Control(
        id="AD-008",
        name="Trust Relationship Security",
        description="Domain and forest trusts should be properly configured with appropriate security controls.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Active Directory Security",
        check_procedure="""
1. Inventory all trust relationships
2. Verify trust types (forest, external, realm)
3. Check SID filtering status
4. Review selective authentication settings
5. Audit trust direction and transitivity
        """,
        expected_result="All trusts documented; SID filtering enabled on external trusts; selective auth where appropriate",
        remediation_steps=[
            RemediationStep(1, "List all trust relationships",
                          "Get-ADTrust -Filter * | Select-Object Name,Direction,TrustType,DisallowTransivity,SIDFilteringForestAware",
                          "powershell", "10 minutes"),
            RemediationStep(2, "Enable SID filtering on external trusts",
                          "netdom trust TrustingDomain /domain:TrustedDomain /quarantine:yes",
                          "cmd", "15 minutes"),
            RemediationStep(3, "Configure selective authentication",
                          "Set-ADTrust -Identity 'TrustName' -SelectiveAuthentication $true",
                          "powershell", "30 minutes", True),
            RemediationStep(4, "Document trust business justification",
                          None, None, "2 hours"),
        ],
        references=["Microsoft Trust Documentation", "NIST SP 800-53 AC-4"],
        nist_mapping=["AC-4", "AC-20", "IA-8"],
        cis_mapping="5.1",
        default_severity=Severity.HIGH
    ),
    
    "AD-009": Control(
        id="AD-009",
        name="Replication Security",
        description="AD replication should be secured with encryption and proper authentication.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Active Directory Security",
        check_procedure="""
1. Verify replication encryption settings
2. Check DC-to-DC communication security
3. Review SYSVOL replication method (FRS vs DFSR)
4. Audit replication health and errors
5. Check for unauthorized replication attempts
        """,
        expected_result="DFSR for SYSVOL; encrypted replication; no replication errors",
        remediation_steps=[
            RemediationStep(1, "Check SYSVOL replication method",
                          "Get-ADDomainController -Filter * | Select-Object Name,@{N='SysvolReplication';E={(Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\DFSR\\Parameters\\SysVols\\Seeding SysVols' -ErrorAction SilentlyContinue)}}",
                          "powershell", "10 minutes"),
            RemediationStep(2, "Migrate from FRS to DFSR if needed",
                          "dfsrmig /setglobalstate 3",
                          "cmd", "4-8 hours", True),
            RemediationStep(3, "Check replication status",
                          "repadmin /replsummary",
                          "cmd", "10 minutes"),
            RemediationStep(4, "Enable advanced auditing for replication",
                          "auditpol /set /subcategory:'Directory Service Replication' /success:enable /failure:enable",
                          "cmd", "10 minutes"),
        ],
        references=["Microsoft DFS-R Documentation", "NIST SP 800-53 SC-8"],
        nist_mapping=["SC-8", "AU-2", "SI-4"],
        cis_mapping="5.1",
        default_severity=Severity.MEDIUM
    ),
    
    "AD-010": Control(
        id="AD-010",
        name="Audit Policy Configuration",
        description="Advanced audit policies should be configured to capture security-relevant events.",
        family=ControlFamily.AUDIT_ACCOUNTABILITY,
        category="Active Directory Security",
        check_procedure="""
1. Review advanced audit policy settings
2. Verify logon/logoff auditing
3. Check account management auditing
4. Review directory service access auditing
5. Verify audit log size and retention
        """,
        expected_result="All security-relevant events audited; logs sized appropriately; central collection enabled",
        remediation_steps=[
            RemediationStep(1, "Review current audit policy",
                          "auditpol /get /category:*",
                          "cmd", "10 minutes"),
            RemediationStep(2, "Configure comprehensive audit policy via GPO",
                          "# Enable: Logon/Logoff, Account Management, DS Access, Policy Change, Privilege Use",
                          "gpo", "1 hour"),
            RemediationStep(3, "Increase Security log size",
                          "wevtutil sl Security /ms:1073741824",
                          "cmd", "5 minutes"),
            RemediationStep(4, "Configure log forwarding to SIEM",
                          "# Configure Windows Event Forwarding or agent-based collection",
                          None, "2-4 hours"),
        ],
        references=["Microsoft Audit Policy Recommendations", "NIST SP 800-53 AU-2"],
        nist_mapping=["AU-2", "AU-3", "AU-12"],
        cis_mapping="17.1",
        default_severity=Severity.HIGH
    ),
}

# ============================================================================
# NETWORK INFRASTRUCTURE CONTROLS
# ============================================================================

NETWORK_CONTROLS = {
    "NET-001": Control(
        id="NET-001",
        name="Network Segmentation",
        description="Network should be properly segmented with appropriate controls between zones.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Network Infrastructure",
        check_procedure="""
1. Review network architecture diagram
2. Identify security zones (DMZ, Internal, Restricted, PCI, etc.)
3. Verify firewall rules between zones
4. Check for flat network segments with unrestricted access
5. Test segmentation effectiveness with port scans
        """,
        expected_result="Clearly defined security zones with documented firewall rules; no flat networks",
        remediation_steps=[
            RemediationStep(1, "Document current network topology",
                          None, None, "2-4 hours"),
            RemediationStep(2, "Define security zones based on data classification",
                          None, None, "2-4 hours"),
            RemediationStep(3, "Implement VLANs for logical separation",
                          "# Example Cisco: vlan 100, name SERVERS",
                          "cisco", "4-8 hours", True),
            RemediationStep(4, "Configure inter-VLAN routing with ACLs",
                          "# Example: ip access-list extended VLAN100-TO-VLAN200",
                          "cisco", "2-4 hours"),
            RemediationStep(5, "Deploy next-gen firewall between zones",
                          None, None, "1-2 days", True),
        ],
        references=["NIST SP 800-53 SC-7", "CIS Controls v8 12"],
        nist_mapping=["SC-7", "SC-7(5)", "AC-4"],
        cis_mapping="12.1",
        default_severity=Severity.CRITICAL
    ),
    
    "NET-002": Control(
        id="NET-002",
        name="Firewall Rule Review",
        description="Firewall rules should follow least privilege and be regularly reviewed for necessity.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Network Infrastructure",
        check_procedure="""
1. Export all firewall rules
2. Identify 'any/any' rules
3. Check for unused rules (no hit count)
4. Verify all rules have business justification/documentation
5. Review rules allowing inbound access from internet
        """,
        expected_result="No 'any/any' rules; all rules documented with business justification; unused rules removed",
        remediation_steps=[
            RemediationStep(1, "Export firewall rules for review",
                          "# Palo Alto: show running security-policy",
                          "firewall", "30 minutes"),
            RemediationStep(2, "Identify and document overly permissive rules",
                          None, None, "2-4 hours"),
            RemediationStep(3, "Create change requests to tighten rules",
                          None, None, "1-2 hours"),
            RemediationStep(4, "Implement rule changes during maintenance window",
                          None, None, "2-4 hours", True),
            RemediationStep(5, "Enable rule hit count logging for future cleanup",
                          None, None, "30 minutes"),
        ],
        references=["NIST SP 800-53 SC-7", "CIS Controls v8 12.2"],
        nist_mapping=["SC-7", "CM-6", "CM-7"],
        cis_mapping="12.2",
        default_severity=Severity.HIGH
    ),
    
    "NET-003": Control(
        id="NET-003",
        name="IDS/IPS Configuration",
        description="Intrusion Detection/Prevention Systems should be deployed and properly tuned.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Network Infrastructure",
        check_procedure="""
1. Verify IDS/IPS is deployed at network perimeter and critical segments
2. Check signature update frequency
3. Review alert volume and false positive rate
4. Verify alerts are being monitored/investigated
5. Check IPS blocking mode configuration
        """,
        expected_result="IDS/IPS deployed at perimeter; signatures updated daily; alerts reviewed within 24 hours",
        remediation_steps=[
            RemediationStep(1, "Verify IDS/IPS sensor placement",
                          None, None, "1 hour"),
            RemediationStep(2, "Configure automatic signature updates",
                          "# Snort: rule_path /etc/snort/rules, update via PulledPork",
                          "ids", "1 hour"),
            RemediationStep(3, "Tune rules to reduce false positives",
                          "# Suppress noisy signatures based on environment",
                          "ids", "4-8 hours"),
            RemediationStep(4, "Configure SIEM integration for alert forwarding",
                          None, None, "2-4 hours"),
            RemediationStep(5, "Enable IPS blocking mode for high-confidence signatures",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 SI-4", "CIS Controls v8 13"],
        nist_mapping=["SI-4", "SI-4(4)", "IR-4"],
        cis_mapping="13.3",
        default_severity=Severity.HIGH
    ),
    
    "NET-004": Control(
        id="NET-004",
        name="VPN Security",
        description="VPN configurations should use strong encryption and multi-factor authentication.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Network Infrastructure",
        check_procedure="""
1. Review VPN encryption protocols (IKEv2, IPSec settings)
2. Verify MFA is required for VPN access
3. Check split tunneling configuration
4. Review VPN access policies and user groups
5. Audit VPN connection logs
        """,
        expected_result="IKEv2/IPSec with AES-256; MFA required; split tunneling disabled for sensitive resources",
        remediation_steps=[
            RemediationStep(1, "Review VPN configuration",
                          "# Check VPN appliance for encryption settings",
                          None, "30 minutes"),
            RemediationStep(2, "Upgrade to IKEv2 with strong ciphers",
                          "# Configure Phase 1: AES-256, SHA-256, DH Group 14+",
                          "vpn", "2-4 hours", True),
            RemediationStep(3, "Enable MFA for VPN access",
                          "# Integrate with RADIUS/Azure MFA/Duo",
                          None, "4-8 hours"),
            RemediationStep(4, "Disable split tunneling or implement exceptions carefully",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 SC-8", "CIS Controls v8 12.6"],
        nist_mapping=["SC-8", "SC-12", "IA-2(1)"],
        cis_mapping="12.6",
        default_severity=Severity.HIGH
    ),
    
    "NET-005": Control(
        id="NET-005",
        name="Switch Port Security",
        description="Switch ports should be secured against unauthorized access and MAC address spoofing.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Network Infrastructure",
        check_procedure="""
1. Verify unused ports are disabled
2. Check port security (MAC limiting) configuration
3. Review 802.1X implementation status
4. Check DHCP snooping configuration
5. Verify ARP inspection settings
        """,
        expected_result="Unused ports disabled; 802.1X on access ports; DHCP snooping and DAI enabled",
        remediation_steps=[
            RemediationStep(1, "Identify and disable unused switch ports",
                          "# Cisco: show interfaces status | include notconnect",
                          "cisco", "2-4 hours"),
            RemediationStep(2, "Configure port security",
                          "# interface GigabitEthernet0/1\n# switchport port-security\n# switchport port-security maximum 2",
                          "cisco", "2-4 hours"),
            RemediationStep(3, "Enable DHCP snooping",
                          "# ip dhcp snooping\n# ip dhcp snooping vlan 1-100",
                          "cisco", "2 hours"),
            RemediationStep(4, "Enable Dynamic ARP Inspection",
                          "# ip arp inspection vlan 1-100",
                          "cisco", "2 hours"),
        ],
        references=["NIST SP 800-53 SC-7", "CIS Controls v8 12.1"],
        nist_mapping=["SC-7", "AC-4", "IA-3"],
        cis_mapping="12.1",
        default_severity=Severity.MEDIUM
    ),
    
    "NET-006": Control(
        id="NET-006",
        name="Router ACL Review",
        description="Router access control lists should follow least privilege and be regularly reviewed.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Network Infrastructure",
        check_procedure="""
1. Export and review all router ACLs
2. Verify explicit deny rules are logged
3. Check for overly permissive rules
4. Review management access restrictions
5. Audit ACL hit counts
        """,
        expected_result="ACLs follow least privilege; management restricted to jump hosts; all rules documented",
        remediation_steps=[
            RemediationStep(1, "Export router ACLs",
                          "# show access-lists",
                          "cisco", "30 minutes"),
            RemediationStep(2, "Review and document each ACL rule",
                          None, None, "4-8 hours"),
            RemediationStep(3, "Remove overly permissive rules",
                          "# no access-list 100 permit ip any any",
                          "cisco", "2 hours", True),
            RemediationStep(4, "Add logging to deny rules",
                          "# access-list 100 deny ip any any log",
                          "cisco", "1 hour"),
        ],
        references=["NIST SP 800-53 AC-4", "CIS Controls v8 12.2"],
        nist_mapping=["AC-4", "SC-7", "AU-3"],
        cis_mapping="12.2",
        default_severity=Severity.MEDIUM
    ),
    
    "NET-007": Control(
        id="NET-007",
        name="Network Device Hardening",
        description="Network devices should be hardened according to vendor and industry best practices.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Network Infrastructure",
        check_procedure="""
1. Review device firmware versions
2. Check for default credentials
3. Verify SSH/encrypted management only
4. Review banner and logging configuration
5. Check NTP and SNMP settings
        """,
        expected_result="Current firmware; no default creds; SSH only; SNMPv3; NTP configured",
        remediation_steps=[
            RemediationStep(1, "Update firmware to latest stable version",
                          None, None, "2-4 hours per device", True),
            RemediationStep(2, "Disable Telnet, enable SSH only",
                          "# line vty 0 15\n# transport input ssh",
                          "cisco", "1 hour"),
            RemediationStep(3, "Configure SNMPv3",
                          "# snmp-server group SNMPGROUP v3 priv\n# snmp-server user SNMPUSER SNMPGROUP v3 auth sha AUTH_PASS priv aes 128 PRIV_PASS",
                          "cisco", "2 hours"),
            RemediationStep(4, "Configure NTP authentication",
                          "# ntp server 10.1.1.1 key 1\n# ntp authenticate",
                          "cisco", "30 minutes"),
        ],
        references=["CIS Cisco Benchmarks", "NIST SP 800-53 CM-6"],
        nist_mapping=["CM-6", "CM-7", "IA-5"],
        cis_mapping="4.1",
        default_severity=Severity.HIGH
    ),
    
    "NET-008": Control(
        id="NET-008",
        name="Wireless Security",
        description="Wireless networks should use WPA3/WPA2-Enterprise with proper segmentation.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Network Infrastructure",
        check_procedure="""
1. Verify wireless encryption standards (WPA3/WPA2-Enterprise)
2. Check RADIUS integration for authentication
3. Review wireless network segmentation
4. Audit guest network isolation
5. Check for rogue access points
        """,
        expected_result="WPA2-Enterprise minimum; RADIUS auth; guest network isolated; regular rogue AP scans",
        remediation_steps=[
            RemediationStep(1, "Audit current wireless configuration",
                          None, None, "2 hours"),
            RemediationStep(2, "Upgrade to WPA2-Enterprise or WPA3",
                          "# Configure RADIUS server integration",
                          None, "4-8 hours"),
            RemediationStep(3, "Segment wireless traffic into separate VLANs",
                          None, None, "4 hours"),
            RemediationStep(4, "Enable rogue AP detection",
                          "# Configure WIPS on wireless controller",
                          None, "2 hours"),
        ],
        references=["NIST SP 800-53 SC-8", "CIS Controls v8 12.6"],
        nist_mapping=["SC-8", "AC-18", "IA-2"],
        cis_mapping="12.6",
        default_severity=Severity.HIGH
    ),
    
    "NET-009": Control(
        id="NET-009",
        name="DNS Security",
        description="DNS should be secured with DNSSEC, filtering, and proper logging.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Network Infrastructure",
        check_procedure="""
1. Verify internal DNS server security
2. Check DNSSEC implementation
3. Review DNS filtering/blocking
4. Audit DNS query logging
5. Check for DNS over HTTPS/TLS support
        """,
        expected_result="DNSSEC validated; malicious domain filtering; query logging enabled",
        remediation_steps=[
            RemediationStep(1, "Enable DNS query logging",
                          "# Windows: dnscmd /config /logLevel 0x8000F301",
                          "powershell", "30 minutes"),
            RemediationStep(2, "Implement DNSSEC validation",
                          "# Enable DNSSEC validation on resolvers",
                          None, "4 hours"),
            RemediationStep(3, "Configure DNS filtering",
                          "# Deploy DNS filtering solution (Umbrella, Quad9, etc.)",
                          None, "4-8 hours"),
            RemediationStep(4, "Secure zone transfers",
                          "# Restrict zone transfers to authorized servers only",
                          None, "2 hours"),
        ],
        references=["NIST SP 800-53 SC-20", "CIS Controls v8 9.2"],
        nist_mapping=["SC-20", "SC-21", "SC-22"],
        cis_mapping="9.2",
        default_severity=Severity.MEDIUM
    ),
    
    "NET-010": Control(
        id="NET-010",
        name="Network Monitoring",
        description="Network traffic should be continuously monitored for anomalies and threats.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Network Infrastructure",
        check_procedure="""
1. Verify NetFlow/sFlow collection
2. Check network behavior analysis tools
3. Review bandwidth monitoring
4. Audit network alerts and thresholds
5. Check integration with SIEM
        """,
        expected_result="Flow data collected; baselines established; anomaly detection active; SIEM integrated",
        remediation_steps=[
            RemediationStep(1, "Enable NetFlow on core devices",
                          "# interface GigabitEthernet0/0\n# ip flow ingress\n# ip flow egress",
                          "cisco", "2 hours"),
            RemediationStep(2, "Deploy flow collector",
                          "# Configure PRTG, SolarWinds, or similar",
                          None, "4-8 hours"),
            RemediationStep(3, "Establish traffic baselines",
                          None, None, "2-4 weeks"),
            RemediationStep(4, "Configure anomaly alerts",
                          "# Set thresholds for bandwidth, connection counts, etc.",
                          None, "4 hours"),
        ],
        references=["NIST SP 800-53 SI-4", "CIS Controls v8 13.6"],
        nist_mapping=["SI-4", "AU-6", "IR-4"],
        cis_mapping="13.6",
        default_severity=Severity.MEDIUM
    ),
}

# ============================================================================
# ENDPOINT SECURITY CONTROLS
# ============================================================================

ENDPOINT_CONTROLS = {
    "END-001": Control(
        id="END-001",
        name="Endpoint Protection Platform",
        description="All endpoints should have EPP/antivirus software installed, updated, and actively protecting.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Endpoint Security",
        check_procedure="""
1. Verify EPP agent is installed on all endpoints
2. Check signature/definition update status
3. Verify real-time protection is enabled
4. Review recent detection/quarantine events
5. Check for endpoints with outdated agents
        """,
        expected_result="100% EPP coverage; signatures <24 hours old; real-time protection enabled",
        remediation_steps=[
            RemediationStep(1, "Generate EPP deployment report",
                          "# Check EPP console for unprotected endpoints",
                          None, "30 minutes"),
            RemediationStep(2, "Deploy EPP agent to missing endpoints",
                          "# Use SCCM, Intune, or EPP push deployment",
                          None, "2-4 hours"),
            RemediationStep(3, "Configure automatic signature updates",
                          "# EPP policy: update every 4 hours",
                          None, "30 minutes"),
            RemediationStep(4, "Enable real-time protection via policy",
                          None, None, "30 minutes"),
            RemediationStep(5, "Configure alerting for protection failures",
                          None, None, "1 hour"),
        ],
        references=["NIST SP 800-53 SI-3", "CIS Controls v8 10"],
        nist_mapping=["SI-3", "SI-3(1)", "SI-3(2)"],
        cis_mapping="10.1",
        default_severity=Severity.CRITICAL
    ),
    
    "END-002": Control(
        id="END-002",
        name="Patch Management",
        description="Operating systems and applications should be patched within defined SLAs based on criticality.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Endpoint Security",
        check_procedure="""
1. Review patch compliance reports
2. Check for critical patches older than 14 days
3. Verify automatic update configuration
4. Review failed patch installations
5. Check for unsupported OS versions
        """,
        expected_result="Critical patches within 14 days; high within 30 days; no unsupported OS",
        remediation_steps=[
            RemediationStep(1, "Generate patch compliance report",
                          "Get-WindowsUpdate -ComputerName <hostname> | Where-Object {$_.IsInstalled -eq $false}",
                          "powershell", "30 minutes"),
            RemediationStep(2, "Configure WSUS/SCCM/Intune patch policies",
                          None, None, "2-4 hours"),
            RemediationStep(3, "Deploy missing critical patches",
                          "Install-WindowsUpdate -AcceptAll -AutoReboot",
                          "powershell", "2-4 hours", True),
            RemediationStep(4, "Create remediation plan for unsupported systems",
                          None, None, "4-8 hours"),
            RemediationStep(5, "Implement patching exceptions process",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 SI-2", "CIS Controls v8 7"],
        nist_mapping=["SI-2", "SI-2(2)", "CM-3"],
        cis_mapping="7.1",
        default_severity=Severity.CRITICAL
    ),
    
    "END-003": Control(
        id="END-003",
        name="Host-based Firewall",
        description="Host-based firewalls should be enabled and configured with restrictive rules.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Endpoint Security",
        check_procedure="""
1. Verify Windows Firewall/iptables is enabled
2. Review inbound/outbound rules
3. Check for overly permissive rules
4. Verify firewall logging is enabled
5. Check GPO/MDM enforcement
        """,
        expected_result="Firewall enabled on all profiles; default deny inbound; logging enabled",
        remediation_steps=[
            RemediationStep(1, "Check firewall status",
                          "Get-NetFirewallProfile | Select-Object Name, Enabled",
                          "powershell", "10 minutes"),
            RemediationStep(2, "Enable Windows Firewall via GPO",
                          "# Computer Config > Windows Settings > Security Settings > Windows Firewall",
                          "gpo", "1 hour"),
            RemediationStep(3, "Configure firewall rules via GPO",
                          "New-NetFirewallRule -DisplayName 'Block Inbound' -Direction Inbound -Action Block",
                          "powershell", "2-4 hours"),
            RemediationStep(4, "Enable firewall logging",
                          "Set-NetFirewallProfile -LogFileName '%systemroot%\\system32\\LogFiles\\Firewall\\pfirewall.log' -LogMaxSizeKilobytes 4096 -LogAllowed True -LogBlocked True",
                          "powershell", "30 minutes"),
        ],
        references=["NIST SP 800-53 SC-7", "CIS Controls v8 4.4"],
        nist_mapping=["SC-7", "SC-7(5)", "AC-4"],
        cis_mapping="4.4",
        default_severity=Severity.MEDIUM
    ),
    
    "END-004": Control(
        id="END-004",
        name="Application Whitelisting",
        description="Application whitelisting should restrict execution to approved applications only.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Endpoint Security",
        check_procedure="""
1. Verify AppLocker/WDAC is deployed
2. Review application rules
3. Check for audit vs enforce mode
4. Review exceptions and blocked applications
5. Verify rule updates process
        """,
        expected_result="Application control in enforce mode; rules reviewed quarterly; exceptions documented",
        remediation_steps=[
            RemediationStep(1, "Enable AppLocker in audit mode",
                          "# Deploy AppLocker GPO in Audit Only mode first",
                          "gpo", "2 hours"),
            RemediationStep(2, "Generate default AppLocker rules",
                          "Get-AppLockerPolicy -Local | Format-List",
                          "powershell", "1 hour"),
            RemediationStep(3, "Analyze audit logs for required applications",
                          "Get-AppLockerFileInformation -EventLog | Group-Object -Property PublisherName",
                          "powershell", "4-8 hours"),
            RemediationStep(4, "Transition to enforce mode",
                          "# Change GPO from Audit to Enforce after baseline",
                          "gpo", "2 hours", True),
        ],
        references=["NIST SP 800-53 CM-7", "CIS Controls v8 2.5"],
        nist_mapping=["CM-7", "CM-7(2)", "CM-7(5)"],
        cis_mapping="2.5",
        default_severity=Severity.HIGH
    ),
    
    "END-005": Control(
        id="END-005",
        name="Local Admin Rights",
        description="End users should not have local administrator rights on their workstations.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Endpoint Security",
        check_procedure="""
1. Review local Administrators group membership on sample workstations
2. Check for domain groups granting local admin
3. Verify PAM/LAPS solution is deployed
4. Review admin rights request process
5. Check for standing admin accounts
        """,
        expected_result="No end users with standing local admin rights; LAPS deployed for break-glass",
        remediation_steps=[
            RemediationStep(1, "Audit local admin group membership",
                          "Get-LocalGroupMember -Group 'Administrators' | Select-Object Name, ObjectClass",
                          "powershell", "30 minutes"),
            RemediationStep(2, "Remove users from local Administrators group",
                          "Remove-LocalGroupMember -Group 'Administrators' -Member 'DOMAIN\\Username'",
                          "powershell", "15 minutes per system"),
            RemediationStep(3, "Deploy Microsoft LAPS",
                          "# Install LAPS CSE via GPO, configure password policy",
                          "gpo", "4-8 hours"),
            RemediationStep(4, "Implement PAM solution for just-in-time admin access",
                          None, None, "1-2 weeks"),
            RemediationStep(5, "Create application elevation rules for approved software",
                          None, None, "4-8 hours"),
        ],
        references=["NIST SP 800-53 AC-6", "CIS Controls v8 5.4"],
        nist_mapping=["AC-6", "AC-6(1)", "AC-6(5)"],
        cis_mapping="5.4",
        default_severity=Severity.HIGH
    ),
    
    "END-006": Control(
        id="END-006",
        name="USB/Removable Media Control",
        description="Removable media should be controlled to prevent data exfiltration and malware.",
        family=ControlFamily.MEDIA_PROTECTION,
        category="Endpoint Security",
        check_procedure="""
1. Review USB device policy
2. Check for blocking vs read-only vs full access
3. Verify encryption requirements for allowed devices
4. Review DLP integration
5. Audit removable media events
        """,
        expected_result="USB storage blocked or restricted; approved devices encrypted; events logged",
        remediation_steps=[
            RemediationStep(1, "Audit current USB policy",
                          "Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR' -Name Start",
                          "powershell", "15 minutes"),
            RemediationStep(2, "Block USB storage via GPO",
                          "# Computer Config > Admin Templates > System > Removable Storage Access",
                          "gpo", "1 hour"),
            RemediationStep(3, "Configure allowed device exceptions",
                          "# Use device ID whitelisting for approved devices",
                          "gpo", "2 hours"),
            RemediationStep(4, "Enable USB device auditing",
                          "# Enable Audit Removable Storage in Advanced Audit Policy",
                          "gpo", "30 minutes"),
        ],
        references=["NIST SP 800-53 MP-7", "CIS Controls v8 10.3"],
        nist_mapping=["MP-7", "MP-7(1)", "SC-41"],
        cis_mapping="10.3",
        default_severity=Severity.MEDIUM
    ),
    
    "END-007": Control(
        id="END-007",
        name="Full Disk Encryption",
        description="All endpoints should have full disk encryption enabled with secure key management.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Endpoint Security",
        check_procedure="""
1. Verify BitLocker/FileVault is enabled
2. Check encryption algorithm (AES-256)
3. Review key escrow configuration
4. Check for TPM + PIN requirement
5. Verify recovery key backup
        """,
        expected_result="All drives encrypted with AES-256; keys escrowed to AD/Intune; TPM+PIN required",
        remediation_steps=[
            RemediationStep(1, "Check BitLocker status",
                          "Get-BitLockerVolume | Select-Object MountPoint, EncryptionMethod, VolumeStatus, ProtectionStatus",
                          "powershell", "15 minutes"),
            RemediationStep(2, "Configure BitLocker via GPO",
                          "# Computer Config > Admin Templates > Windows Components > BitLocker",
                          "gpo", "2 hours"),
            RemediationStep(3, "Enable BitLocker with TPM+PIN",
                          "Enable-BitLocker -MountPoint 'C:' -EncryptionMethod XtsAes256 -TPMandPinProtector -Pin (ConvertTo-SecureString 'PIN' -AsPlainText -Force)",
                          "powershell", "2-4 hours per system"),
            RemediationStep(4, "Backup recovery keys to AD",
                          "Backup-BitLockerKeyProtector -MountPoint 'C:' -KeyProtectorId (Get-BitLockerVolume -MountPoint 'C:').KeyProtector[0].KeyProtectorId",
                          "powershell", "30 minutes"),
        ],
        references=["NIST SP 800-53 SC-28", "CIS Controls v8 3.6"],
        nist_mapping=["SC-28", "SC-28(1)", "MP-5"],
        cis_mapping="3.6",
        default_severity=Severity.HIGH
    ),
    
    "END-008": Control(
        id="END-008",
        name="EDR/XDR Deployment",
        description="Endpoint Detection and Response should be deployed for advanced threat detection.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Endpoint Security",
        check_procedure="""
1. Verify EDR agent deployment coverage
2. Check agent health and connectivity
3. Review detection rules and policies
4. Audit response playbooks
5. Verify SIEM integration
        """,
        expected_result="100% EDR coverage; agents healthy; response playbooks tested; SIEM integrated",
        remediation_steps=[
            RemediationStep(1, "Generate EDR deployment report",
                          "# Check EDR console for agent coverage",
                          None, "30 minutes"),
            RemediationStep(2, "Deploy EDR to missing endpoints",
                          "# Use deployment tool (SCCM, Intune, EDR push)",
                          None, "4-8 hours"),
            RemediationStep(3, "Configure detection policies",
                          "# Enable all high-fidelity detection rules",
                          None, "2-4 hours"),
            RemediationStep(4, "Create response playbooks",
                          "# Define automated responses for common threats",
                          None, "4-8 hours"),
        ],
        references=["NIST SP 800-53 SI-4", "CIS Controls v8 13.7"],
        nist_mapping=["SI-4", "SI-4(4)", "IR-4"],
        cis_mapping="13.7",
        default_severity=Severity.HIGH
    ),
    
    "END-009": Control(
        id="END-009",
        name="Secure Boot Configuration",
        description="Secure Boot should be enabled to prevent boot-level malware.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Endpoint Security",
        check_procedure="""
1. Verify Secure Boot is enabled in UEFI
2. Check for UEFI vs Legacy BIOS mode
3. Review Secure Boot key configuration
4. Verify firmware password protection
5. Check for Credential Guard enablement
        """,
        expected_result="UEFI with Secure Boot enabled; firmware password set; Credential Guard active",
        remediation_steps=[
            RemediationStep(1, "Check Secure Boot status",
                          "Confirm-SecureBootUEFI",
                          "powershell", "10 minutes"),
            RemediationStep(2, "Enable Secure Boot in UEFI",
                          "# Access UEFI settings during boot and enable Secure Boot",
                          None, "30 minutes per system", True),
            RemediationStep(3, "Enable Credential Guard via GPO",
                          "# Computer Config > Admin Templates > System > Device Guard",
                          "gpo", "2 hours"),
            RemediationStep(4, "Set firmware password",
                          "# Configure during UEFI setup",
                          None, "15 minutes per system"),
        ],
        references=["NIST SP 800-53 SI-7", "CIS Controls v8 10.5"],
        nist_mapping=["SI-7", "SI-7(1)", "SC-39"],
        cis_mapping="10.5",
        default_severity=Severity.MEDIUM
    ),
    
    "END-010": Control(
        id="END-010",
        name="Endpoint Logging",
        description="Endpoints should log security-relevant events and forward to central collection.",
        family=ControlFamily.AUDIT_ACCOUNTABILITY,
        category="Endpoint Security",
        check_procedure="""
1. Verify Windows Event Log configuration
2. Check Sysmon deployment
3. Review PowerShell logging settings
4. Verify log forwarding to SIEM
5. Check log retention settings
        """,
        expected_result="Sysmon deployed; PowerShell logging enabled; logs forwarded to SIEM within 5 minutes",
        remediation_steps=[
            RemediationStep(1, "Deploy Sysmon with optimized config",
                          "sysmon64.exe -accepteula -i sysmonconfig.xml",
                          "cmd", "1 hour"),
            RemediationStep(2, "Enable PowerShell logging via GPO",
                          "# Enable Module Logging, Script Block Logging, Transcription",
                          "gpo", "1 hour"),
            RemediationStep(3, "Configure Windows Event Forwarding",
                          "wecutil qc",
                          "cmd", "2-4 hours"),
            RemediationStep(4, "Increase event log sizes",
                          "wevtutil sl Security /ms:1073741824",
                          "cmd", "30 minutes"),
        ],
        references=["NIST SP 800-53 AU-2", "CIS Controls v8 8.5"],
        nist_mapping=["AU-2", "AU-3", "AU-12"],
        cis_mapping="8.5",
        default_severity=Severity.HIGH
    ),
}

# ============================================================================
# PHYSICAL SECURITY CONTROLS
# ============================================================================

PHYSICAL_CONTROLS = {
    "PHY-001": Control(
        id="PHY-001",
        name="Physical Access Control",
        description="Physical access to facilities should be controlled with appropriate authentication mechanisms.",
        family=ControlFamily.PHYSICAL_ENVIRONMENTAL,
        category="Physical Security",
        check_procedure="""
1. Review physical access control system (badge readers, biometrics)
2. Verify all entry points are controlled
3. Check for tailgating prevention measures
4. Review access badge issuance process
5. Audit physical access logs
        """,
        expected_result="All entry points controlled; badge access required; logs retained 90+ days",
        remediation_steps=[
            RemediationStep(1, "Audit all building entry points",
                          None, None, "2-4 hours"),
            RemediationStep(2, "Install badge readers at uncontrolled entries",
                          None, None, "1-2 days per entry", True),
            RemediationStep(3, "Configure access control zones",
                          None, None, "4-8 hours"),
            RemediationStep(4, "Implement anti-tailgating measures (mantraps, turnstiles)",
                          None, None, "1-2 weeks", True),
            RemediationStep(5, "Configure access log retention for 90+ days",
                          None, None, "1 hour"),
        ],
        references=["NIST SP 800-53 PE-3", "CIS Controls v8 N/A"],
        nist_mapping=["PE-3", "PE-3(1)", "PE-6"],
        default_severity=Severity.HIGH
    ),
    
    "PHY-002": Control(
        id="PHY-002",
        name="Visitor Management",
        description="Visitors should be registered, badged, and escorted in secure areas.",
        family=ControlFamily.PHYSICAL_ENVIRONMENTAL,
        category="Physical Security",
        check_procedure="""
1. Review visitor registration process
2. Verify visitor badge system
3. Check escort requirements for secure areas
4. Review visitor log retention
5. Audit visitor access history
        """,
        expected_result="All visitors registered; temporary badges issued; escorts required in secure areas",
        remediation_steps=[
            RemediationStep(1, "Implement visitor management system",
                          None, None, "1-2 days"),
            RemediationStep(2, "Create visitor badge process",
                          None, None, "4 hours"),
            RemediationStep(3, "Define escort requirements by zone",
                          None, None, "2 hours"),
            RemediationStep(4, "Train reception staff on procedures",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 PE-3", "PE-8"],
        nist_mapping=["PE-3", "PE-8", "PE-8(1)"],
        default_severity=Severity.MEDIUM
    ),
    
    "PHY-003": Control(
        id="PHY-003",
        name="Surveillance Systems",
        description="Video surveillance should monitor critical areas with appropriate retention.",
        family=ControlFamily.PHYSICAL_ENVIRONMENTAL,
        category="Physical Security",
        check_procedure="""
1. Verify camera coverage of critical areas
2. Check recording quality and frame rate
3. Review retention period (90+ days recommended)
4. Audit camera system access
5. Verify camera system security
        """,
        expected_result="All entry points and critical areas monitored; 90-day retention; system secured",
        remediation_steps=[
            RemediationStep(1, "Audit current camera coverage",
                          None, None, "2-4 hours"),
            RemediationStep(2, "Install cameras at gaps in coverage",
                          None, None, "1-2 days per camera", True),
            RemediationStep(3, "Configure 90-day retention",
                          None, None, "2 hours"),
            RemediationStep(4, "Secure camera system access",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 PE-6", "PE-6(1)"],
        nist_mapping=["PE-6", "PE-6(1)", "AU-9"],
        default_severity=Severity.MEDIUM
    ),
    
    "PHY-004": Control(
        id="PHY-004",
        name="Server Room Access",
        description="Server rooms and data centers should have restricted access with additional authentication.",
        family=ControlFamily.PHYSICAL_ENVIRONMENTAL,
        category="Physical Security",
        check_procedure="""
1. Verify server room has dedicated access control
2. Check for multi-factor physical authentication (badge + PIN/biometric)
3. Review authorized access list
4. Verify visitor escort policy
5. Check for environmental monitoring
        """,
        expected_result="MFA physical access; limited authorized personnel; visitors always escorted",
        remediation_steps=[
            RemediationStep(1, "Audit current server room access list",
                          None, None, "1 hour"),
            RemediationStep(2, "Implement badge + PIN/biometric access",
                          None, None, "2-4 days", True),
            RemediationStep(3, "Reduce authorized access list to essential personnel",
                          None, None, "2-4 hours"),
            RemediationStep(4, "Install surveillance cameras at entry points",
                          None, None, "1 day", True),
            RemediationStep(5, "Deploy environmental sensors (temp, humidity, water)",
                          None, None, "1 day"),
        ],
        references=["NIST SP 800-53 PE-3", "PE-5"],
        nist_mapping=["PE-3", "PE-5", "PE-6"],
        default_severity=Severity.HIGH
    ),
    
    "PHY-005": Control(
        id="PHY-005",
        name="Environmental Controls",
        description="Data centers should have proper HVAC, humidity control, and monitoring.",
        family=ControlFamily.PHYSICAL_ENVIRONMENTAL,
        category="Physical Security",
        check_procedure="""
1. Verify HVAC capacity and redundancy
2. Check temperature monitoring and alerting
3. Review humidity controls
4. Audit environmental sensor placement
5. Check alert escalation procedures
        """,
        expected_result="Redundant HVAC; temp 64-75°F; humidity 40-60%; real-time monitoring with alerts",
        remediation_steps=[
            RemediationStep(1, "Audit current environmental controls",
                          None, None, "2 hours"),
            RemediationStep(2, "Deploy environmental monitoring sensors",
                          None, None, "1 day"),
            RemediationStep(3, "Configure temperature/humidity alerts",
                          None, None, "2 hours"),
            RemediationStep(4, "Document escalation procedures",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 PE-14", "PE-14(2)"],
        nist_mapping=["PE-14", "PE-14(2)", "PE-15"],
        default_severity=Severity.MEDIUM
    ),
    
    "PHY-006": Control(
        id="PHY-006",
        name="Cable Management",
        description="Network and power cables should be secured and protected from tampering.",
        family=ControlFamily.PHYSICAL_ENVIRONMENTAL,
        category="Physical Security",
        check_procedure="""
1. Review cable management in server rooms
2. Check for cable labeling standards
3. Verify cable protection (conduits, trays)
4. Audit network jack security
5. Check for unauthorized cabling
        """,
        expected_result="Cables organized and labeled; protected in trays/conduits; unused jacks disabled",
        remediation_steps=[
            RemediationStep(1, "Audit current cable management",
                          None, None, "4 hours"),
            RemediationStep(2, "Implement cable labeling standards",
                          None, None, "1-2 days"),
            RemediationStep(3, "Install cable protection",
                          None, None, "2-4 days"),
            RemediationStep(4, "Disable unused network jacks",
                          None, None, "4 hours"),
        ],
        references=["NIST SP 800-53 PE-4", "PE-9"],
        nist_mapping=["PE-4", "PE-9", "PE-9(1)"],
        default_severity=Severity.LOW
    ),
    
    "PHY-007": Control(
        id="PHY-007",
        name="Equipment Disposal",
        description="IT equipment should be securely disposed of with data destruction verification.",
        family=ControlFamily.MEDIA_PROTECTION,
        category="Physical Security",
        check_procedure="""
1. Review equipment disposal process
2. Verify data destruction methods (wipe, degauss, shred)
3. Check destruction certificates
4. Audit chain of custody
5. Review vendor disposal contracts
        """,
        expected_result="Documented disposal process; certificates of destruction; chain of custody maintained",
        remediation_steps=[
            RemediationStep(1, "Document equipment disposal policy",
                          None, None, "4 hours"),
            RemediationStep(2, "Implement data destruction verification",
                          None, None, "2 hours"),
            RemediationStep(3, "Create certificate of destruction template",
                          None, None, "1 hour"),
            RemediationStep(4, "Audit vendor disposal contracts",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 MP-6", "MP-6(1)"],
        nist_mapping=["MP-6", "MP-6(1)", "MP-6(2)"],
        default_severity=Severity.MEDIUM
    ),
    
    "PHY-008": Control(
        id="PHY-008",
        name="Emergency Power",
        description="UPS and generator systems should provide adequate backup power.",
        family=ControlFamily.PHYSICAL_ENVIRONMENTAL,
        category="Physical Security",
        check_procedure="""
1. Verify UPS capacity and runtime
2. Check generator fuel and maintenance
3. Review automatic transfer switch (ATS)
4. Audit power test results
5. Check redundant power feeds
        """,
        expected_result="UPS for 15+ min runtime; generator with 48+ hours fuel; monthly testing",
        remediation_steps=[
            RemediationStep(1, "Audit UPS capacity vs load",
                          None, None, "2 hours"),
            RemediationStep(2, "Test generator failover",
                          None, None, "4 hours", True),
            RemediationStep(3, "Document maintenance schedule",
                          None, None, "2 hours"),
            RemediationStep(4, "Implement monthly power tests",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 PE-11", "PE-11(1)"],
        nist_mapping=["PE-11", "PE-11(1)", "CP-8"],
        default_severity=Severity.HIGH
    ),
    
    "PHY-009": Control(
        id="PHY-009",
        name="Fire Suppression",
        description="Fire detection and suppression systems should protect IT equipment.",
        family=ControlFamily.PHYSICAL_ENVIRONMENTAL,
        category="Physical Security",
        check_procedure="""
1. Verify fire detection coverage
2. Check suppression system type (FM-200, Inergen, etc.)
3. Review inspection and testing records
4. Audit EPO (Emergency Power Off) procedures
5. Check integration with building systems
        """,
        expected_result="Smoke detection in all areas; clean agent suppression in server room; annual testing",
        remediation_steps=[
            RemediationStep(1, "Audit fire detection coverage",
                          None, None, "2 hours"),
            RemediationStep(2, "Install clean agent suppression",
                          None, None, "1-2 weeks", True),
            RemediationStep(3, "Schedule annual inspections",
                          None, None, "1 hour"),
            RemediationStep(4, "Document EPO procedures",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 PE-13", "PE-13(3)"],
        nist_mapping=["PE-13", "PE-13(1)", "PE-13(3)"],
        default_severity=Severity.HIGH
    ),
    
    "PHY-010": Control(
        id="PHY-010",
        name="Physical Security Logging",
        description="Physical access events should be logged and monitored.",
        family=ControlFamily.AUDIT_ACCOUNTABILITY,
        category="Physical Security",
        check_procedure="""
1. Verify access control system logging
2. Check log retention period
3. Review log monitoring processes
4. Audit integration with security operations
5. Check for real-time alerting
        """,
        expected_result="All access events logged; 1-year retention; integrated with SOC; real-time alerts",
        remediation_steps=[
            RemediationStep(1, "Configure comprehensive logging",
                          None, None, "2 hours"),
            RemediationStep(2, "Implement 1-year retention",
                          None, None, "1 hour"),
            RemediationStep(3, "Integrate with SIEM",
                          None, None, "4-8 hours"),
            RemediationStep(4, "Configure real-time alerts",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 PE-6", "AU-2"],
        nist_mapping=["PE-6", "AU-2", "AU-6"],
        default_severity=Severity.MEDIUM
    ),
}

# ============================================================================
# SERVER SECURITY CONTROLS
# ============================================================================

SERVER_CONTROLS = {
    "SRV-001": Control(
        id="SRV-001",
        name="Server Hardening Baseline",
        description="Servers should be hardened according to CIS benchmarks or DISA STIGs.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Server Security",
        check_procedure="""
1. Verify CIS/STIG baseline applied
2. Check for compliance scanning tool
3. Review deviation exceptions
4. Audit baseline version currency
5. Check automated remediation
        """,
        expected_result="CIS L1 minimum applied; compliance scanned weekly; deviations documented",
        remediation_steps=[
            RemediationStep(1, "Download applicable CIS benchmark",
                          None, None, "30 minutes"),
            RemediationStep(2, "Run CIS-CAT assessment",
                          "# CIS-CAT Pro: Assessor-CLI.bat -b benchmarks/CIS_Windows_Server_2022.xml",
                          "cmd", "1 hour"),
            RemediationStep(3, "Apply hardening GPO",
                          "# Import CIS GPO template",
                          "gpo", "4-8 hours", True),
            RemediationStep(4, "Document exceptions with justification",
                          None, None, "2 hours"),
        ],
        references=["CIS Benchmarks", "NIST SP 800-53 CM-6"],
        nist_mapping=["CM-6", "CM-6(1)", "CM-7"],
        cis_mapping="4.1",
        default_severity=Severity.HIGH
    ),
    
    "SRV-002": Control(
        id="SRV-002",
        name="Unnecessary Services Disabled",
        description="Only required services should be running on servers.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Server Security",
        check_procedure="""
1. Inventory running services
2. Compare against baseline requirements
3. Identify unnecessary services
4. Review service account permissions
5. Check for deprecated protocols
        """,
        expected_result="Only business-required services running; no deprecated protocols (SMBv1, TLS 1.0)",
        remediation_steps=[
            RemediationStep(1, "List running services",
                          "Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object Name, DisplayName, StartType",
                          "powershell", "15 minutes"),
            RemediationStep(2, "Disable SMBv1",
                          "Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol",
                          "powershell", "15 minutes", True),
            RemediationStep(3, "Disable TLS 1.0/1.1",
                          "# Registry: HKLM:\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols",
                          "powershell", "30 minutes", True),
            RemediationStep(4, "Stop and disable unnecessary services",
                          "Stop-Service -Name 'ServiceName' -Force; Set-Service -Name 'ServiceName' -StartupType Disabled",
                          "powershell", "30 minutes"),
        ],
        references=["CIS Controls v8 4.8", "NIST SP 800-53 CM-7"],
        nist_mapping=["CM-7", "CM-7(1)", "CM-7(2)"],
        cis_mapping="4.8",
        default_severity=Severity.MEDIUM
    ),
    
    "SRV-003": Control(
        id="SRV-003",
        name="Database Security",
        description="Database servers should be hardened with proper access controls and encryption.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Server Security",
        check_procedure="""
1. Review database authentication mode
2. Check for default/weak passwords
3. Verify TDE or column encryption
4. Review database user permissions
5. Audit database activity logging
        """,
        expected_result="Windows auth preferred; no default passwords; TDE enabled; least privilege access",
        remediation_steps=[
            RemediationStep(1, "Audit database users and permissions",
                          "SELECT name, type_desc FROM sys.server_principals WHERE type IN ('S', 'U', 'G')",
                          "sql", "30 minutes"),
            RemediationStep(2, "Enable TDE",
                          "CREATE DATABASE ENCRYPTION KEY WITH ALGORITHM = AES_256; ALTER DATABASE [DBName] SET ENCRYPTION ON",
                          "sql", "2 hours", True),
            RemediationStep(3, "Remove default sa account access",
                          "ALTER LOGIN sa DISABLE",
                          "sql", "15 minutes"),
            RemediationStep(4, "Enable audit logging",
                          "CREATE SERVER AUDIT [AuditName] TO FILE (FILEPATH = 'C:\\Audits\\');",
                          "sql", "1 hour"),
        ],
        references=["CIS SQL Server Benchmark", "NIST SP 800-53 SC-28"],
        nist_mapping=["SC-28", "AC-3", "AU-2"],
        cis_mapping="6.1",
        default_severity=Severity.CRITICAL
    ),
    
    "SRV-004": Control(
        id="SRV-004",
        name="File Server Permissions",
        description="File shares should have proper NTFS and share permissions with no open shares.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Server Security",
        check_procedure="""
1. Inventory all file shares
2. Review share permissions
3. Check NTFS permissions inheritance
4. Identify shares with Everyone access
5. Audit sensitive data locations
        """,
        expected_result="No Everyone/Anonymous share access; NTFS permissions aligned; sensitive data identified",
        remediation_steps=[
            RemediationStep(1, "List all shares and permissions",
                          "Get-SmbShare | ForEach-Object { Get-SmbShareAccess -Name $_.Name }",
                          "powershell", "30 minutes"),
            RemediationStep(2, "Remove Everyone from shares",
                          "Revoke-SmbShareAccess -Name 'ShareName' -AccountName 'Everyone' -Force",
                          "powershell", "1 hour"),
            RemediationStep(3, "Audit NTFS permissions",
                          "Get-Acl 'D:\\Share' | Format-List",
                          "powershell", "2 hours"),
            RemediationStep(4, "Enable Access-Based Enumeration",
                          "Set-SmbShare -Name 'ShareName' -FolderEnumerationMode AccessBased",
                          "powershell", "30 minutes"),
        ],
        references=["NIST SP 800-53 AC-3", "CIS Controls v8 3.3"],
        nist_mapping=["AC-3", "AC-6", "MP-2"],
        cis_mapping="3.3",
        default_severity=Severity.HIGH
    ),
    
    "SRV-005": Control(
        id="SRV-005",
        name="Web Server Security",
        description="Web servers should be hardened with secure configurations and valid certificates.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Server Security",
        check_procedure="""
1. Review TLS configuration
2. Check certificate validity and chain
3. Verify security headers
4. Audit web server modules
5. Check directory permissions
        """,
        expected_result="TLS 1.2+ only; valid certificates; security headers configured; modules minimized",
        remediation_steps=[
            RemediationStep(1, "Check TLS configuration",
                          "# Use SSL Labs or testssl.sh",
                          None, "30 minutes"),
            RemediationStep(2, "Configure security headers",
                          "# Add: X-Content-Type-Options, X-Frame-Options, HSTS, CSP",
                          None, "2 hours"),
            RemediationStep(3, "Remove unnecessary IIS modules",
                          "Remove-WindowsFeature Web-DAV-Publishing",
                          "powershell", "1 hour", True),
            RemediationStep(4, "Enable request filtering",
                          "# Configure IIS Request Filtering rules",
                          None, "2 hours"),
        ],
        references=["OWASP Secure Headers", "NIST SP 800-53 SC-8"],
        nist_mapping=["SC-8", "SC-17", "CM-7"],
        cis_mapping="9.1",
        default_severity=Severity.HIGH
    ),
    
    "SRV-006": Control(
        id="SRV-006",
        name="Email Server Security",
        description="Email servers should have spam filtering, encryption, and security protocols.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Server Security",
        check_procedure="""
1. Verify TLS for mail transport
2. Check SPF, DKIM, DMARC records
3. Review anti-spam/anti-malware
4. Audit email retention settings
5. Check open relay configuration
        """,
        expected_result="TLS required; SPF/DKIM/DMARC configured; not an open relay; spam filtering active",
        remediation_steps=[
            RemediationStep(1, "Configure TLS for connectors",
                          "Set-ReceiveConnector -Identity 'Internet' -RequireTLS $true",
                          "powershell", "1 hour"),
            RemediationStep(2, "Implement SPF record",
                          "# Add TXT record: v=spf1 include:_spf.domain.com -all",
                          "dns", "30 minutes"),
            RemediationStep(3, "Configure DKIM signing",
                          "# Enable DKIM in Exchange/O365",
                          None, "2 hours"),
            RemediationStep(4, "Implement DMARC policy",
                          "# Add TXT: _dmarc.domain.com v=DMARC1; p=quarantine; rua=mailto:reports@domain.com",
                          "dns", "30 minutes"),
        ],
        references=["NIST SP 800-53 SC-8", "CIS Controls v8 9.5"],
        nist_mapping=["SC-8", "SI-8", "SC-5"],
        cis_mapping="9.5",
        default_severity=Severity.HIGH
    ),
    
    "SRV-007": Control(
        id="SRV-007",
        name="Backup Server Protection",
        description="Backup infrastructure should be protected from ransomware and unauthorized access.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Server Security",
        check_procedure="""
1. Verify backup server hardening
2. Check for air-gapped/immutable backups
3. Review backup admin access
4. Audit backup encryption
5. Test restore procedures
        """,
        expected_result="Backup servers hardened; immutable storage; MFA for admin; encrypted; tested quarterly",
        remediation_steps=[
            RemediationStep(1, "Implement immutable backup storage",
                          "# Configure WORM or immutable snapshots",
                          None, "4-8 hours"),
            RemediationStep(2, "Enable MFA for backup admin access",
                          None, None, "2 hours"),
            RemediationStep(3, "Enable backup encryption",
                          "# Configure AES-256 encryption at rest",
                          None, "2 hours"),
            RemediationStep(4, "Schedule quarterly restore tests",
                          None, None, "4 hours"),
        ],
        references=["NIST SP 800-53 CP-9", "CIS Controls v8 11"],
        nist_mapping=["CP-9", "CP-9(1)", "SC-28"],
        cis_mapping="11.2",
        default_severity=Severity.CRITICAL
    ),
    
    "SRV-008": Control(
        id="SRV-008",
        name="Virtualization Security",
        description="Hypervisors should be hardened with proper isolation and access controls.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Server Security",
        check_procedure="""
1. Review hypervisor hardening
2. Check VM isolation settings
3. Verify management network segmentation
4. Audit hypervisor admin access
5. Check vSwitch security
        """,
        expected_result="Hardened hypervisor; management VLAN isolated; MFA for admin; vSwitch secured",
        remediation_steps=[
            RemediationStep(1, "Apply hypervisor hardening guide",
                          "# Apply VMware/Hyper-V hardening guide",
                          None, "4-8 hours"),
            RemediationStep(2, "Segment management network",
                          "# Dedicated VLAN for vCenter/SCVMM",
                          None, "4 hours", True),
            RemediationStep(3, "Configure vSwitch security",
                          "# Disable promiscuous mode, forged transmits, MAC changes",
                          None, "2 hours"),
            RemediationStep(4, "Implement MFA for hypervisor admin",
                          None, None, "2 hours"),
        ],
        references=["CIS VMware Benchmark", "NIST SP 800-53 SC-2"],
        nist_mapping=["SC-2", "SC-3", "AC-6"],
        cis_mapping="4.1",
        default_severity=Severity.HIGH
    ),
    
    "SRV-009": Control(
        id="SRV-009",
        name="Server Certificate Management",
        description="Server certificates should be properly managed with monitoring for expiration.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Server Security",
        check_procedure="""
1. Inventory all server certificates
2. Check certificate validity dates
3. Verify key sizes (2048+ RSA, 256+ ECC)
4. Review certificate authority trust
5. Check for automated renewal
        """,
        expected_result="All certs inventoried; 30-day expiry alerts; 2048+ bit keys; trusted CA",
        remediation_steps=[
            RemediationStep(1, "Inventory certificates",
                          "Get-ChildItem -Path Cert:\\LocalMachine\\My | Select-Object Subject, NotAfter, Thumbprint",
                          "powershell", "1 hour"),
            RemediationStep(2, "Set up expiry monitoring",
                          "# Configure certificate monitoring in SIEM or dedicated tool",
                          None, "2-4 hours"),
            RemediationStep(3, "Replace weak certificates",
                          "# Request new 2048+ bit certificates",
                          None, "4 hours"),
            RemediationStep(4, "Implement automated renewal",
                          "# Configure Let's Encrypt or internal CA auto-renewal",
                          None, "4 hours"),
        ],
        references=["NIST SP 800-53 SC-17", "CIS Controls v8 3.10"],
        nist_mapping=["SC-17", "IA-5", "CM-3"],
        cis_mapping="3.10",
        default_severity=Severity.MEDIUM
    ),
    
    "SRV-010": Control(
        id="SRV-010",
        name="Server Access Logging",
        description="Server access and administrative actions should be logged and monitored.",
        family=ControlFamily.AUDIT_ACCOUNTABILITY,
        category="Server Security",
        check_procedure="""
1. Verify Windows Security log configuration
2. Check for administrative action logging
3. Review log forwarding to SIEM
4. Audit log retention
5. Check for tamper protection
        """,
        expected_result="All admin actions logged; forwarded to SIEM; 1-year retention; tamper-protected",
        remediation_steps=[
            RemediationStep(1, "Configure advanced audit policy",
                          "auditpol /set /category:'Logon/Logoff' /success:enable /failure:enable",
                          "cmd", "1 hour"),
            RemediationStep(2, "Configure Windows Event Forwarding",
                          "wecutil qc",
                          "cmd", "2-4 hours"),
            RemediationStep(3, "Enable log protection",
                          "# Configure SIEM to detect log clearing",
                          None, "2 hours"),
            RemediationStep(4, "Set 1-year retention",
                          "wevtutil sl Security /ms:4294967296 /rt:true /ab:true",
                          "cmd", "30 minutes"),
        ],
        references=["NIST SP 800-53 AU-2", "CIS Controls v8 8.2"],
        nist_mapping=["AU-2", "AU-3", "AU-9"],
        cis_mapping="8.2",
        default_severity=Severity.HIGH
    ),
}

# ============================================================================
# DATA PROTECTION CONTROLS
# ============================================================================

DATA_CONTROLS = {
    "DAT-001": Control(
        id="DAT-001",
        name="Data Classification",
        description="Data should be classified according to sensitivity with appropriate labels.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Data Protection",
        check_procedure="""
1. Review data classification policy
2. Check classification tool deployment
3. Verify labeling of sensitive repositories
4. Audit user training on classification
5. Check DLP policy alignment
        """,
        expected_result="Classification policy defined; tools deployed; users trained; DLP aligned",
        remediation_steps=[
            RemediationStep(1, "Define data classification levels",
                          None, None, "4 hours"),
            RemediationStep(2, "Deploy classification tools",
                          "# Microsoft AIP, Boldon James, etc.",
                          None, "1-2 weeks"),
            RemediationStep(3, "Train users on classification",
                          None, None, "4 hours"),
            RemediationStep(4, "Configure DLP policies per classification",
                          None, None, "4-8 hours"),
        ],
        references=["NIST SP 800-53 RA-2", "CIS Controls v8 3.1"],
        nist_mapping=["RA-2", "SC-16", "MP-3"],
        cis_mapping="3.1",
        default_severity=Severity.MEDIUM
    ),
    
    "DAT-002": Control(
        id="DAT-002",
        name="Data Loss Prevention",
        description="DLP controls should prevent unauthorized data exfiltration.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Data Protection",
        check_procedure="""
1. Verify DLP solution deployment
2. Review DLP policies and rules
3. Check email DLP coverage
4. Audit endpoint DLP agents
5. Review DLP incident reports
        """,
        expected_result="DLP on email, endpoints, and cloud; policies for PII/PHI/PCI; incidents reviewed",
        remediation_steps=[
            RemediationStep(1, "Deploy DLP solution",
                          "# Microsoft DLP, Symantec DLP, Digital Guardian",
                          None, "1-2 weeks"),
            RemediationStep(2, "Configure PII detection rules",
                          "# SSN, credit cards, health records patterns",
                          None, "4-8 hours"),
            RemediationStep(3, "Enable email DLP",
                          "# Configure transport rules for sensitive data",
                          None, "4 hours"),
            RemediationStep(4, "Deploy endpoint DLP agents",
                          None, None, "1 week"),
        ],
        references=["NIST SP 800-53 SC-7", "CIS Controls v8 3.13"],
        nist_mapping=["SC-7", "AC-4", "MP-5"],
        cis_mapping="3.13",
        default_severity=Severity.HIGH
    ),
    
    "DAT-003": Control(
        id="DAT-003",
        name="Encryption at Rest",
        description="Sensitive data should be encrypted when stored.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Data Protection",
        check_procedure="""
1. Inventory sensitive data locations
2. Verify encryption on file servers
3. Check database encryption (TDE)
4. Review backup encryption
5. Audit key management
        """,
        expected_result="All sensitive data encrypted; AES-256 minimum; keys properly managed",
        remediation_steps=[
            RemediationStep(1, "Enable EFS for file servers",
                          "# Configure EFS via GPO for sensitive folders",
                          "gpo", "4 hours"),
            RemediationStep(2, "Enable TDE on databases",
                          "ALTER DATABASE [DBName] SET ENCRYPTION ON",
                          "sql", "2 hours", True),
            RemediationStep(3, "Encrypt backup files",
                          "# Configure backup software encryption",
                          None, "2 hours"),
            RemediationStep(4, "Implement key management solution",
                          None, None, "1-2 weeks"),
        ],
        references=["NIST SP 800-53 SC-28", "CIS Controls v8 3.11"],
        nist_mapping=["SC-28", "SC-28(1)", "SC-12"],
        cis_mapping="3.11",
        default_severity=Severity.HIGH
    ),
    
    "DAT-004": Control(
        id="DAT-004",
        name="Encryption in Transit",
        description="Data should be encrypted during transmission over networks.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Data Protection",
        check_procedure="""
1. Verify TLS configuration on web servers
2. Check SMTP TLS requirements
3. Review VPN encryption
4. Audit internal service encryption
5. Check for unencrypted protocols
        """,
        expected_result="TLS 1.2+ required; no unencrypted protocols for sensitive data; HSTS enabled",
        remediation_steps=[
            RemediationStep(1, "Disable TLS 1.0/1.1",
                          "# Registry or IIS Crypto tool",
                          "powershell", "1 hour", True),
            RemediationStep(2, "Enable SMTP TLS",
                          "Set-ReceiveConnector -RequireTLS $true",
                          "powershell", "1 hour"),
            RemediationStep(3, "Enable HSTS on web servers",
                          "# Add Strict-Transport-Security header",
                          None, "1 hour"),
            RemediationStep(4, "Migrate from unencrypted protocols",
                          "# Replace Telnet with SSH, FTP with SFTP, HTTP with HTTPS",
                          None, "4-8 hours"),
        ],
        references=["NIST SP 800-53 SC-8", "CIS Controls v8 3.10"],
        nist_mapping=["SC-8", "SC-8(1)", "SC-23"],
        cis_mapping="3.10",
        default_severity=Severity.HIGH
    ),
    
    "DAT-005": Control(
        id="DAT-005",
        name="Backup & Recovery",
        description="Critical data should be backed up regularly with tested recovery procedures.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Data Protection",
        check_procedure="""
1. Review backup schedule and scope
2. Verify offsite/cloud backup copies
3. Check backup integrity testing
4. Audit restore testing frequency
5. Review RTO/RPO compliance
        """,
        expected_result="Daily backups; 3-2-1 rule followed; quarterly restore tests; RTO/RPO documented",
        remediation_steps=[
            RemediationStep(1, "Document backup scope and schedule",
                          None, None, "2 hours"),
            RemediationStep(2, "Implement 3-2-1 backup strategy",
                          "# 3 copies, 2 media types, 1 offsite",
                          None, "1 week"),
            RemediationStep(3, "Configure backup integrity checks",
                          "# Enable backup verification/checksums",
                          None, "2 hours"),
            RemediationStep(4, "Schedule quarterly restore tests",
                          None, None, "4 hours per test"),
        ],
        references=["NIST SP 800-53 CP-9", "CIS Controls v8 11.1"],
        nist_mapping=["CP-9", "CP-9(1)", "CP-10"],
        cis_mapping="11.1",
        default_severity=Severity.CRITICAL
    ),
    
    "DAT-006": Control(
        id="DAT-006",
        name="Data Retention Policy",
        description="Data should be retained according to policy and securely disposed when expired.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Data Protection",
        check_procedure="""
1. Review data retention policy
2. Verify retention automation
3. Check disposal procedures
4. Audit legal hold process
5. Review compliance requirements
        """,
        expected_result="Retention policy defined; automated enforcement; secure disposal; legal hold supported",
        remediation_steps=[
            RemediationStep(1, "Define retention schedules by data type",
                          None, None, "4-8 hours"),
            RemediationStep(2, "Configure automated retention",
                          "# Use retention labels/policies in O365/file systems",
                          None, "4-8 hours"),
            RemediationStep(3, "Implement secure disposal",
                          "# Configure secure delete/crypto-shredding",
                          None, "4 hours"),
            RemediationStep(4, "Create legal hold process",
                          None, None, "4 hours"),
        ],
        references=["NIST SP 800-53 SI-12", "CIS Controls v8 3.4"],
        nist_mapping=["SI-12", "MP-6", "AU-11"],
        cis_mapping="3.4",
        default_severity=Severity.MEDIUM
    ),
    
    "DAT-007": Control(
        id="DAT-007",
        name="Sensitive Data Handling",
        description="Procedures should exist for handling sensitive data throughout its lifecycle.",
        family=ControlFamily.MEDIA_PROTECTION,
        category="Data Protection",
        check_procedure="""
1. Review sensitive data procedures
2. Check secure sharing mechanisms
3. Verify secure printing controls
4. Audit data handling training
5. Review incident procedures
        """,
        expected_result="Handling procedures documented; secure sharing tools available; users trained",
        remediation_steps=[
            RemediationStep(1, "Document data handling procedures",
                          None, None, "4 hours"),
            RemediationStep(2, "Deploy secure file sharing",
                          "# OneDrive/SharePoint with DLP, or secure file transfer",
                          None, "4-8 hours"),
            RemediationStep(3, "Configure secure printing",
                          "# Implement pull printing/PIN release",
                          None, "4-8 hours"),
            RemediationStep(4, "Train users on procedures",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 MP-2", "CIS Controls v8 3.3"],
        nist_mapping=["MP-2", "MP-3", "MP-4"],
        cis_mapping="3.3",
        default_severity=Severity.MEDIUM
    ),
    
    "DAT-008": Control(
        id="DAT-008",
        name="Database Encryption",
        description="Databases containing sensitive data should use TDE or field-level encryption.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Data Protection",
        check_procedure="""
1. Inventory databases with sensitive data
2. Verify TDE configuration
3. Check field-level encryption for PII
4. Review encryption key management
5. Audit encryption performance impact
        """,
        expected_result="All sensitive databases encrypted; keys rotated annually; performance acceptable",
        remediation_steps=[
            RemediationStep(1, "Inventory sensitive databases",
                          None, None, "2-4 hours"),
            RemediationStep(2, "Enable TDE",
                          "CREATE DATABASE ENCRYPTION KEY WITH ALGORITHM = AES_256 ENCRYPTION BY SERVER CERTIFICATE [CertName]; ALTER DATABASE [DBName] SET ENCRYPTION ON",
                          "sql", "2 hours per database", True),
            RemediationStep(3, "Implement Always Encrypted for PII columns",
                          "# Configure Always Encrypted in SSMS",
                          "sql", "4-8 hours"),
            RemediationStep(4, "Configure key rotation",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 SC-28", "CIS Controls v8 3.11"],
        nist_mapping=["SC-28", "SC-12", "IA-5"],
        cis_mapping="3.11",
        default_severity=Severity.HIGH
    ),
    
    "DAT-009": Control(
        id="DAT-009",
        name="Key Management",
        description="Encryption keys should be securely managed with proper access controls and rotation.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Data Protection",
        check_procedure="""
1. Review key management solution
2. Verify key access controls
3. Check key rotation schedules
4. Audit key backup procedures
5. Review key destruction process
        """,
        expected_result="Dedicated key management; access logged; annual rotation; secure backup; destruction documented",
        remediation_steps=[
            RemediationStep(1, "Deploy HSM or key management solution",
                          "# Azure Key Vault, Thales, HashiCorp Vault",
                          None, "1-2 weeks"),
            RemediationStep(2, "Configure key access controls",
                          None, None, "4 hours"),
            RemediationStep(3, "Implement key rotation",
                          "# Configure annual rotation schedules",
                          None, "4 hours"),
            RemediationStep(4, "Document key backup and recovery",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 SC-12", "CIS Controls v8 3.11"],
        nist_mapping=["SC-12", "SC-12(1)", "SC-17"],
        cis_mapping="3.11",
        default_severity=Severity.HIGH
    ),
    
    "DAT-010": Control(
        id="DAT-010",
        name="Data Access Auditing",
        description="Access to sensitive data should be logged and monitored.",
        family=ControlFamily.AUDIT_ACCOUNTABILITY,
        category="Data Protection",
        check_procedure="""
1. Verify file access auditing
2. Check database access logging
3. Review SIEM integration
4. Audit alert configuration
5. Check log retention
        """,
        expected_result="All sensitive data access logged; integrated with SIEM; alerts for anomalies; 1-year retention",
        remediation_steps=[
            RemediationStep(1, "Enable file access auditing",
                          "auditpol /set /subcategory:'File System' /success:enable /failure:enable",
                          "cmd", "1 hour"),
            RemediationStep(2, "Configure SACL on sensitive folders",
                          "# Add auditing entries via folder properties",
                          None, "2-4 hours"),
            RemediationStep(3, "Enable SQL Server auditing",
                          "CREATE SERVER AUDIT [DataAccessAudit] TO FILE (FILEPATH = 'C:\\Audits\\') WITH (ON_FAILURE = CONTINUE)",
                          "sql", "2 hours"),
            RemediationStep(4, "Forward logs to SIEM",
                          None, None, "4 hours"),
        ],
        references=["NIST SP 800-53 AU-2", "CIS Controls v8 8.11"],
        nist_mapping=["AU-2", "AU-6", "AU-12"],
        cis_mapping="8.11",
        default_severity=Severity.HIGH
    ),
}

# ============================================================================
# IDENTITY & ACCESS MANAGEMENT CONTROLS
# ============================================================================

IAM_CONTROLS = {
    "IAM-001": Control(
        id="IAM-001",
        name="Multi-Factor Authentication",
        description="MFA should be required for all users, especially privileged accounts.",
        family=ControlFamily.IDENTIFICATION_AUTH,
        category="Identity & Access Management",
        check_procedure="""
1. Verify MFA solution deployment
2. Check MFA coverage for all users
3. Audit privileged account MFA enforcement
4. Review MFA methods (app, FIDO2, etc.)
5. Check MFA bypass exceptions
        """,
        expected_result="MFA required for all users; FIDO2/app preferred; minimal bypass exceptions documented",
        remediation_steps=[
            RemediationStep(1, "Deploy MFA solution",
                          "# Azure MFA, Duo, RSA SecurID",
                          None, "1-2 weeks"),
            RemediationStep(2, "Enforce MFA for privileged accounts first",
                          None, None, "1 day"),
            RemediationStep(3, "Roll out MFA to all users",
                          None, None, "2-4 weeks"),
            RemediationStep(4, "Disable weak MFA methods (SMS)",
                          None, None, "1 day"),
        ],
        references=["NIST SP 800-53 IA-2(1)", "CIS Controls v8 6.3"],
        nist_mapping=["IA-2", "IA-2(1)", "IA-2(2)"],
        cis_mapping="6.3",
        default_severity=Severity.CRITICAL
    ),
    
    "IAM-002": Control(
        id="IAM-002",
        name="Privileged Access Management",
        description="Privileged accounts should be managed with just-in-time access and monitoring.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Identity & Access Management",
        check_procedure="""
1. Inventory privileged accounts
2. Verify PAM solution deployment
3. Check just-in-time access configuration
4. Review session recording
5. Audit privileged access requests
        """,
        expected_result="All privileged access via PAM; JIT access; sessions recorded; requests approved",
        remediation_steps=[
            RemediationStep(1, "Inventory privileged accounts",
                          "Get-ADGroupMember 'Domain Admins' | Select-Object Name, SamAccountName",
                          "powershell", "2 hours"),
            RemediationStep(2, "Deploy PAM solution",
                          "# CyberArk, BeyondTrust, Delinea",
                          None, "4-8 weeks"),
            RemediationStep(3, "Configure JIT access",
                          "# Implement time-limited privilege elevation",
                          None, "2 weeks"),
            RemediationStep(4, "Enable session recording",
                          None, None, "1 week"),
        ],
        references=["NIST SP 800-53 AC-2(7)", "CIS Controls v8 6.5"],
        nist_mapping=["AC-2", "AC-2(7)", "AC-6(2)"],
        cis_mapping="6.5",
        default_severity=Severity.CRITICAL
    ),
    
    "IAM-003": Control(
        id="IAM-003",
        name="Role-Based Access Control",
        description="Access should be granted based on roles rather than individual permissions.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Identity & Access Management",
        check_procedure="""
1. Review RBAC implementation
2. Check role definitions
3. Verify role assignments
4. Audit direct permission grants
5. Review role governance
        """,
        expected_result="RBAC implemented; roles documented; minimal direct grants; annual role review",
        remediation_steps=[
            RemediationStep(1, "Define role catalog",
                          None, None, "1-2 weeks"),
            RemediationStep(2, "Create AD security groups for roles",
                          "New-ADGroup -Name 'Role_Finance_ReadOnly' -GroupScope Global -GroupCategory Security",
                          "powershell", "4-8 hours"),
            RemediationStep(3, "Migrate direct permissions to roles",
                          None, None, "2-4 weeks"),
            RemediationStep(4, "Implement role governance process",
                          None, None, "1 week"),
        ],
        references=["NIST SP 800-53 AC-2", "CIS Controls v8 6.8"],
        nist_mapping=["AC-2", "AC-3", "AC-6"],
        cis_mapping="6.8",
        default_severity=Severity.MEDIUM
    ),
    
    "IAM-004": Control(
        id="IAM-004",
        name="Account Lifecycle Management",
        description="User accounts should be properly provisioned, modified, and deprovisioned.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Identity & Access Management",
        check_procedure="""
1. Review provisioning process
2. Check HR system integration
3. Verify deprovisioning timeliness
4. Audit orphaned accounts
5. Check account modification logging
        """,
        expected_result="Automated provisioning; same-day deprovisioning; no orphaned accounts",
        remediation_steps=[
            RemediationStep(1, "Implement identity governance solution",
                          "# SailPoint, Saviynt, Microsoft Identity Manager",
                          None, "8-12 weeks"),
            RemediationStep(2, "Integrate with HR system",
                          None, None, "2-4 weeks"),
            RemediationStep(3, "Configure automated deprovisioning",
                          None, None, "2 weeks"),
            RemediationStep(4, "Run orphaned account audit",
                          "Get-ADUser -Filter * -Properties LastLogonDate | Where-Object {$_.LastLogonDate -lt (Get-Date).AddDays(-90)}",
                          "powershell", "2 hours"),
        ],
        references=["NIST SP 800-53 AC-2", "CIS Controls v8 5.1"],
        nist_mapping=["AC-2", "AC-2(3)", "AC-2(4)"],
        cis_mapping="5.1",
        default_severity=Severity.HIGH
    ),
    
    "IAM-005": Control(
        id="IAM-005",
        name="Password Vault/Management",
        description="Service and shared passwords should be stored in a secure vault.",
        family=ControlFamily.IDENTIFICATION_AUTH,
        category="Identity & Access Management",
        check_procedure="""
1. Verify password vault deployment
2. Check vault access controls
3. Review password rotation
4. Audit vault logging
5. Check emergency access procedures
        """,
        expected_result="All service passwords in vault; access logged; automatic rotation; emergency access documented",
        remediation_steps=[
            RemediationStep(1, "Deploy password vault",
                          "# CyberArk, HashiCorp Vault, Keeper",
                          None, "2-4 weeks"),
            RemediationStep(2, "Migrate service account passwords",
                          None, None, "2-4 weeks"),
            RemediationStep(3, "Configure automatic rotation",
                          None, None, "1 week"),
            RemediationStep(4, "Document emergency access",
                          None, None, "4 hours"),
        ],
        references=["NIST SP 800-53 IA-5(7)", "CIS Controls v8 5.2"],
        nist_mapping=["IA-5", "IA-5(7)", "SC-28"],
        cis_mapping="5.2",
        default_severity=Severity.HIGH
    ),
    
    "IAM-006": Control(
        id="IAM-006",
        name="Session Management",
        description="User sessions should timeout appropriately and be secured.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Identity & Access Management",
        check_procedure="""
1. Review session timeout settings
2. Check for concurrent session limits
3. Verify session lock requirements
4. Audit privileged session handling
5. Check session logging
        """,
        expected_result="15-min idle timeout; session lock enabled; concurrent sessions limited for privileged",
        remediation_steps=[
            RemediationStep(1, "Configure screen saver timeout via GPO",
                          "# Computer Config > Admin Templates > Control Panel > Personalization",
                          "gpo", "1 hour"),
            RemediationStep(2, "Enable smart card removal policy",
                          "# Lock workstation on smart card removal",
                          "gpo", "30 minutes"),
            RemediationStep(3, "Configure web application session timeouts",
                          None, None, "2-4 hours"),
            RemediationStep(4, "Enable session logging",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 AC-12", "CIS Controls v8 6.2"],
        nist_mapping=["AC-11", "AC-12", "SC-10"],
        cis_mapping="6.2",
        default_severity=Severity.MEDIUM
    ),
    
    "IAM-007": Control(
        id="IAM-007",
        name="Access Review Process",
        description="User access should be reviewed periodically to ensure appropriate permissions.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Identity & Access Management",
        check_procedure="""
1. Review access review process
2. Check review frequency
3. Verify reviewer assignments
4. Audit review completion rates
5. Check remediation of findings
        """,
        expected_result="Quarterly reviews for privileged; annual for standard; >95% completion; findings remediated",
        remediation_steps=[
            RemediationStep(1, "Define access review policy",
                          None, None, "4 hours"),
            RemediationStep(2, "Implement access review tool",
                          "# Azure AD Access Reviews, SailPoint",
                          None, "2-4 weeks"),
            RemediationStep(3, "Assign reviewers to resources",
                          None, None, "1 week"),
            RemediationStep(4, "Schedule recurring reviews",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 AC-2(3)", "CIS Controls v8 5.1"],
        nist_mapping=["AC-2", "AC-2(3)", "CA-7"],
        cis_mapping="5.1",
        default_severity=Severity.MEDIUM
    ),
    
    "IAM-008": Control(
        id="IAM-008",
        name="Separation of Duties",
        description="Critical functions should require multiple people to complete (SoD).",
        family=ControlFamily.ACCESS_CONTROL,
        category="Identity & Access Management",
        check_procedure="""
1. Identify SoD-required functions
2. Review role conflicts
3. Verify approval workflows
4. Audit SoD violations
5. Check compensating controls
        """,
        expected_result="SoD matrix defined; conflicts detected; approval workflows in place; violations addressed",
        remediation_steps=[
            RemediationStep(1, "Define SoD matrix",
                          None, None, "1-2 weeks"),
            RemediationStep(2, "Implement SoD detection",
                          "# Configure identity governance tool for conflict detection",
                          None, "2-4 weeks"),
            RemediationStep(3, "Configure approval workflows",
                          None, None, "1 week"),
            RemediationStep(4, "Remediate existing violations",
                          None, None, "2-4 weeks"),
        ],
        references=["NIST SP 800-53 AC-5", "CIS Controls v8 6.1"],
        nist_mapping=["AC-5", "AC-6(3)", "CM-5"],
        cis_mapping="6.1",
        default_severity=Severity.MEDIUM
    ),
    
    "IAM-009": Control(
        id="IAM-009",
        name="Remote Access Security",
        description="Remote access should be secured with strong authentication and monitoring.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Identity & Access Management",
        check_procedure="""
1. Inventory remote access methods
2. Verify MFA for remote access
3. Check VPN/RDP security
4. Review remote access logging
5. Audit third-party access
        """,
        expected_result="All remote access via VPN; MFA required; sessions logged; third-party access controlled",
        remediation_steps=[
            RemediationStep(1, "Enforce MFA for VPN",
                          "# Configure RADIUS integration with MFA",
                          None, "4-8 hours"),
            RemediationStep(2, "Restrict RDP access",
                          "# Use RD Gateway or PAM for RDP access",
                          None, "1-2 weeks"),
            RemediationStep(3, "Enable remote access logging",
                          None, None, "4 hours"),
            RemediationStep(4, "Implement third-party access controls",
                          "# Vendor PAM or time-limited access",
                          None, "2-4 weeks"),
        ],
        references=["NIST SP 800-53 AC-17", "CIS Controls v8 6.6"],
        nist_mapping=["AC-17", "AC-17(1)", "AC-17(2)"],
        cis_mapping="6.6",
        default_severity=Severity.HIGH
    ),
    
    "IAM-010": Control(
        id="IAM-010",
        name="Identity Federation",
        description="Identity federation should be securely configured for external authentication.",
        family=ControlFamily.IDENTIFICATION_AUTH,
        category="Identity & Access Management",
        check_procedure="""
1. Inventory federation trusts
2. Verify federation security settings
3. Check certificate management
4. Review claims mapping
5. Audit federation logs
        """,
        expected_result="Federation trusts documented; secure algorithms; certificates valid; claims mapped correctly",
        remediation_steps=[
            RemediationStep(1, "Audit federation trusts",
                          "Get-ADFSRelyingPartyTrust | Select-Object Name, Enabled, TokenLifetime",
                          "powershell", "1 hour"),
            RemediationStep(2, "Update to secure algorithms",
                          "# Disable SHA-1, use SHA-256 minimum",
                          "powershell", "2 hours", True),
            RemediationStep(3, "Review and update certificates",
                          None, None, "2 hours"),
            RemediationStep(4, "Enable federation logging",
                          "# Enable ADFS auditing via GPO",
                          "gpo", "1 hour"),
        ],
        references=["NIST SP 800-53 IA-8", "CIS Controls v8 6.4"],
        nist_mapping=["IA-8", "IA-8(1)", "IA-8(4)"],
        cis_mapping="6.4",
        default_severity=Severity.MEDIUM
    ),
}

# ============================================================================
# MONITORING & LOGGING CONTROLS
# ============================================================================

MONITORING_CONTROLS = {
    "MON-001": Control(
        id="MON-001",
        name="SIEM Implementation",
        description="Security events should be collected and correlated in a SIEM solution.",
        family=ControlFamily.AUDIT_ACCOUNTABILITY,
        category="Monitoring & Logging",
        check_procedure="""
1. Verify SIEM deployment
2. Check log source coverage
3. Review correlation rules
4. Audit alert configuration
5. Check SIEM high availability
        """,
        expected_result="SIEM deployed; all critical sources integrated; correlation rules tuned; HA configured",
        remediation_steps=[
            RemediationStep(1, "Deploy SIEM solution",
                          "# Splunk, Microsoft Sentinel, IBM QRadar, Elastic",
                          None, "4-8 weeks"),
            RemediationStep(2, "Integrate critical log sources",
                          "# AD, firewalls, VPN, endpoints, servers",
                          None, "2-4 weeks"),
            RemediationStep(3, "Configure correlation rules",
                          None, None, "2-4 weeks"),
            RemediationStep(4, "Tune alert thresholds",
                          None, None, "2-4 weeks"),
        ],
        references=["NIST SP 800-53 SI-4", "CIS Controls v8 8.2"],
        nist_mapping=["SI-4", "AU-6", "AU-6(1)"],
        cis_mapping="8.2",
        default_severity=Severity.HIGH
    ),
    
    "MON-002": Control(
        id="MON-002",
        name="Log Collection & Aggregation",
        description="Logs should be collected from all sources and aggregated centrally.",
        family=ControlFamily.AUDIT_ACCOUNTABILITY,
        category="Monitoring & Logging",
        check_procedure="""
1. Inventory log sources
2. Verify log collection agents
3. Check log parsing
4. Review collection latency
5. Audit missing log sources
        """,
        expected_result="All critical sources collected; <5 min latency; logs properly parsed",
        remediation_steps=[
            RemediationStep(1, "Inventory critical log sources",
                          None, None, "4 hours"),
            RemediationStep(2, "Deploy log collection agents",
                          "# Splunk UF, Beats, Windows Event Forwarding",
                          None, "1-2 weeks"),
            RemediationStep(3, "Configure log parsing",
                          None, None, "1-2 weeks"),
            RemediationStep(4, "Set up collection monitoring",
                          None, None, "4 hours"),
        ],
        references=["NIST SP 800-53 AU-3", "CIS Controls v8 8.2"],
        nist_mapping=["AU-3", "AU-6", "AU-12"],
        cis_mapping="8.2",
        default_severity=Severity.HIGH
    ),
    
    "MON-003": Control(
        id="MON-003",
        name="Log Retention & Protection",
        description="Logs should be retained according to policy and protected from tampering.",
        family=ControlFamily.AUDIT_ACCOUNTABILITY,
        category="Monitoring & Logging",
        check_procedure="""
1. Review log retention settings
2. Verify log integrity protection
3. Check access controls on logs
4. Audit log archival process
5. Review compliance requirements
        """,
        expected_result="1-year online; 7-year archive; integrity protected; access restricted",
        remediation_steps=[
            RemediationStep(1, "Configure retention policies",
                          "# Set SIEM retention to 1 year minimum",
                          None, "2 hours"),
            RemediationStep(2, "Enable log integrity protection",
                          "# Enable WORM storage or signing",
                          None, "4 hours"),
            RemediationStep(3, "Restrict log access",
                          "# RBAC for log access",
                          None, "2 hours"),
            RemediationStep(4, "Configure archival",
                          "# Archive to cold storage after 1 year",
                          None, "4 hours"),
        ],
        references=["NIST SP 800-53 AU-9", "CIS Controls v8 8.1"],
        nist_mapping=["AU-9", "AU-9(2)", "AU-11"],
        cis_mapping="8.1",
        default_severity=Severity.MEDIUM
    ),
    
    "MON-004": Control(
        id="MON-004",
        name="Real-time Alerting",
        description="Critical security events should generate real-time alerts.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Monitoring & Logging",
        check_procedure="""
1. Review alert rules
2. Check alert destinations
3. Verify alert escalation
4. Audit alert response times
5. Check for alert fatigue
        """,
        expected_result="Critical events alert in <5 min; escalation defined; reasonable alert volume",
        remediation_steps=[
            RemediationStep(1, "Define critical alert use cases",
                          None, None, "4 hours"),
            RemediationStep(2, "Configure alert rules",
                          "# SIEM correlation rules for critical events",
                          None, "4-8 hours"),
            RemediationStep(3, "Set up alert destinations",
                          "# Email, SMS, PagerDuty, Teams",
                          None, "2 hours"),
            RemediationStep(4, "Define escalation procedures",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 SI-4(5)", "CIS Controls v8 8.11"],
        nist_mapping=["SI-4", "SI-4(5)", "IR-6"],
        cis_mapping="8.11",
        default_severity=Severity.HIGH
    ),
    
    "MON-005": Control(
        id="MON-005",
        name="Security Event Correlation",
        description="Related security events should be correlated to detect complex attacks.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Monitoring & Logging",
        check_procedure="""
1. Review correlation rules
2. Check multi-source correlation
3. Verify attack pattern detection
4. Audit correlation effectiveness
5. Check for MITRE ATT&CK coverage
        """,
        expected_result="Multi-source correlation; MITRE ATT&CK aligned; regular tuning",
        remediation_steps=[
            RemediationStep(1, "Map MITRE ATT&CK techniques to detection",
                          None, None, "1-2 weeks"),
            RemediationStep(2, "Configure correlation rules",
                          "# Chain authentication + network + endpoint events",
                          None, "2-4 weeks"),
            RemediationStep(3, "Test correlation effectiveness",
                          "# Run attack simulations",
                          None, "1 week"),
            RemediationStep(4, "Tune and refine rules",
                          None, None, "Ongoing"),
        ],
        references=["NIST SP 800-53 SI-4(4)", "CIS Controls v8 13.1"],
        nist_mapping=["SI-4", "SI-4(4)", "AU-6(5)"],
        cis_mapping="13.1",
        default_severity=Severity.MEDIUM
    ),
    
    "MON-006": Control(
        id="MON-006",
        name="Threat Detection Rules",
        description="Detection rules should be maintained for known threats and IOCs.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Monitoring & Logging",
        check_procedure="""
1. Review detection rule library
2. Check threat intel integration
3. Verify IOC feed ingestion
4. Audit rule update frequency
5. Check detection coverage
        """,
        expected_result="Threat intel integrated; IOC feeds active; rules updated weekly; tested regularly",
        remediation_steps=[
            RemediationStep(1, "Subscribe to threat intel feeds",
                          "# MISP, AlienVault OTX, commercial feeds",
                          None, "1-2 weeks"),
            RemediationStep(2, "Configure IOC feed ingestion",
                          None, None, "1 week"),
            RemediationStep(3, "Implement Sigma rules",
                          "# Deploy Sigma rules to SIEM",
                          None, "1-2 weeks"),
            RemediationStep(4, "Schedule rule updates",
                          None, None, "4 hours"),
        ],
        references=["NIST SP 800-53 SI-4", "CIS Controls v8 13.3"],
        nist_mapping=["SI-4", "RA-5(5)", "PM-16"],
        cis_mapping="13.3",
        default_severity=Severity.HIGH
    ),
    
    "MON-007": Control(
        id="MON-007",
        name="Network Traffic Analysis",
        description="Network traffic should be analyzed for threats and anomalies.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Monitoring & Logging",
        check_procedure="""
1. Verify NTA solution deployment
2. Check traffic visibility
3. Review anomaly detection
4. Audit threat detection
5. Check integration with SIEM
        """,
        expected_result="Full network visibility; east-west traffic monitored; anomaly baselines established",
        remediation_steps=[
            RemediationStep(1, "Deploy NTA solution",
                          "# Darktrace, ExtraHop, Cisco Stealthwatch",
                          None, "4-8 weeks"),
            RemediationStep(2, "Configure traffic mirroring",
                          "# SPAN/TAP for critical segments",
                          None, "1-2 weeks"),
            RemediationStep(3, "Establish traffic baselines",
                          None, None, "2-4 weeks"),
            RemediationStep(4, "Integrate with SIEM",
                          None, None, "1 week"),
        ],
        references=["NIST SP 800-53 SI-4(4)", "CIS Controls v8 13.6"],
        nist_mapping=["SI-4", "SI-4(4)", "AU-6"],
        cis_mapping="13.6",
        default_severity=Severity.MEDIUM
    ),
    
    "MON-008": Control(
        id="MON-008",
        name="User Behavior Analytics",
        description="User behavior should be baselined and monitored for anomalies.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Monitoring & Logging",
        check_procedure="""
1. Verify UBA/UEBA deployment
2. Check user activity collection
3. Review anomaly detection
4. Audit insider threat detection
5. Check alert configuration
        """,
        expected_result="UBA deployed; user activity baselined; insider threat use cases active",
        remediation_steps=[
            RemediationStep(1, "Deploy UBA solution",
                          "# Microsoft Sentinel, Splunk UBA, Exabeam",
                          None, "4-8 weeks"),
            RemediationStep(2, "Configure user activity collection",
                          "# Authentication, file access, email activity",
                          None, "2 weeks"),
            RemediationStep(3, "Establish behavioral baselines",
                          None, None, "4-8 weeks"),
            RemediationStep(4, "Configure insider threat alerts",
                          None, None, "1 week"),
        ],
        references=["NIST SP 800-53 SI-4(13)", "CIS Controls v8 13.10"],
        nist_mapping=["SI-4", "AC-2(12)", "AU-6"],
        cis_mapping="13.10",
        default_severity=Severity.MEDIUM
    ),
    
    "MON-009": Control(
        id="MON-009",
        name="Incident Response Integration",
        description="Monitoring systems should integrate with incident response workflows.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Monitoring & Logging",
        check_procedure="""
1. Verify SOAR/ticketing integration
2. Check automated response playbooks
3. Review escalation workflows
4. Audit ticket creation
5. Check metrics tracking
        """,
        expected_result="SOAR integrated; playbooks automated; tickets auto-created; metrics tracked",
        remediation_steps=[
            RemediationStep(1, "Deploy SOAR solution",
                          "# Splunk SOAR, Microsoft Sentinel, Palo Alto XSOAR",
                          None, "4-8 weeks"),
            RemediationStep(2, "Integrate with ticketing",
                          "# ServiceNow, Jira integration",
                          None, "1-2 weeks"),
            RemediationStep(3, "Create automated playbooks",
                          "# Phishing, malware, account compromise",
                          None, "4-8 weeks"),
            RemediationStep(4, "Configure metrics dashboard",
                          None, None, "1 week"),
        ],
        references=["NIST SP 800-53 IR-4", "CIS Controls v8 17.4"],
        nist_mapping=["IR-4", "IR-4(1)", "IR-5"],
        cis_mapping="17.4",
        default_severity=Severity.MEDIUM
    ),
    
    "MON-010": Control(
        id="MON-010",
        name="Compliance Reporting",
        description="Monitoring systems should generate compliance reports for audits.",
        family=ControlFamily.AUDIT_ACCOUNTABILITY,
        category="Monitoring & Logging",
        check_procedure="""
1. Review compliance report templates
2. Check automated report generation
3. Verify report accuracy
4. Audit report distribution
5. Check audit trail preservation
        """,
        expected_result="Automated compliance reports; monthly generation; audit trail maintained",
        remediation_steps=[
            RemediationStep(1, "Define compliance report requirements",
                          None, None, "4 hours"),
            RemediationStep(2, "Configure report templates",
                          "# PCI, HIPAA, SOC2, NIST templates",
                          None, "1-2 weeks"),
            RemediationStep(3, "Schedule automated generation",
                          None, None, "4 hours"),
            RemediationStep(4, "Configure report distribution",
                          None, None, "2 hours"),
        ],
        references=["NIST SP 800-53 AU-6", "CIS Controls v8 8.12"],
        nist_mapping=["AU-6", "CA-2", "CA-7"],
        cis_mapping="8.12",
        default_severity=Severity.LOW
    ),
}


# ============================================================================
# VULNERABILITY MANAGEMENT CONTROLS
# ============================================================================

VM_CONTROLS = {
    "VM-001": Control(
        id="VM-001",
        name="Vulnerability Scanning Program",
        description="Automated vulnerability scanning must be conducted at least weekly on all networked assets with authenticated scans.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Vulnerability Management",
        check_procedure="""
1. Verify scanning tool is installed and configured
2. Review scan schedules
3. Confirm authenticated scan credentials
4. Check scan coverage percentage
5. Review last scan date
        """,
        expected_result="100% asset coverage with authenticated scans running weekly",
        remediation_steps=[
            RemediationStep(step_number=1, description="Install and configure vulnerability scanner", command="Install-Module -Name Nessus -Force; Start-NessusScan -Target '10.0.0.0/8' -Policy 'Full Audit'", script_type="powershell", estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure authenticated scan credentials", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
            RemediationStep(step_number=3, description="Set scan schedule to weekly", command=None, script_type=None, estimated_time="15 minutes", requires_downtime=False),
            RemediationStep(step_number=4, description="Configure scan exclusion list for fragile systems", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
        ],
        references=['NIST SP 800-53 RA-5', 'CIS Controls v8 7.1'],
        nist_mapping=['RA-5', 'RA-5(2)', 'SI-2'],
        cis_mapping="7.1",
        default_severity=Severity.CRITICAL,
    ),
    "VM-002": Control(
        id="VM-002",
        name="Vulnerability Remediation SLAs",
        description="Critical vulnerabilities must be remediated within 24 hours, High within 7 days, Medium within 30 days, Low within 90 days.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Vulnerability Management",
        check_procedure="""
1. Review vulnerability remediation policy
2. Check current open vulnerability aging
3. Verify SLA compliance rates
4. Review exception process
        """,
        expected_result="SLA compliance rate >95% across all severity levels",
        remediation_steps=[
            RemediationStep(step_number=1, description="Document remediation SLA policy", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure SLA tracking in vuln management tool", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Set up automated SLA breach alerts", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
        ],
        references=['NIST SP 800-53 SI-2'],
        nist_mapping=['RA-5(5)', 'SI-2', 'SI-2(2)'],
        cis_mapping="7.4",
        default_severity=Severity.HIGH,
    ),
    "VM-003": Control(
        id="VM-003",
        name="Asset Discovery & Inventory",
        description="Continuous asset discovery must identify all hardware and software on the network within 24 hours of connection.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Vulnerability Management",
        check_procedure="""
1. Run asset discovery scan
2. Compare discovered assets to CMDB
3. Identify rogue devices
4. Verify software inventory accuracy
        """,
        expected_result="Asset inventory matches discovered devices within 5% variance",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy network discovery tool", command="Install-WindowsFeature -Name NPAS; Enable-NetFirewallRule -DisplayGroup 'Network Discovery'", script_type="powershell", estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure CMDB integration", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Schedule daily discovery scans", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
        ],
        references=['NIST SP 800-53 CM-8', 'CIS Controls v8 1.1'],
        nist_mapping=['CM-8', 'CM-8(1)', 'PM-5'],
        cis_mapping="1.1",
        default_severity=Severity.HIGH,
    ),
    "VM-004": Control(
        id="VM-004",
        name="Penetration Testing",
        description="Annual penetration testing must be conducted by qualified personnel covering internal and external attack surfaces.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Vulnerability Management",
        check_procedure="""
1. Review last penetration test report
2. Verify tester qualifications
3. Check remediation of prior findings
4. Confirm scope coverage
        """,
        expected_result="Annual pentest completed within last 12 months with all critical findings remediated",
        remediation_steps=[
            RemediationStep(step_number=1, description="Engage qualified penetration testing firm", command=None, script_type=None, estimated_time="2 weeks", requires_downtime=False),
            RemediationStep(step_number=2, description="Define rules of engagement and scope", command=None, script_type=None, estimated_time="1 day", requires_downtime=False),
            RemediationStep(step_number=3, description="Remediate critical/high findings", command=None, script_type=None, estimated_time="Variable", requires_downtime=True),
        ],
        references=['NIST SP 800-53 CA-8', 'PTES Standard'],
        nist_mapping=['CA-8', 'CA-8(1)', 'RA-5(4)'],
        cis_mapping="18.1",
        default_severity=Severity.HIGH,
    ),
    "VM-005": Control(
        id="VM-005",
        name="Threat Intelligence Integration",
        description="Threat intelligence feeds should be integrated with vulnerability management to prioritize exploitation-likely vulnerabilities.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Vulnerability Management",
        check_procedure="""
1. Verify threat intel feed subscriptions
2. Check integration with vuln scanner
3. Review CISA KEV catalog integration
4. Confirm EPSS scoring enabled
        """,
        expected_result="At least 2 threat intel feeds integrated; CISA KEV alerts automated",
        remediation_steps=[
            RemediationStep(step_number=1, description="Subscribe to CISA KEV catalog feed", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=2, description="Integrate threat feeds with scanning platform", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure automated alerting for actively exploited vulns", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['CISA KEV Catalog', 'EPSS Model'],
        nist_mapping=['RA-5(6)', 'PM-16', 'SI-5'],
        cis_mapping="7.6",
        default_severity=Severity.MEDIUM,
    ),
    "VM-006": Control(
        id="VM-006",
        name="Web Application Scanning",
        description="All web applications must be scanned for OWASP Top 10 vulnerabilities monthly.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Vulnerability Management",
        check_procedure="""
1. Inventory all web applications
2. Verify DAST scanner configuration
3. Review scan results for OWASP Top 10
4. Check remediation tracking
        """,
        expected_result="All web apps scanned monthly; no critical OWASP findings unresolved >7 days",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy web application scanner (DAST)", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure scan profiles for each application", command=None, script_type=None, estimated_time="2 hours per app", requires_downtime=False),
            RemediationStep(step_number=3, description="Schedule monthly automated scans", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
        ],
        references=['OWASP Top 10', 'NIST SP 800-53 RA-5'],
        nist_mapping=['RA-5', 'SA-11(8)', 'SI-10'],
        cis_mapping="16.12",
        default_severity=Severity.HIGH,
    ),
    "VM-007": Control(
        id="VM-007",
        name="Container Image Scanning",
        description="All container images must be scanned for vulnerabilities before deployment and regularly in registries.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Vulnerability Management",
        check_procedure="""
1. Verify container registry scanning
2. Check CI/CD pipeline integration
3. Review base image update policy
4. Confirm runtime scanning
        """,
        expected_result="No containers deployed with Critical/High vulnerabilities",
        remediation_steps=[
            RemediationStep(step_number=1, description="Install container scanning tool in CI/CD pipeline", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure registry scanning schedule", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Block deployment of non-compliant images", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['CIS Docker Benchmark', 'NIST SP 800-190'],
        nist_mapping=['RA-5', 'SA-10', 'SI-7'],
        cis_mapping="16.4",
        default_severity=Severity.HIGH,
    ),
    "VM-008": Control(
        id="VM-008",
        name="Database Vulnerability Assessment",
        description="Database systems must be assessed for misconfigurations, default credentials, and known CVEs quarterly.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Vulnerability Management",
        check_procedure="""
1. Inventory all database instances
2. Run database-specific vulnerability scan
3. Check for default credentials
4. Review patch levels
        """,
        expected_result="All databases scanned quarterly; no default credentials; patches current",
        remediation_steps=[
            RemediationStep(step_number=1, description="Run database vulnerability scanner", command="Invoke-SqlVulnerabilityAssessment -ServerInstance 'SQLSERVER01' -DatabaseName 'ALL'", script_type="powershell", estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Remove default credentials", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
            RemediationStep(step_number=3, description="Apply latest security patches", command=None, script_type=None, estimated_time="4 hours", requires_downtime=True),
        ],
        references=['CIS Database Benchmarks', 'NIST SP 800-53 RA-5'],
        nist_mapping=['RA-5', 'IA-5', 'CM-6'],
        cis_mapping="7.5",
        default_severity=Severity.HIGH,
    ),
    "VM-009": Control(
        id="VM-009",
        name="Vulnerability Exception Management",
        description="All vulnerability exceptions must be documented with risk acceptance, compensating controls, and expiration dates.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Vulnerability Management",
        check_procedure="""
1. Review exception register
2. Verify all exceptions have AO approval
3. Check expiration dates
4. Confirm compensating controls are in place
        """,
        expected_result="All exceptions documented, approved, and within expiration date",
        remediation_steps=[
            RemediationStep(step_number=1, description="Establish exception management process", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Create exception request template", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Set up expiration tracking and alerts", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['NIST SP 800-53 RA-3', 'RMF Process Guide'],
        nist_mapping=['RA-3', 'PM-9', 'CA-5'],
        cis_mapping="7.7",
        default_severity=Severity.MEDIUM,
    ),
    "VM-010": Control(
        id="VM-010",
        name="Zero-Day Response Procedure",
        description="Organization must have a documented zero-day response procedure with notification within 4 hours of disclosure.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Vulnerability Management",
        check_procedure="""
1. Review zero-day response plan
2. Verify notification chain
3. Check last zero-day response time
4. Confirm mitigation playbooks exist
        """,
        expected_result="Documented procedure with <4 hour notification SLA and tested playbooks",
        remediation_steps=[
            RemediationStep(step_number=1, description="Document zero-day response procedure", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Establish notification chain and escalation", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Create mitigation playbook templates", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=4, description="Conduct tabletop exercise", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['CISA Vulnerability Disclosure', 'NIST SP 800-61'],
        nist_mapping=['IR-4', 'IR-5', 'SI-5'],
        cis_mapping="17.4",
        default_severity=Severity.HIGH,
    ),
}

# ============================================================================
# CONFIGURATION MANAGEMENT CONTROLS
# ============================================================================

CFG_CONTROLS = {
    "CFG-001": Control(
        id="CFG-001",
        name="Baseline Configuration Standards",
        description="All systems must have documented secure baseline configurations based on CIS Benchmarks or DISA STIGs.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Configuration Management",
        check_procedure="""
1. Review baseline documentation
2. Compare active configs to baselines
3. Check for unauthorized deviations
4. Verify baseline update schedule
        """,
        expected_result="All systems compliant with documented baselines; deviations <5%",
        remediation_steps=[
            RemediationStep(step_number=1, description="Download applicable CIS Benchmarks", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=2, description="Create GPO templates from benchmarks", command="Import-GPO -BackupGpoName 'CIS_Win11_L1' -TargetName 'Workstation_Baseline' -Path 'C:\\GPOBackups'", script_type="powershell", estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Deploy baselines via Group Policy", command=None, script_type=None, estimated_time="2 hours", requires_downtime=True),
            RemediationStep(step_number=4, description="Configure compliance scanning", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['CIS Benchmarks', 'DISA STIGs'],
        nist_mapping=['CM-2', 'CM-2(1)', 'CM-6'],
        cis_mapping="4.1",
        default_severity=Severity.HIGH,
    ),
    "CFG-002": Control(
        id="CFG-002",
        name="Change Management Process",
        description="All changes to production systems must follow a formal change management process with CAB approval.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Configuration Management",
        check_procedure="""
1. Review change management policy
2. Audit recent changes against tickets
3. Check for unauthorized changes
4. Verify rollback plans exist
        """,
        expected_result="100% of production changes have approved change tickets",
        remediation_steps=[
            RemediationStep(step_number=1, description="Implement change management tool", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Define change categories and approval workflows", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Train staff on change management process", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=4, description="Enable automated change detection", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['ITIL Change Management', 'NIST SP 800-53 CM-3'],
        nist_mapping=['CM-3', 'CM-3(2)', 'CM-5'],
        cis_mapping="4.8",
        default_severity=Severity.HIGH,
    ),
    "CFG-003": Control(
        id="CFG-003",
        name="Golden Image Management",
        description="Standardized golden images must be maintained for all OS deployments, updated monthly with latest patches.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Configuration Management",
        check_procedure="""
1. Verify golden image repository
2. Check image patch levels
3. Review image hardening checklist
4. Confirm image update schedule
        """,
        expected_result="Golden images updated within 30 days of Patch Tuesday; hardened per baseline",
        remediation_steps=[
            RemediationStep(step_number=1, description="Create golden image build process", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Apply CIS Benchmark hardening", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Automate monthly image updates", command="New-ScheduledTask -Action (New-ScheduledTaskAction -Execute 'C:\\Scripts\\Update-GoldenImage.ps1') -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -WeeksInterval 4)", script_type="powershell", estimated_time="2 hours", requires_downtime=False),
        ],
        references=['CIS Benchmarks', 'NIST SP 800-53 CM-2'],
        nist_mapping=['CM-2', 'CM-3', 'SI-2'],
        cis_mapping="4.2",
        default_severity=Severity.MEDIUM,
    ),
    "CFG-004": Control(
        id="CFG-004",
        name="Software Inventory Control",
        description="Only authorized software may be installed; unauthorized software must be detected and removed within 24 hours.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Configuration Management",
        check_procedure="""
1. Run software inventory scan
2. Compare against authorized software list
3. Identify unauthorized installations
4. Verify removal process
        """,
        expected_result="No unauthorized software found; inventory updated within 24 hours",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy software inventory agent", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Create authorized software whitelist", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure automated detection of unauthorized software", command="Get-WmiObject Win32_Product | Where-Object {$_.Name -notin (Get-Content 'C:\\Config\\ApprovedSoftware.txt')} | Export-Csv 'UnauthorizedSoftware.csv'", script_type="powershell", estimated_time="1 hour", requires_downtime=False),
        ],
        references=['CIS Controls v8 2.1', 'NIST SP 800-53 CM-11'],
        nist_mapping=['CM-7(5)', 'CM-8(3)', 'CM-11'],
        cis_mapping="2.1",
        default_severity=Severity.HIGH,
    ),
    "CFG-005": Control(
        id="CFG-005",
        name="Hardware Inventory Control",
        description="All hardware assets must be inventoried in a CMDB with automated discovery reconciliation.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Configuration Management",
        check_procedure="""
1. Export CMDB inventory
2. Run network discovery
3. Compare and identify discrepancies
4. Verify asset tagging
        """,
        expected_result="CMDB matches network discovery within 2% variance",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy CMDB solution", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure automated discovery integration", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Establish asset tagging and labeling process", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['CIS Controls v8 1.1', 'NIST SP 800-53 CM-8'],
        nist_mapping=['CM-8', 'CM-8(1)', 'PM-5'],
        cis_mapping="1.1",
        default_severity=Severity.MEDIUM,
    ),
    "CFG-006": Control(
        id="CFG-006",
        name="Configuration Drift Detection",
        description="Automated tools must detect configuration drift from baselines and alert within 1 hour.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Configuration Management",
        check_procedure="""
1. Verify drift detection tool deployment
2. Review recent drift alerts
3. Check remediation of drifted configs
4. Confirm baseline comparison accuracy
        """,
        expected_result="Drift detection active on all critical systems; alerts within 1 hour",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy configuration management tool (DSC/Puppet/Ansible)", command="Install-Module -Name PSDscResources -Force", script_type="powershell", estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Define desired state configurations", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Enable drift detection and alerting", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['Microsoft DSC', 'NIST SP 800-53 CM-6'],
        nist_mapping=['CM-3(5)', 'CM-6(1)', 'SI-7'],
        cis_mapping="4.9",
        default_severity=Severity.MEDIUM,
    ),
    "CFG-007": Control(
        id="CFG-007",
        name="Firmware Security Management",
        description="Firmware on all critical hardware must be inventoried, updated, and verified against known vulnerabilities.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Configuration Management",
        check_procedure="""
1. Inventory firmware versions on servers/network devices
2. Compare against vendor security advisories
3. Verify firmware integrity
4. Check update schedule
        """,
        expected_result="All firmware current; no known vulnerable firmware versions deployed",
        remediation_steps=[
            RemediationStep(step_number=1, description="Inventory all firmware versions", command="Get-WmiObject Win32_BIOS | Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate", script_type="powershell", estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Subscribe to vendor firmware advisories", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Schedule firmware update during maintenance window", command=None, script_type=None, estimated_time="4 hours", requires_downtime=True),
        ],
        references=['NIST SP 800-147', 'NIST SP 800-53 SI-7'],
        nist_mapping=['SI-7(9)', 'CM-6', 'SA-12'],
        cis_mapping="1.5",
        default_severity=Severity.MEDIUM,
    ),
    "CFG-008": Control(
        id="CFG-008",
        name="Network Device Configuration Backup",
        description="Network device configurations must be backed up daily with version control and change tracking.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Configuration Management",
        check_procedure="""
1. Verify backup automation
2. Check backup frequency
3. Test configuration restore
4. Review version history
        """,
        expected_result="Daily backups with 90-day retention; successful restore test within last quarter",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure RANCID/Oxidized for network device backup", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Schedule daily backup jobs", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure change diff notifications", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['CIS Network Device Benchmarks', 'NIST SP 800-53 CP-9'],
        nist_mapping=['CM-2', 'CP-9', 'CM-3'],
        cis_mapping="4.3",
        default_severity=Severity.MEDIUM,
    ),
    "CFG-009": Control(
        id="CFG-009",
        name="Least Functionality Enforcement",
        description="Systems must be configured to provide only essential capabilities; unnecessary functions, ports, and services disabled.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Configuration Management",
        check_procedure="""
1. Run port scan on sample systems
2. Review enabled Windows features
3. Check running services against baseline
4. Verify unnecessary protocols disabled
        """,
        expected_result="No unnecessary ports/services/features enabled beyond baseline",
        remediation_steps=[
            RemediationStep(step_number=1, description="Audit running services", command="Get-Service | Where-Object Status -eq 'Running' | Export-Csv 'RunningServices.csv'", script_type="powershell", estimated_time="30 minutes", requires_downtime=False),
            RemediationStep(step_number=2, description="Disable unnecessary services", command="Set-Service -Name 'RemoteRegistry' -StartupType Disabled; Stop-Service 'RemoteRegistry'", script_type="powershell", estimated_time="1 hour per system", requires_downtime=True),
            RemediationStep(step_number=3, description="Disable unnecessary Windows features", command="Get-WindowsOptionalFeature -Online | Where-Object State -eq 'Enabled' | Export-Csv 'EnabledFeatures.csv'", script_type="powershell", estimated_time="30 minutes", requires_downtime=False),
        ],
        references=['CIS Benchmarks', 'DISA STIGs'],
        nist_mapping=['CM-7', 'CM-7(1)', 'SC-7'],
        cis_mapping="4.8",
        default_severity=Severity.MEDIUM,
    ),
    "CFG-010": Control(
        id="CFG-010",
        name="Security Configuration Compliance Reporting",
        description="Automated compliance reporting must assess all systems against baselines monthly with executive dashboards.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Configuration Management",
        check_procedure="""
1. Review compliance reporting tool
2. Check last compliance scan date
3. Verify dashboard accuracy
4. Review trend data
        """,
        expected_result=">90% baseline compliance across all systems with monthly trending",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy compliance scanning tool", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure baseline policies", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Schedule monthly compliance scans", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=4, description="Build executive compliance dashboard", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['SCAP Protocol', 'NIST SP 800-53 CA-7'],
        nist_mapping=['CA-7', 'CM-6', 'AU-6'],
        cis_mapping="4.12",
        default_severity=Severity.MEDIUM,
    ),
}

# ============================================================================
# INCIDENT RESPONSE CONTROLS
# ============================================================================

IR_CONTROLS = {
    "IR-001": Control(
        id="IR-001",
        name="Incident Response Plan",
        description="A documented incident response plan must exist, be reviewed annually, and address all NIST incident categories.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Incident Response",
        check_procedure="""
1. Review IR plan document
2. Check last review/update date
3. Verify all NIST categories covered
4. Confirm distribution list
        """,
        expected_result="IR plan reviewed within last 12 months covering all NIST incident types",
        remediation_steps=[
            RemediationStep(step_number=1, description="Draft incident response plan per NIST SP 800-61", command=None, script_type=None, estimated_time="40 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Obtain leadership approval", command=None, script_type=None, estimated_time="1 week", requires_downtime=False),
            RemediationStep(step_number=3, description="Distribute to all IR team members", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['NIST SP 800-61 Rev 2', 'NIST SP 800-53 IR-8'],
        nist_mapping=['IR-1', 'IR-8', 'IR-8(1)'],
        cis_mapping="17.1",
        default_severity=Severity.CRITICAL,
    ),
    "IR-002": Control(
        id="IR-002",
        name="Incident Response Team",
        description="A dedicated incident response team must be established with defined roles, responsibilities, and 24/7 contact information.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Incident Response",
        check_procedure="""
1. Verify IR team roster
2. Check role assignments
3. Test contact information
4. Review on-call schedule
        """,
        expected_result="IR team established with current contacts and 24/7 coverage",
        remediation_steps=[
            RemediationStep(step_number=1, description="Define IR team roles and responsibilities", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Establish on-call rotation", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Create IR communication tree", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['NIST SP 800-61', 'NIST SP 800-53 IR-7'],
        nist_mapping=['IR-2', 'IR-7', 'IR-10'],
        cis_mapping="17.1",
        default_severity=Severity.HIGH,
    ),
    "IR-003": Control(
        id="IR-003",
        name="Tabletop Exercises",
        description="Tabletop exercises must be conducted at least annually to test incident response procedures.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Incident Response",
        check_procedure="""
1. Review last tabletop exercise date
2. Check exercise scenario scope
3. Review after-action report
4. Verify corrective actions implemented
        """,
        expected_result="Annual tabletop completed with after-action report and corrective actions tracked",
        remediation_steps=[
            RemediationStep(step_number=1, description="Develop exercise scenario", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Schedule and conduct tabletop exercise", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Write after-action report", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=4, description="Track corrective actions to closure", command=None, script_type=None, estimated_time="Ongoing", requires_downtime=False),
        ],
        references=['NIST SP 800-84', 'CISA Tabletop Exercise Packages'],
        nist_mapping=['IR-3', 'IR-3(2)', 'CP-4'],
        cis_mapping="17.8",
        default_severity=Severity.MEDIUM,
    ),
    "IR-004": Control(
        id="IR-004",
        name="Evidence Preservation & Chain of Custody",
        description="Procedures for digital evidence collection, preservation, and chain of custody must be documented and followed.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Incident Response",
        check_procedure="""
1. Review evidence handling procedures
2. Check forensic toolkit availability
3. Verify chain of custody forms
4. Review evidence storage security
        """,
        expected_result="Documented procedures with forensic tools available and secure evidence storage",
        remediation_steps=[
            RemediationStep(step_number=1, description="Document evidence collection procedures", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Procure forensic toolkit", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=3, description="Establish secure evidence storage", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=4, description="Train IR team on evidence handling", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-86', 'NIST SP 800-53 IR-4'],
        nist_mapping=['IR-4', 'AU-9', 'AU-11'],
        cis_mapping="17.9",
        default_severity=Severity.MEDIUM,
    ),
    "IR-005": Control(
        id="IR-005",
        name="Incident Classification & Prioritization",
        description="All incidents must be classified by type and severity with defined escalation thresholds.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Incident Response",
        check_procedure="""
1. Review classification taxonomy
2. Verify escalation matrix
3. Check recent incident classifications
4. Confirm automated classification rules
        """,
        expected_result="All incidents classified within 15 minutes of detection with correct priority",
        remediation_steps=[
            RemediationStep(step_number=1, description="Define incident classification taxonomy", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Create escalation matrix", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure SIEM correlation rules for auto-classification", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-61', 'US-CERT Classification'],
        nist_mapping=['IR-4', 'IR-5', 'IR-6'],
        cis_mapping="17.2",
        default_severity=Severity.HIGH,
    ),
    "IR-006": Control(
        id="IR-006",
        name="External Reporting Requirements",
        description="Incident reporting to external entities (CISA, law enforcement, regulators) must follow defined timelines.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Incident Response",
        check_procedure="""
1. Review external reporting procedures
2. Verify reporting timelines by incident type
3. Check reporting templates
4. Confirm POC for each external entity
        """,
        expected_result="Documented reporting procedures with templates and contacts for all required entities",
        remediation_steps=[
            RemediationStep(step_number=1, description="Document external reporting requirements", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Create reporting templates per entity", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Establish POC list for external entities", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['CISA Incident Reporting', 'FISMA Requirements'],
        nist_mapping=['IR-6', 'IR-6(1)', 'IR-6(3)'],
        cis_mapping="17.3",
        default_severity=Severity.HIGH,
    ),
    "IR-007": Control(
        id="IR-007",
        name="Forensic Readiness",
        description="Systems must be configured for forensic readiness with adequate logging, disk imaging capability, and memory capture tools.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Incident Response",
        check_procedure="""
1. Verify forensic tools deployed
2. Check disk imaging capability
3. Verify memory capture tools available
4. Review forensic workstation configuration
        """,
        expected_result="Forensic toolkit available with trained personnel; imaging and memory tools tested",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy forensic toolkit on dedicated workstation", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Install and test disk imaging tools", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Install memory capture tools", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=4, description="Test full forensic acquisition procedure", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-86', 'SANS DFIR'],
        nist_mapping=['IR-4', 'IR-10', 'AU-3'],
        cis_mapping="17.9",
        default_severity=Severity.MEDIUM,
    ),
    "IR-008": Control(
        id="IR-008",
        name="Automated Incident Response",
        description="SOAR capabilities or automated playbooks must handle common incident types to reduce MTTR.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Incident Response",
        check_procedure="""
1. Review SOAR platform deployment
2. Check automated playbook coverage
3. Verify playbook test results
4. Review MTTR metrics
        """,
        expected_result="Automated playbooks for top 5 incident types; MTTR <4 hours for critical incidents",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy SOAR platform or scripted playbooks", command=None, script_type=None, estimated_time="40 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Create playbooks for common incident types", command=None, script_type=None, estimated_time="20 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Test and validate playbooks", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 IR-4(1)', 'SOAR Best Practices'],
        nist_mapping=['IR-4(1)', 'IR-4(13)', 'SI-4'],
        cis_mapping="17.4",
        default_severity=Severity.MEDIUM,
    ),
    "IR-009": Control(
        id="IR-009",
        name="Lessons Learned Process",
        description="Post-incident reviews must be conducted within 5 business days of incident closure with documented lessons learned.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Incident Response",
        check_procedure="""
1. Review post-incident reports
2. Check timeliness of reviews
3. Verify corrective actions tracked
4. Confirm process improvements implemented
        """,
        expected_result="All significant incidents reviewed within 5 days; lessons learned documented",
        remediation_steps=[
            RemediationStep(step_number=1, description="Schedule post-incident review meeting", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
            RemediationStep(step_number=2, description="Conduct structured after-action review", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Document lessons learned and corrective actions", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-61 Rev 2'],
        nist_mapping=['IR-4(8)', 'IR-4', 'IR-6'],
        cis_mapping="17.7",
        default_severity=Severity.MEDIUM,
    ),
    "IR-010": Control(
        id="IR-010",
        name="Incident Communication Plan",
        description="A communication plan must define internal and external notification procedures during security incidents.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Incident Response",
        check_procedure="""
1. Review communication plan
2. Verify stakeholder contact list
3. Check communication templates
4. Test out-of-band communication methods
        """,
        expected_result="Communication plan tested; out-of-band methods verified working",
        remediation_steps=[
            RemediationStep(step_number=1, description="Document incident communication plan", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Create notification templates by severity", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Establish out-of-band communication channels", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=4, description="Test communication plan during tabletop", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['NIST SP 800-61', 'NIST SP 800-53 IR-7'],
        nist_mapping=['IR-6', 'IR-7', 'IR-1'],
        cis_mapping="17.3",
        default_severity=Severity.HIGH,
    ),
}

# ============================================================================
# CONTINGENCY PLANNING CONTROLS
# ============================================================================

CP_CONTROLS = {
    "CP-001": Control(
        id="CP-001",
        name="Business Continuity Plan",
        description="A comprehensive BCP must exist addressing all critical business functions with documented recovery procedures.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Contingency Planning",
        check_procedure="""
1. Review BCP document
2. Verify BIA (Business Impact Analysis) current
3. Check recovery procedure accuracy
4. Confirm stakeholder awareness
        """,
        expected_result="BCP reviewed annually with current BIA; all critical functions addressed",
        remediation_steps=[
            RemediationStep(step_number=1, description="Conduct Business Impact Analysis", command=None, script_type=None, estimated_time="40 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Draft BCP based on BIA results", command=None, script_type=None, estimated_time="40 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Obtain leadership approval", command=None, script_type=None, estimated_time="1 week", requires_downtime=False),
            RemediationStep(step_number=4, description="Distribute BCP to all stakeholders", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-34', 'NIST SP 800-53 CP-2'],
        nist_mapping=['CP-1', 'CP-2', 'CP-2(1)'],
        cis_mapping="11.1",
        default_severity=Severity.CRITICAL,
    ),
    "CP-002": Control(
        id="CP-002",
        name="Disaster Recovery Plan",
        description="A DRP must document technical recovery procedures with RTO and RPO targets for all critical systems.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Contingency Planning",
        check_procedure="""
1. Review DRP document
2. Verify RTO/RPO targets defined
3. Check recovery procedure testing
4. Confirm alternate site readiness
        """,
        expected_result="DRP with defined RTO/RPO tested within last 12 months",
        remediation_steps=[
            RemediationStep(step_number=1, description="Define RTO/RPO targets per system", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Document recovery procedures", command=None, script_type=None, estimated_time="24 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Establish alternate processing site", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
        ],
        references=['NIST SP 800-34', 'NIST SP 800-53 CP-7'],
        nist_mapping=['CP-2', 'CP-7', 'CP-10'],
        cis_mapping="11.2",
        default_severity=Severity.CRITICAL,
    ),
    "CP-003": Control(
        id="CP-003",
        name="DR Testing & Exercises",
        description="Disaster recovery plans must be tested at least annually with documented results and corrective actions.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Contingency Planning",
        check_procedure="""
1. Review last DR test date and results
2. Verify all critical systems tested
3. Check corrective actions from prior tests
4. Confirm RTO/RPO targets met during test
        """,
        expected_result="Annual DR test completed; RTO/RPO targets met; corrective actions tracked",
        remediation_steps=[
            RemediationStep(step_number=1, description="Plan DR exercise scope and scenarios", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Conduct DR test", command=None, script_type=None, estimated_time="8-24 hours", requires_downtime=True),
            RemediationStep(step_number=3, description="Document results and gaps", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=4, description="Track corrective actions", command=None, script_type=None, estimated_time="Ongoing", requires_downtime=False),
        ],
        references=['NIST SP 800-84', 'NIST SP 800-53 CP-4'],
        nist_mapping=['CP-4', 'CP-4(1)', 'CP-3'],
        cis_mapping="11.3",
        default_severity=Severity.HIGH,
    ),
    "CP-004": Control(
        id="CP-004",
        name="Backup Verification & Testing",
        description="Backup integrity must be verified weekly and full restoration tested quarterly.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Contingency Planning",
        check_procedure="""
1. Review backup job logs
2. Verify backup integrity checks
3. Check last restoration test
4. Confirm backup coverage
        """,
        expected_result="Weekly integrity checks passing; quarterly restore tests successful",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure automated backup verification", command="Test-DbaLastBackup -SqlInstance 'SQLSERVER01' | Export-Csv 'BackupTest.csv'", script_type="powershell", estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Schedule quarterly restoration tests", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Document restoration procedures", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 CP-9', 'CIS Controls v8 11.4'],
        nist_mapping=['CP-9', 'CP-9(1)', 'CP-10'],
        cis_mapping="11.4",
        default_severity=Severity.HIGH,
    ),
    "CP-005": Control(
        id="CP-005",
        name="Alternate Processing Site",
        description="An alternate processing site must be established that can resume critical operations within RTO targets.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Contingency Planning",
        check_procedure="""
1. Verify alternate site exists
2. Check connectivity and capacity
3. Review failover procedures
4. Test site activation
        """,
        expected_result="Alternate site operational with tested failover procedures meeting RTO",
        remediation_steps=[
            RemediationStep(step_number=1, description="Identify alternate processing site", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=2, description="Establish network connectivity", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=3, description="Document and test failover procedures", command=None, script_type=None, estimated_time="24 hours", requires_downtime=True),
        ],
        references=['NIST SP 800-34', 'NIST SP 800-53 CP-7'],
        nist_mapping=['CP-7', 'CP-7(1)', 'CP-7(3)'],
        cis_mapping="11.5",
        default_severity=Severity.HIGH,
    ),
    "CP-006": Control(
        id="CP-006",
        name="System Recovery Prioritization",
        description="Systems must be prioritized for recovery based on BIA criticality ratings.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Contingency Planning",
        check_procedure="""
1. Review system criticality ratings
2. Verify recovery priority order
3. Check dependencies documented
4. Confirm priority aligns with BIA
        """,
        expected_result="All systems prioritized with documented dependencies and recovery order",
        remediation_steps=[
            RemediationStep(step_number=1, description="Assign criticality ratings based on BIA", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Map system dependencies", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Document recovery priority order", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-34', 'NIST SP 800-53 CP-2'],
        nist_mapping=['CP-2(8)', 'CP-10', 'PM-11'],
        cis_mapping="11.2",
        default_severity=Severity.MEDIUM,
    ),
    "CP-007": Control(
        id="CP-007",
        name="Data Backup Offsite Storage",
        description="Backup media or replication must be stored offsite with geographic separation from primary site.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Contingency Planning",
        check_procedure="""
1. Verify offsite backup location
2. Check geographic separation distance
3. Review transfer security
4. Confirm access controls on offsite storage
        """,
        expected_result="Offsite backups with >50 mile geographic separation; encrypted in transit and at rest",
        remediation_steps=[
            RemediationStep(step_number=1, description="Establish offsite storage location", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure encrypted replication", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Test offsite backup retrieval", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 CP-6'],
        nist_mapping=['CP-6', 'CP-6(1)', 'CP-9(3)'],
        cis_mapping="11.4",
        default_severity=Severity.HIGH,
    ),
    "CP-008": Control(
        id="CP-008",
        name="Telecommunications Redundancy",
        description="Critical telecommunications paths must have redundant connections from different providers.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Contingency Planning",
        check_procedure="""
1. Review network topology for redundancy
2. Verify diverse carrier paths
3. Check failover testing
4. Confirm SLAs with providers
        """,
        expected_result="Dual ISP connections with automatic failover tested quarterly",
        remediation_steps=[
            RemediationStep(step_number=1, description="Procure secondary ISP connection", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure automatic failover", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Test failover quarterly", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 CP-8'],
        nist_mapping=['CP-8', 'CP-8(1)', 'CP-8(2)'],
        cis_mapping="11.6",
        default_severity=Severity.MEDIUM,
    ),
    "CP-009": Control(
        id="CP-009",
        name="Essential Personnel Identification",
        description="Personnel essential for contingency operations must be identified with alternate contacts.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Contingency Planning",
        check_procedure="""
1. Review essential personnel list
2. Verify contact information current
3. Check cross-training documentation
4. Confirm notification procedures
        """,
        expected_result="Essential personnel identified with current contacts and cross-trained backups",
        remediation_steps=[
            RemediationStep(step_number=1, description="Identify essential personnel by function", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Document primary and alternate contacts", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Establish cross-training program", command=None, script_type=None, estimated_time="Ongoing", requires_downtime=False),
        ],
        references=['NIST SP 800-34', 'COOP Planning'],
        nist_mapping=['CP-2', 'PS-4', 'IR-7'],
        cis_mapping="11.1",
        default_severity=Severity.MEDIUM,
    ),
    "CP-010": Control(
        id="CP-010",
        name="Contingency Plan Training",
        description="All personnel with contingency roles must receive training annually on their responsibilities.",
        family=ControlFamily.CONTINGENCY_PLANNING,
        category="Contingency Planning",
        check_procedure="""
1. Review training records
2. Verify all CP-role personnel trained
3. Check training content currency
4. Confirm training includes exercises
        """,
        expected_result="100% of CP-role personnel trained within last 12 months",
        remediation_steps=[
            RemediationStep(step_number=1, description="Develop contingency plan training materials", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Schedule annual training sessions", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Conduct training with practical exercises", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=4, description="Document completion records", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['NIST SP 800-53 CP-3'],
        nist_mapping=['CP-3', 'CP-3(1)', 'AT-3'],
        cis_mapping="11.7",
        default_severity=Severity.MEDIUM,
    ),
}

# ============================================================================
# SECURITY AWARENESS & TRAINING CONTROLS
# ============================================================================

SAT_CONTROLS = {
    "SAT-001": Control(
        id="SAT-001",
        name="Security Awareness Program",
        description="All personnel must complete security awareness training within 30 days of onboarding and annually thereafter.",
        family=ControlFamily.PERSONNEL_SECURITY,
        category="Security Awareness & Training",
        check_procedure="""
1. Review training program content
2. Check completion rates
3. Verify new hire compliance
4. Review training platform
        """,
        expected_result=">95% completion rate; all new hires trained within 30 days",
        remediation_steps=[
            RemediationStep(step_number=1, description="Implement security awareness training platform", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Develop role-appropriate training content", command=None, script_type=None, estimated_time="24 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure automated enrollment and reminders", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-50', 'NIST SP 800-53 AT-2'],
        nist_mapping=['AT-2', 'AT-2(2)', 'AT-1'],
        cis_mapping="14.1",
        default_severity=Severity.HIGH,
    ),
    "SAT-002": Control(
        id="SAT-002",
        name="Phishing Simulation Program",
        description="Monthly phishing simulations must be conducted with targeted training for users who fail.",
        family=ControlFamily.PERSONNEL_SECURITY,
        category="Security Awareness & Training",
        check_procedure="""
1. Review phishing simulation reports
2. Check click rates over time
3. Verify remedial training delivery
4. Review campaign diversity
        """,
        expected_result="Monthly simulations with <5% organization-wide click rate",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy phishing simulation platform", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Create diverse phishing templates", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure automated remedial training", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 AT-2', 'CISA Phishing Resources'],
        nist_mapping=['AT-2(1)', 'AT-2(3)', 'IR-2'],
        cis_mapping="14.2",
        default_severity=Severity.HIGH,
    ),
    "SAT-003": Control(
        id="SAT-003",
        name="Role-Based Security Training",
        description="Privileged users, developers, and administrators must receive specialized security training beyond general awareness.",
        family=ControlFamily.PERSONNEL_SECURITY,
        category="Security Awareness & Training",
        check_procedure="""
1. Review role-based training matrix
2. Check privileged user training completion
3. Verify developer secure coding training
4. Confirm admin hardening training
        """,
        expected_result="100% of privileged users/developers completed role-specific training",
        remediation_steps=[
            RemediationStep(step_number=1, description="Define role-based training requirements", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Procure specialized training (SANS, etc.)", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=3, description="Track completion by role", command=None, script_type=None, estimated_time="Ongoing", requires_downtime=False),
        ],
        references=['NIST SP 800-53 AT-3', 'NICE Framework'],
        nist_mapping=['AT-3', 'AT-3(5)', 'AT-4'],
        cis_mapping="14.9",
        default_severity=Severity.MEDIUM,
    ),
    "SAT-004": Control(
        id="SAT-004",
        name="Social Engineering Awareness",
        description="Training must cover social engineering tactics including vishing, pretexting, tailgating, and USB drops.",
        family=ControlFamily.PERSONNEL_SECURITY,
        category="Security Awareness & Training",
        check_procedure="""
1. Review social engineering training content
2. Check for practical demonstrations
3. Verify physical social engineering testing
4. Review reporting rates
        """,
        expected_result="Training covers all social engineering vectors; reporting rate >60%",
        remediation_steps=[
            RemediationStep(step_number=1, description="Update training with social engineering modules", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Conduct physical social engineering test", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Brief results to management", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['NIST SP 800-53 AT-2', 'SE Toolkit'],
        nist_mapping=['AT-2', 'PE-3', 'IR-6'],
        cis_mapping="14.4",
        default_severity=Severity.MEDIUM,
    ),
    "SAT-005": Control(
        id="SAT-005",
        name="Personnel Screening",
        description="All personnel with access to information systems must undergo background screening prior to access.",
        family=ControlFamily.PERSONNEL_SECURITY,
        category="Security Awareness & Training",
        check_procedure="""
1. Review screening policy
2. Verify screening completion for all users
3. Check rescreening schedule
4. Confirm contractor screening
        """,
        expected_result="100% of personnel screened before system access; rescreening per policy",
        remediation_steps=[
            RemediationStep(step_number=1, description="Establish screening requirements by position sensitivity", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Contract with background check provider", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=3, description="Implement pre-access screening verification", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 PS-3', '5 CFR 731'],
        nist_mapping=['PS-3', 'PS-3(1)', 'PS-1'],
        cis_mapping="14.5",
        default_severity=Severity.HIGH,
    ),
    "SAT-006": Control(
        id="SAT-006",
        name="Personnel Termination Procedures",
        description="Access must be revoked within 4 hours of termination with all credentials disabled and equipment collected.",
        family=ControlFamily.PERSONNEL_SECURITY,
        category="Security Awareness & Training",
        check_procedure="""
1. Review termination procedure
2. Verify access revocation timeliness
3. Check equipment return process
4. Review exit interview process
        """,
        expected_result="Access disabled within 4 hours; all equipment returned and accounted for",
        remediation_steps=[
            RemediationStep(step_number=1, description="Document termination checklist", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Automate AD account disable on HR notification", command="Disable-ADAccount -Identity $TermUser; Set-ADUser $TermUser -Description 'Terminated $(Get-Date -Format yyyy-MM-dd)'", script_type="powershell", estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure equipment return tracking", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 PS-4'],
        nist_mapping=['PS-4', 'PS-4(2)', 'AC-2'],
        cis_mapping="14.6",
        default_severity=Severity.CRITICAL,
    ),
    "SAT-007": Control(
        id="SAT-007",
        name="Access Agreements",
        description="All users must sign acceptable use policies and security agreements before system access.",
        family=ControlFamily.PERSONNEL_SECURITY,
        category="Security Awareness & Training",
        check_procedure="""
1. Review AUP/security agreement
2. Verify all users have signed
3. Check agreement update schedule
4. Confirm contractor agreements
        """,
        expected_result="100% of users with current signed agreements; reviewed annually",
        remediation_steps=[
            RemediationStep(step_number=1, description="Draft acceptable use and security agreement", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Obtain legal review", command=None, script_type=None, estimated_time="1 week", requires_downtime=False),
            RemediationStep(step_number=3, description="Implement digital signature workflow", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 PL-4', 'PS-6'],
        nist_mapping=['PS-6', 'PL-4', 'AC-8'],
        cis_mapping="14.3",
        default_severity=Severity.MEDIUM,
    ),
    "SAT-008": Control(
        id="SAT-008",
        name="Insider Threat Awareness",
        description="Training must address insider threat indicators, reporting procedures, and organizational policies.",
        family=ControlFamily.PERSONNEL_SECURITY,
        category="Security Awareness & Training",
        check_procedure="""
1. Review insider threat training content
2. Verify completion rates
3. Check reporting mechanism awareness
4. Review insider threat program maturity
        """,
        expected_result="All personnel trained on insider threat indicators; anonymous reporting available",
        remediation_steps=[
            RemediationStep(step_number=1, description="Develop insider threat awareness training", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Establish anonymous reporting mechanism", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Conduct annual insider threat briefing", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 PM-12', 'CISA Insider Threat'],
        nist_mapping=['AT-2(2)', 'PM-12', 'IR-4'],
        cis_mapping="14.7",
        default_severity=Severity.MEDIUM,
    ),
    "SAT-009": Control(
        id="SAT-009",
        name="Security Training Effectiveness Measurement",
        description="Training effectiveness must be measured through testing, simulations, and behavioral metrics.",
        family=ControlFamily.PERSONNEL_SECURITY,
        category="Security Awareness & Training",
        check_procedure="""
1. Review testing methodology
2. Check pass rates and trends
3. Verify behavioral metrics tracked
4. Review training improvement actions
        """,
        expected_result=">85% pass rate on security assessments; positive behavioral trends",
        remediation_steps=[
            RemediationStep(step_number=1, description="Implement post-training knowledge assessments", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Track behavioral metrics (phishing click rates, reporting rates)", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Generate quarterly effectiveness reports", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-50', 'NIST SP 800-53 AT-4'],
        nist_mapping=['AT-4', 'AT-2(5)', 'PM-14'],
        cis_mapping="14.8",
        default_severity=Severity.LOW,
    ),
    "SAT-010": Control(
        id="SAT-010",
        name="Third-Party Personnel Security",
        description="Contractors and third-party personnel must meet same security training and screening requirements as employees.",
        family=ControlFamily.PERSONNEL_SECURITY,
        category="Security Awareness & Training",
        check_procedure="""
1. Review contractor security requirements
2. Verify contractor training completion
3. Check contractor screening records
4. Confirm NDA/security agreement signed
        """,
        expected_result="All contractors screened, trained, and under signed security agreements",
        remediation_steps=[
            RemediationStep(step_number=1, description="Include security requirements in contracts", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Extend training platform to contractors", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Verify contractor screening compliance", command=None, script_type=None, estimated_time="Ongoing", requires_downtime=False),
        ],
        references=['NIST SP 800-53 PS-7', 'FAR 52.204-21'],
        nist_mapping=['PS-7', 'SA-9', 'AT-2'],
        cis_mapping="14.10",
        default_severity=Severity.HIGH,
    ),
}

# ============================================================================
# APPLICATION SECURITY CONTROLS
# ============================================================================

APP_CONTROLS = {
    "APP-001": Control(
        id="APP-001",
        name="Secure Software Development Lifecycle",
        description="All internally developed applications must follow a documented SSDLC with security gates at each phase.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Application Security",
        check_procedure="""
1. Review SSDLC documentation
2. Verify security gates defined
3. Check recent project adherence
4. Review security testing integration
        """,
        expected_result="Documented SSDLC with enforced security gates at design, code, test, and deploy",
        remediation_steps=[
            RemediationStep(step_number=1, description="Document SSDLC framework", command=None, script_type=None, estimated_time="24 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Define security gates and criteria", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Integrate security testing into CI/CD", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-218 SSDF', 'OWASP SAMM'],
        nist_mapping=['SA-3', 'SA-8', 'SA-15'],
        cis_mapping="16.1",
        default_severity=Severity.HIGH,
    ),
    "APP-002": Control(
        id="APP-002",
        name="Static Application Security Testing",
        description="SAST must be integrated into CI/CD pipelines for all internally developed code.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Application Security",
        check_procedure="""
1. Verify SAST tool deployment
2. Check CI/CD integration
3. Review false positive management
4. Confirm build-breaking threshold
        """,
        expected_result="SAST runs on every commit; no Critical findings in production releases",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy SAST tool in CI/CD pipeline", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure rulesets for applicable languages", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Set build-breaking severity threshold", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['OWASP SAST Guide', 'NIST SP 800-53 SA-11'],
        nist_mapping=['SA-11', 'SA-11(1)', 'SI-10'],
        cis_mapping="16.2",
        default_severity=Severity.HIGH,
    ),
    "APP-003": Control(
        id="APP-003",
        name="Dynamic Application Security Testing",
        description="DAST must scan all web applications in staging before production deployment.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Application Security",
        check_procedure="""
1. Verify DAST tool deployment
2. Check pre-deployment scan requirement
3. Review scan scope coverage
4. Confirm vulnerability tracking
        """,
        expected_result="All web applications DAST-scanned before production; no Critical/High findings",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy DAST scanner", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure scan profiles per application", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Integrate with deployment pipeline", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['OWASP Testing Guide', 'NIST SP 800-53 SA-11'],
        nist_mapping=['SA-11(8)', 'RA-5', 'SI-10'],
        cis_mapping="16.12",
        default_severity=Severity.HIGH,
    ),
    "APP-004": Control(
        id="APP-004",
        name="Software Composition Analysis",
        description="All third-party libraries and dependencies must be scanned for known vulnerabilities.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Application Security",
        check_procedure="""
1. Verify SCA tool deployment
2. Check SBOM generation
3. Review vulnerable dependency tracking
4. Confirm license compliance
        """,
        expected_result="All dependencies scanned; no Critical/High CVEs in production dependencies",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy SCA tool (Snyk/Dependabot/etc.)", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Generate SBOM for all applications", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure automated vulnerability alerts", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NTIA SBOM', 'NIST SP 800-53 SA-12'],
        nist_mapping=['SA-12', 'SR-4', 'SI-2'],
        cis_mapping="16.4",
        default_severity=Severity.HIGH,
    ),
    "APP-005": Control(
        id="APP-005",
        name="Web Application Firewall",
        description="All internet-facing web applications must be protected by a WAF with OWASP Core Rule Set.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Application Security",
        check_procedure="""
1. Verify WAF deployment
2. Check rule set configuration
3. Review WAF logs for blocks
4. Confirm all web apps behind WAF
        """,
        expected_result="WAF active for all internet-facing apps with OWASP CRS; false positive rate <1%",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy WAF (ModSecurity/AWS WAF/etc.)", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Enable OWASP Core Rule Set", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Tune rules to minimize false positives", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
        ],
        references=['OWASP ModSecurity CRS', 'NIST SP 800-53 SC-7'],
        nist_mapping=['SC-7', 'SI-10', 'SC-5'],
        cis_mapping="13.10",
        default_severity=Severity.HIGH,
    ),
    "APP-006": Control(
        id="APP-006",
        name="API Security",
        description="All APIs must implement authentication, rate limiting, input validation, and logging.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Application Security",
        check_procedure="""
1. Review API inventory
2. Verify authentication on all endpoints
3. Check rate limiting configuration
4. Confirm input validation and logging
        """,
        expected_result="All APIs authenticated with rate limiting; no unauthenticated endpoints",
        remediation_steps=[
            RemediationStep(step_number=1, description="Inventory all APIs", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Implement API gateway with authentication", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure rate limiting and throttling", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['OWASP API Security Top 10', 'NIST SP 800-53 SC-7'],
        nist_mapping=['SC-7', 'IA-2', 'SI-10'],
        cis_mapping="16.8",
        default_severity=Severity.HIGH,
    ),
    "APP-007": Control(
        id="APP-007",
        name="Secure Code Review",
        description="All security-critical code changes must undergo peer review with a security-trained reviewer.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Application Security",
        check_procedure="""
1. Review code review policy
2. Check PR review requirements
3. Verify security reviewer assignments
4. Audit recent PRs for compliance
        """,
        expected_result="All security-critical PRs reviewed by security-trained developer; no bypasses",
        remediation_steps=[
            RemediationStep(step_number=1, description="Define security-critical code review requirements", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Train security reviewers", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure mandatory review in SCM", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['OWASP Code Review Guide', 'NIST SP 800-53 SA-11'],
        nist_mapping=['SA-11(4)', 'SA-15(7)', 'CM-3'],
        cis_mapping="16.11",
        default_severity=Severity.MEDIUM,
    ),
    "APP-008": Control(
        id="APP-008",
        name="Input Validation",
        description="All applications must implement server-side input validation and output encoding to prevent injection attacks.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Application Security",
        check_procedure="""
1. Review coding standards for input validation
2. Test for SQL injection
3. Test for XSS
4. Check for command injection
        """,
        expected_result="No injection vulnerabilities found in DAST/SAST scanning",
        remediation_steps=[
            RemediationStep(step_number=1, description="Implement input validation framework", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=2, description="Deploy output encoding libraries", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=3, description="Run SAST scan for injection patterns", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['OWASP Input Validation Cheat Sheet', 'CWE-20'],
        nist_mapping=['SI-10', 'SI-10(1)', 'SC-18'],
        cis_mapping="16.3",
        default_severity=Severity.CRITICAL,
    ),
    "APP-009": Control(
        id="APP-009",
        name="Secrets Management",
        description="Application secrets (API keys, passwords, certificates) must never be hardcoded; use a secrets vault.",
        family=ControlFamily.IDENTIFICATION_AUTH,
        category="Application Security",
        check_procedure="""
1. Scan repos for hardcoded secrets
2. Verify secrets vault deployment
3. Check secret rotation policy
4. Review access to secrets vault
        """,
        expected_result="No hardcoded secrets; all secrets in vault with automated rotation",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy secrets vault (HashiCorp Vault/etc.)", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Migrate hardcoded secrets to vault", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure automated secret rotation", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=4, description="Deploy pre-commit hook for secret detection", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['OWASP Secrets Management', 'NIST SP 800-53 IA-5'],
        nist_mapping=['IA-5', 'SC-12', 'SC-28'],
        cis_mapping="16.9",
        default_severity=Severity.CRITICAL,
    ),
    "APP-010": Control(
        id="APP-010",
        name="Security Headers & TLS Configuration",
        description="All web applications must implement security headers (CSP, HSTS, X-Frame-Options) and TLS 1.2+.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Application Security",
        check_procedure="""
1. Scan for security headers
2. Test TLS configuration
3. Check certificate validity
4. Verify HSTS preload status
        """,
        expected_result="All security headers present; TLS 1.2+ only; certificates valid",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure security headers in web server", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Disable TLS 1.0/1.1", command=None, script_type=None, estimated_time="1 hour", requires_downtime=True),
            RemediationStep(step_number=3, description="Enable HSTS with preload", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
        ],
        references=['OWASP Secure Headers', 'Mozilla SSL Configuration'],
        nist_mapping=['SC-8', 'SC-17', 'SC-23'],
        cis_mapping="16.5",
        default_severity=Severity.MEDIUM,
    ),
}

# ============================================================================
# SUPPLY CHAIN RISK MANAGEMENT CONTROLS
# ============================================================================

SCR_CONTROLS = {
    "SCR-001": Control(
        id="SCR-001",
        name="Vendor Risk Assessment Program",
        description="All vendors with access to systems or data must undergo risk assessments before engagement and annually.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Supply Chain Risk Management",
        check_procedure="""
1. Review vendor risk assessment program
2. Check assessment completion rates
3. Verify risk ratings documented
4. Confirm remediation tracking
        """,
        expected_result="100% of critical vendors assessed; risk ratings current within 12 months",
        remediation_steps=[
            RemediationStep(step_number=1, description="Develop vendor risk assessment questionnaire", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Assess all critical vendors", command=None, script_type=None, estimated_time="4 hours per vendor", requires_downtime=False),
            RemediationStep(step_number=3, description="Track remediation of identified risks", command=None, script_type=None, estimated_time="Ongoing", requires_downtime=False),
        ],
        references=['NIST SP 800-161', 'NIST SP 800-53 SA-9'],
        nist_mapping=['SA-9', 'SA-9(2)', 'SR-1'],
        cis_mapping="15.1",
        default_severity=Severity.HIGH,
    ),
    "SCR-002": Control(
        id="SCR-002",
        name="Software Bill of Materials",
        description="SBOM must be maintained for all software products used in the environment.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Supply Chain Risk Management",
        check_procedure="""
1. Verify SBOM generation process
2. Check SBOM completeness
3. Review vulnerability tracking from SBOMs
4. Confirm SBOM update frequency
        """,
        expected_result="SBOMs generated for all critical software; updated with each version",
        remediation_steps=[
            RemediationStep(step_number=1, description="Implement SBOM generation tooling", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Generate SBOMs for all critical applications", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure automated SBOM vulnerability monitoring", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NTIA SBOM', 'EO 14028', 'NIST SP 800-161'],
        nist_mapping=['SR-4', 'SA-12', 'CM-8'],
        cis_mapping="16.4",
        default_severity=Severity.MEDIUM,
    ),
    "SCR-003": Control(
        id="SCR-003",
        name="Third-Party Software Patching",
        description="Third-party software must be included in patch management with the same SLAs as OS patches.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Supply Chain Risk Management",
        check_procedure="""
1. Inventory third-party software
2. Verify patch tracking
3. Check patch compliance rates
4. Review end-of-life software
        """,
        expected_result="Third-party software patched within SLA; no EOL software in production",
        remediation_steps=[
            RemediationStep(step_number=1, description="Integrate third-party patching into WSUS/SCCM/Intune", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure third-party patch catalog", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Remove or isolate EOL software", command=None, script_type=None, estimated_time="Variable", requires_downtime=True),
        ],
        references=['CIS Controls v8 7.3', 'NIST SP 800-53 SI-2'],
        nist_mapping=['SI-2', 'SA-12', 'CM-3'],
        cis_mapping="7.3",
        default_severity=Severity.HIGH,
    ),
    "SCR-004": Control(
        id="SCR-004",
        name="Supplier Security Requirements",
        description="Security requirements must be included in all contracts with IT suppliers and service providers.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Supply Chain Risk Management",
        check_procedure="""
1. Review contract templates
2. Verify security clauses present
3. Check incident notification requirements
4. Confirm right-to-audit clauses
        """,
        expected_result="All IT contracts include security requirements, incident notification, and audit rights",
        remediation_steps=[
            RemediationStep(step_number=1, description="Draft security contract language", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Obtain legal approval", command=None, script_type=None, estimated_time="1 week", requires_downtime=False),
            RemediationStep(step_number=3, description="Update contract templates", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 SA-4', 'NIST SP 800-161'],
        nist_mapping=['SA-4', 'SA-4(2)', 'SA-9'],
        cis_mapping="15.2",
        default_severity=Severity.MEDIUM,
    ),
    "SCR-005": Control(
        id="SCR-005",
        name="Component Authenticity Verification",
        description="Hardware and software components must be verified as authentic before deployment.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Supply Chain Risk Management",
        check_procedure="""
1. Review procurement verification process
2. Check firmware hash verification
3. Verify software signature validation
4. Confirm counterfeit detection
        """,
        expected_result="All components verified through checksums, signatures, or chain of custody",
        remediation_steps=[
            RemediationStep(step_number=1, description="Establish procurement verification checklist", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure software signature verification", command="Set-ExecutionPolicy AllSigned; Get-AuthenticodeSignature -FilePath 'C:\\Software\\*.exe'", script_type="powershell", estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Implement hardware chain of custody", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-161', 'NIST SP 800-53 SR-11'],
        nist_mapping=['SR-4(3)', 'SR-11', 'SI-7'],
        cis_mapping="15.4",
        default_severity=Severity.MEDIUM,
    ),
    "SCR-006": Control(
        id="SCR-006",
        name="Supply Chain Incident Notification",
        description="Suppliers must notify organization of security incidents affecting shared systems within 24 hours.",
        family=ControlFamily.INCIDENT_RESPONSE,
        category="Supply Chain Risk Management",
        check_procedure="""
1. Verify notification clauses in contracts
2. Check notification POC current
3. Review supplier incident history
4. Test notification process
        """,
        expected_result="Contractual 24-hour notification requirement with tested communication path",
        remediation_steps=[
            RemediationStep(step_number=1, description="Include incident notification in contracts", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Establish supplier incident POC directory", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Test notification with key suppliers", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-161', 'CISA Supply Chain Guidance'],
        nist_mapping=['IR-6(3)', 'SA-9(2)', 'SR-8'],
        cis_mapping="15.5",
        default_severity=Severity.HIGH,
    ),
    "SCR-007": Control(
        id="SCR-007",
        name="Vendor Access Controls",
        description="Third-party vendor access must use dedicated accounts with MFA, time-limited access, and full session logging.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Supply Chain Risk Management",
        check_procedure="""
1. Review vendor access accounts
2. Verify MFA enforcement
3. Check access time restrictions
4. Confirm session logging
        """,
        expected_result="All vendor access via dedicated MFA accounts with session recording",
        remediation_steps=[
            RemediationStep(step_number=1, description="Create dedicated vendor accounts", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Enforce MFA for vendor accounts", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure time-limited access windows", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=4, description="Enable full session recording", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 AC-2', 'PAM Best Practices'],
        nist_mapping=['AC-2(12)', 'IA-2', 'AU-2'],
        cis_mapping="15.3",
        default_severity=Severity.HIGH,
    ),
    "SCR-008": Control(
        id="SCR-008",
        name="Cloud Service Provider Assessment",
        description="Cloud service providers must maintain FedRAMP or equivalent certification for systems processing org data.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Supply Chain Risk Management",
        check_procedure="""
1. Inventory cloud services in use
2. Verify FedRAMP/SOC2/ISO status
3. Review shared responsibility model
4. Check data residency requirements
        """,
        expected_result="All CSPs have current FedRAMP/SOC2 certification at appropriate impact level",
        remediation_steps=[
            RemediationStep(step_number=1, description="Inventory all cloud services", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Verify FedRAMP authorization status", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Document shared responsibility models", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
        ],
        references=['FedRAMP Marketplace', 'NIST SP 800-53 SA-9'],
        nist_mapping=['SA-9', 'SA-9(5)', 'CA-3'],
        cis_mapping="15.6",
        default_severity=Severity.HIGH,
    ),
    "SCR-009": Control(
        id="SCR-009",
        name="End-of-Life Technology Management",
        description="All EOL hardware and software must be identified, risk-accepted, or replaced before support expiration.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Supply Chain Risk Management",
        check_procedure="""
1. Run EOL inventory scan
2. Check replacement timelines
3. Review risk acceptances for remaining EOL
4. Verify compensating controls
        """,
        expected_result="No unsupported technology without documented risk acceptance and compensating controls",
        remediation_steps=[
            RemediationStep(step_number=1, description="Scan environment for EOL software/hardware", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Create replacement roadmap", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Document risk acceptances with compensating controls", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 SA-22', 'Microsoft Lifecycle Policy'],
        nist_mapping=['SA-22', 'SI-2', 'PM-9'],
        cis_mapping="2.2",
        default_severity=Severity.HIGH,
    ),
    "SCR-010": Control(
        id="SCR-010",
        name="Open Source Software Governance",
        description="Use of open source software must follow a governance process including license compliance and vulnerability tracking.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Supply Chain Risk Management",
        check_procedure="""
1. Review OSS governance policy
2. Check OSS inventory
3. Verify license compliance
4. Confirm vulnerability monitoring
        """,
        expected_result="All OSS tracked with license compliance; no GPL violations in proprietary code",
        remediation_steps=[
            RemediationStep(step_number=1, description="Establish OSS governance policy", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Deploy OSS scanning tool", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Create approved OSS registry", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
        ],
        references=['OpenSSF Scorecard', 'NIST SP 800-53 SA-10'],
        nist_mapping=['SR-4', 'SA-10', 'CM-10'],
        cis_mapping="16.6",
        default_severity=Severity.MEDIUM,
    ),
}

# ============================================================================
# GOVERNANCE & COMPLIANCE CONTROLS
# ============================================================================

GOV_CONTROLS = {
    "GOV-001": Control(
        id="GOV-001",
        name="Information Security Policy",
        description="A comprehensive information security policy must exist, be approved by leadership, and reviewed annually.",
        family=ControlFamily.PLANNING,
        category="Governance & Compliance",
        check_procedure="""
1. Review security policy document
2. Verify leadership approval
3. Check last review date
4. Confirm distribution to all employees
        """,
        expected_result="Policy approved by CISO/CIO within last 12 months; distributed to all staff",
        remediation_steps=[
            RemediationStep(step_number=1, description="Draft comprehensive security policy", command=None, script_type=None, estimated_time="40 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Obtain leadership review and approval", command=None, script_type=None, estimated_time="2 weeks", requires_downtime=False),
            RemediationStep(step_number=3, description="Distribute to all employees with acknowledgment", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 PL-1', 'ISO 27001 A.5'],
        nist_mapping=['PL-1', 'PM-1', 'PL-2'],
        cis_mapping="15.1",
        default_severity=Severity.HIGH,
    ),
    "GOV-002": Control(
        id="GOV-002",
        name="Risk Management Framework",
        description="Organization must implement a structured risk management framework (RMF) with documented risk tolerance.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Governance & Compliance",
        check_procedure="""
1. Review RMF documentation
2. Verify risk tolerance defined
3. Check risk register currency
4. Review risk treatment plans
        """,
        expected_result="RMF implemented with current risk register and defined risk tolerance",
        remediation_steps=[
            RemediationStep(step_number=1, description="Select and document RMF (NIST RMF/ISO 31000)", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Define organizational risk tolerance", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Establish risk register", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-37', 'NIST SP 800-53 PM-9'],
        nist_mapping=['PM-9', 'RA-1', 'RA-3'],
        cis_mapping="15.2",
        default_severity=Severity.HIGH,
    ),
    "GOV-003": Control(
        id="GOV-003",
        name="Security Assessment & Authorization",
        description="All systems must undergo security assessment before authorization to operate (ATO).",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Governance & Compliance",
        check_procedure="""
1. Review ATO documentation
2. Verify assessment completeness
3. Check authorization status
4. Confirm continuous monitoring plan
        """,
        expected_result="All systems have current ATO with documented assessment results",
        remediation_steps=[
            RemediationStep(step_number=1, description="Conduct security assessment per NIST SP 800-53A", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=2, description="Prepare authorization package (SSP, SAR, POA&M)", command=None, script_type=None, estimated_time="80 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Submit to authorizing official", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
        ],
        references=['NIST SP 800-37', 'NIST SP 800-53A'],
        nist_mapping=['CA-2', 'CA-6', 'CA-7'],
        cis_mapping="15.3",
        default_severity=Severity.CRITICAL,
    ),
    "GOV-004": Control(
        id="GOV-004",
        name="Continuous Monitoring Program",
        description="A continuous monitoring program must track security control effectiveness with defined metrics.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Governance & Compliance",
        check_procedure="""
1. Review ISCM strategy
2. Verify monitoring metrics defined
3. Check automated monitoring tools
4. Review reporting cadence
        """,
        expected_result="ISCM strategy implemented with automated monitoring and monthly reporting",
        remediation_steps=[
            RemediationStep(step_number=1, description="Develop ISCM strategy", command=None, script_type=None, estimated_time="24 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Define monitoring metrics and thresholds", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Deploy automated monitoring tools", command=None, script_type=None, estimated_time="40 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-137', 'NIST SP 800-53 CA-7'],
        nist_mapping=['CA-7', 'CA-7(1)', 'PM-14'],
        cis_mapping="15.4",
        default_severity=Severity.HIGH,
    ),
    "GOV-005": Control(
        id="GOV-005",
        name="System Security Plan",
        description="All systems must have a current System Security Plan (SSP) documenting security controls and implementation.",
        family=ControlFamily.PLANNING,
        category="Governance & Compliance",
        check_procedure="""
1. Review SSP document
2. Verify accuracy of system description
3. Check control implementation details
4. Confirm SSP update schedule
        """,
        expected_result="SSP current within last 12 months with accurate control descriptions",
        remediation_steps=[
            RemediationStep(step_number=1, description="Draft SSP using NIST template", command=None, script_type=None, estimated_time="80 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Document all control implementations", command=None, script_type=None, estimated_time="40 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Review and approve SSP", command=None, script_type=None, estimated_time="1 week", requires_downtime=False),
        ],
        references=['NIST SP 800-18', 'NIST SP 800-53 PL-2'],
        nist_mapping=['PL-2', 'PL-2(3)', 'CA-6'],
        cis_mapping="15.5",
        default_severity=Severity.HIGH,
    ),
    "GOV-006": Control(
        id="GOV-006",
        name="Regulatory Compliance Tracking",
        description="All applicable regulatory requirements must be identified, tracked, and compliance validated.",
        family=ControlFamily.PLANNING,
        category="Governance & Compliance",
        check_procedure="""
1. Review compliance obligation register
2. Verify all regulations identified
3. Check compliance status per regulation
4. Review audit readiness
        """,
        expected_result="All applicable regulations tracked with documented compliance status",
        remediation_steps=[
            RemediationStep(step_number=1, description="Identify all applicable regulations (FISMA, HIPAA, PCI, etc.)", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Map requirements to implemented controls", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Establish compliance tracking dashboard", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
        ],
        references=['NIST CSF', 'NIST SP 800-53 PM-1'],
        nist_mapping=['PM-1', 'PL-4', 'CA-2'],
        cis_mapping="15.6",
        default_severity=Severity.MEDIUM,
    ),
    "GOV-007": Control(
        id="GOV-007",
        name="Security Metrics & Reporting",
        description="Security metrics must be collected, analyzed, and reported to leadership monthly.",
        family=ControlFamily.PLANNING,
        category="Governance & Compliance",
        check_procedure="""
1. Review metrics definition document
2. Verify data collection automation
3. Check reporting frequency
4. Review leadership briefing materials
        """,
        expected_result="Monthly security metrics dashboard with KPIs and trend analysis",
        remediation_steps=[
            RemediationStep(step_number=1, description="Define security KPIs and metrics", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Automate metric data collection", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Create executive dashboard", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-55', 'NIST SP 800-53 PM-6'],
        nist_mapping=['PM-6', 'PM-14', 'CA-7'],
        cis_mapping="15.7",
        default_severity=Severity.MEDIUM,
    ),
    "GOV-008": Control(
        id="GOV-008",
        name="Security Architecture Review",
        description="System architecture changes must undergo security architecture review before implementation.",
        family=ControlFamily.PLANNING,
        category="Governance & Compliance",
        check_procedure="""
1. Review architecture review process
2. Check recent reviews conducted
3. Verify security architect involvement
4. Confirm threat modeling included
        """,
        expected_result="All significant architecture changes reviewed with threat modeling",
        remediation_steps=[
            RemediationStep(step_number=1, description="Establish architecture review board", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Define review triggers and criteria", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Integrate threat modeling into reviews", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
        ],
        references=['SABSA Framework', 'NIST SP 800-53 PL-8'],
        nist_mapping=['PL-8', 'SA-8', 'RA-3'],
        cis_mapping="15.8",
        default_severity=Severity.MEDIUM,
    ),
    "GOV-009": Control(
        id="GOV-009",
        name="Interconnection Security Agreements",
        description="All system interconnections must have documented ISAs/MOUs defining security responsibilities.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Governance & Compliance",
        check_procedure="""
1. Inventory all system interconnections
2. Review ISA/MOU documents
3. Verify security requirements documented
4. Check ISA currency
        """,
        expected_result="All interconnections have current ISAs/MOUs reviewed within 12 months",
        remediation_steps=[
            RemediationStep(step_number=1, description="Inventory all system interconnections", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Draft ISA/MOU templates", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Execute ISAs with all interconnected systems", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
        ],
        references=['NIST SP 800-47', 'NIST SP 800-53 CA-3'],
        nist_mapping=['CA-3', 'CA-3(5)', 'SA-9'],
        cis_mapping="15.9",
        default_severity=Severity.HIGH,
    ),
    "GOV-010": Control(
        id="GOV-010",
        name="Privacy Impact Assessment",
        description="Systems processing PII must have a current Privacy Impact Assessment (PIA).",
        family=ControlFamily.PLANNING,
        category="Governance & Compliance",
        check_procedure="""
1. Identify systems processing PII
2. Verify PIA completion
3. Check PIA currency
4. Review privacy controls implemented
        """,
        expected_result="All PII-processing systems have current PIAs with privacy controls implemented",
        remediation_steps=[
            RemediationStep(step_number=1, description="Identify all PII data flows", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Conduct PIA per OMB guidance", command=None, script_type=None, estimated_time="24 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Implement required privacy controls", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
        ],
        references=['OMB M-03-22', 'NIST SP 800-122'],
        nist_mapping=['PT-1', 'PT-5', 'AR-2'],
        cis_mapping="15.10",
        default_severity=Severity.MEDIUM,
    ),
}

# ============================================================================
# WIRELESS & MOBILE SECURITY CONTROLS
# ============================================================================

WMS_CONTROLS = {
    "WMS-001": Control(
        id="WMS-001",
        name="Mobile Device Management",
        description="All mobile devices accessing organization data must be enrolled in an MDM solution.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Wireless & Mobile Security",
        check_procedure="""
1. Verify MDM deployment
2. Check enrolled device count vs total
3. Review compliance policies
4. Confirm remote wipe capability
        """,
        expected_result="100% of mobile devices enrolled in MDM with compliance policies enforced",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy MDM platform (Intune/Workspace ONE)", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure compliance policies", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Enroll all mobile devices", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
        ],
        references=['NIST SP 800-124', 'NIST SP 800-53 AC-19'],
        nist_mapping=['AC-19', 'AC-19(5)', 'CM-8'],
        cis_mapping="1.4",
        default_severity=Severity.HIGH,
    ),
    "WMS-002": Control(
        id="WMS-002",
        name="BYOD Security Policy",
        description="BYOD devices must meet minimum security requirements and use containerization for org data.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Wireless & Mobile Security",
        check_procedure="""
1. Review BYOD policy
2. Verify containerization deployed
3. Check minimum device requirements
4. Confirm data separation
        """,
        expected_result="BYOD policy enforced; org data containerized; personal data separated",
        remediation_steps=[
            RemediationStep(step_number=1, description="Draft BYOD security policy", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Deploy app containerization (MAM)", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure conditional access policies", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-124', 'NIST SP 800-53 AC-20'],
        nist_mapping=['AC-19', 'AC-20', 'MP-7'],
        cis_mapping="1.5",
        default_severity=Severity.MEDIUM,
    ),
    "WMS-003": Control(
        id="WMS-003",
        name="Wireless Network Security",
        description="All wireless networks must use WPA3 or WPA2-Enterprise with 802.1X authentication.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Wireless & Mobile Security",
        check_procedure="""
1. Survey wireless networks
2. Verify encryption standards
3. Check authentication method
4. Review rogue AP detection
        """,
        expected_result="All WLANs using WPA2-Enterprise minimum with certificate-based auth",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure WPA2-Enterprise/WPA3 on all APs", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Deploy RADIUS server for 802.1X", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure certificate-based authentication", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-97', 'CIS Wireless Benchmark'],
        nist_mapping=['SC-8', 'AC-18', 'IA-2'],
        cis_mapping="12.1",
        default_severity=Severity.HIGH,
    ),
    "WMS-004": Control(
        id="WMS-004",
        name="Rogue Wireless Detection",
        description="Wireless IDS must detect rogue access points and unauthorized wireless devices.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Wireless & Mobile Security",
        check_procedure="""
1. Verify WIDS deployment
2. Check rogue AP detection capability
3. Review alert response process
4. Test with controlled rogue AP
        """,
        expected_result="Rogue AP detection active with <15 minute alert time; response procedure documented",
        remediation_steps=[
            RemediationStep(step_number=1, description="Enable WIDS on wireless controller", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure rogue AP alerting", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Document rogue AP response procedure", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 AC-18', 'CIS Controls v8 12.6'],
        nist_mapping=['SI-4', 'AC-18(1)', 'SC-40'],
        cis_mapping="12.6",
        default_severity=Severity.MEDIUM,
    ),
    "WMS-005": Control(
        id="WMS-005",
        name="Guest Wireless Isolation",
        description="Guest wireless must be completely isolated from production network with bandwidth limitations.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Wireless & Mobile Security",
        check_procedure="""
1. Verify guest VLAN isolation
2. Test for cross-VLAN leakage
3. Check bandwidth restrictions
4. Confirm captive portal
        """,
        expected_result="Guest wireless fully isolated with no access to internal resources",
        remediation_steps=[
            RemediationStep(step_number=1, description="Create isolated guest VLAN", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure ACLs blocking internal access", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Deploy captive portal with ToS", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['CIS Wireless Benchmark', 'NIST SP 800-53 SC-7'],
        nist_mapping=['SC-7', 'AC-18(4)', 'AC-4'],
        cis_mapping="12.3",
        default_severity=Severity.MEDIUM,
    ),
    "WMS-006": Control(
        id="WMS-006",
        name="Mobile Application Security",
        description="Organization-deployed mobile apps must be vetted for security before distribution.",
        family=ControlFamily.SYSTEM_SERVICES,
        category="Wireless & Mobile Security",
        check_procedure="""
1. Review app vetting process
2. Check app store restrictions
3. Verify app wrapping/containerization
4. Review app permissions
        """,
        expected_result="Only vetted apps allowed; sideloading blocked; excessive permissions flagged",
        remediation_steps=[
            RemediationStep(step_number=1, description="Establish mobile app vetting process", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure app whitelist in MDM", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Block sideloading on managed devices", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['NIST SP 800-163', 'NIST SP 800-53 CM-7'],
        nist_mapping=['CM-7(5)', 'SA-11', 'CM-11'],
        cis_mapping="2.5",
        default_severity=Severity.MEDIUM,
    ),
    "WMS-007": Control(
        id="WMS-007",
        name="Mobile Device Encryption",
        description="All mobile devices must have full device encryption enabled with strong passcode requirements.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Wireless & Mobile Security",
        check_procedure="""
1. Verify encryption policy in MDM
2. Check compliance reporting
3. Review passcode requirements
4. Confirm non-compliant device blocking
        """,
        expected_result="100% mobile device encryption; 6+ digit passcode; non-compliant devices blocked",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure encryption requirement in MDM", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=2, description="Set passcode policy (6+ digits, biometric optional)", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Enable compliance blocking for non-encrypted devices", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['NIST SP 800-124', 'NIST SP 800-53 SC-28'],
        nist_mapping=['SC-28', 'MP-5', 'IA-5'],
        cis_mapping="3.6",
        default_severity=Severity.HIGH,
    ),
    "WMS-008": Control(
        id="WMS-008",
        name="Lost/Stolen Device Response",
        description="Procedures must exist for immediate remote wipe of lost or stolen mobile devices.",
        family=ControlFamily.MEDIA_PROTECTION,
        category="Wireless & Mobile Security",
        check_procedure="""
1. Review lost device procedure
2. Verify remote wipe capability
3. Check reporting process
4. Test remote wipe function
        """,
        expected_result="Remote wipe capable and tested; reporting process with <1 hour response",
        remediation_steps=[
            RemediationStep(step_number=1, description="Document lost/stolen device procedure", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure remote wipe in MDM", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Test remote wipe capability", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['NIST SP 800-124', 'NIST SP 800-53 MP-6'],
        nist_mapping=['MP-6', 'AC-19(5)', 'IR-4'],
        cis_mapping="3.7",
        default_severity=Severity.HIGH,
    ),
    "WMS-009": Control(
        id="WMS-009",
        name="Bluetooth Security",
        description="Bluetooth must be disabled by default on managed devices with exceptions requiring justification.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Wireless & Mobile Security",
        check_procedure="""
1. Check Bluetooth policy in MDM
2. Verify default disabled
3. Review exception process
4. Check for vulnerable BT versions
        """,
        expected_result="Bluetooth disabled by default; exceptions documented with compensating controls",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure Bluetooth disable policy in MDM", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=2, description="Create exception request process", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Scan for vulnerable Bluetooth versions", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-121', 'NIST SP 800-53 AC-18'],
        nist_mapping=['AC-18', 'SC-40', 'CM-7'],
        cis_mapping="12.8",
        default_severity=Severity.LOW,
    ),
    "WMS-010": Control(
        id="WMS-010",
        name="Wireless Penetration Testing",
        description="Wireless networks must undergo penetration testing at least annually.",
        family=ControlFamily.RISK_ASSESSMENT,
        category="Wireless & Mobile Security",
        check_procedure="""
1. Review last wireless pentest report
2. Check testing scope
3. Verify findings remediated
4. Confirm tester qualifications
        """,
        expected_result="Annual wireless pentest with all critical/high findings remediated",
        remediation_steps=[
            RemediationStep(step_number=1, description="Schedule wireless penetration test", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=2, description="Remediate identified vulnerabilities", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=3, description="Retest to confirm fixes", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['PTES Wireless', 'NIST SP 800-115'],
        nist_mapping=['CA-8', 'RA-5', 'AC-18'],
        cis_mapping="12.9",
        default_severity=Severity.MEDIUM,
    ),
}

# ============================================================================
# VIRTUALIZATION & CONTAINER SECURITY CONTROLS
# ============================================================================

VCS_CONTROLS = {
    "VCS-001": Control(
        id="VCS-001",
        name="Hypervisor Hardening",
        description="Hypervisors must be hardened per vendor security guidelines with unnecessary services disabled.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Virtualization & Container Security",
        check_procedure="""
1. Review hypervisor configuration
2. Compare against CIS benchmark
3. Check for unnecessary services
4. Verify lockdown mode
        """,
        expected_result="Hypervisor hardened per CIS benchmark; lockdown mode enabled",
        remediation_steps=[
            RemediationStep(step_number=1, description="Apply CIS VMware/Hyper-V benchmark", command=None, script_type=None, estimated_time="4 hours", requires_downtime=True),
            RemediationStep(step_number=2, description="Enable lockdown mode", command=None, script_type=None, estimated_time="1 hour", requires_downtime=True),
            RemediationStep(step_number=3, description="Disable unnecessary services", command=None, script_type=None, estimated_time="2 hours", requires_downtime=True),
        ],
        references=['CIS VMware Benchmark', 'NIST SP 800-125'],
        nist_mapping=['CM-6', 'CM-7', 'SC-3'],
        cis_mapping="4.4",
        default_severity=Severity.CRITICAL,
    ),
    "VCS-002": Control(
        id="VCS-002",
        name="VM Isolation & Segmentation",
        description="VMs must be segmented by security zone with micro-segmentation enforced at the hypervisor level.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Virtualization & Container Security",
        check_procedure="""
1. Review network segmentation policy
2. Verify port group isolation
3. Check micro-segmentation rules
4. Test cross-zone communication
        """,
        expected_result="VMs segmented by zone; no unauthorized cross-zone communication",
        remediation_steps=[
            RemediationStep(step_number=1, description="Design VM network segmentation", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure distributed firewall rules", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Test isolation between zones", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-125A', 'NSX Security Guide'],
        nist_mapping=['SC-7', 'SC-3', 'AC-4'],
        cis_mapping="12.2",
        default_severity=Severity.HIGH,
    ),
    "VCS-003": Control(
        id="VCS-003",
        name="Container Runtime Security",
        description="Container runtimes must enforce resource limits, read-only filesystems, and non-root execution.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Virtualization & Container Security",
        check_procedure="""
1. Review container security policies
2. Check for root containers
3. Verify resource limits set
4. Confirm read-only root filesystem
        """,
        expected_result="No containers running as root; resource limits enforced; read-only FS where possible",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure PodSecurityPolicy/SecurityContext", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Set resource limits in all deployments", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Enable read-only root filesystem", command=None, script_type=None, estimated_time="4 hours", requires_downtime=True),
        ],
        references=['CIS Docker Benchmark', 'CIS Kubernetes Benchmark'],
        nist_mapping=['SC-39', 'CM-7', 'AC-6'],
        cis_mapping="5.1",
        default_severity=Severity.HIGH,
    ),
    "VCS-004": Control(
        id="VCS-004",
        name="Container Registry Security",
        description="Container registries must require authentication, enforce vulnerability scanning, and use signed images.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Virtualization & Container Security",
        check_procedure="""
1. Verify registry authentication
2. Check image scanning configuration
3. Review image signing
4. Confirm pull policies
        """,
        expected_result="Registry authenticated; all images scanned; only signed images deployed",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure registry authentication", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Enable automated image scanning", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Implement image signing (Cosign/Notary)", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['CIS Docker Benchmark', 'NIST SP 800-190'],
        nist_mapping=['SI-7', 'CM-7(5)', 'IA-3'],
        cis_mapping="5.2",
        default_severity=Severity.HIGH,
    ),
    "VCS-005": Control(
        id="VCS-005",
        name="VM Snapshot Management",
        description="VM snapshots must not persist beyond 72 hours and must not contain sensitive data in memory dumps.",
        family=ControlFamily.MEDIA_PROTECTION,
        category="Virtualization & Container Security",
        check_procedure="""
1. List all active snapshots
2. Check snapshot ages
3. Review snapshot policy
4. Verify memory snapshots encrypted
        """,
        expected_result="No snapshots older than 72 hours; memory snapshots encrypted or excluded",
        remediation_steps=[
            RemediationStep(step_number=1, description="Audit all active VM snapshots", command="Get-VM | Get-Snapshot | Where-Object {$_.Created -lt (Get-Date).AddHours(-72)} | Select-Object VM, Name, Created", script_type="powershell", estimated_time="30 minutes", requires_downtime=False),
            RemediationStep(step_number=2, description="Remove stale snapshots", command=None, script_type=None, estimated_time="1 hour", requires_downtime=True),
            RemediationStep(step_number=3, description="Implement snapshot aging policy", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['VMware Best Practices', 'NIST SP 800-125'],
        nist_mapping=['MP-4', 'SC-28', 'CM-3'],
        cis_mapping="3.8",
        default_severity=Severity.MEDIUM,
    ),
    "VCS-006": Control(
        id="VCS-006",
        name="Kubernetes RBAC",
        description="Kubernetes clusters must enforce RBAC with least privilege and no default service account usage.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Virtualization & Container Security",
        check_procedure="""
1. Review RBAC configuration
2. Check for ClusterAdmin overuse
3. Verify service account restrictions
4. Audit namespace isolation
        """,
        expected_result="RBAC enforced; no unnecessary ClusterAdmin bindings; default SA restricted",
        remediation_steps=[
            RemediationStep(step_number=1, description="Audit current RBAC bindings", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Remove unnecessary ClusterAdmin bindings", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Restrict default service accounts", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['CIS Kubernetes Benchmark', 'NIST SP 800-53 AC-3'],
        nist_mapping=['AC-3', 'AC-6', 'AC-2'],
        cis_mapping="5.1.1",
        default_severity=Severity.HIGH,
    ),
    "VCS-007": Control(
        id="VCS-007",
        name="Virtual Network Security",
        description="Virtual switches and network overlays must enforce the same security policies as physical networks.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Virtualization & Container Security",
        check_procedure="""
1. Review vSwitch security settings
2. Verify promiscuous mode disabled
3. Check MAC address change policy
4. Review forged transmits setting
        """,
        expected_result="Promiscuous mode disabled; MAC changes rejected; forged transmits blocked",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure vSwitch security policies", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Disable promiscuous mode", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
            RemediationStep(step_number=3, description="Block MAC address changes and forged transmits", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
        ],
        references=['CIS VMware Benchmark', 'NIST SP 800-125A'],
        nist_mapping=['SC-7', 'AC-4', 'CM-6'],
        cis_mapping="12.4",
        default_severity=Severity.MEDIUM,
    ),
    "VCS-008": Control(
        id="VCS-008",
        name="Container Secrets Management",
        description="Container secrets must be stored in dedicated secrets management (not environment variables or config files).",
        family=ControlFamily.IDENTIFICATION_AUTH,
        category="Virtualization & Container Security",
        check_procedure="""
1. Scan for secrets in container configs
2. Verify secrets manager integration
3. Check secret rotation
4. Review access policies
        """,
        expected_result="All secrets in dedicated store; no plaintext secrets in configs/env vars",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy secrets manager (Vault/AWS Secrets Manager)", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Migrate secrets from env vars to secrets store", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure automatic rotation", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-190', 'HashiCorp Vault Docs'],
        nist_mapping=['IA-5', 'SC-12', 'SC-28'],
        cis_mapping="5.4",
        default_severity=Severity.CRITICAL,
    ),
    "VCS-009": Control(
        id="VCS-009",
        name="VM Template Security",
        description="VM templates must be hardened, patched, and validated before use for new deployments.",
        family=ControlFamily.CONFIG_MANAGEMENT,
        category="Virtualization & Container Security",
        check_procedure="""
1. Review template hardening
2. Check template patch level
3. Verify template scanning
4. Confirm template approval process
        """,
        expected_result="Templates hardened per CIS; patched within 30 days; scanned before use",
        remediation_steps=[
            RemediationStep(step_number=1, description="Apply CIS benchmark to VM template", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Schedule monthly template patching", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Scan template for vulnerabilities", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
        ],
        references=['CIS Benchmarks', 'NIST SP 800-125'],
        nist_mapping=['CM-2', 'CM-6', 'SI-2'],
        cis_mapping="4.5",
        default_severity=Severity.MEDIUM,
    ),
    "VCS-010": Control(
        id="VCS-010",
        name="Container Network Policies",
        description="Kubernetes network policies must restrict pod-to-pod communication to only necessary flows.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Virtualization & Container Security",
        check_procedure="""
1. Review network policies
2. Check for default-deny
3. Verify allowed flows documented
4. Test policy enforcement
        """,
        expected_result="Default-deny network policies with documented allowed flows per namespace",
        remediation_steps=[
            RemediationStep(step_number=1, description="Implement default-deny network policies", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Document required network flows", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Test policy enforcement", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['CIS Kubernetes Benchmark', 'NIST SP 800-190'],
        nist_mapping=['SC-7', 'AC-4', 'SC-7(5)'],
        cis_mapping="5.3",
        default_severity=Severity.HIGH,
    ),
}

# ============================================================================
# EMAIL & COMMUNICATIONS SECURITY CONTROLS
# ============================================================================

ECS_CONTROLS = {
    "ECS-001": Control(
        id="ECS-001",
        name="Email Gateway Protection",
        description="Email must pass through a secure gateway with anti-malware, anti-spam, and sandboxing capabilities.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Email & Communications Security",
        check_procedure="""
1. Verify email gateway deployment
2. Check anti-malware effectiveness
3. Review spam filtering rates
4. Confirm sandboxing enabled
        """,
        expected_result="Email gateway active with >99% spam catch rate and sandboxing for attachments",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy email security gateway", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure anti-malware and sandboxing", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Tune spam filters", command=None, script_type=None, estimated_time="Ongoing", requires_downtime=False),
        ],
        references=['NIST SP 800-177', 'CIS Controls v8 9.1'],
        nist_mapping=['SI-8', 'SI-3', 'SC-7'],
        cis_mapping="9.1",
        default_severity=Severity.CRITICAL,
    ),
    "ECS-002": Control(
        id="ECS-002",
        name="DMARC/DKIM/SPF Implementation",
        description="All email domains must have SPF, DKIM, and DMARC configured to prevent email spoofing.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Email & Communications Security",
        check_procedure="""
1. Check DNS for SPF record
2. Verify DKIM signing
3. Confirm DMARC policy
4. Review DMARC reports
        """,
        expected_result="SPF, DKIM, and DMARC (p=reject) configured for all domains",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure SPF record in DNS", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=2, description="Enable DKIM signing", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Deploy DMARC policy (start with p=none, advance to p=reject)", command=None, script_type=None, estimated_time="4 weeks", requires_downtime=False),
        ],
        references=['NIST SP 800-177', 'CISA BOD 18-01'],
        nist_mapping=['SC-8', 'SI-8', 'SC-7'],
        cis_mapping="9.2",
        default_severity=Severity.HIGH,
    ),
    "ECS-003": Control(
        id="ECS-003",
        name="Email Encryption",
        description="Sensitive emails must be encrypted in transit (TLS) and at rest with S/MIME or equivalent.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Email & Communications Security",
        check_procedure="""
1. Verify TLS enforcement
2. Check S/MIME deployment
3. Review encryption policy triggers
4. Test encryption functionality
        """,
        expected_result="TLS enforced for all email; S/MIME available for sensitive communications",
        remediation_steps=[
            RemediationStep(step_number=1, description="Enable opportunistic TLS on mail server", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=2, description="Deploy S/MIME certificates", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure DLP rules for auto-encryption", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-177', 'NIST SP 800-53 SC-8'],
        nist_mapping=['SC-8', 'SC-8(1)', 'SC-12'],
        cis_mapping="9.3",
        default_severity=Severity.MEDIUM,
    ),
    "ECS-004": Control(
        id="ECS-004",
        name="Phishing Protection",
        description="Advanced phishing protection must include URL rewriting, attachment sandboxing, and impersonation detection.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Email & Communications Security",
        check_procedure="""
1. Verify URL rewriting active
2. Check attachment sandboxing
3. Review impersonation detection rules
4. Test with simulated phishing
        """,
        expected_result="URL rewriting, sandboxing, and impersonation detection all active and tested",
        remediation_steps=[
            RemediationStep(step_number=1, description="Enable URL rewriting/safe links", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure attachment sandboxing", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Set up impersonation protection rules", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['Microsoft ATP', 'NIST SP 800-53 SI-8'],
        nist_mapping=['SI-8', 'SI-3', 'SI-4'],
        cis_mapping="9.4",
        default_severity=Severity.HIGH,
    ),
    "ECS-005": Control(
        id="ECS-005",
        name="Email Data Loss Prevention",
        description="DLP policies must prevent sensitive data (PII, PHI, classified) from being sent via email.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Email & Communications Security",
        check_procedure="""
1. Review email DLP policies
2. Check sensitive data patterns configured
3. Review DLP incident reports
4. Verify user notification
        """,
        expected_result="DLP policies active for all sensitive data types; false positive rate <5%",
        remediation_steps=[
            RemediationStep(step_number=1, description="Define sensitive data patterns (SSN, CC, etc.)", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure DLP transport rules", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Test with sample data", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 AC-4', 'DLP Best Practices'],
        nist_mapping=['SC-7', 'AC-4', 'SI-4'],
        cis_mapping="9.5",
        default_severity=Severity.HIGH,
    ),
    "ECS-006": Control(
        id="ECS-006",
        name="Unified Communications Security",
        description="VoIP, video conferencing, and messaging platforms must be secured with encryption and access controls.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Email & Communications Security",
        check_procedure="""
1. Verify SRTP enabled for VoIP
2. Check video conferencing encryption
3. Review messaging platform security
4. Confirm access controls
        """,
        expected_result="All UC platforms encrypted; meeting passwords enforced; lobbies enabled",
        remediation_steps=[
            RemediationStep(step_number=1, description="Enable SRTP on VoIP systems", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure meeting security defaults", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Enable E2E encryption where available", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 SC-8', 'UC Security Guide'],
        nist_mapping=['SC-8', 'SC-12', 'AC-3'],
        cis_mapping="9.6",
        default_severity=Severity.MEDIUM,
    ),
    "ECS-007": Control(
        id="ECS-007",
        name="Email Retention & Archival",
        description="Email retention policies must comply with regulatory requirements with secure archival and eDiscovery capability.",
        family=ControlFamily.AUDIT_ACCOUNTABILITY,
        category="Email & Communications Security",
        check_procedure="""
1. Review retention policy
2. Verify archival configuration
3. Check eDiscovery capability
4. Confirm legal hold process
        """,
        expected_result="Retention policies set per regulation; archive searchable; legal hold functional",
        remediation_steps=[
            RemediationStep(step_number=1, description="Define retention policies per regulatory requirement", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Configure email archival", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Test eDiscovery search and legal hold", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 AU-11', 'eDiscovery Reference Model'],
        nist_mapping=['AU-11', 'SI-12', 'MP-4'],
        cis_mapping="9.7",
        default_severity=Severity.MEDIUM,
    ),
    "ECS-008": Control(
        id="ECS-008",
        name="Secure File Transfer",
        description="File transfers containing sensitive data must use encrypted protocols (SFTP, FTPS, HTTPS) with logging.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Email & Communications Security",
        check_procedure="""
1. Inventory file transfer methods
2. Verify encryption enabled
3. Check logging configuration
4. Review access controls
        """,
        expected_result="All file transfers encrypted; FTP disabled; transfers logged and auditable",
        remediation_steps=[
            RemediationStep(step_number=1, description="Disable unencrypted FTP", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=2, description="Deploy managed file transfer (MFT) solution", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure transfer logging and alerting", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-53 SC-8', 'PCI DSS 4.1'],
        nist_mapping=['SC-8', 'SC-8(1)', 'AU-2'],
        cis_mapping="9.8",
        default_severity=Severity.HIGH,
    ),
    "ECS-009": Control(
        id="ECS-009",
        name="Collaboration Platform Security",
        description="Collaboration tools (Teams, Slack, SharePoint) must have DLP, guest access controls, and data classification.",
        family=ControlFamily.ACCESS_CONTROL,
        category="Email & Communications Security",
        check_procedure="""
1. Review collaboration platform settings
2. Check guest access restrictions
3. Verify DLP integration
4. Confirm data classification labels
        """,
        expected_result="Guest access restricted; DLP active; sensitivity labels enforced",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure guest access policies", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Enable DLP for collaboration platforms", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Deploy sensitivity labels", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
        ],
        references=['Microsoft 365 Security', 'NIST SP 800-53 AC-3'],
        nist_mapping=['AC-3', 'AC-22', 'SC-7'],
        cis_mapping="9.9",
        default_severity=Severity.MEDIUM,
    ),
    "ECS-010": Control(
        id="ECS-010",
        name="External Email Marking",
        description="All emails from external senders must be visually tagged with [EXTERNAL] warning banners.",
        family=ControlFamily.SYSTEM_INFO_INTEGRITY,
        category="Email & Communications Security",
        check_procedure="""
1. Verify external tagging rule
2. Check banner display
3. Review user awareness of tags
4. Confirm no internal email false tags
        """,
        expected_result="All external emails tagged with visible [EXTERNAL] banner; no false positives",
        remediation_steps=[
            RemediationStep(step_number=1, description="Create mail flow rule for external tagging", command="New-TransportRule -Name 'External Email Banner' -FromScope NotInOrganization -PrependSubject '[EXTERNAL] '", script_type="powershell", estimated_time="30 minutes", requires_downtime=False),
            RemediationStep(step_number=2, description="Add HTML banner to email body", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Communicate change to users", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
        ],
        references=['CISA Email Authentication', 'NIST SP 800-53 SI-8'],
        nist_mapping=['SI-8', 'AT-2', 'SC-7'],
        cis_mapping="9.10",
        default_severity=Severity.LOW,
    ),
}

# ============================================================================
# CRYPTOGRAPHIC CONTROLS CONTROLS
# ============================================================================

CRY_CONTROLS = {
    "CRY-001": Control(
        id="CRY-001",
        name="Cryptographic Standards Policy",
        description="Organization must define approved cryptographic algorithms, key lengths, and prohibited ciphers.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Cryptographic Controls",
        check_procedure="""
1. Review crypto policy document
2. Verify approved algorithm list
3. Check prohibited cipher list
4. Confirm FIPS 140-2/3 requirements
        """,
        expected_result="Documented crypto policy with approved algorithms aligned to NIST guidelines",
        remediation_steps=[
            RemediationStep(step_number=1, description="Document cryptographic standards policy", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Define approved algorithms (AES-256, RSA-2048+, SHA-256+)", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Identify and document prohibited ciphers", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-175B', 'NIST SP 800-53 SC-13'],
        nist_mapping=['SC-13', 'SC-12', 'PL-2'],
        cis_mapping="3.10",
        default_severity=Severity.HIGH,
    ),
    "CRY-002": Control(
        id="CRY-002",
        name="TLS Configuration",
        description="All TLS implementations must use TLS 1.2+ with strong cipher suites; TLS 1.0/1.1 must be disabled.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Cryptographic Controls",
        check_procedure="""
1. Scan for TLS version support
2. Check cipher suite order
3. Verify weak ciphers disabled
4. Test with SSL Labs or testssl.sh
        """,
        expected_result="TLS 1.2/1.3 only; A+ rating on SSL Labs; no weak ciphers",
        remediation_steps=[
            RemediationStep(step_number=1, description="Disable TLS 1.0/1.1", command="Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\TLS 1.0\\Server' -Name Enabled -Value 0", script_type="powershell", estimated_time="1 hour", requires_downtime=True),
            RemediationStep(step_number=2, description="Configure strong cipher suite order", command=None, script_type=None, estimated_time="2 hours", requires_downtime=True),
            RemediationStep(step_number=3, description="Test with SSL Labs", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
        ],
        references=['NIST SP 800-52 Rev 2', 'Mozilla TLS Configuration'],
        nist_mapping=['SC-8', 'SC-8(1)', 'SC-13'],
        cis_mapping="3.10",
        default_severity=Severity.HIGH,
    ),
    "CRY-003": Control(
        id="CRY-003",
        name="Certificate Lifecycle Management",
        description="All certificates must be inventoried, tracked for expiration, and renewed 30 days before expiry.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Cryptographic Controls",
        check_procedure="""
1. Inventory all certificates
2. Check expiration dates
3. Verify renewal automation
4. Review CA trust chain
        """,
        expected_result="All certs inventoried; no expired certs; renewal alerts at 30 days",
        remediation_steps=[
            RemediationStep(step_number=1, description="Deploy certificate discovery tool", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Inventory all certificates", command="Get-ChildItem -Path Cert:\\LocalMachine\\My | Select-Object Subject, NotAfter, Issuer | Sort-Object NotAfter", script_type="powershell", estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Configure expiration alerting", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-57', 'NIST SP 800-53 SC-17'],
        nist_mapping=['SC-17', 'IA-5(2)', 'CM-8'],
        cis_mapping="3.11",
        default_severity=Severity.HIGH,
    ),
    "CRY-004": Control(
        id="CRY-004",
        name="PKI Infrastructure Security",
        description="Internal PKI must be secured with offline root CA, constrained intermediate CAs, and audited issuance.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Cryptographic Controls",
        check_procedure="""
1. Verify root CA offline
2. Check CA security configuration
3. Review certificate templates
4. Audit recent issuance
        """,
        expected_result="Root CA offline; intermediate CA hardened; certificate issuance audited",
        remediation_steps=[
            RemediationStep(step_number=1, description="Verify root CA is offline and secured", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Review and restrict certificate templates", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Enable CA issuance auditing", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['Microsoft PKI Best Practices', 'NIST SP 800-57'],
        nist_mapping=['SC-17', 'SC-12(1)', 'AU-2'],
        cis_mapping="3.12",
        default_severity=Severity.CRITICAL,
    ),
    "CRY-005": Control(
        id="CRY-005",
        name="Encryption Key Rotation",
        description="Encryption keys must be rotated per defined schedules based on key type and data sensitivity.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Cryptographic Controls",
        check_procedure="""
1. Review key rotation policy
2. Check rotation schedules by key type
3. Verify automated rotation
4. Confirm old keys properly retired
        """,
        expected_result="Keys rotated per schedule; automated where possible; old keys securely destroyed",
        remediation_steps=[
            RemediationStep(step_number=1, description="Define key rotation schedule by type", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Implement automated key rotation", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Document key destruction procedures", command=None, script_type=None, estimated_time="2 hours", requires_downtime=False),
        ],
        references=['NIST SP 800-57', 'NIST SP 800-53 SC-12'],
        nist_mapping=['SC-12', 'SC-12(1)', 'SC-28'],
        cis_mapping="3.13",
        default_severity=Severity.HIGH,
    ),
    "CRY-006": Control(
        id="CRY-006",
        name="Hardware Security Module Usage",
        description="Critical keys (CA signing, disk encryption master, authentication) must be stored in FIPS 140-2 Level 2+ HSMs.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Cryptographic Controls",
        check_procedure="""
1. Inventory critical keys
2. Verify HSM deployment
3. Check FIPS 140-2 certification level
4. Review HSM access controls
        """,
        expected_result="All critical keys in FIPS 140-2 Level 2+ HSMs with documented access controls",
        remediation_steps=[
            RemediationStep(step_number=1, description="Identify critical keys requiring HSM storage", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Procure and deploy HSM", command=None, script_type=None, estimated_time="Variable", requires_downtime=False),
            RemediationStep(step_number=3, description="Migrate critical keys to HSM", command=None, script_type=None, estimated_time="8 hours", requires_downtime=True),
        ],
        references=['FIPS 140-2', 'NIST SP 800-57'],
        nist_mapping=['SC-12(1)', 'SC-13', 'IA-7'],
        cis_mapping="3.14",
        default_severity=Severity.HIGH,
    ),
    "CRY-007": Control(
        id="CRY-007",
        name="Deprecated Algorithm Remediation",
        description="Systems must not use deprecated algorithms (MD5, SHA-1, DES, 3DES, RC4, RSA <2048).",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Cryptographic Controls",
        check_procedure="""
1. Scan for deprecated algorithms
2. Check TLS cipher suites
3. Review application crypto usage
4. Verify hash algorithms in use
        """,
        expected_result="No deprecated algorithms in use across all systems",
        remediation_steps=[
            RemediationStep(step_number=1, description="Scan network for deprecated cipher usage", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Identify applications using deprecated algorithms", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Upgrade to approved algorithms", command=None, script_type=None, estimated_time="Variable", requires_downtime=True),
        ],
        references=['NIST SP 800-131A', 'NIST SP 800-53 SC-13'],
        nist_mapping=['SC-13', 'SC-8', 'IA-7'],
        cis_mapping="3.15",
        default_severity=Severity.HIGH,
    ),
    "CRY-008": Control(
        id="CRY-008",
        name="Crypto Agility Planning",
        description="Organization must plan for cryptographic transitions including post-quantum readiness.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Cryptographic Controls",
        check_procedure="""
1. Review crypto agility plan
2. Check inventory of crypto implementations
3. Verify PQC awareness
4. Review migration timeline
        """,
        expected_result="Crypto agility plan documented; all crypto implementations inventoried",
        remediation_steps=[
            RemediationStep(step_number=1, description="Inventory all cryptographic implementations", command=None, script_type=None, estimated_time="16 hours", requires_downtime=False),
            RemediationStep(step_number=2, description="Document crypto agility plan", command=None, script_type=None, estimated_time="8 hours", requires_downtime=False),
            RemediationStep(step_number=3, description="Monitor NIST PQC standardization", command=None, script_type=None, estimated_time="Ongoing", requires_downtime=False),
        ],
        references=['NIST PQC Project', 'CISA PQC Guidance'],
        nist_mapping=['SC-13', 'PL-8', 'PM-30'],
        cis_mapping="3.16",
        default_severity=Severity.MEDIUM,
    ),
    "CRY-009": Control(
        id="CRY-009",
        name="Disk Encryption Key Escrow",
        description="BitLocker/disk encryption recovery keys must be escrowed in AD or a secure key management system.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Cryptographic Controls",
        check_procedure="""
1. Verify key escrow configuration
2. Check recovery key storage
3. Test key recovery process
4. Review access to escrowed keys
        """,
        expected_result="All recovery keys escrowed in AD/key vault; recovery process tested",
        remediation_steps=[
            RemediationStep(step_number=1, description="Configure BitLocker AD key escrow via GPO", command="Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\FVE' -Name 'ActiveDirectoryBackup' -Value 1", script_type="powershell", estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=2, description="Verify keys escrowed for all encrypted volumes", command=None, script_type=None, estimated_time="1 hour", requires_downtime=False),
            RemediationStep(step_number=3, description="Test recovery key retrieval", command=None, script_type=None, estimated_time="30 minutes", requires_downtime=False),
        ],
        references=['Microsoft BitLocker', 'NIST SP 800-53 SC-12'],
        nist_mapping=['SC-12', 'SC-28', 'CP-9'],
        cis_mapping="3.6",
        default_severity=Severity.MEDIUM,
    ),
    "CRY-010": Control(
        id="CRY-010",
        name="Random Number Generation",
        description="Systems must use FIPS-approved random number generators for all cryptographic operations.",
        family=ControlFamily.SYSTEM_COMM_PROTECTION,
        category="Cryptographic Controls",
        check_procedure="""
1. Review RNG sources
2. Check FIPS mode status
3. Verify entropy sources
4. Test RNG output quality
        """,
        expected_result="FIPS-approved RNG in use; adequate entropy sources configured",
        remediation_steps=[
            RemediationStep(step_number=1, description="Enable FIPS mode on Windows", command="Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa\\FipsAlgorithmPolicy' -Name 'Enabled' -Value 1", script_type="powershell", estimated_time="30 minutes", requires_downtime=True),
            RemediationStep(step_number=2, description="Verify application compatibility with FIPS mode", command=None, script_type=None, estimated_time="4 hours", requires_downtime=False),
        ],
        references=['FIPS 140-2 Annex C', 'NIST SP 800-90A'],
        nist_mapping=['SC-13', 'IA-7', 'SC-12'],
        cis_mapping="3.17",
        default_severity=Severity.MEDIUM,
    ),
}

# ============================================================================
# CONTROL LIBRARY AGGREGATION
# ============================================================================

ALL_CONTROLS = {
    **AD_CONTROLS,
    **NETWORK_CONTROLS,
    **ENDPOINT_CONTROLS,
    **PHYSICAL_CONTROLS,
    **SERVER_CONTROLS,
    **DATA_CONTROLS,
    **IAM_CONTROLS,
    **MONITORING_CONTROLS,
    **VM_CONTROLS,
    **CFG_CONTROLS,
    **IR_CONTROLS,
    **CP_CONTROLS,
    **SAT_CONTROLS,
    **APP_CONTROLS,
    **SCR_CONTROLS,
    **GOV_CONTROLS,
    **WMS_CONTROLS,
    **VCS_CONTROLS,
    **ECS_CONTROLS,
    **CRY_CONTROLS,
}

def get_control_by_id(control_id: str) -> Optional[Control]:
    """Get a control by its ID"""
    return ALL_CONTROLS.get(control_id)

def get_controls_by_family(family: ControlFamily) -> List[Control]:
    """Get all controls in a specific family"""
    return [c for c in ALL_CONTROLS.values() if c.family == family]

def get_controls_by_category(category: str) -> List[Control]:
    """Get all controls in a specific category"""
    return [c for c in ALL_CONTROLS.values() if c.category == category]

def get_remediation_script(control_id: str, script_type: str = "powershell") -> str:
    """Generate a remediation script for a control"""
    control = get_control_by_id(control_id)
    if not control:
        return ""
    
    script_lines = [f"# Remediation Script for {control.id}: {control.name}"]
    script_lines.append(f"# Family: {control.family.value}")
    script_lines.append(f"# Generated by OPRA\n")
    
    for step in control.remediation_steps:
        if step.command and step.script_type == script_type:
            script_lines.append(f"# Step {step.step_number}: {step.description}")
            script_lines.append(step.command)
            script_lines.append("")
    
    return "\n".join(script_lines)
