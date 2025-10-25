"""
Scan runner for processing multiple tickers in parallel.
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from data.loader import DataLoader
from scan.criteria import IchimokuScanner
from filters.volume import VolumeFilter
from filters.macd import MACDFilter
from filters.rsi import RSIFilter

logger = logging.getLogger(__name__)

class ScanRunner:
    """Runs Ichimoku scan across multiple symbols."""
    
    def __init__(
        self,
        data_loader: DataLoader,
        scanner: IchimokuScanner,
        max_workers: int = 8
    ):
        self.data_loader = data_loader
        self.scanner = scanner
        self.max_workers = max_workers
        
        # Initialize filters registry
        self.filters = {}
    
    def register_filter(self, name: str, filter_func, enabled: bool = True):
        """Register a filter function."""
        self.filters[name] = {
            'function': filter_func,
            'enabled': enabled
        }
    
    def load_tickers_data(
        self, 
        tickers: List[str], 
        start: str, 
        end: str,
        source: str = 'yfinance'
    ) -> Dict[str, pd.DataFrame]:
        """Load data for all tickers."""
        tickers_data = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {}
            
            for ticker in tickers:
                if source == 'yfinance':
                    future = executor.submit(
                        self.data_loader.load_from_yfinance,
                        ticker, start, end
                    )
                    future_to_ticker[future] = ticker
                else:
                    raise ValueError(f"Unsupported data source: {source}")
            
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    if data is not None and not data.empty:
                        tickers_data[ticker] = data
                        logger.debug(f"Loaded data for {ticker}: {len(data)} bars")
                    else:
                        logger.debug(f"No data for {ticker}")
                except Exception as e:
                    logger.error(f"Error loading {ticker}: {e}")
        
        return tickers_data
    
    def run_scan(
        self,
        tickers: List[str],
        start: str,
        end: str,
        source: str = 'yfinance',
        dry_run: bool = False
    ) -> List[Dict[str, Any]]:
        """Run the scan across all tickers."""
        if dry_run:
            logger.info(f"DRY RUN: Would scan {len(tickers)} tickers")
            return []
        
        logger.info(f"Loading data for {len(tickers)} tickers...")
        tickers_data = self.load_tickers_data(tickers, start, end, source)
        logger.info(f"Successfully loaded data for {len(tickers_data)} tickers")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.scanner.scan_symbol, symbol, data): symbol
                for symbol, data in tickers_data.items()
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result is not None:
                        # Apply additional filters
                        if self.apply_filters(symbol, tickers_data[symbol], result):
                            results.append(result)
                            logger.info(f"MATCH: {symbol}")
                            
                except Exception as e:
                    logger.error(f"Error scanning {symbol}: {e}")
        
        logger.info(f"Scan complete: {len(results)} matches found")
        return results
    
    def apply_filters(
        self, 
        symbol: str, 
        data: pd.DataFrame, 
        result: Dict[str, Any]
    ) -> bool:
        """Apply registered filters to scan result."""
        for filter_name, filter_config in self.filters.items():
            if not filter_config['enabled']:
                continue
                
            try:
                filter_func = filter_config['function']
                if not filter_func(symbol, data, result):
                    logger.debug(f"Filtered out {symbol} by {filter_name}")
                    return False
            except Exception as e:
                logger.error(f"Error applying filter {filter_name} to {symbol}: {e}")
                return False
        
        return True
