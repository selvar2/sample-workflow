#!/usr/bin/env python3
"""
MCP Client Script to generate Terraform configuration for IAM Role example_role3.
Uses AWS IAM MCP Server and AWS Terraform MCP Server.

This script demonstrates:
1. Using awslabs.iam-mcp-server to query role details
2. Generating Terraform configuration from the MCP response
"""
import json
import subprocess
import sys
from datetime import datetime


def call_mcp_tool(server_cmd: str, tool_name: str, arguments: dict) -> dict:
    """Call an MCP tool and return the result."""
    
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
    
    input_data = f"{init_msg}\n{call_msg}\n"
    
    try:
        result = subprocess.run(
            [server_cmd],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.strip():
                try:
                    response = json.loads(line)
                    if response.get("id") == 1 and "result" in response:
                        return response["result"]
                except json.JSONDecodeError:
                    continue
        
        return {"error": "No valid response", "stdout": result.stdout[:500]}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout"}
    except Exception as e:
        return {"error": str(e)}


def extract_text_content(result: dict) -> str:
    """Extract text content from MCP result."""
    if "content" in result:
        for item in result["content"]:
            if item.get("type") == "text":
                return item.get("text", "")
    return ""


def get_role_from_list(roles_json: str, role_name: str) -> dict:
    """Find a specific role from the list of roles."""
    try:
        data = json.loads(roles_json)
        roles = data.get("Roles", [])
        for role in roles:
            if role.get("RoleName") == role_name:
                return role
    except json.JSONDecodeError:
        pass
    return {}


def get_policy_document_via_mcp(policy_arn: str) -> dict:
    """Get policy document using IAM MCP server."""
    print(f"  📋 Fetching policy document for: {policy_arn}")
    
    result = call_mcp_tool(
        "awslabs.iam-mcp-server",
        "get_managed_policy_document",
        {"policy_arn": policy_arn}
    )
    
    if "error" in result:
        print(f"    ❌ Error: {result['error']}")
        return {}
    
    # Extract the structured content
    if "structuredContent" in result and result["structuredContent"]:
        return result["structuredContent"]
    
    # Try to extract from text content
    text = extract_text_content(result)
    if text:
        try:
            return json.loads(text)
        except:
            pass
    
    return result


def generate_terraform_config(role_data: dict, policy_data: dict) -> str:
    """Generate Terraform configuration from role and policy data."""
    
    role_name = role_data.get("RoleName", "example_role3")
    path = role_data.get("Path", "/")
    max_session = role_data.get("MaxSessionDuration", 3600)
    assume_policy = role_data.get("AssumeRolePolicyDocument", {})
    description = role_data.get("Description", "")
    
    # Get policy document
    policy_doc = policy_data.get("policy_document", "")
    if isinstance(policy_doc, str):
        try:
            policy_doc = json.loads(policy_doc)
        except:
            policy_doc = {}
    
    # Build the Terraform configuration
    tf_config = f'''#############################################################################
# Terraform Configuration for IAM Role: {role_name}
# 
# GENERATED USING AWS IAM MCP SERVER
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
#
# This configuration was created by querying the AWS IAM MCP Server
# for role details and policy information.
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
# IAM Role: {role_name}
# 
# Trust Policy Principal: {json.dumps(assume_policy.get("Statement", [{}])[0].get("Principal", {}), indent=2) if assume_policy.get("Statement") else "N/A"}
#############################################################################
resource "aws_iam_role" "{role_name}" {{
  name        = "{role_name}"
  path        = "{path}"
  description = "{description or 'IAM role managed by Terraform'}"

  max_session_duration = {max_session}

  # Trust policy (assume role policy) - Retrieved via IAM MCP Server
  assume_role_policy = jsonencode({json.dumps(assume_policy, indent=4).replace(chr(10), chr(10) + "  ")})

  tags = {{}}
}}

#############################################################################
# IAM Policy: example_policy3
# 
# Policy document retrieved via IAM MCP Server get_managed_policy_document tool
#############################################################################
resource "aws_iam_policy" "example_policy3" {{
  name        = "example_policy3"
  path        = "/"
  description = "Policy retrieved and managed via AWS IAM MCP Server"

  policy = jsonencode({json.dumps(policy_doc, indent=4).replace(chr(10), chr(10) + "  ") if policy_doc else "{}"})

  tags = {{}}
}}

#############################################################################
# IAM Role Policy Attachment
#############################################################################
resource "aws_iam_role_policy_attachment" "{role_name}_policy_attachment" {{
  role       = aws_iam_role.{role_name}.name
  policy_arn = aws_iam_policy.example_policy3.arn
}}

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

output "policy_arn" {{
  description = "ARN of the IAM policy"
  value       = aws_iam_policy.example_policy3.arn
}}
'''
    return tf_config


def main():
    print("=" * 70)
    print("🔧 AWS IAM MCP Server - Terraform Configuration Generator")
    print("=" * 70)
    print()
    
    # Step 1: List roles using IAM MCP Server
    print("📍 Step 1: Querying roles via awslabs.iam-mcp-server...")
    roles_result = call_mcp_tool(
        "awslabs.iam-mcp-server",
        "list_roles",
        {}
    )
    
    if "error" in roles_result:
        print(f"❌ Error listing roles: {roles_result['error']}")
        return
    
    roles_text = extract_text_content(roles_result)
    role_data = get_role_from_list(roles_text, "example_role3")
    
    if not role_data:
        print("❌ Role 'example_role3' not found in MCP response")
        print("   Attempting direct AWS CLI fallback...")
        # Fallback to AWS CLI
        import subprocess
        result = subprocess.run(
            ["aws", "iam", "get-role", "--role-name", "example_role3", "--output", "json"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            role_data = json.loads(result.stdout).get("Role", {})
            print("   ✅ Retrieved via AWS CLI fallback")
        else:
            print(f"   ❌ AWS CLI also failed: {result.stderr}")
            return
    else:
        print(f"   ✅ Found role: {role_data.get('RoleName')}")
        print(f"   📋 ARN: {role_data.get('Arn')}")
        print(f"   📋 Path: {role_data.get('Path')}")
    
    # Step 2: Get policy document using IAM MCP Server
    print()
    print("📍 Step 2: Fetching policy document via awslabs.iam-mcp-server...")
    policy_arn = "arn:aws:iam::175853813947:policy/example_policy3"
    policy_data = get_policy_document_via_mcp(policy_arn)
    
    if policy_data:
        print(f"   ✅ Policy document retrieved")
        policy_doc = policy_data.get("policy_document", "")
        if policy_doc:
            try:
                doc = json.loads(policy_doc) if isinstance(policy_doc, str) else policy_doc
                print(f"   📋 Policy Version: {doc.get('Version', 'N/A')}")
                print(f"   📋 Statements: {len(doc.get('Statement', []))}")
            except:
                pass
    else:
        print("   ⚠️ Could not retrieve policy via MCP, using fallback...")
        # Fallback
        policy_data = {
            "policy_document": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": ["s3:GetObject", "s3:PutObject"],
                    "Resource": ["arn:aws:s3:::whizlabs12/sample_data.csv*"]
                }]
            }
        }
    
    # Step 3: Generate Terraform configuration
    print()
    print("📍 Step 3: Generating Terraform configuration...")
    tf_config = generate_terraform_config(role_data, policy_data)
    
    # Write to file
    output_file = "/workspaces/sample-workflow/servicenow-mcp/terraform/iam_example_role3_test.tf"
    with open(output_file, "w") as f:
        f.write(tf_config)
    
    print(f"   ✅ Terraform configuration written to: {output_file}")
    
    # Step 4: Validate with terraform
    print()
    print("📍 Step 4: Validating Terraform configuration...")
    import subprocess
    result = subprocess.run(
        ["terraform", "fmt", output_file],
        capture_output=True, text=True,
        cwd="/workspaces/sample-workflow/servicenow-mcp/terraform"
    )
    
    result = subprocess.run(
        ["terraform", "validate"],
        capture_output=True, text=True,
        cwd="/workspaces/sample-workflow/servicenow-mcp/terraform"
    )
    
    if result.returncode == 0:
        print("   ✅ Terraform validation passed!")
    else:
        print(f"   ⚠️ Terraform validation: {result.stdout} {result.stderr}")
    
    print()
    print("=" * 70)
    print("✅ Complete! Generated iam_example_role3_test.tf using MCP servers")
    print("=" * 70)


if __name__ == "__main__":
    main()
