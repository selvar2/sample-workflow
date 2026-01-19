@echo off
REM ============================================
REM ServiceNow Incident Processor - Local Setup
REM ============================================
REM One-time setup script for Windows
REM Run this after cloning the repository
REM ============================================

echo.
echo ============================================
echo ServiceNow Incident Processor - Local Setup
echo ============================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo [OK] Python found: 
python --version

REM Navigate to script directory
cd /d "%~dp0"
echo [OK] Working directory: %CD%

REM Create virtual environment if not exists
if not exist ".venv" (
    echo.
    echo [SETUP] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo.
echo [SETUP] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install package in editable mode
echo.
echo [SETUP] Installing servicenow-mcp package...
pip install -e . --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install package
    pause
    exit /b 1
)

REM Install additional dependencies
echo.
echo [SETUP] Installing additional dependencies...
pip install bcrypt gunicorn --quiet

REM Check for .env file
echo.
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo.
    echo Please create .env file with your credentials.
    echo You can copy from .env.example:
    echo   copy .env.example .env
    echo.
    echo Then edit .env with your actual credentials:
    echo   - SERVICENOW_INSTANCE_URL
    echo   - SERVICENOW_USERNAME
    echo   - SERVICENOW_PASSWORD
    echo   - AWS_ACCESS_KEY_ID
    echo   - AWS_SECRET_ACCESS_KEY
    echo.
) else (
    echo [OK] .env file found
)

REM Verify installation
echo.
echo [VERIFY] Checking installed packages...
pip show servicenow-mcp >nul 2>&1
if errorlevel 1 (
    echo [ERROR] servicenow-mcp not installed correctly
    pause
    exit /b 1
)
echo [OK] servicenow-mcp installed

pip show flask >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Flask not installed correctly
    pause
    exit /b 1
)
echo [OK] Flask installed

pip show boto3 >nul 2>&1
if errorlevel 1 (
    echo [ERROR] boto3 not installed correctly
    pause
    exit /b 1
)
echo [OK] boto3 installed

echo.
echo ============================================
echo [SUCCESS] Setup complete!
echo ============================================
echo.
echo To start the application, run:
echo   run.bat
echo.
echo Or manually:
echo   .venv\Scripts\activate
echo   python web_ui\run_server.py --debug --port 5000
echo.
pause
