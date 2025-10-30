# core/torrent_engine.py

import libtorrent as lt
import time
import threading
import os
from queue import Queue
from typing import Dict, List, Optional, Any, Union
from . import persistence
from utils.logger import get_logger
from utils.config import config_manager
from utils.security import sanitize_path

logger = get_logger(__name__) 

class TorrentEngine(threading.Thread):
    def __init__(self, alert_queue: Queue) -> None:
        super().__init__()
        self.alert_queue = alert_queue
        self._shutdown_flag = threading.Event()
        self._lock = threading.Lock()
        
        # Initialize database
        persistence.init_db()
        
        # Load configuration
        config = config_manager.get_config()
        
        # Get speed limits from config
        dl_limit = config.global_download_limit * 1024
        ul_limit = config.global_upload_limit * 1024
        
        # Create libtorrent settings
        settings = config.get_libtorrent_settings()
        settings['alert_mask'] = lt.alert.category_t.all_categories
        
        self.ses = lt.session(settings)
        self.handles: Dict[bytes, lt.torrent_handle] = {}
        
        logger.info("TorrentEngine initialized")
        self.load_session()

    def load_session(self) -> None:
        """Load previously saved torrents from database."""
        saved_torrents = persistence.load_torrents_info()
        logger.info(f"Loading {len(saved_torrents)} saved torrents")
        
        for torrent_data in saved_torrents:
            try:
                if torrent_data['type'] == 'magnet':
                    self.add_torrent_by_magnet(torrent_data['source'], torrent_data['save_path'], is_loading=True)
                elif torrent_data['type'] == 'file':
                    self.add_torrent_from_file(torrent_data['source'], torrent_data['save_path'], is_loading=True)
            except Exception as e:
                logger.error(f"Failed to load torrent {torrent_data.get('info_hash', 'unknown')}: {e}")
            
    def run(self) -> None:
        """Main engine loop - processes libtorrent alerts and updates."""
        logger.info("TorrentEngine main loop started")
        while not self._shutdown_flag.is_set():
            try:
                self.ses.wait_for_alert(1000)
                alerts = self.ses.pop_alerts()
                for alert in alerts:
                    self.alert_queue.put(alert)
                self.ses.post_torrent_updates()
            except Exception as e:
                logger.error(f"Error in torrent engine main loop: {e}")
            time.sleep(0.1)  # Reduced sleep time for more responsive shutdown
        
        logger.info("TorrentEngine main loop stopped")
    
    def shutdown(self) -> None:
        """Gracefully shutdown the torrent engine."""
        logger.info("Shutting down TorrentEngine...")
        self._shutdown_flag.set()
        self.join(timeout=5.0)  # Wait up to 5 seconds for graceful shutdown
        logger.info("TorrentEngine shutdown complete")

    def add_torrent_from_file(self, torrent_file_path: str, save_path: str, is_loading: bool = False) -> Optional[bytes]:
        """Add a torrent from a .torrent file."""
        try:
            if not os.path.exists(torrent_file_path):
                raise FileNotFoundError(f"Torrent file not found: {torrent_file_path}")
            
            # Sanitize and ensure save path under configured downloads dir
            base_dir = config_manager.get_config().download_path
            safe_save = sanitize_path(base_dir, save_path) or sanitize_path(base_dir, ".")
            if safe_save is None:
                logger.error("Rejected save path outside base directory")
                return None
            if not os.path.exists(safe_save):
                os.makedirs(safe_save, exist_ok=True)
                logger.debug(f"Created directory: {safe_save}")
            
            params = {
                'ti': lt.torrent_info(torrent_file_path),
                'save_path': safe_save
            }
            handle = self.ses.add_torrent(params)
            info_hash = handle.info_hash()
            info_hash_hex = str(info_hash)
            
            with self._lock:
                self.handles[info_hash] = handle
            
            if not is_loading:
                persistence.save_torrent_info(info_hash_hex, safe_save, 'file', torrent_file_path)
            
            logger.info(f"Added torrent from file: {handle.name() or info_hash_hex}")
            return info_hash
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            return None
        except lt.libtorrent_exception as e:
            logger.error(f"Libtorrent error adding torrent from file {torrent_file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error adding torrent from file {torrent_file_path}: {e}")
            return None

    def add_torrent_by_magnet(self, magnet_link: str, save_path: str, is_loading: bool = False) -> Optional[bytes]:
        """Add a torrent from a magnet link."""
        try:
            if not magnet_link.startswith('magnet:'):
                raise ValueError("Invalid magnet link format")
            
            base_dir = config_manager.get_config().download_path
            safe_save = sanitize_path(base_dir, save_path) or sanitize_path(base_dir, ".")
            if safe_save is None:
                logger.error("Rejected save path outside base directory")
                return None
            if not os.path.exists(safe_save):
                os.makedirs(safe_save, exist_ok=True)
                logger.debug(f"Created directory: {safe_save}")
            
            params = lt.parse_magnet_uri(magnet_link)
            params.save_path = safe_save
            handle = self.ses.add_torrent(params)
            info_hash = handle.info_hash()
            info_hash_hex = str(info_hash)
            
            with self._lock:
                self.handles[info_hash] = handle
            
            if not is_loading:
                persistence.save_torrent_info(info_hash_hex, safe_save, 'magnet', magnet_link)
            
            logger.info(f"Added torrent from magnet: {handle.name() or info_hash_hex}")
            return info_hash
            
        except ValueError as e:
            logger.error(f"Invalid magnet link: {e}")
            return None
        except lt.libtorrent_exception as e:
            logger.error(f"Libtorrent error adding magnet link {magnet_link}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error adding magnet link {magnet_link}: {e}")
            return None

    def pause_torrent(self, info_hash: bytes) -> None:
        """Pause a torrent."""
        with self._lock:
            if info_hash in self.handles:
                self.handles[info_hash].pause()
                logger.info(f"Paused torrent: {info_hash}")

    def resume_torrent(self, info_hash: bytes) -> None:
        """Resume a torrent."""
        with self._lock:
            if info_hash in self.handles:
                self.handles[info_hash].resume()
                logger.info(f"Resumed torrent: {info_hash}")

    def remove_torrent(self, info_hash: bytes, remove_data: bool = False) -> None:
        """Remove a torrent from the session."""
        with self._lock:
            if info_hash in self.handles:
                handle = self.handles.pop(info_hash)
                flags = lt.session.delete_files if remove_data else 0
                self.ses.remove_torrent(handle, flags)
                persistence.remove_torrent_info(str(info_hash))
                logger.info(f"Removed torrent: {info_hash} (data: {remove_data})")

    def get_torrent_files(self, info_hash: bytes) -> List[Dict[str, Any]]:
        """Get file list for a torrent."""
        with self._lock:
            if info_hash not in self.handles: 
                return []
            handle = self.handles[info_hash]
        
        if not handle.status().has_metadata: 
            return []
        
        files = []
        try:
            file_storage = handle.torrent_file().files()
            for i in range(file_storage.num_files()):
                files.append({
                    "path": file_storage.file_path(i), 
                    "size": file_storage.file_size(i)
                })
        except Exception as e:
            logger.error(f"Error getting torrent files: {e}")
        
        return files

    def get_torrent_trackers(self, info_hash: bytes) -> List[Dict[str, str]]:
        """Get tracker list for a torrent."""
        with self._lock:
            if info_hash not in self.handles: 
                return []
            handle = self.handles[info_hash]
        
        try:
            # Use dictionary key access for libtorrent v1.x compatibility
            return [{"url": t['url'], "status": t['message']} for t in handle.trackers()]
        except Exception as e:
            logger.error(f"Error getting torrent trackers: {e}")
            return []

    def get_torrent_peers(self, info_hash: bytes) -> List[Dict[str, Any]]:
        """Get peer list for a torrent."""
        with self._lock:
            if info_hash not in self.handles: 
                return []
            handle = self.handles[info_hash]
        
        try:
            peers = handle.get_peer_info()
            return [{
                "ip": p.ip, 
                "client": p.client.decode('utf-8', 'ignore'), 
                "down_speed": p.down_speed, 
                "up_speed": p.up_speed
            } for p in peers]
        except Exception as e:
            logger.error(f"Error getting torrent peers: {e}")
            return []

    def set_global_speed_limits(self, dl_limit_kib: int, ul_limit_kib: int) -> None:
        """Set global download and upload speed limits."""
        dl_limit_b = dl_limit_kib * 1024 if dl_limit_kib > 0 else 0
        ul_limit_b = ul_limit_kib * 1024 if ul_limit_kib > 0 else 0
        settings = {"download_rate_limit": dl_limit_b, "upload_rate_limit": ul_limit_b}
        self.ses.apply_settings(settings)
        persistence.save_setting('dl_limit', dl_limit_kib)
        persistence.save_setting('ul_limit', ul_limit_kib)
        logger.info(f"Set global limits: DL={dl_limit_kib} KiB/s, UL={ul_limit_kib} KiB/s")

    def set_file_priority(self, info_hash: bytes, file_index: int, priority: int) -> None:
        """Set priority for a specific file in a torrent."""
        with self._lock:
            if info_hash in self.handles:
                handle = self.handles[info_hash]
                handle.file_priority(file_index, priority)
                logger.debug(f"Set priority for file {file_index} in torrent {info_hash} to {priority}")

    def get_file_priorities(self, info_hash: bytes) -> List[int]:
        """Get file priorities for a torrent."""
        with self._lock:
            if info_hash in self.handles:
                return self.handles[info_hash].get_file_priorities()
        return []

    def set_torrent_download_limit(self, info_hash: bytes, limit_kib: int) -> None:
        """Set download limit for a specific torrent."""
        with self._lock:
            if info_hash in self.handles:
                limit_bytes = limit_kib * 1024 if limit_kib > 0 else -1
                self.handles[info_hash].set_download_limit(limit_bytes)
                logger.info(f"Set DL limit for {info_hash} to {limit_kib} KiB/s")

    def set_torrent_upload_limit(self, info_hash: bytes, limit_kib: int) -> None:
        """Set upload limit for a specific torrent."""
        with self._lock:
            if info_hash in self.handles:
                limit_bytes = limit_kib * 1024 if limit_kib > 0 else -1
                self.handles[info_hash].set_upload_limit(limit_bytes)
                logger.info(f"Set UL limit for {info_hash} to {limit_kib} KiB/s")