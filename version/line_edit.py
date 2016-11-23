"""line edit."""
import logging

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtWidgets import (
    QLineEdit,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class LineEdit(QLineEdit):
    """Custom Line Edit which sacrifices contextmenu for selectAll."""

    def __init__(self, parent=None):
        """__init__."""
        super().__init__(parent)

    def mousePressEvent(self, event):
        """mousePressEvent."""
        if event.button() == Qt.RightButton:
            self.selectAll()
        else:
            super().mousePressEvent(event)

    def contextMenuEvent(self, QContextMenuEvent):
        """contextMenuEvent."""
        pass
