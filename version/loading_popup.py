"""loading popup."""
import logging

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtWidgets import (
    QLabel,
    QProgressBar,
    QVBoxLayout,
)

try:
    from base_popup import BasePopup
except ImportError:
    from .base_popup import BasePopup

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class LoadingPopup(BasePopup):
    """Loading."""

    ON = False  # to prevent multiple instances

    def __init__(self, parent=None):
        """__init__."""
        super().__init__(parent)
        self.progress = QProgressBar()
        self.progress.setStyleSheet("color:white")
        self.text = QLabel()
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setStyleSheet("color:white;background-color:transparent;")
        inner_layout_ = QVBoxLayout()
        inner_layout_.addWidget(self.text, 0, Qt.AlignHCenter)
        inner_layout_.addWidget(self.progress)
        self.main_widget.setLayout(inner_layout_)
        self.resize(300, 100)
        # frect = self.frameGeometry()
        #  frect.moveCenter(QDesktopWidget().availableGeometry().center())
        #  self.move(parent.window().frameGeometry().topLeft() +
        # 	parent.window().rect().center() -
        # 	self.rect().center() - QPoint(self.rect().width(),0))
        #  self.setAttribute(Qt.WA_DeleteOnClose)
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

    def setText(self, string):
        """setText."""
        if string != self.text.text():
            self.text.setText(string)
