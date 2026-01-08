#!/usr/bin/env python
"""
Enhanced Security Group Incident Processor v2.0.0

Processes ServiceNow incidents for AWS Security Group operations with:
- Dynamic support for any security group, region, and cluster type
- Operations: add, modify, remove inbound/outbound rules
- Automatic backup of existing rules to markdown with Terraform syntax
- Safety checks to prevent unintended modifications
- Verification of security group association with clusters

Author: MCP Server Automation
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig
from servicenow_mcp.tools.incident_tools import (
    get_incident_by_number,
    update_incident,
    GetIncidentByNumberParams,
    UpdateIncidentParams
)

# Load environment variables
load_dotenv()

# Configuration
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")

# Get configuration from environment variables
instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
username = os.getenv("SERVICENOW_USERNAME")
password = os.getenv("SERVICENOW_PASSWORD")
auth_type = os.getenv("SERVICENOW_AUTH_TYPE", "basic")

if not instance_url or not username or not password:
    print("Error: Missing required environment variables.")
    print("Please set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD.")
    sys.exit(1)

# Create configuration
config_dict = {
    "instance_url": instance_url,
    "auth": {
        "type": auth_type,
        "basic": {
            "username": username,
            "password": password
        }
    }
}

config = ServerConfig(**config_dict)
auth_manager = AuthManager(config.auth, config.instance_url)


# =============================================================================
# AWS Helper Functions - Security Group Details
# =============================================================================

def get_security_group_details(sg_id: str, region: str) -> Dict[str, Any]:
    """Fetch complete security group details including name, VPC, and description."""
    cmd = [
        "aws", "ec2", "describe-security-groups",
        "--group-ids", sg_id,
        "--region", region,
        "--no-cli-pager"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response = json.loads(result.stdout)
        if response.get("SecurityGroups"):
            sg = response["SecurityGroups"][0]
            return {
                "success": True,
                "security_group_id": sg.get("GroupId"),
                "security_group_name": sg.get("GroupName"),
                "vpc_id": sg.get("VpcId"),
                "description": sg.get("Description"),
                "owner_id": sg.get("OwnerId"),
                "tags": {tag["Key"]: tag["Value"] for tag in sg.get("Tags", [])}
            }
        return {"success": False, "message": "Security group not found"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Error: {e.stderr or str(e)}"}
    except json.JSONDecodeError as e:
        return {"success": False, "message": f"JSON parse error: {str(e)}"}


def get_security_group_rules(sg_id: str, region: str, rule_type: str = "inbound") -> Dict[str, Any]:
    """Fetch all rules for a security group."""
    is_egress = rule_type == "outbound"
    
    cmd = [
        "aws", "ec2", "describe-security-group-rules",
        "--filter", f"Name=group-id,Values={sg_id}",
        "--region", region,
        "--no-cli-pager"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response = json.loads(result.stdout)
        all_rules = response.get("SecurityGroupRules", [])
        filtered_rules = [r for r in all_rules if r.get("IsEgress") == is_egress]
        
        return {
            "success": True,
            "rules": filtered_rules,
            "all_rules": all_rules
        }
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Error: {e.stderr or str(e)}", "rules": []}
    except json.JSONDecodeError as e:
        return {"success": False, "message": f"JSON parse error: {str(e)}", "rules": []}


def get_cluster_security_groups(cluster_identifier: str, region: str, cluster_type: str = "redshift") -> Dict[str, Any]:
    """Get security groups associated with a cluster (supports redshift, rds)."""
    if cluster_type == "redshift":
        cmd = [
            "aws", "redshift", "describe-clusters",
            "--cluster-identifier", cluster_identifier,
            "--region", region,
            "--no-cli-pager"
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            response = json.loads(result.stdout)
            clusters = response.get("Clusters", [])
            if clusters:
                vpc_sgs = clusters[0].get("VpcSecurityGroups", [])
                return {
                    "success": True,
                    "cluster_identifier": cluster_identifier,
                    "security_groups": [sg["VpcSecurityGroupId"] for sg in vpc_sgs],
                    "cluster_status": clusters[0].get("ClusterStatus"),
                    "vpc_id": clusters[0].get("VpcId")
                }
            return {"success": False, "message": "Cluster not found", "security_groups": []}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Error: {e.stderr or str(e)}", "security_groups": []}
    
    return {"success": False, "message": f"Unsupported cluster type: {cluster_type}", "security_groups": []}


def check_rule_exists(sg_id: str, region: str, cidr: str, port: int, protocol: str = "tcp") -> Tuple[bool, Optional[Dict]]:
    """Check if a rule with the same CIDR, port, and protocol already exists."""
    rules_result = get_security_group_rules(sg_id, region, "inbound")
    
    if not rules_result["success"]:
        return False, None
    
    for rule in rules_result["rules"]:
        rule_cidr = rule.get("CidrIpv4") or rule.get("CidrIpv6")
        rule_from_port = rule.get("FromPort")
        rule_to_port = rule.get("ToPort")
        rule_protocol = rule.get("IpProtocol")
        
        if rule_cidr == cidr and rule_from_port == port and rule_to_port == port:
            if rule_protocol == protocol or rule_protocol == "-1":
                return True, rule
    
    return False, None


# =============================================================================
# Request Parser - Dynamic parsing from incident description
# =============================================================================

def parse_security_group_request(description: str) -> Dict[str, Any]:
    """
    Parse security group operation details from incident description.
    Supports: add/remove/modify inbound/outbound rules, multiple clusters, regions.
    Supports multiple CIDRs in any format (comma, space, newline separated).
    """
    result = {
        "operation": None,
        "rule_direction": "inbound",
        "security_group_id": None,
        "security_group_name": None,
        "vpc_id": None,
        "region": "us-east-1",
        "cidr": None,
        "cidrs": [],  # Support for multiple CIDRs
        "port": None,
        "port_range_end": None,
        "protocol": "tcp",
        "description": None,
        "rule_type": None,
        "cluster_identifier": None,
        "cluster_type": None,
        "explicit_modify": False,
        "explicit_remove": False
    }
    
    description_lower = description.lower()
    
    # Detect operation type - must be explicit
    if re.search(r'add\s+(an?\s+)?inbound\s+rule', description, re.IGNORECASE):
        result["operation"] = "add_inbound_rule"
        result["rule_direction"] = "inbound"
    elif re.search(r'add\s+(an?\s+)?outbound\s+rule', description, re.IGNORECASE):
        result["operation"] = "add_outbound_rule"
        result["rule_direction"] = "outbound"
    elif re.search(r'remove\s+(an?\s+)?inbound\s+rule', description, re.IGNORECASE):
        result["operation"] = "remove_inbound_rule"
        result["rule_direction"] = "inbound"
        result["explicit_remove"] = True
    elif re.search(r'remove\s+(an?\s+)?outbound\s+rule', description, re.IGNORECASE):
        result["operation"] = "remove_outbound_rule"
        result["rule_direction"] = "outbound"
        result["explicit_remove"] = True
    elif re.search(r'modify\s+(an?\s+)?inbound\s+rule', description, re.IGNORECASE):
        result["operation"] = "modify_inbound_rule"
        result["rule_direction"] = "inbound"
        result["explicit_modify"] = True
    elif re.search(r'modify\s+(an?\s+)?outbound\s+rule', description, re.IGNORECASE):
        result["operation"] = "modify_outbound_rule"
        result["rule_direction"] = "outbound"
        result["explicit_modify"] = True
    
    # Extract security group ID
    sg_patterns = [
        r'security\s+group\s+id\s*[:\s]+\s*(sg-[a-zA-Z0-9]+)',
        r'sg[-_]?id\s*[:\s]+\s*(sg-[a-zA-Z0-9]+)',
        r'\b(sg-[a-zA-Z0-9]{8,})\b'
    ]
    for pattern in sg_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            result["security_group_id"] = match.group(1)
            break
    
    # Extract security group name
    sg_name_match = re.search(r'name\s+of\s+security\s+group\s*[:\s]+\s*([^\n,]+)', description, re.IGNORECASE)
    if sg_name_match:
        result["security_group_name"] = sg_name_match.group(1).strip()
    
    # Extract VPC ID
    vpc_match = re.search(r'vpc[-_]?id\s*[:\s]+\s*(vpc-[a-zA-Z0-9]+)', description, re.IGNORECASE)
    if vpc_match:
        result["vpc_id"] = vpc_match.group(1)
    
    # Extract region
    region_match = re.search(r'region\s*[:\s]+\s*([a-z]{2}-[a-z]+-\d+)', description, re.IGNORECASE)
    if region_match:
        result["region"] = region_match.group(1)
    
    # Extract ALL CIDR ranges - supports multiple formats:
    # - Comma separated: 17.0.0.0/8, 18.0.0.0/8
    # - Space separated: 17.0.0.0/8 18.0.0.0/8
    # - Newline separated: 17.0.0.0/8\n18.0.0.0/8
    # - Mixed formats
    cidr_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})\b'
    all_cidrs = re.findall(cidr_pattern, description)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_cidrs = []
    for cidr in all_cidrs:
        if cidr not in seen:
            seen.add(cidr)
            unique_cidrs.append(cidr)
    
    result["cidrs"] = unique_cidrs
    # For backward compatibility, set first CIDR as "cidr"
    if unique_cidrs:
        result["cidr"] = unique_cidrs[0]
    
    # Extract port
    port_match = re.search(r'port\s*[:\s]+\s*(\d+)', description, re.IGNORECASE)
    if port_match:
        result["port"] = int(port_match.group(1))
        result["port_range_end"] = result["port"]
    
    # Extract protocol
    protocol_match = re.search(r'protocol\s*[:\s]+\s*(tcp|udp|icmp|all)', description, re.IGNORECASE)
    if protocol_match:
        proto = protocol_match.group(1).lower()
        result["protocol"] = "-1" if proto == "all" else proto
    
    # Extract type and set default ports
    type_ports = {"redshift": 5439, "postgresql": 5432, "mysql": 3306, "ssh": 22, "https": 443, "http": 80}
    type_match = re.search(r'type\s*[:\s]+\s*(\w+)', description, re.IGNORECASE)
    if type_match:
        rule_type = type_match.group(1).lower()
        result["rule_type"] = rule_type
        if rule_type in type_ports and not result["port"]:
            result["port"] = type_ports[rule_type]
            result["port_range_end"] = result["port"]
    
    # Extract cluster info
    cluster_match = re.search(r'redshift[-_]cluster[-_](\d+)', description, re.IGNORECASE)
    if cluster_match:
        result["cluster_identifier"] = f"redshift-cluster-{cluster_match.group(1)}"
        result["cluster_type"] = "redshift"
    
    # Detect cluster type
    if "redshift" in description_lower:
        result["cluster_type"] = "redshift"
        if not result["port"]:
            result["port"] = 5439
            result["port_range_end"] = 5439
    
    # Extract rule description
    desc_match = re.search(r'description\s*[:\s]+\s*([^\n]+)', description, re.IGNORECASE)
    if desc_match:
        desc_text = desc_match.group(1).strip()
        if len(desc_text) < 100:
            result["description"] = desc_text
    
    if not result["description"]:
        result["description"] = "MCP Server Automation"
    
    return result


# =============================================================================
# Terraform Backup Generator - Markdown with HCL syntax
# =============================================================================

def generate_terraform_backup(
    sg_id: str,
    sg_details: Dict[str, Any],
    before_rules: List[Dict],
    after_rules: List[Dict],
    operation: str,
    change_details: Dict[str, Any],
    incident_number: str
) -> str:
    """Generate a markdown file with Terraform syntax showing before/after state."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    filename = f"sg-{sg_id}_{incident_number}_{timestamp}.md"
    filepath = os.path.join(BACKUP_DIR, filename)
    
    sg_name = sg_details.get("security_group_name", "unknown")
    vpc_id = sg_details.get("vpc_id", "unknown")
    sg_description = sg_details.get("description", "")
    owner_id = sg_details.get("owner_id", "")
    
    content = f"""# Security Group Backup - {sg_id}

## Incident Information
- **Incident Number:** {incident_number}
- **Operation:** {operation.replace('_', ' ').title()}
- **Timestamp:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
- **Generated By:** MCP Server Automation

---

## Security Group Details

| Property | Value |
|----------|-------|
| Security Group ID | `{sg_id}` |
| Security Group Name | `{sg_name}` |
| VPC ID | `{vpc_id}` |
| Description | {sg_description} |
| Owner ID | {owner_id} |

---

## Change Summary

**Operation:** {operation.replace('_', ' ').title()}

| Parameter | Value |
|-----------|-------|
| CIDR | `{change_details.get('cidr', 'N/A')}` |
| Port | `{change_details.get('port', 'N/A')}` |
| Protocol | `{change_details.get('protocol', 'tcp')}` |
| Rule Description | {change_details.get('description', 'N/A')} |

---

## Before State (Existing Rules)

```hcl
# Security Group: {sg_name}
# State: BEFORE operation

resource "aws_security_group" "{sg_name.replace('-', '_')}" {{
  name        = "{sg_name}"
  description = "{sg_description}"
  vpc_id      = "{vpc_id}"
}}

"""
    
    # Add before rules
    for i, rule in enumerate(before_rules):
        is_egress = rule.get("IsEgress", False)
        rule_type = "egress" if is_egress else "ingress"
        cidr = rule.get("CidrIpv4") or rule.get("CidrIpv6") or "0.0.0.0/0"
        from_port = rule.get("FromPort", 0)
        to_port = rule.get("ToPort", 0)
        protocol = rule.get("IpProtocol", "tcp")
        desc = rule.get("Description", "")
        rule_id = rule.get("SecurityGroupRuleId", "")
        
        content += f"""# Rule ID: {rule_id}
resource "aws_security_group_rule" "{sg_name.replace('-', '_')}_{rule_type}_{i}" {{
  type              = "{rule_type}"
  from_port         = {from_port}
  to_port           = {to_port}
  protocol          = "{protocol}"
  cidr_blocks       = ["{cidr}"]
  security_group_id = aws_security_group.{sg_name.replace('-', '_')}.id
  description       = "{desc}"
}}

"""
    
    content += """```

### Before Rules Table

| Rule ID | Direction | CIDR | Port Range | Protocol | Description |
|---------|-----------|------|------------|----------|-------------|
"""
    
    for rule in before_rules:
        direction = "Outbound" if rule.get("IsEgress", False) else "Inbound"
        cidr = rule.get("CidrIpv4") or rule.get("CidrIpv6") or "N/A"
        content += f"| `{rule.get('SecurityGroupRuleId', 'N/A')}` | {direction} | `{cidr}` | {rule.get('FromPort', 'N/A')}-{rule.get('ToPort', 'N/A')} | {rule.get('IpProtocol', 'N/A')} | {rule.get('Description', '')[:40]} |\n"
    
    content += f"""
---

## Change Applied

```hcl
# Operation: {operation.replace('_', ' ').title()}

resource "aws_security_group_rule" "{sg_name.replace('-', '_')}_change" {{
  type              = "{"egress" if "outbound" in operation else "ingress"}"
  from_port         = {change_details.get('port', 0)}
  to_port           = {change_details.get('port_range_end', change_details.get('port', 0))}
  protocol          = "{change_details.get('protocol', 'tcp')}"
  cidr_blocks       = ["{change_details.get('cidr', '0.0.0.0/0')}"]
  security_group_id = aws_security_group.{sg_name.replace('-', '_')}.id
  description       = "{change_details.get('description', 'MCP Server Automation')}"
}}
```

---

## After State (Updated Rules)

```hcl
# State: AFTER operation

resource "aws_security_group" "{sg_name.replace('-', '_')}" {{
  name        = "{sg_name}"
  description = "{sg_description}"
  vpc_id      = "{vpc_id}"
}}

"""
    
    for i, rule in enumerate(after_rules):
        is_egress = rule.get("IsEgress", False)
        rule_type = "egress" if is_egress else "ingress"
        cidr = rule.get("CidrIpv4") or rule.get("CidrIpv6") or "0.0.0.0/0"
        
        content += f"""resource "aws_security_group_rule" "{sg_name.replace('-', '_')}_{rule_type}_{i}" {{
  type              = "{rule_type}"
  from_port         = {rule.get('FromPort', 0)}
  to_port           = {rule.get('ToPort', 0)}
  protocol          = "{rule.get('IpProtocol', 'tcp')}"
  cidr_blocks       = ["{cidr}"]
  security_group_id = aws_security_group.{sg_name.replace('-', '_')}.id
  description       = "{rule.get('Description', '')}"
}}

"""
    
    content += """```

### After Rules Table

| Rule ID | Direction | CIDR | Port Range | Protocol | Description |
|---------|-----------|------|------------|----------|-------------|
"""
    
    for rule in after_rules:
        direction = "Outbound" if rule.get("IsEgress", False) else "Inbound"
        cidr = rule.get("CidrIpv4") or rule.get("CidrIpv6") or "N/A"
        content += f"| `{rule.get('SecurityGroupRuleId', 'N/A')}` | {direction} | `{cidr}` | {rule.get('FromPort', 'N/A')}-{rule.get('ToPort', 'N/A')} | {rule.get('IpProtocol', 'N/A')} | {rule.get('Description', '')[:40]} |\n"
    
    content += f"""
---

## Rollback Instructions

"""
    
    if "add" in operation:
        content += f"""```bash
aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol {change_details.get('protocol', 'tcp')} --port {change_details.get('port', 0)} --cidr {change_details.get('cidr', '0.0.0.0/0')} --region {change_details.get('region', 'us-east-1')} --no-cli-pager
```"""
    elif "remove" in operation:
        content += f"""```bash
aws ec2 authorize-security-group-ingress --group-id {sg_id} --protocol {change_details.get('protocol', 'tcp')} --port {change_details.get('port', 0)} --cidr {change_details.get('cidr', '0.0.0.0/0')} --region {change_details.get('region', 'us-east-1')} --no-cli-pager
```"""
    
    content += "\n\n---\n*Generated by MCP Server Security Group Processor*\n"
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return filepath


