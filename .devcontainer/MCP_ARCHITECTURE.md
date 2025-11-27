# MCP Server Architecture in Codespaces

## Understanding MCP Servers

**Model Context Protocol (MCP)** servers are designed to be **started on-demand** by MCP clients, not as persistent background services.

## How MCP Servers Work

### 🖥️ In Claude Desktop (Local Machine)
```
┌──────────────┐
│ Claude       │
│ Desktop      │ ──┬──> Starts ServiceNow MCP Server when needed
│              │   │    (Python process)
│              │   │
│              │   └──> Starts Redshift MCP Server when needed
└──────────────┘        (uvx auto-downloads and runs)
```

**Configuration:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Claude Desktop:
1. Reads the config file
2. **Automatically starts** MCP servers when you ask questions
3. **Automatically stops** them when done
4. Manages server lifecycle completely

### ☁️ In GitHub Codespaces (This Environment)
```
┌──────────────┐
│ Developer    │
│ (You)        │ ──┬──> Calls Python scripts directly
│              │   │    (create_incident.py, etc.)
│              │   │
│              │   └──> Calls AWS CLI directly
└──────────────┘        (aws redshift-data ...)
```

**Why?** MCP clients like Claude Desktop aren't running in Codespaces, so we call the tools directly via Python scripts.

## Current Codespaces Setup

### ✅ What's Automatically Installed

When you open a new Codespace, the dev container automatically:

1. **Python 3.12** - Pre-installed
2. **ServiceNow MCP Package** - Installed in `.venv`
3. **uv & uvx** - Python package managers
4. **AWS CLI** - Ready to use
5. **Environment Variables** - Set from GitHub secrets

### 🚀 What Happens on Startup

The `.devcontainer/setup.sh` script runs automatically and:

```bash
# 1. Installs uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Creates Python virtual environment
python3 -m venv .venv

# 3. Installs ServiceNow MCP
pip install -e /workspaces/sample-workflow/servicenow-mcp

# 4. Configures AWS credentials
# (from GitHub Codespaces secrets)

# 5. Installs Redshift MCP server package metadata
# (actual installation happens on first uvx invocation)
```

## Do MCP Servers Need to "Run" in Codespaces?

**No!** They don't need to run as background services because:

### ServiceNow MCP
- **Installed**: ✅ Package is installed in `.venv`
- **Running**: ❌ Not started as a service
- **How to use**: Call Python functions directly

```python
# This is how you use it in Codespaces
from servicenow_mcp.tools.incident_tools import create_incident
result = create_incident(config, auth_manager, params)
```

### Redshift MCP  
- **Installed**: ✅ uvx knows where to get it
- **Running**: ❌ Not started as a service
- **How to use**: Use AWS CLI directly (same underlying API)

```bash
# This is how you use it in Codespaces
aws redshift-data execute-statement \
  --cluster-identifier redshift-cluster-1 \
  --sql "CREATE USER user7"
```

## Verification Scripts

I've created scripts to verify everything is ready:

### Check Installation Status
```bash
bash .devcontainer/verify-mcp-setup.sh
```

This checks:
- ✓ Python installed
- ✓ uv/uvx installed
- ✓ AWS CLI installed
- ✓ ServiceNow MCP package installed
- ✓ Environment variables set
- ✓ AWS credentials working
- ✓ MCP server modules can be imported

### Test MCP Server Readiness
```bash
bash .devcontainer/test-mcp-servers.sh
```

This verifies:
- ✓ ServiceNow MCP module loads
- ✓ Redshift MCP can be invoked via uvx
- ✓ All dependencies are available

## Using MCP Servers in Different Contexts

### 📝 Context 1: GitHub Codespaces (You're Here)

**Purpose:** Development and testing

**Method:** Direct Python/CLI calls
```bash
# ServiceNow operations
python create_incident.py
python read_incident.py INC0010009

# Redshift operations
aws redshift-data execute-statement ...
```

**MCP Servers:** Don't need to run as services

---

### 🖥️ Context 2: Claude Desktop (Your Local Machine)

**Purpose:** AI-assisted automation

**Method:** Natural language → MCP servers
```
You: "Create a ServiceNow incident for adding a database user"
Claude: [starts ServiceNow MCP server, calls create_incident tool, stops server]
```

**MCP Servers:** Started automatically by Claude

**Setup:**
1. Copy `servicenow-mcp/claude_desktop_config.json` to:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
2. Update paths to point to your local installation
3. Restart Claude Desktop

---

## Summary

✅ **Installation**: Fully automated in dev container  
✅ **Configuration**: Environment variables from GitHub secrets  
✅ **Ready to Use**: Scripts work immediately in Codespaces  
❌ **Background Services**: Not needed (and not how MCP works)  
✅ **Verification**: Scripts to test everything is ready  

## Next Steps

1. **Verify Setup**:
   ```bash
   bash .devcontainer/verify-mcp-setup.sh
   ```

2. **Test Everything Works**:
   ```bash
   cd /workspaces/sample-workflow/servicenow-mcp
   source .venv/bin/activate
   python create_incident.py
   ```

3. **For Claude Desktop Integration** (optional):
   - See `servicenow-mcp/claude_desktop_config.json`
   - Copy to Claude's config location on your local machine
   - Servers will auto-start when Claude needs them

The key insight: **MCP servers are libraries with a protocol interface**, not services that need to be running. In Codespaces, you use them as libraries. In Claude Desktop, the MCP client manages their lifecycle.
