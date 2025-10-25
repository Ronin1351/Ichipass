# Ichipass Web Interface

Beautiful Neumorphic UI for the Ichimoku Cloud Scanner.

## Features

- **🎨 Neumorphic Design**: Modern, soft UI with depth and shadows
- **📊 Real-time Scanning**: Monitor scan progress in real-time
- **📈 Interactive Dashboard**: View scan results with rich data visualization
- **⚙️ Configurable Parameters**: Customize Ichimoku periods and filters
- **💾 Data Caching**: Faster rescans with built-in caching
- **📱 Responsive Design**: Works on desktop, tablet, and mobile

## Quick Start

### 1. Install Dependencies

```bash
# From the project root
pip install -r requirements.txt
```

### 2. Start the Web Server

```bash
# Navigate to web directory
cd web

# Start the server
python app.py
```

The application will start on `http://localhost:8000`

### 3. Access the UI

Open your browser and navigate to:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Alternative Docs**: http://localhost:8000/redoc

## Usage Guide

### Scanner Tab

1. **Enter Ticker Symbols**: Comma-separated list (e.g., "AAPL, MSFT, GOOGL")
2. **Set Date Range**: Choose start and end dates for analysis
3. **Configure Ichimoku Parameters**:
   - Tenkan (Conversion Line): Default 9
   - Kijun (Base Line): Default 26
   - Senkou (Leading Span): Default 52
4. **Apply Filters**:
   - Minimum Price: Filter out low-priced stocks
   - Min Avg Dollar Volume: Ensure liquidity
   - Strict Cross Mode: Require previous day below cloud
5. **Click "Start Scan"**: Monitor progress in real-time

### Results Tab

- View all detected breakouts in a table
- See key metrics: Close price, Cloud top, Distance %, Volume
- Download results as CSV

### Settings Tab

- **Thread Count**: Number of parallel workers (default: 8)
- **Cache Directory**: Where to store downloaded data
- **Log Level**: Debug, Info, Warning, or Error
- **Clear Cache**: Remove cached data to force fresh downloads

### Documentation Tab

Complete guide on:
- What is Ichipass
- Ichimoku Cloud components
- How to use the scanner
- Filter explanations

## API Endpoints

### Scans

- **POST** `/api/scans` - Create new scan
- **GET** `/api/scans/{id}` - Get scan status
- **GET** `/api/scans` - List all scans
- **DELETE** `/api/scans/{id}` - Cancel scan

### Cache Management

- **DELETE** `/api/cache` - Clear cache
- **GET** `/api/cache/size` - Get cache size

### Statistics

- **GET** `/api/stats` - Application statistics
- **GET** `/api/health` - Health check

## Neumorphic Design System

### Color Scheme

- **Background**: `#e0e5ec` (soft gray)
- **Primary Accent**: `#6c5ce7` (purple)
- **Secondary Accent**: `#00b894` (teal)
- **Success**: `#00b894` (green)
- **Warning**: `#fdcb6e` (yellow)
- **Danger**: `#d63031` (red)

### Shadow Effects

- **Convex**: Raised elements (buttons, cards)
- **Concave**: Pressed/inset elements (inputs)
- **Flat**: Subtle hover states

### Components

All UI components follow neumorphic principles:
- Cards with soft shadows
- Inset form inputs
- Raised buttons
- Smooth animations
- Consistent spacing

## File Structure

```
web/
├── app.py                 # FastAPI application
├── static/
│   ├── css/
│   │   └── neumorphic.css # Neumorphic styles
│   └── js/
│       └── app.js         # Frontend logic
├── templates/
│   └── index.html         # Main landing page
└── README.md             # This file
```

## Development

### Running in Development Mode

The server runs with hot reload enabled by default:

```bash
python app.py
```

### Running with Custom Settings

```bash
# Custom host and port
uvicorn app:app --host 0.0.0.0 --port 8080 --reload

# Production mode (no reload)
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Environment Variables

You can configure the following:

```bash
export ICHIPASS_CACHE_DIR=/path/to/cache
export ICHIPASS_LOG_LEVEL=DEBUG
export ICHIPASS_MAX_WORKERS=16
```

## Customization

### Changing Colors

Edit `static/css/neumorphic.css` and modify the CSS variables in `:root`:

```css
:root {
  --bg-primary: #e0e5ec;      /* Background */
  --accent-primary: #6c5ce7;  /* Primary accent */
  --accent-secondary: #00b894; /* Secondary accent */
  /* ... */
}
```

### Adding Custom Filters

1. Create filter function in `/filters/` directory
2. Import in `app.py`
3. Register in `run_scan` function

### Extending API

Add new endpoints in `app.py`:

```python
@app.get("/api/custom-endpoint")
async def custom_endpoint():
    return {"data": "value"}
```

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support (iOS 12+)
- Opera: ✅ Full support

## Performance Tips

1. **Use Caching**: Enable cache for faster rescans
2. **Adjust Thread Count**: More threads = faster scans (but more CPU usage)
3. **Filter Early**: Apply price/volume filters to reduce processing
4. **Limit Date Range**: Smaller date ranges process faster

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app:app --port 8001
```

### Cache Issues

```bash
# Clear cache via UI Settings tab
# Or manually delete cache directory
rm -rf ./cache
```

### Dependencies Issues

```bash
# Reinstall all dependencies
pip install --upgrade --force-reinstall -r ../requirements.txt
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Ichipass scanner suite.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Built with ❤️ using FastAPI and Neumorphic Design**
