"""elided label."""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import (
    QFontMetrics,
    QPainter,
)


class ElidedLabel(QLabel):
    """ElidedLabel."""

    def __init__(self, *args, **kwargs):
        """init func."""
        super().__init__(*args, **kwargs)

    def paintEvent(self, event):  # NOQA
        """paint event.

        Args:
            event (QPaintEvent): Paint event.
        """
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)
