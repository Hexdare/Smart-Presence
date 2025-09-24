import os
import sys
from pathlib import Path

# Add backend directory to Python path  
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set environment variables path
os.environ.setdefault('DOTENV_PATH', str(backend_dir / '.env'))

# Import the FastAPI app from server.py
import_error = None
try:
    from server import app
    
    # Vercel expects the app to be available at module level
    # The app is now properly exported for Vercel serverless functions
    
except ImportError as e:
    import_error = str(e)
    # Fallback FastAPI app in case of import issues
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="Smart Attendance API - Fallback")
    
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "Fallback API - Import Error", "error": import_error}

# Export app for Vercel
__all__ = ["app"]