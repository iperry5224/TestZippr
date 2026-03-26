"""
Igento Browser Bridge - MCP to HTML Translator
===============================================
Serves Igento's MCP tools, resources, and prompts as a browser-friendly HTML interface.

Usage:
  1. Start Igento MCP server first:  run igento   (or python igento_server.py --transport streamable-http --port 2323)
  2. Start this bridge:              python igento_browser_bridge.py
  3. Open in browser:                http://localhost:8888

Requires: Igento running on http://localhost:2323
"""

import asyncio
import json
import html as html_lib
from urllib.parse import quote, unquote
from pathlib import Path

MCP_TIMEOUT = 15  # seconds

try:
    from starlette.applications import Starlette
    from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
    from starlette.routing import Route, Mount
    from starlette.requests import Request
    import httpx
except ImportError as e:
    print("Install deps: pip install starlette uvicorn httpx")
    raise SystemExit(1)

MCP_URL = "http://localhost:2323/mcp"
BRIDGE_PORT = 8080

# Minimal MCP-over-HTTP client (bypasses MCP SDK streamable_http which had timeout issues)
_req_id = 0
def _next_id():
    global _req_id
    _req_id += 1
    return _req_id

async def _mcp_request(method: str, params: dict | None = None, session_id: str | None = None) -> dict:
    """Send JSON-RPC request to Igento, return parsed result or raise."""
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if session_id:
        headers["mcp-session-id"] = session_id
    req = {"jsonrpc": "2.0", "id": _next_id(), "method": method, "params": params or {}}
    async with httpx.AsyncClient(timeout=MCP_TIMEOUT) as client:
        r = await client.post(MCP_URL, json=req, headers=headers)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"].get("message", str(data["error"])))
        return data.get("result", {})

async def _init_session() -> str | None:
    """Initialize MCP session, return session_id from response header."""
    req = {
        "jsonrpc": "2.0", "id": _next_id(), "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "igento-bridge", "version": "1.0"}}
    }
    async with httpx.AsyncClient(timeout=MCP_TIMEOUT) as client:
        r = await client.post(MCP_URL, json=req, headers={"Accept": "application/json", "Content-Type": "application/json"})
        r.raise_for_status()
        session_id = r.headers.get("mcp-session-id")
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"].get("message", str(data["error"])))
        # Send initialized notification (no response expected, 202)
        hdrs = {"Accept": "application/json", "Content-Type": "application/json", "mcp-protocol-version": "2024-11-05"}
        if session_id:
            hdrs["mcp-session-id"] = session_id
        await client.post(MCP_URL, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=hdrs)
        return session_id

async def _fetch_mcp_data_inner():
    """Connect to Igento via HTTP and fetch tools, resources, prompts."""
    session_id = await _init_session()
    tools_result = await _mcp_request("tools/list", session_id=session_id)
    resources_result = await _mcp_request("resources/templates/list", session_id=session_id)
    prompts_result = await _mcp_request("prompts/list", session_id=session_id)
    return {
        "tools": tools_result.get("tools", []),
        "resources": resources_result.get("resourceTemplates", []),
        "prompts": prompts_result.get("prompts", []),
        "error": None,
    }


async def fetch_mcp_data():
    """Fetch MCP data with timeout."""
    try:
        return await asyncio.wait_for(_fetch_mcp_data_inner(), timeout=MCP_TIMEOUT)
    except asyncio.TimeoutError:
        return {"tools": [], "resources": [], "prompts": [], "error": f"Connection to Igento timed out after {MCP_TIMEOUT}s. Is it running on port 2323?"}
    except Exception as e:
        return {"tools": [], "resources": [], "prompts": [], "error": str(e)}


async def _call_tool_inner(name: str, arguments: dict) -> dict:
    session_id = await _init_session()
    result = await _mcp_request("tools/call", {"name": name, "arguments": arguments or {}}, session_id=session_id)
    return {"success": True, "result": result}


