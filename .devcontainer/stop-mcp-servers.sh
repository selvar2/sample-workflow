#!/bin/bash
# Stop MCP servers running in background

echo "🛑 Stopping MCP Servers"
echo "======================="
echo ""

# Stop ServiceNow MCP Server
if pgrep -f "servicenow_mcp.cli" > /dev/null; then
    echo "Stopping ServiceNow MCP server..."
    pkill -f "servicenow_mcp.cli"
    sleep 1
    
    if pgrep -f "servicenow_mcp.cli" > /dev/null; then
        echo "⚠️  Process still running, forcing kill..."
        pkill -9 -f "servicenow_mcp.cli"
    fi
    
    echo "✅ ServiceNow MCP server stopped"
else
    echo "ℹ️  ServiceNow MCP server was not running"
fi

echo ""

# Stop Redshift MCP Server
if pgrep -f "awslabs.redshift-mcp-server" > /dev/null; then
    echo "Stopping Redshift MCP server..."
    pkill -f "awslabs.redshift-mcp-server"
    sleep 1
    
    if pgrep -f "awslabs.redshift-mcp-server" > /dev/null; then
        echo "⚠️  Process still running, forcing kill..."
        pkill -9 -f "awslabs.redshift-mcp-server"
    fi
    
    echo "✅ Redshift MCP server stopped"
else
    echo "ℹ️  Redshift MCP server was not running"
fi

echo ""
echo "✅ Done"
