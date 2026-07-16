"""Centralized logging configuration for TrafficIQ."""

import logging
import sys
from pathlib import Path
from backend.core.config import LOGS_DIR

def setup_logger(name: str = "trafficiq", log_file: str | Path | None = None, level: int = logging.INFO) -> logging.Logger:
    """Set up and configure a logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
         return logger
         
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / "app.log"
        
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not configure file log handler: {e}")

    return logger

# Default logger instance
logger = setup_logger()
