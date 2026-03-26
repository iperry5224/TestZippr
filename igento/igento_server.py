"""
IGENTO - MCP Server for ISSO & Compliance
=========================================
Exposes Tools (actions), Resources (data), and Prompts (templates) for
Information System Security Officers (ISSOs) and INFOSEC analysts doing
compliance and assessment work—not SOC monitoring.

Run: python igento_server.py
Test: Add to Cursor MCP config or use MCP Inspector.

Learn more: https://modelcontextprotocol.io
"""

import sys
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Create MCP server - name shows in client UI
# json_response=True uses plain JSON instead of SSE for POST responses - works better with browser bridge
mcp = FastMCP(
    name="Igento",
    instructions="Igento is an MCP server for ISSOs and INFOSEC analysts. Use the tools and resources for NIST 800-53 compliance, POA&M, SSP, risk acceptance, and control assessment workflows.",
    json_response=True,
)

# NIST 800-53 Rev 5 control family reference (lightweight - no heavy imports)
NIST_CONTROL_FAMILIES = {
    "AC": "Access Control",
    "AU": "Audit and Accountability",
    "CA": "Assessment, Authorization, and Monitoring",
    "CM": "Configuration Management",
    "CP": "Contingency Planning",
    "IA": "Identification and Authentication",
    "IR": "Incident Response",
    "MP": "Media Protection",
    "RA": "Risk Assessment",
    "SA": "System and Services Acquisition",
    "SC": "System and Communications Protection",
    "SI": "System and Information Integrity",
    "SR": "Supply Chain Risk Management",
}

# Common control examples for quick reference
CONTROL_EXAMPLES = {
    "AC-2": "Account Management – Manage system accounts (create, enable, modify, disable, remove)",
    "AC-3": "Access Enforcement – Enforce authorized access; deny by default",
    "AC-6": "Least Privilege – Restrict functions and access to least privilege",
    "IA-2": "Identification and Authentication (Org Users) – MFA for network access",
    "IA-5": "Authenticator Management – Manage and protect authenticators",
    "SI-4": "System Monitoring – Monitor system for attacks and unauthorized activity",
    "RA-5": "Vulnerability Scanning – Scan for vulnerabilities and remediate",
    "SC-8": "Transmission Confidentiality – Protect confidentiality of transmitted info",
}

# =============================================================================
# TOOLS - Functions the AI can call (like API endpoints that do things)
# =============================================================================

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together. Simple example of a tool with typed inputs."""
    return a + b


@mcp.tool()
def greet(name: str, style: str = "friendly") -> str:
    """Generate a greeting for someone.
    
    Args:
        name: The person's name
        style: Greeting style - 'friendly', 'formal', or 'casual'
    """
    styles = {
        "friendly": f"Hey {name}! Great to meet you!",
        "formal": f"Good day, {name}. Pleased to make your acquaintance.",
        "casual": f"Yo {name}, what's up?",
    }
    return styles.get(style, styles["friendly"])


@mcp.tool()
def get_timestamp() -> str:
    """Get the current date and time. Useful for testing tool invocation."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool()
def echo_message(message: str, repeat: int = 1) -> str:
    """Echo a message back. Good for testing that tools receive parameters correctly.
    
    Args:
        message: The message to echo
        repeat: How many times to repeat it (default 1)
    """
    return (message + " ") * repeat


# =============================================================================
# ISSO TOOLS - For compliance, assessment, and authorization workflows
# =============================================================================

@mcp.tool()
def lookup_nist_control(control_id: str) -> str:
    """Look up a NIST 800-53 Rev 5 control by ID. Returns family context and a brief description.
    
    Args:
        control_id: NIST control ID, e.g. AC-2, SI-4, RA-5(1)
    """
    # Normalize (e.g., "AC-2(1)" → family "AC")
    base = control_id.split("(")[0].strip().upper()
    family_code = base.split("-")[0] if "-" in base else base[:2]
    
    family_name = NIST_CONTROL_FAMILIES.get(family_code, "Unknown")
    specific = CONTROL_EXAMPLES.get(base, "")
    
    if specific:
        return f"**{control_id}** ({family_name})\n\n{specific}\n\n*Reference: NIST SP 800-53 Rev 5. Use this as a starting point; consult the full control text for assessment.*"
    return f"**{control_id}** – {family_name}\n\nNo quick summary available. Refer to NIST SP 800-53 Rev 5 for full control language. Family: {family_name}."


