# Testing AWS IAM MCP Server and AWS CLI Commands

**Date:** January 2, 2026

---

## Task Request

**User:** Act as an AWS IAM automation engineer.

### Task

Using only the AWS IAM MCP server and AWS CLI, inspect an existing `example_role5_mcp_test` IAM role, retrieve all attached permissions and policies, and add the `s3:PutObject` permission to the role.

### Constraints (Strict)

- ❌ Do not use the AWS Terraform MCP server (even though it is configured).
- ❌ Do not create, delete, or recreate the IAM role.
- ❌ Do not modify or generate any Terraform files.
- ❌ Do not use the AWS Management Console (UI).
- ❌ Do not remove or alter any existing permissions.

### Implementation Requirements

Determine whether the permission is defined in:
- an inline policy, or
- an attached managed policy

Update the permission in place using AWS IAM APIs via the AWS CLI.

**Preserve:**
- role name
- role ARN
- trust policy
- all existing policy statements

### Permission Details

Add `s3:PutObject`

### Output Expectations

- Show the exact AWS CLI commands used
- Clearly indicate:
  - which policy was updated
  - whether it was inline or managed
  - how the new permission was added
- Confirm that the role was modified, not recreated

### Validation

- Verify the final permissions by re-reading the role's policy documents
- Confirm `s3:PutObject` is present without impacting existing access

---

## Execution

### Step 1: Inspect the IAM Role

```bash
aws iam get-role --role-name example_role5_mcp_test --no-cli-pager --output json
```

**Output:**
```json
{
    "Role": {
        "Path": "/",
        "RoleName": "example_role5_mcp_test",
        "RoleId": "AROASR4NUIC5UFZ7CCLAT",
        "Arn": "arn:aws:iam::175853813947:role/example_role5_mcp_test",
        "CreateDate": "2025-12-31T11:30:35+00:00",
        "AssumeRolePolicyDocument": {
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
        },
        "Description": "IAM role for AWS Glue - Generated via AWS IAM MCP Server",
        "MaxSessionDuration": 3600,
        "Tags": [
            {
                "Key": "GeneratedAt",
                "Value": "2025-12-31"
            },
            {
                "Key": "GeneratedBy",
                "Value": "AWS-IAM-MCP-Server"
            }
        ],
        "RoleLastUsed": {}
    }
}
```

### Step 2: List Attached Managed Policies

```bash
aws iam list-attached-role-policies --role-name example_role5_mcp_test --no-cli-pager --output json
```

**Output:**
```json
{
    "AttachedPolicies": [
        {
            "PolicyName": "example_policy5_mcp_test",
            "PolicyArn": "arn:aws:iam::175853813947:policy/example_policy5_mcp_test"
        }
    ]
}
```

### Step 3: Check for Inline Policies

```bash
aws iam list-role-policies --role-name example_role5_mcp_test --no-cli-pager --output json
```

**Output:**
```json
{
    "PolicyNames": []
}
```

> ✅ No inline policies found. Permission is in an **attached managed policy**.

### Step 4: Get Policy Metadata

```bash
aws iam get-policy --policy-arn arn:aws:iam::175853813947:policy/example_policy5_mcp_test --no-cli-pager --output json
```

**Output:**
```json
{
    "Policy": {
        "PolicyName": "example_policy5_mcp_test",
        "PolicyId": "ANPASR4NUIC523FXKERK7",
        "Arn": "arn:aws:iam::175853813947:policy/example_policy5_mcp_test",
        "Path": "/",
        "DefaultVersionId": "v1",
        "AttachmentCount": 1,
        "PermissionsBoundaryUsageCount": 0,
        "IsAttachable": true,
        "Description": "S3 access policy - Generated via AWS IAM MCP Server",
        "CreateDate": "2025-12-31T11:30:35+00:00",
        "UpdateDate": "2025-12-31T11:30:35+00:00",
        "Tags": [
            {
                "Key": "GeneratedBy",
                "Value": "AWS-IAM-MCP-Server"
            },
            {
                "Key": "GeneratedAt",
                "Value": "2025-12-31"
            }
        ]
    }
}
```

### Step 5: Get Policy Document (Version v1)

```bash
aws iam get-policy-version --policy-arn arn:aws:iam::175853813947:policy/example_policy5_mcp_test --version-id v1 --no-cli-pager --output json
```

