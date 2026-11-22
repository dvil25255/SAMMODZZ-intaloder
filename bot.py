<<<<<<< HEAD
import os
import time
import random
import asyncio
import requests
import json
import traceback
from datetime import datetime
from instagrapi import Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters
=======
import logging
from telegram.ext import Application
from telegram_bot.handlers import register_handlers
from scheduler.jobs import start_scheduler, stop_scheduler
>>>>>>> ca6d2da (Switch to instagrapi sessionid login, add session_login and publisher)

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)
logger = logging.getLogger("SAMMODZZ")
from config import BOT_TOKEN

async def post_init(application):
    logger.info("SAMMODZZ Bot started.")
    try:
<<<<<<< HEAD
        cl = Client()
        if BOT_STATE["proxy"]: cl.set_proxy(BOT_STATE["proxy"])
        cl.login(BOT_STATE["username"], BOT_STATE["password"])
        cl.dump_settings(CONFIG_FILE)
        BOT_STATE["target2"] = BOT_STATE["username"]
        await msg.edit_text(f"✅ Login successful as `@{BOT_STATE['target2']}`!\n\nStep 3: Source account ka username batao:", parse_mode='Markdown')
        return WAITING_TARGET
    except Exception as e:
        traceback.print_exc()
        if "challenge_required" in str(e).lower():
            await msg.edit_text("⚠️ **Instagram needs OTP!**\n\nOTP code yahan bhejo:", parse_mode='Markdown')
            return WAITING_OTP
        else:
            await msg.edit_text(f"❌ Login failed: {str(e)[:50]}\n\nTry Session ID method with `/start`.")
            return ConversationHandler.END
=======
        await start_scheduler(application)
        logger.info("Scheduler started.")
    except Exception:
        logger.exception("Scheduler startup failed.")
>>>>>>> ca6d2da (Switch to instagrapi sessionid login, add session_login and publisher)

async def post_shutdown(application):
    try:
<<<<<<< HEAD
        cl = Client()
        if BOT_STATE["proxy"]: cl.set_proxy(BOT_STATE["proxy"])
        cl.login_by_sessionid(sid)
        cl.dump_settings(CONFIG_FILE)
        BOT_STATE["target2"] = cl.account_info().username
        await msg.edit_text(f"✅ Session Valid! Logged in as `@{BOT_STATE['target2']}`\n\nStep 2: Source account ka username batao:", parse_mode='Markdown')
        return WAITING_TARGET
    except Exception as e:
        traceback.print_exc()
        await msg.edit_text(f"❌ Session login failed: {type(e).__name__}. Check Railway logs.", parse_mode='Markdown')
        return ConversationHandler.END
=======
        await stop_scheduler()
    except Exception:
        logger.exception("Scheduler shutdown failed.")
>>>>>>> ca6d2da (Switch to instagrapi sessionid login, add session_login and publisher)

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
