"""
Volume-based filters for the Ichimoku scanner.
"""
import pandas as pd
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def create_volume_filter(min_avg_dollar_volume: float = 0.0):
    """Create a volume filter function."""
    def volume_filter(symbol: str, data: pd.DataFrame, result: Dict[str, Any]) -> bool:
        """Filter based on average dollar volume."""
        if min_avg_dollar_volume <= 0:
            return True
        
        # Use pre-calculated value if available
        if 'avg_dollar_vol_20' in result:
            avg_dollar_vol = result['avg_dollar_vol_20']
        else:
            # Calculate 20-day average dollar volume
            recent_20 = data.tail(20)
            avg_dollar_vol = (recent_20['Close'] * recent_20['Volume']).mean()
        
        return avg_dollar_vol >= min_avg_dollar_volume
    
    return volume_filter

def create_min_price_filter(min_price: float = 0.0):
    """Create a minimum price filter."""
    def min_price_filter(symbol: str, data: pd.DataFrame, result: Dict[str, Any]) -> bool:
        """Filter based on minimum price."""
        if min_price <= 0:
            return True
        
        current_price = result.get('close_y', result.get('price_y', 0))
        return current_price >= min_price
    
    return min_price_filter
