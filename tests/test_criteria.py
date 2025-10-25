"""
Unit tests for scan criteria.
"""
import pandas as pd
import numpy as np
from scan.criteria import IchimokuScanner

def create_test_data():
    """Create test data for scanning."""
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    
    # Create synthetic price data
    np.random.seed(42)
    base_price = 100
    returns = np.random.randn(100) * 0.02
    prices = base_price * (1 + np.cumsum(returns))
    
    data = pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.01,
        'Low': prices * 0.99,
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    return data

def test_first_close_above_cloud():
    """Test detection of first close above cloud."""
    scanner = IchimokuScanner(lookback_not_above=5)
    data = create_test_data()
    
    # Manipulate last few closes to create breakout pattern
    # All prior closes below cloud, yesterday above cloud
    data_with_indicators = scanner.calculate_indicators(data)
    
    # Get cloud levels for manipulation
    cloud_top = data_with_indicators['cloud_top_eff'].copy()
    
    # Create breakout pattern: prior closes below, yesterday above
    for i in range(-7, -2):  # Prior days
        data_with_indicators.iloc[i, data_with_indicators.columns.get_loc('Close')] = \
            cloud_top.iloc[i] - 1.0
    
    # Yesterday above cloud
    data_with_indicators.iloc[-2, data_with_indicators.columns.get_loc('Close')] = \
        cloud_top.iloc[-2] + 1.0
    
    is_match, yesterday_data = scanner.is_first_close_above_cloud(data_with_indicators)
    
    assert is_match == True
    assert yesterday_data is not None
    assert yesterday_data['Close'] > yesterday_data['cloud_top_eff']

def test_already_above_cloud():
    """Test exclusion of symbols already above cloud."""
    scanner = IchimokuScanner(lookback_not_above=5)
    data = create_test_data()
    data_with_indicators = scanner.calculate_indicators(data)
    
    cloud_top = data_with_indicators['cloud_top_eff'].copy()
    
    # Set multiple prior days above cloud
    for i in range(-7, -1):  # Multiple days above
        data_with_indicators.iloc[i, data_with_indicators.columns.get_loc('Close')] = \
            cloud_top.iloc[i] + 1.0
    
    is_match, _ = scanner.is_first_close_above_cloud(data_with_indicators)
    
    assert is_match == False

def test_close_equal_to_cloud():
    """Test that close equal to cloud does not count as above."""
    scanner = IchimokuScanner(lookback_not_above=5)
    data = create_test_data()
    data_with_indicators = scanner.calculate_indicators(data)
    
    cloud_top = data_with_indicators['cloud_top_eff'].copy()
    
    # Set yesterday close equal to cloud top
    data_with_indicators.iloc[-2, data_with_indicators.columns.get_loc('Close')] = \
        cloud_top.iloc[-2]
    
    is_match, _ = scanner.is_first_close_above_cloud(data_with_indicators)
    
    assert is_match == False
