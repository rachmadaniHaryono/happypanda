"""nhen module."""
import logging

try:
    import app_constants
    import settings
    from commenhen import CommenHen
except ImportError:
    from . import (
        app_constants,
        settings,
    )
    from .commenhen import CommenHen

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class NHen(CommenHen):
    """Fetches galleries from nhen."""

    LOGIN_URL = "http://nhentai.net/login/"

    @classmethod
    def login(cls, user, password):
        """login."""
        exprops = settings.ExProperties(settings.ExProperties.NHENTAI)
        if cls.COOKIES:
            if cls.check_login(cls.COOKIES):
                return cls.COOKIES
        elif exprops.cookies:
            if cls.check_login(exprops.cookies):
                cls.COOKIES.update(exprops.cookies)
                return cls.COOKIES

        cls._browser.open(cls.LOGIN_URL)
        login_form = cls._browser.get_form()
        if login_form:
            login_form['username'].value = user
            login_form['password'].value = password
            cls._browser.submit_form(login_form)

        n_c = cls._browser.session.cookies.get_dict()
        if not cls.check_login(n_c):
            log_w("NH login failed")
            raise app_constants.WrongLogin

        log_i("NH login succes")
        exprops.cookies = n_c
        exprops.username = user
        exprops.password = password
        exprops.save()
        cls.COOKIES.update(n_c)
        return n_c

    @classmethod
    def check_login(cls, cookies):
        """check login."""
        if "sessionid" in cookies:
            return True

    @classmethod
    def apply_metadata(cls, gallery, data, append=True):
        """apply metadata."""
        return super().apply_metadata(gallery, data, append)

    def search(self, search_string, cookies=None, **kwargs):
        """search."""
        pass
