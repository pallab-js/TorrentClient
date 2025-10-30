# torrent-downloader

![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A modern, professional BitTorrent client with a sleek dark UI, built with Python and PySide6.

---

## Key Features

* **Modern, Multi-Pane UI**: An intuitive interface with a filterable, searchable, and sortable torrent list.
* **Add Torrents Easily**: Add via `.torrent` files, magnet links, or drag & drop onto the window.
* **Complete Torrent Control**: Pause, resume, and remove torrents individually.
* **Fine-Grained Controls**: Set global and per-torrent speed limits and prioritize files within a torrent.
* **Detailed Information**: View detailed information about trackers, peers, and files for each torrent.
* **Persistent Sessions**: Remembers your torrents and settings between restarts.
* **Polished UX**: Dark/light theme toggle, keyboard shortcuts, and progress bars for at-a-glance status.
* **Bandwidth Scheduler**: Optional quiet hours with automatic speed limits.
* **Secure Paths**: Download locations are constrained under a configured base folder.

## Tech Stack

* **Language**: Python 3.9+
* **GUI Framework**: PySide6 (the official Qt for Python bindings)
* **Torrent Engine**: `python-libtorrent`
* **Database**: SQLite for session and settings persistence
* **Testing**: `pytest` and `pytest-mock`
 

## Getting Started

### Prerequisites

* Python 3.10 or newer
* `pip` and `venv`

### Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd torrent-downloader
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # On macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate

    # On Windows
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install dependencies from `requirements.txt`:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python3 main.py
    ```

### Configuration

Settings are persisted to `config/settings.json` and managed at runtime. Defaults are created on first run.

Key options:

- `download_path`: Base directory for all downloads. All save paths are sanitized to be under this directory.
- `theme`: `dark` or `light`. You can toggle in-app with Ctrl+T.
- `global_download_limit`, `global_upload_limit`: KiB/s, 0 for unlimited.
- `bandwidth_schedules`: Optional quiet hours for automatic limits.

Example `config/settings.json`:

```json
{
  "download_path": "downloads",
  "theme": "dark",
  "global_download_limit": 0,
  "global_upload_limit": 0,
  "bandwidth_schedules": [
    { "start": "23:00", "end": "07:00", "dl": 200, "ul": 50 }
  ]
}
```

### Keyboard Shortcuts

- Ctrl+O: Add torrent
- P: Pause selected
- R: Resume selected
- Delete: Remove selected
- Ctrl+P: Pause all
- Ctrl+R: Resume all
- Ctrl+,: Settings
- Ctrl+T: Toggle theme

## Testing

The project includes a comprehensive test suite for its core logic and data models. To run the tests:

```bash
pytest -v
```

 
