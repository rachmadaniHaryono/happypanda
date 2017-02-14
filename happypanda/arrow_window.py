"""arrow window."""
import logging
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import (
    QPointF,
    QRectF,
    QSizeF,
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QPainter,
    QPaintEvent,
    QPolygonF,
)
from PyQt5.QtWidgets import (
    QCommonStyle,
    QStyleOption,
)

try:
    from transparent_widget import TransparentWidget
except ImportError:
    from .transparent_widget import TransparentWidget

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ArrowWindow(TransparentWidget):
    """ArrowWindow.

    Args:
        parent (QtWidgets.QWidget): Parent widget.
    """

    LEFT, RIGHT, TOP, BOTTOM = range(4)

    def __init__(self, parent):
        """init."""
        super().__init__(parent, flags=Qt.Window | Qt.FramelessWindowHint, move_listener=False)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.resize(550, 300)
        self.direction = self.LEFT
        self._arrow_size = QSizeF(30, 30)
        self.content_margin = 0

    @property
    def arrow_size(self):
        """Arrow size."""
        return self._arrow_size

    @arrow_size.setter
    def arrow_size(self, w_h_tuple):
        """Set arrow size.

        Args:
            w_h_tuple (tuple or list):A tuple or list of width and height.
        """
        if not isinstance(w_h_tuple, (tuple, list)) or len(w_h_tuple) != 2:
            return

        if self.direction in (self.LEFT, self.RIGHT):
            s = QSizeF(w_h_tuple[1], w_h_tuple[0])
        else:
            s = QSizeF(w_h_tuple[0], w_h_tuple[1])

        self._arrow_size = s
        self.update()

    def paintEvent(self, event):  # NOQA
        """paintEvent.

        Args:
            event (QtGui.QPaintEvent): Paint event.
        """
        assert isinstance(event, QPaintEvent)

        opt = QStyleOption()
        opt.initFrom(self)

        painter = QPainter(self)
        painter.setRenderHint(painter.Antialiasing)

        size = self.size()
        if self.direction in (self.LEFT, self.RIGHT):
            actual_size = QSizeF(
                size.width() - self.arrow_size.width(), size.height())
        else:
            actual_size = QSizeF(
                size.width(), size.height() - self.arrow_size.height())

        starting_point = QPointF(0, 0)
        if self.direction == self.LEFT:
            starting_point = QPointF(self.arrow_size.width(), 0)
        elif self.direction == self.TOP:
            starting_point = QPointF(0, self.arrow_size.height())

        # painter.save()
        # painter.translate(starting_point)
        self.style().drawPrimitive(QCommonStyle.PE_Widget, opt, painter, self)
        # painter.restore()
        painter.setBrush(QBrush(painter.pen().color()))

        # draw background
        # background_rect = QRectF(starting_point, actual_size)
        QRectF(starting_point, actual_size)
        # painter.drawRoundedRect(background_rect, 5, 5)

        # calculate the arrow
        arrow_points = []
        if self.direction == self.LEFT:
            middle_point = QPointF(0, actual_size.height() / 2)
            arrow_1 = QPointF(
                self.arrow_size.width(), middle_point.y() - self.arrow_size.height() / 2)
            arrow_2 = QPointF(
                self.arrow_size.width(), middle_point.y() + self.arrow_size.height() / 2)
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)
        elif self.direction == self.RIGHT:
            middle_point = QPointF(
                actual_size.width() + self.arrow_size.width(), actual_size.height() / 2)
            arrow_1 = QPointF(actual_size.width(),
                              middle_point.y() + self.arrow_size.height() / 2)
            arrow_2 = QPointF(actual_size.width(),
                              middle_point.y() - self.arrow_size.height() / 2)
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)
        elif self.direction == self.TOP:
            middle_point = QPointF(actual_size.width() / 2, 0)
            arrow_1 = QPointF(
                actual_size.width() / 2 + self.arrow_size.width() / 2, self.arrow_size.height())
            arrow_2 = QPointF(
                actual_size.width() / 2 - self.arrow_size.width() / 2, self.arrow_size.height())
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)
        elif self.direction == self.BOTTOM:
            middle_point = QPointF(
                actual_size.width() / 2, actual_size.height() + self.arrow_size.height())
            arrow_1 = QPointF(
                actual_size.width() / 2 - self.arrow_size.width() / 2, actual_size.height())
            arrow_2 = QPointF(
                actual_size.width() / 2 + self.arrow_size.width() / 2, actual_size.height())
            arrow_points.append(arrow_1)
            arrow_points.append(middle_point)
            arrow_points.append(arrow_2)

        # draw it!
        painter.drawPolygon(QPolygonF(arrow_points))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    parent_widget = QtWidgets.QWidget()
    widget = ArrowWindow(parent=parent_widget)
    parent_widget.show()

    sys.exit(app.exec_())
