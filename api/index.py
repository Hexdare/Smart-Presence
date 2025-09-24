import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from server import app

# This is the entry point for Vercel
# Vercel will use this file to serve the FastAPI application