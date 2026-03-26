#!/usr/bin/env python3
"""
NIST 800-30 Enhanced Security Risk Score Calculator
====================================================
Calculates risk scores from security assessment reports based on
NIST SP 800-30 Rev 1 methodology with comprehensive threat modeling,
multi-dimensional impact assessment, and quantitative risk analysis.

Features:
- Threat Source Identification (NIST 800-30 Section 2.1.1)
- Threat Event Identification with MITRE ATT&CK mapping (Section 2.1.2)
- Multi-dimensional Impact Assessment (C/I/A + Financial/Mission)
- Enhanced Likelihood Determination (Section 2.2)
- Annualized Loss Expectancy (ALE) Calculator
- Risk Aggregation with Confidence Levels

Author: Security Architecture and Evaluation
Version: 2.0 - NIST 800-30 Enhanced
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import math


# =============================================================================
# NIST 800-30 SECTION 2.1.1: THREAT SOURCE IDENTIFICATION
# =============================================================================

class ThreatSourceType(Enum):
    """Types of threat sources per NIST 800-30."""
    ADVERSARIAL = "Adversarial"
    ACCIDENTAL = "Accidental"
    STRUCTURAL = "Structural"
    ENVIRONMENTAL = "Environmental"


class ThreatCapability(Enum):
    """Threat actor capability level (1-5 scale)."""
    VERY_LOW = 1    # Limited skills, no resources
    LOW = 2         # Basic skills, minimal resources
    MODERATE = 3    # Moderate skills and resources
    HIGH = 4        # Advanced skills, significant resources
    VERY_HIGH = 5   # Nation-state level capabilities


class ThreatIntent(Enum):
    """Threat actor intent level (1-5 scale)."""
    VERY_LOW = 1    # No specific targeting
    LOW = 2         # Opportunistic
    MODERATE = 3    # Targeted but not persistent
    HIGH = 4        # Actively targeting
    VERY_HIGH = 5   # Persistent, dedicated targeting


@dataclass
class ThreatSource:
    """
    Represents a threat source per NIST 800-30.
    Includes capability, intent, and targeting information.
    """
    source_id: str
    name: str
    source_type: ThreatSourceType
    capability: ThreatCapability
    intent: ThreatIntent
    description: str = ""
    targeting_likelihood: float = 0.5  # 0-1 probability of targeting this org
    
    @property
    def threat_score(self) -> float:
        """Calculate composite threat score (1-25 scale)."""
        return self.capability.value * self.intent.value
    
    @property
    def effective_threat(self) -> float:
        """Threat score adjusted for targeting likelihood."""
        return self.threat_score * self.targeting_likelihood


# Pre-defined threat source catalog
THREAT_SOURCE_CATALOG = {
    "NATION_STATE": ThreatSource(
        source_id="TS-001",
        name="Nation State Actor",
        source_type=ThreatSourceType.ADVERSARIAL,
        capability=ThreatCapability.VERY_HIGH,
        intent=ThreatIntent.VERY_HIGH,
        description="State-sponsored actors with advanced persistent threat capabilities",
        targeting_likelihood=0.3
    ),
    "ORGANIZED_CRIME": ThreatSource(
        source_id="TS-002",
        name="Organized Criminal Group",
        source_type=ThreatSourceType.ADVERSARIAL,
        capability=ThreatCapability.HIGH,
        intent=ThreatIntent.VERY_HIGH,
        description="Financially motivated criminal organizations",
        targeting_likelihood=0.5
    ),
    "HACKTIVIST": ThreatSource(
        source_id="TS-003",
        name="Hacktivist",
        source_type=ThreatSourceType.ADVERSARIAL,
        capability=ThreatCapability.MODERATE,
        intent=ThreatIntent.HIGH,
        description="Ideologically motivated threat actors",
        targeting_likelihood=0.2
    ),
    "INSIDER_MALICIOUS": ThreatSource(
        source_id="TS-004",
        name="Malicious Insider",
        source_type=ThreatSourceType.ADVERSARIAL,
        capability=ThreatCapability.HIGH,
        intent=ThreatIntent.VERY_HIGH,
        description="Employees or contractors with malicious intent",
        targeting_likelihood=0.4
    ),
    "INSIDER_NEGLIGENT": ThreatSource(
        source_id="TS-005",
        name="Negligent Insider",
        source_type=ThreatSourceType.ACCIDENTAL,
        capability=ThreatCapability.LOW,
        intent=ThreatIntent.VERY_LOW,
        description="Unintentional actions by employees",
        targeting_likelihood=0.8
    ),
    "SCRIPT_KIDDIE": ThreatSource(
        source_id="TS-006",
        name="Script Kiddie",
        source_type=ThreatSourceType.ADVERSARIAL,
        capability=ThreatCapability.LOW,
        intent=ThreatIntent.MODERATE,
        description="Opportunistic attackers using pre-made tools",
        targeting_likelihood=0.6
    ),
    "COMPETITOR": ThreatSource(
        source_id="TS-007",
        name="Competitor/Corporate Espionage",
        source_type=ThreatSourceType.ADVERSARIAL,
        capability=ThreatCapability.MODERATE,
        intent=ThreatIntent.HIGH,
        description="Business competitors seeking proprietary information",
        targeting_likelihood=0.3
    ),
    "SYSTEM_FAILURE": ThreatSource(
        source_id="TS-008",
        name="System/Hardware Failure",
        source_type=ThreatSourceType.STRUCTURAL,
        capability=ThreatCapability.MODERATE,
        intent=ThreatIntent.VERY_LOW,
        description="Technical failures and malfunctions",
        targeting_likelihood=0.7
    ),
    "NATURAL_DISASTER": ThreatSource(
        source_id="TS-009",
        name="Natural Disaster",
        source_type=ThreatSourceType.ENVIRONMENTAL,
        capability=ThreatCapability.VERY_HIGH,
        intent=ThreatIntent.VERY_LOW,
        description="Environmental events (flood, fire, earthquake)",
        targeting_likelihood=0.2
    ),
}


# =============================================================================
# NIST 800-30 SECTION 2.1.2: THREAT EVENTS & MITRE ATT&CK MAPPING
# =============================================================================

@dataclass
class MITREAttackTechnique:
    """MITRE ATT&CK technique mapping."""
    technique_id: str
    technique_name: str
    tactic: str
    description: str = ""


# MITRE ATT&CK mapping for NIST control families
MITRE_ATTACK_MAPPING = {
    'AC': [  # Access Control
        MITREAttackTechnique("T1078", "Valid Accounts", "Initial Access", "Use of valid credentials"),
        MITREAttackTechnique("T1098", "Account Manipulation", "Persistence", "Modifying account attributes"),
        MITREAttackTechnique("T1136", "Create Account", "Persistence", "Creating new accounts"),
        MITREAttackTechnique("T1548", "Abuse Elevation Control", "Privilege Escalation", "Bypassing access controls"),
    ],
    'AU': [  # Audit and Accountability
        MITREAttackTechnique("T1070", "Indicator Removal", "Defense Evasion", "Clearing logs"),
        MITREAttackTechnique("T1562", "Impair Defenses", "Defense Evasion", "Disabling logging"),
    ],
    'IA': [  # Identification and Authentication
        MITREAttackTechnique("T1110", "Brute Force", "Credential Access", "Password attacks"),
        MITREAttackTechnique("T1556", "Modify Authentication", "Credential Access", "Auth process tampering"),
        MITREAttackTechnique("T1621", "Multi-Factor Auth Request Generation", "Credential Access", "MFA fatigue"),
    ],
    'SC': [  # System and Communications Protection
        MITREAttackTechnique("T1040", "Network Sniffing", "Credential Access", "Capturing network traffic"),
        MITREAttackTechnique("T1557", "Adversary-in-the-Middle", "Collection", "MITM attacks"),
        MITREAttackTechnique("T1573", "Encrypted Channel", "Command and Control", "C2 communications"),
    ],
    'SI': [  # System and Information Integrity
        MITREAttackTechnique("T1059", "Command and Scripting", "Execution", "Script execution"),
        MITREAttackTechnique("T1203", "Exploitation for Client Execution", "Execution", "Exploiting vulnerabilities"),
        MITREAttackTechnique("T1195", "Supply Chain Compromise", "Initial Access", "Compromised supply chain"),
    ],
    'CM': [  # Configuration Management
        MITREAttackTechnique("T1574", "Hijack Execution Flow", "Persistence", "DLL hijacking"),
        MITREAttackTechnique("T1543", "Create or Modify System Process", "Persistence", "Service manipulation"),
    ],
    'IR': [  # Incident Response
        MITREAttackTechnique("T1485", "Data Destruction", "Impact", "Destroying data"),
        MITREAttackTechnique("T1486", "Data Encrypted for Impact", "Impact", "Ransomware"),
    ],
    'CP': [  # Contingency Planning
        MITREAttackTechnique("T1490", "Inhibit System Recovery", "Impact", "Deleting backups"),
        MITREAttackTechnique("T1489", "Service Stop", "Impact", "Stopping services"),
    ],
    'MP': [  # Media Protection
        MITREAttackTechnique("T1052", "Exfiltration Over Physical Medium", "Exfiltration", "USB exfiltration"),
        MITREAttackTechnique("T1200", "Hardware Additions", "Initial Access", "Rogue hardware"),
    ],
    'SR': [  # Supply Chain Risk Management
        MITREAttackTechnique("T1195", "Supply Chain Compromise", "Initial Access", "Compromised dependencies"),
        MITREAttackTechnique("T1199", "Trusted Relationship", "Initial Access", "Third-party compromise"),
    ],
}


@dataclass
class ThreatEvent:
    """
    Represents a threat event scenario per NIST 800-30.
    """
    event_id: str
    name: str
    description: str
    threat_sources: List[str]  # References to ThreatSource IDs
    mitre_techniques: List[MITREAttackTechnique] = field(default_factory=list)
    relevance: float = 1.0  # 0-1 relevance to organization
    
    @property
    def primary_tactic(self) -> str:
        """Get the primary MITRE ATT&CK tactic."""
        if self.mitre_techniques:
            return self.mitre_techniques[0].tactic
        return "Unknown"


# =============================================================================
# NIST 800-30 SECTION 2.3: MULTI-DIMENSIONAL IMPACT ASSESSMENT
# =============================================================================

class ImpactLevel(Enum):
    """Impact level (1-5 scale) per NIST 800-30."""
    NEGLIGIBLE = 1
    MINOR = 2
    MODERATE = 3
    SIGNIFICANT = 4
    SEVERE = 5


@dataclass
class MultiDimensionalImpact:
    """
    Multi-dimensional impact assessment per NIST 800-30.
    Assesses impact across Confidentiality, Integrity, Availability,
    plus organizational factors (Financial, Mission, Reputation).
    """
    # CIA Triad
    confidentiality: ImpactLevel = ImpactLevel.MODERATE
    integrity: ImpactLevel = ImpactLevel.MODERATE
    availability: ImpactLevel = ImpactLevel.MODERATE
    
    # Organizational Impact
    financial_impact: float = 0.0  # Estimated dollar impact
    mission_impact: ImpactLevel = ImpactLevel.MODERATE
    reputation_impact: ImpactLevel = ImpactLevel.MODERATE
    
    # Weights for composite calculation
    WEIGHTS = {
        'confidentiality': 0.25,
        'integrity': 0.20,
        'availability': 0.20,
        'mission': 0.20,
        'reputation': 0.15,
    }
    
    @property
    def composite_impact_score(self) -> float:
        """Calculate weighted composite impact score (1-5 scale)."""
        return (
            self.confidentiality.value * self.WEIGHTS['confidentiality'] +
            self.integrity.value * self.WEIGHTS['integrity'] +
            self.availability.value * self.WEIGHTS['availability'] +
            self.mission_impact.value * self.WEIGHTS['mission'] +
            self.reputation_impact.value * self.WEIGHTS['reputation']
        )
    
    @property
    def max_impact(self) -> ImpactLevel:
        """Get the highest impact level across all dimensions."""
        max_val = max(
            self.confidentiality.value,
            self.integrity.value,
            self.availability.value,
            self.mission_impact.value,
            self.reputation_impact.value
        )
        return ImpactLevel(max_val)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting."""
        return {
            'confidentiality': self.confidentiality.name,
            'integrity': self.integrity.name,
            'availability': self.availability.name,
            'financial_impact': self.financial_impact,
            'mission_impact': self.mission_impact.name,
            'reputation_impact': self.reputation_impact.name,
            'composite_score': round(self.composite_impact_score, 2),
        }


