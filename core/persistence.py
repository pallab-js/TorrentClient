# core/persistence.py

import sqlite3
import os
from typing import List, Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)
DB_FILE = "session.db"

def init_db() -> None:
    """Initializes the database and creates tables if they don't exist."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # Create torrents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS torrents (
                    info_hash TEXT PRIMARY KEY,
                    save_path TEXT NOT NULL,
                    type TEXT NOT NULL,
                    source TEXT NOT NULL
                )
            ''')
            
            # Create settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            conn.commit()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise


def save_torrent_info(info_hash_hex: str, save_path: str, torrent_type: str, source: str) -> None:
    """Saves a torrent's info to the database."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                REPLACE INTO torrents (info_hash, save_path, type, source)
                VALUES (?, ?, ?, ?)
            ''', (info_hash_hex, save_path, torrent_type, source))
            conn.commit()
        logger.debug(f"Saved torrent info: {info_hash_hex}")
    except sqlite3.Error as e:
        logger.error(f"Error saving torrent info: {e}")
        raise

def load_torrents_info() -> List[Dict[str, Any]]:
    """Loads all torrent info from the database."""
    if not os.path.exists(DB_FILE):
        return []
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row 
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM torrents')
            torrents = [dict(row) for row in cursor.fetchall()]
        logger.debug(f"Loaded {len(torrents)} torrents from database")
        return torrents
    except sqlite3.Error as e:
        logger.error(f"Error loading torrents info: {e}")
        return []

def remove_torrent_info(info_hash_hex: str) -> None:
    """Removes a torrent's info from the database."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM torrents WHERE info_hash = ?', (info_hash_hex,))
            conn.commit()
        logger.debug(f"Removed torrent info: {info_hash_hex}")
    except sqlite3.Error as e:
        logger.error(f"Error removing torrent info: {e}")
        raise

def save_setting(key: str, value: Any) -> None:
    """Saves a setting to the database."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
            conn.commit()
        logger.debug(f"Saved setting: {key} = {value}")
    except sqlite3.Error as e:
        logger.error(f"Error saving setting: {e}")
        raise

def load_setting(key: str, default: Any = None) -> Any:
    """Loads a setting from the database."""
    if not os.path.exists(DB_FILE):
        return default
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
        result = row[0] if row else default
        logger.debug(f"Loaded setting: {key} = {result}")
        return result
    except sqlite3.Error as e:
        logger.error(f"Error loading setting: {e}")
        return default