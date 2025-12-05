@echo off
setlocal
cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
  call venv\Scripts\activate.bat
) else (
  python -m venv venv
  call venv\Scripts\activate.bat
)

REM Install requirements only if requirements changed (uncomment if needed)
REM pip install -r backend\requirements.txt
python run.py