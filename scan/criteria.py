"""
Core scanning criteria for Ichimoku cloud breakout detection.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class IchimokuScanner:
    """Scanner for first close above Ichimoku cloud."""
    
    def __init__(
        self,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_period: int = 52,
        lookback_not_above: int = 10,
        min_price: float = 0.0,
        strict_cross: bool = True
    ):
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period  
        self.senkou_period = senkou_period
        self.lookback_not_above = lookback_not_above
        self.min_price = min_price
        self.strict_cross = strict_cross
    
    def has_sufficient_data(self, data: pd.DataFrame) -> bool:
        """Check if we have enough data for Ichimoku calculations."""
        min_bars = self.senkou_period + 26  # 52 + 26 shift
        return len(data) >= min_bars
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Ichimoku indicators and merge with data."""
        from indicators.ichimoku import calculate_ichimoku
        
        ichimoku = calculate_ichimoku(
            data['High'],
            data['Low'], 
            data['Close'],
            self.tenkan_period,
            self.kijun_period,
            self.senkou_period
        )
        
        # Merge with original data
        result = data.join(ichimoku)
        
        # Add effective cloud aligned to price
        # For comparing close[t] with cloud, we use cloud_top[t] (already aligned)
        result['cloud_top_eff'] = result['cloud_top']
        result['cloud_bottom_eff'] = result['cloud_bottom']
        
        return result
    
    def is_first_close_above_cloud(
        self, 
        data: pd.DataFrame,
        lookback_days: Optional[int] = None
    ) -> Tuple[bool, pd.Series]:
        """
        Check if yesterday was first close above cloud in lookback period.
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame with OHLCV and Ichimoku components
        lookback_days : int, optional
            Lookback period to check (defaults to self.lookback_not_above)
        
        Returns:
        --------
        Tuple[bool, pd.Series]
            (is_match, yesterday_data)
        """
        if lookback_days is None:
            lookback_days = self.lookback_not_above
        
        # Ensure we have enough recent data
        if len(data) < lookback_days + 1:
            return False, None
        
        # Get the recent data (yesterday and lookback period)
        recent_data = data.tail(lookback_days + 1).copy()
        
        # Yesterday is the second to last fully closed bar
        yesterday_idx = -2
        yesterday_data = recent_data.iloc[yesterday_idx]
        
        # Check if yesterday's close is above cloud top
        close_yesterday = yesterday_data['Close']
        cloud_top_yesterday = yesterday_data['cloud_top_eff']
        
        # Handle NaN values
        if pd.isna(cloud_top_yesterday) or pd.isna(close_yesterday):
            return False, None
        
        # Check price minimum
        if close_yesterday < self.min_price:
            return False, None
        
        # Strict condition: close must be strictly above cloud top
        if not close_yesterday > cloud_top_yesterday:
            return False, None
        
        # Check previous days to ensure they were NOT above cloud
        prior_data = recent_data.head(lookback_days)
        
        # Check if any prior close was above cloud top
        prior_above = any(
            (prior_data['Close'] > prior_data['cloud_top_eff']).fillna(False)
        )
        
        if prior_above:
            return False, None
        
        # Optional strict cross check
        if self.strict_cross:
            day_before_yesterday = recent_data.iloc[-3]
            close_prev = day_before_yesterday['Close']
            cloud_top_prev = day_before_yesterday['cloud_top_eff']
            
            if pd.isna(close_prev) or pd.isna(cloud_top_prev):
                return False, None
            
            # Require previous close was below or equal to cloud top
            if close_prev > cloud_top_prev:
                return False, None
        
        return True, yesterday_data
    
    def scan_symbol(self, symbol: str, data: pd.DataFrame) -> Optional[dict]:
        """Run full scan on a single symbol."""
        if not self.has_sufficient_data(data):
            logger.debug(f"Insufficient data for {symbol}: {len(data)} bars")
            return None
        
        try:
            # Calculate indicators
            data_with_indicators = self.calculate_indicators(data)
            
            # Check for breakout
            is_match, yesterday_data = self.is_first_close_above_cloud(data_with_indicators)
            
            if not is_match:
                return None
            
            # Calculate additional metrics
            close_y = yesterday_data['Close']
            cloud_top_y = yesterday_data['cloud_top_eff']
            cloud_bot_y = yesterday_data['cloud_bottom_eff']
            
            distance_pct = ((close_y - cloud_top_y) / cloud_top_y) * 100
            
            # Calculate 20-day average dollar volume
            recent_20 = data.tail(20)
            avg_dollar_vol_20 = (recent_20['Close'] * recent_20['Volume']).mean()
            
            result = {
                'symbol': symbol,
                'date_yesterday': yesterday_data.name.strftime('%Y-%m-%d'),
                'close_y': close_y,
                'cloud_top_y': cloud_top_y,
                'cloud_bottom_y': cloud_bot_y,
                'distance_pct': distance_pct,
                'lookback_checked': self.lookback_not_above,
                'avg_dollar_vol_20': avg_dollar_vol_20,
                'price_y': close_y,  # alias
                'tenkan_y': yesterday_data['tenkan'],
                'kijun_y': yesterday_data['kijun']
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            return None
