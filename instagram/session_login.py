import logging
import os
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError
from config import IG_SESSIONID, IG_USERNAME, IG_PASSWORD, SESSION_FILE
logger = logging.getLogger("SAMMODZZ.session")

def get_client():
    cl = Client()
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.get_timeline_feed()
            logger.info("Loaded saved session.")
            return cl
        except Exception:
            logger.warning("Saved session invalid.")
            try: os.remove(SESSION_FILE)
            except OSError: pass
    if IG_SESSIONID:
        try:
            cl.login_by_sessionid(IG_SESSIONID)
            cl.dump_settings(SESSION_FILE)
            logger.info("Logged in via sessionid.")
            return cl
        except LoginRequired:
            logger.warning("sessionid rejected.")
        except ClientError as e:
            logger.warning("sessionid login failed: %s", e)
    if IG_USERNAME and IG_PASSWORD:
        try:
            cl.login(IG_USERNAME, IG_PASSWORD)
            cl.dump_settings(SESSION_FILE)
            logger.info("Logged in via password.")
            return cl
        except Exception:
            logger.exception("Password login failed.")
    raise RuntimeError("Instagram login failed. Set IG_SESSIONID.")

def relogin(cl):
    if os.path.exists(SESSION_FILE):
        try: os.remove(SESSION_FILE)
        except OSError: pass
    return get_client()
