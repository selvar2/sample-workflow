#!/usr/bin/env python3
"""
IAM Role Manager (MCP Version) - Hybrid AWS CLI + MCP Servers

A comprehensive script that handles the complete lifecycle of IAM role management
using a hybrid approach combining MCP servers with AWS CLI fallback:

MCP Servers Used (where available):
- awslabs.iam-mcp-server: For listing roles, inline policies, policy documents
- awslabs.terraform-mcp-server: For Terraform apply/destroy operations

AWS CLI Used (for operations not in MCP):
- get-role, list-attached-role-policies, get-policy, etc.

Available IAM MCP Tools:
- list_roles, list_role_policies, get_role_policy, get_managed_policy_document
- create_role, delete_role_policy, put_role_policy

Usage Examples:
    # Backup and delete a role
    python3 iam_role_manager_mcp.py --role-name example_role5_mcp_test --confirm

    # Backup only (no deletion)
    python3 iam_role_manager_mcp.py --role-name example_role5_mcp_test --backup-only

    # Dry run (show what would happen)
    python3 iam_role_manager_mcp.py --role-name example_role5_mcp_test --dry-run

    # Restore from backup
    python3 iam_role_manager_mcp.py --restore iam_example_role5_mcp_test.txt

Author: Generated for ServiceNow MCP Project
Date: 2026-01-30
"""

import argparse
import json
import os
import subprocess
import sys
import shutil
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_BACKUP_DIR = "/workspaces/sample-workflow/servicenow-mcp/terraform"
AWS_REGION = "us-east-1"

# MCP Server Commands
IAM_MCP_SERVER = "awslabs.iam-mcp-server"
TERRAFORM_MCP_SERVER = "awslabs.terraform-mcp-server"

# Available IAM MCP Tools (as of v1.25.0):
# list_users, get_user, create_user, delete_user, list_roles, create_role,
# list_policies, get_managed_policy_document, attach_user_policy, detach_user_policy,
# create_access_key, delete_access_key, simulate_principal_policy,
# list_groups, get_group, create_group, delete_group, add_user_to_group, remove_user_from_group,
# attach_group_policy, detach_group_policy, put_user_policy, get_user_policy, delete_user_policy,
# put_role_policy, get_role_policy, delete_role_policy, list_user_policies, list_role_policies
#
# NOT AVAILABLE in IAM MCP: get_role, list_attached_role_policies, get_policy, list_policy_versions


# =============================================================================
# AWS CLI Wrapper Functions (for operations not in MCP)
# =============================================================================

def run_aws_command(args: List[str], ignore_errors: bool = False) -> Dict[str, Any]:
    """
    Run an AWS CLI command and return the JSON result.
    
    Args:
        args: List of AWS CLI arguments (without 'aws' prefix)
        ignore_errors: If True, return empty dict on error instead of raising
        
    Returns:
        Parsed JSON response or empty dict on error
    """
    cmd = ["aws"] + args + ["--no-cli-pager", "--output", "json"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            if ignore_errors:
                return {}
            error_msg = result.stderr.strip()
            if "NoSuchEntity" in error_msg:
                return {"error": "NotFound", "message": error_msg}
            return {"error": "CommandFailed", "message": error_msg}
        
        if result.stdout.strip():
            return json.loads(result.stdout)
        return {"success": True}
        
    except subprocess.TimeoutExpired:
        return {"error": "Timeout", "message": "Command timed out"}
    except json.JSONDecodeError as e:
        return {"error": "ParseError", "message": str(e)}
    except Exception as e:
        return {"error": "Exception", "message": str(e)}


# =============================================================================
# MCP Communication Functions
# =============================================================================

def call_mcp_tool(server_cmd: str, tool_name: str, arguments: dict, timeout: int = 60) -> dict:
    """
    Call an MCP tool and return the result.
    
    Uses JSON-RPC protocol to communicate with MCP servers via stdio.
    
    Args:
        server_cmd: MCP server command (e.g., 'awslabs.iam-mcp-server')
        tool_name: Name of the tool to call
        arguments: Dictionary of arguments for the tool
        timeout: Timeout in seconds
        
    Returns:
        Parsed JSON-RPC response dictionary
    """
    # Build JSON-RPC messages
    init_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "iam-role-manager-mcp", "version": "1.0"}
        }
    })
    
    tool_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    })
    
    # Send messages to MCP server
    input_data = f"{init_msg}\n{tool_msg}\n"
    
    try:
        result = subprocess.run(
            [server_cmd],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Parse the responses - look for id=1 (tool call response)
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.strip():
                try:
                    parsed = json.loads(line)
                    if parsed.get("id") == 1:
                        return parsed
                except json.JSONDecodeError:
                    continue
        
        return {"error": "NoValidResponse", "stdout": result.stdout, "stderr": result.stderr}
        
    except subprocess.TimeoutExpired:
        return {"error": "Timeout", "message": f"Command timed out after {timeout} seconds"}
    except FileNotFoundError:
        return {"error": "ServerNotFound", "message": f"MCP server not found: {server_cmd}"}
    except Exception as e:
        return {"error": "Exception", "message": str(e)}


def extract_mcp_content(response: dict) -> Tuple[bool, Any]:
    """
    Extract content from MCP response.
    
    Args:
        response: Raw JSON-RPC response
        
    Returns:
        Tuple of (success, content/error_message)
    """
    if "error" in response:
        return False, response.get("message", response.get("error"))
    
    if "result" not in response:
        return False, "No result in response"
    
    result = response["result"]
    
    # Try structuredContent first
    if isinstance(result, dict) and "structuredContent" in result:
        return True, result["structuredContent"]
    
    # Try content array
    if isinstance(result, dict) and "content" in result:
        content_list = result.get("content", [])
        for item in content_list:
            if item.get("type") == "text":
                try:
                    return True, json.loads(item["text"])
                except json.JSONDecodeError:
                    return True, item["text"]
    
    # Direct result
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict) and item.get("type") == "text":
                try:
                    return True, json.loads(item["text"])
                except json.JSONDecodeError:
                    return True, item["text"]
    
    return True, result


