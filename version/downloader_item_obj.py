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
    """Convenience class for downloader item object.

    Attributes:
        IN_QUEUE (int): 'IN_QUEUE' state.
        DOWNLOADING (int): 'DOWNLOADING' state.
        FINISHED (int): 'FINISHED' state.
        CANCELLED (int): 'CANCEl' state.
        file_rdy (PyQt5.QtCore.pyqtSignal): Signal when file is ready.
        session: Session for item.
        download_url (str): Download url.
        file (str): item's File.
        name (str): Item's name.
        total_size (int): Item's total size.
        current_size (int): Item's current size.
        current_state (int): Item's current state.

    """

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
        """Set current state to 'CANCELLED'."""
        self.current_state = self.CANCELLED

    def open(self, containing=False):
        """Open item.

        Args:
            containing (bool): Open parent directory if True
        """
        if self.file:
            if containing:
                p = os.path.split(self.file)[0]
                utils.open_path(p, self.file)
            else:
                utils.open_path(self.file)
