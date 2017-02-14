"""moved popup."""
import logging
import os

from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QPixmap,
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

try:
    import utils
    from base_popup import BasePopup
except ImportError:
    from .base_popup import BasePopup
    from . import utils

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


class MovedPopup(BasePopup):
    """popup when moved.

    Args:
        new_path:New path.
        gallery:Gallery.
        parent:Parent.
    Attributes:
        UPDATE_SIGNAL:Signal when updated.
        _new_path:New path.
        _gallery:Gallery.
    """

    UPDATE_SIGNAL = pyqtSignal(object)

    def __init__(self, new_path, gallery, parent=None):
        """init func."""
        super().__init__(parent)
        self._new_path = new_path
        self._gallery = gallery
        #
        main_layout = QVBoxLayout()
        inner_layout = QHBoxLayout()
        # title
        title = QLabel(gallery.title)
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignCenter)
        title.adjustSize()
        main_layout.addWidget(title)
        # cover
        cover = QLabel()
        img = QPixmap(gallery.profile)
        cover.setPixmap(img)
        inner_layout.addWidget(cover)
        # text_label
        text = QLabel(
            "The path to this gallery has been renamed\n\n{}\n{}\n{}".format(
                os.path.basename(gallery.path),
                u'\u2192',
                os.path.basename(new_path)
            )
        )
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignCenter)
        inner_layout.addWidget(text)
        #
        button_layout = QHBoxLayout()
        # update_btn
        update_btn = QPushButton('Update')
        update_btn.clicked.connect(self.commit_when_update_btn_clicked)
        button_layout.addWidget(update_btn)
        # close_btn
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.cancel_when_close_btn_clicked)
        button_layout.addWidget(close_btn)
        #
        main_layout.addLayout(inner_layout)
        main_layout.addLayout(button_layout)
        self.main_widget.setLayout(main_layout)
        #
        self.show()

    def commit_when_update_btn_clicked(self):
        """commit when update buttton clicked."""
        g = utils.update_gallery_path(self._new_path, self._gallery)
        self.UPDATE_SIGNAL.emit(g)
        self.close()

    def cancel_when_close_btn_clicked(self):
        """Cancel when close button clicked."""
        self._gallery.dead_link = True
        self.close()
