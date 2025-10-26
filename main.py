# main.py  (FastAPI entrypoint for Vercel)
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, validator
from fastapi import FastAPI, HTTPException

# import your existing modules
from data.loader import DataLoader
from scan.criteria import IchimokuScanner
from scan.runner import ScanRunner
from filters.volume import create_volume_filter, create_min_price_filter
# optional filters you might add later
# from filters.macd import create_macd_filter
# from filters.rsi import create_rsi_filter
from utils.logging import setup_logging

app = FastAPI(title="Ichimoku Cloud Scanner API")

class ScanRequest(BaseModel):
    tickers: List[str]
    start: str = Field(..., description="YYYY-MM-DD")
    end: str = Field("today", description='YYYY-MM-DD or "today"')
    ichi_tenkan: int = 9
    ichi_kijun: int = 26
    ichi_senkou: int = 52
    lookback_not_above: int = 10
    min_price: float = 0.0
    min_avg_dollar_volume: float = 0.0
    strict_cross: bool = True
    threads: int = 4
    source: str = "yfinance"
    log_level: str = "INFO"
    cache_dir: Optional[str] = None

    @validator("tickers")
    def _dedupe(cls, v):
        s = sorted(set([t.strip().upper() for t in v if t.strip()]))
        if not s:
            raise ValueError("tickers cannot be empty")
        return s

class ScanResponse(BaseModel):
    scan_date: str
    results_count: int
    results: list

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

@app.post("/scan", response_model=ScanResponse)
def scan(req: ScanRequest):
    try:
        setup_logging(req.log_level)
        data_loader = DataLoader(cache_dir=Path(req.cache_dir) if req.cache_dir else None)

        scanner = IchimokuScanner(
            tenkan_period=req.ichi_tenkan,
            kijun_period=req.ichi_kijun,
            senkou_period=req.ichi_senkou,
            lookback_not_above=req.lookback_not_above,
            min_price=req.min_price,
            strict_cross=req.strict_cross,
        )

        runner = ScanRunner(
            data_loader=data_loader,
            scanner=scanner,
            max_workers=max(1, min(req.threads, 8)),  # be kind to serverless
        )

        if req.min_avg_dollar_volume > 0:
            runner.register_filter("volume", create_volume_filter(req.min_avg_dollar_volume))
        if req.min_price > 0:
            runner.register_filter("min_price", create_min_price_filter(req.min_price))

        results = runner.run_scan(
            tickers=req.tickers,
            start=req.start,
            end=req.end,
            source=req.source,
            dry_run=False,
        )

        return ScanResponse(
            scan_date=datetime.utcnow().isoformat(),
            results_count=len(results),
            results=results,
        )
    except Exception as e:
        # Make sure the error shows up in Vercel logs
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))
