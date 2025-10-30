# viewmodels/torrent_list_model.py

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import Any, Dict, List, Optional
import math

def format_eta(seconds: float) -> str:
    """Formats seconds into a human-readable ETA string."""
    if seconds == 0 or seconds == float('inf') or math.isinf(seconds):
        return "∞"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{int(hours)}h {int(minutes)}m"
    else:
        return f"{int(minutes)}m {int(seconds % 60)}s"

class TorrentListModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.torrents: List[Dict[str, Any]] = []
        self.headers: List[str] = ["Name", "Progress", "DL Speed", "UL Speed", "ETA", "Ratio", "Status"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.torrents)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[Any]:
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        torrent = self.torrents[row]

        if role == Qt.UserRole:
            if col == 1: return torrent.get('progress', 0)
            if col == 2: return torrent.get('download_rate', 0)
            if col == 3: return torrent.get('upload_rate', 0)
            if col == 4: return torrent.get('eta', float('inf')) 
            if col == 5: return torrent.get('ratio', 0.0)
            if col == 6: return torrent.get('state_str', 'N/A')

        if role == Qt.DisplayRole:
            if col == 0:
                return torrent.get('name', 'Fetching...')
            elif col == 1:
                progress = torrent.get('progress', 0) * 100
                return f"{progress:.2f}%"
            elif col == 2:
                speed = torrent.get('download_rate', 0) / 1024
                return f"{speed:.2f} KiB/s"
            elif col == 3:
                speed = torrent.get('upload_rate', 0) / 1024
                return f"{speed:.2f} KiB/s"
            elif col == 4:
                return format_eta(torrent.get('eta', float('inf')))
            elif col == 5:
                return f"{torrent.get('ratio', 0.0):.2f}"
            elif col == 6:
                return torrent.get('state_str', 'N/A')
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Optional[str]:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def update_torrent_status(self, status_update: Dict[str, Any]) -> None:
        info_hash = status_update['info_hash']
        
        for i, torrent in enumerate(self.torrents):
            if torrent['info_hash'] == info_hash:
                self.torrents[i].update(status_update)
                self.dataChanged.emit(self.index(i, 0), self.index(i, self.columnCount() - 1))
                return

        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.torrents.append(status_update)
        self.endInsertRows()
        
    def get_info_hash_for_row(self, row: int):
        if 0 <= row < len(self.torrents):
            return self.torrents[row]['info_hash']
        return None

    def remove_torrent(self, info_hash) -> None:
        """Finds and removes a torrent by its info_hash."""
        for i, torrent in enumerate(self.torrents):
            if torrent['info_hash'] == info_hash:
                self.beginRemoveRows(QModelIndex(), i, i)
                self.torrents.pop(i)
                self.endRemoveRows()
                return

    def bulk_update(self, updates: List[Dict[str, Any]]) -> None:
        """Apply many status updates in one refresh to minimize signals."""
        if not updates:
            return
        self.layoutAboutToBeChanged.emit()
        info_hash_to_index = {t['info_hash']: idx for idx, t in enumerate(self.torrents)}
        for status_update in updates:
            info_hash = status_update['info_hash']
            idx = info_hash_to_index.get(info_hash)
            if idx is not None:
                self.torrents[idx].update(status_update)
            else:
                self.torrents.append(status_update)
        self.layoutChanged.emit()