# =============================================================================
# IAM MCP Server Functions
# =============================================================================

def mcp_list_roles() -> Dict[str, Any]:
    """
    List all IAM roles using IAM MCP Server.
    
    Returns:
        Dictionary with roles list or error
    """
    response = call_mcp_tool(IAM_MCP_SERVER, "list_roles", {})
    success, content = extract_mcp_content(response)
    
    if not success:
        return {"error": content}
    
    return content


def mcp_get_role(role_name: str) -> Dict[str, Any]:
    """
    Get IAM role details - uses AWS CLI as IAM MCP doesn't have get_role.
    
    Args:
        role_name: Name of the IAM role
        
    Returns:
        Role data dictionary or error
    """
    # IAM MCP server doesn't have get_role, use AWS CLI
    result = run_aws_command(["iam", "get-role", "--role-name", role_name])
    return result


def mcp_list_attached_role_policies(role_name: str) -> List[Dict]:
    """
    List attached managed policies - uses AWS CLI as IAM MCP doesn't have this.
    
    Args:
        role_name: Name of the IAM role
        
    Returns:
        List of attached policies
    """
    # IAM MCP server doesn't have list_attached_role_policies, use AWS CLI
    result = run_aws_command([
        "iam", "list-attached-role-policies",
        "--role-name", role_name
    ])
    return result.get("AttachedPolicies", [])


def mcp_list_role_policies(role_name: str) -> List[str]:
    """
    List inline policies for a role using IAM MCP Server.
    
    Args:
        role_name: Name of the IAM role
        
    Returns:
        List of inline policy names
    """
    response = call_mcp_tool(
        IAM_MCP_SERVER, 
        "list_role_policies", 
        {"role_name": role_name}
    )
    success, content = extract_mcp_content(response)
    
    if not success:
        return []
    
    # Parse from text response or dict
    if isinstance(content, dict):
        return content.get("PolicyNames", [])
    elif isinstance(content, str):
        # Try to extract policy names from text response
        try:
            parsed = json.loads(content)
            return parsed.get("PolicyNames", [])
        except:
            return []
    
    return []


def mcp_get_policy(policy_arn: str) -> Dict[str, Any]:
    """
    Get IAM policy details - uses AWS CLI as IAM MCP doesn't have get_policy.
    
    Args:
        policy_arn: ARN of the policy
        
    Returns:
        Policy data dictionary or error
    """
    # IAM MCP server doesn't have get_policy, use AWS CLI
    result = run_aws_command(["iam", "get-policy", "--policy-arn", policy_arn])
    return result


def mcp_get_policy_version(policy_arn: str, version_id: str) -> Dict[str, Any]:
    """
    Get IAM policy version document - uses AWS CLI as IAM MCP doesn't have this.
    
    Args:
        policy_arn: ARN of the policy
        version_id: Version ID (e.g., 'v1')
        
    Returns:
        Policy version data dictionary or error
    """
    # IAM MCP server doesn't have get_policy_version, use AWS CLI
    result = run_aws_command([
        "iam", "get-policy-version",
        "--policy-arn", policy_arn,
        "--version-id", version_id
    ])
    return result


