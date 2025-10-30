# ui/settings_dialog.py

from typing import Dict
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel,
                               QSpinBox, QDialogButtonBox)

class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(350) # Set a comfortable minimum width

        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Download limit setting (0 for unlimited)
        self.dl_limit_spinbox = QSpinBox()
        self.dl_limit_spinbox.setRange(0, 100000) # 0 to 100,000 KiB/s
        self.dl_limit_spinbox.setSuffix(" KiB/s")
        self.dl_limit_spinbox.setSpecialValueText("Unlimited")
        
        # Upload limit setting (0 for unlimited)
        self.ul_limit_spinbox = QSpinBox()
        self.ul_limit_spinbox.setRange(0, 100000)
        self.ul_limit_spinbox.setSuffix(" KiB/s")
        self.ul_limit_spinbox.setSpecialValueText("Unlimited")

        form_layout.addRow(QLabel("Global Download Limit:"), self.dl_limit_spinbox)
        form_layout.addRow(QLabel("Global Upload Limit:"), self.ul_limit_spinbox)
        
        self.layout.addLayout(form_layout)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.layout.addWidget(self.button_box)

    def get_values(self) -> Dict[str, int]:
        """Returns the configured values from the dialog."""
        return {
            "dl_limit": self.dl_limit_spinbox.value(),
            "ul_limit": self.ul_limit_spinbox.value(),
        }

    def set_values(self, dl_limit: int, ul_limit: int) -> None:
        """Sets the initial values of the spinboxes."""
        self.dl_limit_spinbox.setValue(dl_limit)
        self.ul_limit_spinbox.setValue(ul_limit)