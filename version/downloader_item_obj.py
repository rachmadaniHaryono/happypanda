"""dl item obj."""
import logging
import os

from PyQt5.QtCore import QObject, pyqtSignal

try:
    import utils
except ImportError:
    from . import (
        utils,
    )

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class DownloaderItemObject(QObject):
    """Convenience class."""

    IN_QUEUE, DOWNLOADING, FINISHED, CANCELLED = range(4)
    file_rdy = pyqtSignal(object)

    def __init__(self, url="", session=None):
        """init func."""
        super().__init__()
        self.session = session
        self.download_url = url
        self.file = ""
        self.name = ""

        self.total_size = 0
        self.current_size = 0
        self.current_state = self.IN_QUEUE

    def cancel(self):
        """cancel."""
        self.current_state = self.CANCELLED

    def open(self, containing=False):
        """open."""
        if self.file:
            if containing:
                p = os.path.split(self.file)[0]
                utils.open_path(p, self.file)
            else:
                utils.open_path(self.file)
