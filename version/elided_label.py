"""elided label."""
import logging

from PyQt5.QtCore import (
    Qt,
)
from PyQt5.QtGui import (
    QFontMetrics,
    QPainter,
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


class ElidedLabel(QLabel):
    """ElidedLabel."""

    def __init__(self, *args, **kwargs):
        """init func."""
        super().__init__(*args, **kwargs)

    def paintEvent(self, event):  # NOQA
        """paintEvent."""
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)
