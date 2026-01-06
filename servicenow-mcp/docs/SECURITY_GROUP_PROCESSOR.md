# Security Group Incident Processor v2.1.0

## Overview

The `process_security_group_incident.py` script automates AWS Security Group management through ServiceNow incident tickets. It processes incidents to add or remove inbound/outbound rules from security groups, with full audit trails and Terraform-style backups.

## Features

| Feature | Description |
|---------|-------------|
| **Multi-CIDR Support** | Process multiple CIDRs in a single incident (comma, space, or newline separated) |
| **Dynamic Parsing** | Automatically detects security group, region, CIDRs, port, and protocol from ticket description |
| **Duplicate Detection** | Skips CIDRs that already exist as rules (for add operations) |
| **Terraform Backup** | Generates markdown files with HCL syntax showing before/after states |
| **Cluster Verification** | Validates security group association with Redshift/RDS clusters |
| **Detailed Work Notes** | Updates ServiceNow tickets with comprehensive action logs |

---

## Installation & Requirements

### Prerequisites
- Python 3.10+
- AWS CLI configured with appropriate permissions
- ServiceNow MCP server credentials

### Environment Variables
```bash
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password
SERVICENOW_AUTH_TYPE=basic
```

### Dependencies
```bash
cd /workspaces/sample-workflow/servicenow-mcp
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

### Basic Command
```bash
python process_security_group_incident.py <incident_number>
```

### Example
```bash
python process_security_group_incident.py INC0010117
```

---

## Supported Operations

| Operation | Trigger Phrase | Description |
|-----------|----------------|-------------|
| Add Inbound Rule | "Add an inbound rule" | Adds inbound rule(s) to security group |
| Add Outbound Rule | "Add an outbound rule" | Adds outbound rule(s) to security group |
| Remove Inbound Rule | "Remove an inbound rule" | Removes inbound rule(s) from security group |
| Remove Outbound Rule | "Remove an outbound rule" | Removes outbound rule(s) from security group |

---

## Incident Description Format

### Required Fields
| Field | Example | Description |
|-------|---------|-------------|
| security group id | `sg-3b49e714` | AWS Security Group ID |
| region | `us-east-1` | AWS Region |
| cidr range | `10.0.0.0/8` | CIDR block(s) to add/remove |
| port | `5439` | Port number |

### Optional Fields
| Field | Example | Description |
|-------|---------|-------------|
| type | `redshift` | Service type (sets default port if not specified) |
| protocol | `tcp` | Protocol (default: tcp) |
| description | `Custom description` | Rule description (default: MCP Server Automation) |
| vpc id | `vpc-28595d52` | VPC ID for reference |

### Sample Incident Description
```
Add an inbound rule:
security group id: sg-3b49e714
region: us-east-1
cidr range to be added: 10.0.0.0/8, 11.0.0.0/8, 12.0.0.0/8
port: 5439
type: redshift
```

---

## Multi-CIDR Support

The processor supports multiple CIDRs in various formats:

### Format 1: Comma-Separated
```
cidr range to be added: 17.0.0.0/8, 18.0.0.0/8, 19.0.0.0/8
```

### Format 2: Space-Separated
```
cidr range to be added: 17.0.0.0/8 18.0.0.0/8 19.0.0.0/8
```

### Format 3: Newline-Separated
```
cidr range to be added:
17.0.0.0/8
18.0.0.0/8
19.0.0.0/8
```

### Format 4: Mixed
```
cidr range to be added:
17.0.0.0/8
18.0.0.0/8 19.0.0.0/8
20.0.0.0/8, 21.0.0.0/8
```

---

## Processing Steps

The processor follows a 9-step workflow:

| Step | Description |
|------|-------------|
| 1 | Read incident details from ServiceNow |
| 2 | Parse security group operation details |
| 3 | Verify security group exists in AWS |
| 4 | Verify cluster association (if specified) |
| 5 | Capture before state (existing rules) |
| 6 | Process each CIDR (with duplicate check for add operations) |
| 7 | Capture after state |
| 8 | Generate Terraform backup |
| 9 | Update incident with work notes |

---

## Output Examples

### Console Output (Multi-CIDR Add)
```
Processing incident INC0010117...
======================================================================

