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
if pgrep -f "servicenow_mcp.cli" > /dev/null; then
    echo "⚠️  ServiceNow MCP server is already running"
    echo "   PID: $(pgrep -f 'servicenow_mcp.cli')"
else
    # Note: MCP servers expect stdio communication, so this may not work as expected
    echo "   Starting with servicenow_mcp.cli (stdio-based MCP server)..."
    nohup python -m servicenow_mcp.cli \
        < /dev/null \
        > /tmp/mcp-logs/servicenow-mcp.log 2>&1 &
    
    SNOW_PID=$!
    echo "   Process started with PID: $SNOW_PID"
    echo "   Logs: /tmp/mcp-logs/servicenow-mcp.log"
    
    # Wait a moment to check if it's still running
    sleep 1
    if ps -p $SNOW_PID > /dev/null 2>&1; then
        echo "   ✅ Server is still running"
    else
        echo "   ⚠️  Server exited (check logs for details)"
    fi
fi

echo ""
echo "2️⃣ Starting Redshift MCP Server..."

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "⚠️  AWS credentials not configured. Redshift MCP server may not work."
    echo "   Run: aws configure"
else
    echo "   ✅ AWS credentials verified"
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv not found in PATH"
    echo "   PATH: $PATH"
else
    echo "   ✅ uv found at: $(which uv)"
fi

# Check if already running
if pgrep -f "awslabs.redshift-mcp-server" > /dev/null; then
    echo "⚠️  Redshift MCP server is already running"
    echo "   PID: $(pgrep -f 'awslabs.redshift-mcp-server')"
else
    echo "   Starting Redshift MCP server..."
    # Add uv to PATH if needed
    export PATH="$HOME/.cargo/bin:$PATH"
    
    nohup uv tool run --from awslabs.redshift-mcp-server@latest awslabs.redshift-mcp-server \
        < /dev/null \
        > /tmp/mcp-logs/redshift-mcp.log 2>&1 &
    
    REDSHIFT_PID=$!
    echo "   Process started with PID: $REDSHIFT_PID"
    echo "   Logs: /tmp/mcp-logs/redshift-mcp.log"
    
    # Wait a moment to check if it's still running
    sleep 2
    if ps -p $REDSHIFT_PID > /dev/null 2>&1; then
        echo "   ✅ Server is still running"
    else
        echo "   ⚠️  Server exited (check logs for details)"
    fi
fi

echo ""
echo "✅ MCP Servers startup attempted"

echo ""
echo "📊 To check status:"
echo "   ps aux | grep -E 'servicenow_mcp|redshift-mcp'"
echo ""
echo "📋 To view logs:"
echo "   tail -f /tmp/mcp-logs/servicenow-mcp.log"
echo "   tail -f /tmp/mcp-logs/redshift-mcp.log"
echo ""
echo "🛑 To stop:"
echo "   bash .devcontainer/stop-mcp-servers.sh"
echo ""
echo "ℹ️  Note: MCP servers may exit immediately because they"
echo "   expect an MCP client connection via stdio."
echo ""
