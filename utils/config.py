"""
Configuration management for the torrent client.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class TorrentConfig:
    """Configuration settings for the torrent client."""
    
    # Network settings
    listen_port: int = 6881
    listen_interfaces: str = "0.0.0.0:6881"
    max_connections: int = 200
    max_uploads: int = 4
    
    # Speed limits (KiB/s, 0 = unlimited)
    global_download_limit: int = 0
    global_upload_limit: int = 0
    
    # Paths
    download_path: str = "downloads"
    config_dir: str = "config"
    log_dir: str = "logs"
    
    # UI settings
    window_width: int = 1200
    window_height: int = 700
    theme: str = "dark"
    
    # Torrent settings
    piece_timeout: int = 30
    request_timeout: int = 60
    user_agent: str = "TorrentDownloader/1.0"
    
    # Advanced settings
    enable_dht: bool = True
    enable_lsd: bool = True
    enable_upnp: bool = True
    enable_natpmp: bool = True
    
    # Performance settings
    cache_size: int = 32  # MB
    disk_cache_algorithm: int = 0  # 0 = avoid_readback, 1 = read_through
    
    # Scheduling
    bandwidth_schedules: list = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Initialize paths and validate configuration."""
        self._ensure_directories()
        self._validate_config()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.download_path,
            self.config_dir,
            self.log_dir
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        if self.listen_port < 1024 or self.listen_port > 65535:
            logger.warning(f"Invalid port {self.listen_port}, using default 6881")
            self.listen_port = 6881
        
        if self.max_connections < 1:
            logger.warning(f"Invalid max_connections {self.max_connections}, using default 200")
            self.max_connections = 200
        
        if self.cache_size < 1:
            logger.warning(f"Invalid cache_size {self.cache_size}, using default 32")
            self.cache_size = 32
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'listen_port': self.listen_port,
            'listen_interfaces': self.listen_interfaces,
            'max_connections': self.max_connections,
            'max_uploads': self.max_uploads,
            'global_download_limit': self.global_download_limit,
            'global_upload_limit': self.global_upload_limit,
            'download_path': self.download_path,
            'config_dir': self.config_dir,
            'log_dir': self.log_dir,
            'window_width': self.window_width,
            'window_height': self.window_height,
            'theme': self.theme,
            'piece_timeout': self.piece_timeout,
            'request_timeout': self.request_timeout,
            'user_agent': self.user_agent,
            'enable_dht': self.enable_dht,
            'enable_lsd': self.enable_lsd,
            'enable_upnp': self.enable_upnp,
            'enable_natpmp': self.enable_natpmp,
            'cache_size': self.cache_size,
            'disk_cache_algorithm': self.disk_cache_algorithm
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TorrentConfig':
        """Create configuration from dictionary."""
        return cls(**data)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Updated config: {key} = {value}")
    
    def get_libtorrent_settings(self) -> Dict[str, Any]:
        """Get libtorrent-specific settings."""
        return {
            'user_agent': self.user_agent,
            'listen_interfaces': self.listen_interfaces,
            'download_rate_limit': self.global_download_limit * 1024,  # Convert to bytes
            'upload_rate_limit': self.global_upload_limit * 1024,  # Convert to bytes
            'max_connections': self.max_connections,
            'max_uploads': self.max_uploads,
            'piece_timeout': self.piece_timeout,
            'request_timeout': self.request_timeout,
            'enable_dht': self.enable_dht,
            'enable_lsd': self.enable_lsd,
            'enable_upnp': self.enable_upnp,
            'enable_natpmp': self.enable_natpmp,
            'cache_size': self.cache_size * 1024 * 1024,  # Convert to bytes
            'disk_cache_algorithm': self.disk_cache_algorithm
        }


class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self, config_file: str = "config/settings.json") -> None:
        self.config_file = Path(config_file)
        self.config = TorrentConfig()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.config.update_from_dict(data)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                logger.info("Using default configuration")
        else:
            logger.info("No configuration file found, using defaults")
            self.save_config()  # Create default config file
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            import json
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get_config(self) -> TorrentConfig:
        """Get current configuration."""
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """Update configuration values."""
        self.config.update_from_dict(kwargs)
        self.save_config()


# Global config manager instance
config_manager = ConfigManager()