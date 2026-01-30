# IAM Role Manager - MCP Version (Hybrid)

> **Script:** `iam_role_manager_mcp.py`  
> **Version:** 1.0.0  
> **Author:** ServiceNow MCP Project  
> **Date:** 2026-01-30

A comprehensive Python script for managing AWS IAM roles using **MCP (Model Context Protocol) servers** combined with AWS CLI fallback. Uses `awslabs.iam-mcp-server` for reading and `awslabs.terraform-mcp-server` for restoration.

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

`iam_role_manager_mcp.py` provides the same functionality as `iam_role_manager.py` but integrates with **AWS MCP Servers** where available, demonstrating the MCP protocol for AWS operations.

### Key Features

| Feature                   | Description                                           |
| ------------------------- | ----------------------------------------------------- |
| **Hybrid Approach**       | Uses MCP where available, AWS CLI as fallback         |
| **Terraform MCP Restore** | Restores roles via `awslabs.terraform-mcp-server`     |
| **JSON-RPC Protocol**     | Communicates with MCP servers using standard JSON-RPC |
| **Same CLI Interface**    | Drop-in replacement for `iam_role_manager.py`         |

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      iam_role_manager_mcp.py                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Information Gathering                         │   │
│  ├──────────────────────┬──────────────────────────────────────────┤   │
│  │   MCP (where avail)  │        AWS CLI (fallback)                │   │
│  │   ┌────────────────┐ │   ┌────────────────────────────────┐     │   │
│  │   │list_role_      │ │   │ get-role                       │     │   │
│  │   │policies        │ │   │ list-attached-role-policies    │     │   │
│  │   │get_role_policy │ │   │ get-policy, get-policy-version │     │   │
│  │   └────────────────┘ │   └────────────────────────────────┘     │   │
│  │          │           │              │                           │   │
│  │          ▼           │              ▼                           │   │
│  │   awslabs.iam-mcp-   │         AWS IAM API                      │   │
│  │   server             │                                          │   │
│  └──────────────────────┴──────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         Deletion                                 │   │
│  │                    (AWS CLI - no MCP delete_role)                │   │
│  │   detach-role-policy → delete-role → delete-policy              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       Restoration                                │   │
│  │                 (Terraform MCP Server)                           │   │
│  │   ┌────────────────────────────────────────────────────────┐    │   │
│  │   │  awslabs.terraform-mcp-server                          │    │   │
│  │   │  init → validate → plan → apply                        │    │   │
│  │   └────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### MCP vs AWS CLI Usage Matrix

| Operation              | MCP Tool                      | Available? | Fallback |
| ---------------------- | ----------------------------- | ---------- | -------- |
| Get Role Details       | `get_role`                    | ❌ No      | AWS CLI  |
| List Roles             | `list_roles`                  | ✅ Yes     | -        |
| List Attached Policies | `list_attached_role_policies` | ❌ No      | AWS CLI  |
| List Inline Policies   | `list_role_policies`          | ✅ Yes     | -        |
| Get Inline Policy      | `get_role_policy`             | ✅ Yes     | -        |
| Get Policy Metadata    | `get_policy`                  | ❌ No      | AWS CLI  |
| Get Policy Document    | `get_managed_policy_document` | ✅ Yes     | -        |
| Delete Role            | `delete_role`                 | ❌ No      | AWS CLI  |
| Terraform Apply        | `ExecuteTerraformCommand`     | ✅ Yes     | -        |
| Terraform Destroy      | `ExecuteTerraformCommand`     | ✅ Yes     | -        |

---

## 2. Prerequisites

### Required Tools

| Tool                         | Version | Installation  | Purpose              |
| ---------------------------- | ------- | ------------- | -------------------- |
| Python                       | 3.8+    | Pre-installed | Script runtime       |
| AWS CLI                      | 2.x     | Pre-installed | Fallback operations  |
| awslabs.iam-mcp-server       | 1.25.0+ | npm install   | IAM read operations  |
| awslabs.terraform-mcp-server | 1.25.0+ | npm install   | Terraform operations |
| Terraform                    | 1.0+    | Pre-installed | Infrastructure apply |

