# 📈 Ichipass - Ichimoku Cloud Scanner

A powerful Python-based trading scanner that detects stocks breaking above the Ichimoku Cloud for the first time in a specified lookback period. Available as both a **CLI tool** and a **beautiful web interface**.

## ✨ Features

### Core Capabilities
- 🎯 **First Breakout Detection**: Identifies stocks closing above Ichimoku Cloud for the first time
- 📊 **Customizable Parameters**: Configure Tenkan, Kijun, and Senkou periods
- 🔍 **Advanced Filters**: Volume, price, RSI, and MACD filters
- 🚀 **Parallel Processing**: Multi-threaded data loading and scanning
- 💾 **Smart Caching**: Pickle-based caching for faster rescans
- 📈 **Strict Cross Validation**: Optional strict crossing mode
- 📋 **Multiple Output Formats**: CSV, JSON, and rich terminal tables

### Two Interfaces

#### 1. 🖥️ Command Line Interface (CLI)
- Fast, scriptable, perfect for automation
- Rich terminal output with colored tables
- Comprehensive argument parsing
- Dry-run mode for configuration preview

#### 2. 🎨 Web Interface (NEW!)
- **Neumorphic UI Design**: Modern, beautiful, intuitive
- Real-time scan progress monitoring
- Interactive dashboard with statistics
- Responsive design (mobile-friendly)
- RESTful API for integrations

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Ichipass.git
cd Ichipass

# Install dependencies
pip install -r requirements.txt
```

### Option 1: CLI Usage

```bash
# Basic scan
python ichicloud_scan.py \
  --tickers "AAPL,MSFT,GOOGL" \
  --start "2024-01-01" \
  --end "today" \
  --output results.csv

# Advanced scan with filters
python ichicloud_scan.py \
  --tickers-file my_watchlist.txt \
  --start "2024-01-01" \
  --ichi-tenkan 9 \
  --ichi-kijun 26 \
  --ichi-senkou 52 \
  --lookback-not-above 10 \
  --min-price 5.0 \
  --min-avg-dollar-volume 1000000 \
  --threads 16
```

### Option 2: Web Interface

```bash
# Easy way - use the startup script
./start_web.sh

# Manual way
cd web
python app.py
```

Then open your browser to:
- **UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📖 How It Works

### Ichimoku Cloud Components

The Ichimoku Cloud (Ichimoku Kinko Hyo) is a comprehensive indicator that defines support/resistance, identifies trend direction, gauges momentum, and provides trading signals.

**Components:**
- **Tenkan-sen** (Conversion Line): (9-period high + 9-period low) / 2
- **Kijun-sen** (Base Line): (26-period high + 26-period low) / 2
- **Senkou Span A** (Leading Span A): (Tenkan + Kijun) / 2, plotted 26 periods ahead
- **Senkou Span B** (Leading Span B): (52-period high + 52-period low) / 2, plotted 26 periods ahead
- **Kumo** (Cloud): Area between Senkou Span A and B

### Breakout Detection Logic

Ichipass scans for **first close above cloud** signals:

1. ✅ Yesterday's close > Cloud Top (current alignment)
2. ✅ Previous N days were NOT above cloud (lookback period)
3. ✅ Optional: Strict cross mode (day before yesterday was ≤ cloud top)
4. ✅ Passes all filters (price, volume, RSI, MACD)

This identifies the **exact moment** a stock breaks above the cloud, which is considered a strong bullish signal.

## 🎯 CLI Reference

### Input Sources
```bash
--tickers "AAPL,MSFT"         # Comma-separated list
--tickers-file watchlist.txt  # File with one ticker per line
```

### Date Range
```bash
--start "2024-01-01"  # Required: Start date (YYYY-MM-DD)
--end "today"         # End date (YYYY-MM-DD or "today")
```

### Ichimoku Parameters
```bash
--ichi-tenkan 9   # Conversion line period (default: 9)
--ichi-kijun 26   # Base line period (default: 26)
--ichi-senkou 52  # Leading span period (default: 52)
```

### Scan Criteria
```bash
--lookback-not-above 10      # Days to check for no prior breakout (default: 10)
--min-price 5.0              # Minimum stock price (default: 0)
--min-avg-dollar-volume 1e6  # Minimum 20-day avg dollar volume (default: 0)
--strict-cross               # Require strict cross (enabled by default)
```

### Execution Options
```bash
--output results.csv    # Save results to CSV
--threads 8            # Number of parallel workers (default: 8)
--cache-dir ./cache    # Cache directory for downloaded data
--log-level INFO       # Log level: DEBUG, INFO, WARNING, ERROR
--dry-run             # Preview configuration without scanning
```

## 🌐 Web Interface Guide

### Scanner Tab
1. Enter ticker symbols (comma-separated)
2. Set date range
3. Configure Ichimoku parameters (or use presets)
4. Apply filters
5. Start scan and monitor progress

### Results Tab
- View detected breakouts in table format
- See key metrics: Close, Cloud Top, Distance %, Volume
- Download results as CSV

### Settings Tab
- Configure thread count
- Set cache directory
- Adjust log level
- Clear cache

### API Usage

```python
import requests

