import sqlite3
import logging
from contextlib import contextmanager
from config import DB_PATH
logger = logging.getLogger("SAMMODZZ.db")

def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_url TEXT NOT NULL DEFAULT '',
            source_username TEXT NOT NULL DEFAULT '',
            media_index INTEGER NOT NULL DEFAULT 0,
            post_type TEXT NOT NULL DEFAULT 'photo',
            caption TEXT NOT NULL DEFAULT '',
            is_video INTEGER NOT NULL DEFAULT 0,
            url_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            published_at TEXT
        );
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT NOT NULL,
            media_url TEXT NOT NULL DEFAULT '',
            source_username TEXT NOT NULL DEFAULT '',
            caption TEXT NOT NULL DEFAULT '',
            slot TEXT,
            status TEXT NOT NULL DEFAULT 'success',
            error TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_queue_status ON queue(status);
        CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at);
        """)
    logger.info("DB initialized at %s", DB_PATH)

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
