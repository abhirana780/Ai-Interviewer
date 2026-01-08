@echo off
echo ========================================
echo   AI Interviewer - Local Deployment
echo ========================================
echo.

echo [1/2] Starting Backend Server...
echo.

cd backend
start "AI Interviewer Backend" cmd /k "python app.py"

timeout /t 5 /nobreak > nul

echo [2/2] Starting Frontend Server...
echo.

cd ..\frontend-new
start "AI Interviewer Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   Servers Starting...
echo ========================================
echo.
echo Backend:  http://localhost:7860
echo Frontend: http://localhost:5173
echo.
echo Two new windows will open.
echo Wait for both to finish starting, then open:
echo.
echo   http://localhost:5173
echo.
echo Press any key to exit this window...
pause > nul
