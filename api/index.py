"""
Vercel Serverless Function Entry Point
Re-exports the FastAPI app from web/app.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app from web directory
from web.app import app

# Export for Vercel
__all__ = ['app']
