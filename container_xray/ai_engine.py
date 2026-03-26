"""
Container Xray Lite — AI-powered analysis engine.
Uses Bedrock (or Ollama for air-gapped) for contextual risk assessment,
prioritization, and remediation guidance.
"""
import json
import os

try:
    import boto3
    _HAS_BOTO = True
except ImportError:
    _HAS_BOTO = False

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

from .scanner import ScanResult, VulnFinding


AIRGAPPED = os.environ.get("CONTAINER_XRAY_AIRGAPPED", "false").lower() == "true"
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

BEDROCK_MODELS = [
    "amazon.titan-text-express-v1",
    "amazon.titan-text-lite-v1",
    "meta.llama3-8b-instruct-v1:0",
    "mistral.mistral-7b-instruct-v0:2",
    "nvidia.nemotron-nano-12b-v2",
]


def _call_bedrock(prompt: str, max_tokens: int = 4096, temperature: float = 0.3) -> str | None:
    """Call AWS Bedrock. Returns response text or None."""
    if not _HAS_BOTO:
        return None
    try:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        for model_id in BEDROCK_MODELS:
            try:
                resp = client.converse(
                    modelId=model_id,
                    messages=[{"role": "user", "content": [{"text": prompt}]}],
                    inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
                )
                return resp["output"]["message"]["content"][0]["text"]
            except Exception:
                continue
    except Exception:
        pass
    return None


def _call_ollama(prompt: str, max_tokens: int = 4096) -> str | None:
    """Call local Ollama. Returns response text or None."""
    if not _HAS_REQUESTS:
        return None
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "llama3:8b", "prompt": prompt, "stream": False, "options": {"num_predict": max_tokens}},
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "")
    except Exception:
        pass
    return None


def _call_ai(prompt: str, max_tokens: int = 4096) -> str | None:
    """Call AI (Ollama if air-gapped, else Bedrock)."""
    if AIRGAPPED:
        return _call_ollama(prompt, max_tokens)
    return _call_bedrock(prompt, max_tokens)


def ai_scan_summary(result: ScanResult) -> str:
    """AI-generated executive summary of scan results."""
    if not result.findings:
        return "**No vulnerabilities detected.** This image appears clean based on the scan."

    sample = result.findings[:20]
    sample_json = json.dumps([{
        "id": f.vuln_id, "package": f.package, "version": f.installed_version,
        "fixed": f.fixed_version, "severity": f.severity, "title": (f.title or "")[:80]
    } for f in sample], indent=2)

    prompt = f"""You are a container security expert. Summarize this vulnerability scan for a technical audience.

Image: {result.image}
Total findings: {len(result.findings)}
Critical: {result.total_critical} | High: {result.total_high} | Medium: {result.total_medium} | Low: {result.total_low}

Sample vulnerabilities:
{sample_json}

Provide:
1. EXECUTIVE SUMMARY (2-3 sentences): Overall risk posture and key concerns
2. TOP PRIORITIES: The 3-5 most urgent items to fix and why
3. CONTEXTUAL RISK: Is this image likely exploitable in typical deployment? (Consider base image, exposed services, network exposure)
4. RECOMMENDED ACTIONS: High-level remediation steps in order of impact

Be concise, actionable, and avoid jargon where possible."""

    out = _call_ai(prompt, max_tokens=1536)
    return out or _fallback_summary(result)


def ai_remediation_for_finding(finding: VulnFinding) -> str:
    """AI-generated remediation steps for a single vulnerability."""
    prompt = f"""You are a container security specialist. Provide remediation guidance.

Vulnerability: {finding.vuln_id}
Package: {finding.package} (installed: {finding.installed_version})
Fixed version: {finding.fixed_version or "Not yet available"}
Severity: {finding.severity}
Title: {finding.title or "N/A"}
Description: {(finding.description or "")[:300]}

Provide:
1. IMMEDIATE ACTION: What to do first (upgrade, patch, or workaround)
2. DOCKERFILE/IMAGE FIX: How to fix in a Dockerfile or base image choice
3. ALTERNATIVES: If no fix exists, suggest base image alternatives or mitigations
4. VERIFICATION: How to confirm the fix worked

Keep it practical and copy-paste friendly."""

    out = _call_ai(prompt, max_tokens=1024)
    return out or _fallback_remediation(finding)


def ai_remediation_for_cve(cve_id: str, description: str, severity: str, context: str = "") -> str:
    """AI-generated auto-remediation for a CVE (dashboard/simulation use)."""
    prompt = f"""You are a container security specialist. Provide auto-remediation guidance.

CVE/Vulnerability: {cve_id}
Severity: {severity}
Description: {(description or "")[:400]}
{f"Context: {context[:200]}" if context else ""}

Provide practical remediation:
1. IMMEDIATE ACTION: Upgrade path, patch, or workaround
2. DOCKERFILE/IMAGE: How to fix in Dockerfile or base image
3. CI/CD: How to automate (e.g. dependabot, Renovate, pipeline gates)
4. VERIFICATION: How to confirm the fix

Keep it actionable and copy-paste friendly."""

    out = _call_ai(prompt, max_tokens=1024)
    if out:
        return out
    return f"""**{cve_id}** ({severity})
- Upgrade to a patched version when available
- Pin base image to a fixed digest: `FROM image@sha256:...`
- Add vulnerability scan step to CI/CD pipeline
- Verify with `trivy image <your-image>` after fix"""


