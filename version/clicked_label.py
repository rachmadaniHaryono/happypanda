"""clicked label."""
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
)
from PyQt5.QtWidgets import (
    QLabel,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ClickedLabel(QLabel):
    """ClickedLabel.

    A QLabel which emits clicked signal on click
    """

    clicked = pyqtSignal(str)

    def __init__(self, s="", **kwargs):
        """__init__."""
        super().__init__(s, **kwargs)
        self.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)

    def enterEvent(self, event):
        """enterEvent."""
        if self.text():
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        return super().enterEvent(event)

    def mousePressEvent(self, event):
        """mousePressEvent."""
        self.clicked.emit(self.text())
        return super().mousePressEvent(event)
