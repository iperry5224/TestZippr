# Add Igento to Cursor - Step-by-Step

## Prerequisites
- Igento running locally: `run igento` (or `python igento_server.py --transport streamable-http --port 2323`)
- Server must be at **http://localhost:2323**

## Browser-Friendly UI

**Quick start:** Run `run igento` (from the project root) or `.\run_igento.ps1` (from the igento folder). This starts both Igento and the browser bridge, then opens **http://localhost:8080**.

To view Igento in a web browser (HTML instead of raw MCP):
1. Run: `run igento` (or `.\run.cmd igento` from the TestZippr folder)
2. Your browser opens to **http://localhost:8080**

The bridge translates MCP tools, resources, and prompts into HTML and lets you invoke tools from the browser.

**Troubleshooting:** If port 8080 or 2323 is in use, the script will stop the existing process first. If the bridge shows "Connection timed out", ensure Igento is running on port 2323.

---

## Method 1: Cursor Settings UI

1. **Open Cursor Settings**
   - Press `Ctrl + ,` (Control + comma)
   - Or click the gear icon in the bottom-left → **Cursor Settings**

2. **Go to MCP**
   - In the left sidebar, find **Features** or **Cursor**
   - Click **MCP** (or **Model Context Protocol**)

3. **Add a new server**
   - Click **+ Add new MCP server** or **Add server**
   - Choose **HTTP** or **URL** as the transport (if available)

4. **Enter Igento details**
   - **Name:** `igento`
   - **URL:** `http://localhost:2323/mcp`

5. **Save** and restart Cursor or reload the window

---

## Method 2: Edit mcp.json directly

1. **Open the config file**
   - Press `Ctrl + Shift + P` (Command Palette)
   - Type: `Open User Settings (JSON)` or find the MCP config
   - Or open: `C:\Users\iperr\.cursor\mcp.json`
   - If the file doesn't exist, create it

2. **Paste this JSON** (create or merge into your config):

```json
{
  "mcpServers": {
    "igento": {
      "url": "http://localhost:2323/mcp"
    }
  }
}
```

If you have other servers, add the `"igento"` block inside `mcpServers`:

```json
{
  "mcpServers": {
    "other-server": { ... },
    "igento": {
      "url": "http://localhost:2323/mcp"
    }
  }
}
```

3. **Save** the file

4. **Reload Cursor**
   - `Ctrl + Shift + P` → type `Reload Window` → Enter

---

## Method 3: STDIO (starts Igento automatically)

If the HTTP URL format doesn't work, use STDIO. Cursor will start Igento when needed:

```json
{
  "mcpServers": {
    "igento": {
      "command": "python",
      "args": ["C:\\Users\\iperr\\TestZippr\\igento\\igento_server.py"],
      "cwd": "C:\\Users\\iperr\\TestZippr\\igento"
    }
  }
}
```

This runs Igento in stdio mode (not HTTP). You don't need to run `run igento` separately.

---

## Verify

1. After config, open the **Chat** or **Composer** panel
2. Look for **Igento** in the MCP/tools section
3. Try: *"Use Igento's add_numbers tool with 5 and 7"*
