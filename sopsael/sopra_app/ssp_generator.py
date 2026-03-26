"""
SAELAR System Security Plan (SSP) Generator
============================================
Generates NIST 800-53 compliant System Security Plans from SAELAR assessments.

This module creates comprehensive SSP documents that include:
- System identification and categorization
- Control implementation summaries
- Detailed security implementation statements
- Risk assessment integration
- POA&M (Plan of Action and Milestones)

Usage:
    from ssp_generator import SSPGenerator
    
    ssp = SSPGenerator(
        system_name="My AWS System",
        system_owner="IT Security Team",
        categorization="Moderate"
    )
    ssp.load_assessment_results(results)
    ssp.load_risk_findings(risk_data)
    ssp.generate()
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json


class SystemCategorization(Enum):
    """FIPS 199 Security Categorization Levels."""
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


class ControlStatus(Enum):
    """Control implementation status."""
    IMPLEMENTED = "Implemented"
    PARTIALLY_IMPLEMENTED = "Partially Implemented"
    PLANNED = "Planned"
    NOT_IMPLEMENTED = "Not Implemented"
    NOT_APPLICABLE = "Not Applicable"


@dataclass
class SystemInfo:
    """System identification information for SSP."""
    system_name: str
    system_acronym: str = ""
    system_owner: str = ""
    system_owner_email: str = ""
    authorizing_official: str = ""
    authorizing_official_email: str = ""
    isso_name: str = ""
    isso_email: str = ""
    system_description: str = ""
    authorization_boundary: str = ""
    categorization: SystemCategorization = SystemCategorization.MODERATE
    operational_status: str = "Operational"
    system_type: str = "Cloud (AWS)"
    deployment_model: str = "Infrastructure as a Service (IaaS)"
    
    # Dates
    authorization_date: Optional[datetime] = None
    authorization_expiry: Optional[datetime] = None
    last_assessment_date: Optional[datetime] = None


@dataclass
class ControlImplementation:
    """Individual control implementation details."""
    control_id: str
    control_name: str
    family: str
    status: ControlStatus
    implementation_status: str  # Pass/Fail/Warning from assessment
    responsible_role: str = "System Administrator"
    implementation_statement: str = ""
    evidence: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Risk information
    risk_level: str = ""
    likelihood: str = ""
    impact: str = ""
    risk_score: float = 0.0


@dataclass
class POAMItem:
    """Plan of Action and Milestones item."""
    poam_id: str
    control_id: str
    weakness_description: str
    risk_level: str
    remediation_plan: str
    scheduled_completion: Optional[datetime] = None
    milestone_changes: str = ""
    status: str = "Open"
    resources_required: str = ""
    responsible_party: str = ""


@dataclass 
class SSPDocument:
    """Complete System Security Plan document structure."""
    system_info: SystemInfo
    controls: List[ControlImplementation] = field(default_factory=list)
    poam_items: List[POAMItem] = field(default_factory=list)
    
    # Summary statistics
    total_controls: int = 0
    implemented_count: int = 0
    partial_count: int = 0
    planned_count: int = 0
    not_implemented_count: int = 0
    
    # Risk summary
    total_risk_score: float = 0.0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    
    # Generation metadata
    generated_date: datetime = field(default_factory=datetime.now)
    generated_by: str = "SAELAR SSP Generator"
    version: str = "1.0"


class SSPGenerator:
    """
    System Security Plan Generator.
    
    Generates comprehensive SSP documents from SAELAR assessment results
    and Risk Calculator data.
    """
    
    # NIST 800-53 Control Family mapping
    CONTROL_FAMILIES = {
        'AC': 'Access Control',
        'AU': 'Audit and Accountability',
        'CA': 'Assessment, Authorization, and Monitoring',
        'CM': 'Configuration Management',
        'CP': 'Contingency Planning',
        'IA': 'Identification and Authentication',
        'IR': 'Incident Response',
        'MP': 'Media Protection',
        'RA': 'Risk Assessment',
        'SA': 'System and Services Acquisition',
        'SC': 'System and Communications Protection',
        'SI': 'System and Information Integrity',
        'SR': 'Supply Chain Risk Management'
    }
    
    def __init__(
        self,
        system_name: str,
        system_owner: str = "",
        categorization: str = "Moderate",
        **kwargs
    ):
        """
        Initialize SSP Generator.
        
        Args:
            system_name: Name of the system
            system_owner: System owner name
            categorization: FIPS 199 categorization (Low/Moderate/High)
            **kwargs: Additional SystemInfo fields
        """
        cat_level = SystemCategorization[categorization.upper()]
        
        self.system_info = SystemInfo(
            system_name=system_name,
            system_owner=system_owner,
            categorization=cat_level,
            **kwargs
        )
        
        self.controls: List[ControlImplementation] = []
        self.poam_items: List[POAMItem] = []
        self.risk_findings: List[Dict] = []
        self.assessment_summary: Dict = {}
        
    def load_assessment_results(self, results: List[Any]) -> None:
        """
        Load SAELAR assessment results.
        
        Args:
            results: List of ControlResult objects from NIST assessment
        """
        self.system_info.last_assessment_date = datetime.now()
        
        for result in results:
            # Map assessment status to implementation status
            if hasattr(result, 'status'):
                status_str = str(result.status.value) if hasattr(result.status, 'value') else str(result.status)
                
                if 'PASS' in status_str.upper():
                    impl_status = ControlStatus.IMPLEMENTED
                    assessment_status = "Pass"
                elif 'WARNING' in status_str.upper():
                    impl_status = ControlStatus.PARTIALLY_IMPLEMENTED
                    assessment_status = "Warning"
                elif 'FAIL' in status_str.upper():
                    impl_status = ControlStatus.NOT_IMPLEMENTED
                    assessment_status = "Fail"
                elif 'N/A' in status_str.upper():
                    impl_status = ControlStatus.NOT_APPLICABLE
                    assessment_status = "N/A"
                else:
                    impl_status = ControlStatus.PLANNED
                    assessment_status = "Unknown"
            else:
                impl_status = ControlStatus.PLANNED
                assessment_status = "Unknown"
            
            # Create implementation statement from findings
            findings = getattr(result, 'findings', [])
            recommendations = getattr(result, 'recommendations', [])
            
            impl_statement = self._generate_implementation_statement(
                result.control_id,
                result.control_name,
                assessment_status,
                findings
            )
            
            control = ControlImplementation(
                control_id=result.control_id,
                control_name=result.control_name,
                family=getattr(result, 'family', result.control_id[:2]),
                status=impl_status,
                implementation_status=assessment_status,
                implementation_statement=impl_statement,
                findings=findings if isinstance(findings, list) else [findings],
                recommendations=recommendations if isinstance(recommendations, list) else [recommendations]
            )
            
            self.controls.append(control)
            
            # Create POAM item for failed/warning controls
            if assessment_status in ['Fail', 'Warning']:
                poam = self._create_poam_item(control, findings, recommendations)
                self.poam_items.append(poam)
    
    def load_risk_findings(self, risk_data: Dict) -> None:
        """
        Load Risk Calculator findings.
        
        Args:
            risk_data: Risk assessment data from Risk Calculator
        """
        self.risk_findings = risk_data.get('findings', [])
        
        # Map risk data to controls
        for finding in self.risk_findings:
            control_id = finding.get('control_id', '')
            
            for control in self.controls:
                if control.control_id == control_id:
                    control.risk_level = finding.get('risk_level', '')
                    control.likelihood = finding.get('likelihood', '')
                    control.impact = finding.get('impact', '')
                    control.risk_score = finding.get('risk_score', 0.0)
                    break
    
    def _generate_implementation_statement(
        self,
        control_id: str,
        control_name: str,
        status: str,
        findings: List[str]
    ) -> str:
        """Generate implementation statement for a control."""
        
        if status == "Pass":
            statement = f"The {control_name} ({control_id}) control is fully implemented. "
            if findings:
                statement += f"Assessment confirmed: {'; '.join(findings[:2])}"
            else:
                statement += "Automated assessment verified compliance with control requirements."
        
        elif status == "Warning":
            statement = f"The {control_name} ({control_id}) control is partially implemented. "
            if findings:
                statement += f"Areas requiring attention: {'; '.join(findings[:2])}"
            statement += " Additional implementation work is planned."
        
        elif status == "Fail":
            statement = f"The {control_name} ({control_id}) control is not yet implemented. "
            if findings:
                statement += f"Gaps identified: {'; '.join(findings[:2])}"
            statement += " Remediation is documented in the POA&M."
        
        else:
            statement = f"The {control_name} ({control_id}) control implementation status is under review."
        
        return statement
    
    def _create_poam_item(
        self,
        control: ControlImplementation,
        findings: List[str],
        recommendations: List[str]
    ) -> POAMItem:
        """Create a POA&M item from a control gap."""
        
        poam_id = f"POAM-{control.control_id}-{datetime.now().strftime('%Y%m%d')}"
        
        weakness = "; ".join(findings[:3]) if findings else f"{control.control_name} not fully implemented"
        remediation = "; ".join(recommendations[:3]) if recommendations else "Implement control per NIST 800-53 guidance"
        
        risk_level = "High" if control.implementation_status == "Fail" else "Medium"
        
        return POAMItem(
            poam_id=poam_id,
            control_id=control.control_id,
            weakness_description=weakness,
            risk_level=risk_level,
            remediation_plan=remediation,
            scheduled_completion=datetime.now().replace(month=datetime.now().month + 3) if datetime.now().month <= 9 else datetime.now().replace(year=datetime.now().year + 1, month=(datetime.now().month + 3) % 12),
            responsible_party=self.system_info.isso_name or "Information System Security Officer"
        )
    
    def generate(self) -> SSPDocument:
        """
        Generate the complete SSP document.
        
        Returns:
            SSPDocument with all sections populated
        """
        # Calculate statistics
        total = len(self.controls)
        implemented = sum(1 for c in self.controls if c.status == ControlStatus.IMPLEMENTED)
        partial = sum(1 for c in self.controls if c.status == ControlStatus.PARTIALLY_IMPLEMENTED)
        planned = sum(1 for c in self.controls if c.status == ControlStatus.PLANNED)
        not_impl = sum(1 for c in self.controls if c.status == ControlStatus.NOT_IMPLEMENTED)
        
        # Risk statistics
        total_risk = sum(c.risk_score for c in self.controls)
        high_risk = sum(1 for c in self.controls if c.risk_level == "High")
        med_risk = sum(1 for c in self.controls if c.risk_level == "Medium")
        low_risk = sum(1 for c in self.controls if c.risk_level == "Low")
        
        return SSPDocument(
            system_info=self.system_info,
            controls=self.controls,
            poam_items=self.poam_items,
            total_controls=total,
            implemented_count=implemented,
            partial_count=partial,
            planned_count=planned,
            not_implemented_count=not_impl,
            total_risk_score=total_risk,
            high_risk_count=high_risk,
            medium_risk_count=med_risk,
            low_risk_count=low_risk
        )
    
    def get_family_summary(self) -> Dict[str, Dict]:
        """Get control summary by family."""
        summary = {}
        
        for family_code, family_name in self.CONTROL_FAMILIES.items():
            family_controls = [c for c in self.controls if c.family == family_code]
            
            if family_controls:
                summary[family_code] = {
                    'name': family_name,
                    'total': len(family_controls),
                    'implemented': sum(1 for c in family_controls if c.status == ControlStatus.IMPLEMENTED),
                    'partial': sum(1 for c in family_controls if c.status == ControlStatus.PARTIALLY_IMPLEMENTED),
                    'not_implemented': sum(1 for c in family_controls if c.status == ControlStatus.NOT_IMPLEMENTED),
                    'compliance_pct': round(
                        sum(1 for c in family_controls if c.status == ControlStatus.IMPLEMENTED) / len(family_controls) * 100, 1
                    ) if family_controls else 0
                }
        
        return summary
    
    def get_executive_summary(self) -> Dict:
        """Generate executive summary data."""
        total = len(self.controls)
        implemented = sum(1 for c in self.controls if c.status == ControlStatus.IMPLEMENTED)
        
        compliance_pct = round(implemented / total * 100, 1) if total > 0 else 0
        
        # Determine overall security posture
        if compliance_pct >= 90:
            posture = "Strong"
            posture_description = "The system demonstrates strong security controls with minimal gaps."
        elif compliance_pct >= 70:
            posture = "Satisfactory"
            posture_description = "The system has adequate security controls with some areas for improvement."
        elif compliance_pct >= 50:
            posture = "Needs Improvement"
            posture_description = "The system has notable security gaps requiring attention."
        else:
            posture = "Unsatisfactory"
            posture_description = "The system has significant security deficiencies requiring immediate remediation."
        
        return {
            'system_name': self.system_info.system_name,
            'categorization': self.system_info.categorization.value,
            'assessment_date': self.system_info.last_assessment_date,
            'total_controls': total,
            'implemented': implemented,
            'compliance_percentage': compliance_pct,
            'security_posture': posture,
            'posture_description': posture_description,
            'poam_items': len(self.poam_items),
            'high_risk_findings': sum(1 for c in self.controls if c.risk_level == "High")
        }
    
    def to_dict(self) -> Dict:
        """Export SSP data as dictionary."""
        ssp = self.generate()
        
        return {
            'system_info': {
                'system_name': ssp.system_info.system_name,
                'system_acronym': ssp.system_info.system_acronym,
                'system_owner': ssp.system_info.system_owner,
                'authorizing_official': ssp.system_info.authorizing_official,
                'isso': ssp.system_info.isso_name,
                'categorization': ssp.system_info.categorization.value,
                'system_description': ssp.system_info.system_description,
                'authorization_boundary': ssp.system_info.authorization_boundary
            },
            'summary': self.get_executive_summary(),
            'family_summary': self.get_family_summary(),
            'controls': [
                {
                    'control_id': c.control_id,
                    'control_name': c.control_name,
                    'family': c.family,
                    'status': c.status.value,
                    'implementation_statement': c.implementation_statement,
                    'findings': c.findings,
                    'recommendations': c.recommendations,
                    'risk_level': c.risk_level,
                    'risk_score': c.risk_score
                }
                for c in ssp.controls
            ],
            'poam': [
                {
                    'poam_id': p.poam_id,
                    'control_id': p.control_id,
                    'weakness': p.weakness_description,
                    'risk_level': p.risk_level,
                    'remediation_plan': p.remediation_plan,
                    'scheduled_completion': p.scheduled_completion.isoformat() if p.scheduled_completion else None,
                    'status': p.status
                }
                for p in ssp.poam_items
            ],
            'statistics': {
                'total_controls': ssp.total_controls,
                'implemented': ssp.implemented_count,
                'partial': ssp.partial_count,
                'planned': ssp.planned_count,
                'not_implemented': ssp.not_implemented_count,
                'total_risk_score': ssp.total_risk_score
            },
            'metadata': {
                'generated_date': ssp.generated_date.isoformat(),
                'generated_by': ssp.generated_by,
                'version': ssp.version
            }
        }


# Example usage and testing
if __name__ == '__main__':
    # Create sample SSP
    ssp_gen = SSPGenerator(
        system_name="SAELAR AWS Security Assessment Platform",
        system_owner="Security Architecture and Evaluation Team",
        categorization="Moderate",
        system_acronym="SAELAR",
        isso_name="Information System Security Officer",
        system_description="Cloud-based security assessment tool for NIST 800-53 compliance evaluation",
        authorization_boundary="AWS Commercial Cloud (us-east-1, us-west-2)"
    )
    
    print("SSP Generator initialized successfully!")
    print(f"System: {ssp_gen.system_info.system_name}")
    print(f"Categorization: {ssp_gen.system_info.categorization.value}")
    print(f"Control Families: {len(ssp_gen.CONTROL_FAMILIES)}")

