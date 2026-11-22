import logging
from database.db import get_conn
logger = logging.getLogger("SAMMODZZ.upload")

def next_queued():
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM queue WHERE status='queued' ORDER BY id ASC LIMIT 1").fetchone()
    return dict(row) if row else None

def count_queued():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM queue WHERE status='queued'").fetchone()["n"]