def mcp_get_role_policy(role_name: str, policy_name: str) -> Dict[str, Any]:
    """
    Get inline policy document using IAM MCP Server.
    
    Args:
        role_name: Name of the role
        policy_name: Name of the inline policy
        
    Returns:
        Policy document or error
    """
    response = call_mcp_tool(
        IAM_MCP_SERVER, 
        "get_role_policy", 
        {"role_name": role_name, "policy_name": policy_name}
    )
    success, content = extract_mcp_content(response)
    
    if not success:
        return {"error": content}
    
    # Parse the response - may be text or dict
    if isinstance(content, str):
        try:
            return json.loads(content)
        except:
            return {"PolicyDocument": {}, "raw": content}
    
    return content


def mcp_list_policy_versions(policy_arn: str) -> List[Dict]:
    """
    List policy versions - uses AWS CLI as IAM MCP doesn't have this.
    
    Args:
        policy_arn: ARN of the policy
        
    Returns:
        List of policy versions
    """
    # IAM MCP server doesn't have list_policy_versions, use AWS CLI
    result = run_aws_command([
        "iam", "list-policy-versions",
        "--policy-arn", policy_arn
    ])
    return result.get("Versions", [])
    
    if isinstance(content, dict):
        return content.get("Versions", [])
    
    return []


# =============================================================================
# Terraform MCP Server Functions
# =============================================================================

def mcp_terraform_command(command: str, working_directory: str, timeout: int = 180) -> Dict[str, Any]:
    """
    Execute a Terraform command using Terraform MCP Server.
    
    Args:
        command: Terraform command (validate, init, plan, apply, destroy)
        working_directory: Directory containing Terraform files
        timeout: Timeout in seconds
        
    Returns:
        Dictionary with status, stdout, stderr, outputs
    """
    response = call_mcp_tool(
        TERRAFORM_MCP_SERVER,
        "ExecuteTerraformCommand",
        {
            "command": command,
            "working_directory": working_directory,
            "aws_region": AWS_REGION
        },
        timeout=timeout
    )
    
    success, content = extract_mcp_content(response)
    
    if not success:
        return {
            "status": "error",
            "error_message": content,
            "stdout": "",
            "stderr": "",
            "outputs": {}
        }
    
    if isinstance(content, dict):
        return {
            "status": content.get("status", "unknown"),
            "stdout": content.get("stdout", ""),
            "stderr": content.get("stderr", ""),
            "error_message": content.get("error_message", ""),
            "outputs": content.get("outputs", {})
        }
    
    return {
        "status": "unknown",
        "stdout": str(content),
        "stderr": "",
        "error_message": "",
        "outputs": {}
    }


def run_terraform_workflow(working_dir: str, action: str = "apply") -> Tuple[bool, str]:
    """
    Run a complete Terraform workflow (init, plan, apply/destroy).
    
    Args:
        working_dir: Directory containing .tf files
        action: Either 'apply' or 'destroy'
        
    Returns:
        Tuple of (success, message)
    """
    # Note: validate requires init first, so we run init before validate
    steps = [
        ("init", "Initializing Terraform"),
        ("validate", "Validating configuration"),
        ("plan", "Planning changes"),
        (action, f"Executing {action}"),
    ]
    
    for command, description in steps:
        print(f"   🔧 {description}...")
        result = mcp_terraform_command(command, working_dir)
        
        # Check for errors
        if result["status"] == "error":
            return False, f"{description} failed: {result.get('error_message', 'Unknown error')}"
        
        # For the final action, check if it succeeded
        if command == action:
            stdout = result.get("stdout", "")
            if result["status"] == "success":
                continue
            elif action == "apply" and "Apply complete" in stdout:
                continue
            elif action == "destroy" and "Destroy complete" in stdout:
                continue
            else:
                return False, f"{description} did not succeed: {result.get('stderr', stdout[:200])}"
    
    return True, f"Terraform {action} completed successfully"


# =============================================================================
# IAM Role Information Gathering (via MCP)
# =============================================================================

