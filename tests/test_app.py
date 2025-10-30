# tests/test_app.py

import pytest
import os
import sys
from unittest.mock import MagicMock

# Ensure the test script can find the project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Qt components needed for tests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# Import all the project classes we need to test
from core import persistence
from viewmodels.torrent_list_model import TorrentListModel
from viewmodels.custom_proxy_model import CustomSortFilterProxyModel
from ui.main_window import MainWindow

# --- Fixtures: Reusable setup code for tests ---

@pytest.fixture(scope="session")
def qapp():
    """Fixture to create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def temp_db(tmp_path):
    """Fixture to create and clean up a temporary database for each test function."""
    db_path = tmp_path / "test_session.db"
    original_db_file = persistence.DB_FILE
    persistence.DB_FILE = db_path
    persistence.init_db()
    yield db_path
    persistence.DB_FILE = original_db_file

@pytest.fixture
def mock_engine(mocker):
    """Fixture to create a mocked version of the TorrentEngine."""
    return mocker.MagicMock()

@pytest.fixture
def prefilled_model():
    """Fixture to provide a TorrentListModel pre-filled with diverse data."""
    model = TorrentListModel()
    # MODIFIED: Use simple strings for info_hash in tests.
    # Our application code treats them as comparable keys, so strings are sufficient
    # and avoid libtorrent versioning issues.
    torrents = [
        {'info_hash': 'hash_ubuntu', 'name': 'ubuntu-distro.iso', 'state_str': 'seeding'},
        {'info_hash': 'hash_arch', 'name': 'arch-linux.iso', 'state_str': 'downloading'},
        {'info_hash': 'hash_fedora', 'name': 'fedora-workstation', 'state_str': 'checking'},
    ]
    for t in torrents:
        model.update_torrent_status(t)
    return model

# --- Test Classes ---

class TestPersistence:
    """Tests for the database persistence layer."""
    def test_settings_save_load(self, temp_db):
        persistence.save_setting('dl_limit', 500)
        assert persistence.load_setting('dl_limit') == '500'

    def test_torrents_save_load_remove(self, temp_db):
        assert persistence.load_torrents_info() == []
        persistence.save_torrent_info('hash1', '/path', 'magnet', 'magnet:hash1')
        persistence.save_torrent_info('hash2', '/path2', 'file', '/torrents/file.torrent')
        
        loaded = persistence.load_torrents_info()
        assert len(loaded) == 2
        assert loaded[0]['info_hash'] == 'hash1'
        
        persistence.remove_torrent_info('hash1')
        loaded = persistence.load_torrents_info()
        assert len(loaded) == 1
        assert loaded[0]['info_hash'] == 'hash2'

class TestTorrentListModel:
    """Tests for the main data model."""
    def test_initial_state(self):
        model = TorrentListModel()
        assert model.rowCount() == 0

    def test_add_update_remove(self, prefilled_model):
        assert prefilled_model.rowCount() == 3
        
        prefilled_model.update_torrent_status({'info_hash': 'hash_ubuntu', 'name': 'ubuntu-updated.iso'})
        assert prefilled_model.rowCount() == 3
        assert prefilled_model.data(prefilled_model.index(0, 0)) == 'ubuntu-updated.iso'
        
        prefilled_model.remove_torrent('hash_arch')
        assert prefilled_model.rowCount() == 2
        assert prefilled_model.data(prefilled_model.index(0, 0)) == 'ubuntu-updated.iso'
        assert prefilled_model.data(prefilled_model.index(1, 0)) == 'fedora-workstation'

class TestCustomProxyModel:
    """Tests for the sorting and filtering proxy model."""
    @pytest.fixture
    def proxy_model(self, prefilled_model):
        proxy = CustomSortFilterProxyModel()
        proxy.setSourceModel(prefilled_model)
        return proxy

    def test_name_filter(self, proxy_model):
        proxy_model.set_name_filter("linux")
        assert proxy_model.rowCount() == 1

    def test_status_filter(self, proxy_model):
        proxy_model.set_status_filter("Seeding")
        assert proxy_model.rowCount() == 1
        
    def test_active_status_filter(self, proxy_model):
        proxy_model.set_status_filter("Active")
        assert proxy_model.rowCount() == 3
        
    def test_combined_filter(self, proxy_model):
        proxy_model.set_name_filter("iso")
        proxy_model.set_status_filter("Downloading")
        assert proxy_model.rowCount() == 1

class TestApplicationLogic:
    """Tests the interaction logic within the MainWindow, using a mocked engine."""
    @pytest.fixture
    def main_window(self, qapp, prefilled_model, mock_engine):
        window = MainWindow(prefilled_model, mock_engine)
        return window

    def test_pause_action(self, main_window, mock_engine):
        main_window.table_view.selectRow(0)
        main_window.pause_selected_torrent()
        mock_engine.pause_torrent.assert_called_once_with('hash_ubuntu')

    def test_remove_action(self, main_window, mock_engine):
        main_window.table_view.selectRow(1)
        main_window.remove_selected_torrent()
        mock_engine.remove_torrent.assert_called_once_with('hash_arch', remove_data=False)
        assert main_window.torrent_model.rowCount() == 2

    def test_per_torrent_speed_limit(self, main_window, mock_engine, mocker):
        mocker.patch('PySide6.QtWidgets.QInputDialog.getInt', return_value=(1024, True))
        info_hash = 'hash_fedora'
        main_window.set_selected_torrent_dl_limit(info_hash)
        mock_engine.set_torrent_download_limit.assert_called_once_with(info_hash, 1024)