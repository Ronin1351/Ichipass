#!/usr/bin/env python3
"""
Ichimoku Cloud Scanner CLI
Finds symbols closing above Ichimoku cloud for the first time.
"""
import argparse
import sys
from pathlib import Path
from typing import List, Optional
import pandas as pd
from rich.console import Console
from rich.table import Table
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.loader import DataLoader
from scan.criteria import IchimokuScanner
from scan.runner import ScanRunner
from filters.volume import create_volume_filter, create_min_price_filter
from filters.macd import create_macd_filter
from filters.rsi import create_rsi_filter
from utils.logging import setup_logging

console = Console()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan for first close above Ichimoku cloud"
    )
    
    # Input sources
    input_group = parser.add_argument_group('Input Sources')
    input_group.add_argument(
        '--tickers-file',
        type=Path,
        help='File containing ticker symbols (one per line)'
    )
    input_group.add_argument(
        '--tickers',
        type=str,
        help='Comma-separated list of ticker symbols'
    )
    
    # Date range
    date_group = parser.add_argument_group('Date Range')
    date_group.add_argument(
        '--start',
        type=str,
        required=True,
        help='Start date (YYYY-MM-DD)'
    )
    date_group.add_argument(
        '--end',
        type=str,
        default='today',
        help='End date (YYYY-MM-DD or "today")'
    )
    
    # Ichimoku parameters
    ichi_group = parser.add_argument_group('Ichimoku Parameters')
    ichi_group.add_argument(
        '--ichi-tenkan',
        type=int,
        default=9,
        help='Tenkan period (default: 9)'
    )
    ichi_group.add_argument(
        '--ichi-kijun',
        type=int,
        default=26,
        help='Kijun period (default: 26)'
    )
    ichi_group.add_argument(
        '--ichi-senkou',
        type=int,
        default=52,
        help='Senkou period (default: 52)'
    )
    
    # Scan criteria
    scan_group = parser.add_argument_group('Scan Criteria')
    scan_group.add_argument(
        '--lookback-not-above',
        type=int,
        default=10,
        help='Lookback period to check for no prior close above cloud (default: 10)'
    )
    scan_group.add_argument(
        '--min-price',
        type=float,
        default=0.0,
        help='Minimum price filter (default: 0)'
    )
    scan_group.add_argument(
        '--min-avg-dollar-volume',
        type=float,
        default=0.0,
        help='Minimum 20-day average dollar volume (default: 0)'
    )
    scan_group.add_argument(
        '--strict-cross',
        action='store_true',
        default=True,
        help='Require strict cross (close[t-1] <= cloud and close[t] > cloud)'
    )
    
    # Execution
    exec_group = parser.add_argument_group('Execution')
    exec_group.add_argument(
        '--output',
        type=Path,
        help='Output CSV file path'
    )
    exec_group.add_argument(
        '--source',
        choices=['yfinance', 'csv'],
        default='yfinance',
        help='Data source (default: yfinance)'
    )
    exec_group.add_argument(
        '--threads',
        type=int,
        default=8,
        help='Number of threads for parallel processing (default: 8)'
    )
    exec_group.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Log level (default: INFO)'
    )
    exec_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview configuration without running scan'
    )
    exec_group.add_argument(
        '--cache-dir',
        type=Path,
        help='Directory to cache downloaded data'
    )
    
    return parser.parse_args()

def load_tickers(args) -> List[str]:
    """Load ticker symbols from file or command line."""
    tickers = []
    
    if args.tickers_file:
        try:
            with open(args.tickers_file, 'r') as f:
                tickers = [line.strip() for line in f if line.strip()]
            console.print(f"Loaded {len(tickers)} tickers from {args.tickers_file}")
        except Exception as e:
            console.print(f"[red]Error loading tickers file: {e}[/red]")
            sys.exit(1)
    
    if args.tickers:
        tickers.extend([t.strip() for t in args.tickers.split(',')])
    
    if not tickers:
        console.print("[red]No tickers provided. Use --tickers-file or --tickers[/red]")
        sys.exit(1)
    
    # Remove duplicates
    tickers = list(set(tickers))
    return tickers

