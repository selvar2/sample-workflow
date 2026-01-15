# ServiceNow MCP - Authentication Configuration Session
## Date: January 15, 2026

---

## Overview

This document covers the troubleshooting session for configuring `SERVICENOW_AUTH_TYPE` in GitHub Codespaces, including errors encountered, solutions implemented, and the final working configuration.

---

## Table of Contents

1. [Initial Problem](#initial-problem)
2. [Error Analysis](#error-analysis)
3. [Valid Authentication Types](#valid-authentication-types)
4. [Solution: oauth_with_basic_fallback](#solution-oauth_with_basic_fallback)
5. [Terminal Commands and Outputs](#terminal-commands-and-outputs)
6. [Configuration Reference](#configuration-reference)
7. [Troubleshooting Guide](#troubleshooting-guide)

---

## Initial Problem

### Symptom
The application failed to start with a Pydantic `ValidationError` when `SERVICENOW_AUTH_TYPE` was set to an invalid value.

### Initial Incorrect Configuration
```bash
# Codespaces Secret - INCORRECT
SERVICENOW_AUTH_TYPE=basic,oauth
```

### Error Message
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for ServerConfig
auth.type
  Input should be 'basic', 'oauth', 'api_key' or 'oauth_with_basic_fallback' [type=enum, input_value='basic,oauth', input_type=str]
```

---

## Error Analysis

### Root Cause
The `SERVICENOW_AUTH_TYPE` environment variable expects a **single value**, not comma-separated values. The application uses Pydantic for configuration validation, which enforces strict enum types.

### Invalid Values Attempted
| Value | Result |
|-------|--------|
| `basic,oauth` | ❌ ValidationError - not a valid enum |
| `both` | ❌ ValidationError - not a valid enum |
| `oauth,basic` | ❌ ValidationError - not a valid enum |

---

## Valid Authentication Types

The application supports **four** authentication types:

| Auth Type | Description | Required Environment Variables |
|-----------|-------------|-------------------------------|
| `basic` | Basic username/password authentication | `SERVICENOW_USERNAME`, `SERVICENOW_PASSWORD` |
| `oauth` | OAuth 2.0 client credentials | `SERVICENOW_CLIENT_ID`, `SERVICENOW_CLIENT_SECRET` |
| `api_key` | API key authentication | `SERVICENOW_API_KEY` |
| `oauth_with_basic_fallback` | OAuth with automatic Basic auth fallback | All OAuth + Basic credentials |

---

## Solution: oauth_with_basic_fallback

### Description
The `oauth_with_basic_fallback` authentication type provides the best of both worlds:

1. **Primary**: Attempts OAuth authentication first
2. **Fallback**: If OAuth fails (token expired, invalid credentials, etc.), automatically falls back to Basic authentication

### Benefits
- OAuth security as primary method
- Basic auth reliability as backup
- Seamless failover without manual intervention
- No downtime during token refresh issues

### Configuration
```bash
# Codespaces Secret - CORRECT
SERVICENOW_AUTH_TYPE=oauth_with_basic_fallback
```

### Required Environment Variables
```bash
# OAuth credentials (primary)
SERVICENOW_CLIENT_ID=your_client_id
SERVICENOW_CLIENT_SECRET=your_client_secret

# Basic auth credentials (fallback)
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password

# Instance URL (required for all)
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
```

---

## Terminal Commands and Outputs

### 1. Finding app.py Location
```bash
$ find /workspaces/sample-workflow/servicenow-mcp -name "app.py" 2>/dev/null
/workspaces/sample-workflow/servicenow-mcp/web_ui/app.py
```

### 2. Checking Current Auth Type
```bash
$ cd /workspaces/sample-workflow/servicenow-mcp && source .venv/bin/activate && python -c "import os; print('AUTH_TYPE:', os.getenv('SERVICENOW_AUTH_TYPE', 'not set'))"

AUTH_TYPE: oauth_with_basic_fallback
```

### 3. Restarting the Application
```bash
$ cd /workspaces/sample-workflow/servicenow-mcp && pkill -f "python.*app.py" 2>/dev/null; sleep 1; source .venv/bin/activate && python web_ui/app.py
```

### 4. Successful Startup Output
```
Database initialized at: /workspaces/sample-workflow/servicenow-mcp/web_ui/auth.db
======================================================================
ServiceNow Incident Processor - Web UI
======================================================================
Starting server on http://localhost:5000
ServiceNow Instance: https://dev282453.service-now.com
AWS Region: us-east-1
Dry Run Mode: False
----------------------------------------------------------------------
Authentication: Database-backed with AG-UI Protocol Integration
Database: /workspaces/sample-workflow/servicenow-mcp/web_ui/auth.db
Users configured: ['admin', 'admin2', 'demo']
======================================================================
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://10.0.2.99:5000
Press CTRL+C to quit
```

### 5. Searching for Auth Type Usage in Codebase
```bash
$ grep -r "SERVICENOW_AUTH_TYPE" --include="*.py" /workspaces/sample-workflow/servicenow-mcp/

# Key matches:
/servicenow-mcp/process_incident.py:27:auth_type = os.getenv("SERVICENOW_AUTH_TYPE", "basic")
/servicenow-mcp/src/servicenow_mcp/cli.py:61:default=os.environ.get("SERVICENOW_AUTH_TYPE", "basic")
```

---

## Configuration Reference

### GitHub Codespaces Secrets Setup

Navigate to: **Settings → Codespaces → Secrets → Update secret**

| Secret Name | Value |
|-------------|-------|
| `SERVICENOW_AUTH_TYPE` | `oauth_with_basic_fallback` |
| `SERVICENOW_INSTANCE_URL` | `https://your-instance.service-now.com` |
| `SERVICENOW_USERNAME` | `your_username` |
| `SERVICENOW_PASSWORD` | `your_password` |
| `SERVICENOW_CLIENT_ID` | `your_oauth_client_id` |
| `SERVICENOW_CLIENT_SECRET` | `your_oauth_client_secret` |

### Local .env File Configuration
```bash
# /workspaces/sample-workflow/servicenow-mcp/.env

# Authentication Type
SERVICENOW_AUTH_TYPE=oauth_with_basic_fallback

# Instance Configuration
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com

# Basic Auth Credentials
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password

# OAuth Credentials
SERVICENOW_CLIENT_ID=your_client_id
SERVICENOW_CLIENT_SECRET=your_client_secret
```

---

## Troubleshooting Guide

### Error: ValidationError for auth.type

**Symptom:**
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for ServerConfig
auth.type
  Input should be 'basic', 'oauth', 'api_key' or 'oauth_with_basic_fallback'
```

**Solution:**
Set `SERVICENOW_AUTH_TYPE` to one of the valid values:
- `basic`
- `oauth`
- `api_key`
- `oauth_with_basic_fallback`

---

### Error: OAuth Token Expired

**Symptom:**
```
OAuth authentication failed: Token expired
```

**Solution with oauth_with_basic_fallback:**
The system automatically falls back to Basic auth. No manual intervention required.

**Solution with oauth only:**
1. Refresh the OAuth token
2. Or change `SERVICENOW_AUTH_TYPE` to `oauth_with_basic_fallback`

---

### Error: Missing Credentials

**Symptom:**
```
ServiceNow authentication failed: Missing credentials
```

**Solution:**
Ensure all required environment variables are set for your auth type:

| Auth Type | Required Variables |
|-----------|-------------------|
| `basic` | `SERVICENOW_USERNAME`, `SERVICENOW_PASSWORD` |
| `oauth` | `SERVICENOW_CLIENT_ID`, `SERVICENOW_CLIENT_SECRET` |
| `api_key` | `SERVICENOW_API_KEY` |
| `oauth_with_basic_fallback` | All OAuth + Basic credentials |

---

### Error: App Not Starting

**Symptom:**
Application hangs or doesn't respond on port 5000.

**Solution:**
1. Kill existing processes:
   ```bash
   pkill -f "python.*app.py"
   ```

2. Wait and restart:
   ```bash
   sleep 1
   source .venv/bin/activate
   python web_ui/app.py
   ```

3. Full restart command:
   ```bash
   cd /workspaces/sample-workflow/servicenow-mcp && pkill -f "python.*app.py" 2>/dev/null; sleep 1; source .venv/bin/activate && python web_ui/app.py
   ```

---

## Architecture: How oauth_with_basic_fallback Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Request                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              Auth Type = oauth_with_basic_fallback              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  1. Try OAuth Authentication                     │
│     - Use SERVICENOW_CLIENT_ID & SERVICENOW_CLIENT_SECRET       │
│     - Request OAuth token from ServiceNow                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
       ┌──────────┐           ┌──────────────┐
       │ Success  │           │   Failed     │
       └────┬─────┘           └──────┬───────┘
            │                        │
            ▼                        ▼
┌───────────────────┐    ┌─────────────────────────────────────────┐
│  Return Response  │    │      2. Fallback to Basic Auth          │
│                   │    │  - Use SERVICENOW_USERNAME & PASSWORD   │
└───────────────────┘    │  - Retry the same API request           │
                         └─────────────────────┬───────────────────┘
                                               │
                                               ▼
                                    ┌───────────────────┐
                                    │  Return Response  │
                                    └───────────────────┘
```

---

## Files Modified/Referenced

| File | Purpose |
|------|---------|
| `src/servicenow_mcp/utils/config.py` | Auth configuration and enum types |
| `src/servicenow_mcp/auth/auth_manager.py` | Authentication logic with fallback |
| `src/servicenow_mcp/cli.py` | CLI argument parsing for auth type |
| `web_ui/app.py` | Flask application entry point |

---

## Summary

| Item | Before | After |
|------|--------|-------|
| Auth Type Value | `basic,oauth` (invalid) | `oauth_with_basic_fallback` (valid) |
| Application Status | ❌ ValidationError | ✅ Running |
| Authentication | Single method | OAuth + Basic fallback |

---

## Related Documentation

- [OAUTH_SETUP_GUIDE.md](./OAUTH_SETUP_GUIDE.md) - OAuth configuration guide
- [README.md](../README.md) - Main project documentation
- [PYTHON_USAGE.md](../PYTHON_USAGE.md) - Python usage examples

---

*Document generated: January 15, 2026*
*Session conducted in GitHub Codespaces on branch: workflowag5*