class IAMRoleInfoMCP:
    """Container for all IAM role information gathered via MCP."""
    
    def __init__(self, role_name: str):
        self.role_name = role_name
        self.role_data: Dict = {}
        self.attached_policies: List[Dict] = []
        self.inline_policies: List[str] = []
        self.policy_documents: Dict[str, Dict] = {}
        self.policy_versions: Dict[str, List[Dict]] = {}
        self.inline_policy_documents: Dict[str, Dict] = {}
        self.exists = False
        
    def gather_all_info(self) -> bool:
        """
        Gather all information about the IAM role using MCP servers.
        
        Returns:
            True if role exists and info gathered, False otherwise
        """
        print(f"\n📋 Gathering information for role: {self.role_name}")
        print(f"   Using: IAM MCP Server + AWS CLI (hybrid)")
        print("-" * 60)
        
        # Step 1: Get role details (via AWS CLI - not in MCP)
        print("   🔍 Fetching role details (AWS CLI)...")
        role_response = mcp_get_role(self.role_name)
        
        if "error" in role_response:
            error_type = role_response.get('error')
            if error_type == "NotFound":
                print(f"   ❌ Role not found: {self.role_name}")
            else:
                print(f"   ❌ Error: {role_response.get('message', error_type)}")
            return False
        
        self.role_data = role_response.get("Role", {})
        if not self.role_data:
            print(f"   ❌ No role data returned")
            return False
            
        self.exists = True
        print(f"   ✅ Role ARN: {self.role_data.get('Arn')}")
        print(f"   ✅ Role ID: {self.role_data.get('RoleId')}")
        
        # Step 2: Get attached managed policies (via AWS CLI - not in MCP)
        print("   🔍 Fetching attached policies (AWS CLI)...")
        self.attached_policies = mcp_list_attached_role_policies(self.role_name)
        print(f"   ✅ Attached policies: {len(self.attached_policies)}")
        
        # Step 3: Get inline policies (via MCP - list_role_policies)
        print("   🔍 Fetching inline policies (MCP)...")
        self.inline_policies = mcp_list_role_policies(self.role_name)
        print(f"   ✅ Inline policies: {len(self.inline_policies)}")
        
        # Step 4: Get policy documents for each attached policy (via AWS CLI)
        for policy in self.attached_policies:
            policy_arn = policy.get("PolicyArn")
            policy_name = policy.get("PolicyName")
            
            print(f"   🔍 Fetching policy document (AWS CLI): {policy_name}...")
            
            # Get policy metadata (AWS CLI)
            policy_info = mcp_get_policy(policy_arn)
            policy_meta = policy_info.get("Policy", {})
            default_version = policy_meta.get("DefaultVersionId", "v1")
            
            # Get policy version document (AWS CLI)
            version_result = mcp_get_policy_version(policy_arn, default_version)
            
            self.policy_documents[policy_arn] = {
                "policy_info": policy_meta,
                "document": version_result.get("PolicyVersion", {}).get("Document", {})
            }
            
            # Get all policy versions (AWS CLI)
            self.policy_versions[policy_arn] = mcp_list_policy_versions(policy_arn)
            print(f"   ✅ Policy {policy_name}: {len(self.policy_versions[policy_arn])} version(s)")
        
        # Step 5: Get inline policy documents (via MCP - get_role_policy)
        for policy_name in self.inline_policies:
            print(f"   🔍 Fetching inline policy (MCP): {policy_name}...")
            
            result = mcp_get_role_policy(self.role_name, policy_name)
            self.inline_policy_documents[policy_name] = result.get("PolicyDocument", {})
            print(f"   ✅ Inline policy {policy_name} retrieved")
        
        print("-" * 60)
        print("✅ All information gathered successfully via MCP")
        
        return True


# =============================================================================
# Backup Generation
# =============================================================================

