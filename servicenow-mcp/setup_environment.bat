@echo off
REM ============================================
REM ServiceNow MCP - One-Click Setup
REM ============================================
REM This script sets up everything you need
REM Just run it after cloning the repository
REM ============================================

setlocal EnableDelayedExpansion

echo.
echo ============================================
echo   ServiceNow MCP - Environment Setup
echo ============================================
echo.

REM Navigate to script directory
cd /d "%~dp0"
echo [INFO] Working directory: %CD%
echo.

REM ============================================
REM Step 1: Find Python
REM ============================================
echo [STEP 1/5] Detecting Python...

set "PYTHON_CMD="

REM Try 'py' launcher first
py --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=py"
    for /f "tokens=2" %%v in ('py --version 2^>^&1') do echo   Found Python %%v via 'py' launcher
    goto :python_found
)

REM Try 'python' command
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python"
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   Found Python %%v
    goto :python_found
)

echo   [ERROR] Python not found!
echo.
echo   Please install Python 3.11+ from https://python.org
echo   Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:python_found
echo   [OK] Using: !PYTHON_CMD!
echo.

REM ============================================
REM Step 2: Check .env file
REM ============================================
echo [STEP 2/5] Checking configuration...

if not exist ".env" (
    if exist ".env.example" (
        echo   [INFO] .env not found, copying from .env.example...
        copy .env.example .env >nul
        echo   [WARNING] Please edit .env with your actual credentials!
        echo.
        echo   Required settings:
        echo   - AWS_ACCESS_KEY_ID
        echo   - AWS_SECRET_ACCESS_KEY
        echo   - SERVICENOW_INSTANCE_URL
        echo   - SERVICENOW_USERNAME
        echo   - SERVICENOW_PASSWORD
        echo.
        pause
    ) else (
        echo   [ERROR] No .env or .env.example found!
        echo   Please create .env file with your credentials.
        pause
        exit /b 1
    )
) else (
    echo   [OK] .env file found
)
echo.

REM ============================================
REM Step 3: Create Virtual Environment
REM ============================================
echo [STEP 3/5] Setting up virtual environment...

if exist ".venv\Scripts\python.exe" (
    echo   [OK] Virtual environment already exists
) else (
    echo   Creating virtual environment...
    !PYTHON_CMD! -m venv .venv
    if !errorlevel! neq 0 (
        echo   [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo   [OK] Virtual environment created
)
echo.

REM ============================================
REM Step 4: Activate and Install Dependencies
REM ============================================
echo [STEP 4/5] Installing dependencies...
echo   This may take a few minutes on first run...
echo.

REM Activate venv and install
call .venv\Scripts\activate.bat

REM Upgrade pip
echo   Upgrading pip...
python -m pip install --upgrade pip --quiet
if !errorlevel! neq 0 (
    echo   [WARNING] pip upgrade failed, continuing anyway...
)

REM Install package in editable mode
echo   Installing servicenow-mcp package...
pip install -e . --quiet
if !errorlevel! neq 0 (
    echo   [ERROR] Failed to install package
    pause
    exit /b 1
)

REM Install additional dependencies
echo   Installing additional dependencies...
pip install bcrypt gunicorn --quiet

echo   [OK] All dependencies installed
echo.

REM ============================================
REM Step 5: Verify Installation
REM ============================================
echo [STEP 5/5] Verifying installation...

pip show servicenow-mcp >nul 2>&1
if !errorlevel! neq 0 (
    echo   [ERROR] servicenow-mcp not installed correctly
    pause
    exit /b 1
)
echo   [OK] servicenow-mcp package installed

pip show flask >nul 2>&1
if !errorlevel! neq 0 (
    echo   [ERROR] Flask not installed
    pause
    exit /b 1
)
echo   [OK] Flask installed

pip show boto3 >nul 2>&1
if !errorlevel! neq 0 (
    echo   [ERROR] boto3 not installed
    pause
    exit /b 1
)
echo   [OK] boto3 installed

echo.

REM ============================================
REM Complete!
REM ============================================
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo   To start the application, run:
echo     start_app.bat
echo.
echo   Or manually:
echo     .venv\Scripts\python.exe web_ui\app.py
echo.
echo   The app will be available at:
echo     http://localhost:5000
echo.
echo ============================================
echo.

pause
exit /b 0
