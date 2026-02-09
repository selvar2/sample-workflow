#!/usr/bin/env python
"""
Script to read an incident from ServiceNow.
"""

import os
import sys
from dotenv import load_dotenv

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig
from servicenow_mcp.tools.incident_tools import get_incident_by_number, GetIncidentByNumberParams

# Load environment variables
load_dotenv()

# Get configuration from environment variables
instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
username = os.getenv("SERVICENOW_USERNAME")
password = os.getenv("SERVICENOW_PASSWORD")
auth_type = os.getenv("SERVICENOW_AUTH_TYPE", "basic")

# OAuth configuration
client_id = os.getenv("SERVICENOW_CLIENT_ID")
client_secret = os.getenv("SERVICENOW_CLIENT_SECRET")
token_url = os.getenv("SERVICENOW_TOKEN_URL")
grant_type = os.getenv("SERVICENOW_OAUTH_GRANT_TYPE", "password")

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

# Add OAuth config if using OAuth
if auth_type == "oauth" and client_id and client_secret:
    config_dict["auth"]["oauth"] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "token_url": token_url or f"{instance_url}/oauth_token.do",
        "username": username,
        "password": password,
        "grant_type": grant_type
    }

config = ServerConfig(**config_dict)
auth_manager = AuthManager(config.auth, config.instance_url)

# Get incident number from command line argument
if len(sys.argv) < 2:
    print("Usage: python read_incident.py <incident_number>")
    sys.exit(1)

incident_number = sys.argv[1]

# Fetch the incident
print(f"Fetching incident {incident_number}...")
params = GetIncidentByNumberParams(incident_number=incident_number)
result = get_incident_by_number(config, auth_manager, params)

# Print the result
if result["success"]:
    print(f"\n✓ Incident {incident_number} found!")
    incident = result["incident"]
    print(f"\n  Incident Number: {incident['number']}")
    print(f"  Incident ID: {incident['sys_id']}")
    print(f"  Short Description: {incident['short_description']}")
    print(f"  Description: {incident['description']}")
    print(f"  State: {incident['state']}")
    print(f"  Priority: {incident['priority']}")
    print(f"  Assigned To: {incident['assigned_to']}")
    print(f"  Category: {incident['category']}")
    print(f"  Created On: {incident['created_on']}")
    print(f"  Updated On: {incident['updated_on']}")
else:
    print(f"\n✗ Failed to fetch incident")
    print(f"  Error: {result['message']}")
    sys.exit(1)