# =============================================================================
# Security Group Operations - Add/Remove Inbound/Outbound Rules
# =============================================================================

def add_inbound_rule(sg_details: Dict[str, Any]) -> Dict[str, Any]:
    """Add an inbound rule to a security group."""
    sg_id = sg_details["security_group_id"]
    region = sg_details["region"]
    cidr = sg_details["cidr"]
    port = sg_details["port"]
    port_end = sg_details.get("port_range_end", port)
    protocol = sg_details["protocol"]
    description = sg_details.get("description", "MCP Server Automation")
    
    ip_permissions = json.dumps([{
        "IpProtocol": protocol,
        "FromPort": port,
        "ToPort": port_end,
        "IpRanges": [{"CidrIp": cidr, "Description": description}]
    }])
    
    cmd = [
        "aws", "ec2", "authorize-security-group-ingress",
        "--group-id", sg_id,
        "--region", region,
        "--ip-permissions", ip_permissions,
        "--no-cli-pager"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response = json.loads(result.stdout)
        return {
            "success": True,
            "message": "Inbound rule added successfully",
            "rule_id": response.get("SecurityGroupRules", [{}])[0].get("SecurityGroupRuleId", "N/A"),
            "details": response
        }
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e)
        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
            return {"success": False, "message": f"Rule already exists: {error_msg}", "details": None}
        return {"success": False, "message": f"Failed to add rule: {error_msg}", "details": None}
    except json.JSONDecodeError:
        return {"success": True, "message": "Inbound rule added", "rule_id": "N/A", "details": None}


