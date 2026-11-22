import os
import time
import random
import asyncio
import requests
from datetime import datetime, timedelta
from instagrapi import Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# ==========================================
# RAILWAY VARIABLES
# ==========================================
TG_BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_ID")

WAITING_SESSION, WAITING_TARGET = range(2)

BOT_STATE = {
    "target": None,
    "target2": None,
    "session_id": None,
    "is_running": False,
    "total_uploaded": 0,
    "last_status": "Setup pending.",
    "daily_target": 7,
    "uploaded_today": 0,
    "last_upload_date": None
}

HISTORY_FILE = "uploaded_history.txt"
cl = None

# Fixed Schedule Times (24-hour format)
SCHEDULE_TIMES = ["06:00", "09:00", "12:00", "14:00", "17:00", "19:00", "21:00"]

# ==========================================
# UI / DESIGN HELPERS
# ==========================================
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data='status')],
        [InlineKeyboardButton("▶️ Resume", callback_data='start_post'), InlineKeyboardButton("⏸️ Pause", callback_data='pause_post')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_dashboard_text():
    if not BOT_STATE["target"]:
        return "🤖 **INSTA AUTO-POSTER**\n\n⚠️ **Setup Required**\nUse `/setup` to configure Session ID and Target."
    
    status_icon = "🟢 Running" if BOT_STATE["is_running"] else "🔴 Paused"
    today_str = datetime.now().strftime("%Y-%m-%d")
    if BOT_STATE["last_upload_date"] != today_str:
        BOT_STATE["uploaded_today"] = 0
        BOT_STATE["last_upload_date"] = today_str

    return (
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
        f"   🤖 **INSTA AUTO-POSTER**\n"
        f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"🎯 **Source:** `@{BOT_STATE['target']}`\n"
        f"📥 **Dest:** `@{BOT_STATE['target2']}`\n"
        f"⚡ **Status:** {status_icon}\n\n"
        f"📊 **Today's Progress:** `{BOT_STATE['uploaded_today']} / {BOT_STATE['daily_target']}`\n"
        f"📦 **Total Uploaded:** `{BOT_STATE['total_uploaded']}`\n\n"
        f"⏰ **Fixed Schedule:**\n6AM, 9AM, 12PM, 2PM, 5PM, 7PM, 9PM\n\n"
        f"ℹ️ **Last Activity:**\n_{BOT_STATE['last_status']}_\n\n"
        f"👇 **Control Panel:**"
    )

# ==========================================
# TELEGRAM HANDLERS
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(ADMIN_CHAT_ID): return
    await update.message.reply_text(text=get_dashboard_text(), reply_markup=get_main_menu() if BOT_STATE["target"] else None, parse_mode='Markdown')

async def setup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(ADMIN_CHAT_ID): return
    await update.message.reply_text("Step 1: Apni Instagram `sessionid` paste karo.\n(Browser cookies se `sessionid` copy karo)", parse_mode='Markdown')
    return WAITING_SESSION

async def setup_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cl
    sid = update.message.text.strip()
    BOT_STATE["session_id"] = sid
    try:
        cl = Client()
        cl.login_by_sessionid(sid)
        upload_acc = cl.account_info().username
        BOT_STATE["target2"] = upload_acc
        await update.message.reply_text(f"✅ Session valid! Logged in as `@{upload_acc}`\n\nStep 2: Source account ka username batao (jahan se post copy karni hai):", parse_mode='Markdown')
        return WAITING_TARGET
    except Exception as e:
        await update.message.reply_text(f"❌ Invalid Session. Error: {str(e)[:50]}\nTry `/setup` again.")
        return ConversationHandler.END

async def setup_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_name = update.message.text.strip().replace('@', '')
    BOT_STATE["target"] = target_name
    BOT_STATE["is_running"] = True
    BOT_STATE["last_status"] = f"Started fetching from @{target_name}"
    
    await update.message.reply_text(
        f"✅ Target set to `@{target_name}`\n"
        f"🚀 Bot is now **Running 24/7**!\n"
        f"⏰ Fixed Schedule: 6AM, 9AM, 12PM, 2PM, 5PM, 7PM, 9PM\n\n"
        f"Use `/start` for Dashboard.", 
        parse_mode='Markdown'
    )
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

# ==========================================
# CORE LOGIC (Fixed Time Scheduler)
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
    """Ye function ek single post download aur upload karta hai"""
    global BOT_STATE
    try:
        BOT_STATE["last_status"] = f"Searching for new posts on @{BOT_STATE['target']}..."
        user_id = cl.user_id_from_username(BOT_STATE["target"])
        medias = cl.user_medias(user_id, amount=20)
        posted_pks = load_history()
        
        # Find a new Reel first, then fallback to Image
        post_to_copy = next((m for m in medias if str(m.pk) not in posted_pks and m.media_type == 2), None)
        if not post_to_copy:
            post_to_copy = next((m for m in medias if str(m.pk) not in posted_pks), None)

        if post_to_copy:
            is_video = (post_to_copy.media_type == 2)
            BOT_STATE["last_status"] = f"Downloading {'Reel' if is_video else 'Image'} `{post_to_copy.pk}`..."
            
            media_path = cl.video_download(post_to_copy.pk) if is_video else cl.photo_download(post_to_copy.pk)
            
            if media_path:
                caption = post_to_copy.caption_text if post_to_copy.caption_text else ""
                
                BOT_STATE["last_status"] = f"Uploading to @{BOT_STATE['target2']}..."
                if is_video: cl.clip_upload(media_path, caption)
                else: cl.photo_upload(media_path, caption)
                
                os.remove(media_path)
                save_history(post_to_copy.pk)
                
                # Update Stats
                BOT_STATE["total_uploaded"] += 1
                BOT_STATE["uploaded_today"] += 1
                BOT_STATE["last_status"] = f"✅ Uploaded successfully! (Today: {BOT_STATE['uploaded_today']}/7)"
                send_tg_alert(f"✅ **Auto-Post Success!**\n\nType: {'Reel' if is_video else 'Image'}\nToday: {BOT_STATE['uploaded_today']}/7")
        else:
            BOT_STATE["last_status"] = "No new posts available in source account."
            
    except Exception as e:
        BOT_STATE["last_status"] = f"❌ Upload Error: {str(e)[:50]}"
        print(f"[ERROR] {e}")

async def scheduler_loop():
    """24/7 Loop jo exact time par upload trigger karta hai"""
    global BOT_STATE
    while True:
        if not BOT_STATE["is_running"] or not BOT_STATE["target"] or not cl:
            await asyncio.sleep(10)
            continue

        # Check Daily Reset
        today_str = datetime.now().strftime("%Y-%m-%d")
        if BOT_STATE["last_upload_date"] != today_str:
            BOT_STATE["uploaded_today"] = 0
            BOT_STATE["last_upload_date"] = today_str

        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        # Agar aaj ka target (7) pura nahi hua hai, toh time check karo
        if BOT_STATE["uploaded_today"] < BOT_STATE["daily_target"]:
            if current_time_str in SCHEDULE_TIMES:
                # Check karo ki is time par aaj upload ho chuka hai ya nahi (History se)
                # Ek simple logic: Agar "last_uploaded_time" current time se match karta hai, toh skip karo.
                if BOT_STATE.get("last_triggered_slot") != current_time_str:
                    BOT_STATE["last_triggered_slot"] = current_time_str
                    
                    # Anti-ban: 30 se 90 seconds ka random wait (Jaise insaan karta hai)
                    wait_time = random.randint(30, 90)
                    BOT_STATE["last_status"] = f"Scheduled time hit! Waiting {wait_time}s before upload..."
                    await asyncio.sleep(wait_time)
                    
                    # Execute in a separate thread to avoid blocking the loop
                    await asyncio.to_thread(perform_upload)
        
        # Loop har 30 second me time check karega
        await asyncio.sleep(30)

# ==========================================
# MAIN RUNNER
# ==========================================
if __name__ == '__main__':
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('setup', setup_start)],
        states={
            WAITING_SESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_session)],
            WAITING_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_target)]
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: ConversationHandler.END)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    
    async def post_init(application): 
        asyncio.create_task(scheduler_loop())
        
    app.post_init = post_init
    print("🚀 Bot is starting in 24/7 Scheduled Mode...")
    app.run_polling()