[Step 1] Reading incident details...
✓ Incident retrieved: INC0010117
  Short Description: Add multiple CIDRs test
  State: New

[Step 2] Parsing security group operation details...
✓ Parsed operation: add_inbound_rule
  Security Group: sg-3b49e714
  Region: us-east-1
  CIDRs detected: 3
    1. 19.0.0.0/8
    2. 20.0.0.0/8
    3. 21.0.0.0/8
  Port: 5439

[Step 3] Verifying security group...
✓ Security group verified: default

[Step 4] Skipping cluster verification (not specified)

[Step 5] Capturing before state...
✓ Captured 10 existing rules

[Step 6] Processing 3 CIDR(s)...

  [1/3] Processing CIDR: 19.0.0.0/8
      ✓ Inbound rule added
        Rule ID: sgr-0f35636ee05280d30

  [2/3] Processing CIDR: 20.0.0.0/8
      ✓ Inbound rule added
        Rule ID: sgr-056fd68c41b401551

  [3/3] Processing CIDR: 21.0.0.0/8
      ✓ Inbound rule added
        Rule ID: sgr-05f653a89a9be3e9e

[Step 7] Capturing after state...
✓ Captured 13 rules after operation

[Step 8] Generating Terraform backup...
✓ Backup saved: backups/sg-sg-3b49e714_INC0010117_20260106_150828.md

[Step 9] Updating incident...
✓ Incident updated: INC0010117

======================================================================
SUMMARY
======================================================================
Incident: INC0010117
Operation: Add Inbound Rule
CIDRs Processed: 3 (Success: 3, Skipped: 0, Failed: 0)
Security Group: sg-3b49e714
Backup: sg-sg-3b49e714_INC0010117_20260106_150828.md
======================================================================
```

### ServiceNow Work Notes
```
═══════════════════════════════════════════
Actions Performed by MCP Server Automation
═══════════════════════════════════════════

Total CIDRs Processed: 4
  ✓ Success: 2
  ⊘ Skipped (already exists): 2
  ✗ Failed: 0

✓ 25.0.0.0/8:5439 - Inbound rule ADDED
    Rule ID: sgr-055030f87ca1d8e35
✓ 26.0.0.0/8:5439 - Inbound rule ADDED
    Rule ID: sgr-07ee311fd2d5d264a
⊘ 10.0.0.0/8:5439 - Already exists
    Existing Rule ID: sgr-0d80eb56f9cf1bc21
⊘ 11.0.0.0/8:5439 - Already exists
    Existing Rule ID: sgr-081d4d5abe0bbae66

