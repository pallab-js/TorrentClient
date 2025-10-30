# main.py

import sys
from queue import Queue
import libtorrent as lt
import math
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QFile, QTextStream

from core.torrent_engine import TorrentEngine
from ui.main_window import MainWindow
from viewmodels.torrent_list_model import TorrentListModel
from utils.logger import get_logger
from utils.config import config_manager
from utils.scheduler import pick_limits

logger = get_logger(__name__)

ALERT_TYPES = {
    lt.torrent_status.checking_files: 'checking',
    lt.torrent_status.downloading_metadata: 'metadata',
    lt.torrent_status.downloading: 'downloading',
    lt.torrent_status.finished: 'finished',
    lt.torrent_status.seeding: 'seeding',
    lt.torrent_status.allocating: 'allocating',
    lt.torrent_status.checking_resume_data: 'checking resume'
}

class TorrentApplication(QApplication):
    def __init__(self, sys_argv: list) -> None:
        super(TorrentApplication, self).__init__(sys_argv)
        
        logger.info("Starting Torrent Application")
        
        # Load configuration
        self.config = config_manager.get_config()
        
        # Load theme
        self._load_theme()
        
        # Initialize components
        self.alert_queue: Queue = Queue()
        self.engine: TorrentEngine = TorrentEngine(self.alert_queue)
        self.engine.daemon = True
        self.engine.start()

        self.torrent_model = TorrentListModel()

        self.main_window = MainWindow(self.torrent_model, self.engine)
        self.main_window.resize(self.config.window_width, self.config.window_height)
        self.main_window.show()

        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self.process_alerts)
        self.alert_timer.start(500)
        
        # Scheduler timer (every 60s)
        self.scheduler_timer = QTimer(self)
        self.scheduler_timer.timeout.connect(self.apply_bandwidth_schedule)
        self.scheduler_timer.start(60_000)

        logger.info("Torrent Application initialized successfully")
    
    def _load_theme(self) -> None:
        """Load the application theme based on configuration."""
        theme = self.config.theme
        if theme == 'dark':
            qss_path = "assets/dark_theme.qss"
            qss_file = QFile(qss_path)
            if qss_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(qss_file)
                self.setStyleSheet(stream.readAll())
                logger.info("Dark theme loaded successfully")
            else:
                logger.warning(f"Could not load stylesheet from {qss_path}: {qss_file.errorString()}")
        else:
            # Light theme: clear stylesheet
            self.setStyleSheet("")
            logger.info("Light theme loaded (default Qt style)")
    
    def shutdown(self) -> None:
        """Gracefully shutdown the application."""
        logger.info("Shutting down Torrent Application")
        self.engine.shutdown()
        config_manager.save_config()
        logger.info("Torrent Application shutdown complete")

    def process_alerts(self) -> None:
        """Process libtorrent alerts and update the UI."""
        while not self.alert_queue.empty():
            alert = self.alert_queue.get()
            
            try:
                if isinstance(alert, lt.torrent_finished_alert):
                    logger.info(f"Torrent finished: {alert.torrent_name()}")
                
                elif isinstance(alert, lt.state_update_alert):
                    updates = []
                    for status in alert.status:
                        # Logic to correctly identify the 'paused' state
                        state_str = ALERT_TYPES.get(status.state, 'unknown')
                        if hasattr(lt, 'torrent_flags') and status.flags & lt.torrent_flags.paused and state_str not in ['seeding', 'finished']:
                            state_str = 'paused'

                        bytes_left = status.total_wanted - status.total_done
                        eta_seconds = (bytes_left / status.download_rate) if status.download_rate > 0 else float('inf')
                        ratio = status.total_upload / status.total_done if status.total_done > 0 else 0.0
                        
                        updates.append({
                            'info_hash': status.info_hash,
                            'name': status.name,
                            'progress': status.progress,
                            'download_rate': status.download_rate,
                            'upload_rate': status.upload_rate,
                            'state_str': state_str,
                            'eta': eta_seconds,
                            'ratio': ratio
                        })
                    self.torrent_model.bulk_update(updates)
            except Exception as e:
                logger.error(f"Error processing alert: {e}")

    def apply_bandwidth_schedule(self) -> None:
        cfg = config_manager.get_config()
        entry = pick_limits(None, cfg.bandwidth_schedules)
        if entry:
            self.engine.set_global_speed_limits(entry.dl, entry.ul)
        else:
            # apply configured defaults
            self.engine.set_global_speed_limits(cfg.global_download_limit, cfg.global_upload_limit)

if __name__ == "__main__":
    try:
        app = TorrentApplication(sys.argv)
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}")
        sys.exit(1)
    finally:
        if 'app' in locals():
            app.shutdown()