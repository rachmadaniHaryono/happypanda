"""star rating."""
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


class StarRating():
    """star rating.

    Args:
        starCount (int): Star count.
        maxStarCount (int): Maximum star count.

    Attributes:
        _starCount (int): Star count.
        _maxStarCount (int): Maximum star count.
        starPolygon (QPolygonF): Star polygon.
        diamondPolygon (QPolygonF): Diamond polygon.

    """

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
        """Returns start count.

        Returns:
            int: Star count.
        """
        return self._starCount

    def maxStarCount(self):
        """Returns maximum start count.

        Returns:
            int: Maximum star count.
        """
        return self._maxStarCount

    def setStarCount(self, starCount):
        """set start count.

        Args:
            starCount (int): Star count.
        """
        self._starCount = starCount

    def setMaxStarCount(self, maxStarCount):
        """set maxmum star count.

        Args:
            maxStarCount (int): Maximum star count.
        """
        self._maxStarCount = maxStarCount

    def sizeHint(self):
        """Return size hint.

        Returns:
            Size hint.
        """
        return self.PaintingScaleFactor * QSize(self._maxStarCount, 1)

    def paint(self, painter, rect, editMode=ReadOnly):
        """paint.

        Args:
            painter: Painter.
            rect: Rectangle.
            editMode: Edit mode.
        """
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
