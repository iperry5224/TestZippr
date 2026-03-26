#!/usr/bin/env python3
"""
OWASP Top 10 Assessment for SAELAR Platform
============================================
Runs a security assessment against the SAELAR codebase using the OWASP Top 10 framework.
Produces an HTML report with findings and recommendations.

Usage: python owasp_saelar_assessment.py
Output: saelar_owasp_report_YYYYMMDD.html
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# OWASP Top 10 2024/2025
OWASP_TOP_10 = [
    ("A01", "Broken Access Control", "Failures in enforcing access policies."),
    ("A02", "Security Misconfiguration", "Default configs, unnecessary features, unpatched flaws."),
    ("A03", "Software Supply Chain", "Vulnerable or malicious third-party components."),
    ("A04", "Cryptographic Failures", "Failures related to cryptography and data protection."),
    ("A05", "Injection", "Command, query, or code injection vulnerabilities."),
    ("A06", "Insecure Design", "Missing or ineffective threat modeling."),
    ("A07", "Authentication Failures", "Weak or broken authentication mechanisms."),
    ("A08", "Data Integrity Failures", "Unverified data, unsigned updates, deserialization."),
    ("A09", "Logging & Monitoring", "Missing or inadequate security logging."),
    ("A10", "Mishandling Exceptional Conditions", "Poor error handling, information disclosure."),
]

ROOT = Path(__file__).resolve().parent
SAELAR_FILES = [
    "nist_setup.py",
    "nist_auth.py",
    "nist_dashboard.py",
    "nist_pages.py",
    "risk_score_app.py",
    "risk_score_calculator.py",
    "cisa_kev_checker.py",
]


def read_file(path: Path) -> str:
    """Read file with encoding fallback."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def scan_files() -> Dict[str, str]:
    """Load SAELAR source files."""
    content = {}
    for name in SAELAR_FILES:
        p = ROOT / name
        if p.exists():
            content[name] = read_file(p)
    return content


