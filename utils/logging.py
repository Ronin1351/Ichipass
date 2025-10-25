"""
Logging configuration utilities.
"""
import logging
import sys
from rich.logging import RichHandler

def setup_logging(level: str = "INFO"):
    """Setup rich logging configuration."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
