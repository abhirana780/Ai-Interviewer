@echo off
title AI Interviewer - Frontend Dev Server

echo ========================================
echo   Starting Frontend Dev Server
echo ========================================
echo.

cd frontend-new

if not exist node_modules (
    echo ERROR: Node modules not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

echo Starting Vite dev server on http://localhost:5173
echo.
echo Press Ctrl+C to stop the server
echo.

call npm run dev
