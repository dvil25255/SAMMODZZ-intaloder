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

# ==========================================
# RAILWAY VARIABLES
# ==========================================
TG_BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_ID")

# Webshare Rotating Proxy
DEFAULT_PROXY = "http://vbhaojyx-rotate:ubfsf9jq5wg5@p.webshare.io:80"

WAITING_USER, WAITING_PASS, WAITING_OTP, WAITING_TARGET, WAITING_PROXY, WAITING_SESSION = range(6)
CONFIG_FILE = "config.json"

BOT_STATE = {
    "target": None, "target2": None, "username": None, "password": None,
    "is_running": False, "total_uploaded": 0, "last_status": "Bot starting...",
    "daily_target": 7, "uploaded_today": 0, "last_upload_date": None,
    "watermark": "SAMMODZZ", "challenge_required": False, "proxy": DEFAULT_PROXY
}
HISTORY_FILE = "uploaded_history.txt"
cl = None
SCHEDULE_TIMES = ["06:00", "09:00", "12:00", "14:00", "17:00", "19:00", "21:00"]

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data='status')],
        [InlineKeyboardButton("▶️ Resume", callback_data='start_post'), InlineKeyboardButton("⏸️ Pause", callback_data='pause_post')],
        [InlineKeyboardButton("🔄 Change Login", callback_data='show_login'), InlineKeyboardButton("🛡️ Setup Proxy", callback_data='show_proxy')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_welcome_text():
    return (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"  ⚡ **SAMMODZZ AUTO-POSTER** ⚡\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"👑 **Developer:** @SAMMODZZ\n\n"
        f"👇 **Select Login Method:**"
    )

def get_dashboard_text():
    if not BOT_STATE["target"]: return "🤖 **SAMMODZZ BOT**\n\n⚠️ **Setup Required**"
    status_icon = "🟢 Running" if BOT_STATE["is_running"] else "🔴 Paused"
    today_str = datetime.now().strftime("%Y-%m-%d")
    if BOT_STATE["last_upload_date"] != today_str:
        BOT_STATE["uploaded_today"] = 0; BOT_STATE["last_upload_date"] = today_str
    proxy_status = "✅ Active (Webshare)" if BOT_STATE["proxy"] else "❌ None"
    return (
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n   🤖 **SAMMODZZ PANEL**\n┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"👑 **Dev:** @SAMMODZZ\n🎯 **Source:** `@{BOT_STATE['target']}`\n📥 **Dest:** `@{BOT_STATE['target2']}`\n"
        f"🛡️ **Proxy:** {proxy_status}\n⚡ **Status:** {status_icon}\n\n"
        f"📊 **Today:** `{BOT_STATE['uploaded_today']} / {BOT_STATE['daily_target']}`\n📦 **Total:** `{BOT_STATE['total_uploaded']}`\n\n"
        f"ℹ️ **Last Activity:**\n_{BOT_STATE['last_status']}_\n\n👇 **Control Panel:**"
    )

def get_login_menu():
    keyboard = [
        [InlineKeyboardButton("🔑 Login with Password", callback_data='login_pass')],
        [InlineKeyboardButton("🍪 Login with Session ID", callback_data='login_sess')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(ADMIN_CHAT_ID): return
    if not BOT_STATE["target"]:
        await update.message.reply_text(text=get_welcome_text(), reply_markup=get_login_menu(), parse_mode='Markdown')
    else:
        await update.message.reply_text(text=get_dashboard_text(), reply_markup=get_main_menu(), parse_mode='Markdown')

async def show_login_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=get_welcome_text(), reply_markup=get_login_menu(), parse_mode='Markdown')

async def btn_login_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Step 1: Apna Instagram **Username** bhejo:\n\n_(Send /cancel to abort)_", parse_mode='Markdown')
    return WAITING_USER

async def btn_login_sess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🍪 **Session ID Login**\n\nBrowser se apni Instagram `sessionid` copy karke yahan paste karo:\n\n_(Send /cancel to abort)_", parse_mode='Markdown')
    return WAITING_SESSION

async def setup_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    BOT_STATE["username"] = update.message.text.strip()
    await update.message.reply_text("Step 2: Apna Instagram **Password** bhejo:\n_(Message bhejte hi turant delete kar dena)_", parse_mode='Markdown')
    return WAITING_PASS

async def setup_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cl
    BOT_STATE["password"] = update.message.text.strip()
    try: await update.message.delete()
    except: pass
    msg = await update.message.reply_text("🔄 Trying to login with Password (via Proxy)...")
    try:
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

async def setup_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cl
    sid = update.message.text.strip()
    msg = await update.message.reply_text("🔄 Validating Session ID (via Proxy)...")
    try:
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

async def setup_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cl
    otp_code = update.message.text.strip()
    msg = await update.message.reply_text("🔄 Verifying OTP...")
    try:
        cl.challenge_code(otp_code)
        cl.dump_settings(CONFIG_FILE)
        BOT_STATE["target2"] = BOT_STATE["username"]
        await msg.edit_text(f"✅ Verification successful!\n\nStep 3: Source account ka username batao:", parse_mode='Markdown')
        return WAITING_TARGET
    except Exception as e:
        await msg.edit_text(f"❌ OTP Failed: {str(e)[:50]}\n\nTry Session ID method with `/start`.")
        return ConversationHandler.END

async def setup_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_name = update.message.text.strip().replace('@', '')
    BOT_STATE["target"] = target_name
    BOT_STATE["is_running"] = True
    BOT_STATE["last_status"] = f"Started fetching from @{target_name}"
    await update.message.reply_text(f"✅ Target set to `@{target_name}`\n🚀 Bot is now **Running 24/7**!\n\nUse `/start` for Dashboard.", parse_mode='Markdown')
    return ConversationHandler.END

async def show_proxy_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"🛡️ **Proxy Setup**\n\nCurrent Proxy: `{BOT_STATE['proxy']}`\n\nSend new Proxy in format:\n`http://user:pass@ip:port`\nOR\n`socks5://ip:port`\n\n_(Send /cancel to abort)_", parse_mode='Markdown')
    return WAITING_PROXY

async def setup_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    proxy_url = update.message.text.strip()
    BOT_STATE["proxy"] = proxy_url
    await update.message.reply_text(f"✅ Proxy Saved: `{proxy_url}`", parse_mode='Markdown')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Setup cancelled. Use /start to manage bot.")
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if str(query.message.chat.id) != str(ADMIN_CHAT_ID): return
    await query.answer()
    
    if query.data == 'status':
        await query.edit_message_text(text=get_dashboard_text(), reply_markup=get_main_menu(), parse_mode='Markdown')
    elif query.data == 'pause_post':
        BOT_STATE["is_running"] = False; BOT_STATE["last_status"] = "Paused."
        await query.edit_message_text(text=get_dashboard_text(), reply_markup=get_main_menu(), parse_mode='Markdown')
    elif query.data == 'start_post':
        BOT_STATE["is_running"] = True; BOT_STATE["last_status"] = "Resumed."
        await query.edit_message_text(text=get_dashboard_text(), reply_markup=get_main_menu(), parse_mode='Markdown')

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f: return f.read().splitlines()
    return []
def save_history(pk):
    with open(HISTORY_FILE, "a") as f: f.write(f"{pk}\n")
def send_tg_alert(msg):
    try: requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage", json={"chat_id": ADMIN_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def perform_upload():
    global BOT_STATE
    try:
        BOT_STATE["last_status"] = f"Searching on @{BOT_STATE['target']}..."
        user_id = cl.user_id_from_username(BOT_STATE["target"])
        medias = cl.user_medias(user_id, amount=20)
        posted_pks = load_history()
        post = next((m for m in medias if str(m.pk) not in posted_pks and m.media_type == 2), None)
        if not post: post = next((m for m in medias if str(m.pk) not in posted_pks), None)
        if post:
            is_vid = (post.media_type == 2)
            BOT_STATE["last_status"] = f"Downloading {'Reel' if is_vid else 'Image'}..."
            path = cl.video_download(post.pk) if is_vid else cl.photo_download(post.pk)
            if path:
                cap = post.caption_text if post.caption_text else ""
                if BOT_STATE["watermark"]: cap += f"\n\n📌 Credit: @{BOT_STATE['watermark']}"
                BOT_STATE["last_status"] = f"Uploading to @{BOT_STATE['target2']}..."
                if is_vid: cl.clip_upload(path, cap)
                else: cl.photo_upload(path, cap)
                os.remove(path); save_history(post.pk)
                BOT_STATE["total_uploaded"] += 1; BOT_STATE["uploaded_today"] += 1
                BOT_STATE["last_status"] = f"✅ Uploaded! (Today: {BOT_STATE['uploaded_today']}/7)"
                send_tg_alert(f"✅ **Post Uploaded!**\nType: {'Reel' if is_vid else 'Image'}")
        else: BOT_STATE["last_status"] = "No new posts."
    except Exception as e:
        BOT_STATE["last_status"] = f"❌ Error: {str(e)[:50]}"

async def scheduler_loop():
    global BOT_STATE
    while True:
        if not BOT_STATE["is_running"] or not BOT_STATE["target"] or not cl:
            await asyncio.sleep(10); continue
        today_str = datetime.now().strftime("%Y-%m-%d")
        if BOT_STATE["last_upload_date"] != today_str:
            BOT_STATE["uploaded_today"] = 0; BOT_STATE["last_upload_date"] = today_str
        now = datetime.now(); current_time_str = now.strftime("%H:%M")
        if BOT_STATE["uploaded_today"] < BOT_STATE["daily_target"]:
            if current_time_str in SCHEDULE_TIMES and BOT_STATE.get("last_triggered_slot") != current_time_str:
                BOT_STATE["last_triggered_slot"] = current_time_str
                await asyncio.sleep(random.randint(30, 90))
                await asyncio.to_thread(perform_upload)
        await asyncio.sleep(30)

if __name__ == '__main__':
    if os.path.exists(CONFIG_FILE):
        try:
            cl = Client()
            if BOT_STATE["proxy"]: cl.set_proxy(BOT_STATE["proxy"])
            cl.load_settings(CONFIG_FILE); cl.get_timeline_feed()
            BOT_STATE["target2"] = cl.account_info().username
            BOT_STATE["last_status"] = "Auto-logged in (Proxy Active)."
        except: cl = None
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(btn_login_pass, pattern='^login_pass$'),
            CallbackQueryHandler(btn_login_sess, pattern='^login_sess$'),
            CallbackQueryHandler(show_proxy_menu, pattern='^show_proxy$'),
            CallbackQueryHandler(show_login_menu, pattern='^show_login$'),
            CommandHandler('setup', btn_login_pass)
        ],
        states={
            WAITING_SESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_session)],
            WAITING_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_user)],
            WAITING_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_pass)],
            WAITING_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_otp)],
            WAITING_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_target)],
            WAITING_PROXY: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_proxy)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    
    async def post_init(application): 
        asyncio.create_task(scheduler_loop())
    app.post_init = post_init
    print("🚀 SAMMODZZ Bot is starting with Default Proxy...")
    app.run_polling()