def add_outbound_rule(sg_details: Dict[str, Any]) -> Dict[str, Any]:
    """Add an outbound rule to a security group."""
    sg_id = sg_details["security_group_id"]
    region = sg_details["region"]
    cidr = sg_details["cidr"]
    port = sg_details["port"]
    port_end = sg_details.get("port_range_end", port)
    protocol = sg_details["protocol"]
    description = sg_details.get("description", "MCP Server Automation")
    
    ip_permissions = json.dumps([{
        "IpProtocol": protocol,
        "FromPort": port,
        "ToPort": port_end,
        "IpRanges": [{"CidrIp": cidr, "Description": description}]
    }])
    
    cmd = [
        "aws", "ec2", "authorize-security-group-egress",
        "--group-id", sg_id,
        "--region", region,
        "--ip-permissions", ip_permissions,
        "--no-cli-pager"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response = json.loads(result.stdout)
        return {
            "success": True,
            "message": "Outbound rule added successfully",
            "rule_id": response.get("SecurityGroupRules", [{}])[0].get("SecurityGroupRuleId", "N/A"),
            "details": response
        }
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Failed to add rule: {e.stderr or str(e)}", "details": None}
    except json.JSONDecodeError:
        return {"success": True, "message": "Outbound rule added", "rule_id": "N/A", "details": None}


def remove_inbound_rule(sg_details: Dict[str, Any]) -> Dict[str, Any]:
    """Remove an inbound rule from a security group. Only when explicitly requested."""
    sg_id = sg_details["security_group_id"]
    region = sg_details["region"]
    cidr = sg_details["cidr"]
    port = sg_details["port"]
    port_end = sg_details.get("port_range_end", port)
    protocol = sg_details["protocol"]
    
    ip_permissions = json.dumps([{
        "IpProtocol": protocol,
        "FromPort": port,
        "ToPort": port_end,
        "IpRanges": [{"CidrIp": cidr}]
    }])
    
    cmd = [
        "aws", "ec2", "revoke-security-group-ingress",
        "--group-id", sg_id,
        "--region", region,
        "--ip-permissions", ip_permissions,
        "--no-cli-pager"
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"success": True, "message": "Inbound rule removed successfully", "details": None}
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Failed to remove rule: {e.stderr or str(e)}", "details": None}


def remove_outbound_rule(sg_details: Dict[str, Any]) -> Dict[str, Any]:
    """Remove an outbound rule from a security group. Only when explicitly requested."""
    sg_id = sg_details["security_group_id"]
    region = sg_details["region"]
    cidr = sg_details["cidr"]
    port = sg_details["port"]
    port_end = sg_details.get("port_range_end", port)
    protocol = sg_details["protocol"]
    
    ip_permissions = json.dumps([{
        "IpProtocol": protocol,
        "FromPort": port,
        "ToPort": port_end,
        "IpRanges": [{"CidrIp": cidr}]
    }])
    
    cmd = [
        "aws", "ec2", "revoke-security-group-egress",
        "--group-id", sg_id,
        "--region", region,
        "--ip-permissions", ip_permissions,
        "--no-cli-pager"
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"success": True, "message": "Outbound rule removed successfully", "details": None}
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Failed to remove rule: {e.stderr or str(e)}", "details": None}


# =============================================================================
# Main Incident Processor
# =============================================================================

def process_incident(incident_number: str) -> Dict[str, Any]:
    """Process a ServiceNow incident for security group operations with all safety checks.
    
    Returns:
        Dict containing:
        - success: bool indicating if operation succeeded
        - incident_number: the incident number
        - message: summary message
        - actions: list of action descriptions
        - sg_details: detailed security group operation results (similar to redshift details)
    """
    
    print(f"Processing incident {incident_number}...")
    print("=" * 70)
    
    # Step 1: Read the incident
    print("\n[Step 1] Reading incident details...")
    params = GetIncidentByNumberParams(incident_number=incident_number)
    result = get_incident_by_number(config, auth_manager, params)
    
    if not result["success"]:
        print(f"✗ Failed to fetch incident: {result['message']}")
        return {
            "success": False,
            "incident_number": incident_number,
            "message": f"Failed to fetch incident: {result['message']}",
            "actions": [],
            "sg_details": None
        }
    
    incident = result["incident"]
    print(f"✓ Incident retrieved: {incident['number']}")
    print(f"  Short Description: {incident['short_description']}")
    print(f"  State: {incident['state']}")
    
    # Step 2: Parse the incident description
    print("\n[Step 2] Parsing security group operation details...")
    description = incident['description']
    sg_request = parse_security_group_request(description)
    
    # Validation - operation must be explicit
    if not sg_request["operation"]:
        print("✗ Could not determine operation type")
        print("  ⚠ No action taken - operation must be explicitly specified")
        return {
            "success": False,
            "incident_number": incident_number,
            "message": "Could not determine operation type - must be explicitly specified",
            "actions": ["Failed to parse operation type from description"],
            "sg_details": None
        }
    
    if not sg_request["security_group_id"]:
        print("✗ Could not find security group ID")
        return {
            "success": False,
            "incident_number": incident_number,
            "message": "Could not find security group ID in description",
            "actions": ["Failed to parse security group ID"],
            "sg_details": None
        }
    
    if not sg_request["cidrs"]:
        print("✗ Could not find any CIDR range")
        return {
            "success": False,
            "incident_number": incident_number,
            "message": "Could not find any CIDR range in description",
            "actions": ["Failed to parse CIDR ranges"],
            "sg_details": None
        }
    
    if not sg_request["port"]:
        print("✗ Could not find port")
        return {
            "success": False,
            "incident_number": incident_number,
            "message": "Could not find port in description",
            "actions": ["Failed to parse port number"],
            "sg_details": None
        }
    
    # Display all detected CIDRs
    cidr_count = len(sg_request["cidrs"])
    print(f"✓ Parsed operation: {sg_request['operation']}")
    print(f"  Security Group: {sg_request['security_group_id']}")
    print(f"  Region: {sg_request['region']}")
    print(f"  CIDRs detected: {cidr_count}")
    for i, cidr in enumerate(sg_request["cidrs"], 1):
        print(f"    {i}. {cidr}")
    print(f"  Port: {sg_request['port']}")
    
    # Step 3: Verify security group exists
    print(f"\n[Step 3] Verifying security group...")
    sg_info = get_security_group_details(sg_request["security_group_id"], sg_request["region"])
    
    if not sg_info["success"]:
        print(f"✗ Security group verification failed: {sg_info.get('message')}")
        return {
            "success": False,
            "incident_number": incident_number,
            "message": f"Security group verification failed: {sg_info.get('message')}",
            "actions": ["Failed to verify security group exists"],
            "sg_details": {
                "security_group_id": sg_request["security_group_id"],
                "region": sg_request["region"],
                "error": sg_info.get('message')
            }
        }
    
    print(f"✓ Security group verified: {sg_info['security_group_name']}")
    
    # Step 4: Verify cluster association if specified
    if sg_request.get('cluster_identifier') and sg_request.get('cluster_type'):
        print(f"\n[Step 4] Verifying cluster association...")
        cluster_info = get_cluster_security_groups(
            sg_request['cluster_identifier'], sg_request['region'], sg_request['cluster_type']
        )
        if cluster_info["success"]:
            if sg_request["security_group_id"] in cluster_info["security_groups"]:
                print(f"✓ Security group is associated with cluster {sg_request['cluster_identifier']}")
            else:
                print(f"⚠ Warning: Security group NOT associated with cluster")
        else:
            print(f"⚠ Could not verify cluster: {cluster_info.get('message')}")
    else:
        print(f"\n[Step 4] Skipping cluster verification (not specified)")
    
    # Step 5: Capture before state
    print(f"\n[Step 5] Capturing before state...")
    before_result = get_security_group_rules(sg_request["security_group_id"], sg_request["region"])
    before_rules = before_result.get("all_rules", []) if before_result["success"] else []
    print(f"✓ Captured {len(before_rules)} existing rules")
    
    # Step 6: Process each CIDR
    print(f"\n[Step 6] Processing {len(sg_request['cidrs'])} CIDR(s)...")
    
    operation_map = {
        "add_inbound_rule": add_inbound_rule,
        "add_outbound_rule": add_outbound_rule,
        "remove_inbound_rule": remove_inbound_rule,
        "remove_outbound_rule": remove_outbound_rule,
    }
    
    if sg_request["operation"] not in operation_map:
        print(f"✗ Unsupported operation: {sg_request['operation']}")
        return {
            "success": False,
            "incident_number": incident_number,
            "message": f"Unsupported operation: {sg_request['operation']}",
            "actions": [f"Unknown operation type: {sg_request['operation']}"],
            "sg_details": {
                "security_group_id": sg_request["security_group_id"],
                "operation": sg_request["operation"],
                "supported_operations": list(operation_map.keys())
            }
        }
    
    # Track results for each CIDR
    results = []
    rule_direction = "Inbound" if "inbound" in sg_request['operation'] else "Outbound"
    action_verb = "ADDED" if "add" in sg_request['operation'] else "REMOVED"
    
    for idx, cidr in enumerate(sg_request["cidrs"], 1):
        print(f"\n  [{idx}/{len(sg_request['cidrs'])}] Processing CIDR: {cidr}")
        
        # Check if rule already exists (for add operations)
        if "add" in sg_request["operation"]:
            rule_exists, existing_rule = check_rule_exists(
                sg_request["security_group_id"], sg_request["region"],
                cidr, sg_request["port"], sg_request["protocol"]
            )
            
            if rule_exists:
                print(f"      ⚠ Rule already exists - skipping")
                results.append({
                    "cidr": cidr,
                    "status": "skipped",
                    "message": "Rule already exists",
                    "rule_id": existing_rule.get('SecurityGroupRuleId', 'N/A')
                })
                continue
        
        # Create a copy of sg_request with current CIDR
        current_request = sg_request.copy()
        current_request["cidr"] = cidr
        
        # Execute operation
        operation_result = operation_map[sg_request["operation"]](current_request)
        
        if operation_result["success"]:
            print(f"      ✓ {rule_direction} rule {action_verb.lower()}")
            if operation_result.get("rule_id"):
                print(f"        Rule ID: {operation_result['rule_id']}")
            results.append({
                "cidr": cidr,
                "status": "success",
                "message": operation_result['message'],
                "rule_id": operation_result.get('rule_id', 'N/A')
            })
        else:
            print(f"      ✗ Failed: {operation_result['message']}")
            results.append({
                "cidr": cidr,
                "status": "failed",
                "message": operation_result['message'],
                "rule_id": None
            })
    
    # Step 7: Capture after state
    print(f"\n[Step 7] Capturing after state...")
    after_result = get_security_group_rules(sg_request["security_group_id"], sg_request["region"])
    after_rules = after_result.get("all_rules", []) if after_result["success"] else []
    print(f"✓ Captured {len(after_rules)} rules after operation")
    
    # Step 8: Generate backup
    print(f"\n[Step 8] Generating Terraform backup...")
    # Use all CIDRs for change details
    change_details = {
        "cidr": ", ".join(sg_request["cidrs"]),
        "port": sg_request["port"],
        "port_range_end": sg_request.get("port_range_end", sg_request["port"]),
        "protocol": sg_request["protocol"],
        "description": sg_request.get("description", "MCP Server Automation"),
        "region": sg_request["region"]
    }
    
    backup_file = generate_terraform_backup(
        sg_request["security_group_id"], sg_info, before_rules, after_rules,
        sg_request["operation"], change_details, incident_number
    )
    print(f"✓ Backup saved: {backup_file}")
    
    # Step 9: Update incident with consolidated results
    print(f"\n[Step 9] Updating incident...")
    completion_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Count results
    success_count = sum(1 for r in results if r["status"] == "success")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    total_count = len(results)
    
    # Build work notes with all results
    work_notes_lines = [
        "═══════════════════════════════════════════",
        "Actions Performed by MCP Server Automation",
        "═══════════════════════════════════════════",
        "",
        f"Total CIDRs Processed: {total_count}",
        f"  ✓ Success: {success_count}",
        f"  ⊘ Skipped (already exists): {skipped_count}",
        f"  ✗ Failed: {failed_count}",
        ""
    ]
    
    # Add details for each CIDR
    for r in results:
        if r["status"] == "success":
            work_notes_lines.append(f"✓ {r['cidr']}:{sg_request['port']} - {rule_direction} rule {action_verb}")
            work_notes_lines.append(f"    Rule ID: {r['rule_id']}")
        elif r["status"] == "skipped":
            work_notes_lines.append(f"⊘ {r['cidr']}:{sg_request['port']} - Already exists")
            work_notes_lines.append(f"    Existing Rule ID: {r['rule_id']}")
        else:
            work_notes_lines.append(f"✗ {r['cidr']}:{sg_request['port']} - Failed")
            work_notes_lines.append(f"    Error: {r['message']}")
    
    work_notes_lines.extend([
        "",
        f"Security Group: {sg_request['security_group_id']} ({sg_info.get('security_group_name', 'N/A')})",
        f"Region: {sg_request['region']}",
        f"Protocol: {sg_request['protocol']}",
        f"Description: {sg_request.get('description', 'MCP Server Automation')}",
        f"Timestamp: {completion_time}",
        "MCP Server Automation"
    ])
    
    work_notes = "\n".join(work_notes_lines)
    
    update_params = UpdateIncidentParams(incident_id=incident_number, work_notes=work_notes, state="2")
    update_result = update_incident(config, auth_manager, update_params)
    
    if update_result.success:
        print(f"✓ Incident updated: {update_result.incident_number}")
    else:
        print(f"✗ Failed to update incident: {update_result.message}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Incident: {incident_number}")
    print(f"Operation: {sg_request['operation'].replace('_', ' ').title()}")
    print(f"CIDRs Processed: {total_count} (Success: {success_count}, Skipped: {skipped_count}, Failed: {failed_count})")
    print(f"Security Group: {sg_request['security_group_id']}")
    print(f"Backup: {os.path.basename(backup_file)}")
    print("=" * 70)
    
    # Build detailed actions list
    actions = []
    actions.append(f"Incident retrieved from ServiceNow")
    actions.append(f"Parsed operation: {sg_request['operation'].replace('_', ' ').title()}")
    actions.append(f"Security group verified: {sg_info.get('security_group_name', 'N/A')}")
    actions.append(f"Before state captured: {len(before_rules)} rules")
    for r in results:
        if r["status"] == "success":
            actions.append(f"{rule_direction} rule {action_verb.lower()} for {r['cidr']}:{sg_request['port']}")
        elif r["status"] == "skipped":
            actions.append(f"Rule skipped for {r['cidr']} (already exists)")
        else:
            actions.append(f"Failed to process {r['cidr']}: {r['message']}")
    actions.append(f"After state captured: {len(after_rules)} rules")
    actions.append(f"Terraform backup created: {os.path.basename(backup_file)}")
    actions.append(f"Incident work notes updated")
    
    # Build detailed sg_details dict (similar to redshift details)
    sg_details = {
        "success": failed_count == 0,
        "message": f"Successfully processed {success_count} CIDR(s)" if failed_count == 0 else f"Processing completed with {failed_count} failure(s)",
        "security_group": {
            "id": sg_request["security_group_id"],
            "name": sg_info.get("security_group_name", "N/A"),
            "vpc_id": sg_info.get("vpc_id", "N/A"),
            "description": sg_info.get("description", "N/A"),
            "owner_id": sg_info.get("owner_id", "N/A")
        },
        "operation": {
            "type": sg_request["operation"],
            "direction": rule_direction,
            "action": action_verb
        },
        "request": {
            "cidrs": sg_request["cidrs"],
            "port": sg_request["port"],
            "port_range_end": sg_request.get("port_range_end", sg_request["port"]),
            "protocol": sg_request["protocol"],
            "region": sg_request["region"],
            "cluster_identifier": sg_request.get("cluster_identifier"),
            "cluster_type": sg_request.get("cluster_type")
        },
        "results": {
            "total_cidrs": total_count,
            "success_count": success_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "cidr_details": results
        },
        "rules": {
            "before_count": len(before_rules),
            "after_count": len(after_rules),
            "net_change": len(after_rules) - len(before_rules)
        },
        "backup": {
            "file": os.path.basename(backup_file),
            "path": backup_file
        },
        "timestamp": completion_time,
        "incident_updated": update_result.success
    }
    
    overall_success = failed_count == 0
    return {
        "success": overall_success,
        "incident_number": incident_number,
        "message": f"Security Group operation completed: {success_count} success, {skipped_count} skipped, {failed_count} failed" if overall_success else f"Security Group operation failed: {failed_count} CIDR(s) failed",
        "actions": actions,
        "sg_details": sg_details
    }


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        incident_number = sys.argv[1]
        result = process_incident(incident_number)
        # Handle both new dict return and legacy bool return for compatibility
        if isinstance(result, dict):
            success = result.get("success", False)
        else:
            success = bool(result)
        sys.exit(0 if success else 1)
    else:
        print("Enhanced Security Group Incident Processor v2.0.0")
        print("-" * 50)
        print("\nUsage: python process_security_group_incident.py <incident_number>")
        print("\nExample: python process_security_group_incident.py INC0010106")
        print("\nSupported Operations:")
        print("  - Add inbound/outbound rule")
        print("  - Remove inbound/outbound rule (explicit only)")
        print("\nFeatures:")
        print("  - Dynamic region/security group support")
        print("  - Terraform backup before changes (.md)")
        print("  - Duplicate rule prevention")
        print("  - Cluster association verification")
        sys.exit(1)
