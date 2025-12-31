# AWS IAM MCP Server & AWS Terraform MCP Server

## Testing and Troubleshooting Guide

> **Date:** December 31, 2025  
> **Repository:** `selvar2/sample-workflow`  
> **Branch:** `workflowag4`

---

## Table of Contents

1. [MCP Configuration Setup](#1-mcp-configuration-setup)
2. [Installing Dependencies](#2-installing-dependencies)
3. [AWS IAM MCP Server Installation](#3-aws-iam-mcp-server-installation)
4. [DevContainer Automation](#4-devcontainer-automation)
5. [Creating IAM Roles via MCP Servers](#5-creating-iam-roles-via-mcp-servers)
6. [Working Scripts](#6-working-scripts)
7. [Troubleshooting](#7-troubleshooting)
8. [Summary of Created Resources](#8-summary-of-created-resources)

---

## 1. MCP Configuration Setup

### 1.1 Locating the MCP JSON Configuration File

The MCP configuration file was located at:

```
/workspaces/sample-workflow/servicenow-mcp/claude_desktop_config.json
```

### 1.2 Creating Backup Before Modification

> ⚠️ **Important:** Always backup the configuration file before making changes!

```bash
# Backup created at:
claude_desktop_config.json.bak   # First backup
claude_desktop_config.json.bak2  # Second backup (before adding IAM server)
```

### 1.3 Adding AWS Terraform MCP Server

Added the following entry to the existing `mcpServers` configuration:

```json
{
  "mcpServers": {
    "awslabs.terraform-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.terraform-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### 1.4 Validating JSON Configuration

```bash
python3 -c "import json,sys; json.load(open('claude_desktop_config.json')); print('valid')"
```

**Result:** ✅ `valid`

---

## 2. Installing Dependencies

### 2.1 Terraform CLI Installation

```bash
# Add HashiCorp APT repository
sudo apt-get update -y && \
sudo apt-get install -y gnupg software-properties-common curl lsb-release && \
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list && \
sudo apt-get update -y && \
sudo apt-get install -y terraform
```

**Verification:**
```bash
terraform -version
```
**Result:** ✅ `Terraform v1.14.3`

### 2.2 Checkov Installation

```bash
sudo pip3 install --upgrade checkov
```

**Verification:**
```bash
checkov --version
```
**Result:** ✅ `checkov v3.2.497`

---

## 3. AWS IAM MCP Server Installation

### 3.1 Installation Methods

#### **Option 1: Using uv (Recommended)**

```bash
uv tool install awslabs.iam-mcp-server
```

#### **Option 2: Using pip**

```bash
pip install awslabs.iam-mcp-server
```

### 3.2 Adding to MCP Configuration

Added the following entry to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "awslabs.iam-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.iam-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

### 3.3 Verifying Installation

```bash
awslabs.iam-mcp-server --help
```

**Result:** ✅ Shows usage information

---

## 4. DevContainer Automation

### 4.1 Problem Statement

> Every time the Codespace restarts or a new Codespace is launched, dependencies need to be reinstalled manually.

### 4.2 Solution: Update DevContainer Scripts

#### **Files Modified:**

| File | Purpose |
|------|---------|
| `.devcontainer/setup.sh` | Runs on container creation |
| `.devcontainer/ensure-dependencies.sh` | Runs on every start/attach |
| `.devcontainer/verify-mcp-setup.sh` | Verifies MCP server installation |

#### **Key Changes in `setup.sh`:**

```bash
# Install MCP servers using uv tool install
MCP_SERVERS=(
    "awslabs.redshift-mcp-server"
    "awslabs.iam-mcp-server"
    "awslabs.terraform-mcp-server"
)

for server in "${MCP_SERVERS[@]}"; do
    echo "Installing $server..."
    uv tool install "$server" || echo "Warning: Failed to install $server"
done
```

#### **Key Changes in `ensure-dependencies.sh`:**

```bash
# Ensure PATH includes uv-installed tools
export PATH="$HOME/.local/bin:$PATH"

# Terraform CLI check and install
if ! command -v terraform &> /dev/null; then
    echo "Installing Terraform CLI..."
    # Installation commands...
fi

# Checkov check and install
if ! command -v checkov &> /dev/null; then
    echo "Installing Checkov..."
    pip3 install --upgrade checkov
fi
```

### 4.3 What Happens Now

When you **restart** or **launch a new Codespace**:

1. `postCreateCommand` runs `setup.sh` → installs everything from scratch
2. `postStartCommand` / `postAttachCommand` runs `ensure-dependencies.sh` → verifies and installs any missing tools

**Tools Available Automatically:**
- ✅ `awslabs.iam-mcp-server`
- ✅ `awslabs.redshift-mcp-server`
- ✅ `awslabs.terraform-mcp-server`
- ✅ `terraform` CLI
- ✅ `checkov`

---

## 5. Creating IAM Roles via MCP Servers

### 5.1 Analyzing Existing IAM Role

**Target Role ARN:**
```
arn:aws:iam::175853813947:role/example_role3
```

**Commands Used to Extract Role Details:**

```bash
# Get role details
aws iam get-role --role-name example_role3 --output json

# List attached policies
aws iam list-attached-role-policies --role-name example_role3 --output json

# List inline policies
aws iam list-role-policies --role-name example_role3 --output json

# Get role tags
aws iam list-role-tags --role-name example_role3 --output json

# Get policy document
aws iam get-policy --policy-arn arn:aws:iam::175853813947:policy/example_policy3 --output json
aws iam get-policy-version --policy-arn arn:aws:iam::175853813947:policy/example_policy3 --version-id v4 --output json
```

### 5.2 IAM Role Details Extracted

| Property | Value |
|----------|-------|
| **Role Name** | `example_role3` |
| **ARN** | `arn:aws:iam::175853813947:role/example_role3` |
| **Path** | `/` |
| **Max Session Duration** | 3600 seconds (1 hour) |
| **Trust Policy** | AWS Glue service (`glue.amazonaws.com`) |
| **Attached Policies** | `example_policy3` (custom managed policy) |
| **Inline Policies** | None |
| **Tags** | None |

### 5.3 MCP Server Communication

MCP servers communicate via **JSON-RPC over stdio**. They are designed for MCP clients (like Claude Desktop), not direct CLI usage.

#### **Discovering Available Tools:**

```bash
echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | timeout 10 awslabs.terraform-mcp-server 2>/dev/null
```

#### **AWS Terraform MCP Server Tools:**

| Tool Name | Description |
|-----------|-------------|
| `ExecuteTerraformCommand` | Run terraform commands (init, plan, apply, validate, destroy) |
| `RunCheckovScan` | Run Checkov security scans |
| `GenerateTerraformCode` | Generate Terraform configurations |

#### **AWS IAM MCP Server Tools:**

| Tool Name | Description |
|-----------|-------------|
| `list_roles` | List IAM roles |
| `get_managed_policy_document` | Get policy document |
| `analyze_role` | Analyze IAM role permissions |

### 5.4 Creating Terraform Configuration via MCP

#### **Step-by-Step Terraform Commands via MCP:**

**Step 1: Validate**
```bash
printf '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ExecuteTerraformCommand","arguments":{"command":"validate","working_directory":"/workspaces/sample-workflow/servicenow-mcp/terraform","aws_region":"us-east-1"}}}\n' | timeout 60 awslabs.terraform-mcp-server 2>&1 | tail -1
```

**Step 2: Init**
```bash
printf '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ExecuteTerraformCommand","arguments":{"command":"init","working_directory":"/workspaces/sample-workflow/servicenow-mcp/terraform","aws_region":"us-east-1"}}}\n' | timeout 120 awslabs.terraform-mcp-server 2>&1 | tail -1
```

**Step 3: Plan**
```bash
printf '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ExecuteTerraformCommand","arguments":{"command":"plan","working_directory":"/workspaces/sample-workflow/servicenow-mcp/terraform","aws_region":"us-east-1"}}}\n' | timeout 120 awslabs.terraform-mcp-server 2>&1 | tail -1
```

**Step 4: Apply**
```bash
printf '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"ExecuteTerraformCommand","arguments":{"command":"apply","working_directory":"/workspaces/sample-workflow/servicenow-mcp/terraform","aws_region":"us-east-1"}}}\n' | timeout 180 awslabs.terraform-mcp-server 2>&1 | tail -1
```

---

## 6. Working Scripts

### 6.1 Scripts Summary

| Script | Language | Status | Description |
|--------|----------|--------|-------------|
| `terraform_mcp_apply.sh` | Bash | ✅ **Working** | Shell script to run Terraform via MCP |
| `apply_via_mcp_v3.py` | Python | ✅ **Working** | Python script to run Terraform via MCP |
| `mcp_client.py` | Python | ✅ **Working** | Base MCP client library |
| `generate_tf_via_mcp.py` | Python | ✅ **Working** | Uses mcp_client.py to query IAM MCP |
| `apply_via_mcp.py` | Python | ❌ Not working | Original - parsing issues |
| `apply_via_mcp_v2.py` | Python | ❌ Not working | Improved but still had issues |
| `run_tf_mcp.sh` | Bash | ❌ Not working | Had parsing issues |

### 6.2 terraform_mcp_apply.sh

**Location:** `/workspaces/sample-workflow/servicenow-mcp/terraform/terraform_mcp_apply.sh`

**Usage:**
```bash
# Default (current directory, us-east-1)
./terraform_mcp_apply.sh

# Custom directory and region
./terraform_mcp_apply.sh /path/to/terraform us-west-2
```

**Key Features:**
- Uses `printf` with `tail -1` to capture final JSON response
- Uses Python for JSON parsing
- Runs validate → init → plan → apply sequence
- 180-second timeout for Terraform commands

### 6.3 apply_via_mcp_v3.py

**Location:** `/workspaces/sample-workflow/servicenow-mcp/terraform/apply_via_mcp_v3.py`

**Usage:**
```bash
python3 apply_via_mcp_v3.py [working_directory] [aws_region]
```

**Key Features:**
- Uses `for line in reversed(lines)` to find response with `id=1`
- Parses `structuredContent` from response for clean data access
- Same workflow as shell script

### 6.4 mcp_client.py

**Location:** `/workspaces/sample-workflow/servicenow-mcp/terraform/mcp_client.py`

**Purpose:** Base MCP client library with `call_mcp_tool()` function

```python
def call_mcp_tool(server_command: str, tool_name: str, arguments: dict) -> dict:
    """
    Call a tool on an MCP server via JSON-RPC.
    
    Args:
        server_command: Command to start the MCP server (e.g., "awslabs.iam-mcp-server")
        tool_name: Name of the tool to call
        arguments: Dictionary of arguments for the tool
        
    Returns:
        Dictionary containing the parsed response
    """
```

---

## 7. Troubleshooting

### 7.1 Common Issues and Solutions

#### **Issue 1: Python Scripts Print "Status: unknown"**

**Problem:** Initial Python scripts couldn't parse MCP response properly.

**Solution:** Use `tail -1` in shell or iterate `reversed(lines)` in Python to find response with `id=1`.

#### **Issue 2: Scripts Hang During `terraform init`**

**Problem:** Scripts waited indefinitely for complete subprocess output.

**Solution:** Use timeout and parse only the final response line.

#### **Issue 3: MCP Server Outputs Multiple Lines**

**Problem:** MCP server outputs initialization response + tool response + stderr logs.

**Root Cause:** 
```
Line 1: {"jsonrpc":"2.0","id":0,...}  # Init response
Line 2: {"jsonrpc":"2.0","id":1,...}  # Tool response (this is what we need)
```

**Solution:** Use `tail -1` to get only the final JSON response line.

#### **Issue 4: Hanging MCP Server Processes**

**Solution:**
```bash
pkill -9 -f terraform-mcp 2>/dev/null
pkill -f "awslabs.terraform-mcp-server" 2>/dev/null
```

### 7.2 Debugging MCP Communication

**List Available Tools:**
```bash
echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | timeout 10 awslabs.terraform-mcp-server 2>/dev/null
```

**Validate JSON Configuration:**
```bash
python3 -c "import json,sys; json.load(open('claude_desktop_config.json')); print('valid')"
```

---

## 8. Summary of Created Resources

### 8.1 AWS IAM Roles Created via MCP

| Role | Role ID | Policy ARN | Created Using |
|------|---------|------------|---------------|
| `example_role3_mcp_test` | `AROASR4NUIC5ZHTGSWRIK` | `arn:aws:iam::175853813947:policy/example_policy3_mcp_test` | Inline commands |
| `example_role4_mcp_test` | `AROASR4NUIC5QCD2764BR` | `arn:aws:iam::175853813947:policy/example_policy4_mcp_test` | Inline commands |
| `example_role5_mcp_test` | `AROASR4NUIC5UFZ7CCLAT` | `arn:aws:iam::175853813947:policy/example_policy5_mcp_test` | `apply_via_mcp_v3.py` |
| `example_role6_mcp_test` | `AROASR4NUIC5W7DGT3ICG` | `arn:aws:iam::175853813947:policy/example_policy6_mcp_test` | `terraform_mcp_apply.sh` |

### 8.2 Terraform Files Created

| File | Description |
|------|-------------|
| `iam_example_role3_test.tf` | IAM role 3 configuration |
| `iam_example_role4_test.tf` | IAM role 4 configuration |
| `iam_example_role5_test.tf` | IAM role 5 configuration |
| `iam_example_role6_test.tf` | IAM role 6 configuration |

### 8.3 Commits Pushed to `workflowag4`

| Commit | Message |
|--------|---------|
| `17d0eca` | Add awslabs.terraform-mcp-server to MCP config and add backup |
| `25ca1e3` | Add awslabs.iam-mcp-server to MCP config and add backup |
| `4787dd7` | Add IAM MCP server check to verify-mcp-setup.sh |
| `8f3703c` | Add tsup bundled config artifacts to .gitignore |
| `27fa2cf` | Add working MCP scripts and IAM role terraform configs |

---

## 9. Quick Reference

### 9.1 MCP Server Commands

```bash
# Install MCP servers
uv tool install awslabs.iam-mcp-server
uv tool install awslabs.terraform-mcp-server

# Run Terraform via MCP (using working scripts)
./terraform_mcp_apply.sh
python3 apply_via_mcp_v3.py
```

### 9.2 Terraform Validation Results

| Check | Result |
|-------|--------|
| `terraform fmt` | ✅ Formatted |
| `terraform validate` | ✅ Valid |
| **Checkov** | ✅ 14 passed, 0 failed |

---

## 10. Conclusion

This guide documents the complete process of:

1. **Configuring MCP servers** in `claude_desktop_config.json` with proper backups
2. **Installing dependencies** (Terraform CLI v1.14.3, Checkov v3.2.497)
3. **Setting up DevContainer automation** for consistent environments
4. **Creating IAM roles** using AWS IAM MCP Server and AWS Terraform MCP Server
5. **Building working scripts** (`terraform_mcp_apply.sh`, `apply_via_mcp_v3.py`)
6. **Troubleshooting** common MCP communication issues

**Key Insight:** MCP servers communicate via JSON-RPC over stdio. The key to successful integration is using `tail -1` to capture only the final response line and properly parsing the `structuredContent` from the response.

---

> **Author:** GitHub Copilot  
> **Last Updated:** December 31, 2025
