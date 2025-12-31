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
    postgresql-client \
    sqlite3 \
    libsqlite3-dev

# Install Node.js 20.x for AG-UI
echo "📦 Installing Node.js 20.x for AG-UI..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install pnpm globally for AG-UI
echo "📦 Installing pnpm for AG-UI..."
sudo npm install -g pnpm

# Verify Node.js and pnpm installation
echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"
echo "✅ pnpm version: $(pnpm --version)"

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

# Install AWS SDK and Web UI dependencies
echo "📦 Installing boto3 and Flask dependencies..."
pip install boto3>=1.34.0 flask>=2.3.0 flask-cors>=4.0.0

# Install database authentication dependencies (bcrypt for password hashing)
echo "📦 Installing database authentication dependencies..."
pip install bcrypt>=4.0.0

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

# Install Terraform CLI (for workflow execution)
echo "📦 Installing Terraform CLI..."
if ! command -v terraform &> /dev/null; then
    sudo apt-get install -y gnupg software-properties-common curl lsb-release || true
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg 2>/dev/null || true
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list > /dev/null
    sudo apt-get update -y && sudo apt-get install -y terraform
    echo "✅ Terraform installed: $(terraform -version | head -n1)"
else
    echo "✅ Terraform already installed: $(terraform -version | head -n1)"
fi

# Install Checkov (for security scanning)
echo "📦 Installing Checkov..."
if ! command -v checkov &> /dev/null; then
    pip install checkov || true
    echo "✅ Checkov installed: $(checkov --version 2>/dev/null || echo 'installed')"
else
    echo "✅ Checkov already installed: $(checkov --version 2>/dev/null || echo 'installed')"
fi

# Install MCP servers using uv tool install (adds to PATH)
echo "📦 Installing MCP servers via uv tool install..."
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
for server in awslabs.redshift-mcp-server awslabs.iam-mcp-server awslabs.terraform-mcp-server; do
    if ! command -v "$server" &> /dev/null; then
        echo "  Installing $server..."
        uv tool install "$server" 2>/dev/null || true
    else
        echo "  ✅ $server already installed"
    fi
done

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

# Build AG-UI if directory exists
if [ -d "/workspaces/sample-workflow/ag-ui" ]; then
    echo "📦 Installing AG-UI dependencies..."
    cd /workspaces/sample-workflow/ag-ui
    pnpm install || true
    echo "🔨 Building AG-UI..."
    pnpm build || echo "⚠️  AG-UI build completed with some warnings (this is normal for examples)"
    cd /workspaces/sample-workflow/servicenow-mcp
    source .venv/bin/activate
fi

# Install magic-mcp dependencies if directory exists
if [ -d "/workspaces/sample-workflow/magic-mcp" ]; then
    echo "📦 Installing magic-mcp dependencies..."
    cd /workspaces/sample-workflow/magic-mcp
    npm install || true
    npm run build || echo "⚠️  magic-mcp build completed with warnings"
    cd /workspaces/sample-workflow/servicenow-mcp
    source .venv/bin/activate
fi

# Install dbt (data build tool)
echo "📦 Installing dbt Fusion Engine..."
curl -fsSL https://public.cdn.getdbt.com/fs/install/install.sh | sh -s -- --update || true
echo "✅ dbt installed: $(~/.local/bin/dbt --version 2>/dev/null || echo 'not found')"

# Add dbt to PATH in bashrc if not already there
if ! grep -q '.local/bin' ~/.bashrc 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# Install 21st-dev CLI globally for Cline integration
echo "📦 Installing 21st-dev CLI for Cline..."
npm install -g @21st-dev/cli@latest || true

# Configure Cline with magic-mcp if API key is available
if [ -n "$MAGIC_API_KEY" ]; then
    echo "🔧 Configuring Cline with magic-mcp..."
    npx -y @21st-dev/cli@latest install cline --api-key "$MAGIC_API_KEY" --skip-restart || true
fi

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
