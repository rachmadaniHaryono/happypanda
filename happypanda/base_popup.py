"""base popup."""
import sys
import logging

import click
from PyQt5 import QtWidgets
from PyQt5.QtCore import (
    QPoint,
    Qt,
)
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

try:
    from misc import create_animation
    from spacer_widget import SpacerWidget
    from transparent_widget import TransparentWidget
except ImportError:
    from .misc import create_animation
    from .spacer_widget import SpacerWidget
    from .transparent_widget import TransparentWidget

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical


class BasePopup(TransparentWidget):
    """Bases Popup.

    Args:
        parent (QtWidgets.QWidget): Parent widget.
        blur (bool): Blur the widget.
    """

    graphics_blur = None

    def __init__(self, parent=None, **kwargs):
        """__init__."""
        blur = True
        if kwargs:
            blur = kwargs.pop('blur', True)
            super().__init__(parent, **kwargs)
        else:
            super().__init__(parent, flags=Qt.Dialog | Qt.FramelessWindowHint)

        main_layout = QVBoxLayout()
        self.main_widget = QFrame()
        self.main_widget.setFrameStyle(QFrame.StyledPanel)
        self.setLayout(main_layout)
        main_layout.addWidget(self.main_widget)

        self.generic_buttons = QHBoxLayout()
        self.generic_buttons.addWidget(SpacerWidget('h'))
        self.yes_button = QPushButton('Yes')
        self.no_button = QPushButton('No')
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(SpacerWidget('h'), 3)
        self.generic_buttons.addWidget(self.yes_button)
        self.generic_buttons.addWidget(self.no_button)

        self.setMaximumWidth(500)
        self.resize(500, 350)
        self.curr_pos = QPoint()

        if parent and blur:
            try:
                self.graphics_blur = parent.graphics_blur
                parent.setGraphicsEffect(self.graphics_blur)
            except AttributeError:
                pass

        # animation
        self.fade_animation = create_animation(self, 'windowOpacity')
        self.fade_animation.setDuration(800)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.setWindowOpacity(0.0)

    def mousePressEvent(self, event):
        """mouse press event.

        Args:
            event (QtGui.QMouseEvent): Mouse event.
        """
        self.curr_pos = event.pos()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """mouse move event.

        Args:
            event (QtGui.QMouseEvent): Mouse event.
        """
        if event.buttons() == Qt.LeftButton:
            diff = event.pos() - self.curr_pos
            newpos = self.pos() + diff
            self.move(newpos)
        return super().mouseMoveEvent(event)

    def showEvent(self, event):
        """show event.

        Args:
            event (QtGui.QShowEvent): Show event.
        """
        self.activateWindow()
        self.fade_animation.start()
        if self.graphics_blur:
            self.graphics_blur.setEnabled(True)
        return super().showEvent(event)

    def closeEvent(self, event):
        """close event.

        Args:
            event (QtGui.QCloseEvent): Close event.
        """
        if self.graphics_blur:
            self.graphics_blur.setEnabled(False)
        return super().closeEvent(event)

    def hideEvent(self, event):
        """hide event.

        Args:
            event (QtGui.QCloseEvent): Close event.
        """
        if self.graphics_blur:
            self.graphics_blur.setEnabled(False)
        return super().hideEvent(event)

    def add_buttons(self, *args):
        """add buttons.

        Pass names of buttons, from right to left.
        Returns list of buttons in same order as they came in.
        Note: Remember to add buttons_layout to main layout!
        """
        b = []
        for name in args:
            button = QPushButton(name)
            self.buttons_layout.addWidget(button)
            b.append(button)
        return b


@click.command()
@click.option('--blur/--no-blur', default=False)
def main(blur):
    app = QtWidgets.QApplication(sys.argv)

    parent_widget = QtWidgets.QWidget()
    widget = BasePopup(parent=parent_widget, blur=blur)
    widget.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
