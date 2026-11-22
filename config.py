import os
import json

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID", "")

IG_SESSIONID = os.environ.get("IG_SESSIONID", "")
IG_USERNAME = os.environ.get("IG_USERNAME", "")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "")

SOURCE_ACCOUNTS = [u.strip() for u in os.environ.get("SOURCE_ACCOUNTS", "").split(",") if u.strip()]
AUTO_FETCH_COUNT = int(os.environ.get("AUTO_FETCH_COUNT", "5"))
CREDIT_TEMPLATE = os.environ.get("CREDIT_TEMPLATE", "\n\n📸 Credit: @{source}\n#repost #credit")
CAPTION_MAX_LEN = 2100

POST_SLOTS = ["06:00", "09:00", "12:00", "14:00", "17:00", "19:00", "21:00"]
DAILY_TARGET = 7
TIMEZONE = "Asia/Kolkata"

DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "sammodzz.db")
SESSION_FILE = os.path.join(DATA_DIR, "ig_session.json")
SETTINGS_FILE = os.path.join("config", "settings.json")
os.makedirs(DATA_DIR, exist_ok=True)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    return {}

def save_settings(data):
    os.makedirs("config", exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)