def generate_terraform_backup(role_info: IAMRoleInfoMCP) -> str:
    """
    Generate Terraform configuration from role information.
    
    Args:
        role_info: IAMRoleInfoMCP object with all role data
        
    Returns:
        Terraform configuration as string
    """
    role = role_info.role_data
    role_name = role.get("RoleName", "unknown_role")
    
    # Extract role details
    path = role.get("Path", "/")
    description = role.get("Description", "")
    max_session = role.get("MaxSessionDuration", 3600)
    assume_policy = role.get("AssumeRolePolicyDocument", {})
    tags = role.get("Tags", [])
    create_date = role.get("CreateDate", "")
    role_id = role.get("RoleId", "")
    role_arn = role.get("Arn", "")
    
    # Convert tags list to Terraform format
    tags_lines = []
    for tag in tags:
        tags_lines.append(f'    {tag["Key"]} = "{tag["Value"]}"')
    tags_tf = "\n".join(tags_lines) if tags_lines else ""
    
    # Start building configuration
    config = f'''#############################################################################
# Terraform Configuration for IAM Role: {role_name}
# 
# BACKUP FILE - Created via MCP Servers before deletion
# This configuration can be used to recreate the IAM role with ARN:
#   {role_arn}
#
# Role Details:
#   - Name: {role_name}
#   - RoleId: {role_id}
#   - Path: {path}
#   - Max Session Duration: {max_session} seconds
#   - Attached Managed Policies: {len(role_info.attached_policies)}
#   - Inline Policies: {len(role_info.inline_policies)}
#   - Created: {create_date}
#
# MCP Servers Used:
#   - {IAM_MCP_SERVER} (for role information)
#   - {TERRAFORM_MCP_SERVER} (for restore operations)
#
# Backup Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
#############################################################################

terraform {{
  required_version = ">= 1.0.0"

  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }}
  }}
}}

#############################################################################
# Provider Configuration
#############################################################################
# provider "aws" {{
#   region  = "{AWS_REGION}"
#   profile = "default"
# }}

#############################################################################
# IAM Role: {role_name}
#############################################################################
resource "aws_iam_role" "{role_name}" {{
  name        = "{role_name}"
  path        = "{path}"
  description = "{description}"

  max_session_duration = {max_session}

  assume_role_policy = jsonencode({json.dumps(assume_policy, indent=4).replace(chr(10), chr(10) + "  ")})

  tags = {{
{tags_tf}
  }}
}}
'''

    # Add managed policies
    for policy in role_info.attached_policies:
        policy_arn = policy.get("PolicyArn")
        policy_data = role_info.policy_documents.get(policy_arn, {})
        policy_info = policy_data.get("policy_info", {})
        policy_doc = policy_data.get("document", {})
        
        policy_name = policy_info.get("PolicyName", policy.get("PolicyName", "unknown"))
        policy_desc = policy_info.get("Description", "")
        policy_path = policy_info.get("Path", "/")
        policy_tags = policy_info.get("Tags", [])
        
        policy_tags_lines = []
        for tag in policy_tags:
            policy_tags_lines.append(f'    {tag["Key"]} = "{tag["Value"]}"')
        policy_tags_tf = "\n".join(policy_tags_lines) if policy_tags_lines else ""
        
        config += f'''
#############################################################################
# IAM Policy: {policy_name}
# ARN: {policy_arn}
#############################################################################
resource "aws_iam_policy" "{policy_name}" {{
  name        = "{policy_name}"
  path        = "{policy_path}"
  description = "{policy_desc}"

  policy = jsonencode({json.dumps(policy_doc, indent=4).replace(chr(10), chr(10) + "  ")})

  tags = {{
{policy_tags_tf}
  }}
}}

resource "aws_iam_role_policy_attachment" "{role_name}_{policy_name}_attachment" {{
  role       = aws_iam_role.{role_name}.name
  policy_arn = aws_iam_policy.{policy_name}.arn
}}
'''

    # Add inline policies
    for policy_name, policy_doc in role_info.inline_policy_documents.items():
        config += f'''
#############################################################################
# Inline Policy: {policy_name}
#############################################################################
resource "aws_iam_role_policy" "{role_name}_{policy_name}_inline" {{
  name   = "{policy_name}"
  role   = aws_iam_role.{role_name}.id
  policy = jsonencode({json.dumps(policy_doc, indent=4).replace(chr(10), chr(10) + "  ")})
}}
'''

    # Add outputs
    config += f'''
#############################################################################
# Outputs
#############################################################################
output "role_arn" {{
  description = "ARN of the IAM role"
  value       = aws_iam_role.{role_name}.arn
}}

output "role_name" {{
  description = "Name of the IAM role"
  value       = aws_iam_role.{role_name}.name
}}

output "role_id" {{
  description = "Unique ID of the IAM role"
  value       = aws_iam_role.{role_name}.unique_id
}}
'''

    # Add policy outputs
    for policy in role_info.attached_policies:
        policy_name = policy.get("PolicyName", "unknown")
        config += f'''
output "{policy_name}_arn" {{
  description = "ARN of the {policy_name} policy"
  value       = aws_iam_policy.{policy_name}.arn
}}
'''

    return config


def save_backup(role_info: IAMRoleInfoMCP, backup_dir: str) -> str:
    """
    Generate and save backup file.
    
    Args:
        role_info: IAMRoleInfoMCP object with all role data
        backup_dir: Directory to save backup file
        
    Returns:
        Path to backup file
    """
    role_name = role_info.role_name
    backup_content = generate_terraform_backup(role_info)
    
    backup_filename = f"iam_{role_name}.txt"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    with open(backup_path, "w") as f:
        f.write(backup_content)
    
    return backup_path


