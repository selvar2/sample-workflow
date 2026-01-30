#!/usr/bin/env python3
"""
Destroy IAM Role Script

This script deletes an IAM role and its attached policies using Terraform via MCP.
IMPORTANT: Always ensure backup exists before running this script!

Usage: python3 destroy_iam_role6.py

Prerequisites:
    - Backup file must exist: iam_example_role6_mcp_test.txt
    - awslabs.terraform-mcp-server must be installed
    - AWS credentials must be configured
"""

import argparse
import json
import os
import subprocess
import sys


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Destroy IAM Role with backup verification")
    parser.add_argument("--confirm", action="store_true", 
                        help="Skip interactive confirmation (use with caution)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be deleted without actually deleting")
    return parser.parse_args()


# Configuration
ROLE_NAME = "example_role6_mcp_test"
POLICY_NAME = "example_policy6_mcp_test"
POLICY_ARN = "arn:aws:iam::175853813947:policy/example_policy6_mcp_test"
BACKUP_FILE = "/workspaces/sample-workflow/servicenow-mcp/terraform/iam_example_role6_mcp_test.txt"
WORKING_DIR = "/workspaces/sample-workflow/servicenow-mcp/terraform"
AWS_REGION = "us-east-1"


def verify_backup_exists() -> bool:
    """Verify the backup file exists before proceeding."""
    if os.path.exists(BACKUP_FILE):
        print(f"✅ Backup file exists: {BACKUP_FILE}")
        # Check file size to ensure it's not empty
        size = os.path.getsize(BACKUP_FILE)
        if size > 100:
            print(f"   File size: {size} bytes")
            return True
        else:
            print(f"❌ Backup file is too small ({size} bytes), may be corrupted")
            return False
    else:
        print(f"❌ Backup file NOT found: {BACKUP_FILE}")
        return False


def verify_role_exists() -> bool:
    """Verify the IAM role exists in AWS."""
    print(f"🔍 Checking if role exists: {ROLE_NAME}")
    result = subprocess.run(
        ["aws", "iam", "get-role", "--role-name", ROLE_NAME, "--no-cli-pager"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"✅ Role exists in AWS: {ROLE_NAME}")
        return True
    else:
        print(f"⚠️ Role not found in AWS: {ROLE_NAME}")
        return False


def detach_policy_from_role() -> bool:
    """Detach the managed policy from the role."""
    print(f"🔧 Detaching policy from role...")
    result = subprocess.run(
        ["aws", "iam", "detach-role-policy",
         "--role-name", ROLE_NAME,
         "--policy-arn", POLICY_ARN,
         "--no-cli-pager"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"   ✅ Policy detached: {POLICY_NAME}")
        return True
    else:
        print(f"   ⚠️ Could not detach policy (may already be detached): {result.stderr}")
        return True  # Continue anyway


def delete_role() -> bool:
    """Delete the IAM role."""
    print(f"🔧 Deleting IAM role: {ROLE_NAME}")
    result = subprocess.run(
        ["aws", "iam", "delete-role",
         "--role-name", ROLE_NAME,
         "--no-cli-pager"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"   ✅ Role deleted: {ROLE_NAME}")
        return True
    else:
        print(f"   ❌ Failed to delete role: {result.stderr}")
        return False


def delete_policy() -> bool:
    """Delete the IAM policy."""
    print(f"🔧 Deleting IAM policy: {POLICY_NAME}")
    result = subprocess.run(
        ["aws", "iam", "delete-policy",
         "--policy-arn", POLICY_ARN,
         "--no-cli-pager"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"   ✅ Policy deleted: {POLICY_NAME}")
        return True
    else:
        print(f"   ❌ Failed to delete policy: {result.stderr}")
        return False


def run_tf_mcp(command: str, timeout: int = 180) -> dict:
    """
    Run a Terraform command via AWS Terraform MCP Server.
    This is an alternative method using MCP protocol.
    """
    init_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "destroy-iam-client", "version": "1.0"}
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
                "working_directory": WORKING_DIR,
                "aws_region": AWS_REGION
            }
        }
    })
    
    input_data = f"{init_msg}\n{tool_msg}\n"
    
    try:
        result = subprocess.run(
            ["awslabs.terraform-mcp-server"],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.strip():
                try:
                    parsed = json.loads(line)
                    if parsed.get("id") == 1:
                        return parsed
                except json.JSONDecodeError:
                    continue
        
        return {"error": "No valid response", "raw": result.stdout[-500:]}
        
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout} seconds"}
    except FileNotFoundError:
        return {"error": "awslabs.terraform-mcp-server not found"}
    except Exception as e:
        return {"error": str(e)}


def main():
    args = parse_args()
    
    print("=" * 70)
    print("🗑️  IAM Role Destruction Script")
    print("=" * 70)
    print()
    print(f"Target Role: {ROLE_NAME}")
    print(f"Target Policy: {POLICY_NAME}")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    print()
    
    # Step 1: MANDATORY - Verify backup exists
    print("📍 Step 1: Verifying backup exists (MANDATORY)")
    print("-" * 50)
    if not verify_backup_exists():
        print()
        print("=" * 70)
        print("❌ ABORTING: Backup file not found!")
        print("   Run backup_iam_role6.py first to create backup.")
        print("=" * 70)
        sys.exit(1)
    print()
    
    # Step 2: Verify role exists
    print("📍 Step 2: Verifying role exists in AWS")
    print("-" * 50)
    if not verify_role_exists():
        print()
        print("⚠️ Role does not exist. Nothing to delete.")
        sys.exit(0)
    print()
    
    # Step 3: Confirm deletion
    print("📍 Step 3: Confirmation")
    print("-" * 50)
    print("⚠️  WARNING: This will permanently delete:")
    print(f"   - Role: {ROLE_NAME}")
    print(f"   - Policy: {POLICY_NAME}")
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN: Would delete the above resources. Exiting.")
        sys.exit(0)
    
    # Check for --confirm flag or interactive confirmation
    if args.confirm:
        print("✅ --confirm flag provided, proceeding with deletion...")
    else:
        confirm = input("Type 'DELETE' to confirm: ").strip()
        if confirm != "DELETE":
            print("❌ Deletion cancelled.")
            sys.exit(0)
    print()
    
    # Step 4: Detach policy from role
    print("📍 Step 4: Detaching policy from role")
    print("-" * 50)
    detach_policy_from_role()
    print()
    
    # Step 5: Delete role
    print("📍 Step 5: Deleting IAM role")
    print("-" * 50)
    if not delete_role():
        print("❌ Failed to delete role. Aborting.")
        sys.exit(1)
    print()
    
    # Step 6: Delete policy
    print("📍 Step 6: Deleting IAM policy")
    print("-" * 50)
    if not delete_policy():
        print("⚠️ Failed to delete policy (may have other attachments)")
    print()
    
    # Step 7: Verify deletion
    print("📍 Step 7: Verifying deletion")
    print("-" * 50)
    result = subprocess.run(
        ["aws", "iam", "get-role", "--role-name", ROLE_NAME, "--no-cli-pager"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"✅ Role confirmed deleted: {ROLE_NAME}")
    else:
        print(f"⚠️ Role may still exist: {ROLE_NAME}")
    print()
    
    print("=" * 70)
    print("✅ DELETION COMPLETED")
    print("=" * 70)
    print()
    print(f"Backup is preserved at: {BACKUP_FILE}")
    print("To restore, rename .txt to .tf and run terraform apply")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
