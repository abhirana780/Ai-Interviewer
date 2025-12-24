#!/usr/bin/env python
import sys
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print("✅ Loaded email configuration from .env file")
    else:
        print("⚠️  No .env file found. Email sending disabled.")
        print("ℹ️  Copy .env.example to .env and configure SMTP settings to enable email.")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

# Change to backend directory so imports work correctly
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
sys.path.insert(0, os.getcwd())

from app import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7860, debug=False, use_reloader=False)