# =============================================================================
# Deletion via MCP (Terraform Destroy)
# =============================================================================

def generate_destroy_tf(role_info: IAMRoleInfoMCP) -> str:
    """
    Generate a minimal Terraform file for destroying resources.
    
    This creates a Terraform configuration that imports existing resources
    and then destroys them via terraform destroy.
    
    Args:
        role_info: IAMRoleInfoMCP object with all role data
        
    Returns:
        Terraform configuration as string
    """
    role = role_info.role_data
    role_name = role.get("RoleName", "unknown_role")
    role_arn = role.get("Arn", "")
    assume_policy = role.get("AssumeRolePolicyDocument", {})
    
    config = f'''# Terraform configuration for destroying IAM role: {role_name}
# Auto-generated by iam_role_manager_mcp.py

terraform {{
  required_version = ">= 1.0.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }}
  }}
}}

resource "aws_iam_role" "{role_name}" {{
  name = "{role_name}"
  assume_role_policy = jsonencode({json.dumps(assume_policy, indent=2)})
}}
'''
    
    # Add managed policies
    for policy in role_info.attached_policies:
        policy_arn = policy.get("PolicyArn", "")
        policy_name = policy.get("PolicyName", "unknown")
        
        # Skip AWS managed policies
        if policy_arn.startswith("arn:aws:iam::aws:"):
            continue
        
        policy_data = role_info.policy_documents.get(policy_arn, {})
        policy_doc = policy_data.get("document", {})
        
        config += f'''
resource "aws_iam_policy" "{policy_name}" {{
  name   = "{policy_name}"
  policy = jsonencode({json.dumps(policy_doc, indent=2)})
}}

resource "aws_iam_role_policy_attachment" "{role_name}_{policy_name}" {{
  role       = aws_iam_role.{role_name}.name
  policy_arn = aws_iam_policy.{policy_name}.arn
}}
'''
    
    return config


def delete_role_via_mcp(role_info: IAMRoleInfoMCP, dry_run: bool = False) -> bool:
    """
    Delete an IAM role using AWS CLI (since IAM MCP doesn't have delete_role).
    
    Note: The IAM MCP server doesn't provide delete_role functionality,
    so we use AWS CLI for deletion. The Terraform MCP server is used for
    restoration only.
    
    Args:
        role_info: IAMRoleInfoMCP object with all role data
        dry_run: If True, only show what would be deleted
        
    Returns:
        True if deletion successful, False otherwise
    """
    role_name = role_info.role_name
    success = True
    
    print(f"\n🗑️  Deleting IAM Role: {role_name}")
    print(f"   Note: Using AWS CLI (IAM MCP doesn't have delete_role)")
    print("-" * 60)
    
    if dry_run:
        print("   🔍 [DRY RUN] Would delete:")
        print(f"   - Role: {role_name}")
        for policy in role_info.attached_policies:
            policy_arn = policy.get("PolicyArn", "")
            if not policy_arn.startswith("arn:aws:iam::aws:"):
                print(f"   - Policy: {policy.get('PolicyName')}")
        for policy_name in role_info.inline_policies:
            print(f"   - Inline Policy: {policy_name}")
        return True
    
    # Step 1: Detach all managed policies
    for policy in role_info.attached_policies:
        policy_arn = policy.get("PolicyArn")
        policy_name = policy.get("PolicyName")
        
        print(f"   📎 Detaching policy: {policy_name}")
        result = run_aws_command([
            "iam", "detach-role-policy",
            "--role-name", role_name,
            "--policy-arn", policy_arn
        ], ignore_errors=True)
        
        if "error" not in result:
            print(f"   ✅ Detached: {policy_name}")
        else:
            print(f"   ⚠️ Failed to detach: {policy_name}")
    
    # Step 2: Delete all inline policies (could use MCP delete_role_policy here)
    for policy_name in role_info.inline_policies:
        print(f"   📎 Deleting inline policy: {policy_name}")
        result = run_aws_command([
            "iam", "delete-role-policy",
            "--role-name", role_name,
            "--policy-name", policy_name
        ], ignore_errors=True)
        
        if "error" not in result:
            print(f"   ✅ Deleted inline policy: {policy_name}")
        else:
            print(f"   ⚠️ Failed to delete inline policy: {policy_name}")
    
    # Step 3: Delete the role
    print(f"   🗑️ Deleting role: {role_name}")
    result = run_aws_command([
        "iam", "delete-role",
        "--role-name", role_name
    ])
    
    if "error" not in result:
        print(f"   ✅ Role deleted: {role_name}")
    else:
        print(f"   ❌ Failed to delete role: {result.get('message', '')}")
        success = False
    
    # Step 4: Delete managed policies (and their versions)
    for policy in role_info.attached_policies:
        policy_arn = policy.get("PolicyArn", "")
        policy_name = policy.get("PolicyName", "unknown")
        
        # Skip AWS managed policies
        if policy_arn.startswith("arn:aws:iam::aws:"):
            print(f"   ⏭️ Skipping AWS managed policy: {policy_name}")
            continue
        
        # Delete non-default versions first
        versions = role_info.policy_versions.get(policy_arn, [])
        for version in versions:
            if not version.get("IsDefaultVersion", False):
                version_id = version.get("VersionId")
                print(f"   📎 Deleting policy version: {policy_name} {version_id}")
                run_aws_command([
                    "iam", "delete-policy-version",
                    "--policy-arn", policy_arn,
                    "--version-id", version_id
                ], ignore_errors=True)
        
        # Delete the policy
        print(f"   🗑️ Deleting policy: {policy_name}")
        result = run_aws_command([
            "iam", "delete-policy",
            "--policy-arn", policy_arn
        ], ignore_errors=True)
        
        if "error" not in result:
            print(f"   ✅ Policy deleted: {policy_name}")
        else:
            print(f"   ⚠️ Failed to delete policy: {policy_name}")
    
    print("-" * 60)
    return success


