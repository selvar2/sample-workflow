# ServiceNow OAuth Authentication Setup Guide

This guide explains how to set up OAuth authentication for the ServiceNow MCP integration.

## Overview

The ServiceNow MCP server supports three authentication methods:
1. **Basic Authentication** (default) - Username and password
2. **OAuth 2.0 Authentication** - Client credentials or password grant
3. **API Key Authentication** - Custom API key header

## OAuth Authentication

OAuth 2.0 provides a more secure authentication method compared to basic auth. ServiceNow supports two OAuth grant types:

### Grant Types

| Grant Type | Use Case | Credentials Needed |
|------------|----------|-------------------|
| `client_credentials` | Server-to-server integration | Client ID, Client Secret |
| `password` | User-context operations | Client ID, Client Secret, Username, Password |

## Step-by-Step ServiceNow Configuration

### Step 1: Enable OAuth in ServiceNow

1. Log in to your ServiceNow instance as an admin
2. Navigate to **System OAuth > Application Registry**
3. If OAuth is not enabled, go to **System Properties > OAuth**
4. Ensure the property `com.snc.platform.security.oauth.is.active` is set to `true`

### Step 2: Create an OAuth Application Registry

1. Navigate to **System OAuth > Application Registry**
2. Click **New**
3. Select **"Create an OAuth API endpoint for external clients"**

### Step 3: Configure the OAuth Application

Fill in the following fields:

| Field | Value | Description |
|-------|-------|-------------|
| Name | `MCP Integration` | Descriptive name for your app |
| Client ID | (auto-generated) | Will be used in `SERVICENOW_CLIENT_ID` |
| Client Secret | Click "Generate Secret" | Will be used in `SERVICENOW_CLIENT_SECRET` |
| Redirect URL | Leave empty | Not needed for client_credentials grant |
| Logo URL | (optional) | Your application logo |
| Active | ✓ (checked) | Must be active |
| Refresh Token Lifespan | 8640000 | 100 days in seconds |
| Access Token Lifespan | 1800 | 30 minutes (recommended) |

4. Click **Submit** to save

### Step 4: Configure OAuth Client User (for client_credentials grant)

For `client_credentials` grant, the OAuth client needs a system user:

1. Navigate to **System OAuth > Application Registry**
2. Open your OAuth application
3. Set the **User** field to a service account user (e.g., `admin` or a dedicated integration user)
4. Ensure this user has the required roles:
   - `rest_service`
   - `itil` (for incident management)
   - `table_api` (for table access)
5. Save the record

### Step 5: Grant Required ACLs

Ensure the OAuth application's user has access to the required tables:

1. Navigate to **System Security > Access Control (ACL)**
2. Verify the user's role has read/write access to:
   - `incident` table
   - `sys_user` table
   - `sc_req_item` table (for service requests)
   - Other tables as needed

## Environment Configuration

### Option 1: Client Credentials Grant (Recommended)

Best for server-to-server integrations where no user context is needed.

```bash
# .env file
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_AUTH_TYPE=oauth
SERVICENOW_CLIENT_ID=your-client-id
SERVICENOW_CLIENT_SECRET=your-client-secret
SERVICENOW_TOKEN_URL=https://your-instance.service-now.com/oauth_token.do
SERVICENOW_OAUTH_GRANT_TYPE=client_credentials
```

### Option 2: Password Grant

Best when operations need to be performed in the context of a specific user.

```bash
# .env file
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_AUTH_TYPE=oauth
SERVICENOW_CLIENT_ID=your-client-id
SERVICENOW_CLIENT_SECRET=your-client-secret
SERVICENOW_TOKEN_URL=https://your-instance.service-now.com/oauth_token.do
SERVICENOW_OAUTH_GRANT_TYPE=password
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password
```

## Testing OAuth Authentication

### Using the Test Script

```bash
# Navigate to the servicenow-mcp directory
cd servicenow-mcp

# Activate virtual environment
source .venv/bin/activate

# Run the test script
python test_oauth_auth.py
```

