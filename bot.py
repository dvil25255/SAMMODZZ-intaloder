import os
import time
import random
import asyncio
import requests
import json
from datetime import datetime
from instagrapi import Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# ==========================================
# RAILWAY VARIABLES
# ==========================================
TG_BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_ID")

WAITING_USER, WAITING_PASS, WAITING_OTP, WAITING_TARGET, WAITING_PROXY, WAITING_SESSION = range(6)
CONFIG_FILE = "config.json"

BOT_STATE = {
    "target": None,
    "target2": None,
    "username": None,
    "password": None,
    "is_running": False,
    "total_uploaded": 0,
    "last_status": "Bot starting...",
    "daily_target": 7,
    "uploaded_today": 0,
    "last_upload_date": None,
    "watermark": "SAMMODZZ",
    "challenge_required": False,
    "proxy": None
}

HISTORY_FILE = "uploaded_history.txt"
cl = None

SCHEDULE_TIMES = ["06:00", "09:00", "12:00", "14:00", "17:00", "19:00", "21:00"]

# ==========================================
# UI / DESIGN HELPERS
# ==========================================
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data='status')],
        [InlineKeyboardButton("▶️ Resume", callback_data='start_post'), InlineKeyboardButton("⏸️ Pause", callback_data='pause_post')],
        [InlineKeyboardButton("🛡️ Setup Proxy", callback_data='setup_proxy'), InlineKeyboardButton("⚙️ Settings", callback_data='settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_welcome_text():
    return (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"  ⚡ **SAMMODZZ AUTO-POSTER** ⚡\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"👑 **Developer:** @SAMMODZZ\n"
        f"🚀 **Version:** 2.1 (Session + Proxy)\n\n"
        f"✨ **Available Services:**\n"
        f"1️⃣ **Auto-Login (2 Ways):** Password OR Session ID.\n"
        f"2️⃣ **Proxy Support:** Bypass checkpoints & bans.\n"
        f"3️⃣ **Auto-Post:** 7 Reels/Photos per day.\n"
        f"4️⃣ **Watermark:** Auto credit to your account.\n\n"
        f"👇 **Press Setup to Begin.**"
    )

def get_dashboard_text():
    if not BOT_STATE["target"]:
        return f"🤖 **SAMMODZZ BOT**\n\n⚠️ **Setup Required**"
    
    status_icon = "🟢 Running" if BOT_STATE["is_running"] else "🔴 Paused"
    today_str = datetime.now().strftime("%Y-%m-%d")
    if BOT_STATE["last_upload_date"] != today_str:
        BOT_STATE["uploaded_today"] = 0
        BOT_STATE["last_upload_date"] = today_str

    proxy_status = "✅ Active" if BOT_STATE["proxy"] else "❌ None"

    return (
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
        f"   🤖 **SAMMODZZ PANEL**\n"
        f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"👑 **Dev:** @SAMMODZZ\n"
        f"🎯 **Source:** `@{BOT_STATE['target']}`\n"
        f"📥 **Dest:** `@{BOT_STATE['target2']}`\n"
        f"🛡️ **Proxy:** {proxy_status}\n"
        f"⚡ **Status:** {status_icon}\n\n"
        f"📊 **Today's Progress:** `{BOT_STATE['uploaded_today']} / {BOT_STATE['daily_target']}`\n"
        f"📦 **Total Uploaded:** `{BOT_STATE['total_uploaded']}`\n\n"
        f"ℹ️ **Last Activity:**\n_{BOT_STATE['last_status']}_\n\n"
        f"👇 **Control Panel:**"
    )

# ==========================================
# TELEGRAM HANDLERS
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(ADMIN_CHAT_ID): return
    
    if not BOT_STATE["target"]:
        keyboard = [
            [InlineKeyboardButton("🔑 Login with Password", callback_data='setup_pass_mode')],
            [InlineKeyboardButton("🍪 Login with Session ID", callback_data='setup_session_mode')]
        ]
        await update.message.reply_text(text=get_welcome_text(), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_text(text=get_dashboard_text(), reply_markup=get_main_menu(), parse_mode='Markdown')

async def btn_login_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Step 1: Apna Instagram **Username** bhejo:", parse_mode='Markdown')
    return WAITING_USER

async def setup_session_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🍪 **Session ID Login**\n\nBrowser se apni Instagram `sessionid` copy karke yahan paste karo:", parse_mode='Markdown')
    return WAITING_SESSION

async def setup_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cl
    sid = update.message.text.strip()
    msg = await update.message.reply_text("🔄 Validating Session ID...")
    
    try:
        cl = Client()
        if BOT_STATE["proxy"]:
            cl.set_proxy(BOT_STATE["proxy"])
            
        cl.login_by_sessionid(sid)
        cl.dump_settings(CONFIG_FILE)
        
        BOT_STATE["target2"] = cl.account_info().username
        await msg.edit_text(f"✅ Session Valid! Logged in as `@{BOT_STATE['target2']}`\n\nStep 2: Source account ka username batao jahan se post copy karni hai:", parse_mode='Markdown')
        return WAITING_TARGET
    except Exception as e:
        await msg.edit_text(f"❌ Invalid Session ID: {str(e)[:50]}\n\nTry again with `/start`")
        return ConversationHandler.END

async def setup_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    BOT_STATE["username"] = update.message.text.strip()
    await update.message.reply_text("Step 2: Apna Instagram **Password** bhejo:\n_(Message bhejte hi turant delete kar dena)_", parse_mode='Markdown')
    return WAITING_PASS

async def setup_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cl
    BOT_STATE["password"] = update.message.text.strip()
    try:
        await update.message.delete()
    except: pass
    
    msg = await update.message.reply_text("🔄 Trying to login with Password...")
    
    try:
        cl = Client()
        if BOT_STATE["proxy"]:
            cl.set_proxy(BOT_STATE["proxy"])
            
        cl.login(BOT_STATE["username"], BOT_STATE["password"])
        cl.dump_settings(CONFIG_FILE)
        
        BOT_STATE["target2"] = BOT_STATE["username"]
        await msg.edit_text(f"✅ Login successful as `@{BOT_STATE['target2']}`!\n\nStep 3: Source account ka username batao:", parse_mode='Markdown')
        return WAITING_TARGET
        
    except Exception as e:
        error_str = str(e)
        if "challenge_required" in error_str.lower() or "checkpoint" in error_str.lower():
            await msg.edit_text("⚠️ **Instagram needs OTP!**\n\nOTP code yahan bhejo:", parse_mode='Markdown')
            BOT_STATE["challenge_required"] = True
            return WAITING_OTP
        else:
            await msg.edit_text(f"❌ Password Login failed: {error_str[:100]}\n\nTry `/start` and use Session ID method.")
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
        await msg.edit_text(f"❌ OTP Failed: {str(e)[:50]}\n\nTry Session ID method.")
        return ConversationHandler.END

async def setup_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_name = update.message.text.strip().replace('@', '')
    BOT_STATE["target"] = target_name
    BOT_STATE["is_running"] = True
    BOT_STATE["last_status"] = f"Started fetching from @{target_name}"
    
    await update.message.reply_text(
        f"✅ Target set to `@{target_name}`\n"
        f"🚀 Bot is now **Running 24/7**!\n"
        f"Use `/start` for Dashboard.", 
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def setup_proxy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(ADMIN_CHAT_ID): return
    await update.message.reply_text("🛡️ **Proxy Setup**\n\nSend Proxy in this format:\n`http://user:pass@ip:port`\nOR\n`socks5://ip:port`\n\n_(Send /cancel to abort)_", parse_mode='Markdown')
    return WAITING_PROXY

async def setup_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    proxy_url = update.message.text.strip()
    BOT_STATE["proxy"] = proxy_url
    await update.message.reply_text(f"✅ Proxy Saved: `{proxy_url}`", parse_mode='Markdown')
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if str(query.message.chat.id) != str(ADMIN_CHAT_ID): return
    await query.answer()
    
    if query.data == 'status':
        await query.edit_message_text(text=get_dashboard_text(), reply_markup=get_main_menu(), parse_mode='Markdown')
    elif query.data == 'pause_post':
        BOT_STATE["is_running"] = False; BOT_STATE["last_status"] = "Paused by Admin."
        await query.edit_message_text(text=get_dashboard_text(), reply_markup=get_main_menu(), parse_mode='Markdown')
    elif query.data == 'start_post':
        BOT_STATE["is_running"] = True; BOT_STATE["last_status"] = "Resumed by Admin."
        await query.edit_message_text(text=get_dashboard_text(), reply_markup=get_main_menu(), parse_mode='Markdown')
    elif query.data == 'setup_proxy':
        await query.edit_message_text(text="Use command `/setproxy` to set proxy.", reply_markup=get_main_menu(), parse_mode='Markdown')

# ==========================================
# CORE LOGIC
# ==========================================
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f: return f.read().splitlines()
    return []

def save_history(pk):
    with open(HISTORY_FILE, "a") as f: f.write(f"{pk}\n")

def send_tg_alert(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage", json={"chat_id": ADMIN_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

def perform_upload():
    global BOT_STATE
    try:
        BOT_STATE["last_status"] = f"Searching for new posts on @{BOT_STATE['target']}..."
        user_id = cl.user_id_from_username(BOT_STATE["target"])
        medias = cl.user_medias(user_id, amount=20)
        posted_pks = load_history()
        
        post_to_copy = next((m for m in medias if str(m.pk) not in posted_pks and m.media_type == 2), None)
        if not post_to_copy:
            post_to_copy = next((m for m in medias if str(m.pk) not in posted_pks), None)

        if post_to_copy:
            is_video = (post_to_copy.media_type == 2)
            BOT_STATE["last_status"] = f"Downloading {'Reel' if is_video else 'Image'} `{post_to_copy.pk}`..."
            
            media_path = cl.video_download(post_to_copy.pk) if is_video else cl.photo_download(post_to_copy.pk)
            
            if media_path:
                caption = post_to_copy.caption_text if post_to_copy.caption_text else ""
                if BOT_STATE["watermark"]:
                    caption += f"\n\n📌 Credit: @{BOT_STATE['watermark']}"
                
                BOT_STATE["last_status"] = f"Uploading to @{BOT_STATE['target2']}..."
                if is_video: cl.clip_upload(media_path, caption)
                else: cl.photo_upload(media_path, caption)
                
                os.remove(media_path)
                save_history(post_to_copy.pk)
                
                BOT_STATE["total_uploaded"] += 1
                BOT_STATE["uploaded_today"] += 1
                BOT_STATE["last_status"] = f"✅ Uploaded successfully! (Today: {BOT_STATE['uploaded_today']}/7)"
                send_tg_alert(f"✅ **Auto-Post Success!**\n\nType: {'Reel' if is_video else 'Image'}\nToday: {BOT_STATE['uploaded_today']}/7")
        else:
            BOT_STATE["last_status"] = "No new posts available."
    except Exception as e:
        BOT_STATE["last_status"] = f"❌ Upload Error: {str(e)[:50]}"
        print(f"[ERROR] {e}")

async def scheduler_loop():
    global BOT_STATE
    while True:
        if not BOT_STATE["is_running"] or not BOT_STATE["target"] or not cl:
            await asyncio.sleep(10)
            continue

        today_str = datetime.now().strftime("%Y-%m-%d")
        if BOT_STATE["last_upload_date"] != today_str:
            BOT_STATE["uploaded_today"] = 0
            BOT_STATE["last_upload_date"] = today_str

        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        if BOT_STATE["uploaded_today"] < BOT_STATE["daily_target"]:
            if current_time_str in SCHEDULE_TIMES:
                if BOT_STATE.get("last_triggered_slot") != current_time_str:
                    BOT_STATE["last_triggered_slot"] = current_time_str
                    wait_time = random.randint(30, 90)
                    BOT_STATE["last_status"] = f"Scheduled time hit! Waiting {wait_time}s..."
                    await asyncio.sleep(wait_time)
                    await asyncio.to_thread(perform_upload)
        
        await asyncio.sleep(30)

# ==========================================
# MAIN RUNNER
# ==========================================
if __name__ == '__main__':
    if os.path.exists(CONFIG_FILE):
        try:
            cl = Client()
            if BOT_STATE["proxy"]:
                cl.set_proxy(BOT_STATE["proxy"])
            cl.load_settings(CONFIG_FILE)
            cl.get_timeline_feed() 
            BOT_STATE["target2"] = cl.account_info().username
            BOT_STATE["last_status"] = "Auto-logged in."
            print("[AUTO-LOGIN] Restored session!")
        except Exception as e:
            print(f"[AUTO-LOGIN FAILED] {e}")
            cl = None
            
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('setup', setup_pass_mode), # Default fallback
            CommandHandler('setproxy', setup_proxy_start),
            CallbackQueryHandler(setup_pass_mode, pattern='^setup_pass_mode$'),
            CallbackQueryHandler(setup_session_mode, pattern='^setup_session_mode$')
        ],
        states={
            WAITING_SESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_session)],
            WAITING_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_user)],
            WAITING_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_pass)],
            WAITING_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_otp)],
            WAITING_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_target)],
            WAITING_PROXY: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_proxy)]
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: ConversationHandler.END)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    
    async def post_init(application): 
        asyncio.create_task(scheduler_loop())
        
    app.post_init = post_init
    print("🚀 SAMMODZZ Bot is starting...")
    app.run_polling()
