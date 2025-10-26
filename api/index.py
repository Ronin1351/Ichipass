"""
Vercel Serverless Function Entry Point
Re-exports the lightweight FastAPI app from root app.py
"""
import sys
from pathlib import Path

try:
    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    # Import the lightweight FastAPI app from root directory
    # This version doesn't require static files or templates (serverless-friendly)
    from app import app

    # Export for Vercel
    __all__ = ['app']

except Exception as e:
    # If import fails, create a minimal FastAPI app for debugging
    print(f"Error importing app: {e}")
    import traceback
    traceback.print_exc()

    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI()

    @app.get("/")
    @app.get("/api/health")
    async def error_handler():
        return JSONResponse(
            status_code=500,
            content={
                "error": "Application failed to initialize",
                "details": str(e),
                "message": "Please check the server logs"
            }
        )
