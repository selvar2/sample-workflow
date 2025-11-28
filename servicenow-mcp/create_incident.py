#!/usr/bin/env python
"""
Script to create a new incident in ServiceNow.
"""

import os
import sys
from dotenv import load_dotenv

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig
from servicenow_mcp.tools.incident_tools import create_incident, CreateIncidentParams

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

# Create incident parameters
params = CreateIncidentParams(
    short_description="Add database user for redshift cluster",
    description="Create database user named user9 with password disable in redshift cluster 1"
)

# Create the incident
print("Creating incident...")
result = create_incident(config, auth_manager, params)

# Print the result
if result.success:
    print(f"\n✓ Incident created successfully!")
    print(f"  Incident Number: {result.incident_number}")
    print(f"  Incident ID: {result.incident_id}")
    print(f"  Message: {result.message}")
else:
    print(f"\n✗ Failed to create incident")
    print(f"  Error: {result.message}")
    sys.exit(1)
