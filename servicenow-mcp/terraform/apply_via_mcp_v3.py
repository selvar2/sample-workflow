#!/usr/bin/env python3
"""
Terraform Apply via AWS Terraform MCP Server

This script executes Terraform commands using the awslabs.terraform-mcp-server
via JSON-RPC protocol over stdio.

Usage: python3 apply_via_mcp_v3.py [working_directory] [aws_region]

Example:
    python3 apply_via_mcp_v3.py /workspaces/sample-workflow/servicenow-mcp/terraform us-east-1
"""

import json
import subprocess
import sys


def run_tf_mcp(command: str, working_directory: str, aws_region: str, timeout: int = 180) -> dict:
    """
    Run a Terraform command via AWS Terraform MCP Server.
    
    Args:
        command: Terraform command (validate, init, plan, apply, destroy)
        working_directory: Directory containing Terraform files
        aws_region: AWS region to use
        timeout: Timeout in seconds
        
    Returns:
        Parsed result dictionary
    """
    # Build JSON-RPC messages
    init_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "tf-mcp-client-py", "version": "1.0"}
        }
    })
    
    tool_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "ExecuteTerraformCommand",
            "arguments": {
                "command": command,
                "working_directory": working_directory,
                "aws_region": aws_region
            }
        }
    })
    
    # Send messages to MCP server
    input_data = f"{init_msg}\n{tool_msg}\n"
    
    try:
        result = subprocess.run(
            ["awslabs.terraform-mcp-server"],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Get the last line of stdout (the tool response)
        # This is the key - we only want the final JSON response
        lines = result.stdout.strip().split('\n')
        if not lines:
            return {"error": "No response from MCP server", "stderr": result.stderr}
        
        # Find the response with id=1 (tool call response)
        for line in reversed(lines):
            if line.strip():
                try:
                    parsed = json.loads(line)
                    if parsed.get("id") == 1:
                        return parsed
                except json.JSONDecodeError:
                    continue
        
        return {"error": "No valid tool response found", "raw": result.stdout[-1000:]}
        
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout} seconds"}
    except FileNotFoundError:
        return {"error": "awslabs.terraform-mcp-server not found. Is it installed?"}
    except Exception as e:
        return {"error": str(e)}


def parse_result(response: dict) -> dict:
    """
    Parse the MCP response and extract relevant fields.
    
    Args:
        response: Raw JSON-RPC response
        
    Returns:
        Dictionary with status, stdout, stderr, error_message, outputs
    """
    if "error" in response:
        return {
            "status": "error",
            "error_message": response["error"],
            "stdout": "",
            "stderr": "",
            "outputs": {}
        }
    
    if "result" not in response:
        return {
            "status": "unknown",
            "error_message": "No result in response",
            "stdout": "",
            "stderr": "",
            "outputs": {}
        }
    
    result = response["result"]
    
    # Try structuredContent first (cleaner)
    if "structuredContent" in result:
        content = result["structuredContent"]
        return {
            "status": content.get("status", "unknown"),
            "stdout": content.get("stdout", ""),
            "stderr": content.get("stderr", ""),
            "error_message": content.get("error_message", ""),
            "outputs": content.get("outputs", {})
        }
    
    # Fall back to parsing content array
    if isinstance(result, list) or (isinstance(result, dict) and "content" in result):
        content_list = result if isinstance(result, list) else result.get("content", [])
        for item in content_list:
            if item.get("type") == "text":
                try:
                    data = json.loads(item["text"])
                    return {
                        "status": data.get("status", "unknown"),
                        "stdout": data.get("stdout", ""),
                        "stderr": data.get("stderr", ""),
                        "error_message": data.get("error_message", ""),
                        "outputs": data.get("outputs", {})
                    }
                except json.JSONDecodeError:
                    continue
    
    return {
        "status": "unknown",
        "error_message": "Could not parse response",
        "stdout": "",
        "stderr": "",
        "outputs": {}
    }


def print_step(step_num: int, description: str, command: str):
    """Print step header."""
    print("-" * 78)
    print(f"Step {step_num}: {description}")
    print(f"Command: terraform {command}")
    print("-" * 78)


def print_result(result: dict, show_outputs: bool = False):
    """Print parsed result."""
    print(f"Status: {result['status']}")
    
    if result['stdout']:
        stdout = result['stdout']
        lines = stdout.strip().split('\n')
        if len(lines) > 50:
            print("\nOutput (last 50 lines):")
            print('\n'.join(lines[-50:]))
        else:
            print(f"\nOutput:\n{stdout}")
    
    if result['error_message']:
        print(f"\nError: {result['error_message']}")
    
    if show_outputs and result['outputs']:
        print("\nTerraform Outputs:")
        for key, value in result['outputs'].items():
            print(f"  {key} = {value}")
    
    print()


def main():
    # Parse arguments
    if len(sys.argv) >= 2:
        working_dir = sys.argv[1]
    else:
        working_dir = "/workspaces/sample-workflow/servicenow-mcp/terraform"
    
    if len(sys.argv) >= 3:
        aws_region = sys.argv[2]
    else:
        aws_region = "us-east-1"
    
    timeout = 180
    
    print("=" * 78)
    print("TERRAFORM APPLY VIA AWS TERRAFORM MCP SERVER (Python)")
    print("=" * 78)
    print(f"Working Directory: {working_dir}")
    print(f"AWS Region: {aws_region}")
    print(f"Timeout: {timeout}s per command")
    print()
    
    # Define workflow steps
    steps = [
        (1, "Validating Terraform configuration", "validate"),
        (2, "Initializing Terraform", "init"),
        (3, "Planning Terraform changes", "plan"),
        (4, "Applying Terraform configuration", "apply"),
    ]
    
    all_success = True
    
    for step_num, description, command in steps:
        print_step(step_num, description, command)
        
        # Run command via MCP
        response = run_tf_mcp(command, working_dir, aws_region, timeout)
        result = parse_result(response)
        
        # Print result (show outputs only for apply)
        print_result(result, show_outputs=(command == "apply"))
        
        if result['status'] != 'success':
            print(f"WARNING: Command '{command}' did not return success status.")
            all_success = False
            # Continue anyway to see subsequent steps
    
    print("=" * 78)
    if all_success:
        print("✅ TERRAFORM APPLY COMPLETED SUCCESSFULLY")
    else:
        print("⚠️  TERRAFORM APPLY COMPLETED WITH WARNINGS")
    print("=" * 78)
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
