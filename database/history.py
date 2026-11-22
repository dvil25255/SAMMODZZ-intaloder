import logging
from database.db import get_conn
logger = logging.getLogger("SAMMODZZ.history")

def add_history(media_id, media_url, caption, slot, status, error=None, source_username=""):
    with get_conn() as conn:
        conn.execute("INSERT INTO history (media_id, media_url, source_username, caption, slot, status, error) VALUES (?, ?, ?, ?, ?, ?, ?)", (media_id, media_url, source_username, caption, slot, status, error))
    logger.info("History added: %s (%s)", media_id, status)

def get_recent_history(limit=10):
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

def count_today_published():
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM history WHERE status='success' AND DATE(created_at)=DATE('now')").fetchone()
    return row["n"] if row else 0
