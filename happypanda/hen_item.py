"""hen item."""
import logging

from PyQt5.QtCore import pyqtSignal

try:
    import app_constants
    import utils
    from downloader_item_obj import DownloaderItemObject
    from downloader_obj import DownloaderObject
    from ehen import EHen
except ImportError:
    from . import (
        app_constants,
        utils,
    )
    from .downloader_item_obj import DownloaderItemObject
    from .downloader_obj import DownloaderObject
    from .ehen import EHen

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class HenItem(DownloaderItemObject):
    """A convenience class that most methods in DLManager and it's subclasses returns."""

    thumb_rdy = pyqtSignal(object)

    def __init__(self, session=None):
        """init func."""
        super().__init__(session=session)
        # see also EH API on wiki https://ehwiki.org/wiki/API
        self.thumb_url = ""  # an url to gallery thumb
        self.cost = "0"
        self.size = ""
        self.metadata = {}
        self.gallery_name = ""
        self.gallery_url = ""
        self.download_type = app_constants.HEN_DOWNLOAD_TYPE
        self.torrents_found = 0
        #  will be filled later in fetch_thumb
        self.thumb = None
        #
        self.file_rdy.connect(self.check_type)

    def fetch_thumb(self):
        """Fetch thumbnail. Emits thumb_rdy, when done."""
        def thumb_fetched():
            self.thumb = self._thumb_item.file
            self.thumb_rdy.emit(self)
        self._thumb_item = DownloaderObject.add_to_queue(
            self.thumb_url, self.session, app_constants.temp_dir)
        self._thumb_item.file_rdy.connect(thumb_fetched)

    def check_type(self):
        """check type."""
        if self.download_type == 1:
            utils.open_torrent(self.file)

    def update_metadata(self, key, value):
        """update metadata.

        Recommended way of inserting metadata. Keeps the original EH API response structure
        Remember to call commit_metadata when done!

        Args:
            key: Key of the metadata.
            value: Value from the metadata with input key>
        """
        default_metadata = {
            "gid": 1,
            "title": "",
            "title_jpn": "",
            "category": "Manga",
            "uploader": "",
            "Posted": "",
            "filecount": "0",
            "filesize": 0,
            "expunged": False,
            "rating": "0",
            "torrentcount": "0",
            "tags": []
        }
        if not self.metadata:
            self.metadata = {
                "gmetadata": [default_metadata]
            }
        try:
            metadata = self.metadata['gmetadata'][0]
        except KeyError:
            return
        # replace new value
        metadata[key] = value
        # reapply the obj attribute
        self.metadata['gmetadata'][0] = metadata

    def commit_metadata(self):
        """Call this method when done updating metadata."""
        g_id = 'sample'
        try:
            d_m = {self.metadata['gmetadata'][0]['gid']: g_id}
        except KeyError:
            return
        self.metadata = EHen.parse_metadata(self.metadata, d_m)[g_id]