### Installing MCP Servers

```bash
# Install AWS MCP servers globally
npm install -g @anthropic-ai/awslabs.iam-mcp-server
npm install -g @anthropic-ai/awslabs.terraform-mcp-server

# Verify installation
which awslabs.iam-mcp-server
which awslabs.terraform-mcp-server

# Check versions
awslabs.iam-mcp-server --version 2>/dev/null || echo "MCP servers use JSON-RPC"
```

### AWS Credentials

```bash
# Verify AWS credentials
aws sts get-caller-identity --no-cli-pager

# Expected output:
{
    "UserId": "AROASR4NUIC5...",
    "Account": "175853813947",
    "Arn": "arn:aws:sts::175853813947:assumed-role/..."
}
```

### MCP Server Verification

```bash
# The script automatically checks MCP server availability
python3 iam_role_manager_mcp.py --role-name test --backup-only

# Look for:
# 🔍 Checking MCP server availability...
#    ✅ All MCP servers available
```

---

## 3. CLI Reference

### Synopsis

```bash
python3 iam_role_manager_mcp.py (--role-name ROLE_NAME | --restore BACKUP_FILE)
                                [--backup-dir BACKUP_DIR]
                                [--backup-only]
                                [--confirm]
                                [--dry-run]
```

### Arguments

| Argument                | Required | Description                               |
| ----------------------- | -------- | ----------------------------------------- |
| `--role-name ROLE_NAME` | Yes\*    | Name of the IAM role to backup/delete     |
| `--restore BACKUP_FILE` | Yes\*    | Path to backup file for MCP-based restore |

\*One of `--role-name` or `--restore` is required (mutually exclusive)

### Options

| Option             | Default                     | Description                            |
| ------------------ | --------------------------- | -------------------------------------- |
| `--backup-dir DIR` | `/workspaces/.../terraform` | Directory to save backup files         |
| `--backup-only`    | False                       | Only create backup, do not delete      |
| `--confirm`        | False                       | Skip interactive confirmation          |
| `--dry-run`        | False                       | Show what would happen without changes |

### Key Difference from iam_role_manager.py

| Feature        | iam_role_manager.py       | iam_role_manager_mcp.py     |
| -------------- | ------------------------- | --------------------------- |
| Restore Method | Manual Terraform commands | Automated via Terraform MCP |
| IAM Reading    | 100% AWS CLI              | Hybrid (MCP + CLI)          |
| MCP Dependency | None                      | Requires MCP servers        |

---

## 4. Input/Output Documentation

### Input Parameters

Same as `iam_role_manager.py` - see that documentation for details.

### Output Files

#### Backup File Format

**Filename Pattern:** `iam_{role_name}.txt`

**Content:** Valid Terraform HCL (same format as non-MCP version)

**Additional Header Comments:**

```hcl
#############################################################################
# Terraform Configuration for IAM Role: example_role4_mcp_test
#
# BACKUP FILE - Created via MCP Servers before deletion
# ...
#
# MCP Servers Used:
#   - awslabs.iam-mcp-server (for role information)
#   - awslabs.terraform-mcp-server (for restore operations)
#
# Backup Generated: 2026-01-30 11:19:42
#############################################################################
```

---

## 5. Terminal Output Examples

### Backup and Delete with MCP

```bash
$ python3 iam_role_manager_mcp.py --role-name example_role4_mcp_test --confirm
```

**Output:**

