# ============================================
# ServiceNow MCP - One-Click Setup (PowerShell)
# ============================================
# Run: .\setup_environment.ps1
# ============================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ServiceNow MCP - Environment Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to script directory
Set-Location $PSScriptRoot
Write-Host "[INFO] Working directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# ============================================
# Step 1: Find Python
# ============================================
Write-Host "[STEP 1/5] Detecting Python..." -ForegroundColor Yellow

$pythonCmd = $null

# Try 'py' launcher first
try {
    $pyVersion = py --version 2>&1
    $pythonCmd = "py"
    Write-Host "  Found $pyVersion via 'py' launcher" -ForegroundColor Gray
} catch {
    try {
        $pyVersion = python --version 2>&1
        $pythonCmd = "python"
        Write-Host "  Found $pyVersion" -ForegroundColor Gray
    } catch {
        Write-Host "  [ERROR] Python not found!" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Please install Python 3.11+ from https://python.org" -ForegroundColor White
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "  [OK] Using: $pythonCmd" -ForegroundColor Green
Write-Host ""

# ============================================
# Step 2: Check .env file
# ============================================
Write-Host "[STEP 2/5] Checking configuration..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "  [INFO] .env not found, copying from .env.example..." -ForegroundColor Cyan
        Copy-Item ".env.example" ".env"
        Write-Host "  [WARNING] Please edit .env with your actual credentials!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Required settings:" -ForegroundColor White
        Write-Host "  - AWS_ACCESS_KEY_ID" -ForegroundColor White
        Write-Host "  - AWS_SECRET_ACCESS_KEY" -ForegroundColor White
        Write-Host "  - SERVICENOW_INSTANCE_URL" -ForegroundColor White
        Write-Host "  - SERVICENOW_USERNAME" -ForegroundColor White
        Write-Host "  - SERVICENOW_PASSWORD" -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter after editing .env"
    } else {
        Write-Host "  [ERROR] No .env or .env.example found!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "  [OK] .env file found" -ForegroundColor Green
}
Write-Host ""

# ============================================
# Step 3: Create Virtual Environment
# ============================================
Write-Host "[STEP 3/5] Setting up virtual environment..." -ForegroundColor Yellow

if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "  [OK] Virtual environment already exists" -ForegroundColor Green
} else {
    Write-Host "  Creating virtual environment..." -ForegroundColor Gray
    & $pythonCmd -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "  [OK] Virtual environment created" -ForegroundColor Green
}
Write-Host ""

# ============================================
# Step 4: Install Dependencies
# ============================================
Write-Host "[STEP 4/5] Installing dependencies..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes on first run..." -ForegroundColor Gray
Write-Host ""

# Use venv Python directly
$venvPython = ".\.venv\Scripts\python.exe"

# Upgrade pip
Write-Host "  Upgrading pip..." -ForegroundColor Gray
& $venvPython -m pip install --upgrade pip --quiet 2>$null

# Install package
Write-Host "  Installing servicenow-mcp package..." -ForegroundColor Gray
& $venvPython -m pip install -e . --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] Failed to install package" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install additional dependencies
Write-Host "  Installing additional dependencies..." -ForegroundColor Gray
& $venvPython -m pip install bcrypt gunicorn --quiet

Write-Host "  [OK] All dependencies installed" -ForegroundColor Green
Write-Host ""

# ============================================
# Step 5: Verify Installation
# ============================================
Write-Host "[STEP 5/5] Verifying installation..." -ForegroundColor Yellow

$packages = @("servicenow-mcp", "flask", "boto3")
foreach ($pkg in $packages) {
    $result = & $venvPython -m pip show $pkg 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] $pkg installed" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] $pkg not installed" -ForegroundColor Red
    }
}

Write-Host ""

# ============================================
# Complete!
# ============================================
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  To start the application, run:" -ForegroundColor White
Write-Host "    .\start_app.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Or manually:" -ForegroundColor White
Write-Host "    .\.venv\Scripts\python.exe web_ui\app.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "  The app will be available at:" -ForegroundColor White
Write-Host "    http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to exit"
exit 0
