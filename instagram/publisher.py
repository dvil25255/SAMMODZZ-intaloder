import logging
import os
import tempfile
from instagram.media import upload_photo, upload_video, upload_reel
logger = logging.getLogger("SAMMODZZ.publisher")

def publish_from_pk(api, media_pk, caption, post_type="photo"):
    tmpdir = tempfile.mkdtemp(prefix="sammodzz_")
    try:
        if post_type == "photo":
            path = api.photo_download(int(media_pk), folder=tmpdir)
            mid = upload_photo(api, path, caption)
        elif post_type in ("video", "reel"):
            path = api.video_download(int(media_pk), folder=tmpdir)
            mid = upload_reel(api, path, caption) if post_type == "reel" else upload_video(api, path, caption)
        else:
            raise ValueError("Unsupported post_type: %s" % post_type)
        return {"media_id": mid}
    finally:
        for f in os.listdir(tmpdir):
            try: os.remove(os.path.join(tmpdir, f))
            except OSError: pass
        try: os.rmdir(tmpdir)
        except OSError: pass
