#!/usr/bin/env python3
"""
OAuth Authentication Test Script for ServiceNow MCP

This script tests OAuth authentication against ServiceNow instance.
It can test both client_credentials and password grant types.

Usage:
    # Set environment variables first, then run:
    python test_oauth_auth.py

Environment Variables Required:
    SERVICENOW_INSTANCE_URL - Your ServiceNow instance URL
    SERVICENOW_CLIENT_ID - OAuth client ID
    SERVICENOW_CLIENT_SECRET - OAuth client secret
    
Optional:
    SERVICENOW_TOKEN_URL - OAuth token URL (default: instance_url/oauth_token.do)
    SERVICENOW_OAUTH_GRANT_TYPE - "client_credentials" or "password" (default: client_credentials)
    SERVICENOW_USERNAME - Required for password grant
    SERVICENOW_PASSWORD - Required for password grant
"""

import os
import sys
import base64
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_oauth_authentication():
    """Test OAuth authentication against ServiceNow."""
    
    print("=" * 60)
    print("ServiceNow OAuth Authentication Test")
    print("=" * 60)
    
    # Get configuration from environment
    instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
    client_id = os.getenv("SERVICENOW_CLIENT_ID")
    client_secret = os.getenv("SERVICENOW_CLIENT_SECRET")
    token_url = os.getenv("SERVICENOW_TOKEN_URL")
    grant_type = os.getenv("SERVICENOW_OAUTH_GRANT_TYPE", "client_credentials")
    username = os.getenv("SERVICENOW_USERNAME")
    password = os.getenv("SERVICENOW_PASSWORD")
    
    # Print configuration (masked secrets)
    print("\n📋 Configuration:")
    print(f"  Instance URL: {instance_url}")
    print(f"  Client ID: {client_id[:8] + '***' if client_id and len(client_id) > 8 else 'Not set'}")
    print(f"  Client Secret: {'***' if client_secret else 'Not set'}")
    print(f"  Grant Type: {grant_type}")
    print(f"  Token URL: {token_url or '(will be auto-generated)'}")
    if grant_type == "password":
        print(f"  Username: {username or 'Not set'}")
        print(f"  Password: {'***' if password else 'Not set'}")
    
    # Validate required configuration
    if not instance_url:
        print("\n❌ ERROR: SERVICENOW_INSTANCE_URL is required")
        return False
    
    if not client_id or not client_secret:
        print("\n❌ ERROR: SERVICENOW_CLIENT_ID and SERVICENOW_CLIENT_SECRET are required for OAuth")
        return False
    
    if grant_type == "password" and (not username or not password):
        print("\n❌ ERROR: SERVICENOW_USERNAME and SERVICENOW_PASSWORD are required for password grant")
        return False
    
    # Determine token URL
    if not token_url:
        token_url = f"{instance_url}/oauth_token.do"
    
    print(f"\n🔗 Token URL: {token_url}")
    
    # Prepare authorization header
    auth_str = f"{client_id}:{client_secret}"
    auth_header = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Prepare request data based on grant type
    if grant_type == "client_credentials":
        data = {"grant_type": "client_credentials"}
        print("\n🔐 Testing client_credentials grant...")
    else:
        data = {
            "grant_type": "password",
            "username": username,
            "password": password
        }
        print("\n🔐 Testing password grant...")
    
    # Make the token request
    try:
        response = requests.post(token_url, headers=headers, data=data, timeout=30)
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            token_type = token_data.get("token_type", "Bearer")
            expires_in = token_data.get("expires_in", "N/A")
            scope = token_data.get("scope", "N/A")
            
            print("\n✅ SUCCESS: OAuth token obtained!")
            print(f"  Token Type: {token_type}")
            print(f"  Expires In: {expires_in} seconds")
            print(f"  Scope: {scope}")
            print(f"  Token (first 20 chars): {access_token[:20]}..." if access_token else "  Token: Not found")
            
            # Test the token by making an API call
            print("\n🧪 Testing token with API call...")
            test_api_with_token(instance_url, access_token, token_type)
            
            return True
        else:
            print(f"\n❌ FAILED: OAuth token request failed")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            
            # Parse error details
            try:
                error_data = response.json()
                print(f"  Error: {error_data.get('error', 'Unknown')}")
                print(f"  Description: {error_data.get('error_description', 'No description')}")
            except:
                pass
            
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ ERROR: Request timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ ERROR: Connection failed - {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error - {e}")
        return False


def test_api_with_token(instance_url: str, access_token: str, token_type: str):
    """Test the OAuth token by making an API call to ServiceNow."""
    
    # Try to get system info or list a simple table
    api_url = f"{instance_url}/api/now/table/sys_user?sysparm_limit=1"
    
    headers = {
        "Authorization": f"{token_type} {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get("result", []))
            print(f"  ✅ API call successful! Retrieved {result_count} record(s)")
            return True
        elif response.status_code == 401:
            print(f"  ❌ API call failed - Unauthorized (401)")
            print(f"     Token might be invalid or expired")
            return False
        elif response.status_code == 403:
            print(f"  ❌ API call failed - Forbidden (403)")
            print(f"     OAuth client might not have proper permissions")
            return False
        else:
            print(f"  ⚠️  API call returned status: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ API call error: {e}")
        return False


def print_setup_guide():
    """Print OAuth setup guide for ServiceNow."""
    
    print("\n" + "=" * 60)
    print("📖 ServiceNow OAuth Setup Guide")
    print("=" * 60)
    
    print("""
To set up OAuth in ServiceNow:

1. **Create an OAuth Application Registry**
   - Navigate to: System OAuth > Application Registry
   - Click "New" and select "Create an OAuth API endpoint for external clients"
   - Fill in:
     - Name: Your application name (e.g., "MCP Integration")
     - Client ID: Auto-generated or specify your own
     - Client Secret: Click "Generate Secret" button
     - Redirect URL: Not needed for client_credentials grant
     - Access Token Lifespan: 1800 (30 minutes recommended)
     - Refresh Token Lifespan: 8640000 (100 days)
   - Save the record

2. **Configure OAuth Settings**
   - Ensure OAuth is enabled in your instance
   - Check System Properties > OAuth

3. **For client_credentials grant (recommended)**
   - The OAuth client acts on behalf of a system account
   - Set these environment variables:
     
     SERVICENOW_AUTH_TYPE=oauth
     SERVICENOW_CLIENT_ID=<your-client-id>
     SERVICENOW_CLIENT_SECRET=<your-client-secret>
     SERVICENOW_TOKEN_URL=https://<instance>.service-now.com/oauth_token.do
     SERVICENOW_OAUTH_GRANT_TYPE=client_credentials

4. **For password grant**
   - The OAuth client acts on behalf of a specific user
   - Also set username and password:
     
     SERVICENOW_AUTH_TYPE=oauth
     SERVICENOW_CLIENT_ID=<your-client-id>
     SERVICENOW_CLIENT_SECRET=<your-client-secret>
     SERVICENOW_TOKEN_URL=https://<instance>.service-now.com/oauth_token.do
     SERVICENOW_OAUTH_GRANT_TYPE=password
     SERVICENOW_USERNAME=<username>
     SERVICENOW_PASSWORD=<password>

5. **Grant Required Roles**
   - For client_credentials: Configure the OAuth application's user
   - For password: Ensure the user has necessary roles (e.g., itil, admin)
   - Common roles needed: itil, rest_service, table_api

6. **Test the configuration**
   - Run: python test_oauth_auth.py
""")


if __name__ == "__main__":
    # Check if --help was passed
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print_setup_guide()
        sys.exit(0)
    
    # Run the test
    success = test_oauth_authentication()
    
    if not success:
        print("\n" + "-" * 60)
        print("💡 Need help setting up OAuth? Run: python test_oauth_auth.py --help")
        print("-" * 60)
    
    sys.exit(0 if success else 1)
