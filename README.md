# ServiceNow & AWS Redshift Workflow Automation

This repository demonstrates automated workflows using ServiceNow MCP (Model Context Protocol) server and AWS Redshift MCP server for incident-driven database management tasks.

## Features

- 🎫 **ServiceNow Integration** - Create, read, and update incidents programmatically
- 🗄️ **AWS Redshift Integration** - Execute database operations via MCP server
- 🤖 **Automated Workflows** - End-to-end automation from incident creation to task completion
- 🐳 **Dev Container Ready** - Zero-configuration development environment
- ✅ **Auto-Verification** - Scripts to verify installation on codespace startup

**Note:** MCP servers are started on-demand by MCP clients (like Claude Desktop), not as background services. In Codespaces, you use the tools directly via Python scripts. See [MCP Architecture](.devcontainer/MCP_ARCHITECTURE.md) for details.

## Quick Start

### Prerequisites

Set up GitHub Codespaces secrets (see `.devcontainer/SECRETS_SETUP.md`):
- `SERVICENOW_INSTANCE_URL`
- `SERVICENOW_USERNAME`
- `SERVICENOW_PASSWORD`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Using GitHub Codespaces (Recommended)

1. Click "Code" → "Codespaces" → "Create codespace on main"
2. Wait for automatic setup to complete (~2-3 minutes)
3. Verification runs automatically - everything is pre-installed and ready!

```bash
# Verify installation (runs automatically on setup)
bash .devcontainer/verify-mcp-setup.sh

# Test MCP servers are ready
bash .devcontainer/test-mcp-servers.sh

# Activate the environment (already done by default)
activate-sn

# Run example workflows
python create_incident.py
python read_incident.py INC0010009
```

### Local Development (Manual Setup)

If not using Codespaces, you'll need to manually install:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
cd servicenow-mcp
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
pip install python-dotenv

# Configure AWS
aws configure

# Create .env file
cat > .env << EOF
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password
AWS_DEFAULT_REGION=us-east-1
EOF
```

## Example Workflow

This repository includes a complete example workflow:

### Task 1: Create ServiceNow Incident
```bash
python create_incident.py
```
Creates incident requesting database user creation in Redshift cluster.

**Output:**
```
✓ Incident created successfully!
  Incident Number: INC0010009
  Incident ID: 7b86f994c3a1f2104eb2f5fc0501316d
```

### Task 2: Read Incident Details
```bash
python read_incident.py INC0010009
```
Retrieves and displays incident information.

**Output:**
```
✓ Incident INC0010009 found!
  Short Description: Add database user for redshift cluster
  Description: Create database user named user7 with password disable in redshift cluster 1
  State: New
```

### Task 3: Execute Database Task
Uses AWS Redshift MCP server to create the database user:
```bash
aws redshift-data execute-statement \
  --cluster-identifier redshift-cluster-1 \
  --database dev \
  --db-user awsuser \
  --sql "CREATE USER user7 PASSWORD DISABLE;"
```

### Task 4: Update Incident with Results
```bash
python update_incident.py
```
Adds work notes to the incident documenting task completion.

## Project Structure

```
.
├── .devcontainer/              # Dev container configuration
│   ├── devcontainer.json      # Container setup
│   ├── setup.sh               # Automated installation script
│   ├── README.md              # Dev container docs
│   └── SECRETS_SETUP.md       # GitHub Codespaces secrets guide
├── servicenow-mcp/            # ServiceNow MCP server
│   ├── src/                   # Source code
│   ├── tools/                 # MCP tools
│   ├── examples/              # Example scripts
│   ├── create_incident.py     # Create incident script
│   ├── read_incident.py       # Read incident script
│   └── update_incident.py     # Update incident script
└── README.md                  # This file
```

## Dev Container Benefits

With the included dev container configuration, you get:

✅ **Pre-installed Tools**
- Python 3.12
- uv & uvx (fast package managers)
- AWS CLI
- Git & Docker

✅ **Pre-configured Environment**
- Virtual environment created automatically
- ServiceNow MCP server installed
- AWS Redshift MCP server ready
- All dependencies installed

✅ **Helper Commands**
- `activate-sn` - Activate ServiceNow environment
- `create-incident` - Quick incident creation
- `read-incident` - Read incident details
- `update-incident` - Update incidents

✅ **VS Code Extensions**
- Python & Pylance
- Jupyter
- Docker
- YAML support

## Environment Variables

The following environment variables are required:

### ServiceNow
- `SERVICENOW_INSTANCE_URL` - Your ServiceNow instance URL
- `SERVICENOW_USERNAME` - ServiceNow username
- `SERVICENOW_PASSWORD` - ServiceNow password
- `SERVICENOW_AUTH_TYPE` - Authentication type (default: `basic`)

### AWS
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key
- `AWS_DEFAULT_REGION` - AWS region (default: `us-east-1`)
- `AWS_PROFILE` - AWS profile (default: `default`)

### MCP Server
- `FASTMCP_LOG_LEVEL` - Logging level (default: `INFO`)

## ServiceNow MCP Server

For detailed documentation about the ServiceNow MCP server capabilities:
- See `servicenow-mcp/README.md`
- Available tools: incident management, user management, change management, workflows, and more
- Full API documentation in `servicenow-mcp/docs/`

## AWS Redshift Integration

The workflow uses AWS Redshift Data API to execute SQL statements:
- Create database users
- Manage permissions
- Execute queries
- No direct database connection required

## Troubleshooting

### Dev Container Issues
See `.devcontainer/README.md` for detailed troubleshooting.

### Environment Variables Not Set
1. Check GitHub Codespaces secrets are configured
2. Rebuild the container: `F1` → "Codespaces: Rebuild Container"

### AWS Credentials Not Working
```bash
aws configure list  # Verify credentials
aws sts get-caller-identity  # Test authentication
```

### ServiceNow Connection Failed
```bash
echo $SERVICENOW_INSTANCE_URL  # Verify URL is set
curl -u $SERVICENOW_USERNAME:$SERVICENOW_PASSWORD $SERVICENOW_INSTANCE_URL/api/now/table/incident?sysparm_limit=1
```

## Contributing

This is a demonstration repository. Feel free to use it as a template for your own ServiceNow and AWS integration projects.

## License

See `servicenow-mcp/LICENSE` for details.

## Documentation

- 📚 [Dev Container Setup](.devcontainer/README.md)
- 🔐 [GitHub Codespaces Secrets Setup](.devcontainer/SECRETS_SETUP.md)
- 📖 [ServiceNow MCP Documentation](servicenow-mcp/README.md)
- 📝 [Incident Management](servicenow-mcp/docs/incident_management.md)
- 👥 [User Management](servicenow-mcp/docs/user_management.md)
- 🔄 [Workflow Management](servicenow-mcp/docs/workflow_management.md)