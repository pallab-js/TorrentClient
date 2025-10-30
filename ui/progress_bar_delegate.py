# ui/progress_bar_delegate.py

# MODIFIED: Import QStyleOptionProgressBar directly
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QApplication, QStyleOptionProgressBar
from PySide6.QtCore import Qt

class ProgressBarDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        progress_float = index.data(Qt.UserRole)

        if not isinstance(progress_float, (float, int)):
            super().paint(painter, option, index)
            return

        progress_percent = int(progress_float * 100)

        # MODIFIED: Create an instance of the imported class
        progress_bar_option = QStyleOptionProgressBar()
        progress_bar_option.rect = option.rect
        progress_bar_option.minimum = 0
        progress_bar_option.maximum = 100
        progress_bar_option.progress = progress_percent
        progress_bar_option.text = f"{progress_percent}%"
        progress_bar_option.textVisible = True
        progress_bar_option.textAlignment = Qt.AlignCenter

        QApplication.style().drawControl(
            QStyle.ControlElement.CE_ProgressBar,
            progress_bar_option,
            painter,
        )