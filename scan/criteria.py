"""
Core scanning criteria for Ichimoku cloud breakout detection.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_ichimoku(high, low, close, tenkan_period=9, kijun_period=26, senkou_period=52):
    """Calculate Ichimoku Cloud components."""
    # Tenkan-sen (Conversion Line)
    tenkan_sen = (high.rolling(window=tenkan_period).max() + low.rolling(window=tenkan_period).min()) / 2
    
    # Kijun-sen (Base Line)
    kijun_sen = (high.rolling(window=kijun_period).max() + low.rolling(window=kijun_period).min()) / 2
    
    # Senkou Span A (Leading Span A)
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
    
    # Senkou Span B (Leading Span B)
    senkou_span_b = ((high.rolling(window=senkou_period).max() + low.rolling(window=senkou_period).min()) / 2).shift(kijun_period)
    
    # Chikou Span (Lagging Span)
    chikou_span = close.shift(-kijun_period)
    
    return pd.DataFrame({
        'tenkan': tenkan_sen,
        'kijun': kijun_sen,
        'senkou_a': senkou_span_a,
        'senkou_b': senkou_span_b,
        'chikou': chikou_span,
        'cloud_top': pd.concat([senkou_span_a, senkou_span_b], axis=1).max(axis=1),
        'cloud_bottom': pd.concat([senkou_span_a, senkou_span_b], axis=1).min(axis=1)
    })

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
        result['cloud_top_eff'] = result['cloud_top']
        result['cloud_bottom_eff'] = result['cloud_bottom']
        
        return result
    
    # ... rest of your existing methods remain the same
    def is_first_close_above_cloud(
        self, 
        data: pd.DataFrame,
        lookback_days: Optional[int] = None
    ) -> Tuple[bool, pd.Series]:
        if lookback_days is None:
            lookback_days = self.lookback_not_above
        
        if len(data) < lookback_days + 1:
            return False, None
        
        recent_data = data.tail(lookback_days + 1).copy()
        yesterday_idx = -2
        yesterday_data = recent_data.iloc[yesterday_idx]
        
        close_yesterday = yesterday_data['Close']
        cloud_top_yesterday = yesterday_data['cloud_top_eff']
        
        if pd.isna(cloud_top_yesterday) or pd.isna(close_yesterday):
            return False, None
        
        if close_yesterday < self.min_price:
            return False, None
        
        if not close_yesterday > cloud_top_yesterday:
            return False, None
        
        prior_data = recent_data.head(lookback_days)
        prior_above = any(
            (prior_data['Close'] > prior_data['cloud_top_eff']).fillna(False)
        )
        
        if prior_above:
            return False, None
        
        if self.strict_cross:
            day_before_yesterday = recent_data.iloc[-3]
            close_prev = day_before_yesterday['Close']
            cloud_top_prev = day_before_yesterday['cloud_top_eff']
            
            if pd.isna(close_prev) or pd.isna(cloud_top_prev):
                return False, None
            
            if close_prev > cloud_top_prev:
                return False, None
        
        return True, yesterday_data
    
    def scan_symbol(self, symbol: str, data: pd.DataFrame) -> Optional[dict]:
        if not self.has_sufficient_data(data):
            logger.debug(f"Insufficient data for {symbol}: {len(data)} bars")
            return None
        
        try:
            data_with_indicators = self.calculate_indicators(data)
            is_match, yesterday_data = self.is_first_close_above_cloud(data_with_indicators)
            
            if not is_match:
                return None
            
            close_y = yesterday_data['Close']
            cloud_top_y = yesterday_data['cloud_top_eff']
            cloud_bot_y = yesterday_data['cloud_bottom_eff']
            
            distance_pct = ((close_y - cloud_top_y) / cloud_top_y) * 100
            
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
                'price_y': close_y,
                'tenkan_y': yesterday_data['tenkan'],
                'kijun_y': yesterday_data['kijun']
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            return None