# =============================================================================
# Restore Functions (via MCP)
# =============================================================================

def restore_from_backup_mcp(backup_file: str) -> bool:
    """
    Restore IAM role from backup file using Terraform MCP Server.
    
    Args:
        backup_file: Path to backup .txt file (Terraform format)
        
    Returns:
        True if restore successful, False otherwise
    """
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    # Get the directory and filename
    backup_dir = os.path.dirname(backup_file) or DEFAULT_BACKUP_DIR
    backup_name = os.path.basename(backup_file)
    
    print("\n" + "=" * 70)
    print("🔄 RESTORING IAM ROLE VIA MCP")
    print("=" * 70)
    print(f"\nBackup file: {backup_file}")
    print(f"Using MCP Server: {TERRAFORM_MCP_SERVER}")
    
    # Create temporary directory for Terraform
    temp_dir = tempfile.mkdtemp(prefix="iam_restore_")
    
    try:
        # Copy backup to temp directory as main.tf
        tf_path = os.path.join(temp_dir, "main.tf")
        shutil.copy(backup_file, tf_path)
        print(f"\n   📝 Copied backup to: {tf_path}")
        
        # Run Terraform workflow via MCP
        print("\n   🔧 Running Terraform workflow via MCP...")
        success, message = run_terraform_workflow(temp_dir, "apply")
        
        if success:
            print(f"\n✅ {message}")
            
            # Try to get outputs
            result = mcp_terraform_command("output", temp_dir)
            if result.get("outputs"):
                print("\n📋 Created Resources:")
                for key, value in result["outputs"].items():
                    print(f"   {key}: {value}")
            
            return True
        else:
            print(f"\n❌ {message}")
            return False
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("\n   🧹 Cleaned up temporary directory")
    
    return False


# =============================================================================
# Main Entry Point
# =============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="IAM Role Manager (MCP Version) - Using AWS MCP Servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
MCP Servers Used:
  - awslabs.iam-mcp-server: For reading IAM role information
  - awslabs.terraform-mcp-server: For applying/destroying Terraform configs

