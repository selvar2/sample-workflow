# 📦 Dependency Management in DevContainer

This document explains how dependencies are automatically installed and managed in the ServiceNow MCP Workflow codespace.

## ✅ Automatic Dependency Installation

Dependencies are installed automatically in three phases:

### 1. **Post-Create** (First Time Container Creation)
```bash
postCreateCommand: "bash .devcontainer/setup.sh && bash .devcontainer/ensure-dependencies.sh"
```
**When**: Runs when the container is first created  
**What**: Sets up all system packages, Python virtualenv, Node.js, and project dependencies  
**Duration**: 5-10 minutes (first time only)

### 2. **Post-Start** (Every Time Container Starts)
```bash
postStartCommand: "bash .devcontainer/ensure-dependencies.sh && cd /workspaces/sample-workflow/servicenow-mcp && [...]"
```
**When**: Runs every time the container is restarted  
**What**: Ensures all dependencies are present and up-to-date  
**Duration**: 30 seconds - 2 minutes

### 3. **Post-Attach** (When You Connect to Container)
```bash
postAttachCommand: "bash .devcontainer/ensure-dependencies.sh && cd /workspaces/sample-workflow/servicenow-mcp && source .venv/bin/activate"
```
**When**: Runs when you connect to an existing container  
**What**: Verifies dependencies and activates Python virtualenv  
**Duration**: 10-30 seconds

## 🔄 What Gets Installed Automatically

### Python Virtual Environment
- Location: `/workspaces/sample-workflow/servicenow-mcp/.venv`
- Created automatically if missing
- Activated in all terminal sessions

### Python Dependencies
```
Core:
- mcp (Model Context Protocol SDK)
- requests, pydantic, starlette
- uvicorn, httpx

Web:
- flask, flask-cors
- python-dotenv

Database:
- bcrypt (password hashing)
- sqlite3

AWS:
- boto3 (AWS SDK)
```

### Node.js & NPM
- Version: Latest 20.x LTS
- Global: pnpm, @21st-dev/cli
- Projects: magic-mcp, ag-ui

### System Tools
- AWS CLI
- Docker CLI
- Git (pre-installed)
- SQLite3
- dbt (data build tool)

## 🚀 Quick Start (No Setup Required!)

```bash
# Everything is already installed! Just start coding:
cd /workspaces/sample-workflow/servicenow-mcp

# Python venv is auto-activated
python --version

# Or explicitly activate:
source .venv/bin/activate

# Start the Flask web UI:
python web_ui/app.py
```

## 🔍 Checking Dependency Status

Run at any time to verify all dependencies:
```bash
bash .devcontainer/ensure-dependencies.sh
```

Output shows:
- ✅ Installed packages
- ✅ Active virtualenv
- ✅ Database files
- ✅ Configuration status

## 📋 Manual Dependency Installation

If you need to manually install dependencies:

```bash
# Navigate to project
cd /workspaces/sample-workflow/servicenow-mcp

# Activate virtualenv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -e .

# Install additional packages
pip install python-dotenv boto3 flask flask-cors bcrypt
```

## 🔧 Environment Variables

These are set automatically in the devcontainer:

```
SERVICENOW_INSTANCE_URL    - From GitHub Codespaces secrets
SERVICENOW_USERNAME         - From GitHub Codespaces secrets
SERVICENOW_PASSWORD         - From GitHub Codespaces secrets
AWS_ACCESS_KEY_ID          - From GitHub Codespaces secrets
AWS_SECRET_ACCESS_KEY      - From GitHub Codespaces secrets
AWS_DEFAULT_REGION         - us-east-1 (default)
MAGIC_API_KEY              - From GitHub Codespaces secrets
FASTMCP_LOG_LEVEL          - INFO (default)
```

**To set secrets in GitHub Codespaces:**
1. Go to Settings → Codespaces → Secrets
2. Add your credentials
3. Click "Save"
4. Restart the codespace

## 🛠️ Building & Pre-Building

### Pre-Build Configuration
The `.devcontainer/devcontainer.json` includes optimizations for faster builds:

1. **Features** - Pre-installed:
   - AWS CLI (via feature)
   - Docker in Docker (via feature)
   - Git (via feature)

2. **Customizations**:
   - VS Code extensions pre-configured
   - Python interpreter pre-configured
   - Terminal auto-activation

### Build Times
- **Initial Build**: 5-10 minutes
- **Rebuild**: 1-2 minutes
- **Start/Attach**: 30 seconds - 2 minutes

## 📦 Adding New Dependencies

When adding new Python packages:

### Option 1: In pyproject.toml (Recommended)
```toml
[project]
dependencies = [
    "requests>=2.28.0",
    "your-new-package>=1.0.0",
]
```

Then reinstall:
```bash
pip install -e .
```

### Option 2: Direct Installation
```bash
pip install your-new-package
```

The dependency will be preserved if you:
- Save to `requirements.txt`
- Add to `setup.py` or `pyproject.toml`

## 🚨 Troubleshooting

### Virtual Environment Not Activated
```bash
# Solution: Manually activate
source /workspaces/sample-workflow/servicenow-mcp/.venv/bin/activate
```

### Dependencies Missing After Restart
```bash
# Solution: Reinstall
bash .devcontainer/ensure-dependencies.sh
```

### Python Wrong Version
```bash
# Verify
python --version  # Should be 3.12

# Check virtualenv
which python  # Should be in .venv/bin
```

### Port Forwarding Not Working
Ports 5000 (Flask), 8000, and 3000 are automatically forwarded.  
If not visible: Settings → Ports → Check if forwarding is enabled.

## 📚 Additional Resources

- [setup.sh](setup.sh) - Initial setup script
- [ensure-dependencies.sh](ensure-dependencies.sh) - Dependency checker
- [MCP_ARCHITECTURE.md](MCP_ARCHITECTURE.md) - MCP server details
- [README.md](README.md) - General devcontainer info

## ✨ Summary

✅ **Dependencies are installed automatically**
- No manual setup required
- Runs on: create, start, and attach
- Fast and reliable
- Includes Python, Node.js, AWS tools

✅ **Virtual environment is auto-activated**
- Python virtualenv ready to use
- No need to manually activate
- Activates in all terminal sessions

✅ **Ready to code immediately**
- Open the codespace
- Start developing
- No setup delays

---

**Dependencies management is fully automated!** Just code! 🚀