async def call_tool(name: str, arguments: dict) -> dict:
    """Invoke an MCP tool and return the result."""
    try:
        return await asyncio.wait_for(_call_tool_inner(name, arguments), timeout=MCP_TIMEOUT)
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Timed out after {MCP_TIMEOUT}s. Is Igento running?"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def _read_resource_inner(uri: str) -> dict:
    session_id = await _init_session()
    result = await _mcp_request("resources/read", {"uri": uri}, session_id=session_id)
    return {"success": True, "contents": result.get("contents", [])}


async def read_resource(uri: str) -> dict:
    """Read an MCP resource by URI."""
    try:
        return await asyncio.wait_for(_read_resource_inner(uri), timeout=MCP_TIMEOUT)
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Timed out after {MCP_TIMEOUT}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_input_html(tool) -> str:
    """Generate HTML form inputs from tool inputSchema."""
    schema = tool.get("inputSchema", {}) if isinstance(tool, dict) else (getattr(tool, "inputSchema", None) or {})
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    parts = []
    for key, meta in props.items():
        ptype = meta.get("type", "string")
        desc = meta.get("description", "")
        default = meta.get("default", "")
        r = "required" if key in required else ""
        if ptype == "integer":
            parts.append(f'<label>{html_lib.escape(key)}:</label> <input name="{html_lib.escape(key)}" type="number" value="{html_lib.escape(str(default))}" {r}>')
        else:
            parts.append(f'<label>{html_lib.escape(key)}:</label> <input name="{html_lib.escape(key)}" type="text" value="{html_lib.escape(str(default))}" placeholder="{html_lib.escape(desc[:50])}" {r}>')
    return "<br>".join(parts) if parts else ""