def run_checks(content: Dict[str, str]) -> List[Dict]:
    """Run OWASP checks against the codebase."""
    findings = []

    # A01: Broken Access Control
    nist_text = content.get("nist_setup.py", "")
    if "require_auth" in nist_text or "require_permission" in nist_text:
        auth_count = len(re.findall(r"require_auth|require_permission|is_session_valid", nist_text))
        findings.append({
            "id": "A01",
            "title": "Broken Access Control",
            "severity": "LOW" if auth_count > 5 else "MEDIUM",
            "file": "nist_setup.py",
            "finding": f"Auth decorators used ({auth_count} references). Verify all routes/pages check permissions before sensitive operations.",
            "recommendation": "Audit every page/view for require_auth or require_permission. Ensure role checks on sensitive actions.",
        })

    # A02: Security Misconfiguration
    if any("admin123" in text or "audit123" in text or "view123" in text for text in content.values()):
        findings.append({
            "id": "A02",
            "title": "Security Misconfiguration",
            "severity": "CRITICAL",
            "file": "nist_auth.py",
            "finding": "Default credentials hardcoded (admin/admin123, auditor/audit123, viewer/view123). Demo credentials exposed in login UI.",
            "recommendation": "Remove default users. Require initial setup. Use env vars or secrets manager for any default creds. Remove demo credentials expander in production.",
        })
    if any("localhost" in text and "11434" in text for text in content.values()):
        findings.append({
            "id": "A02",
            "title": "Security Misconfiguration",
            "severity": "MEDIUM",
            "file": "nist_setup.py",
            "finding": "Ollama listens on localhost:11434. In container/network deployment this may expose AI endpoint.",
            "recommendation": "Bind Ollama to loopback only. Use reverse proxy with auth for remote access.",
        })

    # A03: Software Supply Chain
    req_path = ROOT / "requirements.txt"
    if req_path.exists():
        req = read_file(req_path)
        if ">=" in req and "==" not in req:
            findings.append({
                "id": "A03",
                "title": "Software Supply Chain",
                "severity": "MEDIUM",
                "file": "requirements.txt",
                "finding": "Dependencies use flexible version ranges (>=). Pinned versions reduce supply chain risk.",
                "recommendation": "Pin exact versions (==) for reproducible builds. Run pip-audit or safety check regularly.",
            })

    # A04: Cryptographic Failures
    for fname, text in content.items():
        if "hashlib.sha256" in text and "password" in text.lower():
            findings.append({
                "id": "A04",
                "title": "Cryptographic Failures",
                "severity": "HIGH",
                "file": fname,
                "finding": "Passwords hashed with SHA-256. SHA-256 is fast and not designed for password hashing; vulnerable to GPU cracking.",
                "recommendation": "Use bcrypt, argon2, or scrypt for password hashing. Add salt (bcrypt/argon2 do this by default).",
            })
            break

    # A05: Injection
    for fname, text in content.items():
        if re.search(r"\beval\s*\(", text) or re.search(r"\bexec\s*\(", text):
            findings.append({
                "id": "A05",
                "title": "Injection",
                "severity": "CRITICAL",
                "file": fname,
                "finding": "eval() or exec() detected. Dynamic code execution can lead to RCE if user input flows in.",
                "recommendation": "Remove eval/exec or use safe alternatives. Never pass user input to exec/eval.",
            })
        if "subprocess" in text and "shell=True" in text:
            findings.append({
                "id": "A05",
                "title": "Injection",
                "severity": "HIGH",
                "file": fname,
                "finding": "subprocess with shell=True. Command injection risk if arguments include user input.",
                "recommendation": "Avoid shell=True. Use list form: subprocess.run(['cmd', 'arg1', 'arg2']). Validate/sanitize any user input.",
            })

    # A06: Insecure Design
    findings.append({
        "id": "A06",
        "title": "Insecure Design",
        "severity": "MEDIUM",
        "file": "nist_auth.py",
        "finding": "User store is JSON file. No encryption at rest. Single point of failure for credential storage.",
        "recommendation": "Use a proper database (e.g., PostgreSQL) or managed auth (Cognito, Auth0). Encrypt sensitive data at rest.",
    })

    # A07: Authentication Failures
    for fname, text in content.items():
        if "require_mfa" in text and "False" in text:
            findings.append({
                "id": "A07",
                "title": "Authentication Failures",
                "severity": "MEDIUM",
                "file": fname,
                "finding": "MFA disabled (require_mfa: False). Session timeout 60 min; consider shorter for sensitive ops.",
                "recommendation": "Enable MFA for admin/auditor roles. Reduce session timeout for high-privilege users.",
            })
            break
    if any("password_min_length" in t and "8" in t for t in content.values()):
        findings.append({
            "id": "A07",
            "title": "Authentication Failures",
            "severity": "LOW",
            "file": "nist_auth.py",
            "finding": "Minimum password length is 8. NIST SP 800-63B recommends at least 8 with complexity, or longer passphrases.",
            "recommendation": "Increase to 12+ characters. Consider password breach checking (HaveIBeenPwned API).",
        })

    # A08: Data Integrity Failures
    findings.append({
        "id": "A08",
        "title": "Data Integrity Failures",
        "severity": "LOW",
        "file": "nist_auth.py",
        "finding": "User JSON file has no integrity checks. Tampering could add/modify accounts.",
        "recommendation": "Use HMAC or signed storage. Consider checksums or version control for config files.",
    })

    # A09: Logging & Monitoring
    if not any("logging" in text and "login" in text.lower() for text in content.values()) and \
       not any("audit" in text.lower() and "log" in text.lower() for text in content.values()):
        findings.append({
            "id": "A09",
            "title": "Logging & Monitoring",
            "severity": "MEDIUM",
            "file": "nist_auth.py / nist_setup.py",
            "finding": "Limited evidence of security event logging (logins, failures, privilege changes).",
            "recommendation": "Log auth events (success/failure), role changes, and high-risk actions. Use structured logging. Consider SIEM integration.",
        })

    # A10: Mishandling Exceptional Conditions
    for fname, text in content.items():
        if "except Exception" in text or "except:" in text:
            count = len(re.findall(r"except\s*(Exception)?\s*:", text))
            if count > 3:
                findings.append({
                    "id": "A10",
                    "title": "Mishandling Exceptional Conditions",
                    "severity": "LOW",
                    "file": fname,
                    "finding": f"Broad exception handlers ({count} found). May hide errors and leak sensitive data in tracebacks.",
                    "recommendation": "Catch specific exceptions. Log errors without exposing internals. Avoid printing stack traces to users.",
                })
                break

    return findings


