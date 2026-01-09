# GitHub Codespaces Secrets Setup Guide

This guide explains how to configure ServiceNow MCP authentication using GitHub Codespaces secrets for secure credential management.

## Overview

GitHub Codespaces secrets allow you to store sensitive credentials securely without committing them to your repository. The ServiceNow MCP application reads these secrets as environment variables at runtime.

## Benefits of Using GitHub Secrets

| Aspect | Hardcoded .env | GitHub Secrets |
|--------|---------------|----------------|
| **Security** | ❌ Risk of exposure | ✅ Encrypted at rest |
| **Version Control** | ❌ May be committed | ✅ Never in repo |
| **Rotation** | ❌ Manual file updates | ✅ Update in one place |
| **Team Sharing** | ❌ Share files manually | ✅ Automatic for collaborators |

---

## Prerequisites

- GitHub account with access to the repository
- ServiceNow instance with admin access
- OAuth application configured in ServiceNow (see [OAUTH_SETUP_GUIDE.md](OAUTH_SETUP_GUIDE.md))

---

## Step 1: Navigate to GitHub Secrets Settings

1. Go to **GitHub.com**
2. Click your **profile picture** (top-right)
3. Select **Settings**
4. In the left sidebar, click **Codespaces**
5. Scroll to **Codespaces secrets** section

**Direct URL:**
```
https://github.com/settings/codespaces
```

---

## Step 2: Required Secrets

### Core Secrets (Required for All Auth Types)

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SERVICENOW_INSTANCE_URL` | Your ServiceNow instance URL | `https://dev282453.service-now.com` |
| `SERVICENOW_AUTH_TYPE` | Authentication method | `basic` or `oauth` |

### Basic Authentication Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SERVICENOW_USERNAME` | ServiceNow username | `admin` |
| `SERVICENOW_PASSWORD` | ServiceNow password | `your-password` |

### OAuth Authentication Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SERVICENOW_CLIENT_ID` | OAuth Client ID | `0cb82d91d35e486499fe3b276c8a33f0` |
| `SERVICENOW_CLIENT_SECRET` | OAuth Client Secret | `your-client-secret` |
| `SERVICENOW_TOKEN_URL` | OAuth Token Endpoint | `https://instance.service-now.com/oauth_token.do` |
| `SERVICENOW_OAUTH_GRANT_TYPE` | Grant type | `password` or `client_credentials` |
| `SERVICENOW_USERNAME` | User for password grant | `admin` |
| `SERVICENOW_PASSWORD` | Password for password grant | `your-password` |

---

## Step 3: Add Secrets (Step-by-Step)

### For OAuth Authentication (Recommended)

Click **"New secret"** for each of the following:

#### Secret 1: SERVICENOW_AUTH_TYPE
```
Name:  SERVICENOW_AUTH_TYPE
Value: oauth
```
Select repository: `your-username/sample-workflow`

#### Secret 2: SERVICENOW_CLIENT_ID
```
Name:  SERVICENOW_CLIENT_ID
Value: <your-client-id-from-servicenow>
```
Select repository: `your-username/sample-workflow`

#### Secret 3: SERVICENOW_CLIENT_SECRET
```
Name:  SERVICENOW_CLIENT_SECRET
Value: <your-client-secret-from-servicenow>
```
Select repository: `your-username/sample-workflow`

#### Secret 4: SERVICENOW_TOKEN_URL
```
Name:  SERVICENOW_TOKEN_URL
Value: https://<your-instance>.service-now.com/oauth_token.do
```
Select repository: `your-username/sample-workflow`

#### Secret 5: SERVICENOW_OAUTH_GRANT_TYPE
```
Name:  SERVICENOW_OAUTH_GRANT_TYPE
Value: password
```
Select repository: `your-username/sample-workflow`

> **Note:** For `password` grant, you also need `SERVICENOW_USERNAME` and `SERVICENOW_PASSWORD` secrets.

---

## Step 4: Verify Repository Access

For each secret, ensure you grant access to the correct repository:

1. After creating the secret, click on it
2. Under **Repository access**, select:
   - **Selected repositories**
   - Check `your-username/sample-workflow`
3. Click **Update selection**

---

## Step 5: Rebuild Codespace

**Important:** After adding or modifying secrets, you must rebuild your Codespace:

### Option A: Via Command Palette
1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type: `Codespaces: Rebuild Container`
3. Select it and confirm

### Option B: Via Codespace Menu
1. Click the **Codespaces** menu (bottom-left corner)
2. Select **Rebuild Container**

### Option C: Full Rebuild (if issues persist)
1. Press `Ctrl+Shift+P`
2. Type: `Codespaces: Full Rebuild Container`
3. This clears cache and rebuilds from scratch

---

## Step 6: Verify Secrets are Loaded