async def home(request: Request):
    """Serve the main HTML dashboard."""
    data = await fetch_mcp_data()
    err = data["error"]
    if err:
        return HTMLResponse(f"""
<!DOCTYPE html>
<html><head><title>Igento Bridge - Error</title>
<style>
body {{ font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 1rem; }}
.error {{ color: #c00; background: #fee; padding: 1rem; border-radius: 8px; }}
a {{ color: #06c; }}
</style></head>
<body>
<h1>Igento Browser Bridge</h1>
<div class="error">Cannot connect to Igento MCP at {html_lib.escape(MCP_URL)}.<br>
{html_lib.escape(err)}</div>
<p>Make sure Igento is running: <code>run igento</code> or <code>python igento_server.py --transport streamable-http --port 2323</code></p>
<p><a href="/">Retry</a></p>
</body></html>
""")

    TOOL_TIPS = {
        "add_numbers": "Demo: Add two integers. The MCP server infers the JSON schema from the Python signature.",
        "greet": "Demo: Generate a greeting with style (friendly, formal, casual).",
        "get_timestamp": "Demo: Returns current time. Useful for testing tool invocation.",
        "echo_message": "Demo: Echoes a message with optional repeat count.",
        "lookup_nist_control": "ISSO: Look up a NIST 800-53 Rev 5 control by ID (e.g., AC-2, SI-4). Returns family context and brief description.",
        "draft_poam_entry": "ISSO: Generate a POA&M entry template for a control finding. Input control ID, weakness description, and severity.",
        "draft_ssp_statement": "ISSO: Generate an SSP implementation statement template for a control. Optional: describe current implementation.",
        "control_evidence_guide": "ISSO: Suggest types of evidence to collect for demonstrating control implementation.",
        "risk_acceptance_template": "ISSO: Generate risk acceptance language for findings that cannot be remediated immediately.",
    }
    tools_html = ""
    for t in data["tools"]:
        name = t.get("name", str(t)) if isinstance(t, dict) else getattr(t, "name", str(t))
        desc = (t.get("description") or "") if isinstance(t, dict) else (getattr(t, "description", "") or "")
        inputs_html = _get_input_html(t)
        tip = TOOL_TIPS.get(name, "Each MCP tool is defined in igento_server.py with @mcp.tool(). The description and input schema help the AI understand how to call it.")
        tools_html += f"""
<div class="card">
  <h3>{html_lib.escape(name)}
    <span class="info-icon" tabindex="0" aria-label="Learn about this tool" title="Hover for tool context">?<span class="bubble">{html_lib.escape(tip)}</span></span>
  </h3>
  <p>{html_lib.escape(desc)}</p>
  <form method="post" action="/tool/{html_lib.escape(name)}" style="margin-top:0.5rem;">
    {inputs_html}
    <br><button type="submit">Invoke</button>
    <span class="info-icon" tabindex="0" aria-label="Learn about Invoke" title="Hover to learn how Invoke works">?<span class="bubble">
      <strong>Invoke</strong> sends a tools/call JSON-RPC request to the MCP server at localhost:2323. The bridge reads your form values, converts them to the tool's argument types, and displays the result.
    </span></span>
  </form>
</div>
"""

    resources_html = ""
    for r in data["resources"]:
        uri = r.get("uriTemplate") or r.get("uri") or str(r) if isinstance(r, dict) else getattr(r, "uriTemplate", None) or getattr(r, "uri", str(r))
        # For templates like igento://help/{topic}, link to common examples
        if "{topic}" in uri:
            links = []
            for label, val in [("tools", "tools"), ("concepts", "concepts")]:
                u = uri.replace("{topic}", val)
                links.append(f'<a href="/resource?uri={quote(u, safe="")}">{label}</a>')
            resources_html += f'<li>{html_lib.escape(uri)}: ' + " ".join(links) + "</li>"
        elif "{code}" in uri and "nist/family" in uri:
            links = []
            for label, val in [("AC", "AC"), ("AU", "AU"), ("IA", "IA"), ("SI", "SI"), ("RA", "RA")]:
                u = uri.replace("{code}", val)
                links.append(f'<a href="/resource?uri={quote(u, safe="")}">{label}</a>')
            resources_html += f'<li>{html_lib.escape(uri)}: ' + " ".join(links) + "</li>"
        else:
            resources_html += f'<li><a href="/resource?uri={quote(uri, safe="")}">{html_lib.escape(uri)}</a></li>'

    prompts_html = ""
    for p in data["prompts"]:
        name = p.get("name", str(p)) if isinstance(p, dict) else getattr(p, "name", str(p))
        prompts_html += f'<li>{html_lib.escape(name)}</li>'

    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head>
  <title>Igento - MCP Browser</title>
  <style>
    body {{ font-family: system-ui; max-width: 800px; margin: 2rem auto; padding: 1rem; }}
    h1 {{ color: #333; }}
    h2 {{ margin-top: 1.5rem; color: #555; }}
    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
    .card h3 {{ margin: 0 0 0.5rem 0; }}
    input {{ margin: 0.25rem; padding: 0.35rem; }}
    button {{ padding: 0.5rem 1rem; cursor: pointer; }}
    .result {{ background: #e8f5e9; padding: 1rem; border-radius: 8px; margin-top: 1rem; }}
    /* Teaching bubbles - hover/focus blue icons to see tips */
    .info-icon {{ display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px;
      background: #1976d2; color: white; border-radius: 50%; font-size: 12px; font-weight: bold; cursor: help;
      margin-left: 6px; position: relative; vertical-align: middle; line-height: 1; }}
    .info-icon .bubble {{ position: absolute; left: 50%; transform: translateX(-50%); bottom: 100%;
      margin-bottom: 8px; width: 260px; padding: 0.75rem 1rem; background: #1a1a2e; color: #eee;
      border-radius: 8px; font-size: 0.9rem; line-height: 1.4; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      opacity: 0; pointer-events: none; transition: opacity 0.2s; z-index: 100; }}
    .info-icon .bubble::after {{ content: ''; position: absolute; top: 100%; left: 50%;
      margin-left: -6px; border: 6px solid transparent; border-top-color: #1a1a2e; }}
    .info-icon:hover .bubble, .info-icon:focus .bubble {{ opacity: 1; }}
    .info-icon:focus {{ outline: 2px solid #2196f3; outline-offset: 2px; }}
    .section-header {{ display: flex; align-items: center; gap: 0.25rem; }}
  </style>
</head>
<body>
  <h1>Igento MCP Server</h1>
  <p>
    Tools, resources, and prompts translated for the browser.
    <span class="info-icon" tabindex="0" aria-label="Learn about MCP" title="Hover for MCP context">?<span class="bubble">
      <strong>What is this?</strong> This is the Igento Browser Bridge. It turns MCP (Model Context Protocol) definitions into a web UI. MCP lets AI assistants like Cursor or Claude connect to external tools and data in a standard way. What you see here is the same structure an AI sees when it connects to Igento.
    </span></span>
  </p>

  <h2 class="section-header">Tools
    <span class="info-icon" tabindex="0" aria-label="Learn about tools" title="Hover for tools context">?<span class="bubble">
      <strong>What are Tools?</strong> Tools are functions an AI can call—like API endpoints that do things. Each tool has a name, description, and typed inputs (from a JSON schema). When you click Invoke, the bridge sends a JSON-RPC request to the MCP server and displays the result. Try add_numbers with 5 and 7!
    </span></span>
  </h2>
  {tools_html}

  <h2 class="section-header">Resources
    <span class="info-icon" tabindex="0" aria-label="Learn about resources" title="Hover for resources context">?<span class="bubble">
      <strong>What are Resources?</strong> Resources are read-only data the AI can load into its context. Each has a URI (e.g. igento://info/about). The AI fetches them only when needed. Click a link to read the resource content—the bridge translates the MCP request into HTTP.
    </span></span>
  </h2>
  <ul>{resources_html}</ul>

  <h2 class="section-header">Prompts
    <span class="info-icon" tabindex="0" aria-label="Learn about prompts" title="Hover for prompts context">?<span class="bubble">
      <strong>What are Prompts?</strong> Prompts are reusable templates that structure AI interactions. They can take parameters (e.g. topic, depth) and return a prompt string. Great for consistent workflows like &quot;learn about X&quot; or &quot;debug tool Y&quot;.
    </span></span>
  </h2>
  <ul>{prompts_html}</ul>
</body>
</html>
""")


async def tool_invoke(request: Request):
    """Handle tool invocation POST."""
    name = request.path_params.get("name", "")
    if request.method != "POST":
        return RedirectResponse("/", status_code=303)
    form = await request.form()
    args = {}
    for k, v in form.items():
        if v and k != "submit":
            try:
                args[k] = int(v) if v.isdigit() else v
            except ValueError:
                args[k] = v
    result = await call_tool(name, args)
    if result.get("success"):
        res = result.get("result")
        content = res.get("content", []) if isinstance(res, dict) else (getattr(res, "content", None) or [])
        text = ""
        for c in content or []:
            t = c.get("text") if isinstance(c, dict) else getattr(c, "text", None)
            if t:
                text += t
        display = text or json.dumps(res, default=str, indent=2)
    else:
        display = f"Error: {result.get('error', 'Unknown')}"
    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head><title>Tool Result</title>
<style>body {{ font-family: system-ui; max-width: 600px; margin: 2rem auto; padding: 1rem; }}
.result {{ background: #e8f5e9; padding: 1rem; border-radius: 8px; }}
pre {{ white-space: pre-wrap; }}
.info-icon {{ display: inline-flex; align-items: center; justify-content: center; width: 1.1em; height: 1.1em;
  background: #2196f3; color: white; border-radius: 50%; font-size: 0.75em; font-weight: bold; cursor: help;
  margin-left: 0.35em; position: relative; vertical-align: middle; }}
.info-icon .bubble {{ position: absolute; left: 50%; transform: translateX(-50%); bottom: 100%;
  margin-bottom: 8px; width: 220px; padding: 0.75rem 1rem; background: #1a1a2e; color: #eee;
  border-radius: 8px; font-size: 0.9rem; line-height: 1.4; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  opacity: 0; pointer-events: none; transition: opacity 0.2s; z-index: 100; }}
.info-icon .bubble::after {{ content: ''; position: absolute; top: 100%; left: 50%;
  margin-left: -6px; border: 6px solid transparent; border-top-color: #1a1a2e; }}
.info-icon:hover .bubble, .info-icon:focus .bubble {{ opacity: 1; }}</style>
</head>
<body>
  <h2>Result: {html_lib.escape(name)}
    <span class="info-icon" tabindex="0" aria-label="Learn" title="Hover for result context">?<span class="bubble">
      <strong>Tool result</strong> The MCP server returned this. For tools, the result is typically a list of content blocks (text, images). The bridge extracts text for display. An AI would get the full structured response.
    </span></span>
  </h2>
  <div class="result"><pre>{html_lib.escape(display)}</pre></div>
  <p><a href="/">Back to Igento</a></p>
</body>
</html>
""")


async def resource_read(request: Request):
    """Read and display an MCP resource."""
    uri = unquote(request.query_params.get("uri", ""))
    if not uri:
        return RedirectResponse("/", status_code=303)
    result = await read_resource(uri)
    if result.get("success"):
        contents = result.get("contents", [])
        text = ""
        for c in contents or []:
            t = c.get("text") if isinstance(c, dict) else getattr(c, "text", None)
            if t:
                text += t
        display = text or "(empty)"
    else:
        display = f"Error: {result.get('error', 'Unknown')}"
    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head><title>Resource</title>
<style>body {{ font-family: system-ui; max-width: 700px; margin: 2rem auto; padding: 1rem; }}
pre {{ white-space: pre-wrap; background: #f5f5f5; padding: 1rem; border-radius: 8px; }}
.info-icon {{ display: inline-flex; align-items: center; justify-content: center; width: 1.1em; height: 1.1em;
  background: #2196f3; color: white; border-radius: 50%; font-size: 0.75em; font-weight: bold; cursor: help;
  margin-left: 0.35em; position: relative; vertical-align: middle; }}
.info-icon .bubble {{ position: absolute; left: 50%; transform: translateX(-50%); bottom: 100%;
  margin-bottom: 8px; width: 240px; padding: 0.75rem 1rem; background: #1a1a2e; color: #eee;
  border-radius: 8px; font-size: 0.9rem; line-height: 1.4; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  opacity: 0; pointer-events: none; transition: opacity 0.2s; z-index: 100; }}
.info-icon .bubble::after {{ content: ''; position: absolute; top: 100%; left: 50%;
  margin-left: -6px; border: 6px solid transparent; border-top-color: #1a1a2e; }}
.info-icon:hover .bubble, .info-icon:focus .bubble {{ opacity: 1; }}</style>
</head>
<body>
  <h2>Resource: {html_lib.escape(uri)}
    <span class="info-icon" tabindex="0" aria-label="Learn" title="Hover for resource context">?<span class="bubble">
      <strong>Resource content</strong> Resources are fetched via resources/read with the URI. The server returns text or blob content. The AI loads these only when needed—e.g. to answer a question about MCP tools.
    </span></span>
  </h2>
  <pre>{html_lib.escape(display)}</pre>
  <p><a href="/">Back to Igento</a></p>
</body>
</html>
""")


async def ping(request):
    """Quick health check - responds immediately without connecting to MCP."""
    return HTMLResponse("<h1>Igento Bridge OK</h1><p>Bridge is running. <a href='/'>Go to dashboard</a></p>")


def main():
    routes = [
        Route("/", home, methods=["GET"]),
        Route("/ping", ping),
        Route("/tool/{name}", tool_invoke, methods=["POST", "GET"]),
        Route("/resource", resource_read, methods=["GET"]),
    ]
    app = Starlette(debug=True, routes=routes)
    import uvicorn
    print(f"\nIgento Browser Bridge: http://localhost:{BRIDGE_PORT}")
    print("(Igento MCP must be running on http://localhost:2323)\n")
    uvicorn.run(app, host="0.0.0.0", port=BRIDGE_PORT)


if __name__ == "__main__":
    main()