@mcp.tool()
def draft_poam_entry(control_id: str, weakness: str, severity: str = "Moderate") -> str:
    """Generate a POA&M (Plan of Action & Milestones) entry template for a control finding.
    
    Args:
        control_id: NIST control ID (e.g., AC-2, SI-4)
        weakness: Brief description of the weakness or gap
        severity: Low, Moderate, or High
    """
    return f"""## POA&M Entry Template

**Weakness ID:** [Auto-assign]  
**Control:** {control_id}  
**Weakness Description:** {weakness}  
**Severity:** {severity}  
**Point of Contact:** [POC Name]  
**Resource Requirements:** [Staff, tools, budget]  
**Scheduled Completion Date:** [YYYY-MM-DD]  
**Milestones:** [Key checkpoints]  
**Status:** Open  

*Fill in placeholders and submit per your organization's POA&M process.*"""


@mcp.tool()
def draft_ssp_statement(control_id: str, implementation: str = "") -> str:
    """Generate an SSP (System Security Plan) implementation statement template for a control.
    
    Args:
        control_id: NIST control ID (e.g., AC-2, IA-5)
        implementation: Optional brief description of how the control is implemented
    """
    impl_placeholder = implementation if implementation else "[Describe how this control is implemented—policies, procedures, technical measures, responsible roles.]"
    return f"""## SSP Implementation Statement: {control_id}

**What is implemented:**
{impl_placeholder}

**Responsible entity:** [Org/team]  
**Evidence references:** [Policy docs, config screenshots, audit logs]  
**Limitations/exceptions:** [If any, document and reference risk acceptance]  

*Refine for your system and control baseline. Align with assessor expectations.*"""


@mcp.tool()
def control_evidence_guide(control_id: str) -> str:
    """Suggest types of evidence an ISSO might collect to demonstrate control implementation.
    
    Args:
        control_id: NIST control ID (e.g., AC-2, AU-2, SI-4)
    """
    guides = {
        "AC-2": "Policy/procedure for account lifecycle; screen captures of account management; list of account types and approval workflow; evidence of periodic review.",
        "AC-3": "Access control policy; RBAC/ABAC configuration; screenshots of deny-by-default and least-privilege settings.",
        "IA-2": "MFA configuration; login flow screenshots; policy requiring MFA for org users.",
        "IA-5": "Password policy; authenticator management procedure; evidence of complexity and rotation requirements.",
        "AU-2": "Audit policy; list of auditable events; log configuration; retention policy.",
        "SI-4": "Monitoring capability documentation; SIEM/deployment config; alert rule samples; incident response linkage.",
        "RA-5": "Vulnerability scan reports; remediation tracking; scan schedule and scope.",
        "SC-8": "TLS/encryption config; network diagram showing protected paths; certificate management.",
    }
    base = control_id.split("(")[0].strip().upper()
    suggestion = guides.get(base, "Policy documents, configuration evidence, screenshots, logs, or attestations relevant to the control. Align with assessor requirements.")
    family = NIST_CONTROL_FAMILIES.get(base.split("-")[0] if "-" in base else "?", "N/A")
    return f"**Evidence guidance for {control_id} ({family}):**\n\n{suggestion}"


@mcp.tool()
def risk_acceptance_template(finding: str, justification: str, mitigating: str = "") -> str:
    """Generate risk acceptance language for a finding that cannot be remediated immediately.
    
    Args:
        finding: Brief description of the finding or gap
        justification: Why remediation is deferred (cost, legacy, operational constraint)
        mitigating: Optional compensating controls or interim measures
    """
    mitig = f"\n**Compensating controls:** {mitigating}" if mitigating else ""
    return f"""## Risk Acceptance Draft

**Finding:** {finding}  
**Justification for acceptance:** {justification}{mitig}  
**Accepted by:** [Authorizing Official]  
**Review date:** [Date for reassessment]  
**Conditions:** Acceptance is temporary; reassess when system changes or funding available.  

*Tailor to your organization's risk acceptance process and AOR format.*"""


# =============================================================================
# RESOURCES - Read-only data the AI can load into context (like GET endpoints)
# =============================================================================