```
======================================================================
🔧 IAM Role Manager (MCP Version)
   Using AWS IAM & Terraform MCP Servers
======================================================================

🔍 Checking MCP server availability...
   ✅ All MCP servers available

Target Role: example_role4_mcp_test
Backup Directory: /workspaces/sample-workflow/servicenow-mcp/terraform
Mode: BACKUP & DELETE

📋 Gathering information for role: example_role4_mcp_test
   Using: IAM MCP Server + AWS CLI (hybrid)
------------------------------------------------------------
   🔍 Fetching role details (AWS CLI)...
   ✅ Role ARN: arn:aws:iam::175853813947:role/example_role4_mcp_test
   ✅ Role ID: AROASR4NUIC5UNZ6TZMX7
   🔍 Fetching attached policies (AWS CLI)...
   ✅ Attached policies: 1
   🔍 Fetching inline policies (MCP)...
   ✅ Inline policies: 0
   🔍 Fetching policy document (AWS CLI): example_policy4_mcp_test...
   ✅ Policy example_policy4_mcp_test: 1 version(s)
------------------------------------------------------------
✅ All information gathered successfully via MCP

📝 Creating backup...
------------------------------------------------------------
   ✅ Backup created: /workspaces/.../iam_example_role4_mcp_test.txt
   ✅ Backup size: 3843 bytes

✅ Backup verified. Proceeding with deletion via MCP...

🗑️  Deleting IAM Role: example_role4_mcp_test
   Note: Using AWS CLI (IAM MCP doesn't have delete_role)
------------------------------------------------------------
   📎 Detaching policy: example_policy4_mcp_test
   ✅ Detached: example_policy4_mcp_test
   🗑️ Deleting role: example_role4_mcp_test
   ✅ Role deleted: example_role4_mcp_test
   🗑️ Deleting policy: example_policy4_mcp_test
   ✅ Policy deleted: example_policy4_mcp_test
------------------------------------------------------------

🔍 Verifying deletion via MCP...
   ✅ Role confirmed deleted: example_role4_mcp_test

======================================================================
✅ DELETION COMPLETED SUCCESSFULLY VIA MCP
======================================================================

Backup preserved at: /workspaces/.../iam_example_role4_mcp_test.txt
To restore via MCP, run:
  python3 iam_role_manager_mcp.py --restore /workspaces/.../iam_example_role4_mcp_test.txt
```

### Restore via Terraform MCP Server

```bash
$ python3 iam_role_manager_mcp.py --restore /workspaces/.../iam_example_role4_mcp_test.txt
```

**Output:**

```
======================================================================
🔧 IAM Role Manager (MCP Version)
   Using AWS IAM & Terraform MCP Servers
======================================================================

🔍 Checking MCP server availability...
   ✅ All MCP servers available

======================================================================
🔄 RESTORING IAM ROLE VIA MCP
======================================================================

Backup file: /workspaces/.../iam_example_role4_mcp_test.txt
Using MCP Server: awslabs.terraform-mcp-server

   📝 Copied backup to: /tmp/iam_restore_xyz123/main.tf

   🔧 Running Terraform workflow via MCP...
   🔧 Initializing Terraform...
   🔧 Validating configuration...
   🔧 Planning changes...
   🔧 Executing apply...

✅ Terraform apply completed successfully

   🧹 Cleaned up temporary directory
```

### Dry Run Mode

```bash
$ python3 iam_role_manager_mcp.py --role-name example_role4_mcp_test --dry-run
```

**Output:**

```
======================================================================
🔧 IAM Role Manager (MCP Version)
   Using AWS IAM & Terraform MCP Servers
======================================================================

🔍 Checking MCP server availability...
   ✅ All MCP servers available

Target Role: example_role4_mcp_test
Mode: DRY RUN

📋 Gathering information for role: example_role4_mcp_test
   Using: IAM MCP Server + AWS CLI (hybrid)
...
✅ All information gathered successfully via MCP

📝 Creating backup...
   ✅ Backup created: /workspaces/.../iam_example_role4_mcp_test.txt

🗑️  Deleting IAM Role: example_role4_mcp_test
------------------------------------------------------------
   🔍 [DRY RUN] Would delete:
   - Role: example_role4_mcp_test
   - Policy: example_policy4_mcp_test
------------------------------------------------------------

======================================================================
🔍 DRY RUN COMPLETED - No changes were made
======================================================================
```

---

## 6. Testing Guide

### Step 1: Verify MCP Server Installation