# Create a scan
response = requests.post('http://localhost:8000/api/scans', json={
    'tickers': ['AAPL', 'MSFT'],
    'start': '2024-01-01',
    'end': '2024-12-31',
    'tenkan': 9,
    'kijun': 26,
    'senkou': 52,
    'lookback': 10,
    'minPrice': 5.0,
    'minVolume': 1000000,
    'strictCross': True,
    'threads': 8
})

scan_id = response.json()['scan_id']

# Check status
status = requests.get(f'http://localhost:8000/api/scans/{scan_id}')
print(status.json())
```

## 🏗️ Project Structure

```
Ichipass/
├── ichicloud_scan.py      # Main CLI application
├── start_web.sh           # Web server startup script
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── data/
│   └── loader.py         # Data loading and caching
│
├── indicators/
│   └── ichimoku.py       # Ichimoku calculations
│
├── scan/
│   ├── criteria.py       # Scan logic and breakout detection
│   └── runner.py         # Parallel scan orchestration
│
├── filters/
│   ├── volume.py         # Volume and price filters
│   ├── rsi.py           # RSI filter
│   └── macd.py          # MACD filter
│
├── utils/
│   └── logging.py       # Logging configuration
│
├── tests/
│   ├── test_ichimoku.py  # Ichimoku unit tests
│   └── test_criteria.py  # Scan criteria tests
│
└── web/
    ├── app.py            # FastAPI application
    ├── static/
    │   ├── css/
    │   │   └── neumorphic.css  # Neumorphic styles
    │   └── js/
    │       └── app.js          # Frontend logic
    ├── templates/
    │   └── index.html          # Landing page
    └── README.md              # Web interface docs
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_ichimoku.py

# Run with verbose output
pytest -v
```

## 🎨 Neumorphic UI Design

The web interface features a modern **Neumorphic** (soft UI) design:

- **Soft shadows** creating depth and dimension
- **Subtle gradients** for visual interest
- **Smooth animations** for better UX
- **Consistent spacing** using a design system
- **Responsive layout** that works on all devices

**Color Palette:**
- Background: #e0e5ec (soft gray)
- Primary: #6c5ce7 (purple)
- Secondary: #00b894 (teal)
- Success: #00b894, Warning: #fdcb6e, Danger: #d63031

## 📊 Example Output

### CLI Output
```
╭──────────────────────────────────────────────────────────╮
│  Ichimoku Cloud Breakouts - 3 Matches                   │
├────────┬────────────┬────────┬───────────┬────────────┬─┤
│ Symbol │ Date       │ Close  │ Cloud Top │ Distance % │  │
├────────┼────────────┼────────┼───────────┼────────────┼─┤
│ AAPL   │ 2024-10-23 │ 150.25 │ 148.50   │ 1.18%     │  │
│ MSFT   │ 2024-10-23 │ 380.75 │ 375.20   │ 1.48%     │  │
│ GOOGL  │ 2024-10-23 │ 142.80 │ 140.15   │ 1.89%     │  │
╰────────┴────────────┴────────┴───────────┴────────────┴─╯
```

### CSV Output
```csv
symbol,date_yesterday,close_y,cloud_top_y,distance_pct,avg_dollar_vol_20
AAPL,2024-10-23,150.25,148.50,1.18,50000000000
MSFT,2024-10-23,380.75,375.20,1.48,30000000000
GOOGL,2024-10-23,142.80,140.15,1.89,25000000000
```

## 🔧 Advanced Usage

### Custom Filter Development

Create custom filters by following this pattern:

```python
# filters/custom.py
def create_custom_filter(threshold: float):
    def custom_filter(symbol: str, data: pd.DataFrame, result: dict) -> bool:
        # Your custom logic here
        return some_condition
    return custom_filter
```

### Batch Scanning

```bash
# Scan multiple watchlists
for list in watchlists/*.txt; do
    python ichicloud_scan.py \
        --tickers-file "$list" \
        --start "2024-01-01" \
        --output "results_$(basename $list .txt).csv"
done
```

### Scheduled Scans (Cron)

```bash
# Add to crontab: Run daily at 5 PM
0 17 * * * cd /path/to/Ichipass && ./daily_scan.sh
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'yfinance'`
```bash
pip install -r requirements.txt
```

**Issue**: Web server port already in use
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

**Issue**: No data returned for symbols
- Check ticker symbol is correct (use Yahoo Finance format)
- Verify internet connection
- Check date range is valid
- Try clearing cache

**Issue**: Scan is slow
- Increase thread count: `--threads 16`
- Use cache: Enabled by default
- Reduce date range
- Filter by volume to reduce symbols

## 📈 Performance

- **Data Loading**: ~100-200 symbols/minute (with caching: 1000+/minute)
- **Scanning**: ~500-1000 symbols/minute (depends on CPU cores)
- **Memory**: ~50-100MB for typical scans
- **Cache Size**: ~1-5MB per symbol per year

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Ichimoku Kinko Hyo methodology
- Yahoo Finance for data
- FastAPI framework
- Rich library for beautiful CLI output

## 📧 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check the documentation
- Review existing issues

---

**Made with ❤️ for traders who love technical analysis**

*Disclaimer: This tool is for educational and research purposes only. Always do your own research before making investment decisions.*
