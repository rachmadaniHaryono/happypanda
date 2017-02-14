"""toolbar button."""
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


class ToolbarButton(QPushButton):
    """Toolbar button.

    Args:
        parent (QtWidgets.QWidget): Parent widget.
        txt (str): Text.

    Attributes:
        select (pyqtSignal): Signal when selected.
        close_tab (pyqtSignal): Signal when tab closed.
        _txt (str): Text.
        _font_metrics (QtGui.QFontMetrics):  Font metrics.
        _selected (bool): State if button selected.
        _enable_contextmenu (bool): Enable context menu.
    """

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
        """Selected property.

        When it is set with value, it will also update the button.
        """
        return self._selected

    @selected.setter
    def selected(self, b):
        self._selected = b
        self.update()

    def contextMenuEvent(self, event):  # NOQA
        """Context menu event.

        Args:
            event (QtGui.QContextMenuEvent): Context menu event.
        """
        if self._enable_contextmenu:
            m = QMenu(self)
            m.addAction("Close Tab").triggered.connect(
                lambda: self.close_tab.emit(self))
            m.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()

    def paintEvent(self, event):  # NOQA
        """Paint event.

        Args:
            event (QtGui.QPaintEvent): Paint event.
        """
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
        """set Text.

        Args:
            txt: Text.
        """
        self._text = txt
        self.update()
        super().setText(txt)

    def text(self):
        """Text."""
        return self._text
