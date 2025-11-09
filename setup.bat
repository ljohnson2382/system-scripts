@echo off
:: Quick setup script for Windows systems
:: Author: Loyd Johnson
:: Date: November 2025

setlocal enabledelayedexpansion

echo ==================================================
echo   System Scripts Toolkit - Quick Setup (Windows)
echo   Author: Loyd Johnson
echo ==================================================
echo.

:: Check Python version
echo 🔍 Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.6+ from python.org and try again
    pause
    exit /b 1
)

python --version

:: Create virtual environment
echo.
echo 🔄 Creating virtual environment...
if exist venv (
    echo ✅ Virtual environment already exists
) else (
    python -m venv venv
    if %errorlevel% equ 0 (
        echo ✅ Virtual environment created
    ) else (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo.
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo.
echo 🔄 Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
echo.
echo 🔄 Installing dependencies...
if "%1"=="--dev" (
    echo Installing development dependencies...
    pip install -r requirements-dev.txt
) else if "%1"=="-d" (
    echo Installing development dependencies...
    pip install -r requirements-dev.txt
) else (
    echo Installing production dependencies...
    pip install -r requirements.txt
)

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

:: Test installation
echo.
echo 🧪 Testing installation...
python auto_update.py --check-prereq

echo.
echo 🎉 Setup complete!
echo.
echo To activate the virtual environment:
echo   venv\Scripts\activate.bat
echo.
echo To test the tools:
echo   python auto_update.py --check-prereq
echo   python scripts\helpdesk\system_info.py
echo   python scripts\helpdesk\network_diagnostics.py
echo.
echo Windows-specific tools:
echo   scripts\windows\windows_maintenance.bat
echo   powershell -ExecutionPolicy Bypass -File scripts\windows\windows_powershell_utils.ps1
echo.
echo To deactivate when done:
echo   deactivate
echo.
pause