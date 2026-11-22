import os
import time
import random
import asyncio
import requests
from instagrapi import Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler

# ==========================================
# RAILWAY VARIABLES (Environment se uthayega)
# ==========================================
TG_BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_ID")

# Conversation States
WAITING_SESSION, WAITING_TARGET, WAITING_TARGET_2 = range(3)

BOT_STATE = {
    "target": None,
    "target2": None,
    "session_id": None,
    "is_running": False,
    "total_uploaded": 0,
    "last_status": "Setup pending. Please configure the bot.",
    "min_delay_hours": 2,
    "max_delay_hours": 4
}

cl = None
HISTORY_FILE = "uploaded_history.txt"

# ==========================================
# UI / DESIGN HELPERS
# ==========================================
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard", callback_data='status')],
        [InlineKeyboardButton("▶️ Start Auto-Post", callback_data='start_post'), InlineKeyboardButton("⏸️ Pause Bot", callback_data='pause_post')],
        [InlineKeyboardButton("🔄 Change Target", callback_data='change_target'), InlineKeyboardButton("📜 View History", callback_data='history')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_dashboard_text():
    if not BOT_STATE["is_running"] and not BOT_STATE["target"]:
        return (
            f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
            f"   🤖 **INSTA AUTO-POSTER**\n"
            f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
            f"⚠️ **Setup Required**\n\n"
            f"Please use `/setup` to configure:\n"
            f"1. Instagram Session ID\n"
            f"2. Target Account (Jahan se copy karna hai)\n"
            f"3. Your Account (Jahan post karna hai)\n"
        )
    
    status_icon = "🟢 Running" if BOT_STATE["is_running"] else "🔴 Paused"
    return (
        f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
        f"   🤖 **INSTA AUTO-POSTER**\n"
        f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"🎯 **Target (Fetch):** `@{BOT_STATE['target']}`\n"
        f"📥 **Target (Upload):** `@{BOT_STATE['target2']}`\n"
        f"⚡ **Status:** {status_icon}\n"
        f"📦 **Uploaded:** `{BOT_STATE['total_uploaded']}`\n"
        f"⏱ **Delay:** Random ({BOT_STATE['min_delay_hours']} - {BOT_STATE['max_delay_hours']} hours)\n\n"
        f"ℹ️ **Last Activity:**\n_{BOT_STATE['last_status']}_\n\n"
        f"👇 **Use buttons below to manage:**"
    )

# ==========================================
# TELEGRAM COMMAND HANDLERS
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(ADMIN_CHAT_ID): return
    await update.message.reply_text(text=get_dashboard_text(), reply_markup=get_main_menu() if BOT_STATE["target"] else None, parse_mode='Markdown')

async def setup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(ADMIN_CHAT_ID): return
    await update.message.reply_text("Step 1: Apni Instagram `sessionid` paste karo.\n_(Browser cookies se `sessionid` copy karo)_", parse_mode='Markdown')
    return WAITING_SESSION

async def setup_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cl
    sid = update.message.text.strip()
    BOT_STATE["session_id"] = sid
    try:
        cl = Client()
        cl.login_by_sessionid(sid)
        # Upload account username nikalna
        upload_acc = cl.account_info().username
        BOT_STATE["target2"] = upload_acc
        await update.message.reply_text(f"✅ Session ID valid! Logged in as `@{upload_acc}`\n\nStep 2: Target account ka username batao jahan se post copy karni hai (bina @ ke):", parse_mode='Markdown')
        return WAITING_TARGET
    except Exception as e:
        await update.message.reply_text(f"❌ Invalid Session ID or login failed. Error: {str(e)[:50]}\n\nTry again with `/setup`")
        return ConversationHandler.END

async def setup_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_name = update.message.text.strip().replace('@', '')
    BOT_STATE["target"] = target_name
    
    # Set bot to running and update status
    BOT_STATE["is_running"] = True
    BOT_STATE["last_status"] = f"Started fetching from @{target_name}"
    
    await update.message.reply_text(
        f"✅ Target set to `@{target_name}`\n"
        f"🚀 Bot is now **Running**!\n\n"
        f"Use `/start` to see dashboard.", 
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def cancel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Setup cancelled.")
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

async def auto_post_loop():
    global BOT_STATE
    while True:
        if not BOT_STATE["is_running"] or not BOT_STATE["target"] or not cl:
            await asyncio.sleep(10); continue
            
        BOT_STATE["last_status"] = f"Checking @{BOT_STATE['target']}..."
        try:
            # Download (Side A)
            user_id = cl.user_id_from_username(BOT_STATE["target"])
            medias = cl.user_medias(user_id, amount=10)
            posted_pks = load_history()
            post_to_copy = next((m for m in medias if str(m.pk) not in posted_pks), None)
            
            if post_to_copy:
                BOT_STATE["last_status"] = f"Downloading post `{post_to_copy.pk}`..."
                media_path, is_video = "", False
                if post_to_copy.media_type == 2: 
                    media_path = cl.video_download(post_to_copy.pk); is_video = True
                elif post_to_copy.media_type == 1: 
                    media_path = cl.photo_download(post_to_copy.pk)
                
                if media_path:
                    caption = post_to_copy.caption_text if post_to_copy.caption_text else ""
                    
                    # Random anti-ban wait
                    upload_delay = random.randint(30, 60)
                    BOT_STATE["last_status"] = f"Waiting {upload_delay}s to upload (Anti-Ban)..."
                    await asyncio.sleep(upload_delay)
                    
                    # Upload (Side B)
                    BOT_STATE["last_status"] = f"Uploading to @{BOT_STATE['target2']}..."
                    if is_video: cl.clip_upload(media_path, caption)
                    else: cl.photo_upload(media_path, caption)
                    
                    os.remove(media_path); save_history(post_to_copy.pk)
                    BOT_STATE["total_uploaded"] += 1
                    BOT_STATE["last_status"] = f"✅ Uploaded post `{post_to_copy.pk}`!"
                    send_tg_alert(f"✅ **Post Uploaded!**\nFrom: @{BOT_STATE['target']}\nTo: @{BOT_STATE['target2']}")
            else:
                BOT_STATE["last_status"] = "No new posts found."
        except Exception as e:
            BOT_STATE["last_status"] = f"❌ Error: {str(e)[:50]}"
            print(f"[ERROR] {e}")
            
        # Wait before next check (Randomized)
        wait_sec = int(random.uniform(BOT_STATE["min_delay_hours"], BOT_STATE["max_delay_hours"]) * 3600)
        BOT_STATE["last_status"] = f"Next post in ~{wait_sec//3600} hours."
        await asyncio.sleep(wait_sec)

# ==========================================
# MAIN
# ==========================================
if __name__ == '__main__':
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()
    
    # Setup Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('setup', setup_start)],
        states={
            WAITING_SESSION: [CommandHandler('cancel', cancel_setup), MessageHandler(filters.TEXT & ~filters.COMMAND, setup_session)],
            WAITING_TARGET: [CommandHandler('cancel', cancel_setup), MessageHandler(filters.TEXT & ~filters.COMMAND, setup_target)]
        },
        fallbacks=[CommandHandler('cancel', cancel_setup)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    
    async def post_init(application): 
        asyncio.create_task(auto_post_loop())
        
    app.post_init = post_init
    print("Bot is starting...")
    app.run_polling()
