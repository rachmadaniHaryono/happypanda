"""moduel for list widget in gallery downloader."""
import logging
import os

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    QSize,
)
from PyQt5.QtGui import (
    QColor,
)
from PyQt5.QtWidgets import (
    QMenu,
    QTableWidget,
    qApp,
)

try:
    import app_constants
    import pewnet
    from fetch_obj import FetchObject
    from gallery_downloader_item_obj import GalleryDownloaderItemObject
except ImportError:
    from .fetch_obj import FetchObject
    from .gallery_downloader_item_obj import GalleryDownloaderItemObject
    from . import (
        app_constants,
        pewnet,
    )

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


class GalleryDownloaderListWidget(QTableWidget):
    """list widget for gallery downloader.

    Args:
        app_inst:Application instance.
        parent:Parent widget.
    Attributes:
        init_fetch_instance(:class:`PyQt5.QtCore.pyqtSignal`):Signal when fetch instance initiated.
        fetch_instance(:class:`.fetch_obj.FetchObject`):Fetch instance.
    """

    init_fetch_instance = pyqtSignal(list)

    def __init__(self, app_inst, parent=None):
        """init func."""
        super().__init__(parent)
        self.app_inst = app_inst
        #
        self.setColumnCount(5)
        self.setIconSize(QSize(50, 100))
        self.setAlternatingRowColors(True)
        self.setEditTriggers(self.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        # vertical header
        v_header = self.verticalHeader()
        v_header.setSectionResizeMode(v_header.Fixed)
        v_header.setDefaultSectionSize(100)
        v_header.hide()
        #
        self.setDragEnabled(False)
        self.setShowGrid(True)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.SingleSelection)
        self.setSortingEnabled(True)
        # palle
        palette = self.palette()
        palette.setColor(palette.Highlight, QColor(88, 88, 88, 70))
        palette.setColor(palette.HighlightedText, QColor('black'))
        self.setPalette(palette)
        #
        self.setHorizontalHeaderLabels(
            [' ', 'Status', 'Size', 'Cost', 'Type'])
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(0, self.horizontalHeader().Stretch)
        self.horizontalHeader().setSectionResizeMode(
            1, self.horizontalHeader().ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(
            2, self.horizontalHeader().ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(
            3, self.horizontalHeader().ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(
            4, self.horizontalHeader().ResizeToContents)
        # fetch_instance
        self.fetch_instance = FetchObject()
        self.fetch_instance.download_items = []
        self.fetch_instance.FINISHED.connect(self._gallery_to_model)
        self.fetch_instance.moveToThread(app_constants.GENERAL_THREAD)
        self.init_fetch_instance.connect(self.fetch_instance.local)
        #
        self.doubleClicked.connect(self.widget_double_clicked)

    def widget_double_clicked(self, idx):
        """Run the funciton when widget double clicked.

        Args:
            idx:Index
        """
        hitem = self._get_hitem(idx)
        if hitem.current_state == hitem.DOWNLOADING:
            hitem.open(True)

    def add_entry(self, hitem):
        """Add entry.

        Args:
            hitem(:class:`.pewnet.HenItem`):H-item
        """
        assert isinstance(hitem, pewnet.HenItem)
        g_item = GalleryDownloaderItemObject(hitem)
        if hitem.download_type == 0:
            g_item.d_item_ready.connect(self._init_gallery)

        self.insertRow(0)
        self.setSortingEnabled(False)
        self.setItem(0, 0, g_item.profile_item)
        self.setItem(0, 1, g_item.status_item)
        self.setItem(0, 2, g_item.size_item)
        self.setItem(0, 3, g_item.cost_item)
        self.setItem(0, 4, g_item.type_item)
        self.setSortingEnabled(True)

    def _get_hitem(self, idx):
        """get h-item.

        Args:
            idx:Index
        Returns:
            Item.
        """
        r = idx.row()
        return self.item(r, 0).data(Qt.UserRole + 1)

    def contextMenuEvent(self, event):  # NOQA
        """context menu when event is triggered.

        Args:
            event:Event
        """
        idx = self.indexAt(event.pos())
        if idx.isValid():
            hitem = self._get_hitem(idx)
            clipboard = qApp.clipboard()
            menu = QMenu()
            if hitem.current_state == hitem.DOWNLOADING:
                menu.addAction("Cancel", hitem.cancel)
            if hitem.current_state == hitem.FINISHED:
                menu.addAction("Open", hitem.open)
                menu.addAction("Show in folder", lambda: hitem.open(True))
            menu.addAction("Copy path", lambda: clipboard.setText(hitem.file))
            menu.addAction("Copy gallery URL",
                           lambda: clipboard.setText(hitem.gallery_url))
            menu.addAction("Copy download URL",
                           lambda: clipboard.setText(hitem.download_url))
            if not hitem.current_state == hitem.DOWNLOADING:
                menu.addAction("Remove", lambda: self.removeRow(idx.row()))
            menu.exec_(event.globalPos())
            event.accept()
            del menu
        else:
            event.ignore()

    def _init_gallery(self, download_item):
        """Init gallery.

        Args:
            download_item(:class:`GalleryDownloaderItemObject`):Downloaded item.
        """
        assert isinstance(download_item, GalleryDownloaderItemObject)
        app_constants.TEMP_PATH_IGNORE.append(
            os.path.normcase(download_item.item.file))
        self.fetch_instance.download_items.append(download_item)
        self.init_fetch_instance.emit([download_item.item.file])

    def _gallery_to_model(self, gallery_list):
        """Gallery to model.

        Args:
            gallery_list:Gallery list.
        """
        log_i("Adding downloaded gallery to library")
        try:
            d_item = self.fetch_instance.download_items.pop(0)
        except IndexError:
            return
        if gallery_list:
            gallery = gallery_list[0]
            gallery.link = d_item.item.gallery_url
            if d_item.item.metadata:
                gallery = pewnet.EHen.apply_metadata(
                    gallery, d_item.item.metadata)
            if app_constants.DOWNLOAD_GALLERY_TO_LIB:
                self.app_inst.default_manga_view.add_gallery(gallery, True)
                d_item.status_item.setText('Added to library!')
                log_i("Added downloaded gallery to library")
            else:
                self.app_inst.addition_tab.view.add_gallery(gallery, True)
                d_item.status_item.setText('Added to inbox!')
                log_i("Added downloaded gallery to inbox")
        else:
            d_item.status_item.setText('Gallery could not be added!')
            log_i("Could not add downloaded gallery to library")

    def clear_list(self):
        """Clear list."""
        for r in range(self.rowCount() - 1, -1, -1):
            status = self.item(r, 1)
            if '!' in status.text():
                self.removeRow(r)
