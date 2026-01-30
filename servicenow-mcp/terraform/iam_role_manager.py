#!/usr/bin/env python3
"""
IAM Role Manager - Unified Backup and Removal Script

A comprehensive script that handles the complete lifecycle of IAM role management:
- Dynamic role discovery and information gathering
- Automatic backup generation in Terraform format
- Safe deletion with mandatory backup verification
- Restore capability from backup files

Usage Examples:
    # Backup and delete a role
    python3 iam_role_manager.py --role-name example_role5_mcp_test --confirm

    # Backup only (no deletion)
    python3 iam_role_manager.py --role-name example_role5_mcp_test --backup-only

    # Dry run (show what would happen)
    python3 iam_role_manager.py --role-name example_role5_mcp_test --dry-run

    # Restore from backup
    python3 iam_role_manager.py --restore iam_example_role5_mcp_test.txt

Author: Generated for ServiceNow MCP Project
Date: 2026-01-30
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_BACKUP_DIR = "/workspaces/sample-workflow/servicenow-mcp/terraform"
AWS_REGION = "us-east-1"


# =============================================================================
# AWS CLI Wrapper Functions
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


def run_aws_command_simple(args: List[str]) -> bool:
    """
    Run an AWS CLI command and return success/failure.
    
    Args:
        args: List of AWS CLI arguments (without 'aws' prefix)
        
    Returns:
        True if command succeeded, False otherwise
    """
    cmd = ["aws"] + args + ["--no-cli-pager"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    except Exception:
        return False


# =============================================================================
# IAM Role Information Gathering
# =============================================================================

class IAMRoleInfo:
    """Container for all IAM role information."""
    
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
        Gather all information about the IAM role.
        
        Returns:
            True if role exists and info gathered, False otherwise
        """
        print(f"\n📋 Gathering information for role: {self.role_name}")
        print("-" * 60)
        
        # Step 1: Get role details
        print("   🔍 Fetching role details...")
        result = run_aws_command(["iam", "get-role", "--role-name", self.role_name])
        
        if "error" in result:
            if result["error"] == "NotFound":
                print(f"   ❌ Role not found: {self.role_name}")
                return False
            print(f"   ❌ Error: {result.get('message', 'Unknown error')}")
            return False
        
        self.role_data = result.get("Role", {})
        self.exists = True
        print(f"   ✅ Role ARN: {self.role_data.get('Arn')}")
        print(f"   ✅ Role ID: {self.role_data.get('RoleId')}")
        
        # Step 2: Get attached managed policies
        print("   🔍 Fetching attached policies...")
        result = run_aws_command([
            "iam", "list-attached-role-policies",
            "--role-name", self.role_name
        ])
        
        self.attached_policies = result.get("AttachedPolicies", [])
        print(f"   ✅ Attached policies: {len(self.attached_policies)}")
        
        # Step 3: Get inline policies
        print("   🔍 Fetching inline policies...")
        result = run_aws_command([
            "iam", "list-role-policies",
            "--role-name", self.role_name
        ])
        
        self.inline_policies = result.get("PolicyNames", [])
        print(f"   ✅ Inline policies: {len(self.inline_policies)}")
        
        # Step 4: Get policy documents for each attached policy
        for policy in self.attached_policies:
            policy_arn = policy.get("PolicyArn")
            policy_name = policy.get("PolicyName")
            
            print(f"   🔍 Fetching policy document: {policy_name}...")
            
            # Get policy metadata
            policy_info = run_aws_command([
                "iam", "get-policy",
                "--policy-arn", policy_arn
            ])
            
            policy_meta = policy_info.get("Policy", {})
            default_version = policy_meta.get("DefaultVersionId", "v1")
            
            # Get policy version document
            version_result = run_aws_command([
                "iam", "get-policy-version",
                "--policy-arn", policy_arn,
                "--version-id", default_version
            ])
            
            self.policy_documents[policy_arn] = {
                "policy_info": policy_meta,
                "document": version_result.get("PolicyVersion", {}).get("Document", {})
            }
            
            # Get all policy versions
            versions_result = run_aws_command([
                "iam", "list-policy-versions",
                "--policy-arn", policy_arn
            ])
            
            self.policy_versions[policy_arn] = versions_result.get("Versions", [])
            print(f"   ✅ Policy {policy_name}: {len(self.policy_versions[policy_arn])} version(s)")
        
        # Step 5: Get inline policy documents
        for policy_name in self.inline_policies:
            print(f"   🔍 Fetching inline policy: {policy_name}...")
            
            result = run_aws_command([
                "iam", "get-role-policy",
                "--role-name", self.role_name,
                "--policy-name", policy_name
            ])
            
            self.inline_policy_documents[policy_name] = result.get("PolicyDocument", {})
            print(f"   ✅ Inline policy {policy_name} retrieved")
        
        print("-" * 60)
        print("✅ All information gathered successfully")
        
        return True


