#!/bin/bash
#############################################################################
# Terraform Apply via AWS Terraform MCP Server
#
# This script executes Terraform commands using the awslabs.terraform-mcp-server
# via JSON-RPC protocol over stdio.
#
# Usage: ./terraform_mcp_apply.sh [working_directory] [aws_region]
#
# Example:
#   ./terraform_mcp_apply.sh /workspaces/sample-workflow/servicenow-mcp/terraform us-east-1
#############################################################################

set -e

# Configuration
WORKING_DIR="${1:-/workspaces/sample-workflow/servicenow-mcp/terraform}"
AWS_REGION="${2:-us-east-1}"
TIMEOUT_SECONDS=180

echo "=============================================================================="
echo "TERRAFORM APPLY VIA AWS TERRAFORM MCP SERVER"
echo "=============================================================================="
echo "Working Directory: $WORKING_DIR"
echo "AWS Region: $AWS_REGION"
echo "Timeout: ${TIMEOUT_SECONDS}s per command"
echo ""

# Function to run a Terraform command via MCP server
run_tf_mcp() {
    local cmd="$1"
    local description="$2"
    
    echo "------------------------------------------------------------------------------"
    echo "Step: $description"
    echo "Command: terraform $cmd"
    echo "------------------------------------------------------------------------------"
    
    # Build JSON-RPC messages
    local init_msg='{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"tf-mcp-client","version":"1.0"}}}'
    local tool_msg='{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ExecuteTerraformCommand","arguments":{"command":"'"$cmd"'","working_directory":"'"$WORKING_DIR"'","aws_region":"'"$AWS_REGION"'"}}}'
    
    # Execute via MCP server and capture the response (last line only)
    local response
    response=$(printf '%s\n%s\n' "$init_msg" "$tool_msg" | timeout "$TIMEOUT_SECONDS" awslabs.terraform-mcp-server 2>&1 | tail -1)
    
    # Parse the response
    local status
    status=$(echo "$response" | python3 -c "
import sys, json
try:
    r = json.load(sys.stdin)
    if 'result' in r:
        content = r['result']
        if isinstance(content, list):
            for item in content:
                if item.get('type') == 'text':
                    data = json.loads(item['text'])
                    print(data.get('status', 'unknown'))
                    break
        elif 'structuredContent' in r['result']:
            print(r['result']['structuredContent'].get('status', 'unknown'))
        else:
            print('unknown')
    else:
        print('error')
except Exception as e:
    print('parse_error')
" 2>/dev/null)
    
    echo "Status: $status"
    
    # Extract and display stdout
    local stdout
    stdout=$(echo "$response" | python3 -c "
import sys, json
try:
    r = json.load(sys.stdin)
    if 'result' in r and 'structuredContent' in r['result']:
        stdout = r['result']['structuredContent'].get('stdout', '')
        # Print last 50 lines if too long
        lines = stdout.strip().split('\n')
        if len(lines) > 50:
            print('... (truncated, showing last 50 lines)')
            print('\n'.join(lines[-50:]))
        else:
            print(stdout)
except:
    pass
" 2>/dev/null)
    
    if [ -n "$stdout" ]; then
        echo ""
        echo "Output:"
        echo "$stdout"
    fi
    
    # Extract and display outputs (for apply command)
    if [ "$cmd" == "apply" ]; then
        local outputs
        outputs=$(echo "$response" | python3 -c "
import sys, json
try:
    r = json.load(sys.stdin)
    if 'result' in r and 'structuredContent' in r['result']:
        outputs = r['result']['structuredContent'].get('outputs', {})
        if outputs:
            print('Terraform Outputs:')
            for k, v in outputs.items():
                print(f'  {k} = {v}')
except:
    pass
" 2>/dev/null)
        
        if [ -n "$outputs" ]; then
            echo ""
            echo "$outputs"
        fi
    fi
    
    # Check for errors
    if [ "$status" != "success" ]; then
        local error_msg
        error_msg=$(echo "$response" | python3 -c "
import sys, json
try:
    r = json.load(sys.stdin)
    if 'result' in r and 'structuredContent' in r['result']:
        print(r['result']['structuredContent'].get('error_message', ''))
except:
    pass
" 2>/dev/null)
        
        if [ -n "$error_msg" ]; then
            echo ""
            echo "Error: $error_msg"
        fi
        
        echo ""
        echo "WARNING: Command '$cmd' did not return success status."
        # Continue anyway to see subsequent steps
    fi
    
    echo ""
    return 0
}

# Execute Terraform workflow
echo ""

# Step 1: Validate
run_tf_mcp "validate" "Validating Terraform configuration"

# Step 2: Init
run_tf_mcp "init" "Initializing Terraform"

# Step 3: Plan
run_tf_mcp "plan" "Planning Terraform changes"

# Step 4: Apply
run_tf_mcp "apply" "Applying Terraform configuration"

echo "=============================================================================="
echo "TERRAFORM APPLY COMPLETED"
echo "=============================================================================="
