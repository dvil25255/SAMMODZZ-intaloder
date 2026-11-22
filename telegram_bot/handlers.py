import hashlib
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from config import load_settings, save_settings, DAILY_TARGET, POST_SLOTS
from database.db import get_conn, init_db
from database.history import get_recent_history, count_today_published
from telegram_bot.keyboards import main_menu, back_to_menu
from telegram_bot.messages import WELCOME, HELP_ADD, STATUS_TEMPLATE
logger = logging.getLogger("SAMMODZZ.handlers")

def register_handlers(application):
    init_db()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("add", cmd_add))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("history", cmd_history))
    application.add_handler(CommandHandler("pause", cmd_pause))
    application.add_handler(CommandHandler("resume", cmd_resume))
    application.add_handler(CommandHandler("source", cmd_source))
    application.add_handler(CallbackQueryHandler(cb_menu, pattern="^menu$"))
    application.add_handler(CallbackQueryHandler(cb_status, pattern="^status$"))
    application.add_handler(CallbackQueryHandler(cb_history, pattern="^history$"))
    application.add_handler(CallbackQueryHandler(cb_pause, pattern="^pause$"))
    application.add_handler(CallbackQueryHandler(cb_resume, pattern="^resume$"))
    application.add_handler(CallbackQueryHandler(cb_add_help, pattern="^add_help$"))

def _add_to_queue(source_username, media_index, post_type, caption):
    key = "%s:%d:%s" % (source_username, media_index, post_type)
    url_hash = hashlib.sha256(key.encode()).hexdigest()
    is_video = int(post_type in ("video", "reel"))
    try:
        with get_conn() as conn:
            conn.execute("INSERT INTO queue (source_username, media_index, post_type, caption, is_video, url_hash) VALUES (?, ?, ?, ?, ?, ?)", (source_username, media_index, post_type, caption, is_video, url_hash))
        return True, "जोड़ दिया गया ✅"
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "यह entry पहले से queue में है ❌"
        return False, "DB error: %s" % e

def _next_slot_str():
    now = datetime.now()
    for s in POST_SLOTS:
        hh, mm = s.split(":")
        if (int(hh), int(mm)) > (now.hour, now.minute):
            return s
    return POST_SLOTS[0] + " (कल)"

async def cmd_start(update, context):
    await update.message.reply_text(WELCOME, parse_mode="Markdown", reply_markup=main_menu())

async def cmd_add(update, context):
    args = context.args
    if len(args) < 4:
        await update.message.reply_text(HELP_ADD, parse_mode="Markdown")
        return
    source, idx, ptype = args[0], args[1], args[2].lower()
    caption = " ".join(args[3:])
    if ptype not in ("photo", "video", "reel"):
        await update.message.reply_text("post_type सिर्फ photo/video/reel")
        return
    try:
        media_index = int(idx)
    except ValueError:
        await update.message.reply_text("index पूरा नंबर होना चाहिए")
        return
    ok, msg = _add_to_queue(source, media_index, ptype, caption)
    await update.message.reply_text(msg, reply_markup=back_to_menu())

async def cmd_status(update, context):
    await update.message.reply_text(_status_text(), parse_mode="Markdown", reply_markup=back_to_menu())

async def cmd_history(update, context):
    await update.message.reply_text(_history_text(), parse_mode="Markdown", reply_markup=back_to_menu())

async def cmd_pause(update, context):
    s = load_settings(); s["paused"] = True; save_settings(s)
    await update.message.reply_text("⏸ Paused", reply_markup=back_to_menu())

async def cmd_resume(update, context):
    s = load_settings(); s["paused"] = False; save_settings(s)
    await update.message.reply_text("▶️ Resumed", reply_markup=back_to_menu())

async def cb_menu(update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(WELCOME, parse_mode="Markdown", reply_markup=main_menu())

async def cb_status(update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(_status_text(), parse_mode="Markdown", reply_markup=back_to_menu())

async def cb_history(update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(_history_text(), parse_mode="Markdown", reply_markup=back_to_menu())

async def cb_pause(update, context):
    q = update.callback_query; await q.answer()
    s = load_settings(); s["paused"] = True; save_settings(s)
    await q.edit_message_text("⏸ Paused", reply_markup=back_to_menu())

async def cb_resume(update, context):
    q = update.callback_query; await q.answer()
    s = load_settings(); s["paused"] = False; save_settings(s)
    await q.edit_message_text("▶️ Resumed", reply_markup=back_to_menu())

async def cb_add_help(update, context):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(HELP_ADD, parse_mode="Markdown", reply_markup=back_to_menu())

def _status_text():
    s = load_settings()
    with get_conn() as conn:
        queued = conn.execute("SELECT COUNT(*) AS n FROM queue WHERE status='queued'").fetchone()["n"]
    return STATUS_TEMPLATE.format(paused="✅ Yes" if s.get("paused") else "❌ No", queued=queued, today=count_today_published(), target=s.get("daily_target", DAILY_TARGET), next_slot=_next_slot_str())

def _history_text():
    rows = get_recent_history(10)
    if not rows:
        return "कोई history नहीं है।"
    lines = ["📜 *Recent uploads*", ""]
    for r in rows:
        when = r["created_at"][:16]
        icon = "✅" if r["status"] == "success" else "❌"
        src = "@%s" % r["source_username"] if r["source_username"] else "file"
        lines.append("%s `%s` — %s — media_id: `%s`" % (icon, when, src, r["media_id"]))
    return "\n".join(lines)


async def cmd_source(update, context):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /source add <username> | /source list | /source remove <username>")
        return
    action = args[0].lower()
    if action == "add" and len(args) == 2:
        username = args[1].lstrip("@")
        try:
            with get_conn() as conn:
                conn.execute("INSERT INTO sources (username) VALUES (?)", (username,))
            await update.message.reply_text("@%s source में जोड़ दिया ✅" % username)
        except Exception as e:
            if "UNIQUE" in str(e):
                await update.message.reply_text("यह source पहले से जुड़ा है ❌")
            else:
                await update.message.reply_text("DB error: %s" % e)
    elif action == "list":
        with get_conn() as conn:
            rows = conn.execute("SELECT username FROM sources ORDER BY id").fetchall()
        if not rows:
            await update.message.reply_text("कोई source नहीं जुड़ा।")
            return
        await update.message.reply_text("📋 Sources:\n" + "\n".join("• @" + r["username"] for r in rows))
    elif action == "remove" and len(args) == 2:
        username = args[1].lstrip("@")
        with get_conn() as conn:
            conn.execute("DELETE FROM sources WHERE username=?", (username,))
        await update.message.reply_text("@%s हटा दिया।" % username)
    else:
        await update.message.reply_text("गलत usage।")