Expected successful output:
```
============================================================
ServiceNow OAuth Authentication Test
============================================================

📋 Configuration:
  Instance URL: https://your-instance.service-now.com
  Client ID: abc12345***
  Client Secret: ***
  Grant Type: client_credentials
  Token URL: https://your-instance.service-now.com/oauth_token.do

🔗 Token URL: https://your-instance.service-now.com/oauth_token.do

🔐 Testing client_credentials grant...

📡 Response Status: 200

✅ SUCCESS: OAuth token obtained!
  Token Type: Bearer
  Expires In: 1800 seconds
  Scope: useraccount
  Token (first 20 chars): eyJhbGciOiJSUzI1NiIs...

🧪 Testing token with API call...
  ✅ API call successful! Retrieved 1 record(s)
```

### Using cURL

Test OAuth token acquisition directly:

```bash
# Client Credentials Grant
curl -X POST "https://your-instance.service-now.com/oauth_token.do" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "client_id:client_secret" \
  -d "grant_type=client_credentials"

# Password Grant
curl -X POST "https://your-instance.service-now.com/oauth_token.do" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "client_id:client_secret" \
  -d "grant_type=password&username=your_username&password=your_password"
```

## Troubleshooting

### Common Errors

#### Error: "invalid_client"
- **Cause**: Client ID or Client Secret is incorrect
- **Solution**: Verify credentials in ServiceNow Application Registry

#### Error: "invalid_grant"
- **Cause**: Invalid username/password for password grant
- **Solution**: Verify user credentials and ensure user is active

#### Error: "unauthorized_client"
- **Cause**: OAuth application is not configured for this grant type
- **Solution**: Check OAuth application settings in ServiceNow

#### Error: 401 Unauthorized on API calls
- **Cause**: Token expired or insufficient permissions
- **Solution**: 
  1. Check token expiration
  2. Verify user roles and ACLs
  3. Ensure OAuth application user has required permissions

#### Error: "CSRF token validation failed"
- **Cause**: ServiceNow CSRF protection blocking request
- **Solution**: Use proper OAuth headers, not session-based auth

### Debug Mode

Enable debug logging to see detailed OAuth flow:

```bash
export FASTMCP_LOG_LEVEL=DEBUG
python -m servicenow_mcp
```

## Switching Between Auth Methods

The authentication method is controlled by `SERVICENOW_AUTH_TYPE`:

```bash
# Use Basic Auth
export SERVICENOW_AUTH_TYPE=basic

# Use OAuth
export SERVICENOW_AUTH_TYPE=oauth

# Use API Key
export SERVICENOW_AUTH_TYPE=api_key
```

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** or secure secret management
3. **Rotate client secrets** periodically
4. **Use client_credentials grant** for server-to-server when possible
5. **Limit OAuth client permissions** to minimum required
6. **Monitor OAuth token usage** in ServiceNow logs
7. **Set appropriate token lifespans** (shorter is more secure)

## API Reference

### Configuration Classes

```python
from servicenow_mcp.utils.config import (
    AuthConfig,
    AuthType,
    OAuthConfig,
    BasicAuthConfig
)

# OAuth with client_credentials
oauth_config = OAuthConfig(
    client_id="your-client-id",
    client_secret="your-client-secret",
    grant_type="client_credentials",
    token_url="https://instance.service-now.com/oauth_token.do"
)

auth_config = AuthConfig(
    type=AuthType.OAUTH,
    oauth=oauth_config
)
```

### AuthManager Usage

```python
from servicenow_mcp.auth.auth_manager import AuthManager

auth_manager = AuthManager(auth_config, instance_url)

# Get headers for API requests (token will be acquired automatically)
headers = auth_manager.get_headers()

# Manually refresh token if needed
auth_manager.refresh_token()
```

## Additional Resources

- [ServiceNow OAuth Documentation](https://docs.servicenow.com/bundle/vancouver-api-reference/page/integrate/inbound-rest/concept/c_OAuthAPI.html)
- [ServiceNow REST API Guide](https://docs.servicenow.com/bundle/vancouver-api-reference/page/integrate/inbound-rest/concept/c_RESTAPI.html)
- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)
