import logging
from pathlib import Path
logger = logging.getLogger("SAMMODZZ.media")

def upload_photo(api, image_path, caption):
    media = api._call(api.cl.photo_upload, Path(image_path), caption=caption)
    return str(media.pk)

def upload_video(api, video_path, caption, thumbnail=None):
    media = api._call(api.cl.video_upload, Path(video_path), caption=caption, thumbnail=Path(thumbnail) if thumbnail else None)
    return str(media.pk)

def upload_reel(api, video_path, caption, thumbnail=None):
    media = api._call(api.cl.clip_upload, Path(video_path), caption=caption, thumbnail=Path(thumbnail) if thumbnail else None)
    return str(media.pk)
