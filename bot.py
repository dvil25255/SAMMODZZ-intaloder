import logging
from telegram.ext import Application
from telegram_bot.handlers import register_handlers
from scheduler.jobs import start_scheduler, stop_scheduler

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)
logger = logging.getLogger("SAMMODZZ")
from config import BOT_TOKEN

async def post_init(application):
    logger.info("SAMMODZZ Bot started.")
    try:
        await start_scheduler(application)
        logger.info("Scheduler started.")
    except Exception:
        logger.exception("Scheduler startup failed.")

async def post_shutdown(application):
    try:
        await stop_scheduler()
    except Exception:
        logger.exception("Scheduler shutdown failed.")

def main():
    app = (Application.builder().token(BOT_TOKEN).post_init(post_init).post_shutdown(post_shutdown).build())
    register_handlers(app)
    app.run_polling(allowed_updates=["message", "callback_query"], drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Stopped manually.")
    except Exception:
        logger.exception("Critical error.")
        raise
