"""
Logging configuration and utilities for the torrent client.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class TorrentLogger:
    """Centralized logging configuration for the torrent client."""
    
    _instance: Optional['TorrentLogger'] = None
    _initialized = False
    
    def __new__(cls) -> 'TorrentLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if not self._initialized:
            self._setup_logging()
            TorrentLogger._initialized = True
    
    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"torrent_client_{timestamp}.log"
        
        # Configure root logger
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)

        rotating_handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=5, encoding='utf-8')
        rotating_handler.setFormatter(formatter)

        root = logging.getLogger()
        root.setLevel(logging.INFO)
        # Clear existing handlers to avoid duplicate logs in some environments
        root.handlers = []
        root.addHandler(stream_handler)
        root.addHandler(rotating_handler)
        
        # Set specific log levels for different modules
        logging.getLogger('libtorrent').setLevel(logging.WARNING)
        logging.getLogger('PySide6').setLevel(logging.WARNING)
        
        # Create application logger
        self.logger = logging.getLogger('torrent_client')
        self.logger.setLevel(logging.INFO)

        # Log startup
        self.logger.info("Torrent client logging initialized")
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module."""
        return logging.getLogger(f'torrent_client.{name}')

    


# Global logger instance
torrent_logger = TorrentLogger()


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger for a module."""
    return torrent_logger.get_logger(name)