# =============================================================================
# Backup Generation
# =============================================================================

def generate_terraform_backup(role_info: IAMRoleInfo) -> str:
    """
    Generate Terraform configuration from role information.
    
    Args:
        role_info: IAMRoleInfo object with all role data
        
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
# BACKUP FILE - Created before deletion
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


def save_backup(role_info: IAMRoleInfo, backup_dir: str) -> str:
    """
    Generate and save backup file.
    
    Args:
        role_info: IAMRoleInfo object with all role data
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
# Deletion Functions
# =============================================================================

def delete_role(role_info: IAMRoleInfo, dry_run: bool = False) -> bool:
    """
    Delete an IAM role and all associated resources.
    
    Args:
        role_info: IAMRoleInfo object with all role data
        dry_run: If True, only show what would be deleted
        
    Returns:
        True if deletion successful, False otherwise
    """
    role_name = role_info.role_name
    success = True
    
    print(f"\n🗑️  Deleting IAM Role: {role_name}")
    print("-" * 60)
    
    # Step 1: Detach all managed policies
    for policy in role_info.attached_policies:
        policy_arn = policy.get("PolicyArn")
        policy_name = policy.get("PolicyName")
        
        print(f"   📎 Detaching policy: {policy_name}")
        
        if not dry_run:
            result = run_aws_command_simple([
                "iam", "detach-role-policy",
                "--role-name", role_name,
                "--policy-arn", policy_arn
            ])
            
            if result:
                print(f"   ✅ Detached: {policy_name}")
            else:
                print(f"   ⚠️ Failed to detach: {policy_name}")
        else:
            print(f"   🔍 [DRY RUN] Would detach: {policy_name}")
    
    # Step 2: Delete all inline policies
    for policy_name in role_info.inline_policies:
        print(f"   📎 Deleting inline policy: {policy_name}")
        
        if not dry_run:
            result = run_aws_command_simple([
                "iam", "delete-role-policy",
                "--role-name", role_name,
                "--policy-name", policy_name
            ])
            
            if result:
                print(f"   ✅ Deleted inline policy: {policy_name}")
            else:
                print(f"   ⚠️ Failed to delete inline policy: {policy_name}")
        else:
            print(f"   🔍 [DRY RUN] Would delete inline policy: {policy_name}")
    
    # Step 3: Delete the role
    print(f"   🗑️ Deleting role: {role_name}")
    
    if not dry_run:
        result = run_aws_command_simple([
            "iam", "delete-role",
            "--role-name", role_name
        ])
        
        if result:
            print(f"   ✅ Role deleted: {role_name}")
        else:
            print(f"   ❌ Failed to delete role: {role_name}")
            success = False
    else:
        print(f"   🔍 [DRY RUN] Would delete role: {role_name}")
    
    # Step 4: Delete managed policies (and their versions)
    for policy in role_info.attached_policies:
        policy_arn = policy.get("PolicyArn")
        policy_name = policy.get("PolicyName")
        
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
                
                if not dry_run:
                    run_aws_command_simple([
                        "iam", "delete-policy-version",
                        "--policy-arn", policy_arn,
                        "--version-id", version_id
                    ])
                else:
                    print(f"   🔍 [DRY RUN] Would delete version: {version_id}")
        
        # Delete the policy
        print(f"   🗑️ Deleting policy: {policy_name}")
        
        if not dry_run:
            result = run_aws_command_simple([
                "iam", "delete-policy",
                "--policy-arn", policy_arn
            ])
            
            if result:
                print(f"   ✅ Policy deleted: {policy_name}")
            else:
                print(f"   ⚠️ Failed to delete policy: {policy_name} (may be attached elsewhere)")
        else:
            print(f"   🔍 [DRY RUN] Would delete policy: {policy_name}")
    
    print("-" * 60)
    
    return success


