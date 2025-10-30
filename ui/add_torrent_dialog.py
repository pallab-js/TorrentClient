# ui/add_torrent_dialog.py

import os
from typing import Dict
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QPushButton, QDialogButtonBox, QHBoxLayout,
                               QFileDialog, QLabel)
from PySide6.QtCore import Slot

class AddTorrentDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add New Torrent")
        self.setMinimumWidth(500)

        # Main layout
        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Source input (Magnet link or file path)
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Magnet link or path to .torrent file")
        
        source_browse_btn = QPushButton("Browse File...")
        source_browse_btn.clicked.connect(self.browse_torrent_file)
        
        source_layout = QHBoxLayout()
        source_layout.addWidget(self.source_edit)
        source_layout.addWidget(source_browse_btn)

        # Save path input
        self.save_path_edit = QLineEdit()
        default_save_path = os.path.join(os.getcwd(), 'downloads')
        if not os.path.exists(default_save_path):
            os.makedirs(default_save_path)
        self.save_path_edit.setText(default_save_path)

        save_browse_btn = QPushButton("Browse Path...")
        save_browse_btn.clicked.connect(self.browse_save_path)

        save_layout = QHBoxLayout()
        save_layout.addWidget(self.save_path_edit)
        save_layout.addWidget(save_browse_btn)

        form_layout.addRow(QLabel("Source:"), source_layout)
        form_layout.addRow(QLabel("Save Location:"), save_layout)

        self.layout.addLayout(form_layout)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.layout.addWidget(self.button_box)

    @Slot()
    def browse_torrent_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Torrent File", "", "Torrent Files (*.torrent)")
        if file_path:
            self.source_edit.setText(file_path)

    @Slot()
    def browse_save_path(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if dir_path:
            self.save_path_edit.setText(dir_path)

    def get_values(self) -> Dict[str, str]:
        source = self.source_edit.text().strip()
        save_path = self.save_path_edit.text().strip()
        
        # Basic validation
        if not source:
            raise ValueError("Source cannot be empty")
        if not save_path:
            raise ValueError("Save path cannot be empty")
        
        # Validate magnet link format
        if source.startswith("magnet:"):
            if "xt=urn:btih:" not in source:
                raise ValueError("Invalid magnet link format")
        
        # Validate torrent file
        elif source.endswith(".torrent"):
            if not os.path.exists(source):
                raise ValueError("Torrent file does not exist")
        
        return {
            "source": source,
            "save_path": save_path
        }