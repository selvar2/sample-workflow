# ============================================
# ServiceNow Incident Processor - Run Script
# ============================================
# One-click app starter for Windows (PowerShell)
# Auto-installs dependencies if missing
# ============================================

$ErrorActionPreference = "Stop"

# Navigate to script directory
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "ServiceNow Incident Processor" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.11+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check/Create virtual environment
$needsInstall = $false

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "[SETUP] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    $needsInstall = $true
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[SETUP] Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Check if servicenow-mcp is installed
$installed = pip show servicenow-mcp 2>&1
if ($LASTEXITCODE -ne 0) {
    $needsInstall = $true
}

# Install dependencies if needed
if ($needsInstall) {
    Write-Host ""
    Write-Host "[SETUP] Installing dependencies (first-time setup)..." -ForegroundColor Yellow
    python -m pip install --upgrade pip --quiet
    pip install -e . --quiet
    pip install bcrypt gunicorn --quiet
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[OK] Dependencies already installed" -ForegroundColor Green
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "[WARNING] .env file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create .env with your credentials:" -ForegroundColor Yellow
    Write-Host "  1. Copy .env.example to .env" -ForegroundColor White
    Write-Host "  2. Edit .env with your actual credentials" -ForegroundColor White
    Write-Host ""
    Write-Host "See docs\LOCAL_DEPLOYMENT_GUIDE.md for details." -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] .env file found" -ForegroundColor Green

# Start the application
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Starting ServiceNow Incident Processor..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URL: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python web_ui\run_server.py --debug --port 5000
