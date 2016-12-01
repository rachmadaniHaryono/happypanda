"""star rating."""

import logging
import math

from PyQt5.QtCore import (
    QPointF,
    QRectF,
    QSize,
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPolygonF,
)


log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class StarRating():
    """star rating."""

    # enum EditMode
    Editable, ReadOnly = range(2)

    PaintingScaleFactor = 18

    def __init__(self, starCount=1, maxStarCount=5):
        """init func."""
        self._starCount = starCount
        self._maxStarCount = maxStarCount

        self.starPolygon = QPolygonF([QPointF(1.0, 0.5)])
        for i in range(5):
            args = list(map(
                lambda func: 0.5 + 0.5 * func(0.8 * i * math.pi), [math.cos, math.sin]
            ))
            self.starPolygon << QPointF(*args)

        self.diamondPolygon = QPolygonF()
        self.diamondPolygon << QPointF(0.4, 0.5) \
                            << QPointF(0.5, 0.4) \
                            << QPointF(0.6, 0.5) \
                            << QPointF(0.5, 0.6) \
                            << QPointF(0.4, 0.5)

    def starCount(self):
        """start count."""
        return self._starCount

    def maxStarCount(self):
        """max start count."""
        return self._maxStarCount

    def setStarCount(self, starCount):
        """set start count."""
        self._starCount = starCount

    def setMaxStarCount(self, maxStarCount):
        """set max star count."""
        self._maxStarCount = maxStarCount

    def sizeHint(self):
        """size hint."""
        return self.PaintingScaleFactor * QSize(self._maxStarCount, 1)

    def paint(self, painter, rect, editMode=ReadOnly):
        """paint."""
        painter.save()

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.drawRoundedRect(QRectF(rect), 2, 2)

        painter.setBrush(QBrush(Qt.yellow))

        scaleFactor = self.PaintingScaleFactor
        yOffset = (rect.height() - scaleFactor) / 2
        painter.translate(rect.x(), rect.y() + yOffset)
        painter.scale(scaleFactor, scaleFactor)

        for i in range(self._maxStarCount):
            if i < self._starCount:
                painter.drawPolygon(self.starPolygon, Qt.WindingFill)
            elif editMode == StarRating.Editable:
                painter.drawPolygon(self.diamondPolygon, Qt.WindingFill)

            painter.translate(1.0, 0.0)

        painter.restore()