Security Group: sg-3b49e714 (default)
Region: us-east-1
Protocol: tcp
Description: MCP Server Automation
Timestamp: 2026-01-06 15:15:46 UTC
MCP Server Automation
```

---

## Backup Files

Backups are stored in the `backups/` directory with the naming convention:
```
sg-{security_group_id}_{incident_number}_{timestamp}.md
```

### Example Backup Content
The backup includes:
- Incident information
- Security group details
- Change summary
- Before state (Terraform HCL format)
- After state (Terraform HCL format)
- Rollback instructions

---

## Testing Scenarios

### Test 1: Add Single CIDR
**Incident:** INC0010107  
**Description:** Add inbound rule 12.0.0.0/8  
**Result:** ✅ Success - Rule added

### Test 2: Duplicate Detection (Add)
**Incident:** INC0010108  
**Description:** Add same CIDR 12.0.0.0/8  
**Result:** ✅ Skipped - Rule already exists

### Test 3: Remove Single CIDR
**Incident:** INC0010110  
**Description:** Remove inbound rule 12.0.0.0/8  
**Result:** ✅ Success - Rule removed

### Test 4: Add Single CIDR (with cluster)
**Incident:** INC0010111  
**Description:** Add inbound rule 13.0.0.0/8 for redshift-cluster-1  
**Result:** ✅ Success - Cluster association verified, rule added

### Test 5: Updated Work Notes Format
**Incident:** INC0010112  
**Description:** Add inbound rule 14.0.0.0/8  
**Result:** ✅ New work notes format with "MCP Server Automation" branding

### Test 6: No Description Field (Default)
**Incident:** INC0010115  
**Description:** Add inbound rule 16.0.0.0/8 (no description in ticket)  
**Result:** ✅ Default description "MCP Server Automation" applied

### Test 7: Add Multiple CIDRs (Comma-Separated)
**Incident:** INC0010117  
**Description:** Add 19.0.0.0/8, 20.0.0.0/8, 21.0.0.0/8  
**Result:** ✅ All 3 CIDRs added successfully

### Test 8: Add Multiple CIDRs (Mixed Format with Duplicate)
**Incident:** INC0010118  
**Description:** Add 22.0.0.0/8, 23.0.0.0/8, 24.0.0.0/8, 19.0.0.0/8 (duplicate)  
**Result:** ✅ 3 added, 1 skipped (duplicate)

### Test 9: Remove Multiple CIDRs (Comma-Separated)
**Incident:** INC0010119  
**Description:** Remove 19.0.0.0/8, 20.0.0.0/8, 21.0.0.0/8  
**Result:** ✅ All 3 CIDRs removed successfully

### Test 10: Remove Multiple CIDRs (Mixed Format)
**Incident:** INC0010120  
**Description:** Remove CIDRs with newlines and spaces  
**Result:** ✅ All 3 CIDRs removed successfully

### Test 11: Add with Existing Rules Check
**Incident:** INC0010121  
**Description:** Add mix of new and existing CIDRs  
**Result:** ✅ 2 added, 2 skipped (already existed)

---

## Summary Table

| Incident | Operation | CIDRs | Success | Skipped | Failed |
|----------|-----------|-------|---------|---------|--------|
| INC0010107 | Add | 1 | 1 | 0 | 0 |
| INC0010108 | Add (dup) | 1 | 0 | 1 | 0 |
| INC0010110 | Remove | 1 | 1 | 0 | 0 |
| INC0010111 | Add | 1 | 1 | 0 | 0 |
| INC0010112 | Add | 1 | 1 | 0 | 0 |
| INC0010114 | Add | 1 | 1 | 0 | 0 |
| INC0010115 | Add | 1 | 1 | 0 | 0 |
| INC0010116 | Add | 1 | 1 | 0 | 0 |
| INC0010117 | Add | 3 | 3 | 0 | 0 |
| INC0010118 | Add | 4 | 3 | 1 | 0 |
| INC0010119 | Remove | 3 | 3 | 0 | 0 |
| INC0010120 | Remove | 3 | 3 | 0 | 0 |
| INC0010121 | Add | 4 | 2 | 2 | 0 |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Missing security group ID | Exits with error message |
| Missing CIDR | Exits with error message |
| Missing port | Exits with error message |
| Invalid security group | Exits with verification failed |
| Rule already exists (add) | Skips CIDR, continues with others |
| Rule doesn't exist (remove) | AWS returns error, logged as failed |
| AWS API error | Logged as failed, continues with remaining CIDRs |

---

## File Structure

```
servicenow-mcp/
├── process_security_group_incident.py   # Main processor script
├── create_incident.py                   # Helper to create test incidents
├── backups/                             # Terraform backup files
│   ├── sg-sg-3b49e714_INC0010107_*.md
│   ├── sg-sg-3b49e714_INC0010110_*.md
│   └── ...
└── docs/
    └── SECURITY_GROUP_PROCESSOR.md      # This documentation
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | 2026-01-06 | Initial release - single CIDR support |
| v2.0.0 | 2026-01-06 | Added Terraform backup, cluster verification, duplicate detection |
| v2.1.0 | 2026-01-06 | Multi-CIDR support, improved work notes, MCP Server Automation branding |

---

## Author

**MCP Server Automation**  
Generated: 2026-01-06
