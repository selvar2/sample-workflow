#!/bin/bash
# Alternative: Start MCP servers as background processes (for testing only)

set -e

echo "🚀 MCP Server Background Launcher"
echo "=================================="
echo ""
echo "⚠️  IMPORTANT NOTE:"
echo "    MCP servers use STDIO protocol - they expect input/output via stdin/stdout."
echo "    Running them as background services without an MCP client doesn't make sense."
echo ""
echo "    In Codespaces, you should use:"
echo "    - Python scripts (create_incident.py, etc.) - calls tools directly"
echo "    - AWS CLI - for Redshift operations"
echo ""
echo "    Background execution is NOT recommended and may not work correctly."
echo ""

read -p "Do you really want to try starting in background? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled. This is the right choice! 👍"
    echo ""
    echo "✅ Use these instead:"
    echo "   python create_incident.py"
    echo "   python read_incident.py INC0010009"
    echo "   aws redshift-data execute-statement ..."
    exit 0
fi

echo ""
echo "⚠️  Proceeding with background start (for testing/debugging)..."

# Create logs directory
mkdir -p /tmp/mcp-logs

# Start ServiceNow MCP Server in background
echo "1️⃣ Attempting to start ServiceNow MCP Server..."

cd /workspaces/sample-workflow/servicenow-mcp
source .venv/bin/activate

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if already running
if pgrep -f "servicenow_mcp.server" > /dev/null; then
    echo "⚠️  ServiceNow MCP server is already running"
    echo "   PID: $(pgrep -f 'servicenow_mcp.server')"
else
    # Note: MCP servers expect stdio communication, so this may not work as expected
    echo "   Starting with redirected stdio (may exit immediately)..."
    nohup python -m servicenow_mcp.server \
        < /dev/null \
        > /tmp/mcp-logs/servicenow-mcp.log 2>&1 &
    
    SNOW_PID=$!
    echo "   Process started with PID: $SNOW_PID"
    echo "   Logs: /tmp/mcp-logs/servicenow-mcp.log"
fi

echo ""
echo "ℹ️  Note: The server may exit immediately because MCP servers"
echo "   expect an MCP client connection via stdio."

echo ""
echo "🛑 To stop:"
echo "   bash .devcontainer/stop-mcp-servers.sh"
echo ""
