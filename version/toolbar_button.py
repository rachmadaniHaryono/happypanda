"""toolbar button."""
import logging

from PyQt5.QtCore import (
    pyqtSignal,
    QRectF,
    Qt,
)
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPaintEvent,
)
from PyQt5.QtWidgets import (
    QMenu,
    QPushButton,
    QStyleOption,
)

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class ToolbarButton(QPushButton):
    """ToolbarButton."""

    select = pyqtSignal(object)
    close_tab = pyqtSignal(object)

    def __init__(self, parent=None, txt=''):
        """__init__."""
        super().__init__(parent)
        self._text = txt
        self._font_metrics = self.fontMetrics()
        if txt:
            self.setText(txt)
        self._selected = False
        self.clicked.connect(lambda: self.select.emit(self))
        self._enable_contextmenu = True

    @property
    def selected(self):
        """selected."""
        return self._selected

    @selected.setter
    def selected(self, b):
        """selected."""
        self._selected = b
        self.update()

    def contextMenuEvent(self, event):  # NOQA
        """contextMenuEvent."""
        if self._enable_contextmenu:
            m = QMenu(self)
            m.addAction("Close Tab").triggered.connect(
                lambda: self.close_tab.emit(self))
            m.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()

    def paintEvent(self, event):  # NOQA
        """paintEvent."""
        assert isinstance(event, QPaintEvent)
        painter = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        # self.style().drawPrimitive(self.style().PE_FrameButtonTool, opt, painter, self)

        # painter.setPen(QColor(164,164,164,120))
        # painter.setBrush(Qt.NoBrush)
        if self._selected:
            painter.setPen(QColor("#d64933"))
        # painter.setPen(Qt.NoPen)
        painter.setRenderHint(painter.Antialiasing)
        ch_width = self._font_metrics.averageCharWidth() / 4
        ch_height = self._font_metrics.height()
        but_rect = QRectF(
            ch_width, ch_width, self.width() - ch_width * 2, self.height() - ch_width * 2)
        select_rect = QRectF(0, 0, self.width(), self.height())

        painter.drawRoundedRect(but_rect, ch_width, ch_width)
        txt_to_draw = self._font_metrics.elidedText(
            self._text, Qt.ElideRight, but_rect.width())

        but_center = (but_rect.height() - ch_height) / 2
        text_rect = QRectF(
            but_rect.x() + ch_width * 2,
            but_rect.y() + but_center, but_rect.width(), but_rect.height())
        # painter.setPen(QColor('white'))
        painter.drawText(text_rect, txt_to_draw)

        if self.underMouse():
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(164, 164, 164, 90)))
            painter.drawRoundedRect(select_rect, 2, 2)
            painter.restore()

    def setText(self, txt):  # NOQA
        """setText."""
        self._text = txt
        self.update()
        super().setText(txt)

    def text(self):
        """text."""
        return self._text
