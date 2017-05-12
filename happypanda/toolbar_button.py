"""toolbar button.

taken from misc.py
"""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QMenu,
    QPushButton,
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
