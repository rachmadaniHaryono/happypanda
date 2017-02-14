"""base move widget."""
import logging

from PyQt5.QtCore import (
    Qt,
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


class BaseMoveWidget(QWidget):
    """BaseMoveWidget.

    Args:
        parent (QtWidgets.QWidget): Parent widget.
        move_listener (bool): connect parent widget method to this widget.
    """

    def __init__(self, parent=None, **kwargs):
        """__init__."""
        move_listener = kwargs.pop('move_listener', True)
        super().__init__(parent, **kwargs)
        self.parent_widget = parent
        self.setAttribute(Qt.WA_DeleteOnClose)
        if parent and move_listener:
            try:
                parent.move_listener.connect(self.update_move)
            except AttributeError:
                pass

    def update_move(self, new_size=None):
        """update move.

        Args:
            new_size: Size in tuple of (x, y).
        """
        if new_size:
            self.move(new_size)
            return
        if self.parent_widget:
            self.move(
                self.parent_widget.window().frameGeometry().center() -
                self.window().rect().center())