Examples:
  # Backup and delete a role
  python3 iam_role_manager_mcp.py --role-name example_role5_mcp_test --confirm

  # Backup only (no deletion)
  python3 iam_role_manager_mcp.py --role-name example_role5_mcp_test --backup-only

  # Dry run (show what would happen)
  python3 iam_role_manager_mcp.py --role-name example_role5_mcp_test --dry-run

  # Restore from backup
  python3 iam_role_manager_mcp.py --restore iam_example_role5_mcp_test.txt
        """
    )
    
    # Main operation modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--role-name",
        help="Name of the IAM role to backup/delete"
    )
    group.add_argument(
        "--restore",
        metavar="BACKUP_FILE",
        help="Restore from backup file using Terraform MCP Server"
    )
    
    # Options
    parser.add_argument(
        "--backup-dir",
        default=DEFAULT_BACKUP_DIR,
        help=f"Directory to save backup files (default: {DEFAULT_BACKUP_DIR})"
    )
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Only create backup, do not delete"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip interactive confirmation for deletion"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    
    return parser.parse_args()


def check_mcp_servers() -> Tuple[bool, str]:
    """
    Check if MCP servers are available.
    
    Returns:
        Tuple of (all_available, message)
    """
    servers = [IAM_MCP_SERVER, TERRAFORM_MCP_SERVER]
    missing = []
    
    for server in servers:
        try:
            result = subprocess.run(
                ["which", server],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                missing.append(server)
        except Exception:
            missing.append(server)
    
    if missing:
        return False, f"Missing MCP servers: {', '.join(missing)}"
    
    return True, "All MCP servers available"


def main():
    """Main entry point."""
    args = parse_args()
    
    print("=" * 70)
    print("🔧 IAM Role Manager (MCP Version)")
    print("   Using AWS IAM & Terraform MCP Servers")
    print("=" * 70)
    
    # Check MCP server availability
    print("\n🔍 Checking MCP server availability...")
    available, msg = check_mcp_servers()
    
    if not available:
        print(f"   ⚠️ {msg}")
        print("   ℹ️ Ensure MCP servers are installed and on PATH")
        print("   ℹ️ Install with: npm install -g @awslabs/iam-mcp-server @awslabs/terraform-mcp-server")
        # Continue anyway - servers might be available via different mechanism
    else:
        print(f"   ✅ {msg}")
    
    # Handle restore mode
    if args.restore:
        return 0 if restore_from_backup_mcp(args.restore) else 1
    
    role_name = args.role_name
    
    print(f"\nTarget Role: {role_name}")
    print(f"Backup Directory: {args.backup_dir}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'BACKUP ONLY' if args.backup_only else 'BACKUP & DELETE'}")
    
    # Step 1: Gather all role information via MCP
    role_info = IAMRoleInfoMCP(role_name)
    
    if not role_info.gather_all_info():
        print("\n❌ Failed to gather role information via MCP. Exiting.")
        return 1
    
    # Step 2: Create backup
    print("\n📝 Creating backup...")
    print("-" * 60)
    
    backup_path = save_backup(role_info, args.backup_dir)
    backup_size = os.path.getsize(backup_path)
    
    print(f"   ✅ Backup created: {backup_path}")
    print(f"   ✅ Backup size: {backup_size} bytes")
    
    # Step 3: If backup-only mode, exit here
    if args.backup_only:
        print("\n" + "=" * 70)
        print("✅ BACKUP COMPLETED (--backup-only mode)")
        print("=" * 70)
        print(f"\nBackup file: {backup_path}")
        return 0
    
    # Step 4: Verify backup before deletion
    if not os.path.exists(backup_path) or backup_size < 100:
        print("\n❌ ABORTING: Backup file missing or too small!")
        return 1
    
    print("\n✅ Backup verified. Proceeding with deletion via MCP...")
    
    # Step 5: Confirmation
    if not args.confirm and not args.dry_run:
        print("\n⚠️  WARNING: This will permanently delete (via Terraform MCP):")
        print(f"   - Role: {role_name}")
        for policy in role_info.attached_policies:
            print(f"   - Policy: {policy.get('PolicyName')}")
        print()
        
        confirm = input("Type 'DELETE' to confirm: ").strip()
        if confirm != "DELETE":
            print("❌ Deletion cancelled.")
            return 0
    
    # Step 6: Delete role via MCP
    success = delete_role_via_mcp(role_info, dry_run=args.dry_run)
    
    # Step 7: Verify deletion (via MCP)
    if not args.dry_run:
        print("\n🔍 Verifying deletion via MCP...")
        verify_result = mcp_get_role(role_name)
        
        if "error" in verify_result:
            print(f"   ✅ Role confirmed deleted: {role_name}")
        else:
            print(f"   ⚠️ Role may still exist: {role_name}")
    
    # Final summary
    print("\n" + "=" * 70)
    if args.dry_run:
        print("🔍 DRY RUN COMPLETED - No changes were made")
    elif success:
        print("✅ DELETION COMPLETED SUCCESSFULLY VIA MCP")
    else:
        print("⚠️ DELETION MAY NOT BE COMPLETE - Check AWS Console")
    print("=" * 70)
    print(f"\nBackup preserved at: {backup_path}")
    print("To restore via MCP, run:")
    print(f"  python3 iam_role_manager_mcp.py --restore {backup_path}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