# =============================================================================
# NIST 800-30 SECTION 2.2: ENHANCED LIKELIHOOD DETERMINATION
# =============================================================================

class Likelihood(Enum):
    """Likelihood of threat exploitation (1-5 scale)."""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


@dataclass
class EnhancedLikelihood:
    """
    Enhanced likelihood calculation per NIST 800-30.
    Considers threat capability, intent, vulnerability severity,
    and predisposing conditions.
    """
    threat_capability: ThreatCapability = ThreatCapability.MODERATE
    threat_intent: ThreatIntent = ThreatIntent.MODERATE
    vulnerability_severity: float = 5.0  # CVSS-style 0-10 scale
    predisposing_conditions: float = 0.5  # 0-1 scale (exposure factors)
    
    @property
    def calculated_likelihood(self) -> Likelihood:
        """
        Calculate likelihood using NIST 800-30 semi-quantitative approach.
        
        Formula: Likelihood = f(Capability, Intent, Vulnerability, Conditions)
        """
        # Normalize inputs to 0-1 scale
        cap_norm = self.threat_capability.value / 5.0
        intent_norm = self.threat_intent.value / 5.0
        vuln_norm = self.vulnerability_severity / 10.0
        
        # Weighted calculation
        raw_score = (
            cap_norm * 0.25 +           # Threat capability
            intent_norm * 0.25 +         # Threat intent
            vuln_norm * 0.30 +           # Vulnerability severity
            self.predisposing_conditions * 0.20  # Environmental factors
        )
        
        # Convert to 1-5 scale
        likelihood_value = math.ceil(raw_score * 5)
        likelihood_value = max(1, min(5, likelihood_value))
        
        return Likelihood(likelihood_value)
    
    @property
    def confidence_level(self) -> str:
        """Return confidence level in the likelihood assessment."""
        # Higher confidence when inputs are at extremes
        variance = abs(self.threat_capability.value - 3) + abs(self.threat_intent.value - 3)
        if variance >= 3:
            return "HIGH"
        elif variance >= 1:
            return "MODERATE"
        else:
            return "LOW"


