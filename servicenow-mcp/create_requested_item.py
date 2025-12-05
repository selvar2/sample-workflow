#!/usr/bin/env python
"""
Create a Requested Item (RITM) in ServiceNow Service Catalog.

This script creates a ServiceNow Requested Item with the specified details.
A Requested Item represents an individual item requested from the Service Catalog.
# This code is for testing purposes only.

"""

import json
import os
import requests
from dotenv import load_dotenv

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


def create_request_and_item(instance_url: str, headers: dict, short_description: str, description: str) -> dict:
    """
    Create a Service Catalog Request (REQ) and a Requested Item (RITM).
    
    Args:
        instance_url: ServiceNow instance URL
        headers: Authentication headers
        short_description: Short description for the request
        description: Detailed description for the request
        
    Returns:
        Dictionary with the created request and requested item details
    """
    # Step 1: Create a Service Catalog Request (sc_request / REQ)
    request_url = f"{instance_url}/api/now/table/sc_request"
    
    request_data = {
        "short_description": short_description,
        "description": description,
        "requested_for": "6816f79cc0a8016401c5a33be04be441",  # admin user sys_id
    }
    
    headers_with_content = headers.copy()
    headers_with_content["Content-Type"] = "application/json"
    
    print("Step 1: Creating Service Catalog Request (REQ)...")
    response = requests.post(request_url, json=request_data, headers=headers_with_content)
    response.raise_for_status()
    
    request_result = response.json()
    request_record = request_result.get("result", {})
    request_sys_id = request_record.get("sys_id")
    request_number = request_record.get("number")
    
    print(f"  Created Request: {request_number} (sys_id: {request_sys_id})")
    
    # Step 2: Create a Requested Item (sc_req_item / RITM) linked to the request
    ritm_url = f"{instance_url}/api/now/table/sc_req_item"
    
    ritm_data = {
        "request": request_sys_id,  # Link to the parent request
        "short_description": short_description,
        "description": description,
        "quantity": "1",
        "stage": "request_approval",  # Set to approval stage like in the example
    }
    
    print("Step 2: Creating Requested Item (RITM)...")
    ritm_response = requests.post(ritm_url, json=ritm_data, headers=headers_with_content)
    ritm_response.raise_for_status()
    
    ritm_result = ritm_response.json()
    ritm_record = ritm_result.get("result", {})
    ritm_sys_id = ritm_record.get("sys_id")
    ritm_number = ritm_record.get("number")
    
    print(f"  Created Requested Item: {ritm_number} (sys_id: {ritm_sys_id})")
    
    return {
        "success": True,
        "request": {
            "number": request_number,
            "sys_id": request_sys_id,
            "record": request_record
        },
        "requested_item": {
            "number": ritm_number,
            "sys_id": ritm_sys_id,
            "record": ritm_record
        }
    }


def main():
    """Create the requested item."""
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
    auth_manager = AuthManager(auth_config, server_config.instance_url)

    print("=" * 60)
    print("Creating ServiceNow Requested Item (RITM)")
    print("=" * 60)
    print(f"Instance URL: {server_config.instance_url}")
    print()

    # Get authentication headers
    headers = auth_manager.get_headers()
    headers["Accept"] = "application/json"

    # Create the requested item
    short_description = "Add database user for redshift cluster"
    description = "Create database user named user11 with password disabled in redshift cluster 1"

    print(f"Short Description: {short_description}")
    print(f"Description: {description}")
    print()

    try:
        result = create_request_and_item(
            instance_url=server_config.instance_url,
            headers=headers,
            short_description=short_description,
            description=description
        )

        print()
        print("=" * 60)
        print("Result:")
        print("=" * 60)
        
        if result.get("success"):
            print(f"\n✓ Successfully created Requested Item!")
            print(f"\n  Request Number: {result['request']['number']}")
            print(f"  Requested Item Number: {result['requested_item']['number']}")
            print(f"\n  View in ServiceNow:")
            print(f"  {server_config.instance_url}/nav_to.do?uri=sc_req_item.do?sys_id={result['requested_item']['sys_id']}")
        else:
            print("\n✗ Failed to create requested item.")
            
        print()
        print("Full Response:")
        print(json.dumps(result, indent=2, default=str))

    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error creating requested item: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")


if __name__ == "__main__":
    main()
