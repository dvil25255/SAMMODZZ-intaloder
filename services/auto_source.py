import hashlib
import logging
from database.db import get_conn
from config import CREDIT_TEMPLATE, CAPTION_MAX_LEN
logger = logging.getLogger("SAMMODZZ.autosource")

def _build_caption(source_caption, source_username):
    source_caption = (source_caption or "").strip()
    credit = CREDIT_TEMPLATE.format(source=source_username)
    room = CAPTION_MAX_LEN - len(credit)
    if len(source_caption) > room:
        source_caption = source_caption[:room].rstrip() + "…"
    return source_caption + credit

def fetch_and_queue(api, source_username, count):
    try:
        user_id = api.user_id_from_username(source_username)
        medias = api.user_medias(user_id, amount=count)
    except Exception:
        logger.exception("Failed to fetch @%s", source_username)
        return 0
    queued = 0
    for m in medias:
        if m.media_type == 1:
            post_type = "photo"
        elif m.media_type == 2:
            post_type = "reel" if getattr(m, "product_type", "") == "clips" else "video"
        else:
            continue
        key = "%s:%s" % (source_username, m.pk)
        url_hash = hashlib.sha256(key.encode()).hexdigest()
        caption = _build_caption(m.caption_text or "", source_username)
        try:
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO queue (source_username, media_pk, media_index, post_type, caption, is_video, url_hash) "
                    "VALUES (?, ?, 0, ?, ?, ?, ?)",
                    (source_username, str(m.pk), post_type, caption, int(post_type in ("video", "reel")), url_hash),
                )
            queued += 1
        except Exception as e:
            if "UNIQUE" in str(e):
                continue
            logger.exception("Queue insert failed %s", key)
    logger.info("Queued %d new from @%s", queued, source_username)
    return queued

def refill_all(api, sources, count):
    total = 0
    for u in sources:
        total += fetch_and_queue(api, u, count)
    return total