# =============================================================================
# NIST 800-30 QUANTITATIVE ANALYSIS: ALE CALCULATOR
# =============================================================================

@dataclass
class QuantitativeRiskMetrics:
    """
    Quantitative risk metrics including ALE (Annualized Loss Expectancy).
    Based on NIST 800-30 and FAIR methodology.
    """
    asset_value: float = 0.0          # Dollar value of asset at risk
    exposure_factor: float = 0.5       # 0-1, percentage of asset loss
    annual_rate_of_occurrence: float = 0.1  # Expected incidents per year
    
    # Cost factors
    response_cost: float = 0.0        # Incident response costs
    recovery_cost: float = 0.0        # Recovery and remediation costs
    regulatory_cost: float = 0.0      # Fines, penalties, legal costs
    reputation_cost: float = 0.0      # Brand/customer impact costs
    
    @property
    def single_loss_expectancy(self) -> float:
        """Calculate SLE (Single Loss Expectancy)."""
        base_sle = self.asset_value * self.exposure_factor
        total_sle = base_sle + self.response_cost + self.recovery_cost + \
                   self.regulatory_cost + self.reputation_cost
        return total_sle
    
    @property
    def annualized_loss_expectancy(self) -> float:
        """Calculate ALE (Annualized Loss Expectancy)."""
        return self.single_loss_expectancy * self.annual_rate_of_occurrence
    
    @property
    def risk_reduction_value(self) -> float:
        """Estimate value of risk reduction (for ROI calculations)."""
        # Assuming 70% risk reduction with proper controls
        return self.annualized_loss_expectancy * 0.70
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting."""
        return {
            'asset_value': self.asset_value,
            'exposure_factor': self.exposure_factor,
            'annual_rate_occurrence': self.annual_rate_of_occurrence,
            'single_loss_expectancy': round(self.single_loss_expectancy, 2),
            'annualized_loss_expectancy': round(self.annualized_loss_expectancy, 2),
            'risk_reduction_value': round(self.risk_reduction_value, 2),
        }


# =============================================================================
# CORE RISK LEVELS AND LEGACY COMPATIBILITY
# =============================================================================

class RiskLevel(Enum):
    """Overall risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Legacy Impact enum for backward compatibility
Impact = ImpactLevel


# =============================================================================
# ENHANCED FINDING WITH NIST 800-30 ATTRIBUTES
# =============================================================================

@dataclass
class EnhancedFinding:
    """
    Enhanced security finding with full NIST 800-30 attributes.
    """
    finding_id: str
    title: str
    description: str
    control_family: str
    control_id: str
    
    # Legacy fields (backward compatible)
    likelihood: Likelihood = Likelihood.MEDIUM
    impact: Impact = Impact.MODERATE
    assets_affected: List[str] = field(default_factory=list)
    remediation: str = ""
    status: str = "OPEN"
    
    # NIST 800-30 Enhanced fields
    threat_sources: List[str] = field(default_factory=list)  # IDs from catalog
    threat_events: List[ThreatEvent] = field(default_factory=list)
    mitre_techniques: List[MITREAttackTechnique] = field(default_factory=list)
    multi_dimensional_impact: Optional[MultiDimensionalImpact] = None
    enhanced_likelihood: Optional[EnhancedLikelihood] = None
    quantitative_metrics: Optional[QuantitativeRiskMetrics] = None
    
    # Confidence and uncertainty
    confidence_level: str = "MODERATE"  # LOW, MODERATE, HIGH
    uncertainty_range: Tuple[float, float] = (0.8, 1.2)  # Min/max multiplier
    
    @property
    def risk_score(self) -> float:
        """Calculate risk score (1-25 scale) - legacy method."""
        return self.likelihood.value * self.impact.value
    
    @property
    def enhanced_risk_score(self) -> float:
        """Calculate enhanced risk score using NIST 800-30 methodology."""
        if self.enhanced_likelihood and self.multi_dimensional_impact:
            likelihood_val = self.enhanced_likelihood.calculated_likelihood.value
            impact_val = self.multi_dimensional_impact.composite_impact_score
            return likelihood_val * impact_val
        return self.risk_score
    
    @property
    def risk_score_range(self) -> Tuple[float, float]:
        """Get risk score range based on uncertainty."""
        base = self.enhanced_risk_score
        return (base * self.uncertainty_range[0], base * self.uncertainty_range[1])
    
    @property
    def risk_level(self) -> RiskLevel:
        """Determine risk level based on enhanced score."""
        score = self.enhanced_risk_score
        if score <= 4:
            return RiskLevel.LOW
        elif score <= 9:
            return RiskLevel.MEDIUM
        elif score <= 16:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    @property
    def ale(self) -> float:
        """Get Annualized Loss Expectancy if available."""
        if self.quantitative_metrics:
            return self.quantitative_metrics.annualized_loss_expectancy
        return 0.0
    
    def get_mitre_techniques(self) -> List[MITREAttackTechnique]:
        """Get MITRE ATT&CK techniques for this finding."""
        if self.mitre_techniques:
            return self.mitre_techniques
        # Fall back to control family mapping
        return MITRE_ATTACK_MAPPING.get(self.control_family, [])


# Alias for backward compatibility
Finding = EnhancedFinding


