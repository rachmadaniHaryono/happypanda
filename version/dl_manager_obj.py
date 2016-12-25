"""downloader manager object."""
from robobrowser import RoboBrowser

from PyQt5.QtCore import QObject

try:
    import app_constants
except ImportError:
    from . import (
        app_constants,
    )


class DLManagerObject(QObject):
    """Base class for site-specific download managers."""

    _browser = RoboBrowser(
        history=True,
        user_agent="Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
        parser='html.parser',
        allow_redirects=False)
    # download type
    ARCHIVE, TORRENT = False, False

    def __init__(self):
        """init func."""
        super().__init__()
        self.ARCHIVE, self.TORRENT = False, False
        if app_constants.HEN_DOWNLOAD_TYPE == app_constants.DOWNLOAD_TYPE_ARCHIVE:
            self.ARCHIVE = True
        elif app_constants.HEN_DOWNLOAD_TYPE == app_constants.DOWNLOAD_TYPE_TORRENT:
            self.TORRENT = True

    def _error(self):
        """error."""
        pass

    def from_gallery_url(self, url):
        """From gallery url.

        Needs to be implemented in site-specific subclass
        URL checking  and class instantiating is done in GalleryDownloader class in io_misc.py
        Basic procedure for this method:
        - open url with self._browser and do the parsing
        - create HenItem and fill out it's attributes
        - specify download type (important)... 0 for archive and 1 for torrent 2 for other
        - fetch optional thumbnail on HenItem
        - set download url on HenItem (important)
        - add h_item to download queue
        - return h-item if everything went successfully, else return none

        Metadata should imitiate the offical EH API response.
        It is recommended to use update_metadata in HenItem when adding metadata
        see the ChaikaManager class for a complete example
        EH API: http://ehwiki.org/wiki/API
        """
        raise NotImplementedError
