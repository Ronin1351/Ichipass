"""
RSI filter for Ichimoku scanner.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    delta = close.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def create_rsi_filter(rsi_min: Optional[float] = None, rsi_max: Optional[float] = None):
    """Create RSI filter function."""
    def rsi_filter(symbol: str, data: pd.DataFrame, result: Dict[str, Any]) -> bool:
        """Filter based on RSI values."""
        if rsi_min is None and rsi_max is None:
            return True
        
        try:
            rsi_data = calculate_rsi(data['Close'])
            latest_rsi = rsi_data.iloc[-2]  # Yesterday
            
            if pd.isna(latest_rsi):
                return False
            
            if rsi_min is not None and latest_rsi < rsi_min:
                return False
            
            if rsi_max is not None and latest_rsi > rsi_max:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error calculating RSI for {symbol}: {e}")
            return False
    
    return rsi_filter