def generate_html_report(findings: List[Dict], out_path: Path) -> None:
    """Generate HTML report."""
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    sorted_findings = sorted(findings, key=lambda f: (severity_order.get(f["severity"], 4), f["id"]))

    rows = ""
    for f in sorted_findings:
        color = {"CRITICAL": "#dc3545", "HIGH": "#fd7e14", "MEDIUM": "#ffc107", "LOW": "#0dcaf0"}.get(f["severity"], "#6c757d")
        rows += f"""
        <tr>
            <td><span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;">{f['severity']}</span></td>
            <td>{f['id']}</td>
            <td>{f['title']}</td>
            <td><code>{f['file']}</code></td>
            <td>{f['finding']}</td>
            <td>{f['recommendation']}</td>
        </tr>
        """

    summary = {}
    for f in findings:
        summary[f["severity"]] = summary.get(f["severity"], 0) + 1

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAELAR OWASP Top 10 Assessment Report</title>
    <style>
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 2rem; background: #f8f9fa; }}
        h1 {{ color: #1e3a5f; border-bottom: 2px solid #2d5a87; padding-bottom: 0.5rem; }}
        h2 {{ color: #2d5a87; margin-top: 2rem; }}
        table {{ width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
        th {{ background: #1e3a5f; color: #fff; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f5f7fa; }}
        code {{ background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
        .summary {{ display: flex; gap: 1rem; margin: 1rem 0; flex-wrap: wrap; }}
        .badge {{ padding: 8px 16px; border-radius: 6px; font-weight: 600; color: #fff; }}
        .meta {{ color: #6c757d; font-size: 0.9rem; margin-bottom: 1.5rem; }}
    </style>
</head>
<body>
    <h1>SAELAR OWASP Top 10 Security Assessment Report</h1>
    <p class="meta">Generated: {date_str} | Platform: SAELAR (NIST 800-53 Assessment Tool) | Framework: OWASP Top 10 2024</p>

    <h2>Summary</h2>
    <div class="summary">
        <span class="badge" style="background:#dc3545;">CRITICAL: {summary.get('CRITICAL', 0)}</span>
        <span class="badge" style="background:#fd7e14;">HIGH: {summary.get('HIGH', 0)}</span>
        <span class="badge" style="background:#ffc107;">MEDIUM: {summary.get('MEDIUM', 0)}</span>
        <span class="badge" style="background:#0dcaf0;">LOW: {summary.get('LOW', 0)}</span>
    </div>

    <h2>Findings</h2>
    <table>
        <thead>
            <tr>
                <th>Severity</th>
                <th>ID</th>
                <th>Category</th>
                <th>File</th>
                <th>Finding</th>
                <th>Recommendation</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>

    <h2>OWASP Top 10 Reference</h2>
    <table>
        <thead><tr><th>ID</th><th>Category</th><th>Description</th></tr></thead>
        <tbody>
            {"".join(f'<tr><td>{id}</td><td>{name}</td><td>{desc}</td></tr>' for id, name, desc in OWASP_TOP_10)}
        </tbody>
    </table>

    <p class="meta" style="margin-top: 2rem;">Report generated by owasp_saelar_assessment.py. Review findings and remediate according to priority.</p>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")


def main():
    print("SAELAR OWASP Top 10 Assessment")
    print("=" * 50)
    content = scan_files()
    print(f"Scanned {len(content)} files")
    findings = run_checks(content)
    print(f"Found {len(findings)} findings")

    date_str = datetime.now().strftime("%Y%m%d")
    out_path = ROOT / f"saelar_owasp_report_{date_str}.html"
    generate_html_report(findings, out_path)
    print(f"Report saved: {out_path}")
    return out_path


if __name__ == "__main__":
    main()
