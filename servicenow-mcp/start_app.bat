@echo off
REM ============================================
REM ServiceNow MCP - Quick Start
REM ============================================
REM One-click application launcher
REM ============================================

setlocal EnableDelayedExpansion

cd /d "%~dp0"

echo.
echo ============================================
echo   ServiceNow MCP - Starting Application
echo ============================================
echo.

REM Check if setup has been done
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run setup_environment.bat first.
    echo.
    pause
    exit /b 1
)

REM Check .env
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env with your credentials.
    echo.
    pause
    exit /b 1
)

REM Start the application
echo Starting ServiceNow Incident Processor...
echo.
echo URL: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
echo ============================================
echo.

.venv\Scripts\python.exe web_ui\app.py

REM If we get here, the app exited
echo.
echo Application stopped.
pause