# =============================================================================
# ENHANCED RISK ASSESSMENT
# =============================================================================

@dataclass
class EnhancedRiskAssessment:
    """
    Complete NIST 800-30 risk assessment with aggregation and analysis.
    """
    assessment_id: str
    assessment_name: str
    organization: str
    assessor: str
    date: datetime
    findings: List[EnhancedFinding] = field(default_factory=list)
    
    # Threat landscape
    threat_sources: Dict[str, ThreatSource] = field(default_factory=dict)
    
    # Assessment metadata
    scope: str = ""
    methodology: str = "NIST SP 800-30 Rev 1"
    confidence_level: str = "MODERATE"
    
    def add_finding(self, finding: EnhancedFinding):
        """Add a finding to the assessment."""
        self.findings.append(finding)
    
    def add_threat_source(self, source: ThreatSource):
        """Add a threat source to the assessment."""
        self.threat_sources[source.source_id] = source
    
    @property
    def total_findings(self) -> int:
        return len(self.findings)
    
    @property
    def open_findings(self) -> int:
        return len([f for f in self.findings if f.status == "OPEN"])
    
    @property
    def average_risk_score(self) -> float:
        """Calculate average enhanced risk score."""
        if not self.findings:
            return 0.0
        return sum(f.enhanced_risk_score for f in self.findings) / len(self.findings)
    
    @property
    def max_risk_score(self) -> float:
        """Get the highest risk score."""
        if not self.findings:
            return 0.0
        return max(f.enhanced_risk_score for f in self.findings)
    
    @property
    def total_ale(self) -> float:
        """Calculate total Annualized Loss Expectancy."""
        return sum(f.ale for f in self.findings)
    
    @property
    def overall_risk_level(self) -> RiskLevel:
        """Determine overall risk level using aggregation."""
        if not self.findings:
            return RiskLevel.LOW
        
        critical_count = len([f for f in self.findings if f.risk_level == RiskLevel.CRITICAL])
        high_count = len([f for f in self.findings if f.risk_level == RiskLevel.HIGH])
        
        if critical_count > 0:
            return RiskLevel.CRITICAL if critical_count >= 2 else RiskLevel.HIGH
        if high_count >= 3:
            return RiskLevel.CRITICAL
        elif high_count >= 1:
            return RiskLevel.HIGH
        
        avg_score = self.average_risk_score
        if avg_score <= 4:
            return RiskLevel.LOW
        elif avg_score <= 9:
            return RiskLevel.MEDIUM
        elif avg_score <= 16:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    @property
    def risk_score_percentage(self) -> float:
        """Convert risk score to percentage (0-100)."""
        return (self.average_risk_score / 25) * 100
    
    @property
    def compliance_score(self) -> float:
        """Calculate compliance score (inverse of risk)."""
        return 100 - self.risk_score_percentage
    
    def get_threat_landscape_summary(self) -> Dict:
        """Generate threat landscape summary."""
        if not self.threat_sources:
            # Use default catalog if no specific sources
            self.threat_sources = THREAT_SOURCE_CATALOG.copy()
        
        landscape = {
            'adversarial': [],
            'accidental': [],
            'structural': [],
            'environmental': [],
        }
        
        for source in self.threat_sources.values():
            category = source.source_type.value.lower()
            if category in landscape:
                landscape[category].append({
                    'name': source.name,
                    'threat_score': source.threat_score,
                    'effective_threat': source.effective_threat,
                })
        
        return landscape
    
    def get_impact_breakdown(self) -> Dict:
        """Aggregate impact across all findings."""
        if not self.findings:
            return {}
        
        c_impacts = [f.multi_dimensional_impact.confidentiality.value 
                    for f in self.findings if f.multi_dimensional_impact]
        i_impacts = [f.multi_dimensional_impact.integrity.value 
                    for f in self.findings if f.multi_dimensional_impact]
        a_impacts = [f.multi_dimensional_impact.availability.value 
                    for f in self.findings if f.multi_dimensional_impact]
        
        return {
            'confidentiality_avg': sum(c_impacts) / len(c_impacts) if c_impacts else 0,
            'integrity_avg': sum(i_impacts) / len(i_impacts) if i_impacts else 0,
            'availability_avg': sum(a_impacts) / len(a_impacts) if a_impacts else 0,
            'total_financial_impact': sum(f.multi_dimensional_impact.financial_impact 
                                         for f in self.findings if f.multi_dimensional_impact),
        }
    
    def get_mitre_attack_coverage(self) -> Dict[str, List[str]]:
        """Get MITRE ATT&CK technique coverage from all findings."""
        coverage = {}
        for finding in self.findings:
            for technique in finding.get_mitre_techniques():
                tactic = technique.tactic
                if tactic not in coverage:
                    coverage[tactic] = []
                if technique.technique_id not in coverage[tactic]:
                    coverage[tactic].append(technique.technique_id)
        return coverage


# Alias for backward compatibility
RiskAssessment = EnhancedRiskAssessment


# =============================================================================
# ENHANCED RISK SCORE CALCULATOR
# =============================================================================

