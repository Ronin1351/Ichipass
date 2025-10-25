"""
FastAPI Web Application for Ichipass Scanner
Provides REST API and serves Neumorphic UI
"""
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import uuid
import shutil

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request
from pydantic import BaseModel
import uvicorn

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.loader import DataLoader
from scan.criteria import IchimokuScanner
from scan.runner import ScanRunner
from filters.volume import create_volume_filter, create_min_price_filter
from filters.macd import create_macd_filter
from filters.rsi import create_rsi_filter
from utils.logging import setup_logging

# Setup logging
setup_logging('INFO')

# Initialize FastAPI
app = FastAPI(
    title="Ichipass Scanner API",
    description="REST API for Ichimoku Cloud Scanner",
    version="1.0.0"
)

# Mount static files and templates (with error handling for serverless)
try:
    static_dir = Path(__file__).parent / "static"
    templates_dir = Path(__file__).parent / "templates"

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
    else:
        templates = None
except Exception as e:
    # In serverless environment, static files may not be available
    print(f"Warning: Could not mount static files: {e}")
    templates = None

# In-memory storage for scan jobs
scan_jobs: Dict[str, Dict[str, Any]] = {}


# Pydantic Models
class ScanConfig(BaseModel):
    tickers: List[str]
    start: str
    end: str
    tenkan: int = 9
    kijun: int = 26
    senkou: int = 52
    lookback: int = 10
    minPrice: float = 0.0
    minVolume: float = 0.0
    strictCross: bool = True
    threads: int = 8
    cacheDir: Optional[str] = None


class ScanResult(BaseModel):
    symbol: str
    date_yesterday: str
    close_y: float
    cloud_top_y: float
    cloud_bottom_y: float
    distance_pct: float
    lookback_checked: int
    avg_dollar_vol_20: float
    price_y: float
    tenkan_y: float
    kijun_y: float


class ScanStatus(BaseModel):
    scan_id: str
    status: str
    progress: int
    results: Optional[List[Dict[str, Any]]] = None
    details: Optional[str] = None
    error: Optional[str] = None


# Routes

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main landing page."""
    if templates is None:
        return JSONResponse({
            "message": "Ichipass Scanner API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "health": "/api/health"
        })
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/scans")
async def create_scan(config: ScanConfig, background_tasks: BackgroundTasks):
    """Create a new scan job."""
    scan_id = str(uuid.uuid4())

    # Initialize scan job
    scan_jobs[scan_id] = {
        'scan_id': scan_id,
        'status': 'initializing',
        'progress': 0,
        'results': None,
        'config': config.dict(),
        'created_at': datetime.now().isoformat(),
        'details': 'Initializing scan...'
    }

    # Run scan in background
    background_tasks.add_task(run_scan, scan_id, config)

    return {
        'scan_id': scan_id,
        'status': 'initializing',
        'message': 'Scan job created successfully'
    }


@app.get("/api/scans/{scan_id}")
async def get_scan_status(scan_id: str):
    """Get status of a scan job."""
    if scan_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="Scan not found")

    return scan_jobs[scan_id]


@app.get("/api/scans")
async def list_scans():
    """List all scan jobs."""
    return {
        'scans': list(scan_jobs.values()),
        'total': len(scan_jobs)
    }


@app.delete("/api/scans/{scan_id}")
async def cancel_scan(scan_id: str):
    """Cancel a running scan."""
    if scan_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan_jobs[scan_id]['status'] = 'cancelled'
    scan_jobs[scan_id]['details'] = 'Scan cancelled by user'

    return {'message': 'Scan cancelled'}


@app.delete("/api/cache")
async def clear_cache():
    """Clear the data cache."""
    try:
        cache_dir = Path('./cache')
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)

        return {'message': 'Cache cleared successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@app.get("/api/cache/size")
async def get_cache_size():
    """Get cache directory size."""
    try:
        cache_dir = Path('./cache')
        if not cache_dir.exists():
            return {'size_mb': 0}

        total_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)

        return {'size_mb': round(size_mb, 2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache size: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get application statistics."""
    completed_scans = [s for s in scan_jobs.values() if s['status'] == 'completed']
    total_matches = sum(len(s.get('results', [])) for s in completed_scans)
    total_symbols = sum(len(s['config']['tickers']) for s in completed_scans)

    return {
        'totalScans': len(completed_scans),
        'matchesFound': total_matches,
        'symbolsTracked': total_symbols,
        'successRate': round((total_matches / max(total_symbols, 1)) * 100, 2)
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }


# Background Tasks

async def run_scan(scan_id: str, config: ScanConfig):
    """Execute scan in background."""
    try:
        # Update status
        scan_jobs[scan_id]['status'] = 'loading_data'
        scan_jobs[scan_id]['details'] = f'Loading data for {len(config.tickers)} symbols...'
        scan_jobs[scan_id]['progress'] = 10

        # Initialize components
        cache_dir = Path(config.cacheDir) if config.cacheDir else None
        data_loader = DataLoader(cache_dir=cache_dir)

        scanner = IchimokuScanner(
            tenkan_period=config.tenkan,
            kijun_period=config.kijun,
            senkou_period=config.senkou,
            lookback_not_above=config.lookback,
            min_price=config.minPrice,
            strict_cross=config.strictCross
        )

        runner = ScanRunner(
            data_loader=data_loader,
            scanner=scanner,
            max_workers=config.threads
        )

        # Register filters
        if config.minVolume > 0:
            runner.register_filter(
                'volume',
                create_volume_filter(config.minVolume)
            )

        if config.minPrice > 0:
            runner.register_filter(
                'min_price',
                create_min_price_filter(config.minPrice)
            )

        # Update status
        scan_jobs[scan_id]['status'] = 'scanning'
        scan_jobs[scan_id]['details'] = 'Scanning for breakouts...'
        scan_jobs[scan_id]['progress'] = 30

        # Run scan
        results = runner.run_scan(
            tickers=config.tickers,
            start=config.start,
            end=config.end,
            source='yfinance',
            dry_run=False
        )

        # Update progress
        scan_jobs[scan_id]['progress'] = 90
        scan_jobs[scan_id]['details'] = f'Processing {len(results)} matches...'

        # Complete
        scan_jobs[scan_id]['status'] = 'completed'
        scan_jobs[scan_id]['progress'] = 100
        scan_jobs[scan_id]['results'] = results
        scan_jobs[scan_id]['details'] = f'Found {len(results)} breakout(s)'
        scan_jobs[scan_id]['completed_at'] = datetime.now().isoformat()

    except Exception as e:
        # Handle errors
        scan_jobs[scan_id]['status'] = 'failed'
        scan_jobs[scan_id]['error'] = str(e)
        scan_jobs[scan_id]['details'] = f'Scan failed: {str(e)}'
        scan_jobs[scan_id]['progress'] = 0


# Main entry point
if __name__ == "__main__":
    print("Starting Ichipass Web Server...")
    print("Access the UI at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
