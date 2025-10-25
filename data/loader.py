"""
Data loading module for fetching and caching OHLCV data.
Supports yfinance and CSV inputs.
"""
import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import pickle
from typing import Optional, Union, List, Dict
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    """Handles data loading from yfinance or CSV with caching."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cached_path(self, symbol: str) -> Path:
        """Get cache file path for symbol."""
        return self.cache_dir / f"{symbol.replace(':', '_')}.pkl"
    
    def load_from_yfinance(
        self, 
        symbol: str, 
        start: str, 
        end: str,
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """Load OHLCV data from yfinance with caching."""
        cache_file = self.get_cached_path(symbol) if self.cache_dir else None
        
        if use_cache and cache_file and cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                logger.debug(f"Loaded cached data for {symbol}")
                return data
            except Exception as e:
                logger.warning(f"Cache read failed for {symbol}: {e}")
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start, end=end, auto_adjust=True)
            
            if data.empty:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            # Ensure we have proper OHLCV columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_cols):
                logger.warning(f"Missing required columns for {symbol}")
                return None
            
            # Cache the data
            if use_cache and cache_file:
                try:
                    with open(cache_file, 'wb') as f:
                        pickle.dump(data, f)
                    logger.debug(f"Cached data for {symbol}")
                except Exception as e:
                    logger.warning(f"Cache write failed for {symbol}: {e}")
            
            return data
            
        except Exception as e:
            logger.error(f"Error loading {symbol} from yfinance: {e}")
            return None
    
    def load_from_csv(
        self,
        file_path: Path,
        symbol_column: str = 'symbol',
        date_column: str = 'date'
    ) -> Dict[str, pd.DataFrame]:
        """Load OHLCV data from CSV file.
        
        Expected CSV format: symbol, date, open, high, low, close, volume
        """
        try:
            df = pd.read_csv(file_path, parse_dates=[date_column])
            symbols_data = {}
            
            for symbol in df[symbol_column].unique():
                symbol_data = df[df[symbol_column] == symbol].copy()
                symbol_data = symbol_data.set_index(date_column)
                symbol_data = symbol_data.sort_index()
                
                # Ensure proper column names
                symbol_data = symbol_data.rename(columns={
                    'open': 'Open', 'high': 'High', 'low': 'Low', 
                    'close': 'Close', 'volume': 'Volume'
                })
                
                symbols_data[symbol] = symbol_data
            
            return symbols_data
            
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            return {}
