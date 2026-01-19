# ============================================
# ServiceNow MCP - Quick Start (PowerShell)
# ============================================
# Run: .\start_app.ps1
# ============================================

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ServiceNow MCP - Starting Application" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if setup has been done
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run .\setup_environment.ps1 first." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check .env
if (-not (Test-Path ".env")) {
    Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create .env with your credentials." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the application
Write-Host "Starting ServiceNow Incident Processor..." -ForegroundColor Green
Write-Host ""
Write-Host "URL: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

try {
    & .\.venv\Scripts\python.exe web_ui\app.py
} catch {
    Write-Host ""
    Write-Host "Application stopped." -ForegroundColor Yellow
}

Read-Host "Press Enter to exit"
