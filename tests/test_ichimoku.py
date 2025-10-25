"""
Unit tests for Ichimoku calculations.
"""
import pandas as pd
import numpy as np
import pytest
from indicators.ichimoku import calculate_ichimoku

def test_ichimoku_basic_calculation():
    """Test basic Ichimoku calculation with known values."""
    # Create synthetic data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    close = pd.Series(100 + np.cumsum(np.random.randn(100) * 2), index=dates)
    high = close + np.random.rand(100) * 5
    low = close - np.random.rand(100) * 5
    
    # Calculate Ichimoku
    result = calculate_ichimoku(high, low, close, 9, 26, 52)
    
    # Check that all components are present
    expected_columns = ['tenkan', 'kijun', 'senkou_a', 'senkou_b', 'cloud_top', 'cloud_bottom']
    assert all(col in result.columns for col in expected_columns)
    
    # Check that cloud top is >= cloud bottom
    assert (result['cloud_top'] >= result['cloud_bottom']).all()
    
    # Check that senkou spans are shifted
    assert pd.isna(result['senkou_a'].iloc[25])  # First 26 should be NaN due to shift
    assert not pd.isna(result['senkou_a'].iloc[26])

def test_ichimoku_known_values():
    """Test Ichimoku with known input/output."""
    # Create simple ascending data
    dates = pd.date_range('2023-01-01', periods=60, freq='D')
    close = pd.Series(range(1, 61), index=dates)
    high = close + 1
    low = close - 1
    
    result = calculate_ichimoku(high, low, close, 9, 26, 52)
    
    # For period 52, high=52+1=53, low=52-1=51, midpoint=52
    expected_senkou_b = 52.0
    
    # Check senkou_b calculation (should be at index 25 due to shift)
    assert abs(result['senkou_b'].iloc[51] - expected_senkou_b) < 0.001

def test_ichimoku_insufficient_data():
    """Test Ichimoku with insufficient data."""
    dates = pd.date_range('2023-01-01', periods=10, freq='D')
    close = pd.Series(range(1, 11), index=dates)
    high = close + 1
    low = close - 1
    
    result = calculate_ichimoku(high, low, close, 9, 26, 52)
    
    # With only 10 periods, most values should be NaN
    assert result['senkou_a'].isna().all()
    assert result['senkou_b'].isna().all()
