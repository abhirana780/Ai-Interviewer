@echo off
echo ========================================
echo   AI Interviewer - Quick Start
echo ========================================
echo.

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)
echo Python found!

echo.
echo [2/4] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 16+ from https://nodejs.org/
    pause
    exit /b 1
)
echo Node.js found!

echo.
echo [3/4] Setting up Backend...
cd backend

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt --quiet

echo.
echo [4/4] Setting up Frontend...
cd ..\frontend-new

if not exist node_modules (
    echo Installing Node.js dependencies...
    call npm install
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo To start the application:
echo.
echo 1. Backend:  cd backend ^&^& venv\Scripts\activate ^&^& python app.py
echo 2. Frontend: cd frontend-new ^&^& npm run dev
echo.
echo Backend will run on:  http://localhost:7860
echo Frontend will run on: http://localhost:5173
echo.
pause
