#!/bin/bash
# Script to ensure all ServiceNow MCP dependencies are installed
# This can be run manually or automatically on codespace start

set -e

VENV_PATH="/workspaces/sample-workflow/servicenow-mcp/.venv"
PROJECT_PATH="/workspaces/sample-workflow/servicenow-mcp"

echo "🔍 Checking ServiceNow MCP dependencies..."

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
    echo "ℹ️  Authentication database will be created on first run"
fi

echo ""
echo "✅ Dependency check complete!"
