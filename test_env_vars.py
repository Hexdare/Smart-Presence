#!/usr/bin/env python3
"""
Test script to verify environment variables are properly loaded
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
env_file = ROOT_DIR / '.env'

print(f"Looking for .env file at: {env_file}")
print(f".env file exists: {env_file.exists()}")

if env_file.exists():
    with open(env_file, 'r') as f:
        print(f".env file contents:\n{f.read()}")

load_dotenv(env_file)

# Check environment variables
print("\nEnvironment Variables:")
print(f"SYSTEM_ADMIN_USERNAME: {os.environ.get('SYSTEM_ADMIN_USERNAME')}")
print(f"SYSTEM_ADMIN_PASSWORD: {os.environ.get('SYSTEM_ADMIN_PASSWORD')}")
print(f"SYSTEM_ADMIN_FULL_NAME: {os.environ.get('SYSTEM_ADMIN_FULL_NAME')}")

# Test the login logic
username = "admin"
password = "admin123"

system_admin_username = os.environ.get("SYSTEM_ADMIN_USERNAME")
system_admin_password = os.environ.get("SYSTEM_ADMIN_PASSWORD")

print(f"\nLogin Test:")
print(f"Input username: {username}")
print(f"Input password: {password}")
print(f"Env username: {system_admin_username}")
print(f"Env password: {system_admin_password}")
print(f"Username match: {system_admin_username == username}")
print(f"Password match: {system_admin_password == password}")
print(f"Both match: {system_admin_username == username and system_admin_password == password}")