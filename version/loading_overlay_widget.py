"""loading overlay widget."""
import logging
import math

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPalette,
    QPen,
)
from PyQt5.QtWidgets import (
    QWidget,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class LoadingOverlayWidget(QWidget):
    """LoadingOverlay."""

    def __init__(self, parent=None):
        """__init__."""
        super().__init__(parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)

    def paintEngine(self, event):
        """paintEngine."""
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(),
                         QBrush(QColor(255, 255, 255, 127)))
        painter.setPen(QPen(Qt.NoPen))
        for i in range(6):
            if (self.counter / 5) % 6 == i:
                painter.setBrush(
                    QBrush(QColor(127 + (self.counter % 5) * 32, 127, 127)))
            else:
                painter.setBrush(QBrush(QColor(127, 127, 127)))
                painter.drawEllipse(self.width() / 2 + 30 * math.cos(2 * math.pi * i / 6.0) - 10,
                                    self.height() / 2 + 30 * math.sin(2 * math.pi * i / 6.0) - 10,
                                    20, 20)

        painter.end()

    def showEvent(self, event):
        """showEvent."""
        self.timer = self.startTimer(50)
        self.counter = 0
        super().showEvent(event)

    def timerEvent(self, event):
        """timerEvent."""
        self.counter += 1
        self.update()
        if self.counter == 60:
            self.killTimer(self.timer)
            self.hide()
