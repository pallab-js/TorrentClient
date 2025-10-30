# ui/main_window.py

import os
from functools import partial
from typing import Optional
from PySide6.QtWidgets import (QMainWindow, QToolBar, QTableView, QWidget,
                               QMessageBox, QSplitter,
                               QTabWidget, QAbstractItemView,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QComboBox, QVBoxLayout, QLineEdit, QListWidget,
                               QListWidgetItem, QInputDialog, QMenu)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Slot, Qt, QPoint
from viewmodels.custom_proxy_model import CustomSortFilterProxyModel
from .settings_dialog import SettingsDialog
from .add_torrent_dialog import AddTorrentDialog
from .progress_bar_delegate import ProgressBarDelegate
from core import persistence
from utils.config import config_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, torrent_model, engine_ref) -> None:
        super().__init__()
        self.setWindowTitle("torrent-downloader")
        self.setGeometry(100, 100, 1200, 700)
        
        self.torrent_model = torrent_model
        self.engine = engine_ref
        self.current_selected_hash: Optional[bytes] = None

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        add_torrent_action = QAction("Add Torrent", self)
        add_torrent_action.setShortcut(QKeySequence.Open)
        add_torrent_action.triggered.connect(self.open_add_torrent_dialog)
        toolbar.addAction(add_torrent_action)

        pause_action = QAction("Pause", self)
        pause_action.setShortcut(QKeySequence("P"))
        pause_action.triggered.connect(self.pause_selected_torrent)
        toolbar.addAction(pause_action)

        resume_action = QAction("Resume", self)
        resume_action.setShortcut(QKeySequence("R"))
        resume_action.triggered.connect(self.resume_selected_torrent)
        toolbar.addAction(resume_action)

        remove_action = QAction("Remove", self)
        remove_action.setShortcut(QKeySequence.Delete)
        remove_action.triggered.connect(self.remove_selected_torrent)
        toolbar.addAction(remove_action)
        
        settings_action = QAction("Settings", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.open_settings_dialog)
        toolbar.addAction(settings_action)

        # Global actions
        pause_all_action = QAction("Pause All", self)
        pause_all_action.setShortcut(QKeySequence("Ctrl+P"))
        pause_all_action.triggered.connect(self.pause_all)
        toolbar.addAction(pause_all_action)

        resume_all_action = QAction("Resume All", self)
        resume_all_action.setShortcut(QKeySequence("Ctrl+R"))
        resume_all_action.triggered.connect(self.resume_all)
        toolbar.addAction(resume_all_action)

        # Theme toggle
        theme_action = QAction("Toggle Theme", self)
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)

        self.proxy_model = CustomSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.torrent_model)
        self.proxy_model.setSortRole(Qt.UserRole)

        self.filter_list = QListWidget()
        self.filter_list.addItems(["All", "Active", "Downloading", "Seeding", "Completed", "Paused", "Checking"])
        self.filter_list.setCurrentRow(0)
        self.filter_list.currentItemChanged.connect(self.on_filter_changed)
        
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model) 
        
        progress_delegate = ProgressBarDelegate(self)
        self.table_view.setItemDelegateForColumn(1, progress_delegate)

        self.table_view.setSortingEnabled(True)
        self.table_view.sortByColumn(0, Qt.AscendingOrder)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_torrent_context_menu)
        
        # Set logical default column widths and stretch behaviors
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch) # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Progress
        header.resizeSection(2, 120) # DL Speed
        header.resizeSection(3, 120) # UL Speed
        header.resizeSection(4, 100) # ETA
        header.resizeSection(5, 80)  # Ratio
        header.resizeSection(6, 120) # Status

        self.details_tabs = QTabWidget()
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(3)
        self.files_table.setHorizontalHeaderLabels(["Name", "Size", "Priority"])
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.trackers_list = QTableWidget()
        self.trackers_list.setColumnCount(2)
        self.trackers_list.setHorizontalHeaderLabels(["URL", "Status"])
        self.trackers_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.trackers_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self.peers_table = QTableWidget()
        self.peers_table.setColumnCount(4)
        self.peers_table.setHorizontalHeaderLabels(["IP Address", "Client", "DL Speed", "UL Speed"])
        self.peers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.details_tabs.addTab(self.files_table, "Files")
        self.details_tabs.addTab(self.trackers_list, "Trackers")
        self.details_tabs.addTab(self.peers_table, "Peers")
        self.details_tabs.addTab(QWidget(), "Properties")

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Filter by name...")
        self.search_bar.textChanged.connect(self.proxy_model.set_name_filter)

        right_splitter = QSplitter(Qt.Horizontal)
        right_splitter.addWidget(self.table_view)
        right_splitter.addWidget(self.details_tabs)
        right_splitter.setSizes([700, 500])

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self.filter_list)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([150, 1050])

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        main_layout.addWidget(self.search_bar)
        main_layout.addWidget(main_splitter)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.table_view.selectionModel().selectionChanged.connect(self.update_details_panel)

        # Drag & Drop support
        self.table_view.setAcceptDrops(True)
        self.table_view.viewport().setAcceptDrops(True)
        self.setAcceptDrops(True)

    @Slot(QListWidgetItem)
    def on_filter_changed(self, current):
        if current:
            self.proxy_model.set_status_filter(current.text())

    @Slot(QPoint)
    def show_torrent_context_menu(self, pos):
        info_hash = self.get_selected_info_hash(show_warning=False)
        if not info_hash:
            return

        menu = QMenu(self)
        set_dl_action = menu.addAction("Set Download Limit...")
        set_ul_action = menu.addAction("Set Upload Limit...")
        
        set_dl_action.triggered.connect(lambda: self.set_selected_torrent_dl_limit(info_hash))
        set_ul_action.triggered.connect(lambda: self.set_selected_torrent_ul_limit(info_hash))

        global_pos = self.table_view.viewport().mapToGlobal(pos)
        menu.exec(global_pos)

    def set_selected_torrent_dl_limit(self, info_hash: bytes) -> None:
        limit, ok = QInputDialog.getInt(
            self, "Set Download Limit", "Limit (KiB/s, 0 for unlimited):", 
            value=0, min=0, max=100000)
        if ok:
            self.engine.set_torrent_download_limit(info_hash, limit)

    def set_selected_torrent_ul_limit(self, info_hash: bytes) -> None:
        limit, ok = QInputDialog.getInt(
            self, "Set Upload Limit", "Limit (KiB/s, 0 for unlimited):", 
            value=0, min=0, max=100000)
        if ok:
            self.engine.set_torrent_upload_limit(info_hash, limit)

    @Slot()
    def open_add_torrent_dialog(self):
        dialog = AddTorrentDialog(self)
        if dialog.exec():
            try:
                values = dialog.get_values()
                source, save_path = values['source'], values['save_path']
                
                if source.startswith("magnet:"):
                    result = self.engine.add_torrent_by_magnet(source, save_path)
                elif source.endswith(".torrent"):
                    result = self.engine.add_torrent_from_file(source, save_path)
                else:
                    QMessageBox.warning(self, "Invalid Source", "The source must be a valid magnet link or a path to a .torrent file.")
                    return
                
                if result is None:
                    QMessageBox.warning(self, "Error", "Failed to add torrent. Please check the source and try again.")
                    
            except ValueError as e:
                QMessageBox.warning(self, "Invalid Input", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    # Drag & Drop handlers
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        default_save_path = config_manager.get_config().download_path
        handled = False
        if event.mimeData().hasText():
            text = event.mimeData().text().strip()
            if text.startswith("magnet:"):
                self.engine.add_torrent_by_magnet(text, default_save_path)
                handled = True
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if local_path and local_path.endswith('.torrent'):
                    self.engine.add_torrent_from_file(local_path, default_save_path)
                    handled = True
        if handled:
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    @Slot()
    def update_details_panel(self) -> None:
        # Disconnect all existing signal connections to prevent memory leaks
        for row in range(self.files_table.rowCount()):
            widget = self.files_table.cellWidget(row, 2)
            if widget:
                try:
                    widget.currentIndexChanged.disconnect()
                except TypeError:
                    # Signal was already disconnected or never connected
                    pass
        
        # Clear all tables
        self.files_table.setRowCount(0)
        self.trackers_list.setRowCount(0)
        self.peers_table.setRowCount(0)
        
        info_hash = self.get_selected_info_hash(show_warning=False)
        self.current_selected_hash = info_hash
        if not info_hash: return

        files = self.engine.get_torrent_files(info_hash)
        if files:
            self.files_table.setRowCount(len(files))
            priorities = self.engine.get_file_priorities(info_hash)
            for i, file_info in enumerate(files):
                name_item = QTableWidgetItem(file_info['path'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                size_mb = file_info['size'] / (1024 * 1024)
                size_item = QTableWidgetItem(f"{size_mb:.2f} MB")
                size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
                priority_combo = QComboBox()
                priority_combo.addItems(["Don't Download", "Normal"])
                if priorities and i < len(priorities):
                    priority_combo.setCurrentIndex(1 if priorities[i] > 0 else 0)
                priority_combo.currentIndexChanged.connect(partial(self.on_file_priority_changed, file_index=i))
                self.files_table.setItem(i, 0, name_item)
                self.files_table.setItem(i, 1, size_item)
                self.files_table.setCellWidget(i, 2, priority_combo)
        
        trackers = self.engine.get_torrent_trackers(info_hash)
        self.trackers_list.setRowCount(len(trackers))
        for row, tracker in enumerate(trackers):
            self.trackers_list.setItem(row, 0, QTableWidgetItem(tracker['url']))
            self.trackers_list.setItem(row, 1, QTableWidgetItem(tracker['status']))

        peers = self.engine.get_torrent_peers(info_hash)
        self.peers_table.setRowCount(len(peers))
        for row, peer in enumerate(peers):
            self.peers_table.setItem(row, 0, QTableWidgetItem(f"{peer['ip'][0]}:{peer['ip'][1]}"))
            self.peers_table.setItem(row, 1, QTableWidgetItem(peer['client']))
            self.peers_table.setItem(row, 2, QTableWidgetItem(f"{peer['down_speed'] / 1024:.2f} KiB/s"))
            self.peers_table.setItem(row, 3, QTableWidgetItem(f"{peer['up_speed'] / 1024:.2f} KiB/s"))

    @Slot(int)
    def on_file_priority_changed(self, combo_index: int, file_index: int) -> None:
        if self.current_selected_hash:
            priority = 1 if combo_index == 1 else 0
            self.engine.set_file_priority(self.current_selected_hash, file_index, priority)
            
    def get_selected_info_hash(self, show_warning: bool = True):
        selected_indexes_proxy = self.table_view.selectionModel().selectedRows()
        if not selected_indexes_proxy:
            if show_warning: QMessageBox.warning(self, "No Selection", "Please select a torrent first.")
            return None
        source_index = self.proxy_model.mapToSource(selected_indexes_proxy[0])
        return self.torrent_model.get_info_hash_for_row(source_index.row())

    @Slot()
    def pause_selected_torrent(self) -> None:
        info_hash = self.get_selected_info_hash()
        if info_hash: self.engine.pause_torrent(info_hash)

    @Slot()
    def resume_selected_torrent(self) -> None:
        info_hash = self.get_selected_info_hash()
        if info_hash: self.engine.resume_torrent(info_hash)

    @Slot()
    def remove_selected_torrent(self) -> None:
        info_hash = self.get_selected_info_hash()
        if info_hash:
            self.engine.remove_torrent(info_hash, remove_data=False)
            self.torrent_model.remove_torrent(info_hash)

    @Slot()
    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self)
        dl_limit = int(persistence.load_setting('dl_limit', 0))
        ul_limit = int(persistence.load_setting('ul_limit', 0))
        dialog.set_values(dl_limit, ul_limit)
        if dialog.exec():
            values = dialog.get_values()
            self.engine.set_global_speed_limits(values["dl_limit"], values["ul_limit"])

    # Global pause/resume
    def pause_all(self) -> None:
        for i in range(self.torrent_model.rowCount()):
            info_hash = self.torrent_model.get_info_hash_for_row(i)
            if info_hash:
                self.engine.pause_torrent(info_hash)

    def resume_all(self) -> None:
        for i in range(self.torrent_model.rowCount()):
            info_hash = self.torrent_model.get_info_hash_for_row(i)
            if info_hash:
                self.engine.resume_torrent(info_hash)

    # Theme toggle
    def toggle_theme(self) -> None:
        cfg = config_manager.get_config()
        new_theme = 'light' if cfg.theme == 'dark' else 'dark'
        config_manager.update_config(theme=new_theme)
        # Re-apply stylesheet
        if new_theme == 'dark':
            qss_path = "assets/dark_theme.qss"
            from PySide6.QtCore import QFile, QTextStream
            qss_file = QFile(qss_path)
            if qss_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(qss_file)
                self.window().setStyleSheet(stream.readAll())
        else:
            self.window().setStyleSheet("")