class RiskScoreCalculator:
    """
    NIST 800-30 Enhanced Risk Score Calculator.
    """
    
    # Risk matrix for visual representation
    RISK_MATRIX = {
        (Likelihood.VERY_HIGH, Impact.SEVERE): (25, RiskLevel.CRITICAL),
        (Likelihood.VERY_HIGH, Impact.SIGNIFICANT): (20, RiskLevel.CRITICAL),
        (Likelihood.VERY_HIGH, Impact.MODERATE): (15, RiskLevel.HIGH),
        (Likelihood.VERY_HIGH, Impact.MINOR): (10, RiskLevel.MEDIUM),
        (Likelihood.VERY_HIGH, Impact.NEGLIGIBLE): (5, RiskLevel.LOW),
        
        (Likelihood.HIGH, Impact.SEVERE): (20, RiskLevel.CRITICAL),
        (Likelihood.HIGH, Impact.SIGNIFICANT): (16, RiskLevel.HIGH),
        (Likelihood.HIGH, Impact.MODERATE): (12, RiskLevel.HIGH),
        (Likelihood.HIGH, Impact.MINOR): (8, RiskLevel.MEDIUM),
        (Likelihood.HIGH, Impact.NEGLIGIBLE): (4, RiskLevel.LOW),
        
        (Likelihood.MEDIUM, Impact.SEVERE): (15, RiskLevel.HIGH),
        (Likelihood.MEDIUM, Impact.SIGNIFICANT): (12, RiskLevel.HIGH),
        (Likelihood.MEDIUM, Impact.MODERATE): (9, RiskLevel.MEDIUM),
        (Likelihood.MEDIUM, Impact.MINOR): (6, RiskLevel.MEDIUM),
        (Likelihood.MEDIUM, Impact.NEGLIGIBLE): (3, RiskLevel.LOW),
        
        (Likelihood.LOW, Impact.SEVERE): (10, RiskLevel.MEDIUM),
        (Likelihood.LOW, Impact.SIGNIFICANT): (8, RiskLevel.MEDIUM),
        (Likelihood.LOW, Impact.MODERATE): (6, RiskLevel.MEDIUM),
        (Likelihood.LOW, Impact.MINOR): (4, RiskLevel.LOW),
        (Likelihood.LOW, Impact.NEGLIGIBLE): (2, RiskLevel.LOW),
        
        (Likelihood.VERY_LOW, Impact.SEVERE): (5, RiskLevel.LOW),
        (Likelihood.VERY_LOW, Impact.SIGNIFICANT): (4, RiskLevel.LOW),
        (Likelihood.VERY_LOW, Impact.MODERATE): (3, RiskLevel.LOW),
        (Likelihood.VERY_LOW, Impact.MINOR): (2, RiskLevel.LOW),
        (Likelihood.VERY_LOW, Impact.NEGLIGIBLE): (1, RiskLevel.LOW),
    }
    
    # Control family risk weights
    CONTROL_WEIGHTS = {
        'AC': 1.2,   # Access Control
        'AU': 1.0,   # Audit & Accountability
        'AT': 0.8,   # Awareness & Training
        'CA': 1.0,   # Assessment & Authorization
        'CM': 1.1,   # Configuration Management
        'CP': 1.0,   # Contingency Planning
        'IA': 1.3,   # Identification & Authentication
        'IR': 1.1,   # Incident Response
        'MA': 0.9,   # Maintenance
        'MP': 1.0,   # Media Protection
        'PE': 0.9,   # Physical & Environmental
        'PL': 0.8,   # Planning
        'PM': 0.8,   # Program Management
        'PS': 0.9,   # Personnel Security
        'PT': 0.8,   # PII Processing
        'RA': 1.0,   # Risk Assessment
        'SA': 1.1,   # System Acquisition
        'SC': 1.2,   # System & Communications Protection
        'SI': 1.1,   # System Integrity
        'SR': 1.0,   # Supply Chain
    }
    
    # Default asset values by control family (for ALE estimation)
    DEFAULT_ASSET_VALUES = {
        'AC': 500000,   # Access control failures can expose all data
        'AU': 100000,   # Audit failures enable undetected breaches
        'IA': 750000,   # Authentication failures are critical
        'SC': 400000,   # Communications protection
        'SI': 300000,   # System integrity
        'CM': 200000,   # Configuration issues
        'IR': 150000,   # Incident response capability
        'CP': 250000,   # Continuity planning
        'MP': 100000,   # Media protection
        'SR': 350000,   # Supply chain risks
    }
    
    # Annual rate of occurrence by control family
    DEFAULT_ARO = {
        'AC': 0.15,    # 15% chance per year
        'AU': 0.20,
        'IA': 0.12,
        'SC': 0.10,
        'SI': 0.18,
        'CM': 0.25,
        'IR': 0.08,
        'CP': 0.05,
        'MP': 0.10,
        'SR': 0.07,
    }
    
    def __init__(self):
        self.assessments: List[EnhancedRiskAssessment] = []
    
    def calculate_weighted_risk(self, finding: EnhancedFinding) -> float:
        """Calculate risk score with control family weighting."""
        base_score = finding.enhanced_risk_score
        weight = self.CONTROL_WEIGHTS.get(finding.control_family, 1.0)
        return base_score * weight
    
    def estimate_quantitative_metrics(self, finding: EnhancedFinding) -> QuantitativeRiskMetrics:
        """Estimate quantitative risk metrics for a finding."""
        family = finding.control_family
        
        # Get default values or estimate
        asset_value = self.DEFAULT_ASSET_VALUES.get(family, 200000)
        aro = self.DEFAULT_ARO.get(family, 0.10)
        
        # Adjust based on risk level
        if finding.risk_level == RiskLevel.CRITICAL:
            exposure_factor = 0.8
            aro *= 1.5
        elif finding.risk_level == RiskLevel.HIGH:
            exposure_factor = 0.5
            aro *= 1.2
        elif finding.risk_level == RiskLevel.MEDIUM:
            exposure_factor = 0.3
        else:
            exposure_factor = 0.1
            aro *= 0.5
        
        return QuantitativeRiskMetrics(
            asset_value=asset_value,
            exposure_factor=exposure_factor,
            annual_rate_of_occurrence=aro,
            response_cost=asset_value * 0.05,
            recovery_cost=asset_value * 0.10,
            regulatory_cost=asset_value * 0.02 if family in ['IA', 'AC', 'SC'] else 0,
            reputation_cost=asset_value * 0.03,
        )
    
    def create_enhanced_finding(
        self,
        control_id: str,
        control_name: str,
        family: str,
        status: str,
        findings_list: List[str],
        recommendations: List[str]
    ) -> Optional[EnhancedFinding]:
        """Create an enhanced finding with full NIST 800-30 attributes."""
        
        if status == "PASS":
            return None
        
        # Determine base likelihood
        likelihood_map = {
            'AC': Likelihood.HIGH,
            'AU': Likelihood.MEDIUM,
            'IA': Likelihood.HIGH,
            'SC': Likelihood.HIGH,
            'SI': Likelihood.MEDIUM,
            'CM': Likelihood.MEDIUM,
            'IR': Likelihood.LOW,
            'CP': Likelihood.LOW,
            'RA': Likelihood.MEDIUM,
            'SA': Likelihood.LOW,
            'CA': Likelihood.LOW,
            'MP': Likelihood.MEDIUM,
            'SR': Likelihood.MEDIUM,
        }
        
        impact_map = {
            'FAIL': Impact.SIGNIFICANT,
            'WARNING': Impact.MODERATE,
            'ERROR': Impact.SEVERE,
        }
        
        base_likelihood = likelihood_map.get(family, Likelihood.MEDIUM)
        base_impact = impact_map.get(status, Impact.MODERATE)
        
        # Create enhanced likelihood
        enhanced_likelihood = EnhancedLikelihood(
            threat_capability=ThreatCapability(min(base_likelihood.value + 1, 5)),
            threat_intent=ThreatIntent(base_likelihood.value),
            vulnerability_severity=base_impact.value * 2,  # Convert to 0-10 scale
            predisposing_conditions=0.5 if status == "FAIL" else 0.3,
        )
        
        # Create multi-dimensional impact
        multi_impact = MultiDimensionalImpact(
            confidentiality=base_impact if family in ['AC', 'IA', 'SC', 'MP'] else Impact.MODERATE,
            integrity=base_impact if family in ['SI', 'CM', 'AU'] else Impact.MODERATE,
            availability=base_impact if family in ['CP', 'IR', 'SC'] else Impact.MODERATE,
            financial_impact=self.DEFAULT_ASSET_VALUES.get(family, 100000) * 0.1,
            mission_impact=base_impact if family in ['AC', 'IA', 'CP'] else Impact.MODERATE,
            reputation_impact=Impact(max(1, base_impact.value - 1)),
        )
        
        # Get MITRE ATT&CK techniques
        mitre_techniques = MITRE_ATTACK_MAPPING.get(family, [])
        
        # Determine threat sources
        threat_sources = ['ORGANIZED_CRIME', 'INSIDER_NEGLIGENT']
        if family in ['AC', 'IA']:
            threat_sources.append('NATION_STATE')
        if family in ['SR']:
            threat_sources.append('COMPETITOR')
        
        finding = EnhancedFinding(
            finding_id=f"FIND-{control_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=f"{control_id}: {control_name}",
            description="; ".join(findings_list) if findings_list else f"Issue with {control_name}",
            control_family=family,
            control_id=control_id,
            likelihood=base_likelihood,
            impact=base_impact,
            remediation="; ".join(recommendations) if recommendations else "",
            status="OPEN",
            threat_sources=threat_sources,
            mitre_techniques=mitre_techniques,
            multi_dimensional_impact=multi_impact,
            enhanced_likelihood=enhanced_likelihood,
            confidence_level=enhanced_likelihood.confidence_level,
        )
        
        # Add quantitative metrics
        finding.quantitative_metrics = self.estimate_quantitative_metrics(finding)
        
        return finding
    
    # Backward compatible method
    def create_finding_from_nist_result(
        self,
        control_id: str,
        control_name: str,
        family: str,
        status: str,
        findings_list: List[str],
        recommendations: List[str]
    ) -> Optional[EnhancedFinding]:
        """Backward compatible alias for create_enhanced_finding."""
        return self.create_enhanced_finding(
            control_id, control_name, family, status, findings_list, recommendations
        )
    
    def load_nist_assessment(self, json_file: Path) -> EnhancedRiskAssessment:
        """Load a NIST assessment JSON file and convert to enhanced risk assessment."""
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        assessment = EnhancedRiskAssessment(
            assessment_id=f"RA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            assessment_name=data.get('assessment_info', {}).get('scope', 'NIST 800-53 Assessment'),
            organization=data.get('assessment_info', {}).get('account_id', 'Unknown'),
            assessor="Security Architecture and Evaluation",
            date=datetime.now(),
            threat_sources=THREAT_SOURCE_CATALOG.copy(),
        )
        
        for result in data.get('results', []):
            status = result.get('status', 'PASS')
            if status != 'PASS':
                finding = self.create_enhanced_finding(
                    control_id=result.get('control_id', 'Unknown'),
                    control_name=result.get('control_name', 'Unknown'),
                    family=result.get('family', 'Unknown'),
                    status=status,
                    findings_list=result.get('findings', []),
                    recommendations=result.get('recommendations', [])
                )
                if finding:
                    assessment.add_finding(finding)
        
        self.assessments.append(assessment)
        return assessment
    
    def generate_nist_800_30_report(self, assessment: EnhancedRiskAssessment) -> str:
        """Generate a comprehensive NIST 800-30 risk report."""
        
        # Count findings by risk level
        risk_counts = {level: 0 for level in RiskLevel}
        for finding in assessment.findings:
            risk_counts[finding.risk_level] += 1
        
        # Count findings by control family
        family_counts = {}
        family_ale = {}
        for finding in assessment.findings:
            family = finding.control_family
            if family not in family_counts:
                family_counts[family] = {'count': 0, 'total_risk': 0}
                family_ale[family] = 0
            family_counts[family]['count'] += 1
            family_counts[family]['total_risk'] += finding.enhanced_risk_score
            family_ale[family] += finding.ale
        
        report = f"""
{'='*80}
             NIST SP 800-30 REV 1 ENHANCED RISK ASSESSMENT REPORT
{'='*80}

Assessment ID:      {assessment.assessment_id}
Assessment Name:    {assessment.assessment_name}
Organization:       {assessment.organization}
Assessor:           {assessment.assessor}
Date:               {assessment.date.strftime('%Y-%m-%d %H:%M:%S')}
Methodology:        {assessment.methodology}
Confidence Level:   {assessment.confidence_level}

{'='*80}
                           EXECUTIVE SUMMARY
{'='*80}

Overall Risk Level:      {assessment.overall_risk_level.value}
Average Risk Score:      {assessment.average_risk_score:.2f} / 25
Maximum Risk Score:      {assessment.max_risk_score:.0f} / 25
Risk Score Percentage:   {assessment.risk_score_percentage:.1f}%
Compliance Score:        {assessment.compliance_score:.1f}%

Total Findings:          {assessment.total_findings}
Open Findings:           {assessment.open_findings}

{'='*80}
                    QUANTITATIVE RISK ANALYSIS (ALE)
{'='*80}

Total Annualized Loss Expectancy (ALE): ${assessment.total_ale:,.2f}

ALE by Control Family:
{'-'*60}
{'Family':<10} {'Findings':<12} {'Total ALE':<20} {'Risk Level':<15}
{'-'*60}
"""
        
        for family, data in sorted(family_ale.items(), key=lambda x: x[1], reverse=True):
            avg_risk = family_counts[family]['total_risk'] / family_counts[family]['count'] if family_counts[family]['count'] > 0 else 0
            level = "CRITICAL" if avg_risk > 16 else "HIGH" if avg_risk > 9 else "MEDIUM" if avg_risk > 4 else "LOW"
            report += f"{family:<10} {family_counts[family]['count']:<12} ${data:>15,.2f} {level:<15}\n"
        
        report += f"""
{'='*80}
                       THREAT LANDSCAPE ANALYSIS
                    (NIST 800-30 Section 2.1.1)
{'='*80}

Threat Sources Considered:
{'-'*60}
"""
        
        for source_id, source in assessment.threat_sources.items():
            report += f"""
  {source.name} ({source.source_type.value})
    - Capability:  {source.capability.name} ({source.capability.value}/5)
    - Intent:      {source.intent.name} ({source.intent.value}/5)
    - Threat Score: {source.threat_score}/25
    - Targeting Likelihood: {source.targeting_likelihood:.0%}
    - Effective Threat: {source.effective_threat:.1f}
"""
        
        report += f"""
{'='*80}
                       RISK DISTRIBUTION
{'='*80}

{'Risk Level':<15} {'Count':<10} {'Percentage':<15} {'Visual':<30}
{'-'*70}
"""
        
        for level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
            count = risk_counts[level]
            pct = (count / assessment.total_findings * 100) if assessment.total_findings > 0 else 0
            bar = '█' * int(pct / 3)
            report += f"{level.value:<15} {count:<10} {pct:>5.1f}%         {bar}\n"
        
        report += f"""
{'='*80}
                    MULTI-DIMENSIONAL IMPACT ANALYSIS
                       (NIST 800-30 Section 2.3)
{'='*80}

Impact Category         Average Score    Risk Level
{'-'*60}
"""
        
        impact_breakdown = assessment.get_impact_breakdown()
        if impact_breakdown:
            c_level = "HIGH" if impact_breakdown.get('confidentiality_avg', 0) > 3.5 else "MEDIUM" if impact_breakdown.get('confidentiality_avg', 0) > 2.5 else "LOW"
            i_level = "HIGH" if impact_breakdown.get('integrity_avg', 0) > 3.5 else "MEDIUM" if impact_breakdown.get('integrity_avg', 0) > 2.5 else "LOW"
            a_level = "HIGH" if impact_breakdown.get('availability_avg', 0) > 3.5 else "MEDIUM" if impact_breakdown.get('availability_avg', 0) > 2.5 else "LOW"
            
            report += f"Confidentiality         {impact_breakdown.get('confidentiality_avg', 0):.2f}/5          {c_level}\n"
            report += f"Integrity               {impact_breakdown.get('integrity_avg', 0):.2f}/5          {i_level}\n"
            report += f"Availability            {impact_breakdown.get('availability_avg', 0):.2f}/5          {a_level}\n"
            report += f"\nTotal Financial Impact: ${impact_breakdown.get('total_financial_impact', 0):,.2f}\n"
        
        report += f"""
{'='*80}
                      MITRE ATT&CK COVERAGE
                   (Threat Event Identification)
{'='*80}

"""
        mitre_coverage = assessment.get_mitre_attack_coverage()
        for tactic, techniques in mitre_coverage.items():
            report += f"\n{tactic}:\n"
            for tech in techniques:
                report += f"  • {tech}\n"
        
        report += f"""
{'='*80}
                        DETAILED FINDINGS
{'='*80}
"""
        
        sorted_findings = sorted(assessment.findings, key=lambda f: f.enhanced_risk_score, reverse=True)
        
        for i, finding in enumerate(sorted_findings, 1):
            risk_indicator = "🔴" if finding.risk_level == RiskLevel.CRITICAL else \
                           "🟠" if finding.risk_level == RiskLevel.HIGH else \
                           "🟡" if finding.risk_level == RiskLevel.MEDIUM else "🟢"
            
            report += f"""
{i}. {risk_indicator} {finding.title}
   Finding ID:      {finding.finding_id}
   Control Family:  {finding.control_family}
   
   RISK SCORES:
   - Base Score:      {finding.risk_score:.0f}/25 ({finding.likelihood.name} × {finding.impact.name})
   - Enhanced Score:  {finding.enhanced_risk_score:.2f}/25
   - Risk Level:      {finding.risk_level.value}
   - Confidence:      {finding.confidence_level}
   
   IMPACT ANALYSIS (C/I/A):
"""
            if finding.multi_dimensional_impact:
                mi = finding.multi_dimensional_impact
                report += f"""   - Confidentiality: {mi.confidentiality.name}
   - Integrity:       {mi.integrity.name}
   - Availability:    {mi.availability.name}
   - Financial:       ${mi.financial_impact:,.2f}
"""
            
            report += f"""
   QUANTITATIVE METRICS:
"""
            if finding.quantitative_metrics:
                qm = finding.quantitative_metrics
                report += f"""   - Single Loss Expectancy (SLE): ${qm.single_loss_expectancy:,.2f}
   - Annual Rate of Occurrence:    {qm.annual_rate_of_occurrence:.2%}
   - Annualized Loss Expectancy:   ${qm.annualized_loss_expectancy:,.2f}
"""
            
            report += f"""
   THREAT SOURCES: {', '.join(finding.threat_sources)}
   
   MITRE ATT&CK TECHNIQUES:
"""
            for tech in finding.get_mitre_techniques()[:3]:
                report += f"   - {tech.technique_id}: {tech.technique_name} ({tech.tactic})\n"
            
            report += f"""
   Description:
   {finding.description[:300]}{'...' if len(finding.description) > 300 else ''}
   
   Remediation:
   {finding.remediation[:300]}{'...' if len(finding.remediation) > 300 else ''}
   
   {'-'*70}
"""
        
        report += f"""
{'='*80}
                        5x5 RISK MATRIX
                    (NIST 800-30 Table I-2)
{'='*80}

                         I M P A C T
             NEGLIGIBLE  MINOR  MODERATE  SIGNIF.  SEVERE
           +----------+-------+---------+--------+--------+
  V.HIGH   |    5     |  10   |   15    |   20   |   25   | ← CRITICAL
           +----------+-------+---------+--------+--------+
L  HIGH    |    4     |   8   |   12    |   16   |   20   | ← HIGH
I          +----------+-------+---------+--------+--------+
K  MEDIUM  |    3     |   6   |    9    |   12   |   15   | ← MEDIUM
E          +----------+-------+---------+--------+--------+
L  LOW     |    2     |   4   |    6    |    8   |   10   | ← LOW
I          +----------+-------+---------+--------+--------+
H  V.LOW   |    1     |   2   |    3    |    4   |    5   | ← LOW
           +----------+-------+---------+--------+--------+

Risk Levels: LOW (1-4) | MEDIUM (5-9) | HIGH (10-16) | CRITICAL (17-25)

{'='*80}
                    RECOMMENDATIONS SUMMARY
{'='*80}

PRIORITY 1 - CRITICAL & HIGH RISK (Immediate Action Required):
"""
        
        critical_high = [f for f in sorted_findings if f.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]]
        for finding in critical_high[:5]:
            report += f"\n  • {finding.control_id}: {finding.remediation[:150]}..."
            report += f"\n    ALE Impact: ${finding.ale:,.2f}/year\n"
        
        report += f"""
PRIORITY 2 - MEDIUM RISK (Address Within 90 Days):
"""
        medium = [f for f in sorted_findings if f.risk_level == RiskLevel.MEDIUM]
        for finding in medium[:3]:
            report += f"\n  • {finding.control_id}: {finding.remediation[:100]}..."
        
        report += f"""

{'='*80}
                    RISK REDUCTION RECOMMENDATIONS
{'='*80}

Total Current ALE:             ${assessment.total_ale:,.2f}/year
Estimated Post-Remediation:    ${assessment.total_ale * 0.30:,.2f}/year
Projected Annual Savings:      ${assessment.total_ale * 0.70:,.2f}/year

ROI of Security Investments:
- If remediation costs < ${assessment.total_ale * 0.70:,.2f}, investment is justified
- Break-even period: < 1 year with proper implementation

{'='*80}
                       REPORT GENERATED BY
              SAELAR - Security Architecture and Evaluation
                   NIST SP 800-30 Rev 1 Methodology
                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}
"""
        
        return report
    
    # Backward compatible alias
    def generate_risk_report(self, assessment: EnhancedRiskAssessment) -> str:
        """Generate risk report (backward compatible)."""
        return self.generate_nist_800_30_report(assessment)
    
    def export_to_json(self, assessment: EnhancedRiskAssessment, output_file: Path):
        """Export assessment to JSON format with NIST 800-30 data."""
        data = {
            'assessment_id': assessment.assessment_id,
            'assessment_name': assessment.assessment_name,
            'organization': assessment.organization,
            'assessor': assessment.assessor,
            'date': assessment.date.isoformat(),
            'methodology': assessment.methodology,
            'summary': {
                'overall_risk_level': assessment.overall_risk_level.value,
                'average_risk_score': round(assessment.average_risk_score, 2),
                'max_risk_score': assessment.max_risk_score,
                'risk_percentage': round(assessment.risk_score_percentage, 2),
                'compliance_score': round(assessment.compliance_score, 2),
                'total_findings': assessment.total_findings,
                'open_findings': assessment.open_findings,
                'total_ale': round(assessment.total_ale, 2),
            },
            'threat_landscape': assessment.get_threat_landscape_summary(),
            'impact_breakdown': assessment.get_impact_breakdown(),
            'mitre_attack_coverage': assessment.get_mitre_attack_coverage(),
            'findings': [
                {
                    'finding_id': f.finding_id,
                    'title': f.title,
                    'description': f.description,
                    'control_family': f.control_family,
                    'control_id': f.control_id,
                    'likelihood': f.likelihood.name,
                    'impact': f.impact.name,
                    'risk_score': f.risk_score,
                    'enhanced_risk_score': round(f.enhanced_risk_score, 2),
                    'risk_level': f.risk_level.value,
                    'confidence_level': f.confidence_level,
                    'threat_sources': f.threat_sources,
                    'mitre_techniques': [
                        {'id': t.technique_id, 'name': t.technique_name, 'tactic': t.tactic}
                        for t in f.get_mitre_techniques()
                    ],
                    'multi_dimensional_impact': f.multi_dimensional_impact.to_dict() if f.multi_dimensional_impact else None,
                    'quantitative_metrics': f.quantitative_metrics.to_dict() if f.quantitative_metrics else None,
                    'remediation': f.remediation,
                    'status': f.status,
                }
                for f in assessment.findings
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)


def demo_calculation():
    """Demonstrate the enhanced NIST 800-30 risk calculator."""
    
    print("\n" + "="*80)
    print("    NIST SP 800-30 ENHANCED RISK CALCULATOR - DEMONSTRATION")
    print("="*80)
    
    calculator = RiskScoreCalculator()
    
    # Create a sample assessment
    assessment = EnhancedRiskAssessment(
        assessment_id="RA-DEMO-001",
        assessment_name="AWS Security Assessment - NIST 800-30 Enhanced",
        organization="Security Architecture and Evaluation",
        assessor="SAE Security Team",
        date=datetime.now(),
        threat_sources=THREAT_SOURCE_CATALOG.copy(),
        methodology="NIST SP 800-30 Rev 1",
        confidence_level="MODERATE",
    )
    
    # Create enhanced findings
    sample_findings = [
        calculator.create_enhanced_finding(
            control_id="AC-2",
            control_name="Account Management",
            family="AC",
            status="FAIL",
            findings_list=["Root account does not have MFA enabled", "3 dormant accounts found"],
            recommendations=["Enable MFA on root account immediately", "Disable or remove dormant accounts"]
        ),
        calculator.create_enhanced_finding(
            control_id="AU-2",
            control_name="Audit Events",
            family="AU",
            status="WARNING",
            findings_list=["CloudTrail not enabled in all regions"],
            recommendations=["Enable CloudTrail multi-region trail"]
        ),
        calculator.create_enhanced_finding(
            control_id="SC-8",
            control_name="Transmission Confidentiality",
            family="SC",
            status="FAIL",
            findings_list=["Unencrypted S3 buckets detected", "No TLS enforcement on load balancers"],
            recommendations=["Enable default encryption on S3", "Configure HTTPS-only listeners"]
        ),
        calculator.create_enhanced_finding(
            control_id="IA-5",
            control_name="Authenticator Management",
            family="IA",
            status="FAIL",
            findings_list=["Weak password policy", "No credential rotation policy"],
            recommendations=["Implement 14-character minimum password", "Enable credential rotation"]
        ),
        calculator.create_enhanced_finding(
            control_id="CM-2",
            control_name="Baseline Configuration",
            family="CM",
            status="WARNING",
            findings_list=["No documented baseline configurations"],
            recommendations=["Implement AWS Systems Manager State Manager"]
        ),
    ]
    
    for finding in sample_findings:
        if finding:
            assessment.add_finding(finding)
    
    # Generate and print report
    report = calculator.generate_nist_800_30_report(assessment)
    print(report)
    
    # Save to files
    output_dir = Path("C:/Users/iperr/OneDrive/Desktop/NIST_Assessment_Reports/risk_reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save text report
    report_file = output_dir / f"nist_800_30_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n📄 Report saved to: {report_file}")
    
    # Save JSON
    json_file = output_dir / f"nist_800_30_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    calculator.export_to_json(assessment, json_file)
    print(f"📊 JSON saved to: {json_file}")


def main():
    """Main entry point."""
    import sys
    
    print("\n" + "="*70)
    print("   NIST SP 800-30 ENHANCED RISK SCORE CALCULATOR")
    print("   Security Architecture and Evaluation")
    print("="*70)
    
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
        if input_file.exists():
            print(f"\n📂 Loading assessment from: {input_file}")
            calculator = RiskScoreCalculator()
            assessment = calculator.load_nist_assessment(input_file)
            report = calculator.generate_nist_800_30_report(assessment)
            print(report)
        else:
            print(f"❌ File not found: {input_file}")
    else:
        print("\nNo input file provided. Running demonstration...")
        print("Usage: python risk_score_calculator.py <nist_assessment.json>")
        demo_calculation()


if __name__ == "__main__":
    main()
