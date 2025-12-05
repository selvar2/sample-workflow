#!/usr/bin/env python
"""
Script to update an incident in ServiceNow with work notes.
# This code is for testing purposes only.
"""

import os
import sys
from dotenv import load_dotenv

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig
from servicenow_mcp.tools.incident_tools import update_incident, UpdateIncidentParams

# Load environment variables
load_dotenv()

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

# Update incident INC0010010 with work notes
work_notes = """Task completed successfully.

Action taken: Created database user 'user8' in Redshift cluster 'redshift-cluster-1'
- Cluster: redshift-cluster-1
- Database: dev
- User: user8
- Password: Disabled
- Status: User created successfully with standard privileges (no superuser or createdb permissions)

Verification: User existence confirmed via pg_user system catalog query.
Completion timestamp: 2025-11-27 10:52:20 UTC"""

params = UpdateIncidentParams(
    incident_id="INC0010010",
    work_notes=work_notes
)

# Update the incident
print("Updating incident INC0010009...")
result = update_incident(config, auth_manager, params)

# Print the result
if result.success:
    print(f"\n✓ Incident updated successfully!")
    print(f"  Incident Number: {result.incident_number}")
    print(f"  Incident ID: {result.incident_id}")
    print(f"  Message: {result.message}")
else:
    print(f"\n✗ Failed to update incident")
    print(f"  Error: {result.message}")
    sys.exit(1)
