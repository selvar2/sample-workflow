#!/usr/bin/env python3
"""
MCP Client Script to interact with AWS IAM and Terraform MCP Servers.
This script demonstrates using MCP servers to gather IAM role information.
"""
import json
import subprocess
import sys

def call_mcp_tool(server_cmd: str, tool_name: str, arguments: dict) -> dict:
    """Call an MCP tool and return the result."""
    
    # Build the JSON-RPC messages
    init_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-client", "version": "1.0"}
        }
    })
    
    call_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    })
    
    # Combine messages
    input_data = f"{init_msg}\n{call_msg}\n"
    
    try:
        result = subprocess.run(
            [server_cmd],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse the responses (may have multiple lines)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.strip():
                try:
                    response = json.loads(line)
                    if response.get("id") == 1:
                        return response
                except json.JSONDecodeError:
                    continue
        
        return {"error": "No valid response", "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout"}
    except Exception as e:
        return {"error": str(e)}


def get_role_details_via_mcp():
    """Get IAM role details using the IAM MCP server."""
    
    print("=" * 70)
    print("🔧 Using AWS IAM MCP Server to get role details")
    print("=" * 70)
    
    # Call list_roles to find our role
    result = call_mcp_tool(
        "awslabs.iam-mcp-server",
        "list_roles",
        {}
    )
    
    print("\n📋 list_roles response:")
    print(json.dumps(result, indent=2, default=str)[:2000])
    
    return result


if __name__ == "__main__":
    result = get_role_details_via_mcp()
