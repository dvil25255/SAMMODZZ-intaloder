import logging
from instagram.session_login import get_client, relogin
logger = logging.getLogger("SAMMODZZ.api")

class InstagramAPI:
    def __init__(self):
        self.cl = get_client()
    def _call(self, method, *args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as e:
            if "login_required" in str(e).lower():
                logger.warning("Session expired; relogging.")
                self.cl = relogin(self.cl)
                return method(*args, **kwargs)
            raise
    def user_id_from_username(self, username):
        return self._call(self.cl.user_id_from_username, username)
    def user_medias(self, user_id, amount=10):
        return self._call(self.cl.user_medias, user_id, amount)
    def photo_download(self, media_pk, folder=""):
        return str(self._call(self.cl.photo_download, media_pk, folder=folder))
    def video_download(self, media_pk, folder=""):
        return str(self._call(self.cl.video_download, media_pk, folder=folder))
