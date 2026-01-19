# Quick Start Guide - ServiceNow Incident Processor

## One-Command Setup (Windows)

### Option 1: PowerShell (Recommended)
```powershell
.\run.ps1
```

### Option 2: Command Prompt (Batch)
```cmd
run.bat
```

That's it! The script will:
1. ✅ Check if Python is installed
2. ✅ Create virtual environment (if needed)
3. ✅ Install all dependencies (if needed)
4. ✅ Start the web application

---

## First-Time Setup

### Step 1: Clone Repository
```powershell
git clone https://github.com/selvar2/sample-workflow.git
cd sample-workflow/servicenow-mcp
git checkout localworkflow
```

### Step 2: Create .env File
```powershell
Copy-Item .env.example .env
```

Then edit `.env` with your credentials:
```env
# Required
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password

# AWS (if using Redshift features)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

### Step 3: Run the Application
```powershell
.\run.ps1
```

---

## Available Scripts

| Script | Description |
|--------|-------------|
| `run.ps1` | PowerShell - Auto-setup and run (recommended) |
| `run.bat` | Batch - Auto-setup and run |
| `setup_local.ps1` | PowerShell - Full setup with verification |
| `setup_local.bat` | Batch - Full setup with verification |

---

## Manual Setup (Optional)

If you prefer manual control:

```powershell
# Create virtual environment
python -m venv .venv

# Activate
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .
pip install bcrypt gunicorn

# Run
python web_ui\run_server.py --debug --port 5000
```

---

## Access the Application

After running, open: **http://127.0.0.1:5000**

---

## Troubleshooting

### "Python not found"
Install Python 3.11+ from https://python.org and ensure it's in your PATH.

### ".env file not found"
Copy `.env.example` to `.env` and add your credentials.

### "charmap codec error"
The UTF-8 encoding fix is already applied. If you still see this, restart the application.

### PowerShell Execution Policy
If PowerShell scripts are blocked, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Files Reference

```
servicenow-mcp/
├── run.ps1              # One-click starter (PowerShell)
├── run.bat              # One-click starter (Batch)
├── setup_local.ps1      # Full setup (PowerShell)
├── setup_local.bat      # Full setup (Batch)
├── .env                 # Your credentials (create from .env.example)
├── .env.example         # Template for credentials
├── requirements.txt     # Python dependencies
└── web_ui/
    └── run_server.py    # Web server entry point
```

---

*For detailed deployment instructions, see `docs/LOCAL_DEPLOYMENT_GUIDE.md`*