After rebuild, verify your secrets are available:

```bash
cd /workspaces/sample-workflow/servicenow-mcp
source .venv/bin/activate

# Check environment variables (will show values from GitHub secrets)
echo "Auth Type: $SERVICENOW_AUTH_TYPE"
echo "Instance URL: $SERVICENOW_INSTANCE_URL"
echo "Client ID: ${SERVICENOW_CLIENT_ID:0:10}..."
```

---

## Step 7: Test Authentication

### Test OAuth Authentication

```bash
cd /workspaces/sample-workflow/servicenow-mcp
source .venv/bin/activate
python test_oauth_auth.py
```

Expected output:
```
============================================================
ServiceNow OAuth Authentication Test
============================================================
✅ SUCCESS: OAuth token obtained!
🧪 Testing token with API call...
  ✅ API call successful!
```

### Test Basic Authentication

First, update the secret:
```
SERVICENOW_AUTH_TYPE=basic
```

Then rebuild Codespace and test:
```bash
python -c "
from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig
import os

config = AuthConfig(
    type=AuthType.BASIC,
    basic=BasicAuthConfig(
        username=os.getenv('SERVICENOW_USERNAME'),
        password=os.getenv('SERVICENOW_PASSWORD')
    )
)
auth = AuthManager(config, os.getenv('SERVICENOW_INSTANCE_URL'))
headers = auth.get_headers()
print('✅ Basic Auth configured successfully')
"
```

---

## Configuration Summary

### For OAuth (Recommended)

| Secret | Value |
|--------|-------|
| `SERVICENOW_INSTANCE_URL` | `https://your-instance.service-now.com` |
| `SERVICENOW_AUTH_TYPE` | `oauth` |
| `SERVICENOW_CLIENT_ID` | `your-client-id` |
| `SERVICENOW_CLIENT_SECRET` | `your-client-secret` |
| `SERVICENOW_TOKEN_URL` | `https://your-instance.service-now.com/oauth_token.do` |
| `SERVICENOW_OAUTH_GRANT_TYPE` | `password` |
| `SERVICENOW_USERNAME` | `admin` |
| `SERVICENOW_PASSWORD` | `your-password` |

### For Basic Auth

| Secret | Value |
|--------|-------|
| `SERVICENOW_INSTANCE_URL` | `https://your-instance.service-now.com` |
| `SERVICENOW_AUTH_TYPE` | `basic` |
| `SERVICENOW_USERNAME` | `admin` |
| `SERVICENOW_PASSWORD` | `your-password` |

---

## Switching Between Auth Methods

To switch between Basic and OAuth authentication:

1. Go to GitHub Settings → Codespaces → Secrets
2. Edit `SERVICENOW_AUTH_TYPE` secret:
   - For Basic: `basic`
   - For OAuth: `oauth`
3. Rebuild your Codespace

---

## Troubleshooting

### Secrets Not Available

**Symptom:** Environment variables are empty after rebuild

**Solutions:**
1. Verify repository access is granted for each secret
2. Ensure Codespace was rebuilt (not just restarted)
3. Try a full rebuild: `Codespaces: Full Rebuild Container`

### OAuth Token Request Fails

**Symptom:** `401 Unauthorized` or `invalid_client` error

**Solutions:**
1. Verify `SERVICENOW_CLIENT_ID` and `SERVICENOW_CLIENT_SECRET` are correct
2. Check the OAuth application is **Active** in ServiceNow
3. Ensure `SERVICENOW_TOKEN_URL` uses the correct instance name

### Environment Variable Precedence

**Order of precedence (highest to lowest):**
1. Command-line arguments
2. GitHub Codespaces secrets (environment variables)
3. Local `.env` file (if exists)
4. Default values in code

---

## Security Best Practices

1. **Never commit `.env` files** with real credentials
2. **Rotate secrets regularly** - Update both ServiceNow and GitHub
3. **Use least privilege** - Grant repository access only where needed
4. **Audit access** - Regularly review who has access to secrets
5. **Use OAuth over Basic** - OAuth tokens can be revoked without changing passwords

---

## Quick Reference

### Add a New Secret
```
GitHub → Settings → Codespaces → Secrets → New secret
```

### Rebuild Codespace
```
Ctrl+Shift+P → Codespaces: Rebuild Container
```

### Test OAuth
```bash
python test_oauth_auth.py
```

### Check Environment
```bash
env | grep SERVICENOW
```

---

## Related Documentation

- [OAUTH_SETUP_GUIDE.md](OAUTH_SETUP_GUIDE.md) - ServiceNow OAuth application setup
- [README.md](../README.md) - Main project documentation
- [GitHub Docs: Codespaces Secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-encrypted-secrets-for-your-codespaces)
