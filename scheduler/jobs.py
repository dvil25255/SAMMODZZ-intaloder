import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import POST_SLOTS, TIMEZONE, load_settings, SOURCE_ACCOUNTS, AUTO_FETCH_COUNT
from database.db import get_conn
from database.history import add_history, count_today_published
from instagram.api import InstagramAPI
from instagram.publisher import publish_from_pk
from services.auto_source import refill_all
logger = logging.getLogger("SAMMODZZ.scheduler")
_scheduler = None

async def start_scheduler(application):
    global _scheduler
    if _scheduler is not None: return
    _scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    for slot in POST_SLOTS:
        hh, mm = slot.split(":")
        rh = int(hh); rm = int(mm) - 15
        if rm < 0: rm += 60; rh = (rh - 1) % 24
        _scheduler.add_job(refill_job, CronTrigger(hour=rh, minute=rm, timezone=TIMEZONE), id="refill_" + slot, replace_existing=True)
        _scheduler.add_job(run_slot, CronTrigger(hour=int(hh), minute=int(mm), timezone=TIMEZONE), args=[application, slot], id="slot_" + slot, replace_existing=True)
    _scheduler.start()
    logger.info("Scheduler started.")

async def stop_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False); _scheduler = None

async def refill_job():
    if not SOURCE_ACCOUNTS: return
    try:
        api = InstagramAPI()
        n = refill_all(api, SOURCE_ACCOUNTS, AUTO_FETCH_COUNT)
        logger.info("Refill added %d", n)
    except Exception:
        logger.exception("Refill failed")

async def run_slot(application, slot):
    s = load_settings()
    if s.get("paused"): return
    if count_today_published() >= s.get("daily_target", 7): return
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM queue WHERE status='queued' ORDER BY id ASC LIMIT 1").fetchone()
        if not row:
            await refill_job()
            with get_conn() as conn:
                row = conn.execute("SELECT * FROM queue WHERE status='queued' ORDER BY id ASC LIMIT 1").fetchone()
            if not row: return
        conn.execute("UPDATE queue SET status='publishing' WHERE id=?", (row["id"],))
    item = dict(row)
    api = InstagramAPI()
    try:
        result = publish_from_pk(api, item["media_pk"], item["caption"], item["post_type"])
        add_history(result["media_id"], item["media_url"], item["caption"], slot, "success", source_username=item["source_username"])
        with get_conn() as conn:
            conn.execute("UPDATE queue SET status='published', published_at=CURRENT_TIMESTAMP WHERE id=?", (item["id"],))
        await _notify(application, "✅ Published at %s\n@%s → %s" % (slot, item["source_username"], result["media_id"]))
    except Exception as e:
        logger.exception("Publish failed %s", slot)
        add_history("", item["media_url"], item["caption"], slot, "failed", str(e), source_username=item["source_username"])
        with get_conn() as conn:
            conn.execute("UPDATE queue SET status='failed' WHERE id=?", (item["id"],))
        await _notify(application, "❌ Failed at %s: %s" % (slot, e))

async def _notify(application, text):
    from services.notifications import broadcast
    await broadcast(application, text)
