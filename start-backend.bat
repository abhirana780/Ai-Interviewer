@echo off
title AI Interviewer - Backend Server

echo ========================================
echo   Starting Backend Server
echo ========================================
echo.

cd backend

if not exist venv (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Flask server on http://localhost:7860
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py
