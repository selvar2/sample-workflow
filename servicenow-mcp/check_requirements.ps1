# ============================================
# ServiceNow MCP - Requirements Checker (PowerShell)
# ============================================
# Run: .\check_requirements.ps1
# ============================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ServiceNow MCP - Requirements Checker" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0
$warnings = 0

# Navigate to script directory
Set-Location $PSScriptRoot

# ============================================
# Check 1: Python Installation
# ============================================
Write-Host "[CHECK] Python installation..." -ForegroundColor Yellow

$pythonCmd = $null
$pyVersion = $null

# Try 'py' launcher first
try {
    $pyVersion = (py --version 2>&1) -replace "Python ", ""
    $pythonCmd = "py"
    Write-Host "  [OK] Python found via 'py' launcher: $pyVersion" -ForegroundColor Green
} catch {
    # Try 'python' command
    try {
        $pyVersion = (python --version 2>&1) -replace "Python ", ""
        $pythonCmd = "python"
        Write-Host "  [OK] Python found: $pyVersion" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Python is NOT installed!" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Please install Python 3.11 or higher from:" -ForegroundColor White
        Write-Host "  https://www.python.org/downloads/" -ForegroundColor White
        Write-Host ""
        $errors++
    }
}

# ============================================
# Check 2: Python Version
# ============================================
if ($pyVersion) {
    Write-Host "[CHECK] Python version..." -ForegroundColor Yellow
    $versionParts = $pyVersion.Split(".")
    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    
    if ($major -ge 3 -and $minor -ge 11) {
        Write-Host "  [OK] Python $pyVersion meets minimum requirement (3.11+)" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Python $pyVersion detected. Recommended: 3.11+" -ForegroundColor Yellow
        $warnings++
    }
}

# ============================================
# Check 3: .env File
# ============================================
Write-Host "[CHECK] Environment configuration..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "  [OK] .env file found" -ForegroundColor Green
    
    $envContent = Get-Content ".env" -Raw
    
    $requiredVars = @(
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY", 
        "SERVICENOW_INSTANCE_URL",
        "SERVICENOW_USERNAME",
        "SERVICENOW_PASSWORD"
    )
    
    foreach ($var in $requiredVars) {
        if ($envContent -match $var) {
            Write-Host "  [OK] $var configured" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] $var not found in .env" -ForegroundColor Red
            $errors++
        }
    }
    
    # Check for problematic AWS_PROFILE
    if ($envContent -match "AWS_PROFILE=") {
        Write-Host "  [WARNING] AWS_PROFILE is set in .env - consider removing it" -ForegroundColor Yellow
        $warnings++
    }
} else {
    Write-Host "  [ERROR] .env file NOT found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please create .env file. Copy from .env.example:" -ForegroundColor White
    Write-Host "    Copy-Item .env.example .env" -ForegroundColor White
    Write-Host ""
    $errors++
}

# ============================================
# Check 4: Virtual Environment
# ============================================
Write-Host "[CHECK] Virtual environment..." -ForegroundColor Yellow

if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "  [OK] Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "  [INFO] Virtual environment not found - will be created during setup" -ForegroundColor Cyan
}

# ============================================
# Check 5: AWS CLI (Optional)
# ============================================
Write-Host "[CHECK] AWS CLI (optional)..." -ForegroundColor Yellow

try {
    $awsVersion = aws --version 2>&1
    Write-Host "  [OK] AWS CLI installed: $awsVersion (optional - not required)" -ForegroundColor Green
} catch {
    Write-Host "  [INFO] AWS CLI not installed (not required - using boto3)" -ForegroundColor Cyan
}

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if ($errors -eq 0) {
    if ($warnings -eq 0) {
        Write-Host "  [SUCCESS] All checks passed!" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Ready to proceed with $warnings warning(s)" -ForegroundColor Yellow
    }
    Write-Host "  Run .\setup_environment.ps1 to install dependencies." -ForegroundColor White
} else {
    Write-Host "  [FAILED] $errors error(s) found. Please fix them." -ForegroundColor Red
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

if ($errors -gt 0) {
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to continue"
exit 0
