# Why MCP Servers Don't Need to "Start" in Codespaces

## The Question
"Should the ServiceNow MCP server be started and running in my Codespace?"

## The Answer
**No!** And here's why:

## Understanding MCP Architecture

### What is an MCP Server?

MCP (Model Context Protocol) servers are **libraries with a standardized communication protocol**, not traditional web services or daemons.

Think of them like this:
- **Traditional Web Server**: Runs 24/7, listens on a port, serves HTTP requests
- **MCP Server**: A Python module that communicates via **stdin/stdout** when invoked

### How MCP Servers Communicate

```
MCP Server Communication:
┌─────────────────┐
│   MCP Client    │  (e.g., Claude Desktop)
│  (Controller)   │
└────────┬────────┘
         │ stdio (stdin/stdout)
         │ JSON-RPC messages
         ▼
┌─────────────────┐
│   MCP Server    │  (e.g., servicenow_mcp)
│   (Responder)   │
└─────────────────┘
```

The server:
1. Reads JSON-RPC requests from **stdin**
2. Processes the request
3. Writes JSON-RPC response to **stdout**
4. Exits when stdio closes

**Without an MCP client sending requests via stdin, the server has nothing to do and will exit!**

## Different Contexts

### Context 1: Claude Desktop (Your Local Machine)

**Configuration File:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "servicenow": {
      "command": "/path/to/python",
      "args": ["-m", "servicenow_mcp.server"],
      "env": { ... }
    }
  }
}
```

**What Happens:**
1. You ask Claude: "Create a ServiceNow incident"
2. Claude **starts** the MCP server process: `python -m servicenow_mcp.server`
3. Claude **sends** JSON-RPC request via stdin: `{"method": "create_incident", ...}`
4. Server **processes** request, **returns** result via stdout
5. Claude **stops** the server process
6. Claude shows you the result

**Duration:** Seconds. Server runs only when needed.

### Context 2: GitHub Codespaces (Development Environment)

**No MCP Client Running!**

In Codespaces, you don't have Claude Desktop or another MCP client. So:

❌ Starting `python -m servicenow_mcp.server` as background service = **USELESS**
   - No client to send stdin requests
   - Process will exit immediately or hang waiting for stdin
   - Can't communicate via HTTP (it uses stdio!)

✅ Calling tools directly via Python = **CORRECT**
```python
from servicenow_mcp.tools.incident_tools import create_incident
result = create_incident(config, auth_manager, params)
```

## What the Setup Script Does

Our `setup.sh` does:

```bash
# 1. Install the MCP server package
pip install -e /workspaces/sample-workflow/servicenow-mcp

# 2. Verify it CAN be invoked
python -m servicenow_mcp.cli --help  # Quick test, exits immediately

# 3. DOES NOT start it as a service
# (because that doesn't make sense!)
```

## Why We Created Start Scripts

The `start-mcp-servers-background.sh` script exists for:
- **Educational purposes** - to show why it doesn't work
- **Testing/debugging** - if you want to experiment
- **Verification** - that the module can be imported

**But it explicitly warns you this isn't how MCP works!**

## The Right Way to Use MCP Tools in Codespaces

### ServiceNow Operations
```bash
# Direct Python script (already configured)
python create_incident.py
python read_incident.py INC0010009
python update_incident.py
```

These scripts call the ServiceNow tools **directly as Python functions**, not via MCP protocol.

### AWS Redshift Operations
```bash
# AWS CLI (same API as Redshift MCP server uses)
aws redshift-data execute-statement \
  --cluster-identifier redshift-cluster-1 \
  --sql "CREATE USER user7"
```

## Summary Table

| Context | MCP Client? | How to Use | Server Running? |
|---------|-------------|-----------|-----------------|
| **Claude Desktop** | ✅ Yes | Natural language | On-demand (seconds) |
| **Codespaces** | ❌ No | Python scripts | No (not needed) |
| **Background Script** | ❌ No | N/A | Exits immediately |

## Conclusion

**MCP servers in Codespaces:**
- ✅ **Installed** - Yes, package is installed
- ✅ **Ready** - Yes, can be imported and used
- ❌ **Running** - No, and they don't need to be!

The architecture is **working as designed**. You're using the tools correctly by calling them directly via Python scripts.

## If You Still Want to Test

If you really want to see the MCP server in action:

1. **Install Claude Desktop on your local machine**
2. **Copy the config** from `servicenow-mcp/claude_desktop_config.json`
3. **Update paths** to point to your local installation
4. **Restart Claude Desktop**
5. **Ask Claude** to create incidents - the server will start/stop automatically!

That's the environment where MCP servers are meant to run.
