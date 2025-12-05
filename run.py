#!/usr/bin/env python
import sys
import os

# Change to backend directory so imports work correctly
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
sys.path.insert(0, os.getcwd())

from app import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7860, debug=False, use_reloader=False)
