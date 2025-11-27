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

for package in "mcp" "requests" "pydantic" "dotenv" "starlette" "uvicorn" "httpx" "yaml"; do
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
    echo "✅ All dependencies installed"
else
    echo "✅ All dependencies are present"
fi

echo ""
echo "📋 Installed packages:"
pip list | grep -E "(mcp|requests|pydantic|dotenv|starlette|uvicorn|httpx|PyYAML)" || true

echo ""
echo "✅ Dependency check complete!"
