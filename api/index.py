import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the FastAPI app
from server import app

# Export the app instance for Vercel
# Vercel's Python runtime expects the app to be directly accessible
app = app