```bash
# Check if MCP servers are on PATH
which awslabs.iam-mcp-server
which awslabs.terraform-mcp-server

# Test MCP server communication
python3 -c "
import json
import subprocess

msg = json.dumps({
    'jsonrpc': '2.0', 'id': 0, 'method': 'initialize',
    'params': {'protocolVersion': '2024-11-05', 'capabilities': {},
               'clientInfo': {'name': 'test', 'version': '1.0'}}
})

result = subprocess.run(
    ['awslabs.iam-mcp-server'],
    input=msg + '\n',
    capture_output=True, text=True, timeout=10
)
print('IAM MCP Server:', 'OK' if 'serverInfo' in result.stdout else 'FAILED')
"
```

### Step 2: List Available MCP Tools

```bash
python3 -c "
import json, subprocess

init = json.dumps({'jsonrpc': '2.0', 'id': 0, 'method': 'initialize',
    'params': {'protocolVersion': '2024-11-05', 'capabilities': {},
               'clientInfo': {'name': 'test', 'version': '1.0'}}})
tools = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list', 'params': {}})

result = subprocess.run(['awslabs.iam-mcp-server'],
    input=f'{init}\n{tools}\n', capture_output=True, text=True, timeout=30)

for line in result.stdout.split('\n'):
    try:
        parsed = json.loads(line)
        if parsed.get('id') == 1:
            for tool in parsed['result'].get('tools', []):
                print(f\"  - {tool['name']}\")
    except: pass
"
```

**Expected Output:**

```
  - list_users
  - get_user
  - list_roles
  - create_role
  - list_role_policies
  - get_role_policy
  - delete_role_policy
  - put_role_policy
  ... (29 tools total)
```

### Step 3: Test Full Cycle

```bash
cd /workspaces/sample-workflow/servicenow-mcp/terraform

# 1. Backup only
python3 iam_role_manager_mcp.py --role-name example_role4_mcp_test --backup-only

# 2. Verify backup
cat iam_example_role4_mcp_test.txt | head -30

# 3. Delete with confirmation
python3 iam_role_manager_mcp.py --role-name example_role4_mcp_test --confirm

# 4. Verify deletion
aws iam get-role --role-name example_role4_mcp_test 2>&1 | grep NoSuchEntity

# 5. Restore via MCP
python3 iam_role_manager_mcp.py --restore iam_example_role4_mcp_test.txt

# 6. Verify restoration
aws iam get-role --role-name example_role4_mcp_test --no-cli-pager
aws iam list-attached-role-policies --role-name example_role4_mcp_test --no-cli-pager
```

### Step 4: Compare with Non-MCP Version

```bash
# Both should produce identical backup files
python3 iam_role_manager.py --role-name test_role --backup-only
mv iam_test_role.txt iam_test_role_cli.txt

python3 iam_role_manager_mcp.py --role-name test_role --backup-only
mv iam_test_role.txt iam_test_role_mcp.txt

# Compare (header timestamps will differ)
diff iam_test_role_cli.txt iam_test_role_mcp.txt
```

---

## 7. Alternative Approaches

### Comparison: MCP vs Non-MCP

| Aspect              | iam_role_manager.py | iam_role_manager_mcp.py        |
| ------------------- | ------------------- | ------------------------------ |
| **Dependencies**    | AWS CLI only        | AWS CLI + MCP servers          |
| **Restore Method**  | Manual Terraform    | Automated via MCP              |
| **Complexity**      | Simpler             | More complex                   |
| **MCP Integration** | None                | Demonstrates MCP protocol      |
| **Portability**     | Works anywhere      | Requires MCP servers           |
| **Speed**           | Fast                | Slightly slower (MCP overhead) |

### When to Use MCP Version

```
Use iam_role_manager_mcp.py when:
├── You're building an MCP-integrated workflow
├── You want automated Terraform restore (no manual commands)
├── You're demonstrating MCP capabilities
└── You have MCP servers already installed

Use iam_role_manager.py when:
├── You need maximum portability
├── You want fewer dependencies
├── MCP servers aren't available
└── You prefer manual Terraform control for restore
```

### Pure MCP Alternative (Future)

When IAM MCP server adds more tools, a pure MCP version could:

```python
# Hypothetical future - if IAM MCP had delete_role
def mcp_delete_role(role_name):
    return call_mcp_tool(IAM_MCP_SERVER, "delete_role", {"role_name": role_name})
```

### Terraform-Only Alternative

