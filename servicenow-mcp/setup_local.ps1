# ============================================
# ServiceNow Incident Processor - Local Setup
# ============================================
# One-time setup script for Windows (PowerShell)
# Run this after cloning the repository
# ============================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "ServiceNow Incident Processor - Local Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to script directory
Set-Location $PSScriptRoot
Write-Host "[OK] Working directory: $PWD" -ForegroundColor Green

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment if not exists
if (-not (Test-Path ".venv")) {
    Write-Host ""
    Write-Host "[SETUP] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "[SETUP] Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host ""
Write-Host "[SETUP] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install package in editable mode
Write-Host ""
Write-Host "[SETUP] Installing servicenow-mcp package..." -ForegroundColor Yellow
pip install -e . --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install package" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Package installed" -ForegroundColor Green

# Install additional dependencies
Write-Host ""
Write-Host "[SETUP] Installing additional dependencies..." -ForegroundColor Yellow
pip install bcrypt gunicorn --quiet
Write-Host "[OK] Additional dependencies installed" -ForegroundColor Green

# Check for .env file
Write-Host ""
if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please create .env file with your credentials:" -ForegroundColor White
    Write-Host "  1. Copy .env.example to .env:" -ForegroundColor White
    Write-Host "     Copy-Item .env.example .env" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Edit .env with your actual credentials:" -ForegroundColor White
    Write-Host "     - SERVICENOW_INSTANCE_URL" -ForegroundColor Gray
    Write-Host "     - SERVICENOW_USERNAME" -ForegroundColor Gray
    Write-Host "     - SERVICENOW_PASSWORD" -ForegroundColor Gray
    Write-Host "     - AWS_ACCESS_KEY_ID" -ForegroundColor Gray
    Write-Host "     - AWS_SECRET_ACCESS_KEY" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "[OK] .env file found" -ForegroundColor Green
}

# Verify installation
Write-Host ""
Write-Host "[VERIFY] Checking installed packages..." -ForegroundColor Yellow

$packages = @("servicenow-mcp", "flask", "boto3", "bcrypt")
foreach ($pkg in $packages) {
    $result = pip show $pkg 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] $pkg installed" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] $pkg not installed" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "[SUCCESS] Setup complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application, run:" -ForegroundColor White
Write-Host "  .\run.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use the batch file:" -ForegroundColor White
Write-Host "  run.bat" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