@mcp.resource("igento://info/about")
def get_about() -> str:
    """Information about the Igento MCP server."""
    return """
# Igento MCP Server

A learning project for Model Context Protocol (MCP).

## What is MCP?
MCP lets AI assistants connect to external data and tools in a standardized way.
- **Tools** = Actions the AI can execute (like API POST)
- **Resources** = Data the AI can read (like API GET)
- **Prompts** = Reusable templates for common tasks

## Resources in this server:
- igento://info/about - This file
- igento://help/{topic} - Help on a topic
- igento://nist/family/{code} - NIST 800-53 control family overview
- igento://isso/workflows - ISSO workflow reference

## Tools in this server:
Demo: add_numbers, greet, get_timestamp, echo_message
ISSO: lookup_nist_control, draft_poam_entry, draft_ssp_statement, control_evidence_guide, risk_acceptance_template
"""


@mcp.resource("igento://help/{topic}")
def get_help(topic: str) -> str:
    """Get help on an MCP topic. Try: tools, resources, prompts, or concepts."""
    help_content = {
        "tools": """
## MCP Tools
Tools are functions the AI can call. They can take parameters and return results.
- Define with @mcp.tool() decorator
- Use type hints for parameters (AI gets a schema)
- Docstring becomes the tool description

Example: add_numbers(a: int, b: int) -> int
""",
        "resources": """
## MCP Resources
Resources are URI-addressable data. The AI reads them to get context.
- Define with @mcp.resource("uri://path/{param}") 
- URI template params map to function args
- Only loaded when requested (lazy)

Example: igento://help/{topic}
""",
        "prompts": """
## MCP Prompts
Prompts are reusable templates that help structure AI interactions.
- Define with @mcp.prompt()
- Can take parameters to customize the prompt
- Great for consistent workflows

Example: prompt_template(topic: str) -> str
""",
        "concepts": """
## MCP Core Concepts
1. **Server** - Exposes tools, resources, prompts
2. **Client** - Cursor, Claude Desktop, or custom app
3. **Transport** - stdio (local) or HTTP (remote)
4. **Protocol** - JSON-RPC over the transport

STDIO: Server runs as subprocess, client talks via stdin/stdout.
HTTP: Server runs as web server, client makes HTTP requests.
""",
    }
    return help_content.get(topic.lower(), f"No help found for '{topic}'. Try: tools, resources, prompts, concepts")


@mcp.resource("igento://nist/family/{code}")
def get_nist_family(code: str) -> str:
    """Get NIST 800-53 control family overview by 2-letter code (AC, AU, IA, SI, etc.)."""
    code = code.upper().strip()
    name = NIST_CONTROL_FAMILIES.get(code, "")
    if not name:
        return f"No family found for '{code}'. Valid codes: {', '.join(NIST_CONTROL_FAMILIES.keys())}"
    controls = [k for k in CONTROL_EXAMPLES if k.startswith(f"{code}-")]
    lines = [f"# {code} - {name}", "", f"Overview of the {name} control family.", ""]
    if controls:
        lines.append("## Example controls")
        for c in controls:
            lines.append(f"- **{c}**: {CONTROL_EXAMPLES[c]}")
    return "\n".join(lines) + "\n\n*Reference: NIST SP 800-53 Rev 5*"


@mcp.resource("igento://isso/workflows")
def get_isso_workflows() -> str:
    """ISSO workflow reference for compliance and authorization tasks."""
    return """
# ISSO Workflow Reference

Common workflows for Information System Security Officers (non-SOC focus).

## Authorization (A&A)
1. Gather system documentation (SSP, diagrams, policies)
2. Conduct control assessments (implemented vs. stated)
3. Document findings in POA&M
4. Support risk determinations (accept, mitigate, remediate)
5. Prepare authorization package for AO

## Continuous Monitoring
- Track POA&M milestones and due dates
- Review vulnerability scan results and remediation status
- Verify change management ties to controls
- Prepare status reports for governance

## Assessment Prep
- Map controls to evidence locations
- Verify policies and procedures are current
- Pre-populate SSP implementation statements
- Coordinate with assessor on scope and schedule

## Finding Response
- Document root cause
- Assess severity (Low/Moderate/High/Critical)
- Draft POA&M entry or risk acceptance
- Track remediation to closure

*Use Igento tools: lookup_nist_control, draft_poam_entry, draft_ssp_statement, control_evidence_guide, risk_acceptance_template*
"""


# =============================================================================
# PROMPTS - Reusable templates for AI interactions
# =============================================================================

