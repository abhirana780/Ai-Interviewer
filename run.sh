#!/bin/bash
set -e
cd backend
if [ -f "venv/bin/activate" ]; then
source venv/bin/activate
else
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
fi
python app.py