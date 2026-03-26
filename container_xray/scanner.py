"""
Container Xray Lite — Image vulnerability scanner.
Uses Trivy (or Grype) to scan container images, returns structured findings.
"""
import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class VulnFinding:
    """Single vulnerability finding."""
    vuln_id: str
    package: str
    installed_version: str
    fixed_version: Optional[str]
    severity: str
    title: Optional[str]
    description: Optional[str]
    target: str
    pkg_type: str
    primary_url: Optional[str] = None
    references: list = field(default_factory=list)


@dataclass
class ScanResult:
    """Container scan result."""
    image: str
    success: bool
    findings: list[VulnFinding] = field(default_factory=list)
    total_critical: int = 0
    total_high: int = 0
    total_medium: int = 0
    total_low: int = 0
    total_info: int = 0
    artifact_type: str = ""
    error_message: Optional[str] = None


def _trivy_available() -> bool:
    """Check if Trivy binary is available."""
    return shutil.which("trivy") is not None


def _grype_available() -> bool:
    """Check if Grype binary is available."""
    return shutil.which("grype") is not None


def _parse_trivy_json(data: dict) -> ScanResult:
    """Parse Trivy JSON output into ScanResult."""
    findings: list[VulnFinding] = []
    artifact_name = data.get("ArtifactName", "unknown")
    results = data.get("Results", [])

    for r in results:
        target = r.get("Target", "")
        pkg_type = r.get("Type", "")
        vulns = r.get("Vulnerabilities", [])

        for v in vulns:
            findings.append(VulnFinding(
                vuln_id=v.get("VulnerabilityID", ""),
                package=v.get("PkgName", ""),
                installed_version=v.get("InstalledVersion", ""),
                fixed_version=v.get("FixedVersion"),
                severity=(v.get("Severity") or "UNKNOWN").upper(),
                title=v.get("Title"),
                description=v.get("Description"),
                target=target,
                pkg_type=pkg_type,
                primary_url=v.get("PrimaryURL"),
                references=v.get("References", []),
            ))

    critical = sum(1 for f in findings if f.severity == "CRITICAL")
    high = sum(1 for f in findings if f.severity == "HIGH")
    medium = sum(1 for f in findings if f.severity == "MEDIUM")
    low = sum(1 for f in findings if f.severity == "LOW")
    info = sum(1 for f in findings if f.severity in ("INFO", "UNKNOWN"))

    return ScanResult(
        image=artifact_name,
        success=True,
        findings=findings,
        total_critical=critical,
        total_high=high,
        total_medium=medium,
        total_low=low,
        total_info=info,
        artifact_type=data.get("ArtifactType", "container_image"),
    )


def scan_image(image_ref: str) -> ScanResult:
    """
    Scan a container image for vulnerabilities.
    
    Args:
        image_ref: Docker image reference (e.g. nginx:latest, alpine:3.18, myregistry.io/app:v1)
    
    Returns:
        ScanResult with findings or error state
    """
    if _trivy_available():
        return _scan_with_trivy(image_ref)
    if _grype_available():
        return _scan_with_grype(image_ref)

    return ScanResult(
        image=image_ref,
        success=False,
        error_message=(
            "No scanner found. Install Trivy or Grype:\n"
            "  • Trivy: https://trivy.dev/docs/installation/\n"
            "  • Grype: https://github.com/anchore/grype#installation\n"
            "  On Windows (scoop): scoop install trivy"
        ),
    )


def _scan_with_trivy(image_ref: str) -> ScanResult:
    """Run Trivy image scan and parse JSON output."""
    try:
        proc = subprocess.run(
            ["trivy", "image", "--format", "json", "--quiet", image_ref],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if proc.returncode != 0 and not proc.stdout.strip():
            return ScanResult(
                image=image_ref,
                success=False,
                error_message=proc.stderr or f"Trivy exited with code {proc.returncode}",
            )

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            return ScanResult(
                image=image_ref,
                success=False,
                error_message=f"Failed to parse Trivy JSON: {e}",
            )

        return _parse_trivy_json(data)
    except subprocess.TimeoutExpired:
        return ScanResult(
            image=image_ref,
            success=False,
            error_message="Scan timed out after 5 minutes",
        )
    except FileNotFoundError:
        return ScanResult(
            image=image_ref,
            success=False,
            error_message="Trivy binary not found. Install from https://trivy.dev",
        )
    except Exception as e:
        return ScanResult(
            image=image_ref,
            success=False,
            error_message=str(e),
        )


def _scan_with_grype(image_ref: str) -> ScanResult:
    """Run Grype image scan and parse JSON output."""
    try:
        proc = subprocess.run(
            ["grype", image_ref, "-o", "json"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if proc.returncode != 0 and not proc.stdout.strip():
            return ScanResult(
                image=image_ref,
                success=False,
                error_message=proc.stderr or f"Grype exited with code {proc.returncode}",
            )

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            return ScanResult(
                image=image_ref,
                success=False,
                error_message=f"Failed to parse Grype JSON: {e}",
            )

        return _parse_grype_json(data, image_ref)
    except subprocess.TimeoutExpired:
        return ScanResult(
            image=image_ref,
            success=False,
            error_message="Scan timed out after 5 minutes",
        )
    except FileNotFoundError:
        return ScanResult(
            image=image_ref,
            success=False,
            error_message="Grype binary not found. Install from https://github.com/anchore/grype",
        )
    except Exception as e:
        return ScanResult(
            image=image_ref,
            success=False,
            error_message=str(e),
        )


def _parse_grype_json(data: dict, image_ref: str) -> ScanResult:
    """Parse Grype JSON output into ScanResult."""
    findings: list[VulnFinding] = []
    matches = data.get("matches", [])

    for m in matches:
        vuln = m.get("vulnerability", {})
        artifact = m.get("artifact", {})
        severity = (vuln.get("severity") or "Unknown").upper()
        if severity not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "UNKNOWN"):
            severity = "UNKNOWN"

        findings.append(VulnFinding(
            vuln_id=vuln.get("id", ""),
            package=artifact.get("name", ""),
            installed_version=artifact.get("version", ""),
            fixed_version=vuln.get("fix", {}).get("versions", [None])[0] if vuln.get("fix", {}).get("versions") else None,
            severity=severity,
            title=vuln.get("description"),
            description=vuln.get("description"),
            target=artifact.get("locations", [{}])[0].get("path", "") if artifact.get("locations") else "",
            pkg_type=artifact.get("type", ""),
            primary_url=vuln.get("urls", [None])[0] if vuln.get("urls") else None,
            references=vuln.get("urls", []),
        ))

    critical = sum(1 for f in findings if f.severity == "CRITICAL")
    high = sum(1 for f in findings if f.severity == "HIGH")
    medium = sum(1 for f in findings if f.severity == "MEDIUM")
    low = sum(1 for f in findings if f.severity == "LOW")
    info = sum(1 for f in findings if f.severity in ("INFO", "UNKNOWN"))

    return ScanResult(
        image=image_ref,
        success=True,
        findings=findings,
        total_critical=critical,
        total_high=high,
        total_medium=medium,
        total_low=low,
        total_info=info,
        artifact_type="container_image",
    )


def scanner_available() -> tuple[bool, str]:
    """
    Check which scanner is available.
    Returns (available, message).
    """
    if _trivy_available():
        return True, "Trivy"
    if _grype_available():
        return True, "Grype"
    return False, "None (install Trivy or Grype)"