def ai_prioritization(result: ScanResult) -> list[dict]:
    """AI-ranked prioritization of findings by exploitability and impact."""
    if not result.findings:
        return []

    sample = result.findings[:25]
    sample_json = json.dumps([{
        "id": f.vuln_id, "package": f.package, "severity": f.severity,
        "fixed": f.fixed_version, "title": (f.title or "")[:60]
    } for f in sample], indent=2)

    prompt = f"""You are a container security analyst. Prioritize these vulnerabilities.

Image: {result.image}
Findings (sample):
{sample_json}

Return a JSON array of objects with:
- "vuln_id": the CVE/vuln ID
- "priority_score": 1-10 (10 = fix immediately)
- "reason": One sentence why this order
- "exploitable_likely": true/false

Sort by priority_score descending. Return ONLY valid JSON array, no markdown."""

    out = _call_ai(prompt, max_tokens=2048)
    if out:
        try:
            start = out.find("[")
            end = out.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(out[start:end])
        except json.JSONDecodeError:
            pass

    # Fallback: severity-based order
    order = {"CRITICAL": 10, "HIGH": 8, "MEDIUM": 5, "LOW": 2, "INFO": 1, "UNKNOWN": 1}
    return [
        {"vuln_id": f.vuln_id, "priority_score": order.get(f.severity, 5), "reason": f"{f.severity} severity", "exploitable_likely": f.severity in ("CRITICAL", "HIGH")}
        for f in sorted(result.findings, key=lambda x: -order.get(x.severity, 5))
    ][:15]


def ai_policy_recommendations(result: ScanResult) -> str:
    """AI-suggested policy controls for container deployment."""
    if not result.findings:
        return "No policy recommendations needed for a clean image. Consider maintaining a baseline: require signed images, pin versions, and scan on push."

    critical_high = result.total_critical + result.total_high
    prompt = f"""You are a DevSecOps lead. Suggest policy controls for container deployment.

Image: {result.image}
Findings: {len(result.findings)} total ({result.total_critical} Critical, {result.total_high} High)

Recommend:
1. DEPLOYMENT POLICY: Should this image be blocked, allowed with exceptions, or monitored? Justify.
2. CI/CD GATES: What thresholds (e.g., fail on Critical, warn on High) and how to implement
3. REGISTRY CONTROLS: Scan-on-push, retention, base image requirements
4. RUNTIME: Any runtime mitigations (read-only root, drop caps, network policies)

Be specific and implementable."""

    out = _call_ai(prompt, max_tokens=1024)
    return out or _fallback_policy(result)


def ai_sbom_narrative(result: ScanResult) -> str:
    """AI-generated SBOM / supply chain narrative."""
    pkgs = {}
    for f in result.findings:
        pkgs[f.package] = pkgs.get(f.package, 0) + 1
    top_pkgs = sorted(pkgs.items(), key=lambda x: -x[1])[:15]

    prompt = f"""You are a supply chain security analyst. Provide a brief narrative.

Image: {result.image}
Package types present: {list(set(f.pkg_type for f in result.findings))}
Top packages by vuln count: {top_pkgs}
Total distinct packages with vulns: {len(pkgs)}

Write 2-3 paragraphs:
1. SUPPLY CHAIN RISK: What does this image's dependency profile say about risk?
2. TRUST BOUNDARIES: Which packages are most concerning (upstream, transitive)?
3. SBOM VALUE: What would an SBOM (CycloneDX/SPDX) add for this image?

Concise, executive-friendly."""

    out = _call_ai(prompt, max_tokens=1024)
    return out or f"Image {result.image} has {len(result.findings)} vulnerabilities across {len(pkgs)} packages. Prioritize include OS packages (base image) and application dependencies."


def _fallback_summary(result: ScanResult) -> str:
    s = result
    return f"""**Executive Summary**
Image `{s.image}` has {len(s.findings)} vulnerabilities: {s.total_critical} Critical, {s.total_high} High, {s.total_medium} Medium, {s.total_low} Low.

**Top Priorities**
1. Address all Critical and High findings first.
2. Upgrade packages with available fixes.
3. Consider a newer base image if many OS-level vulns.

**Contextual Risk**
Manual review recommended. Base image age and exposure (e.g., internet-facing) affect exploitability.

**Recommended Actions**
- Patch or upgrade vulnerable packages.
- Rebuild image from updated base.
- Rescan after changes."""


def _fallback_remediation(finding: VulnFinding) -> str:
    parts = [
        f"**Immediate action:** Update {finding.package} from {finding.installed_version}",
        f"**Fixed version:** {finding.fixed_version or 'Check upstream'}",
        f"**Verification:** Rescan image after applying fix.",
    ]
    return "\n\n".join(parts)


def _fallback_policy(result: ScanResult) -> str:
    if result.total_critical > 0 or result.total_high > 3:
        return "**Deployment policy:** Block this image until Critical/High vulnerabilities are remediated. Add CI gate: fail on Critical."
    return "**Deployment policy:** Allow with monitoring. Add CI gate: fail on Critical, warn on High."
