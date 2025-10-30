import os
from pathlib import Path


def test_config_defaults_and_dirs(tmp_path, monkeypatch):
    # Redirect working directory to temp to avoid polluting project
    monkeypatch.chdir(tmp_path)

    from utils.config import ConfigManager
    cm = ConfigManager(config_file=str(tmp_path / 'config' / 'settings.json'))
    cfg = cm.get_config()

    # Defaults
    assert cfg.download_path == 'downloads'
    assert cfg.listen_port == 6881

    # Directories created
    assert Path('downloads').exists()
    assert Path('config').exists()
    assert Path('logs').exists()

    # Save and reload
    cm.update_config(global_download_limit=123)
    cm2 = ConfigManager(config_file=str(tmp_path / 'config' / 'settings.json'))
    assert cm2.get_config().global_download_limit == 123
