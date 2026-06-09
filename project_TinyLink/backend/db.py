"""SQLite connection + schema bootstrap.

One file (tinylink.db). One table (links). Connection is shared across
threads since FastAPI's default thread pool may dispatch handlers from
different threads -- check_same_thread=False allows that, and we serialise
writes via SQLite's own lock.
"""

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("TINYLINK_DB", Path(__file__).parent / "tinylink.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    long_url  TEXT NOT NULL,
    created   DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
