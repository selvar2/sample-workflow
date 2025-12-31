#!/bin/bash
# Verification script to test MCP server installations and configurations

set -e

echo "🔍 MCP Server Installation Verification"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ALL_GOOD=true

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        ALL_GOOD=false
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Check Python installation
echo "📍 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status 0 "Python installed: $PYTHON_VERSION"
else
    print_status 1 "Python not found"
fi

# 2. Check uv installation
echo ""
echo "📍 Checking uv..."
if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version)
    print_status 0 "uv installed: $UV_VERSION"
else
    print_status 1 "uv not found"
fi

# 3. Check uvx installation
echo ""
echo "📍 Checking uvx..."
if command -v uvx &> /dev/null; then
    print_status 0 "uvx installed"
else
    # Check if uv can run as uvx
    if uv --help | grep -q "uvx"; then
        print_status 0 "uvx available via uv"
    else
        print_status 1 "uvx not found"
    fi
fi

# 4. Check AWS CLI
echo ""
echo "📍 Checking AWS CLI..."
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version 2>&1 | head -n1)
    print_status 0 "AWS CLI installed: $AWS_VERSION"
else
    print_status 1 "AWS CLI not found"
fi

# 5. Check AWS credentials
echo ""
echo "📍 Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    print_status 0 "AWS credentials configured (Account: $AWS_ACCOUNT)"
else
    print_status 1 "AWS credentials not configured or invalid"
fi

# 6. Check ServiceNow MCP virtual environment
echo ""
echo "📍 Checking ServiceNow MCP installation..."
if [ -d "/workspaces/sample-workflow/servicenow-mcp/.venv" ]; then
    print_status 0 "Virtual environment exists"
    
    # Check if servicenow-mcp is installed
    if /workspaces/sample-workflow/servicenow-mcp/.venv/bin/python -c "import servicenow_mcp" &> /dev/null; then
        print_status 0 "servicenow_mcp module installed"
    else
        print_status 1 "servicenow_mcp module not found in venv"
    fi
else
    print_status 1 "Virtual environment not found at /workspaces/sample-workflow/servicenow-mcp/.venv"
fi

# 7. Check environment variables
echo ""
echo "📍 Checking environment variables..."
if [ -n "$SERVICENOW_INSTANCE_URL" ]; then
    print_status 0 "SERVICENOW_INSTANCE_URL is set"
else
    print_status 1 "SERVICENOW_INSTANCE_URL not set"
fi

if [ -n "$SERVICENOW_USERNAME" ]; then
    print_status 0 "SERVICENOW_USERNAME is set"
else
    print_status 1 "SERVICENOW_USERNAME not set"
fi

if [ -n "$SERVICENOW_PASSWORD" ]; then
    print_status 0 "SERVICENOW_PASSWORD is set"
else
    print_status 1 "SERVICENOW_PASSWORD not set"
fi

# 8. Test ServiceNow MCP server can start
echo ""
echo "📍 Testing ServiceNow MCP server..."
if timeout 5 /workspaces/sample-workflow/servicenow-mcp/.venv/bin/python -m servicenow_mcp.cli --help &> /dev/null; then
    print_status 0 "ServiceNow MCP server can be invoked"
else
    # Try to capture the error
    ERROR_OUTPUT=$(/workspaces/sample-workflow/servicenow-mcp/.venv/bin/python -m servicenow_mcp.cli --help 2>&1 | head -n3 || true)
    print_status 1 "ServiceNow MCP server failed to start"
    if [ -n "$ERROR_OUTPUT" ]; then
        print_warning "Error: $ERROR_OUTPUT"
    fi
fi

# 9. Test Redshift MCP server availability
echo ""
echo "📍 Testing Redshift MCP server..."
if uvx --help &> /dev/null; then
    print_status 0 "uvx can run packages"
    # Note: We don't actually start the server as it requires AWS resources
    print_warning "Redshift MCP server will be auto-installed on first use"
else
    print_status 1 "Cannot test Redshift MCP server (uvx not working)"
fi

# 10. Check IAM MCP server availability
echo ""
echo "📍 Checking IAM MCP server..."
if command -v awslabs.iam-mcp-server &> /dev/null; then
    print_status 0 "IAM MCP server installed: $(which awslabs.iam-mcp-server)"
else
    print_warning "IAM MCP server is not installed — it will be auto-installed on first use or by .devcontainer/scripts"
fi

# 10. Check Redshift cluster availability
echo ""
echo "📍 Checking Redshift cluster..."
if aws redshift describe-clusters --region us-east-1 &> /dev/null; then
    CLUSTER_COUNT=$(aws redshift describe-clusters --region us-east-1 --query 'length(Clusters)' --output text 2>/dev/null || echo "0")
    if [ "$CLUSTER_COUNT" -gt 0 ]; then
        print_status 0 "Found $CLUSTER_COUNT Redshift cluster(s)"
        # List clusters
        aws redshift describe-clusters --region us-east-1 --query 'Clusters[*].[ClusterIdentifier,ClusterStatus]' --output table 2>/dev/null | head -n 10
    else
        print_warning "No Redshift clusters found"
    fi
else
    print_status 1 "Cannot access Redshift (check AWS permissions)"
fi

# Summary
echo ""
echo "========================================"
if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "🎯 Both MCP servers are ready to use:"
    echo "  1. ServiceNow MCP: Installed and configured"
    echo "  2. Redshift MCP: Will auto-install on first use via uvx"
    echo ""
    echo "💡 MCP servers are started automatically by MCP clients (like Claude Desktop)"
    echo "   They don't need to run as background services in Codespaces."
else
    echo -e "${RED}✗ Some checks failed.${NC} See details above."
    echo ""
    echo "🔧 To fix issues, try:"
    echo "  - Run the dev container setup: bash .devcontainer/setup.sh"
    echo "  - Check GitHub Codespaces secrets are set"
    echo "  - Rebuild the container: Cmd/Ctrl+Shift+P → 'Rebuild Container'"
fi

echo ""