# =============================================================================
# Restore Functions
# =============================================================================

def restore_from_backup(backup_file: str) -> bool:
    """
    Provide instructions to restore from backup file.
    
    Args:
        backup_file: Path to backup file
        
    Returns:
        True if instructions provided successfully
    """
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    # Get the directory and filename
    backup_dir = os.path.dirname(backup_file)
    backup_name = os.path.basename(backup_file)
    tf_name = backup_name.replace(".txt", ".tf")
    tf_path = os.path.join(backup_dir, tf_name)
    
    print("\n" + "=" * 70)
    print("🔄 RESTORE INSTRUCTIONS")
    print("=" * 70)
    print()
    print(f"Backup file: {backup_file}")
    print()
    print("To restore this IAM role, run the following commands:")
    print()
    print(f"  # Step 1: Copy backup to Terraform file")
    print(f"  cp {backup_file} {tf_path}")
    print()
    print(f"  # Step 2: Initialize Terraform")
    print(f"  cd {backup_dir}")
    print(f"  terraform init")
    print()
    print(f"  # Step 3: Preview changes")
    print(f"  terraform plan -target=aws_iam_role.* -target=aws_iam_policy.*")
    print()
    print(f"  # Step 4: Apply changes")
    print(f"  terraform apply -target=aws_iam_role.* -target=aws_iam_policy.*")
    print()
    print("=" * 70)
    
    return True


# =============================================================================
# Main Entry Point
# =============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="IAM Role Manager - Backup and Removal Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backup and delete a role
  python3 iam_role_manager.py --role-name example_role5_mcp_test --confirm

  # Backup only (no deletion)
  python3 iam_role_manager.py --role-name example_role5_mcp_test --backup-only

  # Dry run (show what would happen)
  python3 iam_role_manager.py --role-name example_role5_mcp_test --dry-run

  # Restore from backup
  python3 iam_role_manager.py --restore iam_example_role5_mcp_test.txt
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
        help="Restore from backup file (shows instructions)"
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


def main():
    """Main entry point."""
    args = parse_args()
    
    print("=" * 70)
    print("🔧 IAM Role Manager - Backup and Removal Script")
    print("=" * 70)
    
    # Handle restore mode
    if args.restore:
        return 0 if restore_from_backup(args.restore) else 1
    
    role_name = args.role_name
    
    print(f"\nTarget Role: {role_name}")
    print(f"Backup Directory: {args.backup_dir}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'BACKUP ONLY' if args.backup_only else 'BACKUP & DELETE'}")
    
    # Step 1: Gather all role information
    role_info = IAMRoleInfo(role_name)
    
    if not role_info.gather_all_info():
        print("\n❌ Failed to gather role information. Exiting.")
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
    
    print("\n✅ Backup verified. Proceeding with deletion...")
    
    # Step 5: Confirmation
    if not args.confirm and not args.dry_run:
        print("\n⚠️  WARNING: This will permanently delete:")
        print(f"   - Role: {role_name}")
        for policy in role_info.attached_policies:
            print(f"   - Policy: {policy.get('PolicyName')}")
        print()
        
        confirm = input("Type 'DELETE' to confirm: ").strip()
        if confirm != "DELETE":
            print("❌ Deletion cancelled.")
            return 0
    
    # Step 6: Delete role and policies
    success = delete_role(role_info, dry_run=args.dry_run)
    
    # Step 7: Verify deletion
    if not args.dry_run:
        print("\n🔍 Verifying deletion...")
        result = run_aws_command(["iam", "get-role", "--role-name", role_name])
        
        if "error" in result and result["error"] == "NotFound":
            print(f"   ✅ Role confirmed deleted: {role_name}")
        else:
            print(f"   ⚠️ Role may still exist: {role_name}")
    
    # Final summary
    print("\n" + "=" * 70)
    if args.dry_run:
        print("🔍 DRY RUN COMPLETED - No changes were made")
    elif success:
        print("✅ DELETION COMPLETED SUCCESSFULLY")
    else:
        print("⚠️ DELETION COMPLETED WITH WARNINGS")
    print("=" * 70)
    print(f"\nBackup preserved at: {backup_path}")
    print("To restore, run:")
    print(f"  python3 iam_role_manager.py --restore {backup_path}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
