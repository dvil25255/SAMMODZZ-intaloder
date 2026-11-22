import logging
from config import OWNER_CHAT_ID
logger = logging.getLogger("SAMMODZZ.notify")

async def broadcast(application, text):
    if not OWNER_CHAT_ID:
        logger.info("No OWNER_CHAT_ID; skip: %s", text)
        return
    try:
        await application.bot.send_message(chat_id=int(OWNER_CHAT_ID), text=text, parse_mode="Markdown")
    except Exception:
        logger.exception("Notification failed.")
