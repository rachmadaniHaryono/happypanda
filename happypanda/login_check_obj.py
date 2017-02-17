"""module for login check obj."""
from PyQt5.QtCore import QObject

from . import settings
from .ehen import EHen


class LoginCheckObject(QObject):
    """login check object."""

    def __init__(self):
        super().__init__()

    def check(self):
        """check login."""
        for s in settings.ExProperties.sites:
            ex = settings.ExProperties(s)
            if ex.cookies:
                if s == settings.ExProperties.EHENTAI:
                    EHen.check_login(ex.cookies)
