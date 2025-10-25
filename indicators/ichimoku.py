"""
Ichimoku Cloud indicator calculations with proper alignment.
"""
import pandas as pd
import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

def calculate_ichimoku(
    high: pd.Series, 
    low: pd.Series, 
    close: pd.Series,
    tenkan_period: int = 9,
    kijun_period: int = 26, 
    senkou_period: int = 52,
    senkou_shift: int = 26
) -> pd.DataFrame:
    """
    Calculate Ichimoku Cloud components with proper alignment.
    
    Parameters:
    -----------
    high : pd.Series
        High prices
    low : pd.Series  
        Low prices
    close : pd.Series
        Close prices
    tenkan_period : int
        Conversion line period (default 9)
    kijun_period : int
        Base line period (default 26)
    senkou_period : int
        Leading span period (default 52)
    senkou_shift : int
        Leading span shift (default 26)
    
    Returns:
    --------
    pd.DataFrame with columns:
        tenkan, kijun, senkou_a, senkou_b, cloud_top, cloud_bottom
    """
    # Calculate components
    tenkan = (high.rolling(window=tenkan_period).max() + 
              low.rolling(window=tenkan_period).min()) / 2
    
    kijun = (high.rolling(window=kijun_period).max() + 
             low.rolling(window=kijun_period).min()) / 2
    
    # Senkou Span A: (Tenkan + Kijun) / 2, shifted forward
    senkou_a = ((tenkan + kijun) / 2).shift(senkou_shift)
    
    # Senkou Span B: 52-period high/low midpoint, shifted forward  
    senkou_b = ((high.rolling(window=senkou_period).max() + 
                 low.rolling(window=senkou_period).min()) / 2).shift(senkou_shift)
    
    # Effective cloud aligned to price (shifted back for comparison)
    # For comparing price at time t with cloud, we use senkou_a[t-senkou_shift]
    # But since we already shifted forward, we need to align properly
    cloud_top = np.maximum(senkou_a, senkou_b)
    cloud_bottom = np.minimum(senkou_a, senkou_b)
    
    result = pd.DataFrame({
        'tenkan': tenkan,
        'kijun': kijun,
        'senkou_a': senkou_a,
        'senkou_b': senkou_b,
        'cloud_top': cloud_top,
        'cloud_bottom': cloud_bottom
    }, index=close.index)
    
    return result

def get_effective_cloud(ichimoku_df: pd.DataFrame, shift: int = 26) -> pd.DataFrame:
    """
    Get cloud values aligned to current price for comparison.
    
    The cloud is plotted 26 periods ahead, so for comparing price at time t
    with the cloud, we need to look at senkou_a[t-26] and senkou_b[t-26].
    
    Parameters:
    -----------
    ichimoku_df : pd.DataFrame
        DataFrame with Ichimoku components
    shift : int
        Senkou shift period (default 26)
    
    Returns:
    --------
    pd.DataFrame with cloud_top_eff and cloud_bottom_eff aligned to price
    """
    # For price at time t, the effective cloud is the senkou spans at time t-shift
    # But since senkou spans are already shifted forward in calculation,
    # we need to handle the alignment carefully
    
    # The cloud that would be visible at time t was calculated shift periods ago
    effective_cloud = pd.DataFrame({
        'cloud_top_eff': ichimoku_df['cloud_top'].shift(-shift),
        'cloud_bottom_eff': ichimoku_df['cloud_bottom'].shift(-shift)
    })
    
    return effective_cloud
