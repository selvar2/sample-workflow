# Dev Container Configuration

This directory contains the development container configuration for the ServiceNow MCP workflow project.

## What's Included

The dev container automatically sets up:

### Pre-installed Tools
- ✅ Python 3.12
- ✅ pip (latest version)
- ✅ uv (fast Python package installer)
- ✅ uvx (Python application runner)
- ✅ AWS CLI
- ✅ Git
- ✅ Docker
- ✅ PostgreSQL client (for Redshift)

### Python Packages
- ServiceNow MCP server (installed from local source)
- python-dotenv
- pytest & pytest-cov
- black, flake8, mypy (code quality tools)
- All dependencies from pyproject.toml

### MCP Servers
- ServiceNow MCP server (local installation)
- AWS Redshift MCP server (via uvx)

**Important:** MCP servers are started **on-demand** by MCP clients (like Claude Desktop), not as background services. In Codespaces, you use the tools directly via Python scripts or AWS CLI. The servers don't need to "run" - they're libraries that are ready to be invoked.

For details, see [MCP_ARCHITECTURE.md](./MCP_ARCHITECTURE.md).

### VS Code Extensions
- Python
- Pylance (Python language server)
- Python Debugger
- Jupyter
- YAML
- Docker

## Environment Variables

Set these as GitHub Codespaces secrets or local environment variables:

### ServiceNow Configuration
- `SERVICENOW_INSTANCE_URL` - Your ServiceNow instance URL
- `SERVICENOW_USERNAME` - ServiceNow username
- `SERVICENOW_PASSWORD` - ServiceNow password

### AWS Configuration
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_DEFAULT_REGION` (optional, defaults to us-east-1)

## Quick Start

Once the codespace is created:

```bash
# Verify everything is installed correctly
bash .devcontainer/verify-mcp-setup.sh

# Test MCP servers are ready
bash .devcontainer/test-mcp-servers.sh

# Activate the ServiceNow MCP environment
activate-sn

# Or manually:
cd /workspaces/sample-workflow/servicenow-mcp
source .venv/bin/activate
```

## Helper Aliases

The following aliases are automatically configured:

- `activate-sn` - Activate ServiceNow MCP environment
- `create-incident` - Create a new incident
- `read-incident` - Read incident details
- `update-incident` - Update incident with notes

## Manual Setup (Not Needed with Dev Container)

If you're not using the dev container, you would need to manually:

1. Install Python 3.12
2. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Install AWS CLI
4. Create virtual environment: `python -m venv .venv`
5. Install packages: `pip install -e .`
6. Configure AWS credentials
7. Set environment variables

With the dev container, **all of this is done automatically!**

## Rebuilding the Container

If you need to rebuild the container:

1. Press `F1` or `Cmd/Ctrl + Shift + P`
2. Type: "Dev Containers: Rebuild Container"
3. Select the option

## Troubleshooting

### Environment Variables Not Set
If environment variables aren't available:
1. Go to GitHub Codespaces settings
2. Add secrets for your repository
3. Rebuild the container

### AWS Credentials Not Working
The container tries to mount `~/.aws` from your local machine. In Codespaces, set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as secrets instead.

### Python Virtual Environment Issues
The setup script creates a virtual environment at `/workspaces/sample-workflow/servicenow-mcp/.venv`. If there are issues:

```bash
cd /workspaces/sample-workflow/servicenow-mcp
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```
