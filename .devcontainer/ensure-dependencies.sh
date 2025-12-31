#!/bin/bash
# Script to ensure all ServiceNow MCP dependencies are installed
# This can be run manually or automatically on codespace start
# Call this script in: postCreateCommand, postStartCommand, postAttachCommand
# Usage: bash .devcontainer/ensure-dependencies.sh

set -e

VENV_PATH="/workspaces/sample-workflow/servicenow-mcp/.venv"
PROJECT_PATH="/workspaces/sample-workflow/servicenow-mcp"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔍 Checking ServiceNow MCP dependencies..."
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "📦 Creating virtual environment..."
    cd "$PROJECT_PATH"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e .
    echo "✅ Virtual environment created and dependencies installed"
    exit 0
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Check if python-dotenv is installed
if ! python -c "import dotenv" 2>/dev/null; then
    echo "❌ python-dotenv not found"
    echo "📦 Installing dependencies..."
    cd "$PROJECT_PATH"
    pip install --upgrade pip
    pip install -e .
    echo "✅ Dependencies installed"
else
    echo "✅ python-dotenv is installed"
fi

# Check if all required packages are installed
echo "🔍 Verifying all dependencies..."
MISSING=0

for package in "mcp" "requests" "pydantic" "dotenv" "starlette" "uvicorn" "httpx" "yaml" "bcrypt" "sqlite3" "flask"; do
    if ! python -c "import $package" 2>/dev/null; then
        echo "❌ Missing package: $package"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo "📦 Reinstalling all dependencies..."
    cd "$PROJECT_PATH"
    pip install --upgrade pip
    pip install -e .
    pip install bcrypt flask flask-cors boto3
    echo "✅ All dependencies installed"
else
    echo "✅ All dependencies are present"
fi

# Verify Node.js and pnpm for AG-UI
echo "🔍 Verifying AG-UI dependencies (Node.js/pnpm)..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found"
else
    echo "✅ Node.js: $(node --version)"
fi

if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm not found"
else
    echo "✅ pnpm: $(pnpm --version)"
fi

# Ensure uv is installed (used for MCP servers and Python dependency management)
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv not found — installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || true
    export PATH="$HOME/.cargo/bin:$PATH"
    if command -v uv &> /dev/null; then
        echo "✅ uv installed: $(uv --version 2>/dev/null || echo 'unknown')"
    else
        echo "❌ uv installation failed"
    fi
else
    echo "✅ uv found: $(uv --version 2>/dev/null || echo 'unknown')"
fi

# Ensure commonly-used MCP servers are available (idempotent)
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
for server in awslabs.iam-mcp-server awslabs.redshift-mcp-server awslabs.terraform-mcp-server; do
    if ! command -v "$server" &> /dev/null; then
        echo "⚠️  $server not found — installing via uv tool install..."
        uv tool install "$server" 2>/dev/null || true
    fi
    if command -v "$server" &> /dev/null; then
        echo "✅ $server available: $(which "$server")"
    else
        echo "⚠️  $server could not be installed (will use uvx on-demand)"
    fi
done

# Verify Terraform CLI
if ! command -v terraform &> /dev/null; then
    echo "⚠️  Terraform CLI not found — installing..."
    sudo apt-get install -y gnupg software-properties-common curl lsb-release 2>/dev/null || true
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg 2>/dev/null || true
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list > /dev/null
    sudo apt-get update -y && sudo apt-get install -y terraform 2>/dev/null || true
    if command -v terraform &> /dev/null; then
        echo "✅ Terraform: $(terraform -version | head -n1)"
    else
        echo "❌ Terraform installation failed"
    fi
else
    echo "✅ Terraform: $(terraform -version | head -n1)"
fi

# Verify Checkov
if ! command -v checkov &> /dev/null; then
    echo "⚠️  Checkov not found — installing..."
    pip install checkov 2>/dev/null || true
    if command -v checkov &> /dev/null; then
        echo "✅ Checkov: $(checkov --version 2>/dev/null || echo 'installed')"
    else
        echo "❌ Checkov installation failed"
    fi
else
    echo "✅ Checkov: $(checkov --version 2>/dev/null || echo 'installed')"
fi

# Verify SQLite
if ! command -v sqlite3 &> /dev/null; then
    echo "❌ SQLite3 CLI not found"
else
    echo "✅ SQLite3: $(sqlite3 --version | head -c 20)"
fi

# Verify magic-mcp dependencies
echo "🔍 Verifying magic-mcp dependencies..."
if [ -d "/workspaces/sample-workflow/magic-mcp" ]; then
    if [ -d "/workspaces/sample-workflow/magic-mcp/node_modules" ]; then
        echo "✅ magic-mcp: node_modules installed"
    else
        echo "⚠️  magic-mcp: node_modules missing, installing..."
        cd /workspaces/sample-workflow/magic-mcp
        npm install || true
        cd "$PROJECT_PATH"
    fi
else
    echo "ℹ️  magic-mcp directory not found"
fi

# Verify 21st-dev CLI
if command -v npx &> /dev/null; then
    echo "✅ npx available for @21st-dev/cli"
else
    echo "❌ npx not found"
fi

# Verify dbt
if [ -f "$HOME/.local/bin/dbt" ]; then
    echo "✅ dbt: $($HOME/.local/bin/dbt --version 2>/dev/null || echo 'installed')"
else
    echo "⚠️  dbt not found, installing..."
    curl -fsSL https://public.cdn.getdbt.com/fs/install/install.sh | sh -s -- --update || true
fi

# Verify MAGIC_API_KEY
if [ -n "$MAGIC_API_KEY" ]; then
    echo "✅ MAGIC_API_KEY: configured"
else
    echo "⚠️  MAGIC_API_KEY: not set (add to GitHub Codespaces secrets)"
fi

echo ""
echo "📋 Installed packages:"
pip list | grep -E "(mcp|requests|pydantic|dotenv|starlette|uvicorn|httpx|PyYAML|bcrypt|Flask)" || true

echo ""
echo "📋 Database files:"
if [ -f "$PROJECT_PATH/web_ui/auth.db" ]; then
    echo "✅ Authentication database: $PROJECT_PATH/web_ui/auth.db"
else
    echo "ℹ️  Initializing authentication database..."
    # Initialize the database with default users
    cd "$PROJECT_PATH"
    python3 -c "
import sys
sys.path.insert(0, 'web_ui')
import database
database.init_db()
print('Database initialized successfully')
" || echo "⚠️  Database will be created on first web UI run"
fi

echo ""
echo "✅ Dependency check complete!"
