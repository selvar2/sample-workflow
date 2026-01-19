# Local Deployment Guide - ServiceNow Incident Processor

## Overview

This guide covers deploying the ServiceNow Incident Processor application on a local Windows machine. The application was originally developed for GitHub Codespaces and requires specific configuration changes for local deployment.

---

## Prerequisites

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | >= 3.11 | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |

### Verify Prerequisites

```powershell
python --version
pip --version
```

**Expected Output:**
```text
Python 3.13.9
pip 25.2 from C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\Lib\site-packages\pip
```

---

## Key Difference: GitHub Codespaces vs Local

| Aspect | GitHub Codespaces | Local Windows |
|--------|-------------------|---------------|
| **Secrets Location** | GitHub Settings → Codespaces → Secrets | `.env` file in project root |
| **Secret Injection** | Automatic (environment variables) | Manual (load via `python-dotenv`) |
| **Console Encoding** | UTF-8 (default) | cp1252 (requires fix) |
| **Path** | `/workspaces/sample-workflow/servicenow-mcp/` | `C:\Users\{user}\sample-workflow\servicenow-mcp\` |

### Secrets Mapping

| GitHub Codespace Secret | Local .env Variable |
|------------------------|---------------------|
| `AWS_ACCESS_KEY_ID` | `AWS_ACCESS_KEY_ID` |
| `AWS_SECRET_ACCESS_KEY` | `AWS_SECRET_ACCESS_KEY` |
| `SERVICENOW_INSTANCE_URL` | `SERVICENOW_INSTANCE_URL` |
| `SERVICENOW_USERNAME` | `SERVICENOW_USERNAME` |
| `SERVICENOW_PASSWORD` | `SERVICENOW_PASSWORD` |
| `SERVICENOW_AUTH_TYPE` | `SERVICENOW_AUTH_TYPE` |
| `SERVICENOW_CLIENT_ID` | `SERVICENOW_CLIENT_ID` |
| `SERVICENOW_CLIENT_SECRET` | `SERVICENOW_CLIENT_SECRET` |
| `SERVICENOW_TOKEN_URL` | `SERVICENOW_TOKEN_URL` |
| `SERVICENOW_OAUTH_GRANT_TYPE` | `SERVICENOW_OAUTH_GRANT_TYPE` |

---

## Step-by-Step Deployment

### Step 1: Clone/Navigate to Project

```powershell
cd C:\Users\Lenovo\sample-workflow\servicenow-mcp
```

### Step 2: Install Python Dependencies

```powershell
# Install main package in editable mode
pip install -e .

# Install additional dependencies
pip install bcrypt gunicorn
```

**Expected Output:**
```text
Successfully built servicenow-mcp
Installing collected packages: werkzeug, itsdangerous, blinker, flask, flask-cors, servicenow-mcp
Successfully installed blinker-1.9.0 flask-3.1.2 flask-cors-6.0.2 itsdangerous-2.2.0 servicenow-mcp-0.1.0 werkzeug-3.1.5
```

### Step 3: Verify Installation

```powershell
pip list | Select-String "flask|boto3|mcp|dotenv|bcrypt|requests|pydantic|servicenow"
```

**Expected Output:**
```text
bcrypt                    5.0.0
boto3                     1.35.49
Flask                     3.1.2
flask-cors                6.0.2
mcp                       1.3.0
pydantic                  2.12.4
python-dotenv             1.2.1
requests                  2.32.5
servicenow-mcp            0.1.0
```

### Step 4: Create .env Configuration File

Create file at: `C:\Users\Lenovo\sample-workflow\servicenow-mcp\.env`

```powershell
@"
# ============================================
# ServiceNow MCP Server Configuration
# ============================================
# Copy values from GitHub Codespace Secrets

# ============================================
# AWS CREDENTIALS
# ============================================
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_PROFILE=default
AWS_DEFAULT_REGION=us-east-1

# ============================================
# SERVICENOW CONFIGURATION
# ============================================
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_AUTH_TYPE=basic

# Basic Authentication
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password

# OAuth Authentication (if using SERVICENOW_AUTH_TYPE=oauth)
SERVICENOW_CLIENT_ID=your-client-id
SERVICENOW_CLIENT_SECRET=your-client-secret
SERVICENOW_TOKEN_URL=https://your-instance.service-now.com/oauth_token.do
SERVICENOW_OAUTH_GRANT_TYPE=client_credentials

