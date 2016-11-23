"""notification overlay widget."""
import logging
import threading

from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
    QTimer,
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QWidget,
)

try:
    from misc import create_animation
except ImportError:
    from .misc import create_animation

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class NotificationOverlayWidget(QWidget):
    """A notifaction bar."""

    clicked = pyqtSignal()
    _show_signal = pyqtSignal()
    _hide_signal = pyqtSignal()
    _unset_cursor = pyqtSignal()
    _set_cursor = pyqtSignal(object)

    def __init__(self, parent=None):
        """__init__."""
        super().__init__(parent)
        self._main_layout = QHBoxLayout(self)
        self._default_height = 20
        self._dynamic_height = 0
        self._lbl = QLabel()
        self._main_layout.addWidget(self._lbl)
        self._lbl.setAlignment(Qt.AlignCenter)
        self.setContentsMargins(-10, -10, -10, -10)
        self._click = False
        self._override_hide = False
        self.text_queue = []

        self.slide_animation = create_animation(self, 'minimumHeight')
        self.slide_animation.setDuration(500)
        self.slide_animation.setStartValue(0)
        self.slide_animation.setEndValue(self._default_height)
        self.slide_animation.valueChanged.connect(self.set_dynamic_height)
        self._show_signal.connect(self.show)
        self._hide_signal.connect(self.hide)
        self._unset_cursor.connect(self.unsetCursor)
        self._set_cursor.connect(self.setCursor)

    def set_dynamic_height(self, h):
        """set_dynamic_height."""
        self._dynamic_height = h

    def mousePressEvent(self, event):
        """mousePressEvent."""
        if self._click:
            self.clicked.emit()
        return super().mousePressEvent(event)

    def set_clickable(self, d=True):
        """set_clickable."""
        self._click = d
        self._set_cursor.emit(Qt.PointingHandCursor)

    def resize(self, x, y=0):
        """resize."""
        return super().resize(x, self._dynamic_height)

    def add_text(self, text, autohide=True):
        """add_text.

        Add new text to the bar, deleting the previous one
        """
        try:
            self._reset()
        except TypeError:
            pass
        if not self.isVisible():
            self._show_signal.emit()
        self._lbl.setText(text)
        if autohide:
            if not self._override_hide:
                threading.Timer(10, self._hide_signal.emit).start()

    def begin_show(self):
        """Control how long you will show notification bar.

        end_show() must be called to hide the bar.
        """
        self._override_hide = True
        self._show_signal.emit()

    def end_show(self):
        """end_show."""
        self._override_hide = False
        QTimer.singleShot(5000, self._hide_signal.emit)

    def _reset(self):
        """_reset."""
        self._unset_cursor.emit()
        self._click = False
        self.clicked.disconnect()

    def showEvent(self, event):
        """showEvent."""
        self.slide_animation.start()
        return super().showEvent(event)
