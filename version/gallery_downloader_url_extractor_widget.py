"""module url extractor widget for gallery downloader."""
import logging

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QIcon,
    QTextOption,
)
from PyQt5.QtWidgets import (
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

try:
    import app_constants
except ImportError:
    from . import (
        app_constants,
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


class GalleryDownloaderUrlExtractorWidget(QWidget):
    """widget for url extractor in gallery downloader.

    Args:
        parent:Parent widget.
    Attributes:
        url_emit(:class:`PyQt5.QtCore.pyqtSignal`):Signal when url emitted.
        main_layout(:class:`PyQt5.QtWidgets.QVBoxLayout`):Main layout.
        text_area_editor(:class:`PyQt5.QtWidgets.QPlainTextEdit`):Text area editor.
        add_to_queue_btn(:class:`PyQt5.QtWidgets.QPushButton`):Add to queue button.
    """

    url_emit = pyqtSignal(str)

    def __init__(self, parent=None):
        """init func."""
        super().__init__(parent, flags=Qt.Window | Qt.WindowStaysOnTopHint)
        # main layout
        self.main_layout = QVBoxLayout(self)
        # text_area_editor
        self.text_area_editor = QPlainTextEdit(self)
        self.text_area_editor.setPlaceholderText(
            "URLs are seperated by a newline")
        self.main_layout.addWidget(self.text_area_editor)
        self.text_area_editor.setWordWrapMode(QTextOption.NoWrap)
        # add_to_queue_btn
        add_to_queue_btn = QPushButton('Add to queue')
        add_to_queue_btn.adjustSize()
        add_to_queue_btn.setFixedWidth(add_to_queue_btn.width())
        add_to_queue_btn.clicked.connect(self.add_to_queue_btn_clicked)
        #
        self.main_layout.addWidget(add_to_queue_btn, 0, Qt.AlignRight)
        self.setWindowIcon(QIcon(app_constants.APP_ICO_PATH))
        self.show()

    def add_to_queue_btn_clicked(self):
        """add func when event triggered."""
        txt = self.text_area_editor.document().toPlainText()
        urls = txt.split('\n')
        for u in urls:
            if u:
                self.url_emit.emit(u)
        self.close()