# ============================================
# APPLICATION SETTINGS
# ============================================
FASTMCP_LOG_LEVEL=INFO
POLL_INTERVAL=10
MAX_RETRIES=3
STATEMENT_TIMEOUT=60
"@ | Out-File -FilePath ".env" -Encoding utf8
```

### Step 5: Update .env with Actual Credentials

1. Go to GitHub → Settings → Codespaces → Secrets
2. Copy each secret value
3. Paste into the corresponding variable in `.env`

> **Note:** GitHub doesn't show existing secret values. You may need to re-enter them or check your password manager.

### Step 6: Start the Application

**Development Mode:**
```powershell
python web_ui/run_server.py --debug --port 5000
```

**Production Mode:**
```powershell
python web_ui/run_server.py --production --workers 4
```

**Expected Output:**
```text
Database initialized at: C:\Users\Lenovo\sample-workflow\servicenow-mcp\web_ui\auth.db
======================================================================
ServiceNow Incident Processor - Web UI
======================================================================
Mode: Development
Local URL: http://0.0.0.0:5000
======================================================================
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.0.105:5000
 * Debugger is active!
 * Debugger PIN: xxx-xxx-xxx
```

### Step 7: Verify Deployment

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:5000" -UseBasicParsing -TimeoutSec 5
```

**Expected Output:**
```text
StatusCode        : 200
StatusDescription : OK
```

### Step 8: Access the Application

Open browser: **http://127.0.0.1:5000**

---

## Troubleshooting

### Error 1: Missing Environment Variables

**Error Message:**
```text
Error: Missing required environment variables.
Please set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD.
```

**Solution:**
1. Verify `.env` file exists at `C:\Users\Lenovo\sample-workflow\servicenow-mcp\.env`
2. Check that all required variables have values (not placeholders)
3. Restart the application

**Verification Command:**
```powershell
Get-Content ".env" | Select-String "^[A-Z]" | ForEach-Object { $_.Line.Split("=")[0] }
```

---

### Error 2: Unicode Encoding Error (Windows-Specific)

**Error Message:**
```text
'charmap' codec can't encode character '\u2713' in position 0: character maps to
```

**Root Cause:**
- Windows console uses `cp1252` encoding
- Application uses Unicode symbols (✓, ✗, ✅, ❌)

**Solution:**
Add UTF-8 encoding fix to these files:
- `process_servicenow_redshift.py`
- `process_security_group_incident.py`
- `web_ui/app.py`

**Code to Add (after imports):**
```python
# Windows UTF-8 Encoding Fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
```

---

### Error 3: Port Already in Use

**Error Message:**
```text
OSError: [Errno 98] Address already in use
```

**Solution:**
```powershell
# Find and kill existing Python processes
Get-Process -Name "python" | Stop-Process -Force

# Or use a different port
python web_ui/run_server.py --debug --port 8080
```

---

### Error 4: Module Not Found

**Error Message:**
```text
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
```powershell
# Reinstall dependencies
pip install -e .
pip install bcrypt gunicorn flask flask-cors
```

---

## Quick Reference Commands

| Action | Command |
|--------|---------|
| Start (Dev) | `python web_ui/run_server.py --debug --port 5000` |
| Start (Prod) | `python web_ui/run_server.py --production` |
| Stop Server | `Get-Process -Name "python" \| Stop-Process -Force` |
| Check Status | `Invoke-WebRequest -Uri "http://127.0.0.1:5000" -UseBasicParsing` |
| View Logs | Check terminal output |
| Install Deps | `pip install -e .` |

---

## Application URLs

| URL | Description |
|-----|-------------|
| http://127.0.0.1:5000 | Local access |
| http://192.168.0.105:5000 | Network access (your IP may vary) |
| http://127.0.0.1:5000/login | Login page |
| http://127.0.0.1:5000/api/events | API events endpoint |

---

## Security Notes

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Use strong passwords** for ServiceNow credentials
3. **Rotate AWS keys** periodically
4. **Use OAuth** instead of basic auth for production

---

## Files Modified for Local Deployment

| File | Change |
|------|--------|
| `.env` | Created (secrets configuration) |
| `process_servicenow_redshift.py` | UTF-8 encoding fix |
| `process_security_group_incident.py` | UTF-8 encoding fix |
| `web_ui/app.py` | UTF-8 encoding fix |

---

*Last Updated: January 19, 2026*
