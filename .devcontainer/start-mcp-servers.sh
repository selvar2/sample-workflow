#!/bin/bash
# Script to start MCP servers for testing/debugging purposes
# Note: MCP servers are normally started by MCP clients, not run as background services

set -e

echo "🚀 MCP Server Startup Script"
echo "============================"
echo ""
echo "⚠️  WARNING: MCP servers are designed to be started by MCP clients"
echo "    (like Claude Desktop), not as persistent background services."
echo ""
echo "    This script is for TESTING/DEBUGGING purposes only."
echo ""

# Check if we should proceed
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""

# Function to check if a port is in use
port_in_use() {
    lsof -i:$1 >/dev/null 2>&1
}

# 1. Start ServiceNow MCP Server
echo "1️⃣ Starting ServiceNow MCP Server..."
echo ""

cd /workspaces/sample-workflow/servicenow-mcp
source .venv/bin/activate

# Check if already running
if port_in_use 8000; then
    echo "⚠️  Port 8000 is already in use (server may already be running)"
    lsof -i:8000
else
    echo "📡 Starting ServiceNow MCP server on stdio (MCP protocol)..."
    echo "   This will run in the foreground. Press Ctrl+C to stop."
    echo ""
    
    # Load environment variables
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Start the MCP server
    # Note: MCP servers communicate via stdio, not HTTP
    echo "Starting: python -m servicenow_mcp.server"
    python -m servicenow_mcp.server
fi

# Note: The script will block here while the server runs
# Redshift MCP server would be started similarly if needed
