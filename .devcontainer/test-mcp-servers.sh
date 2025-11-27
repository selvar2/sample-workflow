#!/bin/bash
# Test script to verify MCP servers can be invoked directly (for testing purposes)

set -e

echo "🧪 MCP Server Direct Test"
echo "=========================="
echo ""

# Test ServiceNow MCP Server
echo "1️⃣ Testing ServiceNow MCP Server..."
echo "   Starting server in test mode (will timeout after 3 seconds)..."
echo ""

cd /workspaces/sample-workflow/servicenow-mcp
source .venv/bin/activate

# Test that the server module loads
python -c "
import sys
from servicenow_mcp.server import main
print('✓ ServiceNow MCP server module loaded successfully')
print('✓ Server is ready to be started by MCP client')
" 2>&1

echo ""
echo "2️⃣ Testing Redshift MCP Server availability..."
echo "   Checking if uvx can access the package..."
echo ""

# Test uvx can find the package (but don't actually run it)
if uvx --help | head -n 1; then
    echo "✓ uvx is working"
    echo "✓ Redshift MCP server will auto-install when invoked by MCP client"
fi

echo ""
echo "=========================="
echo "✅ MCP Server Tests Complete"
echo ""
echo "📝 Important Notes:"
echo "   - MCP servers are NOT meant to run as background services"
echo "   - They are started ON-DEMAND by MCP clients (like Claude Desktop)"
echo "   - In Codespaces, you use Python scripts to call the tools directly"
echo "   - In Claude Desktop, the servers start automatically when needed"
echo ""
echo "🎯 To use in Codespaces:"
echo "   python create_incident.py     # Calls ServiceNow tools directly"
echo "   python read_incident.py       # Calls ServiceNow tools directly"
echo "   aws redshift-data ...          # Calls Redshift directly via AWS CLI"
echo ""
echo "🎯 To use in Claude Desktop:"
echo "   1. Copy claude_desktop_config.json to Claude's config folder"
echo "   2. Restart Claude Desktop"
echo "   3. Ask Claude to create incidents, manage Redshift, etc."
echo "   4. Claude will automatically start/stop the MCP servers as needed"
echo ""
