"""
MACD filter for Ichimoku scanner.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def calculate_macd(
    close: pd.Series, 
    fast_period: int = 12, 
    slow_period: int = 26, 
    signal_period: int = 9
) -> pd.DataFrame:
    """Calculate MACD indicator."""
    ema_fast = close.ewm(span=fast_period).mean()
    ema_slow = close.ewm(span=slow_period).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period).mean()
    histogram = macd_line - signal_line
    
    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }, index=close.index)

def create_macd_filter(histogram_positive: bool = True):
    """Create MACD filter function."""
    def macd_filter(symbol: str, data: pd.DataFrame, result: Dict[str, Any]) -> bool:
        """Filter based on MACD histogram."""
        if not histogram_positive:
            return True
        
        try:
            macd_data = calculate_macd(data['Close'])
            latest_histogram = macd_data['histogram'].iloc[-2]  # Yesterday
            
            if pd.isna(latest_histogram):
                return False
            
            return latest_histogram > 0
            
        except Exception as e:
            logger.error(f"Error calculating MACD for {symbol}: {e}")
            return False
    
    return macd_filter
