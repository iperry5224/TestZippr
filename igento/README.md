# Igento – MCP Learning App

Igento is a small Model Context Protocol (MCP) server for learning MCP concepts. It exposes **tools**, **resources**, and **prompts** you can try from Cursor or Claude.

## What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io) lets AI assistants connect to external data and tools in a standard way:

| Concept | What it does |
|--------|----------------|
| **Tools** | Functions the AI can call (e.g., add numbers, greet someone) |
| **Resources** | URI-addressable data the AI can load (e.g., help docs) |
| **Prompts** | Reusable templates for common workflows |

## Setup

```powershell
cd igento
pip install -r requirements.txt
```

## Running the server

For Cursor/Claude Desktop, you normally don't run the server yourself – the client spawns it when needed. To run it manually (e.g., for debugging):

```powershell
python igento_server.py
```

The server uses **stdio** (stdin/stdout) for communication. It will wait for a client to connect.

## Add Igento to Cursor

1. Open **Cursor Settings** → **MCP** (or edit `%USERPROFILE%\.cursor\mcp.json` on Windows).
2. Add the Igento server. You can copy from `cursor-mcp-config.example.json` in this folder:

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

If you have other MCP servers, merge the `igento` entry into your existing `mcpServers` object.

3. Restart Cursor or reload MCP. Igento will appear under MCP servers.

**Tip:** Use absolute paths. Set `cwd` to the `igento` folder so imports work.

## Try it in Cursor

Once Igento is configured, you can ask:

- **"Use the add_numbers tool with 7 and 13"**
- **"Greet Alice in formal style"**
- **"What time is it according to Igento?"**
- **"Read the help for igento://help/tools"**

## Test with MCP Inspector

For standalone testing without Cursor:

1. Start the server in one terminal:
   ```powershell
   cd igento
   python igento_server.py
   ```

2. Use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) to connect over stdio, or run the server with HTTP:
   ```powershell
   python igento_server.py --transport streamable-http
   ```
   Then connect to `http://localhost:8000/mcp` in the inspector.

## Server contents

### Tools

| Tool | Description |
|------|-------------|
| `add_numbers` | Add two integers |
| `greet` | Generate a greeting (friendly, formal, or casual) |
| `get_timestamp` | Return current date/time |
| `echo_message` | Echo a message back (with optional repeat) |

### Resources

| URI | Description |
|-----|-------------|
| `igento://info/about` | About Igento and MCP |
| `igento://help/{topic}` | Help on tools, resources, prompts, or concepts |

### Prompts

| Prompt | Description |
|--------|-------------|
| `learn_mcp` | Generate a prompt to learn about an MCP topic |
| `debug_tool` | Create a debugging prompt when a tool fails |

## Learn more

- [MCP Specification](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
