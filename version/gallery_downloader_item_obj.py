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

try:
    from hen_item import HenItem
except ImportError:
    from .hen_item import HenItem

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

        Args:
            hitem(:class:`.pewnet.HenItem`):H-item
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
        type = 'Archive' if hitem.download_type == 0 else 'Torrent'
        self.type_item = QTableWidgetItem(type)
        self.type_item.setToolTip(url)
        # status_timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(
            self.check_progress_when_status_timer_timeout)
        self.status_timer.start(500)

    def item_file_ready(self):
        """run when item file ready."""
        self.status_item.setText('Finished!')
        self.d_item_ready.emit(self)

    def check_progress_when_status_timer_timeout(self):
        """check progress when status_timer timeout."""
        btomb = 1048576
        if self.item.current_state == self.item.DOWNLOADING:
            self.status_item.setText(
                "{0:.2f}/{1:.2f} MB".format(
                    self.item.current_size / btomb, self.item.total_size / btomb
                )
            )
            self.size_item.setText("{0:.2f} MB".format(
                self.item.total_size / btomb))
        elif self.item.current_state == self.item.CANCELLED:
            self.status_item.setText("Cancelled!")
            self.status_timer.stop()

    def d_item_ready_finished(self):
        """Run the function when d-item ready."""
        self.status_timer.stop()
        if self.item.download_type == 0:
            self.status_item.setText("Creating gallery...")
        else:
            self.status_item.setText("Sent to torrent client!")