**Output:**
```json
{
    "PolicyVersion": {
        "Document": {
            "Statement": [
                {
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject"
                    ],
                    "Effect": "Allow",
                    "Resource": [
                        "arn:aws:s3:::whizlabs12/sample_data.csv*"
                    ]
                }
            ],
            "Version": "2012-10-17"
        },
        "VersionId": "v1",
        "IsDefaultVersion": true,
        "CreateDate": "2025-12-31T11:30:35+00:00"
    }
}
```

---

## Summary of Findings

**Role:** `example_role5_mcp_test`
- **ARN:** `arn:aws:iam::175853813947:role/example_role5_mcp_test`
- **Role ID:** `AROASR4NUIC5UFZ7CCLAT`
- **Trust Policy:** Allows `glue.amazonaws.com` to assume the role

**Policy Type:** **Managed Policy** (not inline)
- **Policy Name:** `example_policy5_mcp_test`
- **Policy ARN:** `arn:aws:iam::175853813947:policy/example_policy5_mcp_test`

**Current Permissions:**
```json
{
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Effect": "Allow",
  "Resource": ["arn:aws:s3:::whizlabs12/sample_data.csv*"]
}
```

---

## ✅ Result: `s3:PutObject` Permission Already Exists

The `s3:PutObject` permission is **already present** in the managed policy `example_policy5_mcp_test` attached to the role. The current policy document includes both:
- `s3:GetObject`
- `s3:PutObject`

**No modification is needed.** The role already has the requested permission.

---

## AWS CLI Commands Used

| Step | Command |
|------|---------|
| 1. Inspect role | `aws iam get-role --role-name example_role5_mcp_test` |
| 2. List attached managed policies | `aws iam list-attached-role-policies --role-name example_role5_mcp_test` |
| 3. Check for inline policies | `aws iam list-role-policies --role-name example_role5_mcp_test` |
| 4. Get policy metadata | `aws iam get-policy --policy-arn arn:aws:iam::175853813947:policy/example_policy5_mcp_test` |
| 5. Get policy document | `aws iam get-policy-version --policy-arn arn:aws:iam::175853813947:policy/example_policy5_mcp_test --version-id v1` |

---

## Validation Confirmed

- ✅ Role was **not recreated** (same Role ID: `AROASR4NUIC5UFZ7CCLAT`, created `2025-12-31`)
- ✅ Trust policy preserved (glue.amazonaws.com)
- ✅ `s3:PutObject` is present in the managed policy
- ✅ `s3:GetObject` permission also preserved
- ✅ No inline policies on this role - permission is in an **attached managed policy**

---

## Follow-up: Add `s3:ListBucket` Permission

**User:** Add ListObject to the same block

### Step 6: Create New Policy Version with `s3:ListBucket`

```bash
aws iam create-policy-version \
  --policy-arn arn:aws:iam::175853813947:policy/example_policy5_mcp_test \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::whizlabs12/sample_data.csv*"
        ]
      }
    ]
  }' \
  --set-as-default \
  --no-cli-pager --output json
```

**Output:**
```json
{
    "PolicyVersion": {
        "VersionId": "v2",
        "IsDefaultVersion": true,
        "CreateDate": "2026-01-02T07:59:32+00:00"
    }
}
```

### Step 7: Verify Updated Policy Document

```bash
aws iam get-policy-version --policy-arn arn:aws:iam::175853813947:policy/example_policy5_mcp_test --version-id v2 --no-cli-pager --output json
```

**Output:**
```json
{
    "PolicyVersion": {
        "Document": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "arn:aws:s3:::whizlabs12/sample_data.csv*"
                    ]
                }
            ]
        },
        "VersionId": "v2",
        "IsDefaultVersion": true,
        "CreateDate": "2026-01-02T07:59:32+00:00"
    }
}
```

---

## ✅ Final Result

**Policy Updated:** `example_policy5_mcp_test` (managed policy)

| Before (v1) | After (v2) |
|-------------|------------|
| `s3:GetObject` | `s3:GetObject` |
| `s3:PutObject` | `s3:PutObject` |
| | `s3:ListBucket` ← **Added** |

### Validation

- ✅ Role not modified (only policy updated)
- ✅ New policy version `v2` set as default
- ✅ All existing permissions preserved
- ✅ Role ID unchanged: `AROASR4NUIC5UFZ7CCLAT`
- ✅ Trust policy preserved: `glue.amazonaws.com`