def display_results(results: List[dict], args):
    """Display results in pretty table and save to CSV."""
    if not results:
        console.print("[yellow]No matches found.[/yellow]")
        return
    
    # Create rich table
    table = Table(title=f"Ichimoku Cloud Breakouts - {len(results)} Matches")
    
    table.add_column("Symbol", style="cyan")
    table.add_column("Date", style="white")
    table.add_column("Close", style="green")
    table.add_column("Cloud Top", style="magenta")
    table.add_column("Distance %", style="yellow")
    table.add_column("Avg $ Vol", style="blue")
    
    for result in results:
        table.add_row(
            result['symbol'],
            result['date_yesterday'],
            f"{result['close_y']:.2f}",
            f"{result['cloud_top_y']:.2f}",
            f"{result['distance_pct']:.2f}%",
            f"{result['avg_dollar_vol_20']:,.0f}"
        )
    
    console.print(table)
    
    # Save to CSV
    if args.output:
        df = pd.DataFrame(results)
        df.to_csv(args.output, index=False)
        console.print(f"[green]Results saved to {args.output}[/green]")
    
    # Save JSON summary
    summary = {
        'scan_date': datetime.now().isoformat(),
        'parameters': {
            'start_date': args.start,
            'end_date': args.end,
            'tenkan_period': args.ichi_tenkan,
            'kijun_period': args.ichi_kijun,
            'senkou_period': args.ichi_senkou,
            'lookback_not_above': args.lookback_not_above,
            'min_price': args.min_price,
            'min_avg_dollar_volume': args.min_avg_dollar_volume
        },
        'results_count': len(results),
        'symbols': [r['symbol'] for r in results]
    }
    
    if args.output:
        json_file = args.output.with_suffix('.json')
        with open(json_file, 'w') as f:
            json.dump(summary, f, indent=2)
        console.print(f"[green]Summary saved to {json_file}[/green]")

def main():
    """Main CLI entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load tickers
    tickers = load_tickers(args)
    
    if args.dry_run:
        console.print("[yellow]DRY RUN - Configuration Preview:[/yellow]")
        console.print(f"Tickers: {len(tickers)} symbols")
        console.print(f"Date Range: {args.start} to {args.end}")
        console.print(f"Ichimoku: Tenkan={args.ichi_tenkan}, Kijun={args.ichi_kijun}, Senkou={args.ichi_senkou}")
        console.print(f"Lookback: {args.lookback_not_above} days")
        console.print(f"Filters: Price>={args.min_price}, Dollar Vol>={args.min_avg_dollar_volume:,.0f}")
        console.print(f"Threads: {args.threads}")
        return
    
    # Initialize components
    data_loader = DataLoader(cache_dir=args.cache_dir)
    
    scanner = IchimokuScanner(
        tenkan_period=args.ichi_tenkan,
        kijun_period=args.ichi_kijun,
        senkou_period=args.ichi_senkou,
        lookback_not_above=args.lookback_not_above,
        min_price=args.min_price,
        strict_cross=args.strict_cross
    )
    
    runner = ScanRunner(
        data_loader=data_loader,
        scanner=scanner,
        max_workers=args.threads
    )
    
    # Register filters
    if args.min_avg_dollar_volume > 0:
        runner.register_filter(
            'volume',
            create_volume_filter(args.min_avg_dollar_volume)
        )
    
    if args.min_price > 0:
        runner.register_filter(
            'min_price', 
            create_min_price_filter(args.min_price)
        )
    
    # Run scan
    console.print("[green]Starting Ichimoku cloud scan...[/green]")
    results = runner.run_scan(
        tickers=tickers,
        start=args.start,
        end=args.end,
        source=args.source,
        dry_run=args.dry_run
    )
    
    # Display and save results
    display_results(results, args)

if __name__ == '__main__':
    main()
