@echo off
REM ============================================
REM ServiceNow Incident Processor - Run Script
REM ============================================
REM One-click app starter for Windows
REM Auto-installs dependencies if missing
REM ============================================

setlocal EnableDelayedExpansion

REM Navigate to script directory
cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Check/Create virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo [SETUP] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    set "NEEDS_INSTALL=1"
) else (
    set "NEEDS_INSTALL=0"
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if servicenow-mcp is installed
pip show servicenow-mcp >nul 2>&1
if errorlevel 1 (
    set "NEEDS_INSTALL=1"
)

REM Install dependencies if needed
if "!NEEDS_INSTALL!"=="1" (
    echo [SETUP] Installing dependencies (first-time setup)...
    python -m pip install --upgrade pip --quiet
    pip install -e . --quiet
    pip install bcrypt gunicorn --quiet
    echo [OK] Dependencies installed
)

REM Check for .env file
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found!
    echo Please create .env with your credentials.
    echo See docs\LOCAL_DEPLOYMENT_GUIDE.md for details.
    echo.
    pause
    exit /b 1
)

REM Start the application
echo.
echo ============================================
echo Starting ServiceNow Incident Processor...
echo ============================================
echo.
echo URL: http://127.0.0.1:5000
echo Press Ctrl+C to stop
echo.

python web_ui\run_server.py --debug --port 5000
