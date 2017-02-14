"""arrow handle widget."""
import logging
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import (
    pyqtSignal,
    QPointF,
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPolygonF,
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


class ArrowHandleWidget(QWidget):
    """Arrow Handle.

    Args:
        parent (QtWidgets.QWidget): Parent widget.
    """

    IN, OUT = range(2)
    CLICKED = pyqtSignal(int)

    def __init__(self, parent):
        """init."""
        super().__init__(parent)
        self.parent_widget = parent
        self.current_arrow = self.IN
        self.arrow_height = 20
        self.setFixedWidth(10)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):  # NOQA
        """paint event.

        Args:
            event (QtGui.QPaintEvent): Paint event.
        """
        rect = self.rect()
        x, y, w, h = rect.getRect()
        painter = QPainter(self)
        painter.setPen(QColor("white"))
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.fillRect(rect, QColor(0, 0, 0, 100))

        arrow_points = []

        # for horizontal
        if self.current_arrow == self.IN:
            arrow_1 = QPointF(x + w, h / 2 - self.arrow_height / 2)
            middle_point = QPointF(x, h / 2)
            arrow_2 = QPointF(x + w, h / 2 + self.arrow_height / 2)
        else:
            arrow_1 = QPointF(x, h / 2 - self.arrow_height / 2)
            middle_point = QPointF(x + w, h / 2)
            arrow_2 = QPointF(x, h / 2 + self.arrow_height / 2)

        arrow_points.append(arrow_1)
        arrow_points.append(middle_point)
        arrow_points.append(arrow_2)
        painter.drawPolygon(QPolygonF(arrow_points))

    def click(self):
        """click function.."""
        if self.current_arrow == self.IN:
            self.current_arrow = self.OUT
            self.CLICKED.emit(1)
        else:
            self.current_arrow = self.IN
            self.CLICKED.emit(0)
        self.update()

    def mousePressEvent(self, event):  # NOQA
        """mouse press event.

        Args:
            event (QtGui.QMouseEvent): Mouse event.
        """
        if event.button() == Qt.LeftButton:
            self.click()
        return super().mousePressEvent(event)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    parent_widget = QtWidgets.QWidget()
    widget = ArrowHandleWidget(parent=parent_widget)
    parent_widget.show()

    sys.exit(app.exec_())
