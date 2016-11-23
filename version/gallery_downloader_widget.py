"""gallery downloader widget."""
import logging

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtGui import (
    QIcon,
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

try:
    import app_constants
    from gallery_downloader_list_widget import GalleryDownloaderListWidget
    from gallery_downloader_url_extractor_widget import GalleryDownloaderUrlExtractorWidget
except ImportError:
    from . import (
        app_constants,
    )
    from .gallery_downloader_list_widget import GalleryDownloaderListWidget
    from .gallery_downloader_url_extractor_widget import GalleryDownloaderUrlExtractorWidget


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


class GalleryDownloaderWidget(QWidget):
    """A gallery downloader window.

    Args:
        parent:Parent widget.
    Attributes:
        parent_widget:Parent widget
        download_list(:class:`GalleryDownloaderListWidget`):Download list widget.
        url_inserter(:class:`PyQt5.QtWidgets.QLineEdit`):Line editor for url.
        info_lbl(:class:`PyQt5.QtWidgets.QLabel`):Info label.
    """

    def __init__(self, parent):
        """init func."""
        super().__init__(
            None, Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        main_layout = QVBoxLayout(self)
        self.parent_widget = parent
        self.download_list = GalleryDownloaderListWidget(parent, self)
        # url_inserter
        self.url_inserter = QLineEdit()
        self.url_inserter.setPlaceholderText("Hover to see supported URLs")
        self.url_inserter.setToolTip(app_constants.SUPPORTED_DOWNLOAD_URLS)
        self.url_inserter.setToolTipDuration(999999999)
        self.url_inserter.returnPressed.connect(self.add_download_entry)
        main_layout.addWidget(self.url_inserter)
        # info label
        self.info_lbl = QLabel(self)
        self.info_lbl.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_lbl)
        self.info_lbl.hide()
        # buttons_layout
        buttons_layout = QHBoxLayout()
        url_window_btn = QPushButton('Batch URLs')
        url_window_btn.adjustSize()
        url_window_btn.setFixedWidth(url_window_btn.width())
        url_window_btn.clicked.connect(
            self.open_batch_url_window_when_url_window_btn_clicked)
        buttons_layout.addWidget(url_window_btn, 0, Qt.AlignLeft)
        # clear_all_btn
        clear_all_btn = QPushButton('Clear List')
        clear_all_btn.adjustSize()
        clear_all_btn.setFixedWidth(clear_all_btn.width())
        clear_all_btn.clicked.connect(self.download_list.clear_list)
        buttons_layout.addWidget(clear_all_btn, 0, Qt.AlignRight)
        #
        main_layout.addLayout(buttons_layout)
        # download_list_scroll
        download_list_scroll = QScrollArea(self)
        download_list_scroll.setBackgroundRole(self.palette().Base)
        download_list_scroll.setWidgetResizable(True)
        download_list_scroll.setWidget(self.download_list)
        main_layout.addWidget(download_list_scroll, 1)
        # close_button
        close_button = QPushButton('Close', self)
        close_button.clicked.connect(self.hide)
        main_layout.addWidget(close_button)
        #
        self.resize(480, 600)
        self.setWindowIcon(QIcon(app_constants.APP_ICO_PATH))

    def open_batch_url_window_when_url_window_btn_clicked(self):
        """Open batch url window hen url window button clicked."""
        self._batch_url = GalleryDownloaderUrlExtractorWidget()
        self._batch_url.url_emit.connect(self.add_download_entry)

    def add_download_entry(self, url=None):
        """add download entry.

        Args:
            url(str):Url of download entry.
        """
        log_i('Adding download entry: {}'.format(url))
        self.info_lbl.hide()
        h_item = None
        try:
            if not url:
                url = self.url_inserter.text()
                if not url:
                    return
                self.url_inserter.clear()
            url = url.lower()

            manager = self.website_validator(url)
            h_item = manager.from_gallery_url(url)
        except app_constants.WrongURL:
            self.info_lbl.setText(
                "<font color='red'>Failed to add:\n{}</font>".format(url))
            self.info_lbl.show()
            return
        except app_constants.NeedLogin:
            self.info_lbl.setText(
                "<font color='red'>Login is required to download:\n{}</font>".format(url))
            self.info_lbl.show()
            return
        except app_constants.WrongLogin:
            self.info_lbl.setText(
                "<font color='red'Wrong login info to download:\n{}</font>".format(url))
            self.info_lbl.show()
            return
        if h_item:
            log_i('Successfully added download entry')
            self.download_list.add_entry(h_item)

    def show(self):
        """show widget."""
        if self.isVisible():
            self.activateWindow()
        else:
            super().show()
