#!/bin/bash
set -e

echo "🚀 Starting dev container setup..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install essential tools
echo "🔧 Installing essential tools..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    jq \
    tree \
    vim \
    less \
    postgresql-client

# Install uv (Python package installer)
echo "📦 Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Verify uv installation
if command -v uv &> /dev/null; then
    echo "✅ uv installed successfully: $(uv --version)"
else
    echo "❌ Failed to install uv"
    exit 1
fi

# Install uvx (if not already included with uv)
if ! command -v uvx &> /dev/null; then
    echo "📦 Installing uvx..."
    # uvx is typically included with uv, but we can symlink if needed
    ln -sf ~/.cargo/bin/uv ~/.cargo/bin/uvx || true
fi

# Navigate to servicenow-mcp directory
cd /workspaces/sample-workflow/servicenow-mcp

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
SERVICENOW_INSTANCE_URL=${SERVICENOW_INSTANCE_URL}
SERVICENOW_USERNAME=${SERVICENOW_USERNAME}
SERVICENOW_PASSWORD=${SERVICENOW_PASSWORD}
SERVICENOW_AUTH_TYPE=basic
AWS_PROFILE=default
AWS_DEFAULT_REGION=us-east-1
FASTMCP_LOG_LEVEL=INFO
EOF
fi

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -e .

# Install additional dependencies
echo "📦 Installing additional Python packages..."
pip install python-dotenv pytest pytest-cov black flake8 mypy

# Ensure python-dotenv is installed (critical dependency)
echo "📦 Verifying python-dotenv installation..."
pip install --upgrade python-dotenv
pip show python-dotenv

# Install AWS CLI (if not already installed via feature)
if ! command -v aws &> /dev/null; then
    echo "📦 Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Configure AWS if credentials are available
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "🔐 Configuring AWS credentials..."
    mkdir -p ~/.aws
    cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF
    
    cat > ~/.aws/config << EOF
[default]
region = us-east-1
output = json
EOF
    chmod 600 ~/.aws/credentials
fi

# Install Redshift MCP server using uvx
echo "📦 Installing Redshift MCP server..."
~/.cargo/bin/uvx awslabs.redshift-mcp-server@latest --help || true

# Create helper aliases
echo "🔗 Creating helper aliases..."
cat >> ~/.bashrc << 'EOF'

# ServiceNow MCP aliases
alias activate-sn='cd /workspaces/sample-workflow/servicenow-mcp && source .venv/bin/activate'
alias create-incident='cd /workspaces/sample-workflow/servicenow-mcp && .venv/bin/python create_incident.py'
alias read-incident='cd /workspaces/sample-workflow/servicenow-mcp && .venv/bin/python read_incident.py'
alias update-incident='cd /workspaces/sample-workflow/servicenow-mcp && .venv/bin/python update_incident.py'

# Add uv to PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Auto-activate virtual environment when in servicenow-mcp directory
cd /workspaces/sample-workflow/servicenow-mcp && source .venv/bin/activate
EOF

# Set up git configuration (if not already configured)
if [ -z "$(git config --global user.email)" ]; then
    git config --global user.email "user@example.com"
    git config --global user.name "DevContainer User"
fi

# Final verification
echo ""
echo "✅ Dev container setup complete!"
echo ""
echo "📋 Installed tools:"
echo "  - Python: $(python --version)"
echo "  - pip: $(pip --version)"
echo "  - uv: $(~/.cargo/bin/uv --version || echo 'not found')"
echo "  - AWS CLI: $(aws --version 2>&1 | head -n1 || echo 'not found')"
echo "  - Git: $(git --version)"
echo ""
echo "🎯 ServiceNow MCP server installed at: /workspaces/sample-workflow/servicenow-mcp"
echo "🎯 Virtual environment: /workspaces/sample-workflow/servicenow-mcp/.venv"
echo ""
echo "💡 Quick commands:"
echo "  - activate-sn      : Activate ServiceNow MCP environment"
echo "  - create-incident  : Create a new incident"
echo "  - read-incident    : Read incident details"
echo "  - update-incident  : Update incident with notes"
echo ""
echo "🚀 Ready to go! Run 'activate-sn' to start working."
echo ""

# Run verification
echo "🔍 Running installation verification..."
echo ""
bash /workspaces/sample-workflow/.devcontainer/verify-mcp-setup.sh

echo ""
echo "================================================"
echo "ℹ️  MCP Server Information"
echo "================================================"
echo ""
echo "MCP servers are installed and ready but NOT running as services."
echo "This is by design - MCP servers are started on-demand by MCP clients."
echo ""
echo "📖 For details, see: .devcontainer/MCP_ARCHITECTURE.md"
echo ""
echo "🧪 If you need to start servers for testing/debugging:"
echo "   bash .devcontainer/start-mcp-servers-background.sh"
echo ""
echo "🛑 To stop background servers:"
echo "   bash .devcontainer/stop-mcp-servers.sh"
echo ""
