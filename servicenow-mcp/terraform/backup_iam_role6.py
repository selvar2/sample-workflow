#!/usr/bin/env python3
"""
Backup IAM Role Script

This script backs up an IAM role and its attached policies to a Terraform format file.
Uses AWS CLI with --no-cli-pager to avoid interactive output.

Usage: python3 backup_iam_role6.py [role_name] [output_file]

Example:
    python3 backup_iam_role6.py example_role6_mcp_test iam_example_role6_mcp_test.txt
"""

import json
import subprocess
import sys
from datetime import datetime


def run_aws_command(args: list) -> dict:
    """Run an AWS CLI command and return the JSON result."""
    cmd = ["aws"] + args + ["--no-cli-pager", "--output", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return {}
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error running command: {e}")
        return {}


def get_role_details(role_name: str) -> dict:
    """Get IAM role details."""
    print(f"📋 Fetching role details for: {role_name}")
    result = run_aws_command(["iam", "get-role", "--role-name", role_name])
    return result.get("Role", {})


def get_attached_policies(role_name: str) -> list:
    """Get list of attached managed policies."""
    print(f"📋 Fetching attached policies for: {role_name}")
    result = run_aws_command(["iam", "list-attached-role-policies", "--role-name", role_name])
    return result.get("AttachedPolicies", [])


def get_inline_policies(role_name: str) -> list:
    """Get list of inline policies."""
    print(f"📋 Fetching inline policies for: {role_name}")
    result = run_aws_command(["iam", "list-role-policies", "--role-name", role_name])
    return result.get("PolicyNames", [])


def get_policy_document(policy_arn: str) -> dict:
    """Get policy document for a managed policy."""
    print(f"📋 Fetching policy document: {policy_arn}")
    
    # First get the policy to find the default version
    policy_info = run_aws_command(["iam", "get-policy", "--policy-arn", policy_arn])
    policy = policy_info.get("Policy", {})
    version_id = policy.get("DefaultVersionId", "v1")
    
    # Get the policy version document
    version_result = run_aws_command([
        "iam", "get-policy-version",
        "--policy-arn", policy_arn,
        "--version-id", version_id
    ])
    
    return {
        "policy_info": policy,
        "document": version_result.get("PolicyVersion", {}).get("Document", {})
    }


def generate_terraform_config(role_data: dict, policies_data: list) -> str:
    """Generate Terraform configuration from role and policy data."""
    
    role_name = role_data.get("RoleName", "unknown_role")
    role_id = role_data.get("RoleId", "")
    path = role_data.get("Path", "/")
    max_session = role_data.get("MaxSessionDuration", 3600)
    description = role_data.get("Description", "")
    assume_policy = role_data.get("AssumeRolePolicyDocument", {})
    tags = role_data.get("Tags", [])
    create_date = role_data.get("CreateDate", "")
    
    # Convert tags list to dict
    tags_dict = {tag["Key"]: tag["Value"] for tag in tags}
    tags_tf = "\n    ".join([f'{k} = "{v}"' for k, v in tags_dict.items()]) if tags_dict else ""
    
    # Start building the config
    config = f'''#############################################################################
# Terraform Configuration for IAM Role: {role_name}
# 
# BACKUP FILE - Created before deletion
# This configuration can be used to recreate the IAM role with ARN:
#   {role_data.get("Arn", "")}
#
# Role Details:
#   - Name: {role_name}
#   - RoleId: {role_id}
#   - Path: {path}
#   - Max Session Duration: {max_session} seconds
#   - Created: {create_date}
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
#   region  = "us-east-1"
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

    # Add each policy
    for policy_data in policies_data:
        policy_info = policy_data.get("policy_info", {})
        policy_doc = policy_data.get("document", {})
        policy_name = policy_info.get("PolicyName", "unknown_policy")
        policy_desc = policy_info.get("Description", "")
        policy_path = policy_info.get("Path", "/")
        policy_tags = policy_info.get("Tags", [])
        
        policy_tags_dict = {tag["Key"]: tag["Value"] for tag in policy_tags}
        policy_tags_tf = "\n    ".join([f'{k} = "{v}"' for k, v in policy_tags_dict.items()]) if policy_tags_dict else ""
        
        config += f'''
#############################################################################
# IAM Policy: {policy_name}
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

#############################################################################
# IAM Role Policy Attachment: {role_name} <- {policy_name}
#############################################################################
resource "aws_iam_role_policy_attachment" "{role_name}_{policy_name}_attachment" {{
  role       = aws_iam_role.{role_name}.name
  policy_arn = aws_iam_policy.{policy_name}.arn
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

    return config


def main():
    # Parse arguments
    role_name = sys.argv[1] if len(sys.argv) > 1 else "example_role6_mcp_test"
    output_file = sys.argv[2] if len(sys.argv) > 2 else f"iam_{role_name}.txt"
    
    print("=" * 70)
    print("🔧 IAM Role Backup Script")
    print("=" * 70)
    print(f"Role Name: {role_name}")
    print(f"Output File: {output_file}")
    print()
    
    # Step 1: Get role details
    role_data = get_role_details(role_name)
    if not role_data:
        print(f"❌ Failed to get role details for: {role_name}")
        sys.exit(1)
    print(f"   ✅ Role ARN: {role_data.get('Arn')}")
    
    # Step 2: Get attached policies
    attached_policies = get_attached_policies(role_name)
    print(f"   ✅ Attached policies: {len(attached_policies)}")
    
    # Step 3: Get policy documents
    policies_data = []
    for policy in attached_policies:
        policy_arn = policy.get("PolicyArn")
        policy_data = get_policy_document(policy_arn)
        policies_data.append(policy_data)
        print(f"   ✅ Policy document retrieved: {policy.get('PolicyName')}")
    
    # Step 4: Check for inline policies
    inline_policies = get_inline_policies(role_name)
    if inline_policies:
        print(f"   ⚠️ Inline policies found (not backed up): {inline_policies}")
    else:
        print(f"   ✅ No inline policies")
    
    # Step 5: Generate Terraform configuration
    print()
    print("📝 Generating Terraform configuration...")
    tf_config = generate_terraform_config(role_data, policies_data)
    
    # Step 6: Write to file
    output_path = f"/workspaces/sample-workflow/servicenow-mcp/terraform/{output_file}"
    with open(output_path, "w") as f:
        f.write(tf_config)
    
    print(f"   ✅ Backup written to: {output_path}")
    
    print()
    print("=" * 70)
    print("✅ BACKUP COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print()
    print(f"To restore this role, copy {output_file} to a .tf file and run:")
    print("  terraform init")
    print("  terraform plan")
    print("  terraform apply")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
