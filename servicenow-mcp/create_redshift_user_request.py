#!/usr/bin/env python
"""
Create a change request for adding a database user to Redshift cluster.

This script creates a ServiceNow change request with the specified details.
"""

import json
import os
from dotenv import load_dotenv

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.change_tools import create_change_request
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


def main():
    """Create the change request."""
    # Load environment variables from .env file
    load_dotenv()

    # Create auth configuration
    auth_config = AuthConfig(
        type=AuthType.BASIC,
        basic=BasicAuthConfig(
            username=os.environ.get("SERVICENOW_USERNAME"),
            password=os.environ.get("SERVICENOW_PASSWORD"),
        )
    )

    # Create server configuration with auth
    server_config = ServerConfig(
        instance_url=os.environ.get("SERVICENOW_INSTANCE_URL"),
        debug=os.environ.get("DEBUG", "false").lower() == "true",
        auth=auth_config,
    )

    # Create authentication manager with the auth_config
    auth_manager = AuthManager(auth_config)

    print("Creating ServiceNow Change Request")
    print("==================================")
    print(f"Instance URL: {server_config.instance_url}")
    print()

    # Create the change request parameters
    create_params = {
        "short_description": "Add database user for redshift cluster",
        "description": "Create database user named user11 with password disabled in redshift cluster 1",
        "type": "normal",
        "category": "Database",
        "risk": "low",
        "impact": "low",
    }

    print("Creating change request with parameters:")
    print(json.dumps(create_params, indent=2))
    print()

    # Create the change request
    result = create_change_request(auth_manager, server_config, create_params)

    print("Result:")
    print(json.dumps(result, indent=2))

    if result.get("success"):
        change_id = result["change_request"]["sys_id"]
        print(f"\nSuccessfully created change request with ID: {change_id}")
        print("You can view this change request in your ServiceNow instance.")
    else:
        print("\nFailed to create change request.")


if __name__ == "__main__":
    main()