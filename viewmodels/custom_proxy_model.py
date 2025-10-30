# viewmodels/custom_proxy_model.py

from PySide6.QtCore import QSortFilterProxyModel, Qt
from typing import Any

STATUS_MAP = {
    "Downloading": "downloading",
    "Seeding": "seeding",
    "Paused": "paused",
    "Completed": "finished",
    "Checking": "checking",
    "Active": ["downloading", "seeding", "checking"]
}

class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_filter = ""
        self._name_filter = ""

    def set_status_filter(self, status: str) -> None:
        self._status_filter = status
        self.invalidateFilter()

    def set_name_filter(self, text: str) -> None:
        self._name_filter = text
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:
        name_index = self.sourceModel().index(source_row, 0, source_parent)
        status_index = self.sourceModel().index(source_row, 6, source_parent) # Changed from 4 to 6
        
        name = self.sourceModel().data(name_index, Qt.DisplayRole)
        status = self.sourceModel().data(status_index, Qt.UserRole)

        name_match = True
        if self._name_filter:
            name_match = self._name_filter.lower() in name.lower()
        
        status_match = False
        if not self._status_filter or self._status_filter == "All":
            status_match = True
        elif self._status_filter == "Active":
            if status in STATUS_MAP["Active"]:
                status_match = True
        elif self._status_filter in STATUS_MAP:
            if status == STATUS_MAP[self._status_filter]:
                status_match = True
        
        return name_match and status_match