```bash
# Import existing role into Terraform state
terraform import aws_iam_role.example_role example_role_name

# Then destroy via Terraform
terraform destroy -target=aws_iam_role.example_role
```

---

## 8. Technical Implementation

### MCP JSON-RPC Communication

The script communicates with MCP servers using JSON-RPC 2.0 over stdio:

```python
def call_mcp_tool(server_cmd: str, tool_name: str, arguments: dict, timeout: int = 60) -> dict:
    """Call an MCP tool using JSON-RPC protocol."""

    # Step 1: Initialize session
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

    # Step 2: Call the tool
    tool_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    })

    # Step 3: Send to MCP server via stdin
    input_data = f"{init_msg}\n{tool_msg}\n"

    result = subprocess.run(
        [server_cmd],
        input=input_data,
        capture_output=True,
        text=True,
        timeout=timeout
    )

    # Step 4: Parse response (find id=1)
    for line in result.stdout.strip().split('\n'):
        parsed = json.loads(line)
        if parsed.get("id") == 1:
            return parsed

    return {"error": "NoValidResponse"}
```

### MCP Response Parsing

```python
def extract_mcp_content(response: dict) -> Tuple[bool, Any]:
    """Extract content from MCP response."""

    if "error" in response:
        return False, response.get("message", response["error"])

    result = response.get("result", {})

    # Try structuredContent first (cleaner format)
    if "structuredContent" in result:
        return True, result["structuredContent"]

    # Fall back to content array
    if "content" in result:
        for item in result["content"]:
            if item.get("type") == "text":
                return True, json.loads(item["text"])

    return True, result
```

### Hybrid Approach Explanation

```python
# Operations using MCP (where available)
def mcp_list_role_policies(role_name: str) -> List[str]:
    response = call_mcp_tool(IAM_MCP_SERVER, "list_role_policies", {"role_name": role_name})
    # ... parse response

# Operations using AWS CLI (MCP not available)
def mcp_get_role(role_name: str) -> Dict[str, Any]:
    # IAM MCP server doesn't have get_role, use AWS CLI
    result = run_aws_command(["iam", "get-role", "--role-name", role_name])
    return result
```

### Terraform MCP Workflow

```python
def run_terraform_workflow(working_dir: str, action: str = "apply") -> Tuple[bool, str]:
    """Run complete Terraform workflow via MCP."""

    # Order matters: init must come before validate
    steps = [
        ("init", "Initializing Terraform"),
        ("validate", "Validating configuration"),
        ("plan", "Planning changes"),
        (action, f"Executing {action}"),  # "apply" or "destroy"
    ]

    for command, description in steps:
        result = mcp_terraform_command(command, working_dir)

        if result["status"] == "error":
            return False, f"{description} failed"

    return True, f"Terraform {action} completed successfully"
```

### Available IAM MCP Tools (v1.25.0)

```
✅ Available:
- list_users, get_user, create_user, delete_user
- list_roles, create_role
- list_policies, get_managed_policy_document
- list_role_policies, get_role_policy, put_role_policy, delete_role_policy
- list_groups, get_group, create_group, delete_group
- attach/detach policies (user, group)
- create/delete access keys
- simulate_principal_policy

❌ NOT Available (requires AWS CLI fallback):
- get_role (only list_roles exists)
- delete_role (only create_role exists)
- list_attached_role_policies
- get_policy, get_policy_version
- list_policy_versions
- detach_role_policy, attach_role_policy
```

---

## 9. Troubleshooting

### MCP Server Issues

#### Error: MCP Server Not Found

```
⚠️ Missing MCP servers: awslabs.iam-mcp-server, awslabs.terraform-mcp-server
```

**Solution:**

```bash
# Install MCP servers
npm install -g @anthropic-ai/awslabs.iam-mcp-server
npm install -g @anthropic-ai/awslabs.terraform-mcp-server

# Verify PATH
echo $PATH
which awslabs.iam-mcp-server
```

#### Error: Unknown Tool

```
{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"Unknown tool: get_role"}],"isError":true}}
```

**Solution:** This is expected! The script automatically falls back to AWS CLI for unsupported operations. Check that `run_aws_command` is being called.

