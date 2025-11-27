#!/bin/bash
# Stop MCP servers running in background

echo "🛑 Stopping MCP Servers"
echo "======================="
echo ""

# Stop ServiceNow MCP Server
if pgrep -f "servicenow_mcp.server" > /dev/null; then
    echo "Stopping ServiceNow MCP server..."
    pkill -f "servicenow_mcp.server"
    sleep 1
    
    if pgrep -f "servicenow_mcp.server" > /dev/null; then
        echo "⚠️  Process still running, forcing kill..."
        pkill -9 -f "servicenow_mcp.server"
    fi
    
    echo "✅ ServiceNow MCP server stopped"
else
    echo "ℹ️  ServiceNow MCP server was not running"
fi

echo ""
echo "✅ Done"
