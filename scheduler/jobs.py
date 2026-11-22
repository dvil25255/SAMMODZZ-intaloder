import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import POST_SLOTS, TIMEZONE, load_settings
from database.db import get_conn
from database.history import add_history, count_today_published
from instagram.api import InstagramAPI
from instagram.publisher import publish_from_source, publish_from_file
logger = logging.getLogger("SAMMODZZ.scheduler")
_scheduler = None

async def start_scheduler(application):
    global _scheduler
    if _scheduler is not None: return
    _scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    for slot in POST_SLOTS:
        hh, mm = slot.split(":")
        _scheduler.add_job(run_slot, CronTrigger(hour=int(hh), minute=int(mm), timezone=TIMEZONE), args=[application, slot], id="slot_" + slot, replace_existing=True)
    _scheduler.start()
    logger.info("Scheduler started.")

async def stop_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped.")

async def run_slot(application, slot):
    s = load_settings()
    if s.get("paused"):
        return
    if count_today_published() >= s.get("daily_target", 7):
        return
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM queue WHERE status='queued' ORDER BY id ASC LIMIT 1").fetchone()
        if not row: return
        conn.execute("UPDATE queue SET status='publishing' WHERE id=?", (row["id"],))
    item = dict(row)
    api = InstagramAPI()
    try:
        if item["source_username"]:
            result = publish_from_source(api, item["source_username"], item["media_index"], item["caption"], item["post_type"])
        else:
            result = publish_from_file(api, item["media_url"], item["caption"], item["post_type"])
        add_history(result["media_id"], item["media_url"], item["caption"], slot, "success", source_username=item["source_username"])
        with get_conn() as conn:
            conn.execute("UPDATE queue SET status='published', published_at=CURRENT_TIMESTAMP WHERE id=?", (item["id"],))
        await _notify(application, "✅ Published at %s\nmedia_id: `%s`" % (slot, result["media_id"]))
    except Exception as e:
        logger.exception("Publish failed at %s", slot)
        add_history("", item["media_url"], item["caption"], slot, "failed", str(e), source_username=item["source_username"])
        with get_conn() as conn:
            conn.execute("UPDATE queue SET status='failed' WHERE id=?", (item["id"],))
        await _notify(application, "❌ Publish failed at %s: %s" % (slot, e))

async def _notify(application, text):
    from services.notifications import broadcast
    await broadcast(application, text)
