import logging
import os
import tempfile
from instagram.media import upload_photo, upload_video, upload_reel
logger = logging.getLogger("SAMMODZZ.publisher")

def publish_from_source(api, source_username, media_index=0, caption="", post_type="photo"):
    user_id = api.user_id_from_username(source_username)
    medias = api.user_medias(user_id, amount=media_index + 1)
    if len(medias) <= media_index:
        raise ValueError("Source has no media at index %d" % media_index)
    target = medias[media_index]
    tmpdir = tempfile.mkdtemp(prefix="sammodzz_")
    try:
        if target.media_type == 1:
            path = api.photo_download(target.pk, folder=tmpdir)
            if not caption: caption = target.caption_text or ""
            mid = upload_photo(api, path, caption)
        elif target.media_type == 2:
            path = api.video_download(target.pk, folder=tmpdir)
            if not caption: caption = target.caption_text or ""
            mid = upload_reel(api, path, caption) if post_type == "reel" else upload_video(api, path, caption)
        else:
            raise ValueError("Unsupported media_type: %s" % target.media_type)
        return {"media_id": mid, "source": source_username, "index": media_index}
    finally:
        for f in os.listdir(tmpdir):
            try: os.remove(os.path.join(tmpdir, f))
            except OSError: pass
        try: os.rmdir(tmpdir)
        except OSError: pass

def publish_from_file(api, file_path, caption, post_type="photo"):
    if post_type == "photo":
        mid = upload_photo(api, file_path, caption)
    elif post_type == "reel":
        mid = upload_reel(api, file_path, caption)
    else:
        mid = upload_video(api, file_path, caption)
    return {"media_id": mid}