@mcp.prompt()
def learn_mcp(topic: str, depth: str = "brief") -> str:
    """Generate a prompt to learn about an MCP topic.
    
    Args:
        topic: What to learn (e.g., tools, resources, architecture)
        depth: How deep - 'brief', 'detailed', or 'deep_dive'
    """
    depth_instructions = {
        "brief": "Give a 2-3 sentence overview.",
        "detailed": "Explain with examples and key points.",
        "deep_dive": "Provide a comprehensive explanation with best practices and gotchas.",
    }
    instr = depth_instructions.get(depth, depth_instructions["brief"])
    return f"Please explain MCP {topic} for someone learning. {instr}"


@mcp.prompt()
def debug_tool(tool_name: str, error_message: str) -> str:
    """Create a debugging prompt when a tool fails.
    
    Args:
        tool_name: The tool that failed
        error_message: The error received
    """
    return f"""I'm debugging an MCP tool called "{tool_name}".

Error: {error_message}

Please help me:
1. Identify the likely cause
2. Suggest how to fix it
3. Mention common MCP tool pitfalls (e.g., stdout vs stderr for logging)
"""


# ---- ISSO Prompts ----

@mcp.prompt()
def draft_finding(control_id: str, condition: str, impact: str = "") -> str:
    """Generate a prompt to draft a control assessment finding.
    
    Args:
        control_id: NIST control ID (e.g., AC-2, SI-4)
        condition: What was observed (the condition)
        impact: Optional description of impact if known
    """
    return f"""Help me draft an assessment finding for control {control_id}.

**Condition observed:** {condition}
**Impact (if known):** {impact or "[To be assessed]"}

Please provide:
1. A clear, concise finding statement (Condition + Criteria + Cause + Effect format if appropriate)
2. Recommended severity (Low/Moderate/High/Critical) with brief rationale
3. Suggested remediation actions
4. Possible compensating controls if full remediation is delayed

Use lookup_nist_control or igento://nist/family/{{code}} if you need control context."""


@mcp.prompt()
def audit_prep(system_name: str, control_families: str = "all") -> str:
    """Generate a prompt to prepare for a control assessment or audit.
    
    Args:
        system_name: Name or identifier of the system
        control_families: Comma-separated families (AC, AU, IA...) or 'all'
    """
    return f"""I'm preparing for an assessment/audit of {system_name}.

**Control families in scope:** {control_families}

Help me create a preparation checklist:
1. Evidence to gather per family (policies, configs, logs, screenshots)
2. Key people to coordinate with (system owner, admins, assessor)
3. Common gaps to check proactively
4. Timeline and sequencing (what to verify first)

Use igento://isso/workflows and control_evidence_guide where relevant."""


@mcp.prompt()
def remediation_plan(finding_summary: str, constraints: str = "") -> str:
    """Generate a prompt to create a remediation plan for a finding.
    
    Args:
        finding_summary: Brief description of the finding
        constraints: Budget, timeline, or technical constraints
    """
    return f"""Help me create a remediation plan for this finding:

**Finding:** {finding_summary}
**Constraints:** {constraints or "None specified"}

Please suggest:
1. Concrete remediation steps (prioritized)
2. Milestones with realistic due dates
3. Resource requirements (staff, tools, budget)
4. Risks of deferral if we cannot remediate immediately
5. How to verify closure (evidence to collect)

Format suitable for a POA&M entry or project tracker."""


@mcp.prompt()
def control_assessment(control_id: str, implementation: str = "") -> str:
    """Generate a prompt to assess whether a control is implemented adequately.
    
    Args:
        control_id: NIST control ID (e.g., AC-2, IA-5)
        implementation: Brief description of what is implemented (or leave blank)
    """
    return f"""Help me assess whether control {control_id} is adequately implemented.

**Current implementation (as described):** {implementation or "[Not yet described - help me know what to look for]"}

Please provide:
1. Key assessment questions to ask / evidence to verify
2. Common weaknesses for this control
3. Red flags that suggest non-compliance
4. What "satisfactory" looks like for this control

Use lookup_nist_control if you need the control definition."""


# =============================================================================
# MAIN - Run the server
# =============================================================================

def main():
    import argparse
    p = argparse.ArgumentParser(description="Igento MCP server")
    p.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="stdio for Cursor/Claude, streamable-http for local HTTP",
    )
    p.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for streamable-http (default 8000)",
    )
    args = p.parse_args()
    msg = f"Igento MCP server starting ({args.transport})... Use Cursor or MCP Inspector to connect."
    print(msg, file=sys.stderr)
    if args.transport == "streamable-http":
        app = mcp.streamable_http_app()
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    else:
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