#### Error: Timeout on MCP Call

```
{"error": "Timeout", "message": "Command timed out after 60 seconds"}
```

**Solution:**

```bash
# Test MCP server directly
echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{}}' | awslabs.iam-mcp-server

# Check for network/credential issues
aws sts get-caller-identity
```

### Terraform MCP Issues

#### Error: Terraform Validate Failed

```
❌ Validating configuration failed
```

**Cause:** Validate was called before init.

**Solution:** The script now runs init before validate (fixed in latest version).

#### Error: Terraform Apply Failed

```
❌ Executing apply failed: Resource already exists
```

**Cause:** The role already exists in AWS.

**Solution:**

```bash
# Check if role exists
aws iam get-role --role-name ROLE_NAME

# Delete first, then restore
python3 iam_role_manager_mcp.py --role-name ROLE_NAME --confirm
python3 iam_role_manager_mcp.py --restore backup.txt
```

### Common AWS Errors

See `IAM_ROLE_MANAGER_README.md` Section 9 for AWS-specific errors.

---

## 10. Quick Reference

### Command Cheat Sheet

| Task                 | Command                                                       |
| -------------------- | ------------------------------------------------------------- |
| Backup only          | `python3 iam_role_manager_mcp.py --role-name X --backup-only` |
| Dry run              | `python3 iam_role_manager_mcp.py --role-name X --dry-run`     |
| Delete (interactive) | `python3 iam_role_manager_mcp.py --role-name X`               |
| Delete (automated)   | `python3 iam_role_manager_mcp.py --role-name X --confirm`     |
| Restore via MCP      | `python3 iam_role_manager_mcp.py --restore backup.txt`        |

### MCP Tools Quick Reference

| Operation            | MCP Tool                  | Server               |
| -------------------- | ------------------------- | -------------------- |
| List inline policies | `list_role_policies`      | iam-mcp-server       |
| Get inline policy    | `get_role_policy`         | iam-mcp-server       |
| Terraform init       | `ExecuteTerraformCommand` | terraform-mcp-server |
| Terraform apply      | `ExecuteTerraformCommand` | terraform-mcp-server |
| Terraform destroy    | `ExecuteTerraformCommand` | terraform-mcp-server |

### One-Liner Examples

```bash
# Full cycle: backup → delete → restore
python3 iam_role_manager_mcp.py --role-name my_role --confirm && \
python3 iam_role_manager_mcp.py --restore iam_my_role.txt

# Test MCP server availability
python3 -c "import subprocess; print(subprocess.run(['which', 'awslabs.iam-mcp-server'], capture_output=True).returncode == 0)"

# Compare MCP vs CLI output
diff <(python3 iam_role_manager.py --role-name X --dry-run 2>&1) \
     <(python3 iam_role_manager_mcp.py --role-name X --dry-run 2>&1)
```

### Exit Codes

| Code | Meaning                                              |
| ---- | ---------------------------------------------------- |
| 0    | Success                                              |
| 1    | Error (role not found, MCP failure, deletion failed) |

### Environment Variables

| Variable      | Effect                                         |
| ------------- | ---------------------------------------------- |
| `AWS_REGION`  | AWS region for operations (default: us-east-1) |
| `AWS_PROFILE` | AWS credentials profile to use                 |
| `PATH`        | Must include MCP server binaries               |

---

## Appendix: MCP Protocol Reference

### JSON-RPC Message Format

```json
// Initialize Session
{"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "client", "version": "1.0"}
}}

// Call Tool
{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
    "name": "list_role_policies",
    "arguments": {"role_name": "example_role"}
}}

// List Available Tools
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
```

### Response Format

```json
// Success
{"jsonrpc": "2.0", "id": 1, "result": {
    "content": [{"type": "text", "text": "{\"PolicyNames\": []}"}],
    "structuredContent": {"PolicyNames": []}
}}

// Error
{"jsonrpc": "2.0", "id": 1, "result": {
    "content": [{"type": "text", "text": "Unknown tool: get_role"}],
    "isError": true
}}
```

---

## License

MIT License - ServiceNow MCP Project
