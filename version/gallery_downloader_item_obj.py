"""gallery downloader item object."""
import logging

from PyQt5.QtCore import (
    Qt,
    QObject,
    pyqtSignal,
    QTimer,
)
from PyQt5.QtGui import (
    QIcon,
)
from PyQt5.QtWidgets import (
    QTableWidgetItem,
)

try:  # pragma: no cover
    from hen_item import HenItem
    import app_constants
except ImportError:
    from .hen_item import HenItem
    from . import app_constants

log = logging.getLogger(__name__)
""":class:`logging.Logger`: Logger for module."""
log_i = log.info
""":meth:`logging.Logger.info`: Info logger func"""
log_d = log.debug
""":meth:`logging.Logger.debug`: Debug logger func"""
log_w = log.warning
""":meth:`logging.Logger.warning`: Warning logger func"""
log_e = log.error
""":meth:`logging.Logger.error`: Error logger func"""
log_c = log.critical
""":meth:`logging.Logger.critical`: Critical logger func"""


class GalleryDownloaderItemObject(QObject):
    """Receives a HenItem.

    Args:
        hitem(:class:`.pewnet.HenItem`):H-item

    Attributes:
        status_timer(:class:`PyQt5.QtCore.QTimer`):Status timer.
        d_item_ready(:class:`PyQt5.QtCore.pyqtSignal`):Signal when data item ready.
        cost_item(:class:`PyQt5.QtWidgets.QTableWidgetItem`):Cost item.
        profile_item(:class:`PyQt5.QtWidgets.QTableWidgetItem`):Profile item.
        size_item(:class:`PyQt5.QtWidgets.QTableWidgetItem`):Size item.
        status_item(:class:`PyQt5.QtWidgets.QTableWidgetItem`):Status item.
        type_item(:class:`PyQt5.QtWidgets.QTableWidgetItem`):Type item.
        hitem(:class:`.pewnet.HenItem`):H-item.
    """

    d_item_ready = pyqtSignal(object)

    def __init__(self, hitem):
        """init func.

        """
        super().__init__()
        self.d_item_ready.connect(self.d_item_ready_finished)
        # item
        assert isinstance(hitem, HenItem)
        self.item = hitem
        url = self.item.gallery_url
        # profile item
        self.profile_item = QTableWidgetItem(self.item.name)
        self.profile_item.setData(Qt.UserRole + 1, hitem)
        self.profile_item.setToolTip(url)
        self.item.thumb_rdy.connect(
            lambda:
            self.profile_item.setIcon(QIcon(self.item.thumb))
        )
        # status
        self.status_item = QTableWidgetItem('In queue...')
        self.status_item.setToolTip(url)
        self.item.file_rdy.connect(self.item_file_ready)
        # cost_item
        self.cost_item = QTableWidgetItem(self.item.cost)
        self.cost_item.setToolTip(url)
        # size_item
        self.size_item = QTableWidgetItem(self.item.size)
        self.size_item.setToolTip(url)
        # type_item
        type_ = app_constants.DOWNLOAD_TYPE_DICT_CONSTANT[hitem.download_type]
        self.type_item = QTableWidgetItem(type_)
        self.type_item.setToolTip(url)
        # status_timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_progress)
        self.status_timer.start(500)
        # set default download type to None
        # download manager have to change it to valid type on app_constants
        self.download_type = None

    def item_file_ready(self):
        """run when item file ready."""
        self.status_item.setText('Finished!')
        self.d_item_ready.emit(self)

    @staticmethod
    def _get_readable_item_total_size(item):
        """Get readable item's total size.
        Args:
            item: Download item.

        Returns:
            str: Readable item's total size.
        """
        btomb = 1048576
        return "{0:.2f} MB".format(item.total_size / btomb)

    @staticmethod
    def _get_progress_status_item_text(item):
        """Get status item text on progress.

        Args:
            item: Download item.

        Returns:
            str: Status item text.
        """
        btomb = 1048576
        if item.current_state == item.DOWNLOADING:
            return "{0:.2f}/{1:.2f} MB".format(
                item.current_size / btomb,
                item.total_size / btomb
            )
        elif item.current_state == item.CANCELLED:
            return "Cancelled!"
        else:
            log_w('Unknown state: {}'.format(item.current_state))
            return

    def check_progress(self):
        """check progress when status_timer timeout."""
        status_item_text = self._get_progress_status_item_text(item=self.item)
        if status_item_text:
            self.status_item.setText(status_item_text)

        if self.item.current_state == self.item.DOWNLOADING:
            self.size_item.setText(self._get_readable_item_total_size(item=self.item))
        elif self.item.current_state == self.item.CANCELLED:
            self.status_timer.stop()

    def d_item_ready_finished(self):
        """Run the function when downloaded item ready."""
        self.status_timer.stop()
        default_text = 'Finished!'
        status_item_text_dict = {
            app_constants.DOWNLOAD_TYPE_ARCHIVE: "Creating gallery...",
            app_constants.DOWNLOAD_TYPE_TORRENT: "Sent to torrent client!",
        }
        status_item_text = status_item_text_dict.get(self.item.download_type, default_text)
        self.status_item.setText(status_item_text)
