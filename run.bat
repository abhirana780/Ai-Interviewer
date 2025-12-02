@echo off
setlocal
cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
  call venv\Scripts\activate.bat
) else (
  python -m venv venv
  call venv\Scripts\activate.bat
)

pip install -r backend\requirements.txt
python backend\app.py