"""app bubble."""
import logging
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import (
    Qt,
    QTimer,
)
from PyQt5.QtWidgets import (
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)

try:
    from base_popup import BasePopup
except ImportError:
    from .base_popup import BasePopup

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class AppBubble(BasePopup):
    """For application notifications."""

    def __init__(self, parent):
        """__init__."""
        super().__init__(parent, flags=Qt.Window | Qt.FramelessWindowHint, blur=False)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.hide)

        main_layout = QVBoxLayout(self.main_widget)
        #
        self.title = QLabel()
        self.title.setTextFormat(Qt.RichText)
        main_layout.addWidget(self.title)
        #
        self.content = QLabel()
        self.content.setWordWrap(True)
        self.content.setTextFormat(Qt.RichText)
        self.content.setOpenExternalLinks(True)
        main_layout.addWidget(self.content)

        self.adjustSize()

    def update_text(self, title, txt='', duration=20):
        """update text.

        Args:
            title: Title on widget.
            txt: Text on widget, under title.
            duration: Duration of showing the text in seconds.
        """
        if self.hide_timer.isActive():
            self.hide_timer.stop()
        self.title.setText('<h3>{}</h3>'.format(title))
        self.content.setText(txt)
        self.hide_timer.start(duration * 1000)
        self.show()
        self.adjustSize()
        self.update_move()

    def update_move(self):
        """update move."""
        if self.parent_widget and hasattr(self.parent_widget, "statusBar"):
            tl = self.parent_widget.geometry().topLeft()
            x = tl.x() + self.parent_widget.width() - self.width() - 10
            y = tl.y() + self.parent_widget.height() - self.height() - \
                self.parent_widget.statusBar().height()
            self.move(x, y)

    def mousePressEvent(self, event):
        """mouse press event.

        Args:
            event (QtGui.QMouseEvent): Mouse event.
        """
        if event.button() == Qt.RightButton:
            self.close()
        super().mousePressEvent(event)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    widget = QtWidgets.QWidget()
    popup = AppBubble(parent=widget)
    popup.show()
    popup.update_text(title='title', txt='text')

    sys.exit(app.exec_())
