import logging
from urllib.parse import urlparse
logger = logging.getLogger("SAMMODZZ.source")

def validate_media_url(url):
    try:
        p = urlparse(url)
    except Exception as e:
        return False, "invalid URL: %s" % e
    if p.scheme not in ("http", "https"):
        return False, "URL must start with https://"
    if not p.netloc:
        return False, "URL missing host"
    return True, "ok"

def is_video_url(url):
    return urlparse(url).path.lower().endswith((".mp4", ".mov", ".m4v"))
