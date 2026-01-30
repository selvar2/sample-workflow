# IAM Role Manager - AWS CLI Version

> **Script:** `iam_role_manager.py`  
> **Version:** 1.0.0  
> **Author:** ServiceNow MCP Project  
> **Date:** 2026-01-30

A comprehensive Python script for managing AWS IAM roles using **direct AWS CLI commands**. Provides backup, deletion, and restoration capabilities with safety features.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [CLI Reference](#3-cli-reference)
4. [Input/Output Documentation](#4-inputoutput-documentation)
5. [Terminal Output Examples](#5-terminal-output-examples)
6. [Testing Guide](#6-testing-guide)
7. [Alternative Approaches](#7-alternative-approaches)
8. [Technical Implementation](#8-technical-implementation)
9. [Troubleshooting](#9-troubleshooting)
10. [Quick Reference](#10-quick-reference)

---

## 1. Overview

### Purpose

`iam_role_manager.py` automates the complete lifecycle of IAM role management:

- **Backup**: Captures complete role configuration in Terraform format
- **Delete**: Safely removes roles with mandatory backup verification
- **Restore**: Provides instructions for recreating roles from backups

### Key Features

| Feature                  | Description                                                        |
| ------------------------ | ------------------------------------------------------------------ |
| Dynamic Role Discovery   | Automatically gathers all role metadata, policies, and attachments |
| Terraform Backup Format  | Backups are valid `.tf` files ready for `terraform apply`          |
| Safety First             | Requires backup verification before deletion                       |
| Non-Destructive Options  | `--dry-run` and `--backup-only` modes                              |
| Interactive Confirmation | Requires typing "DELETE" unless `--confirm` is used                |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    iam_role_manager.py                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Gather     │───▶│  Generate   │───▶│  Delete     │         │
│  │  Role Info  │    │  Backup     │    │  Resources  │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ AWS CLI     │    │ .txt File   │    │ AWS CLI     │         │
│  │ get-role    │    │ (Terraform) │    │ delete-*    │         │
│  │ list-*      │    │             │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                                     │                 │
│         ▼                                     ▼                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    AWS IAM API                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

### Required Tools

| Tool      | Version | Installation                  |
| --------- | ------- | ----------------------------- |
| Python    | 3.8+    | Pre-installed in devcontainer |
| AWS CLI   | 2.x     | Pre-installed in devcontainer |
| Terraform | 1.0+    | Required only for restore     |

### AWS Credentials

```bash
# Verify AWS credentials are configured
aws sts get-caller-identity

# Expected output:
{
    "UserId": "AROASR4NUIC5...",
    "Account": "175853813947",
    "Arn": "arn:aws:sts::175853813947:assumed-role/..."
}
```

### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:DeleteRole",
        "iam:ListAttachedRolePolicies",
        "iam:DetachRolePolicy",
        "iam:ListRolePolicies",
        "iam:DeleteRolePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions",
        "iam:DeletePolicyVersion",
        "iam:DeletePolicy"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 3. CLI Reference

### Synopsis

```bash
python3 iam_role_manager.py (--role-name ROLE_NAME | --restore BACKUP_FILE)
                            [--backup-dir BACKUP_DIR]
                            [--backup-only]
                            [--confirm]
                            [--dry-run]
```

### Arguments

| Argument                | Required | Description                                  |
| ----------------------- | -------- | -------------------------------------------- |
| `--role-name ROLE_NAME` | Yes\*    | Name of the IAM role to backup/delete        |
| `--restore BACKUP_FILE` | Yes\*    | Path to backup file for restore instructions |

\*One of `--role-name` or `--restore` is required (mutually exclusive)

### Options

| Option             | Default                     | Description                                    |
| ------------------ | --------------------------- | ---------------------------------------------- |
| `--backup-dir DIR` | `/workspaces/.../terraform` | Directory to save backup files                 |
| `--backup-only`    | False                       | Only create backup, do not delete              |
| `--confirm`        | False                       | Skip interactive confirmation (for automation) |
| `--dry-run`        | False                       | Show what would happen without making changes  |

### Flag Combinations

| Mode               | Flags                         | Behavior                    |
| ------------------ | ----------------------------- | --------------------------- |
| Backup Only        | `--role-name X --backup-only` | Creates backup, exits       |
| Dry Run            | `--role-name X --dry-run`     | Shows actions, no changes   |
| Interactive Delete | `--role-name X`               | Backup + prompt + delete    |
| Automated Delete   | `--role-name X --confirm`     | Backup + delete (no prompt) |
| Restore            | `--restore backup.txt`        | Shows restore instructions  |

---

## 4. Input/Output Documentation

### Input Parameters

#### Role Name Input

```bash
# Direct role name
--role-name example_role4_mcp_test

# Role name with special characters (use quotes)
--role-name "my-role-with-dashes"
```

#### Backup File Input (for restore)

```bash
# Absolute path
--restore /workspaces/sample-workflow/servicenow-mcp/terraform/iam_example_role.txt

# Relative path (from current directory)
--restore ./iam_example_role.txt
```

### Output Files

#### Backup File Format

**Filename Pattern:** `iam_{role_name}.txt`

**Location:** `--backup-dir` (default: `/workspaces/sample-workflow/servicenow-mcp/terraform/`)

**Content Structure (Terraform HCL):**

```hcl
#############################################################################
# Terraform Configuration for IAM Role: example_role4_mcp_test
#
# BACKUP FILE - Created before deletion
# Role Details:
#   - Name: example_role4_mcp_test
#   - RoleId: AROASR4NUIC5UNZ6TZMX7
#   - Path: /
#   - Max Session Duration: 3600 seconds
#   - Attached Managed Policies: 1
#   - Inline Policies: 0
#
# Backup Generated: 2026-01-30 10:45:32
#############################################################################

terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
}

resource "aws_iam_role" "example_role4_mcp_test" {
  name        = "example_role4_mcp_test"
  path        = "/"
  description = "IAM role for AWS Glue"

  max_session_duration = 3600

  assume_role_policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "glue.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  })

  tags = {
    GeneratedAt = "2025-12-31"
    GeneratedBy = "AWS-IAM-MCP-Server"
  }
}

resource "aws_iam_policy" "example_policy4_mcp_test" {
  name        = "example_policy4_mcp_test"
  description = "S3 access policy"

  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:PutObject"],
        "Resource": ["arn:aws:s3:::whizlabs12/sample_data.csv*"]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "example_role4_mcp_test_example_policy4_mcp_test_attachment" {
  role       = aws_iam_role.example_role4_mcp_test.name
  policy_arn = aws_iam_policy.example_policy4_mcp_test.arn
}

output "role_arn" {
  value = aws_iam_role.example_role4_mcp_test.arn
}
```

---

## 5. Terminal Output Examples

### Backup Only Mode

```bash
$ python3 iam_role_manager.py --role-name example_role4_mcp_test --backup-only
```

**Output:**

```
======================================================================
🔧 IAM Role Manager - Backup and Removal Script
======================================================================

Target Role: example_role4_mcp_test
Backup Directory: /workspaces/sample-workflow/servicenow-mcp/terraform
Mode: BACKUP ONLY

📋 Gathering information for role: example_role4_mcp_test
------------------------------------------------------------
   🔍 Fetching role details...
   ✅ Role ARN: arn:aws:iam::175853813947:role/example_role4_mcp_test
   ✅ Role ID: AROASR4NUIC5UNZ6TZMX7
   🔍 Fetching attached policies...
   ✅ Attached policies: 1
   🔍 Fetching inline policies...
   ✅ Inline policies: 0
   🔍 Fetching policy document: example_policy4_mcp_test...
   ✅ Policy example_policy4_mcp_test: 1 version(s)
------------------------------------------------------------
✅ All information gathered successfully

📝 Creating backup...
------------------------------------------------------------
   ✅ Backup created: /workspaces/.../iam_example_role4_mcp_test.txt
   ✅ Backup size: 3693 bytes

======================================================================
✅ BACKUP COMPLETED (--backup-only mode)
======================================================================

Backup file: /workspaces/.../iam_example_role4_mcp_test.txt
```

### Backup and Delete with Confirmation

```bash
$ python3 iam_role_manager.py --role-name example_role4_mcp_test --confirm
```

**Output:**

```
======================================================================
🔧 IAM Role Manager - Backup and Removal Script
======================================================================

Target Role: example_role4_mcp_test
Backup Directory: /workspaces/sample-workflow/servicenow-mcp/terraform
Mode: BACKUP & DELETE

📋 Gathering information for role: example_role4_mcp_test
------------------------------------------------------------
   🔍 Fetching role details...
   ✅ Role ARN: arn:aws:iam::175853813947:role/example_role4_mcp_test
   ✅ Role ID: AROASR4NUIC5UNZ6TZMX7
   🔍 Fetching attached policies...
   ✅ Attached policies: 1
   🔍 Fetching inline policies...
   ✅ Inline policies: 0
   🔍 Fetching policy document: example_policy4_mcp_test...
   ✅ Policy example_policy4_mcp_test: 1 version(s)
------------------------------------------------------------
✅ All information gathered successfully

📝 Creating backup...
------------------------------------------------------------
   ✅ Backup created: /workspaces/.../iam_example_role4_mcp_test.txt
   ✅ Backup size: 3693 bytes

✅ Backup verified. Proceeding with deletion...

🗑️  Deleting IAM Role: example_role4_mcp_test
------------------------------------------------------------
   📎 Detaching policy: example_policy4_mcp_test
   ✅ Detached: example_policy4_mcp_test
   🗑️ Deleting role: example_role4_mcp_test
   ✅ Role deleted: example_role4_mcp_test
   🗑️ Deleting policy: example_policy4_mcp_test
   ✅ Policy deleted: example_policy4_mcp_test
------------------------------------------------------------

🔍 Verifying deletion...
   ✅ Role confirmed deleted: example_role4_mcp_test

======================================================================
✅ DELETION COMPLETED SUCCESSFULLY
======================================================================

Backup preserved at: /workspaces/.../iam_example_role4_mcp_test.txt
To restore, run:
  python3 iam_role_manager.py --restore /workspaces/.../iam_example_role4_mcp_test.txt
```

### Dry Run Mode

```bash
$ python3 iam_role_manager.py --role-name example_role4_mcp_test --dry-run
```

**Output:**

```
======================================================================
🔧 IAM Role Manager - Backup and Removal Script
======================================================================

Target Role: example_role4_mcp_test
Mode: DRY RUN

📋 Gathering information for role: example_role4_mcp_test
...
✅ All information gathered successfully

📝 Creating backup...
   ✅ Backup created: /workspaces/.../iam_example_role4_mcp_test.txt

🗑️  Deleting IAM Role: example_role4_mcp_test
------------------------------------------------------------
   🔍 [DRY RUN] Would detach: example_policy4_mcp_test
   🔍 [DRY RUN] Would delete role: example_role4_mcp_test
   🔍 [DRY RUN] Would delete policy: example_policy4_mcp_test
------------------------------------------------------------

======================================================================
🔍 DRY RUN COMPLETED - No changes were made
======================================================================
```

### Restore Mode

```bash
$ python3 iam_role_manager.py --restore /workspaces/.../iam_example_role4_mcp_test.txt
```

**Output:**

```
======================================================================
🔧 IAM Role Manager - Backup and Removal Script
======================================================================

======================================================================
🔄 RESTORE INSTRUCTIONS
======================================================================

Backup file: /workspaces/.../iam_example_role4_mcp_test.txt

To restore this IAM role, run the following commands:

  # Step 1: Copy backup to Terraform file
  cp /workspaces/.../iam_example_role4_mcp_test.txt /workspaces/.../iam_example_role4_mcp_test.tf

  # Step 2: Initialize Terraform
  cd /workspaces/sample-workflow/servicenow-mcp/terraform
  terraform init

  # Step 3: Preview changes
  terraform plan -target=aws_iam_role.* -target=aws_iam_policy.*

  # Step 4: Apply changes
  terraform apply -target=aws_iam_role.* -target=aws_iam_policy.*

======================================================================
```

---

## 6. Testing Guide

### Step 1: Create a Test Role

```bash
# Create a test IAM role using AWS CLI
aws iam create-role \
  --role-name test_role_for_deletion \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --no-cli-pager

# Create and attach a test policy
aws iam create-policy \
  --policy-name test_policy_for_deletion \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::test-bucket/*"
    }]
  }' \
  --no-cli-pager

# Get the policy ARN from output, then attach
aws iam attach-role-policy \
  --role-name test_role_for_deletion \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT:policy/test_policy_for_deletion \
  --no-cli-pager
```

### Step 2: Test Backup Only

```bash
cd /workspaces/sample-workflow/servicenow-mcp/terraform

# Run backup only
python3 iam_role_manager.py --role-name test_role_for_deletion --backup-only

# Verify backup file was created
ls -la iam_test_role_for_deletion.txt

# Check backup content
head -50 iam_test_role_for_deletion.txt
```

### Step 3: Test Dry Run

```bash
# Run dry run (shows what would happen)
python3 iam_role_manager.py --role-name test_role_for_deletion --dry-run

# Verify role still exists
aws iam get-role --role-name test_role_for_deletion --no-cli-pager
```

### Step 4: Test Deletion

```bash
# Delete with confirmation flag (for automation)
python3 iam_role_manager.py --role-name test_role_for_deletion --confirm

# Verify role was deleted
aws iam get-role --role-name test_role_for_deletion --no-cli-pager 2>&1
# Expected: NoSuchEntity error
```

### Step 5: Test Restore

```bash
# Option A: Show restore instructions
python3 iam_role_manager.py --restore iam_test_role_for_deletion.txt

# Option B: Manual restore using Terraform
cp iam_test_role_for_deletion.txt iam_test_role_for_deletion.tf
terraform init
terraform plan
terraform apply -auto-approve

# Verify role was restored
aws iam get-role --role-name test_role_for_deletion --no-cli-pager
```

### Verification Commands

```bash
# Check if role exists
aws iam get-role --role-name ROLE_NAME --no-cli-pager

# List attached policies
aws iam list-attached-role-policies --role-name ROLE_NAME --no-cli-pager

# List inline policies
aws iam list-role-policies --role-name ROLE_NAME --no-cli-pager

# Check policy exists
aws iam get-policy --policy-arn POLICY_ARN --no-cli-pager
```

---

## 7. Alternative Approaches

### Comparison Table

| Approach                             | Pros                                            | Cons                         | Best For                     |
| ------------------------------------ | ----------------------------------------------- | ---------------------------- | ---------------------------- |
| **iam_role_manager.py (AWS CLI)**    | Simple, no extra dependencies, works everywhere | No MCP integration           | Quick operations, automation |
| **iam_role_manager_mcp.py (Hybrid)** | Uses MCP where available, Terraform restore     | Requires MCP servers         | MCP-integrated workflows     |
| **Direct AWS CLI**                   | Maximum control                                 | No backup automation         | One-off manual tasks         |
| **Boto3 Python SDK**                 | Programmatic, testable                          | More code to maintain        | Custom applications          |
| **Terraform Only**                   | State management, IaC                           | Requires import for existing | New infrastructure           |
| **AWS Console**                      | Visual, easy                                    | No automation, audit trail   | Learning, exploration        |

### When to Use Each Approach

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Decision Tree: Which Approach?                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Need MCP integration?                                              │
│       │                                                             │
│       ├── Yes ──▶ Use iam_role_manager_mcp.py                      │
│       │                                                             │
│       └── No ──▶ Need automation?                                  │
│                      │                                              │
│                      ├── Yes ──▶ Use iam_role_manager.py           │
│                      │                                              │
│                      └── No ──▶ One-time task?                     │
│                                     │                               │
│                                     ├── Yes ──▶ Direct AWS CLI     │
│                                     │                               │
│                                     └── No ──▶ AWS Console         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Direct AWS CLI Alternative

```bash
# Manual backup (less comprehensive)
aws iam get-role --role-name ROLE_NAME > role_backup.json

# Manual deletion sequence
aws iam detach-role-policy --role-name ROLE_NAME --policy-arn POLICY_ARN
aws iam delete-role-policy --role-name ROLE_NAME --policy-name POLICY_NAME
aws iam delete-role --role-name ROLE_NAME
aws iam delete-policy --policy-arn POLICY_ARN
```

### Boto3 Alternative

```python
import boto3

iam = boto3.client('iam')

# Get role
role = iam.get_role(RoleName='example_role')

# Delete sequence
iam.detach_role_policy(RoleName='example_role', PolicyArn='arn:...')
iam.delete_role(RoleName='example_role')
```

---

## 8. Technical Implementation

### AWS CLI Wrapper Functions

The script uses subprocess to call AWS CLI:

```python
def run_aws_command(args: List[str], ignore_errors: bool = False) -> Dict[str, Any]:
    """
    Run an AWS CLI command and return the JSON result.
    """
    cmd = ["aws"] + args + ["--no-cli-pager", "--output", "json"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        if "NoSuchEntity" in result.stderr:
            return {"error": "NotFound"}
        return {"error": "CommandFailed", "message": result.stderr}

    return json.loads(result.stdout)
```

### Key AWS CLI Commands Used

| Operation              | AWS CLI Command                                             |
| ---------------------- | ----------------------------------------------------------- |
| Get Role               | `aws iam get-role --role-name X`                            |
| List Attached Policies | `aws iam list-attached-role-policies --role-name X`         |
| List Inline Policies   | `aws iam list-role-policies --role-name X`                  |
| Get Policy             | `aws iam get-policy --policy-arn X`                         |
| Get Policy Version     | `aws iam get-policy-version --policy-arn X --version-id v1` |
| Detach Policy          | `aws iam detach-role-policy --role-name X --policy-arn Y`   |
| Delete Role            | `aws iam delete-role --role-name X`                         |
| Delete Policy          | `aws iam delete-policy --policy-arn X`                      |

### Deletion Order (Important!)

```
1. Detach all managed policies from role
2. Delete all inline policies from role
3. Delete the role itself
4. Delete non-default policy versions
5. Delete the managed policies
```

⚠️ **Order matters!** You cannot delete a role with attached policies, and you cannot delete a policy with non-default versions.

---

## 9. Troubleshooting

### Common Errors

#### Error: Role Not Found

```
❌ Role not found: example_role_xyz
```

**Solution:** Verify the role name is correct:

```bash
aws iam list-roles --no-cli-pager | grep example_role
```

#### Error: Cannot Delete Policy with Multiple Versions

```
An error occurred (DeleteConflict) when calling the DeletePolicy operation:
Cannot delete a policy with multiple versions
```

**Solution:** The script handles this automatically by deleting non-default versions first. If it fails, manually delete versions:

```bash
aws iam list-policy-versions --policy-arn POLICY_ARN --no-cli-pager
aws iam delete-policy-version --policy-arn POLICY_ARN --version-id v1
```

#### Error: Cannot Delete Role with Attached Policies

```
An error occurred (DeleteConflict) when calling the DeleteRole operation:
Cannot delete entity, must detach all policies first
```

**Solution:** The script handles this, but if manual:

```bash
aws iam list-attached-role-policies --role-name ROLE_NAME --no-cli-pager
aws iam detach-role-policy --role-name ROLE_NAME --policy-arn POLICY_ARN
```

#### Error: Access Denied

```
An error occurred (AccessDenied) when calling the DeleteRole operation
```

**Solution:** Check IAM permissions. You need `iam:DeleteRole`, `iam:DeletePolicy`, etc.

---

## 10. Quick Reference

### Command Cheat Sheet

| Task                 | Command                                                       |
| -------------------- | ------------------------------------------------------------- |
| Backup only          | `python3 iam_role_manager.py --role-name X --backup-only`     |
| Dry run              | `python3 iam_role_manager.py --role-name X --dry-run`         |
| Delete (interactive) | `python3 iam_role_manager.py --role-name X`                   |
| Delete (automated)   | `python3 iam_role_manager.py --role-name X --confirm`         |
| Restore instructions | `python3 iam_role_manager.py --restore backup.txt`            |
| Custom backup dir    | `python3 iam_role_manager.py --role-name X --backup-dir /tmp` |

### One-Liner Examples

```bash
# Backup and delete in one command
python3 iam_role_manager.py --role-name my_role --confirm

# Backup multiple roles (loop)
for role in role1 role2 role3; do
  python3 iam_role_manager.py --role-name $role --backup-only
done

# Delete multiple roles (be careful!)
for role in role1 role2 role3; do
  python3 iam_role_manager.py --role-name $role --confirm
done

# Restore from backup using Terraform
cp backup.txt backup.tf && terraform init && terraform apply -auto-approve
```

### Exit Codes

| Code | Meaning                                       |
| ---- | --------------------------------------------- |
| 0    | Success                                       |
| 1    | Error (role not found, deletion failed, etc.) |

---

## License

MIT License - ServiceNow MCP Project
