@echo off
REM ============================================
REM ServiceNow MCP - Requirements Checker
REM ============================================
REM Run this script to verify your system is ready
REM ============================================

setlocal EnableDelayedExpansion

echo.
echo ============================================
echo   ServiceNow MCP - Requirements Checker
echo ============================================
echo.

set "ERRORS=0"
set "WARNINGS=0"

REM ============================================
REM Check 1: Python Installation
REM ============================================
echo [CHECK] Python installation...

REM Try 'py' launcher first (recommended for Windows)
py --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=2" %%v in ('py --version 2^>^&1') do set "PY_VERSION=%%v"
    echo   [OK] Python found via 'py' launcher: !PY_VERSION!
    set "PYTHON_CMD=py"
    goto :python_ok
)

REM Try 'python' command
python --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VERSION=%%v"
    echo   [OK] Python found: !PY_VERSION!
    set "PYTHON_CMD=python"
    goto :python_ok
)

echo   [ERROR] Python is NOT installed!
echo.
echo   Please install Python 3.11 or higher from:
echo   https://www.python.org/downloads/
echo.
echo   During installation, check "Add Python to PATH"
echo.
set /a ERRORS+=1
goto :check_env

:python_ok

REM ============================================
REM Check 2: Python Version (3.11+)
REM ============================================
echo [CHECK] Python version...
for /f "tokens=1,2 delims=." %%a in ("!PY_VERSION!") do (
    set "MAJOR=%%a"
    set "MINOR=%%b"
)
if !MAJOR! geq 3 if !MINOR! geq 11 (
    echo   [OK] Python !PY_VERSION! meets minimum requirement ^(3.11+^)
) else (
    echo   [WARNING] Python !PY_VERSION! detected. Recommended: 3.11+
    set /a WARNINGS+=1
)

:check_env
REM ============================================
REM Check 3: .env File
REM ============================================
echo [CHECK] Environment configuration...

cd /d "%~dp0"

if exist ".env" (
    echo   [OK] .env file found
    
    REM Check for required variables
    findstr /C:"AWS_ACCESS_KEY_ID" .env >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] AWS_ACCESS_KEY_ID configured
    ) else (
        echo   [ERROR] AWS_ACCESS_KEY_ID not found in .env
        set /a ERRORS+=1
    )
    
    findstr /C:"AWS_SECRET_ACCESS_KEY" .env >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] AWS_SECRET_ACCESS_KEY configured
    ) else (
        echo   [ERROR] AWS_SECRET_ACCESS_KEY not found in .env
        set /a ERRORS+=1
    )
    
    findstr /C:"SERVICENOW_INSTANCE_URL" .env >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] SERVICENOW_INSTANCE_URL configured
    ) else (
        echo   [ERROR] SERVICENOW_INSTANCE_URL not found in .env
        set /a ERRORS+=1
    )
    
    findstr /C:"SERVICENOW_USERNAME" .env >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] SERVICENOW_USERNAME configured
    ) else (
        echo   [ERROR] SERVICENOW_USERNAME not found in .env
        set /a ERRORS+=1
    )
    
    findstr /C:"SERVICENOW_PASSWORD" .env >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] SERVICENOW_PASSWORD configured
    ) else (
        echo   [ERROR] SERVICENOW_PASSWORD not found in .env
        set /a ERRORS+=1
    )
    
    REM Check for problematic AWS_PROFILE setting
    findstr /C:"AWS_PROFILE=" .env >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [WARNING] AWS_PROFILE is set in .env - this may cause issues
        echo            Consider removing it if you're using explicit credentials
        set /a WARNINGS+=1
    )
) else (
    echo   [ERROR] .env file NOT found!
    echo.
    echo   Please create .env file with your credentials.
    echo   Copy from .env.example:
    echo     copy .env.example .env
    echo.
    set /a ERRORS+=1
)

REM ============================================
REM Check 4: Virtual Environment
REM ============================================
echo [CHECK] Virtual environment...
if exist ".venv\Scripts\python.exe" (
    echo   [OK] Virtual environment exists
) else (
    echo   [INFO] Virtual environment not found - will be created during setup
)

REM ============================================
REM Check 5: AWS CLI (Optional)
REM ============================================
echo [CHECK] AWS CLI ^(optional^)...
aws --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=1,2" %%a in ('aws --version 2^>^&1') do set "AWS_VERSION=%%a"
    echo   [OK] AWS CLI installed: !AWS_VERSION! ^(optional - not required^)
) else (
    echo   [INFO] AWS CLI not installed ^(not required - using boto3 with explicit credentials^)
)

REM ============================================
REM Summary
REM ============================================
echo.
echo ============================================
echo   Summary
echo ============================================
if !ERRORS! equ 0 (
    if !WARNINGS! equ 0 (
        echo   [SUCCESS] All checks passed!
        echo   You can run setup_environment.bat to install dependencies.
    ) else (
        echo   [OK] Ready to proceed with !WARNINGS! warning^(s^)
        echo   You can run setup_environment.bat to install dependencies.
    )
) else (
    echo   [FAILED] !ERRORS! error^(s^) found. Please fix them before continuing.
)
echo ============================================
echo.

if !ERRORS! gtr 0 (
    pause
    exit /b 1
)

pause
exit /b 0
